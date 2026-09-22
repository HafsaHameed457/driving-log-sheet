"""Tests for the daily log builder."""

import pytest
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from trips.services.logs import (
    build_daily_logs,
    _split_at_midnight,
    DailyLog,
    LogEvent,
    LogTotals,
    LogRecap,
)
from trips.services.hos_planner import DutyEvent, PlanResult


MIDNIGHT_NEXT = lambda d: datetime(d.year, d.month, d.day) + timedelta(days=1)


# ── helpers ────────────────────────────────────────────────────


def _make_plan_result(events, total_miles=1100.0, total_drive_hrs=20.0):
    return PlanResult(
        stops=[],
        events=events,
        total_miles=total_miles,
        total_drive_hrs=total_drive_hrs,
        trip_start=events[0].start if events else datetime(2026, 10, 1),
        trip_end=events[-1].end if events else datetime(2026, 10, 1),
    )


def _de(*args, **kwargs):
    return DutyEvent(*args, **kwargs)


def _midnight(d):
    return datetime(d.year, d.month, d.day)


# ============================================================
# t1: Single day trip — totals sum to 24hrs
# ============================================================
def test_t1_single_day_trip_24hrs():
    day = datetime(2026, 10, 1)
    events = [
        _de("off_duty", day.replace(hour=0), day.replace(hour=6), "Dallas, TX", "Off duty"),
        _de("driving", day.replace(hour=6), day.replace(hour=14), "Amarillo, TX", "Driving"),
        _de("off_duty", day.replace(hour=14), day.replace(hour=14, minute=30), "Amarillo, TX", "30-min break"),
        _de("driving", day.replace(hour=14, minute=30), day.replace(hour=18), "Oklahoma City, OK", "Driving"),
        _de("on_duty", day.replace(hour=18), day.replace(hour=19), "Oklahoma City, OK", "Pickup"),
        _de("driving", day.replace(hour=19), day.replace(hour=22), "Denver, CO", "Driving"),
        _de("off_duty", day.replace(hour=22), MIDNIGHT_NEXT(day), "Denver, CO", "Off duty"),
    ]

    result = _make_plan_result(events)
    logs = build_daily_logs(result, trip_starting_cycle_hrs=0)

    assert len(logs) == 1
    log = logs[0]
    total = log.totals.off_duty + log.totals.sleeper + log.totals.driving + log.totals.on_duty
    assert abs(total - 24.0) < 0.01, f"Total: {total:.4f}"


# ============================================================
# t2: Overnight split — event crosses midnight
# ============================================================
def test_t2_overnight_split():
    d1 = datetime(2026, 10, 1)
    d2 = datetime(2026, 10, 2)
    events = [
        _de("driving", d1.replace(hour=22), d2.replace(hour=8), "Somewhere, TX", "Driving"),
    ]

    result = _make_plan_result(events, total_miles=550.0, total_drive_hrs=10.0)
    logs = build_daily_logs(result, trip_starting_cycle_hrs=0)

    assert len(logs) == 2

    day1 = logs[0]
    day2 = logs[1]

    assert day1.date == "2026-10-01"
    assert day2.date == "2026-10-02"

    total1 = day1.totals.off_duty + day1.totals.sleeper + day1.totals.driving + day1.totals.on_duty
    total2 = day2.totals.off_duty + day2.totals.sleeper + day2.totals.driving + day2.totals.on_duty
    assert abs(total1 - 24.0) < 0.01, f"Day 1 total: {total1:.4f}"
    assert abs(total2 - 24.0) < 0.01, f"Day 2 total: {total2:.4f}"

    for log in logs:
        for ev in log.events:
            h1, m1 = map(int, ev.start.split(":"))
            h2, m2 = map(int, ev.end.split(":"))
            start_min = h1 * 60 + m1
            end_min = h2 * 60 + m2
            if end_min == 0:
                end_min = 24 * 60
            duration = end_min - start_min
            assert duration > 0, (
                f"Event {ev.status} {ev.start}-{ev.end}: zero duration"
            )


