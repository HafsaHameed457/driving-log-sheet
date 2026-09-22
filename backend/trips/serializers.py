from rest_framework import serializers


# ── Input ──────────────────────────────────────────────────────


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


# ── Output ─────────────────────────────────────────────────────


class StopSerializer(serializers.Serializer):
    type = serializers.CharField()
    lat = serializers.FloatField()
    lng = serializers.FloatField()
    label = serializers.CharField()
    arrive = serializers.DateTimeField(format="%Y-%m-%dT%H:%M")
    duration_min = serializers.IntegerField()
    miles_from_start = serializers.FloatField()


class LogEventSerializer(serializers.Serializer):
    status = serializers.CharField()
    start = serializers.CharField()
    end = serializers.CharField()
    location = serializers.CharField()
    remark = serializers.CharField()


class LogTotalsSerializer(serializers.Serializer):
    off_duty = serializers.FloatField()
    sleeper = serializers.FloatField()
    driving = serializers.FloatField()
    on_duty = serializers.FloatField()


class LogRecapSerializer(serializers.Serializer):
    on_duty_today = serializers.FloatField()
    last_7_days = serializers.FloatField()
    total_70hr = serializers.FloatField()
    available_tomorrow = serializers.FloatField()


class DailyLogSerializer(serializers.Serializer):
    date = serializers.CharField()
    from_location = serializers.CharField()
    to_location = serializers.CharField()
    total_miles_today = serializers.FloatField()
    events = LogEventSerializer(many=True)
    totals = LogTotalsSerializer()
    recap = LogRecapSerializer()


class RouteSerializer(serializers.Serializer):
    total_miles = serializers.FloatField()
    total_drive_hrs = serializers.FloatField()
    geometry = serializers.ListField(child=serializers.ListField(child=serializers.FloatField()))


class TripResponseSerializer(serializers.Serializer):
    route = RouteSerializer()
    stops = StopSerializer(many=True)
    logs = DailyLogSerializer(many=True)
