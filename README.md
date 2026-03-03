# Carrier Sales API

Backend API + metrics dashboard for HappyRobot's inbound carrier sales automation. A voice agent calls these endpoints to verify carriers, search loads, negotiate pricing, and log call data.

## Live Deployment

- **API**: https://happyrobot-assessment.onrender.com
- **Swagger docs**: https://happyrobot-assessment.onrender.com/docs
- **Dashboard**: https://happyrobot-assessment.onrender.com/dashboard

## Tech Stack

Python 3.9+ / FastAPI / SQLAlchemy / SQLite / Pydantic v2 / httpx / Docker / Chart.js

## Quick Start

```bash
git clone git@github.com:darshselarka1497/happyrobot-assessment.git
cd happyrobot-assessment
cp .env.example .env   # then edit with your values
docker compose up --build
```

Or without Docker:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FMCSA_API_KEY` | Key from [FMCSA QC Portal](https://mobile.fmcsa.dot.gov/QCDevsite/HomePage) | `""` (fallback mode) |
| `API_KEY` | Secures all `/api/*` endpoints via `X-API-Key` header | `"changeme"` |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./data/carrier_sales.db` |

## API Endpoints

All `/api/*` endpoints require the `X-API-Key` header. `/health` and `/dashboard` are public.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/fmcsa/verify/{mc_number}` | Verify carrier via FMCSA |
| GET | `/api/loads/search` | Search loads (origin, destination, equipment_type, min/max_rate, max_weight) |
| GET | `/api/loads/{load_id}` | Get load by ID |
| POST | `/api/negotiate` | Carrier counter-offer evaluation |
| POST | `/api/calls/log` | Log call data |
| GET | `/api/calls/log` | List call logs |
| GET | `/api/calls/metrics` | Aggregated metrics |
| GET | `/dashboard` | Metrics dashboard UI |

## Security

- **API Key Auth**: All `/api/*` endpoints require `X-API-Key` header. Returns `401` if missing or invalid.
- **HTTPS**: TLS provided automatically by Render (Let's Encrypt) in production.

## HappyRobot Platform Integration

The voice agent calls these endpoints as "tools" during carrier conversations:

```
Greet → Ask MC → Verify (FMCSA) → Ask lanes → Search loads → Pitch
→ Negotiate (up to 3 rounds) → Transfer if agreed → Log call
```

## Negotiation Logic

Carriers negotiate **up**; the broker negotiates **down**.

- Ceiling: **110%** of `loadboard_rate`
- Offer ≤ loadboard rate → **accept** (great deal)
- Offer ≤ 103% → **accept** (close enough)
- Offer within ceiling → **counter** with midpoint, capped at ceiling
- After 3 rounds → ceiling as final take-it-or-leave-it

## Dashboard

Served at `/dashboard` — dark-themed metrics UI with:

- Total calls, booking rate, outcome & sentiment breakdowns
- Average negotiation rounds and rate discount %
- Calls over time trend chart and recent call log table

## Deployment (Render)

1. Fork this repo
2. Create a **Web Service** on [render.com](https://render.com) linked to the repo
3. Render auto-detects the `Dockerfile`
4. Set env vars: `FMCSA_API_KEY`, `API_KEY`
5. Deploy — HTTPS is enabled automatically

## Project Structure

```
api/
  main.py          — App entry point, lifespan, CORS
  config.py        — Environment settings
  auth.py          — API key authentication
  database.py      — SQLAlchemy engine & session
  models.py        — ORM models (Load, CallLog, NegotiationSession)
  schemas.py       — Pydantic schemas
  seed.py          — Seed data loader
  routes/
    fmcsa.py       — Carrier verification
    loads.py       — Load search & retrieval
    negotiate.py   — Negotiation engine
    calls.py       — Call logging & metrics
dashboard/
  index.html       — Metrics dashboard
data/
  loads_seed.json  — Sample freight loads
```
