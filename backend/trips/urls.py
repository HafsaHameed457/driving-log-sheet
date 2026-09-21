from django.urls import path
from .views import health_check, TripView

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("trip/", TripView.as_view(), name="trip-create"),
]
