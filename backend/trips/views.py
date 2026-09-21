from django.http import JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import TripRequestSerializer
from .services.geo import geocode, get_route
from .services.errors import GeoServiceError


def health_check(request):
    return JsonResponse({"status": "ok"})


class TripView(APIView):
    """Smoke-test endpoint for Phase B2.

    Accepts trip input, geocodes locations, fetches the route,
    and returns a partial response (no stops/logs yet).
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
            route = get_route(waypoints)

            return Response({
                "route": {
                    "total_miles": route["total_miles"],
                    "total_drive_hrs": route["total_duration_hrs"],
                    "geometry": route["geometry"],
                },
                "geocoded": {
                    "current": geo_current,
                    "pickup": geo_pickup,
                    "dropoff": geo_dropoff,
                },
                "note": "B2 smoke test — stops and logs will be added in B3/B4",
            })

        except GeoServiceError as e:
            return Response({"error": e.message}, status=e.http_status)
        except Exception:
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
