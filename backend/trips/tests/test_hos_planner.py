"""Tests for the HOS trip planner."""

import pytest
from datetime import datetime, timedelta
from collections import defaultdict

from trips.services.hos_planner import plan_trip, Stop, DutyEvent, PlanResult
from trips.services.geo import point_at_distance


DEFAULT_SPEED_MPH = 55.0
START = datetime(2026, 10, 1, 6, 0)

stub_location = lambda m: f"Mile {m:.0f}"


def _make_route(total_miles: float, geometry: list = None) -> dict:
    if geometry is None:
        geometry = [[32.0, -96.0], [35.0, -97.0], [39.0, -104.0]]
    return {
        "total_miles": total_miles,
        "total_duration_hrs": total_miles / DEFAULT_SPEED_MPH,
        "geometry": geometry,
        "legs": [
            {"from_index": 0, "to_index": 1, "miles": total_miles * 0.4,
             "duration_hrs": (total_miles * 0.4) / DEFAULT_SPEED_MPH,
             "end_distance_from_start_mi": total_miles * 0.4},
            {"from_index": 1, "to_index": 2, "miles": total_miles * 0.6,
             "duration_hrs": (total_miles * 0.6) / DEFAULT_SPEED_MPH,
             "end_distance_from_start_mi": total_miles},
        ],
    }


def _drive_hours(result: PlanResult) -> float:
    return sum(
        (e.end - e.start).total_seconds() / 3600.0
        for e in result.events if e.status == "driving"
    )


def _events_on_day(events: list[DutyEvent], day: datetime.date) -> list[DutyEvent]:
    out = []
    for e in events:
        if e.start.date() == day or e.end.date() == day:
            out.append(e)
    return out


def _event_hours_in_day(event: DutyEvent, day: datetime.date) -> float:
    day_start = datetime(day.year, day.month, day.day)
    day_end = day_start + timedelta(days=1)
    s = max(event.start, day_start)
    e = min(event.end, day_end)
    if e <= s:
        return 0.0
    return (e - s).total_seconds() / 3600.0


# ============================================================
# t1: Short trip — no break needed
# ============================================================
def test_t1_short_trip_no_break():
    miles = 300.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    drive_hrs = _drive_hours(result)
    assert drive_hrs < 8.0

    breaks = [s for s in result.stops if s.type == "break"]
    rests = [s for s in result.stops if s.type in ("rest", "restart")]
    assert len(breaks) == 0
    assert len(rests) == 0

    pickups = [s for s in result.stops if s.type == "pickup"]
    dropoffs = [s for s in result.stops if s.type == "dropoff"]
    assert len(pickups) == 1
    assert len(dropoffs) == 1

    drive_events = [e for e in result.events if e.status == "driving"]
    assert len(drive_events) == 2


# ============================================================
# t2: Break inserted at 8 hrs driving
# ============================================================
def test_t2_eight_hour_break_inserted():
    miles = 550.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    breaks = [s for s in result.stops if s.type == "break"]
    assert len(breaks) == 1
    assert breaks[0].duration_min == 30

    rests = [s for s in result.stops if s.type in ("rest", "restart")]
    assert len(rests) == 0

    drive_hrs = _drive_hours(result)
    assert drive_hrs < 11.0


# ============================================================
# t3: 11-hr limit triggers rest
# ============================================================
def test_t3_eleven_hour_limit_rest_inserted():
    miles = 800.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    breaks = [s for s in result.stops if s.type == "break"]
    rests = [s for s in result.stops if s.type == "rest"]
    assert len(breaks) >= 1
    assert len(rests) >= 1

    rest_stop = rests[0]
    assert rest_stop.duration_min == 600


