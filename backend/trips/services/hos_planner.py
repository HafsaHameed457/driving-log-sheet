"""HOS (Hours of Service) trip planner.

Pure Python module — no Django, DRF, or network imports.

Rules implemented:
  - Property-carrying driver, 70 hrs / 8 days cycle
  - Driving limit per shift: 11 hours
  - Driving window: 14 hours from start of duty
  - Rest break: 30 min after 8 cumulative hours of driving (since last break)
  - Off-duty reset: 10 consecutive hours (logged as SLEEPER BERTH)
  - Cycle limit: 70 hours on-duty in 8 consecutive days
  - Restart: 34 consecutive hours off duty resets the 70-hr cycle (logged as SLEEPER BERTH)
  - Fuel: at least every 1,000 miles (30 min on-duty stop)
  - Pickup / dropoff: 1 hour on-duty each

Documented assumptions:
  - Trip starts at 06:00 local time on Day 1
  - Single time zone (no TZ math)
  - No split-sleeper provision
  - No pre-trip inspection modeled
  - 10-hour reset is logged as SLEEPER BERTH
  - 34-hour restart is logged as SLEEPER BERTH
  - 30-minute break is logged as OFF DUTY
  - Fuel and pickup/dropoff are logged as ON DUTY (not driving)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable

from .geo import point_at_distance


@dataclass
class Stop:
    type: str            # "pickup" | "dropoff" | "fuel" | "break" | "rest" | "restart"
    lat: float
    lng: float
    label: str
    arrive: datetime
    duration_min: int
    miles_from_start: float


@dataclass
class DutyEvent:
    status: str          # "off_duty" | "sleeper" | "driving" | "on_duty"
    start: datetime
    end: datetime
    location: str
    remark: str


@dataclass
class PlanResult:
    stops: list
    events: list
    total_miles: float
    total_drive_hrs: float
    trip_start: datetime
    trip_end: datetime


def plan_trip(
    route: dict,
    pickup_miles: float,
    dropoff_miles: float,
    cycle_used_hrs: float,
    geometry: list,
    location_lookup: Callable[[float], str],
    start_time: datetime = None,
) -> PlanResult:
    """Plan a trip with HOS compliance.

    Args:
        route: Output of geo.get_route().
        pickup_miles: Cumulative miles from start to pickup.
        dropoff_miles: Cumulative miles from start to dropoff.
        cycle_used_hrs: Hours already on-duty in last 8 days.
        geometry: Route geometry for point_at_distance.
        location_lookup: Callable(miles) -> location label string.
        start_time: Trip start datetime (default: 06:00 on a fixed date).

    Returns:
        PlanResult with stops, events, and summary info.
    """
    if start_time is None:
        start_time = datetime(2026, 10, 1, 6, 0)

    DEFAULT_SPEED_MPH = 55.0

    stops: list[Stop] = []
    events: list[DutyEvent] = []

    clock = start_time
    miles_driven = 0.0
    drive_in_shift = 0.0
    shift_start = clock
    drive_since_break = 0.0
    cycle_used = cycle_used_hrs
    miles_since_fuel = 0.0

    def _loc(miles: float) -> str:
        return location_lookup(miles)

    def _pos(miles: float) -> dict:
        return point_at_distance(geometry, miles)

    def _advance_clock(hours: float) -> None:
        nonlocal clock
        clock += timedelta(hours=hours)

    def _add_event(status: str, start: datetime, end: datetime,
                   location: str, remark: str) -> None:
        if events and events[-1].status == status and events[-1].end == start:
            events[-1].end = end
        else:
            events.append(DutyEvent(
                status=status, start=start, end=end,
                location=location, remark=remark,
            ))

    def _driving_time_for_distance(miles: float) -> float:
        return miles / DEFAULT_SPEED_MPH

    # --- mission segments ---
    segments = [
        (0.0, pickup_miles, "pickup"),
        (pickup_miles, dropoff_miles, "dropoff"),
    ]

    for seg_start, seg_end, endpoint_type in segments:
        while miles_driven < seg_end:
            remaining_to_waypoint = seg_end - miles_driven

            drive_budget_11 = 11.0 - drive_in_shift
            window_remaining = 14.0 - (clock - shift_start).total_seconds() / 3600.0
            break_budget = 8.0 - drive_since_break
            fuel_remaining = max(0.0, 1000.0 - miles_since_fuel)
            cycle_remaining = max(0.0, 70.0 - cycle_used)

            candidates: list[tuple[float, str]] = []

            candidates.append((remaining_to_waypoint, "waypoint"))
            candidates.append((fuel_remaining, "fuel"))

            if break_budget > 0:
                candidates.append((break_budget * DEFAULT_SPEED_MPH, "break"))
            else:
                candidates.append((0.0, "break"))

            if drive_budget_11 > 0:
                candidates.append((drive_budget_11 * DEFAULT_SPEED_MPH, "limit_11"))
            else:
                candidates.append((0.0, "limit_11"))

            if window_remaining > 0:
                candidates.append((window_remaining * DEFAULT_SPEED_MPH, "limit_14"))
            else:
                candidates.append((0.0, "limit_14"))

            if cycle_remaining > 0:
                candidates.append((cycle_remaining * DEFAULT_SPEED_MPH, "cycle"))
            else:
                candidates.append((0.0, "cycle"))

            candidates = [(m, r) for m, r in candidates if m >= 0]
            if not candidates:
                candidates.append((remaining_to_waypoint, "waypoint"))

            miles_to_drive, reason = min(candidates, key=lambda x: x[0])
            miles_to_drive = max(0.0, miles_to_drive)

            if reason == "waypoint" and miles_to_drive == 0:
                miles_to_drive = min(remaining_to_waypoint, 0.001)
                reason = "waypoint"

            drive_hrs = _driving_time_for_distance(miles_to_drive)
            event_start = clock

            _advance_clock(drive_hrs)
            miles_driven += miles_to_drive
            miles_since_fuel += miles_to_drive
            drive_in_shift += drive_hrs
            drive_since_break += drive_hrs
            cycle_used += drive_hrs

            _add_event("driving", event_start, clock, _loc(miles_driven), "Driving")

            if reason == "waypoint":
                stop_duration = 60
                stop_type = endpoint_type
                stop_label = _loc(miles_driven)
                pos = _pos(miles_driven)

                cycle_used += stop_duration / 60.0

                stop = Stop(
                    type=stop_type, lat=pos["lat"], lng=pos["lng"],
                    label=stop_label, arrive=clock,
                    duration_min=stop_duration, miles_from_start=miles_driven,
                )
                stops.append(stop)

                _add_event("on_duty", clock, clock + timedelta(minutes=stop_duration),
                           stop_label, stop_type.capitalize())
                _advance_clock(stop_duration / 60.0)

                if endpoint_type == "dropoff":
                    break

            elif reason == "fuel":
                stop_duration = 30
                pos = _pos(miles_driven)
                label = _loc(miles_driven)

                cycle_used += stop_duration / 60.0
                miles_since_fuel = 0.0

                stop = Stop(
                    type="fuel", lat=pos["lat"], lng=pos["lng"],
                    label=label, arrive=clock,
                    duration_min=stop_duration, miles_from_start=miles_driven,
                )
                stops.append(stop)

                _add_event("on_duty", clock, clock + timedelta(minutes=stop_duration),
                           label, "Fueling")
                _advance_clock(stop_duration / 60.0)

            elif reason == "break":
                stop_duration = 30
                pos = _pos(miles_driven)
                label = _loc(miles_driven)

                stop = Stop(
                    type="break", lat=pos["lat"], lng=pos["lng"],
                    label=label, arrive=clock,
                    duration_min=stop_duration, miles_from_start=miles_driven,
                )
                stops.append(stop)

                _add_event("off_duty", clock, clock + timedelta(minutes=stop_duration),
                           label, "30-min break")
                _advance_clock(stop_duration / 60.0)
                drive_since_break = 0.0

            elif reason == "limit_11":
                stop_duration = 600
                pos = _pos(miles_driven)
                label = _loc(miles_driven)

                stop = Stop(
                    type="rest", lat=pos["lat"], lng=pos["lng"],
                    label=label, arrive=clock,
                    duration_min=stop_duration, miles_from_start=miles_driven,
                )
                stops.append(stop)

                _add_event("sleeper", clock, clock + timedelta(minutes=stop_duration),
                           label, "10-hr reset")
                _advance_clock(stop_duration / 60.0)
                drive_in_shift = 0.0
                drive_since_break = 0.0
                shift_start = clock

            elif reason == "limit_14":
                stop_duration = 600
                pos = _pos(miles_driven)
                label = _loc(miles_driven)

                stop = Stop(
                    type="rest", lat=pos["lat"], lng=pos["lng"],
                    label=label, arrive=clock,
                    duration_min=stop_duration, miles_from_start=miles_driven,
                )
                stops.append(stop)

                _add_event("sleeper", clock, clock + timedelta(minutes=stop_duration),
                           label, "10-hr reset")
                _advance_clock(stop_duration / 60.0)
                drive_in_shift = 0.0
                drive_since_break = 0.0
                shift_start = clock

            elif reason == "cycle":
                stop_duration = 2040
                pos = _pos(miles_driven)
                label = _loc(miles_driven)

                stop = Stop(
                    type="restart", lat=pos["lat"], lng=pos["lng"],
                    label=label, arrive=clock,
                    duration_min=stop_duration, miles_from_start=miles_driven,
                )
                stops.append(stop)

                _add_event("sleeper", clock, clock + timedelta(minutes=stop_duration),
                           label, "34-hr restart")
                _advance_clock(stop_duration / 60.0)
                drive_in_shift = 0.0
                drive_since_break = 0.0
                cycle_used = 0.0
                shift_start = clock

    _fill_off_duty_gaps(events)

    total_drive_hrs = sum(
        (e.end - e.start).total_seconds() / 3600.0
        for e in events if e.status == "driving"
    )

    return PlanResult(
        stops=stops,
        events=events,
        total_miles=route.get("total_miles", miles_driven),
        total_drive_hrs=total_drive_hrs,
        trip_start=start_time,
        trip_end=clock,
    )


def _fill_off_duty_gaps(events: list[DutyEvent]) -> None:
    """Insert off_duty events to fill gaps so each duty day totals 24 hours.

    Fills from midnight of first day through midnight of last duty day.
    """
    if not events:
        return

    events.sort(key=lambda e: e.start)

    first_day = events[0].start.date()
    last_duty_day = None
    for e in reversed(events):
        if e.status in ("driving", "on_duty", "sleeper"):
            last_duty_day = e.start.date()
            break
    if last_duty_day is None:
        last_duty_day = events[-1].start.date()

    end_of_span = datetime(
        last_duty_day.year, last_duty_day.month, last_duty_day.day
    ) + timedelta(days=1)

    filled = []
    current = datetime(first_day.year, first_day.month, first_day.day)

    for ev in events:
        if ev.start > current:
            filled.append(DutyEvent(
                status="off_duty", start=current, end=ev.start,
                location=ev.location, remark="Off duty",
            ))
        filled.append(ev)
        current = ev.end

    if current < end_of_span:
        filled.append(DutyEvent(
            status="off_duty", start=current, end=end_of_span,
            location=filled[-1].location, remark="Off duty",
        ))

    events.clear()
    events.extend(filled)
