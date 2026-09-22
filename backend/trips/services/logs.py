"""Daily log builder.

Pure Python module — no Django, DRF, or network imports.

Converts the flat event list from the HOS planner into per-day
daily log sheets that match the paper "Drivers Daily Log" form.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .hos_planner import PlanResult


@dataclass
class LogEvent:
    status: str
    start: str
    end: str
    location: str
    remark: str


@dataclass
class LogTotals:
    off_duty: float
    sleeper: float
    driving: float
    on_duty: float


@dataclass
class LogRecap:
    on_duty_today: float
    last_7_days: float
    total_70hr: float
    available_tomorrow: float


@dataclass
class DailyLog:
    date: str
    from_location: str
    to_location: str
    total_miles_today: float
    events: list
    totals: LogTotals
    recap: LogRecap


def _split_at_midnight(events: list) -> dict[str, list]:
    """Split events at midnight boundaries.

    Returns dict keyed by "YYYY-MM-DD" with list of DutyEvent-like dicts.
    """
    day_map: dict[str, list] = defaultdict(list)

    for ev in events:
        current = ev.start
        while current.date() < ev.end.date():
            midnight_next = datetime(
                current.year, current.month, current.day
            ) + timedelta(days=1)
            piece = {
                "status": ev.status,
                "start": current,
                "end": midnight_next,
                "location": ev.location,
                "remark": ev.remark,
            }
            day_key = current.strftime("%Y-%m-%d")
            day_map[day_key].append(piece)
            current = midnight_next

        if ev.end > current:
            day_key = current.strftime("%Y-%m-%d")
            day_map[day_key].append({
                "status": ev.status,
                "start": current,
                "end": ev.end,
                "location": ev.location,
                "remark": ev.remark,
            })

    for key in day_map:
        day_map[key].sort(key=lambda e: e["start"])

    return dict(day_map)


def _fmt_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def _compute_day_miles(driving_hrs: float, avg_speed: float) -> float:
    return round(driving_hrs * avg_speed)


def _compute_totals(day_events: list[dict]) -> LogTotals:
    mins = defaultdict(float)
    for ev in day_events:
        delta = (ev["end"] - ev["start"]).total_seconds() / 60.0
        mins[ev["status"]] += delta

    hours = {k: round(v / 60.0, 2) for k, v in mins.items()}
    return LogTotals(
        off_duty=hours.get("off_duty", 0.0),
        sleeper=hours.get("sleeper", 0.0),
        driving=hours.get("driving", 0.0),
        on_duty=hours.get("on_duty", 0.0),
    )


def _pad_day(day_events: list[dict], day_start: datetime, day_end: datetime) -> list[dict]:
    """Pad day with off_duty events so it sums to exactly 24 hours."""
    if not day_events:
        return [{
            "status": "off_duty",
            "start": day_start,
            "end": day_end,
            "location": "",
            "remark": "Off duty",
        }]

    filled = []
    current = day_start

    for ev in sorted(day_events, key=lambda e: e["start"]):
        if ev["start"] > current:
            filled.append({
                "status": "off_duty",
                "start": current,
                "end": ev["start"],
                "location": ev["location"],
                "remark": "Off duty",
            })
        filled.append(ev)
        current = ev["end"]

    if current < day_end:
        filled.append({
            "status": "off_duty",
            "start": current,
            "end": day_end,
            "location": filled[-1]["location"],
            "remark": "Off duty",
        })

    return filled


def build_daily_logs(
    result: PlanResult,
    trip_starting_cycle_hrs: float,
) -> list[DailyLog]:
    """Build per-day daily logs from a PlanResult.

    Args:
        result: Output of plan_trip().
        trip_starting_cycle_hrs: cycle_used_hrs the user passed in.

    Returns:
        List of DailyLog sorted by date ascending.
    """
    day_map = _split_at_midnight(result.events)

    if not day_map:
        return []

    avg_speed = result.total_miles / result.total_drive_hrs if result.total_drive_hrs > 0 else 55.0

    sorted_days = sorted(day_map.keys())

    daily_logs = []
    running_on_duty = 0.0

    for day_str in sorted_days:
        day_date = datetime.strptime(day_str, "%Y-%m-%d").date()
        day_start = datetime(day_date.year, day_date.month, day_date.day)
        day_end = day_start + timedelta(days=1)

        raw_events = day_map[day_str]
        padded = _pad_day(raw_events, day_start, day_end)

        log_events = []
        for ev in padded:
            log_events.append(LogEvent(
                status=ev["status"],
                start=_fmt_time(ev["start"]),
                end=_fmt_time(ev["end"]),
                location=ev["location"],
                remark=ev["remark"],
            ))

        totals = _compute_totals(padded)

        driving_hrs = totals.driving
        total_miles_today = _compute_day_miles(driving_hrs, avg_speed)

        non_off = [ev for ev in padded if ev["status"] != "off_duty"]
        from_loc = non_off[0]["location"] if non_off else (padded[0]["location"] if padded else "")
        to_loc = non_off[-1]["location"] if non_off else (padded[-1]["location"] if padded else "")

        on_duty_today = round(totals.driving + totals.on_duty, 2)

        last_7_days = round(running_on_duty + trip_starting_cycle_hrs, 2)
        total_70hr = round(last_7_days + on_duty_today, 2)
        available_tomorrow = round(max(0.0, 70.0 - total_70hr), 2)

        recap = LogRecap(
            on_duty_today=on_duty_today,
            last_7_days=last_7_days,
            total_70hr=total_70hr,
            available_tomorrow=available_tomorrow,
        )

        daily_logs.append(DailyLog(
            date=day_str,
            from_location=from_loc,
            to_location=to_loc,
            total_miles_today=total_miles_today,
            events=log_events,
            totals=totals,
            recap=recap,
        ))

        running_on_duty += on_duty_today

    return daily_logs
