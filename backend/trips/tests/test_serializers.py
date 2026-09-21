import pytest
from trips.serializers import TripRequestSerializer


@pytest.fixture
def valid_data():
    return {
        "current_location": "Dallas, TX",
        "pickup_location": "Oklahoma City, OK",
        "dropoff_location": "Denver, CO",
        "cycle_used_hrs": 22.5,
    }


class TestTripRequestSerializer:
    def test_valid_payload_passes(self, valid_data):
        serializer = TripRequestSerializer(data=valid_data)
        assert serializer.is_valid()

    def test_missing_current_location_fails(self, valid_data):
        del valid_data["current_location"]
        serializer = TripRequestSerializer(data=valid_data)
        assert not serializer.is_valid()
        assert "current_location" in serializer.errors

    def test_cycle_used_hrs_negative_fails(self, valid_data):
        valid_data["cycle_used_hrs"] = -1
        serializer = TripRequestSerializer(data=valid_data)
        assert not serializer.is_valid()
        assert "cycle_used_hrs" in serializer.errors

    def test_cycle_used_hrs_over_70_fails(self, valid_data):
        valid_data["cycle_used_hrs"] = 71
        serializer = TripRequestSerializer(data=valid_data)
        assert not serializer.is_valid()
        assert "cycle_used_hrs" in serializer.errors

    def test_pickup_equals_dropoff_fails(self, valid_data):
        valid_data["pickup_location"] = "Denver, CO"
        serializer = TripRequestSerializer(data=valid_data)
        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
        assert "same" in str(serializer.errors).lower()

    def test_whitespace_is_stripped(self, valid_data):
        valid_data["current_location"] = "  Dallas, TX  "
        serializer = TripRequestSerializer(data=valid_data)
        assert serializer.is_valid()
        assert serializer.validated_data["current_location"] == "Dallas, TX"

    def test_blank_string_fails(self, valid_data):
        valid_data["current_location"] = ""
        serializer = TripRequestSerializer(data=valid_data)
        assert not serializer.is_valid()
        assert "current_location" in serializer.errors
