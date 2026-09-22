# Driving Log Sheet — Frontend

React + Vite + Tailwind UI for planning a truck route and generating FMCSA-compliant daily log sheets.

## Local development

```bash
npm install
npm run dev
```

Dev server runs at `http://localhost:5173` by default.

## Environment variables

Copy `.env.example` to `.env` and set:

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Base URL of the Django API (e.g. `http://localhost:8000` locally, or your deployed backend URL). Falls back to `http://localhost:8000` if unset. |

## Build

```bash
npm run build
```

Outputs static files to `dist/`.

## Deploy to Vercel

1. Push the repository to GitHub.
2. Import the repo on [vercel.com](https://vercel.com).
3. Set the project **root directory** to `frontend`.
4. Set the environment variable `VITE_API_URL` to your deployed backend URL.
5. Deploy.
