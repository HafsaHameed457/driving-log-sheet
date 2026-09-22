import pytest
from unittest.mock import patch, MagicMock

from trips.services.geo import geocode, reverse_geocode, get_route, point_at_distance
from trips.services.errors import (
    LocationNotFoundError,
    NoRouteFoundError,
    GeoServiceUnavailableError,
    GeoServiceConfigError,
)


@pytest.fixture
def mock_ors_key(monkeypatch):
    monkeypatch.setenv("ORS_API_KEY", "test-api-key")


@pytest.fixture
def geocode_response():
    return {
        "features": [
            {
                "geometry": {"coordinates": [-96.7970, 32.7767]},
                "properties": {"label": "Dallas, TX, United States"},
            }
        ]
    }


@pytest.fixture
def reverse_geocode_response():
    return {
        "features": [
            {
                "geometry": {"coordinates": [-101.8313, 35.2220]},
                "properties": {
                    "locality": "Amarillo",
                    "region": "TX",
                    "label": "Amarillo, TX, United States",
                },
            }
        ]
    }


@pytest.fixture
def route_response():
    return {
        "features": [
            {
                "geometry": {
                    "coordinates": [
                        [-96.7970, 32.7767],
                        [-97.5164, 35.4676],
                        [-104.9903, 39.7392],
                    ]
                },
                "properties": {
                    "segments": [
                        {
                            "summary": {
                                "distance": 260000,
                                "duration": 9360,
                            }
                        },
                        {
                            "summary": {
                                "distance": 1080000,
                                "duration": 38880,
                            }
                        },
                    ]
                },
            }
        ]
    }


class TestGeocode:
    def test_success(self, mock_ors_key, geocode_response):
        with patch("trips.services.geo.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: geocode_response
            )
            result = geocode("Dallas, TX")

        assert result["lat"] == pytest.approx(32.7767)
        assert result["lng"] == pytest.approx(-96.7970)
        assert result["label"] == "Dallas, TX, United States"

    def test_empty_features_raises_not_found(self, mock_ors_key):
        with patch("trips.services.geo.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: {"features": []}
            )
            with pytest.raises(LocationNotFoundError):
                geocode("asdfghjkl")

    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("ORS_API_KEY", raising=False)
        with pytest.raises(GeoServiceConfigError):
            geocode("Dallas, TX")

    def test_rate_limited(self, mock_ors_key):
        with patch("trips.services.geo.requests.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=429, text="Rate limited")
            with pytest.raises(GeoServiceUnavailableError):
                geocode("Dallas, TX")


class TestReverseGeocode:
    def test_success(self, mock_ors_key, reverse_geocode_response):
        with patch("trips.services.geo.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: reverse_geocode_response
            )
            result = reverse_geocode(35.2220, -101.8313)

        assert result == "Amarillo, TX"

    def test_fallback_to_label(self, mock_ors_key):
        response = {
            "features": [
                {
                    "properties": {"label": "Some Place, AB, Canada"},
                }
            ]
        }
        with patch("trips.services.geo.requests.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200, json=lambda: response
            )
            result = reverse_geocode(50.0, -100.0)

        assert result == "Some Place, AB, Canada"


class TestGetRoute:
    def test_conversions(self, mock_ors_key, route_response):
        with patch("trips.services.geo.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, json=lambda: route_response
            )
            result = get_route(
                [{"lat": 32.7767, "lng": -96.7970},
                 {"lat": 35.4676, "lng": -97.5164},
                 {"lat": 39.7392, "lng": -104.9903}]
            )

        # 260000 m = 161.40 mi, 1080000 m = 671.0 mi, total = 832.64 mi
        # 9360 s = 2.60 hr, 38880 s = 10.80 hr, total = 13.40 hr
        assert result["total_miles"] == pytest.approx(832.64, abs=1.0)
        assert result["total_duration_hrs"] == pytest.approx(13.4, abs=0.1)
        assert len(result["geometry"]) == 3
        assert result["legs"][0]["miles"] == pytest.approx(161.56, abs=1.0)
        assert result["legs"][1]["miles"] == pytest.approx(671.08, abs=1.0)

    def test_cumulative_distance(self, mock_ors_key, route_response):
        with patch("trips.services.geo.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, json=lambda: route_response
            )
            result = get_route(
                [{"lat": 32.7767, "lng": -96.7970},
                 {"lat": 35.4676, "lng": -97.5164},
                 {"lat": 39.7392, "lng": -104.9903}]
            )

        leg0_end = result["legs"][0]["end_distance_from_start_mi"]
        leg1_end = result["legs"][1]["end_distance_from_start_mi"]
        assert leg1_end == pytest.approx(leg0_end + result["legs"][1]["miles"], abs=0.1)

    def test_empty_features_raises_no_route(self, mock_ors_key):
        with patch("trips.services.geo.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200, json=lambda: {"features": []}
            )
            with pytest.raises(NoRouteFoundError):
                get_route([{"lat": 0, "lng": 0}, {"lat": 1, "lng": 1}])

    def test_server_error(self, mock_ors_key):
        with patch("trips.services.geo.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=500, text="Internal error")
            with pytest.raises(GeoServiceUnavailableError):
                get_route([{"lat": 0, "lng": 0}, {"lat": 1, "lng": 1}])


class TestPointAtDistance:
    def test_midpoint(self):
        geometry = [[0.0, 0.0], [2.0, 0.0]]
        result = point_at_distance(geometry, 69.0)
        assert result["lat"] == pytest.approx(1.0, abs=0.01)
        assert result["lng"] == pytest.approx(0.0, abs=0.01)

    def test_target_zero(self):
        geometry = [[0.0, 0.0], [2.0, 0.0]]
        result = point_at_distance(geometry, 0)
        assert result["lat"] == 0.0
        assert result["lng"] == 0.0

    def test_target_negative(self):
        geometry = [[0.0, 0.0], [2.0, 0.0]]
        result = point_at_distance(geometry, -10)
        assert result["lat"] == 0.0
        assert result["lng"] == 0.0

    def test_target_exceeds_total(self):
        geometry = [[0.0, 0.0], [1.0, 0.0]]
        result = point_at_distance(geometry, 10000)
        assert result["lat"] == 1.0
        assert result["lng"] == 0.0

    def test_empty_geometry(self):
        result = point_at_distance([], 10)
        assert result == {"lat": 0.0, "lng": 0.0}
