import logging
import itertools
from dataclasses import asdict

from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import (
    TripRequestSerializer,
    TripResponseSerializer,
)
from .services.geo import geocode, get_route, point_at_distance, reverse_geocode
from .services.errors import GeoServiceError, NoRouteFoundError
from .services.hos_planner import plan_trip
from .services.logs import build_daily_logs

logger = logging.getLogger(__name__)

MAX_MILES = 6000

_ROUTE_OFFSETS = [0.01, -0.01, 0.02, -0.02]


def _try_get_route(waypoints: list[dict]) -> dict:
    """Try get_route, nudging failing waypoints if routing fails.

    ORS geocoder returns city centroids that may not be within 350m of a
    routable road. Parses the error to find which coordinate failed and
    retries only that waypoint with small offsets.
    """
    try:
        route = get_route(waypoints)
        if route["total_miles"] > 0:
            return route
    except NoRouteFoundError as e:
        failing_idx = None
        msg = str(e)
        if "coordinate" in msg:
            try:
                coord_str = msg.split("coordinate")[1].split(":")[0].strip()
                failing_idx = int(coord_str)
            except (IndexError, ValueError):
                pass

    for wp_idx in range(len(waypoints)):
        if failing_idx is not None and wp_idx != failing_idx:
            continue
        for dx in _ROUTE_OFFSETS:
            for dy in _ROUTE_OFFSETS:
                adjusted = [dict(w) for w in waypoints]
                adjusted[wp_idx] = {
                    "lat": waypoints[wp_idx]["lat"] + dx,
                    "lng": waypoints[wp_idx]["lng"] + dy,
                    "label": waypoints[wp_idx]["label"],
                }
                try:
                    route = get_route(adjusted)
                    if route["total_miles"] > 0:
                        return route
                except NoRouteFoundError:
                    continue

    raise NoRouteFoundError("One or more locations are not near a routable road")


def health_check(request):
    return JsonResponse({"status": "ok"})


class TripView(APIView):
    """Full trip planning endpoint.

    Accepts trip input, geocodes, routes, plans HOS, builds daily logs.
    """

    def post(self, request):
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            geo_current = geocode(data["current_location"])
            geo_pickup = geocode(data["pickup_location"])
            geo_dropoff = geocode(data["dropoff_location"])

            waypoints = [geo_current, geo_pickup, geo_dropoff]
            route = _try_get_route(waypoints)

            if route["total_miles"] > MAX_MILES:
                return Response(
                    {"error": "Trip is too long to plan in a single request (>6000 miles)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            pickup_miles = route["legs"][0]["end_distance_from_start_mi"]
            dropoff_miles = route["legs"][1]["end_distance_from_start_mi"]
            cycle_used_hrs = data["cycle_used_hrs"]

            geo_cache: dict[int, str] = {}

            def location_lookup(miles: float) -> str:
                rounded = int(round(miles))
                if rounded in geo_cache:
                    return geo_cache[rounded]
                pt = point_at_distance(route["geometry"], miles)
                try:
                    label = reverse_geocode(pt["lat"], pt["lng"])
                except GeoServiceError:
                    label = f"Mile {miles:.0f}"
                geo_cache[rounded] = label
                return label

            result = plan_trip(
                route=route,
                pickup_miles=pickup_miles,
                dropoff_miles=dropoff_miles,
                cycle_used_hrs=cycle_used_hrs,
                geometry=route["geometry"],
                location_lookup=location_lookup,
            )

            daily_logs = build_daily_logs(result, cycle_used_hrs)

            response_data = {
                "route": {
                    "total_miles": result.total_miles,
                    "total_drive_hrs": result.total_drive_hrs,
                    "geometry": route["geometry"],
                },
                "stops": [asdict(s) for s in result.stops],
                "logs": [asdict(l) for l in daily_logs],
            }

            resp_serializer = TripResponseSerializer(data=response_data)
            resp_serializer.is_valid(raise_exception=True)

            return Response(resp_serializer.data)

        except GeoServiceError as e:
            return Response({"error": e.message}, status=e.http_status)
        except Exception:
            logger.exception("Unexpected error planning trip")
            return Response(
                {"error": "Internal error while planning trip."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