# ============================================================
# t4: No day exceeds 11 driving hrs or 14 hr window
# ============================================================
def test_t4_two_day_trip_no_day_over_11_driving_hours():
    miles = 1200.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    all_days = set()
    for e in result.events:
        all_days.add(e.start.date())
        all_days.add(e.end.date())

    for day in sorted(all_days):
        day_drive = sum(
            _event_hours_in_day(e, day)
            for e in result.events if e.status == "driving"
        )
        assert day_drive <= 11.0 + 1e-6, f"Day {day}: {day_drive:.2f} driving hrs"

    shift_groups = []
    current_group = []
    for e in result.events:
        if e.status in ("sleeper",) and ("reset" in e.remark.lower() or "restart" in e.remark.lower()):
            if current_group:
                shift_groups.append(current_group)
                current_group = []
        elif e.status in ("driving", "on_duty"):
            current_group.append(e)
    if current_group:
        shift_groups.append(current_group)

    for group in shift_groups:
        if len(group) >= 2:
            shift_start = group[0].start
            shift_end = group[-1].end
            window_hrs = (shift_end - shift_start).total_seconds() / 3600.0
            assert window_hrs <= 14.0 + 1e-6, f"Window: {window_hrs:.2f} hrs"


# ============================================================
# t5: Fuel stops every 1000 miles
# ============================================================
def test_t5_fuel_stop_every_1000_miles():
    miles = 2500.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    fuel_stops = [s for s in result.stops if s.type == "fuel"]
    assert len(fuel_stops) >= 2

    sorted_fuel = sorted(fuel_stops, key=lambda s: s.miles_from_start)
    for i in range(len(sorted_fuel) - 1):
        gap = sorted_fuel[i + 1].miles_from_start - sorted_fuel[i].miles_from_start
        assert gap <= 1000.0 + 1e-6, f"Fuel gap: {gap:.1f} mi"


# ============================================================
# t6: Cycle limit triggers restart
# ============================================================
def test_t6_cycle_used_near_limit_triggers_restart():
    miles = 500.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=65.0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    restarts = [s for s in result.stops if s.type == "restart"]
    assert len(restarts) >= 1
    assert restarts[0].duration_min == 2040

    cycle_limit = 70.0
    for i, e in enumerate(result.events):
        if e.status == "driving":
            driving_before = sum(
                (ev.end - ev.start).total_seconds() / 3600.0
                for ev in result.events[:i] if ev.status == "driving"
            )
            on_duty_before = sum(
                (ev.end - ev.start).total_seconds() / 3600.0
                for ev in result.events[:i]
                if ev.status in ("driving", "on_duty")
            )
            if on_duty_before >= cycle_limit:
                restarts_before = [
                    ev for ev in result.events[:i]
                    if ev.status == "sleeper" and "restart" in ev.remark.lower()
                ]
                assert len(restarts_before) > 0, "Driving after 70hr without restart"


# ============================================================
# t7: Every day totals 24 hours
# ============================================================
def test_t7_every_day_totals_24_hours():
    miles = 1500.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    duty_days = set()
    for e in result.events:
        if e.status in ("driving", "on_duty", "sleeper"):
            duty_days.add(e.start.date())
            duty_days.add(e.end.date())

    for day in sorted(duty_days):
        total = sum(_event_hours_in_day(e, day) for e in result.events)
        assert abs(total - 24.0) < 1.0, f"Day {day}: {total:.4f} hrs (expected 24)"


# ============================================================
# t8: No overlapping events
# ============================================================
def test_t8_no_overlapping_events():
    miles = 1500.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    sorted_events = sorted(result.events, key=lambda e: e.start)
    for i in range(len(sorted_events)):
        assert sorted_events[i].end >= sorted_events[i].start, (
            f"Event {i} ends before start"
        )
        if i < len(sorted_events) - 1:
            assert sorted_events[i].end <= sorted_events[i + 1].start + timedelta(seconds=1), (
                f"Events {i} and {i+1} overlap"
            )


