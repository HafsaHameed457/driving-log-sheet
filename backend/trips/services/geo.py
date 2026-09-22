import math
import os

import requests

from .errors import (
    GeoServiceConfigError,
    GeoServiceUnavailableError,
    LocationNotFoundError,
    NoRouteFoundError,
)

ORS_BASE_URL = "https://api.openrouteservice.org"


def _get_api_key() -> str:
    """Return the ORS API key or raise if missing."""
    key = os.getenv("ORS_API_KEY", "")
    if not key:
        raise GeoServiceConfigError("ORS_API_KEY environment variable is not set")
    return key


def _handle_response(resp: requests.Response) -> dict:
    """Raise appropriate errors for HTTP failures."""
    if resp.status_code == 429:
        raise GeoServiceUnavailableError("Rate limited by OpenRouteService")
    if resp.status_code >= 500:
        raise GeoServiceUnavailableError(
            f"OpenRouteService unavailable (HTTP {resp.status_code})"
        )
    if resp.status_code == 404:
        raise NoRouteFoundError(
            "One or more locations are not near a routable road"
        )
    if resp.status_code != 200:
        raise GeoServiceUnavailableError(
            f"OpenRouteService returned HTTP {resp.status_code}: {resp.text[:200]}"
        )
    return resp.json()


def geocode(query: str) -> dict:
    """Geocode a location string using ORS Pelias geocoding.

    Args:
        query: A human-readable location string (e.g. "Dallas, TX").

    Returns:
        {"lat": float, "lng": float, "label": str}

    Raises:
        LocationNotFoundError: if no results found.
        GeoServiceUnavailableError: on HTTP errors or network issues.
        GeoServiceConfigError: if API key is missing.
    """
    api_key = _get_api_key()
    try:
        resp = requests.get(
            f"{ORS_BASE_URL}/geocode/search",
            params={"api_key": api_key, "text": query, "size": 1},
            timeout=10,
        )
    except requests.RequestException as e:
        raise GeoServiceUnavailableError(f"Network error geocoding '{query}': {e}")

    data = _handle_response(resp)
    features = data.get("features", [])
    if not features:
        raise LocationNotFoundError(f"Location not found: '{query}'")

    props = features[0].get("properties", {})
    coords = features[0].get("geometry", {}).get("coordinates", [0, 0])
    label = props.get("label", query)

    return {"lat": coords[1], "lng": coords[0], "label": label}


def reverse_geocode(lat: float, lng: float) -> str:
    """Reverse-geocode a lat/lng into a short human-readable string.

    NOTE: Callers should only invoke this for STOP locations, not every
    point on the route, to stay within API rate limits.

    Args:
        lat: Latitude.
        lng: Longitude.

    Returns:
        A short string like "Amarillo, TX".

    Raises:
        LocationNotFoundError: if reverse geocoding returns no results.
        GeoServiceUnavailableError: on HTTP errors or network issues.
        GeoServiceConfigError: if API key is missing.
    """
    api_key = _get_api_key()
    try:
        resp = requests.get(
            f"{ORS_BASE_URL}/geocode/reverse",
            params={
                "api_key": api_key,
                "point.lon": lng,
                "point.lat": lat,
                "size": 1,
            },
            timeout=10,
        )
    except requests.RequestException as e:
        raise GeoServiceUnavailableError(
            f"Network error reverse geocoding ({lat}, {lng}): {e}"
        )

    data = _handle_response(resp)
    features = data.get("features", [])
    if not features:
        raise LocationNotFoundError(
            f"Reverse geocode not found for ({lat}, {lng})"
        )

    props = features[0].get("properties", {})
    locality = props.get("locality", "")
    region = props.get("region", "")
    if locality and region:
        return f"{locality}, {region}"
    return props.get("label", f"{lat}, {lng}")


