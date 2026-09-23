# Frontend — Driving Log Sheet

React + Vite + Tailwind UI for the Driving Log Sheet app.

## Local Development

    npm install
    cp .env.example .env
    # Set VITE_API_URL=http://localhost:8000
    npm run dev

## Build

    npm run build

## Deployment (Vercel)

1. Import this repo on vercel.com
2. Set the **Root Directory** to `frontend`
3. Framework preset: Vite
4. Environment variable:
   - VITE_API_URL=https://<your-render-host>.onrender.com
5. Deploy

## Component Overview

- `TripForm` — trip input form with autocomplete
- `LocationInput` — debounced geocode autocomplete input
- `RouteMap` — Leaflet map with color-coded stop markers
- `StopIcon` — SVG marker factory per stop type
- `TripSummary` — sidebar summary of total miles, hours, stops, days
- `LogSheet` — SVG Driver's Daily Log matching the FMCSA paper form
- `LogSheetList` — list of log sheets with print button
- `EmptyState` — placeholder before a trip is planned
- `LoadingSkeleton` — pulsing placeholder during loading