# ============================================================
# t9: Pickup and dropoff are 1-hour on-duty
# ============================================================
def test_t9_pickup_and_dropoff_are_one_hour_on_duty():
    miles = 1500.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    pickup_stop = next(s for s in result.stops if s.type == "pickup")
    dropoff_stop = next(s for s in result.stops if s.type == "dropoff")

    assert pickup_stop.duration_min == 60
    assert dropoff_stop.duration_min == 60

    for stop in [pickup_stop, dropoff_stop]:
        covering = [
            e for e in result.events
            if e.start <= stop.arrive and e.end >= stop.arrive + timedelta(minutes=stop.duration_min)
            and e.status == "on_duty"
        ]
        assert len(covering) >= 1, f"No on_duty event covers {stop.type}"


# ============================================================
# t10: Stop count matches expectation
# ============================================================
def test_t10_stop_count_matches_expectation():
    miles = 1500.0
    route = _make_route(miles)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=route["geometry"],
        location_lookup=stub_location, start_time=START,
    )

    type_counts = defaultdict(int)
    for s in result.stops:
        type_counts[s.type] += 1

    assert type_counts["pickup"] == 1
    assert type_counts["dropoff"] == 1
    assert type_counts["fuel"] >= 1

    drive_hrs = _drive_hours(result)
    if drive_hrs > 8.0:
        assert type_counts["break"] >= 1
    if drive_hrs > 11.0:
        assert type_counts["rest"] >= 1


# ============================================================
# Regression A: No break immediately after coincident fuel stop
# ============================================================
def test_no_break_immediately_after_coincident_fuel():
    geometry = [[0, 0], [0, 1]]
    route = _make_route(1600.0, geometry=geometry)

    result = plan_trip(
        route=route, pickup_miles=500.0, dropoff_miles=1600.0,
        cycle_used_hrs=0, geometry=geometry,
        location_lookup=lambda m: f"Mile {m:.0f}", start_time=START,
    )

    fuel_stops = [s for s in result.stops if s.type == "fuel"]
    break_stops = [s for s in result.stops if s.type == "break"]
    assert len(fuel_stops) >= 1

    for fuel in fuel_stops:
        for brk in break_stops:
            gap = abs(brk.miles_from_start - fuel.miles_from_start)
            assert gap >= 1.0, (
                f"Break at mile {brk.miles_from_start:.2f} within 1 mi of "
                f"fuel stop at mile {fuel.miles_from_start:.2f}"
            )


# ============================================================
# Regression B: Last duty day pads to midnight when event crosses midnight
# ============================================================
def test_last_day_pads_to_midnight_when_event_crosses_midnight():
    geometry = [[0, 0], [0, 1]]
    # Total drive ~15.82h; 11-hr rest shifts the finish so final on-duty
    # crosses midnight (day 2 ends after 00:00 on day 3).
    miles = 870.0
    route = _make_route(miles, geometry=geometry)
    pickup_mi = miles * 0.4
    dropoff_mi = miles

    start_time = datetime(2026, 10, 1, 6, 0)
    result = plan_trip(
        route=route, pickup_miles=pickup_mi, dropoff_miles=dropoff_mi,
        cycle_used_hrs=0, geometry=geometry,
        location_lookup=lambda m: f"Mile {m:.0f}", start_time=start_time,
    )

    # Find a calendar day whose last event ends after midnight
    days_with_post_midnight_end = set()
    for e in result.events:
        if e.end.date() != e.start.date():
            days_with_post_midnight_end.add(e.start.date())
    assert days_with_post_midnight_end, (
        "Expected at least one duty event crossing midnight"
    )

    all_days = set()
    for e in result.events:
        all_days.add(e.start.date())
        all_days.add(e.end.date())

    for day in sorted(all_days):
        total = sum(_event_hours_in_day(e, day) for e in result.events)
        assert abs(total - 24.0) <= 1.0 / 3600.0, (
            f"Day {day}: {total * 3600:.3f} sec (expected 86400)"
        )
