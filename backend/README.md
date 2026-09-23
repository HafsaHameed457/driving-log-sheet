# Backend — Driving Log Sheet

Django REST API for HOS-compliant trip planning.

## Local Development

    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env
    # Edit .env to set ORS_API_KEY
    python manage.py migrate
    python manage.py runserver

## Tests

    pytest -v

## Deployment (Render)

1. Create a new Web Service on render.com
2. Point it at this repo, root directory `backend`
3. Build command: `pip install -r requirements.txt && python manage.py migrate`
4. Start command: `gunicorn config.wsgi:application`
5. Environment variables:
   - DEBUG=False
   - SECRET_KEY=<random>
   - ORS_API_KEY=<your key or leave blank if self-hosting ORS>
   - ALLOWED_HOSTS=<your-render-host>.onrender.com,localhost,127.0.0.1
   - CORS_ALLOWED_ORIGINS=https://<your-vercel-app>.vercel.app

## API Endpoints

- `GET /api/health/` — health check
- `GET /api/geocode/?q=<query>` — location autocomplete proxy
- `POST /api/trip/` — full trip planning (returns route, stops, logs)

## Environment Variables

See the root README.md for the full list.