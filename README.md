# Driving Log Sheet

Plan your route. Generate compliant ELD logs.

A full-stack app (Django + React) that takes trip details as input and produces:
- An interactive map with the route, fuel stops, rest breaks, and pickup/dropoff points
- FMCSA-compliant Driver's Daily Log sheets (one per day), ready to print or save as PDF

## Live Demo

- **Frontend:** <VERCEL_URL>
- **Backend:** <RENDER_URL>

> **Note:** The backend runs on Render's free tier and sleeps after 15 minutes of inactivity. The first request after a sleep may take 30-60 seconds to respond.

## Features

- Route planning via OpenRouteService (self-hosted OR public API)
- HOS engine implementing 11-hr driving limit, 14-hr window, 30-min break after 8 cumulative hours driving, 10-hr off-duty reset, 70-hr/8-day cycle, 34-hr restart
- Automatic fuel stops every 1,000 miles
- 1-hour on-duty pickup and dropoff
- Multi-day trip support with automatic overnight split
- SVG-rendered Driver's Daily Log matching the FMCSA paper form
- Print / Save as PDF support

## HOS Rules Implemented

| Rule | Value |
|---|---|
| Driving limit per shift | 11 hours |
| Driving window | 14 hours |
| Rest break | 30 min after 8 cumulative hours driving |
| Off-duty reset | 10 consecutive hours |
| Cycle limit | 70 hours in 8 days |
| Restart | 34 consecutive hours |
| Fuel | Every 1,000 miles (30 min on-duty) |
| Pickup / Dropoff | 1 hour on-duty each |

See `docs/assumptions.md` for documented simplifications.

## Tech Stack

**Backend:** Django 5 + Django REST Framework, pure-Python HOS engine, OpenRouteService for geocoding and routing
**Frontend:** React + Vite + Tailwind CSS, Leaflet + react-leaflet for maps, hand-built SVG for log sheets
**Deploy:** Vercel (frontend) + Render (backend)

## Project Structure

    .
    ├── backend/                Django REST API + HOS engine
    │   ├── config/             Django settings
    │   └── trips/
    │       ├── services/
    │       │   ├── geo.py              OpenRouteService client
    │       │   ├── hos_planner.py      HOS calculation engine (pure Python)
    │       │   ├── logs.py             Daily log splitter + recap
    │       │   └── errors.py           Custom exception classes
    │       ├── serializers.py
    │       ├── views.py
    │       └── tests/
    ├── frontend/               React + Vite + Tailwind UI
    │   └── src/
    │       ├── components/
    │       │   ├── TripForm.jsx
    │       │   ├── LocationInput.jsx
    │       │   ├── RouteMap.jsx
    │       │   ├── StopIcon.js
    │       │   ├── LogSheet.jsx
    │       │   ├── LogSheetList.jsx
    │       │   ├── TripSummary.jsx
    │       │   ├── EmptyState.jsx
    │       │   └── LoadingSkeleton.jsx
    │       ├── api/
    │       └── utils/
    └── docs/                   FMCSA references, assumptions, screenshots

## Local Setup

### Backend

    cd backend
    python -m venv venv
    source venv/bin/activate         # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env and set your ORS_API_KEY
    python manage.py migrate
    python manage.py runserver
    # Runs at http://localhost:8000

### Frontend

    cd frontend
    npm install
    cp .env.example .env
    # Set VITE_API_URL=http://localhost:8000
    npm run dev
    # Runs at http://localhost:5173

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description | Example |
|---|---|---|
| DEBUG | Django debug mode | False |
| SECRET_KEY | Django secret key | (random string) |
| ORS_API_KEY | OpenRouteService key (not needed if self-hosting) | (key) |
| ALLOWED_HOSTS | Comma-separated allowed hosts | driving-log-sheet.onrender.com,localhost,127.0.0.1 |
| CORS_ALLOWED_ORIGINS | Comma-separated allowed origins | https://your-app.vercel.app |
| ORS_BASE_URL | Optional override for self-hosted ORS | http://localhost:8080/ors |

### Frontend (`frontend/.env`)

| Variable | Description | Example |
|---|---|---|
| VITE_API_URL | Backend base URL | https://driving-log-sheet.onrender.com |

## Testing

Backend tests:

    cd backend
    pytest -v

All HOS planner tests, geo service tests, log builder tests, and API endpoint tests should pass.

## Assumptions

See `docs/assumptions.md` for the full list.

## License

MIT