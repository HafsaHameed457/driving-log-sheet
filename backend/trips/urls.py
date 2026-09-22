from django.urls import path
from .views import health_check, TripView, GeocodeView

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("trip/", TripView.as_view(), name="trip-create"),
    path("geocode/", GeocodeView.as_view(), name="geocode"),
]
