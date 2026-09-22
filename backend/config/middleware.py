import logging

logger = logging.getLogger(__name__)


def _get_origin(request) -> str:
    return request.META.get("HTTP_ORIGIN") or request.META.get("HTTP_REFERER") or "unknown"


class RequestLoggingMiddleware:
    """Log origin, route, method, and body for every incoming request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        body = ""
        try:
            body = request.body.decode("utf-8", errors="replace")
        except Exception:
            body = ""

        logger.info(
            "Request: origin=%s method=%s path=%s body=%s",
            _get_origin(request),
            request.method,
            request.path,
            body,
        )

        return self.get_response(request)