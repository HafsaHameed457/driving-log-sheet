class GeoServiceError(Exception):
    """Base class for all geo service errors."""
    http_status = 502

    def __init__(self, message: str = "Geo service error"):
        self.message = message
        super().__init__(self.message)


class LocationNotFoundError(GeoServiceError):
    """Raised when a location cannot be geocoded."""
    http_status = 400


class NoRouteFoundError(GeoServiceError):
    """Raised when ORS cannot find a route between waypoints."""
    http_status = 400


class GeoServiceUnavailableError(GeoServiceError):
    """Raised when ORS is down, rate-limited, or returns a server error."""
    http_status = 503


class GeoServiceConfigError(GeoServiceError):
    """Raised when the ORS API key is missing or invalid."""
    http_status = 500
