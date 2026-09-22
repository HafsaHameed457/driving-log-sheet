import os, sys, json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django; django.setup()
from dotenv import load_dotenv; load_dotenv()

from django.test import RequestFactory
from unittest.mock import patch
from trips.views import TripView

factory = RequestFactory()
request = factory.post(
    "/api/trip/",
    data=json.dumps({
        "current_location": "Dallas, TX",
        "pickup_location": "Oklahoma City, OK",
        "dropoff_location": "Denver, CO",
        "cycle_used_hrs": 22.5,
    }),
    content_type="application/json",
)

view = TripView.as_view()
response = view(request)
print("Status: %d" % response.status_code)
data = response.data
if response.status_code == 200:
    print("Route: %.0f mi" % data["route"]["total_miles"])
    print("Stops: %d" % len(data["stops"]))
    print("Logs: %d" % len(data["logs"]))
    for log in data["logs"]:
        t = log["totals"]
        total = t["off_duty"] + t["sleeper"] + t["driving"] + t["on_duty"]
        print("  %s: %d mi, %.2f hrs" % (log["date"], log["total_miles_today"], total))
else:
    print("Error: %s" % json.dumps(data, indent=2))
