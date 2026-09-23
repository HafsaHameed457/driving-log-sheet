# Documented Assumptions

This project makes several deliberate simplifications to keep the HOS engine tractable within the assessment time budget. Each is documented here so reviewers understand what is and is not modeled.

## HOS Rules

- **Property-carrying driver, 70-hour / 8-day cycle.** Passenger-carrying and 60-hour / 7-day cycles are not implemented.
- **No adverse driving conditions exception.** The 2-hour adverse conditions extension is not modeled.
- **No split-sleeper provision.** A 10-hour reset must be taken in one block. The 8+2 and 7+3 splits are not supported.
- **No CDL short-haul exception.** Every trip is treated as if it requires a full log.
- **No 16-hour short-haul exception.**

## Time Handling

- **Single time zone.** All times are in the driver's local time. Time-zone crossings are not modeled.
- **Fixed start time of 06:00 local time.** The HOS planner starts the trip at 06:00 on Day 1.
- **No daylight saving time transitions.**

## Duty Status Conventions

- **10-hour resets** are logged as **Sleeper Berth**.
- **30-minute breaks** are logged as **Off Duty**.
- **Fuel stops** (30 minutes) are logged as **On Duty (not driving)**.
- **Pickup** and **Dropoff** (1 hour each) are logged as **On Duty (not driving)**.

## Speeds and Distances

- **Average speed derived from the routing API's duration and distance.** The HOS engine uses the ORS-provided duration, not a hardcoded speed.
- **1 mile = 1609.344 meters** for unit conversion.
- **Fuel stops every 1,000 miles** (assumption from the assessment brief).

## Routing

- **Driving profile is `driving-hgv` when supported by the ORS instance**, otherwise `driving-car`.
- **Geocoding is limited to the three input locations plus reverse-geocode lookups for stop locations only.** Reverse geocoding is NOT performed for every point on the route.

## Persistence

- **The API is stateless.** No data is stored between requests. SQLite exists only for Django's built-in auth, sessions, admin, and contenttypes tables.

## Data Validation

- **All three locations must be distinct.** This is enforced at the serializer level. A driver cannot pick up and drop off at the same location in a single trip.

## What Is Not Modeled

- Pre-trip inspection time
- Post-trip inspection time
- Loading and unloading time beyond the 1-hour pickup/dropoff allotment
- Traffic delays
- Weather delays
- Road closures
- Weight restrictions
- Hazmat routing
- Hours-of-service exemptions for specific industries