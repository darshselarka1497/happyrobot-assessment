# Carrier Sales API — HappyRobot FDE Technical Challenge

## Project Overview
Backend API + dashboard for HappyRobot's inbound carrier sales automation. A HappyRobot voice agent calls these endpoints during carrier conversations to verify carriers, search loads, negotiate pricing, and log call data.

## Tech Stack
- **API**: Python 3.9+ / FastAPI / SQLAlchemy / SQLite
- **Dashboard**: Single-page HTML with Chart.js (served at `/dashboard`)
- **Containerization**: Docker + docker-compose
- **External API**: FMCSA SAFER Web API for MC number verification

## Project Structure
```
api/
  main.py          — FastAPI app entry point, lifespan, CORS, dashboard route
  config.py        — Pydantic settings (env vars: FMCSA_API_KEY, API_KEY, DATABASE_URL)
  auth.py          — X-API-Key header middleware
  database.py      — SQLAlchemy engine, session, Base
  models.py        — ORM models: Load, CallLog, NegotiationSession
  schemas.py       — Pydantic request/response schemas
  seed.py          — Seeds 10 loads from data/loads_seed.json on startup
  routes/
    fmcsa.py       — GET /api/fmcsa/verify/{mc_number}
    loads.py       — GET /api/loads/search, GET /api/loads/{load_id}
    negotiate.py   — POST /api/negotiate (stateful, 3-round max, 110% ceiling)
    calls.py       — POST/GET /api/calls/log, GET /api/calls/metrics
dashboard/
  index.html       — Dark-themed metrics dashboard
data/
  loads_seed.json  — 10 sample freight loads
```

## Live Deployment
- **Render URL**: https://happyrobot-assessment.onrender.com
- **API docs**: https://happyrobot-assessment.onrender.com/docs
- **Dashboard**: https://happyrobot-assessment.onrender.com/dashboard
- **GitHub repo**: https://github.com/darshselarka1497/happyrobot-assessment

## Key Commands
- **Run locally**: `source .venv/bin/activate && uvicorn api.main:app --reload --port 8000`
- **Run with Docker**: `docker compose up --build`
- **API docs (local)**: http://localhost:8000/docs
- **Dashboard (local)**: http://localhost:8000/dashboard

## Conventions
- Python 3.9 compatible — use `Optional[str]` not `str | None`, `List[X]` not `list[X]`, `Dict[K,V]` not `dict[k,v]`
- All API endpoints require `X-API-Key` header (except `/health`)
- Pydantic v2 with `model_config = {"from_attributes": True}` for ORM models
- Environment variables loaded from `.env` file via pydantic-settings

## Negotiation Logic
- Ceiling price = 110% of `loadboard_rate` (max broker will pay)
- Carrier offer ≤ loadboard rate → accept immediately (great deal)
- Carrier offer ≤ 103% of loadboard → accept (close enough)
- Carrier offer within ceiling → counter with midpoint of (carrier_offer + current_offer), capped at ceiling
- Max 3 rounds, then present ceiling as final take-it-or-leave-it

## Environment Variables
- `FMCSA_API_KEY` — from https://mobile.fmcsa.dot.gov/QCDevsite/HomePage
- `API_KEY` — secures all endpoints (default: "changeme")
- `DATABASE_URL` — SQLite connection string (default: sqlite:///./data/carrier_sales.db)

## HappyRobot Platform Integration
The voice agent on HappyRobot calls these deployed API endpoints as "tools" during calls.
Conversation flow: greet → ask MC → verify via FMCSA → ask lanes → search loads → pitch → negotiate (up to 3 rounds) → transfer if agreed → log call.
Use web call trigger for testing (no phone number needed).
Platform docs password: oshappyrobot
