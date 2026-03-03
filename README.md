# Carrier Sales API

Backend API + metrics dashboard for HappyRobot's inbound carrier sales automation. A HappyRobot voice agent calls these endpoints during carrier conversations to verify carriers, search loads, negotiate pricing, and log call data.

## Live Deployment

- **API**: https://happyrobot-assessment.onrender.com
- **API docs (Swagger)**: https://happyrobot-assessment.onrender.com/docs
- **Dashboard**: https://happyrobot-assessment.onrender.com/dashboard
- **Health check**: https://happyrobot-assessment.onrender.com/health
- **GitHub repo**: https://github.com/darshselarka1497/happyrobot-assessment

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API Framework | Python 3.9+ / FastAPI |
| ORM / Database | SQLAlchemy 2.0 / SQLite |
| HTTP Client | httpx (async, for FMCSA API) |
| Validation | Pydantic v2 + pydantic-settings |
| Dashboard | Single-page HTML + Chart.js |
| Containerization | Docker + docker-compose |
| Deployment | Render (auto-deploy from GitHub) |
| External API | FMCSA SAFER Web API |

## Features

- **FMCSA Carrier Verification** — Validate MC numbers against the FMCSA database (with fallback when API is unavailable)
- **Load Search** — Search available loads by origin, destination, equipment type, rate, and weight
- **Negotiation Engine** — Stateful counter-offer logic with ceiling price (110% of loadboard rate) and max 3 rounds
- **Call Logging** — Record call outcomes, sentiment, agreed rates, and extracted data
- **Metrics Dashboard** — Visual dashboard at `/dashboard` with KPIs, charts, and call history
- **API Key Authentication** — All API endpoints secured with `X-API-Key` header
- **HTTPS** — TLS provided by Render (Let's Encrypt) in production
- **Docker** — Fully containerized with Dockerfile and docker-compose

## Project Structure

```
api/
  main.py              — FastAPI app entry point, lifespan, CORS, dashboard route
  config.py            — Pydantic settings (env vars: FMCSA_API_KEY, API_KEY, DATABASE_URL)
  auth.py              — X-API-Key header authentication dependency
  database.py          — SQLAlchemy engine, session factory, Base
  models.py            — ORM models: Load, CallLog, NegotiationSession
  schemas.py           — Pydantic request/response schemas
  seed.py              — Seeds 10 loads from data/loads_seed.json on startup
  routes/
    fmcsa.py           — GET /api/fmcsa/verify/{mc_number}
    loads.py           — GET /api/loads/search, GET /api/loads/{load_id}
    negotiate.py       — POST /api/negotiate (stateful, 3-round max, 110% ceiling)
    calls.py           — POST/GET /api/calls/log, GET /api/calls/metrics
dashboard/
  index.html           — Dark-themed metrics dashboard (Chart.js)
data/
  loads_seed.json      — 10 sample freight loads
docs/
  IMPLEMENTATION_GUIDE.md — HappyRobot platform setup guide
Dockerfile             — Production container image
docker-compose.yml     — Local dev orchestration
requirements.txt       — Python dependencies
```

## Security

### API Key Authentication

All API endpoints are protected with API key authentication via the `X-API-Key` header. Requests without a valid key receive a `401 Unauthorized` response.

| Endpoint | Auth Required |
|----------|:------------:|
| `GET /health` | No (health checks for monitoring) |
| `GET /dashboard` | No (static HTML; dashboard calls authenticated API endpoints) |
| All `/api/*` endpoints | **Yes** — `X-API-Key` header required |

The API key is configured via the `API_KEY` environment variable. See [Environment Variables](#environment-variables) below.

### HTTPS

- **Production (Render)**: TLS is automatically provided by Render via Let's Encrypt.
- **Local development**: Runs over HTTP on `localhost:8000`. Use a reverse proxy or self-signed cert if HTTPS is needed locally.

## Quick Start

### 1. Clone and configure

```bash
git clone git@github.com:darshselarka1497/happyrobot-assessment.git
cd happyrobot-assessment
cp .env.example .env
# Edit .env with your values (see Environment Variables below)
```

### 2. Run with Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

### 3. Run locally (without Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

## Environment Variables

Configure these in your `.env` file (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `FMCSA_API_KEY` | API key from [FMCSA QC Portal](https://mobile.fmcsa.dot.gov/QCDevsite/HomePage) | `""` (fallback mode) |
| `API_KEY` | Secures all `/api/*` endpoints via `X-API-Key` header | `"changeme"` |
| `DATABASE_URL` | SQLite connection string | `sqlite:///./data/carrier_sales.db` |

## API Endpoints

All `/api/*` endpoints require the `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/api/fmcsa/verify/{mc_number}` | Verify carrier MC number via FMCSA |
| GET | `/api/loads/search` | Search loads (query params: origin, destination, equipment_type, min_rate, max_rate, max_weight) |
| GET | `/api/loads/{load_id}` | Get a specific load by ID |
| POST | `/api/negotiate` | Submit/evaluate a carrier counter-offer |
| POST | `/api/calls/log` | Log call data (outcome, sentiment, rates) |
| GET | `/api/calls/log` | List call logs with optional filters |
| GET | `/api/calls/metrics` | Aggregated metrics for dashboard |
| GET | `/dashboard` | Metrics dashboard UI |
| GET | `/docs` | Interactive API docs (Swagger) |

## HappyRobot Platform Integration

The HappyRobot voice agent calls these deployed endpoints as "tools" during carrier conversations. The conversation flow:

```
Greet carrier → Ask MC number → Verify via FMCSA → Ask preferred lanes
→ Search loads → Pitch load details → Negotiate (up to 3 rounds)
→ Transfer to sales rep if agreed → Log call data
```

### Tool Endpoints

1. **Verify Carrier** → `GET /api/fmcsa/verify/{mc_number}`
2. **Search Loads** → `GET /api/loads/search?origin=X&destination=Y&equipment_type=Z`
3. **Negotiate** → `POST /api/negotiate` with body `{"call_id": "...", "load_id": "...", "carrier_offer": 2400}`
4. **Log Call** → `POST /api/calls/log` (called after call ends via webhook)

See `docs/IMPLEMENTATION_GUIDE.md` for the full step-by-step platform setup.

## Negotiation Logic

Carriers negotiate **up** (they want more than the loadboard rate). The broker negotiates **down**.

- Ceiling price: **110%** of `loadboard_rate` (max the broker will pay)
- Carrier offer ≤ loadboard rate → **accept immediately** (great deal for broker)
- Carrier offer ≤ 103% of loadboard rate → **accept** (close enough)
- Carrier offer within ceiling → **counter** with midpoint of (carrier offer + broker's current offer)
- Counter never exceeds ceiling price
- After 3 rounds → present ceiling as final take-it-or-leave-it offer

## Deployment

Deployed on **Render** using Docker. HTTPS is provided automatically via Let's Encrypt.

### Reproduce on Render

1. Fork/clone this repo
2. Create a new **Web Service** on [render.com](https://render.com) connected to the GitHub repo
3. Render auto-detects the `Dockerfile`
4. Set environment variables: `FMCSA_API_KEY`, `API_KEY`
5. Deploy — the service will be available at your Render URL with HTTPS enabled

### Run locally with Docker

```bash
git clone git@github.com:darshselarka1497/happyrobot-assessment.git
cd happyrobot-assessment
cp .env.example .env
# Edit .env
docker compose up --build
```

## Dashboard

The metrics dashboard is served at `/dashboard` and provides:

- **Total calls** and **booking rate** KPIs
- **Outcome breakdown** — booked, no match, price rejected, carrier ineligible, call dropped, transferred
- **Sentiment analysis** — positive, neutral, negative
- **Average negotiation rounds** and **rate discount percentage**
- **Calls over time** trend chart
- **Recent call log** table

The dashboard fetches data from `GET /api/calls/metrics` and `GET /api/calls/log` (both require the API key).