def get_route(waypoints: list[dict]) -> dict:
    """Get a driving route through the given waypoints using ORS Directions.

    Uses driving-hgv profile (truck-friendly). Falls back to driving-car
    if HGV access is restricted on the free tier.

    Args:
        waypoints: List of {"lat": float, "lng": float} in order.

    Returns:
        {
            "total_miles": float,
            "total_duration_hrs": float,
            "geometry": [[lat, lng], ...],
            "legs": [
                {
                    "from_index": int,
                    "to_index": int,
                    "miles": float,
                    "duration_hrs": float,
                    "end_distance_from_start_mi": float,
                },
                ...
            ]
        }

    Raises:
        NoRouteFoundError: if ORS returns no route.
        GeoServiceUnavailableError: on HTTP errors or network issues.
        GeoServiceConfigError: if API key is missing.
    """
    api_key = _get_api_key()
    coords = [[wp["lng"], wp["lat"]] for wp in waypoints]

    profiles = ["driving-hgv", "driving-car"]
    last_resp = None

    for profile in profiles:
        try:
            resp = requests.post(
                f"{ORS_BASE_URL}/v2/directions/{profile}/geojson",
                json={"coordinates": coords},
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
        except requests.RequestException as e:
            raise GeoServiceUnavailableError(f"Network error fetching route: {e}")

        last_resp = resp
        if resp.status_code == 200:
            break

    if last_resp.status_code == 401:
        raise GeoServiceConfigError("ORS API key is invalid or unauthorized")

    data = _handle_response(last_resp)
    features = data.get("features", [])
    if not features:
        raise NoRouteFoundError("No route found between the given locations")

    route = features[0]
    legs_data = route.get("properties", {}).get("segments", [])
    geom_coords = route.get("geometry", {}).get("coordinates", [])

    geometry = [[c[1], c[0]] for c in geom_coords]

    total_miles = 0.0
    total_duration = 0.0
    legs = []
    for i, leg in enumerate(legs_data):
        dist_m = leg.get("summary", {}).get("distance", 0)
        dur_s = leg.get("summary", {}).get("duration", 0)
        leg_miles = dist_m / 1609.344
        leg_hours = dur_s / 3600.0
        total_miles += leg_miles
        total_duration += leg_hours
        legs.append({
            "from_index": i,
            "to_index": i + 1,
            "miles": round(leg_miles, 2),
            "duration_hrs": round(leg_hours, 2),
            "end_distance_from_start_mi": round(total_miles, 2),
        })

    return {
        "total_miles": round(total_miles, 2),
        "total_duration_hrs": round(total_duration, 2),
        "geometry": geometry,
        "legs": legs,
    }


def _haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate the great-circle distance between two points in miles."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def point_at_distance(geometry: list[list[float]], target_miles: float) -> dict:
    """Find a point along the polyline at a given distance from the start.

    Uses haversine distance between consecutive points and linear
    interpolation for the final position.

    Args:
        geometry: List of [lat, lng] pairs.
        target_miles: Distance in miles from the start.

    Returns:
        {"lat": float, "lng": float}
    """
    if not geometry:
        return {"lat": 0.0, "lng": 0.0}
    if target_miles <= 0:
        return {"lat": geometry[0][0], "lng": geometry[0][1]}

    accumulated = 0.0
    for i in range(1, len(geometry)):
        seg_dist = _haversine_miles(
            geometry[i - 1][0], geometry[i - 1][1],
            geometry[i][0], geometry[i][1],
        )
        if accumulated + seg_dist >= target_miles:
            overshoot = target_miles - accumulated
            fraction = overshoot / seg_dist if seg_dist > 0 else 0
            lat = geometry[i - 1][0] + fraction * (geometry[i][0] - geometry[i - 1][0])
            lng = geometry[i - 1][1] + fraction * (geometry[i][1] - geometry[i - 1][1])
            return {"lat": lat, "lng": lng}
        accumulated += seg_dist

    return {"lat": geometry[-1][0], "lng": geometry[-1][1]}
