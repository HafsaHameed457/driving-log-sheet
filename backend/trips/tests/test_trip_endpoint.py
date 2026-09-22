"""Tests for the POST /api/trip/ endpoint (mocked geo services)."""

import pytest
from unittest.mock import patch, MagicMock
from django.test import override_settings

from trips.services.errors import LocationNotFoundError


# ── Mock data ──────────────────────────────────────────────────

MOCK_GEOCODE_DALLAS = {"lat": 32.78, "lng": -96.80, "label": "Dallas, TX"}
MOCK_GEOCODE_OKC = {"lat": 35.47, "lng": -97.52, "label": "Oklahoma City, OK"}
MOCK_GEOCODE_DENVER = {"lat": 39.74, "lng": -104.99, "label": "Denver, CO"}

MOCK_ROUTE = {
    "total_miles": 900.0,
    "total_duration_hrs": 16.36,
    "geometry": [
        [32.78, -96.80], [33.50, -97.00], [34.50, -97.30],
        [35.47, -97.52], [36.50, -98.00], [37.50, -100.00],
        [38.50, -102.00], [39.74, -104.99],
    ],
    "legs": [
        {
            "from_index": 0, "to_index": 1,
            "miles": 360.0, "duration_hrs": 6.55,
            "end_distance_from_start_mi": 360.0,
        },
        {
            "from_index": 1, "to_index": 2,
            "miles": 540.0, "duration_hrs": 9.82,
            "end_distance_from_start_mi": 900.0,
        },
    ],
}


def _mock_geocode(query):
    mapping = {
        "dallas, tx": MOCK_GEOCODE_DALLAS,
        "oklahoma city, ok": MOCK_GEOCODE_OKC,
        "denver, co": MOCK_GEOCODE_DENVER,
    }
    key = query.strip().lower()
    if key in mapping:
        return mapping[key]
    return {"lat": 35.0, "lng": -97.0, "label": query}


VALID_PAYLOAD = {
    "current_location": "Dallas, TX",
    "pickup_location": "Oklahoma City, OK",
    "dropoff_location": "Denver, CO",
    "cycle_used_hrs": 22.5,
}


# ============================================================
# t7: Full endpoint shape
# ============================================================
@pytest.mark.django_db
@patch("trips.views.reverse_geocode", return_value="Somewhere, TX")
@patch("trips.views.get_route", return_value=MOCK_ROUTE)
@patch("trips.views.geocode", side_effect=_mock_geocode)
def test_t7_full_endpoint_shape(mock_geo, mock_route, mock_rev, client):
    resp = client.post(
        "/api/trip/",
        data=VALID_PAYLOAD,
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.json()

    assert "route" in body
    assert "stops" in body
    assert "logs" in body

    assert body["route"]["total_miles"] > 0
    assert body["route"]["total_drive_hrs"] > 0
    assert isinstance(body["route"]["geometry"], list)

    assert isinstance(body["stops"], list)
    assert len(body["stops"]) > 0

    assert isinstance(body["logs"], list)
    assert len(body["logs"]) > 0
    for log in body["logs"]:
        assert "date" in log
        assert "events" in log
        assert "totals" in log
        assert "recap" in log
        assert "from_location" in log
        assert "to_location" in log
        assert "total_miles_today" in log


# ============================================================
# t8: Days sum to 24.00
# ============================================================
@pytest.mark.django_db
@patch("trips.views.reverse_geocode", return_value="Somewhere, TX")
@patch("trips.views.get_route", return_value=MOCK_ROUTE)
@patch("trips.views.geocode", side_effect=_mock_geocode)
def test_t8_days_sum_to_24(mock_geo, mock_route, mock_rev, client):
    resp = client.post(
        "/api/trip/",
        data=VALID_PAYLOAD,
        content_type="application/json",
    )
    assert resp.status_code == 200
    body = resp.json()

    for log in body["logs"]:
        t = log["totals"]
        total = t["off_duty"] + t["sleeper"] + t["driving"] + t["on_duty"]
        assert abs(total - 24.0) < 0.01, f"{log['date']}: {total:.4f}"


# ============================================================
# t9: Invalid payload returns 400
# ============================================================
@pytest.mark.django_db
def test_t9_invalid_payload_returns_400(client):
    resp = client.post(
        "/api/trip/",
        data={"pickup_location": "OKC", "dropoff_location": "Denver", "cycle_used_hrs": 10},
        content_type="application/json",
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "current_location" in body


# ============================================================
# t10: Geocode failure returns 400
# ============================================================
@pytest.mark.django_db
@patch("trips.views.geocode", side_effect=LocationNotFoundError("Location not found: 'Atlantis'"))
def test_t10_geocode_failure_returns_400(mock_geo, client):
    resp = client.post(
        "/api/trip/",
        data=VALID_PAYLOAD,
        content_type="application/json",
    )
    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body
