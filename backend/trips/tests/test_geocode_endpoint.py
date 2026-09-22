"""Tests for the GET /api/geocode/ proxy endpoint (mocked geocode)."""

import pytest
from unittest.mock import patch

from trips.services.errors import LocationNotFoundError


MOCK_RESULT = {"lat": 32.7767, "lng": -96.797, "label": "Dallas, TX, USA"}


@pytest.mark.django_db
@patch("trips.views.geocode", return_value=MOCK_RESULT)
def test_geocode_success_returns_list_of_one(mock_geocode, client):
    resp = client.get("/api/geocode/?q=Dallas")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["lat"] == MOCK_RESULT["lat"]
    assert data[0]["lng"] == MOCK_RESULT["lng"]
    assert data[0]["label"] == MOCK_RESULT["label"]


@pytest.mark.django_db
@patch(
    "trips.views.geocode",
    side_effect=LocationNotFoundError("Location not found: 'Atlantis'"),
)
def test_geocode_not_found_returns_empty_list(mock_geocode, client):
    resp = client.get("/api/geocode/?q=Atlantis")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.django_db
def test_geocode_short_query_returns_empty_list(client):
    resp = client.get("/api/geocode/?q=ab")
    assert resp.status_code == 200
    assert resp.json() == []