# ============================================================
# t3: Multi-day recap accumulates
# ============================================================
def test_t3_multi_day_recap_accumulates():
    d1 = datetime(2026, 10, 1)
    d2 = datetime(2026, 10, 2)
    d3 = datetime(2026, 10, 3)

    events = [
        _de("off_duty", d1, d1.replace(hour=6), "A", "Off duty"),
        _de("driving", d1.replace(hour=6), d1.replace(hour=16), "B", "Driving"),
        _de("on_duty", d1.replace(hour=16), d1.replace(hour=17), "B", "Dropoff"),
        _de("off_duty", d1.replace(hour=17), MIDNIGHT_NEXT(d1), "B", "Off duty"),
        _de("off_duty", d2, d2.replace(hour=6), "B", "Off duty"),
        _de("driving", d2.replace(hour=6), d2.replace(hour=16), "C", "Driving"),
        _de("on_duty", d2.replace(hour=16), d2.replace(hour=17), "C", "Dropoff"),
        _de("off_duty", d2.replace(hour=17), MIDNIGHT_NEXT(d2), "C", "Off duty"),
        _de("off_duty", d3, d3.replace(hour=6), "C", "Off duty"),
        _de("driving", d3.replace(hour=6), d3.replace(hour=16), "D", "Driving"),
        _de("on_duty", d3.replace(hour=16), d3.replace(hour=17), "D", "Dropoff"),
        _de("off_duty", d3.replace(hour=17), MIDNIGHT_NEXT(d3), "D", "Off duty"),
    ]

    result = _make_plan_result(events, total_miles=1650.0, total_drive_hrs=30.0)
    logs = build_daily_logs(result, trip_starting_cycle_hrs=50.0)

    assert len(logs) == 3

    for log in logs:
        total = log.totals.off_duty + log.totals.sleeper + log.totals.driving + log.totals.on_duty
        assert abs(total - 24.0) < 0.01, f"{log.date} total: {total:.4f}"

    assert logs[0].recap.last_7_days == 50.0
    expected_on_duty_d1 = round(10.0 + 1.0, 2)
    assert abs(logs[0].recap.on_duty_today - expected_on_duty_d1) < 0.01

    assert abs(logs[1].recap.last_7_days - (50.0 + expected_on_duty_d1)) < 0.01

    expected_on_duty_d2 = round(10.0 + 1.0, 2)
    expected_last_7_d3 = round(50.0 + expected_on_duty_d1 + expected_on_duty_d2, 2)
    assert abs(logs[2].recap.last_7_days - expected_last_7_d3) < 0.01

    for log in logs:
        assert log.recap.available_tomorrow == round(max(0.0, 70.0 - log.recap.total_70hr), 2)


# ============================================================
# t4: from_location and to_location
# ============================================================
def test_t4_from_and_to_locations():
    day = datetime(2026, 10, 1)
    events = [
        _de("off_duty", day.replace(hour=0), day.replace(hour=6), "Start, TX", "Off duty"),
        _de("driving", day.replace(hour=6), day.replace(hour=12), "Mid, OK", "Driving"),
        _de("on_duty", day.replace(hour=12), day.replace(hour=13), "Mid, OK", "Pickup"),
        _de("driving", day.replace(hour=13), day.replace(hour=20), "End, CO", "Driving"),
        _de("off_duty", day.replace(hour=20), MIDNIGHT_NEXT(day), "End, CO", "Off duty"),
    ]

    result = _make_plan_result(events)
    logs = build_daily_logs(result, trip_starting_cycle_hrs=0)

    assert len(logs) == 1
    assert logs[0].from_location == "Mid, OK"
    assert logs[0].to_location == "End, CO"


# ============================================================
# t5: total_miles_today
# ============================================================
def test_t5_total_miles_today():
    day = datetime(2026, 10, 1)
    events = [
        _de("off_duty", day.replace(hour=0), day.replace(hour=6), "A", "Off duty"),
        _de("driving", day.replace(hour=6), day.replace(hour=16), "B", "Driving"),
        _de("off_duty", day.replace(hour=16), MIDNIGHT_NEXT(day), "B", "Off duty"),
    ]

    result = _make_plan_result(events, total_miles=1100.0, total_drive_hrs=20.0)
    logs = build_daily_logs(result, trip_starting_cycle_hrs=0)

    assert len(logs) == 1
    assert abs(logs[0].total_miles_today - 550) <= 2


# ============================================================
# t6: Exact 24hr invariant for every day in every test case
# ============================================================
def test_t6_exact_24hr_invariant():
    cases = []

    d = datetime(2026, 10, 1)
    cases.append([
        _de("off_duty", d.replace(hour=0), d.replace(hour=6), "X", "Off duty"),
        _de("driving", d.replace(hour=6), d.replace(hour=10), "Y", "Driving"),
        _de("off_duty", d.replace(hour=10), d.replace(hour=14), "Y", "Off duty"),
        _de("driving", d.replace(hour=14), d.replace(hour=18), "Z", "Driving"),
        _de("off_duty", d.replace(hour=18), MIDNIGHT_NEXT(d), "Z", "Off duty"),
    ])

    d1 = datetime(2026, 10, 1)
    d2 = datetime(2026, 10, 2)
    cases.append([
        _de("off_duty", d1, d1.replace(hour=22), "A", "Off duty"),
        _de("driving", d1.replace(hour=22), d2.replace(hour=8), "B", "Driving"),
        _de("off_duty", d2.replace(hour=8), MIDNIGHT_NEXT(d2), "B", "Off duty"),
    ])

    for events in cases:
        result = _make_plan_result(events)
        logs = build_daily_logs(result, trip_starting_cycle_hrs=0)
        for log in logs:
            total = log.totals.off_duty + log.totals.sleeper + log.totals.driving + log.totals.on_duty
            assert abs(total - 24.0) < 0.001, f"{log.date}: {total:.4f}"
