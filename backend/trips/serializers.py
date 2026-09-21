from rest_framework import serializers


class TripRequestSerializer(serializers.Serializer):
    """Input validation for the POST /api/trip/ endpoint."""

    current_location = serializers.CharField(max_length=200, required=True, allow_blank=False)
    pickup_location = serializers.CharField(max_length=200, required=True, allow_blank=False)
    dropoff_location = serializers.CharField(max_length=200, required=True, allow_blank=False)
    cycle_used_hrs = serializers.FloatField(required=True, min_value=0.0, max_value=70.0)

    def validate(self, data: dict) -> dict:
        """Strip whitespace and check that no two locations are identical."""
        data["current_location"] = data["current_location"].strip()
        data["pickup_location"] = data["pickup_location"].strip()
        data["dropoff_location"] = data["dropoff_location"].strip()

        locations = {
            "current": data["current_location"].lower(),
            "pickup": data["pickup_location"].lower(),
            "dropoff": data["dropoff_location"].lower(),
        }

        if locations["pickup"] == locations["dropoff"]:
            raise serializers.ValidationError(
                "Pickup and dropoff cannot be the same location."
            )
        if locations["current"] == locations["pickup"]:
            raise serializers.ValidationError(
                "Current location and pickup cannot be the same location."
            )
        if locations["current"] == locations["dropoff"]:
            raise serializers.ValidationError(
                "Current location and dropoff cannot be the same location."
            )

        return data
