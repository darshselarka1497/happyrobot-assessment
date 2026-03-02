# Carrier Sales API

Backend API for HappyRobot inbound carrier sales automation. This service provides the external endpoints that the HappyRobot voice agent calls during carrier conversations.

## Live Deployment

- **API**: https://happyrobot-assessment.onrender.com
- **Health check**: https://happyrobot-assessment.onrender.com/health
- **API docs (Swagger)**: https://happyrobot-assessment.onrender.com/docs
- **Dashboard**: https://happyrobot-assessment.onrender.com/dashboard

## Features

- **FMCSA Carrier Verification** — Validate MC numbers against the FMCSA database (with fallback when API is unavailable)
- **Load Search** — Search available loads by origin, destination, equipment type, rate, and weight
- **Negotiation Engine** — Stateful counter-offer logic with configurable floor price (90% of loadboard rate) and max 3 rounds
- **Call Logging** — Record call outcomes, sentiment, agreed rates, and extracted data
- **Metrics Dashboard** — Visual dashboard at `/dashboard` with KPIs, charts, and call history
- **API Key Authentication** — All endpoints secured with `X-API-Key` header
- **Docker** — Fully containerized with Dockerfile

## Quick Start

### 1. Clone and configure

```bash
git clone git@github.com:darshselarka1497/happyrobot-assessment.git
cd happyrobot-assessment
cp .env.example .env
# Edit .env with your values:
#   FMCSA_API_KEY=<your key from https://mobile.fmcsa.dot.gov/QCDevsite/HomePage>
#   API_KEY=<choose a strong API key>
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

## API Endpoints

All endpoints require the `X-API-Key` header (except `/health`).

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

The HappyRobot voice agent calls these deployed endpoints as tools during carrier conversations:

1. **Verify Carrier** → `GET https://happyrobot-assessment.onrender.com/api/fmcsa/verify/{mc_number}`
2. **Search Loads** → `GET https://happyrobot-assessment.onrender.com/api/loads/search?origin=X&destination=Y&equipment_type=Z`
3. **Negotiate** → `POST https://happyrobot-assessment.onrender.com/api/negotiate` with body `{"call_id": "...", "load_id": "...", "carrier_offer": 2400}`
4. **Log Call** → `POST https://happyrobot-assessment.onrender.com/api/calls/log` (called after call ends via webhook)

See `docs/IMPLEMENTATION_GUIDE.md` for the full step-by-step platform setup.

## Deployment

Deployed on **Render** using Docker. To reproduce:

1. Fork/clone this repo
2. Create a new **Web Service** on [render.com](https://render.com) connected to the GitHub repo
3. Render auto-detects the `Dockerfile`
4. Set environment variables: `FMCSA_API_KEY`, `API_KEY`, `DATABASE_URL`
5. Deploy

### Run locally with Docker

```bash
git clone git@github.com:darshselarka1497/happyrobot-assessment.git
cd happyrobot-assessment
cp .env.example .env
# Edit .env
docker compose up --build
```

## Negotiation Logic

- Floor price: 90% of `loadboard_rate`
- Carrier offer >= floor → **accept**, transfer to sales rep
- Carrier offer < floor → **counter** with midpoint of (carrier offer + current ask)
- Counter never goes below floor price
- After 3 rounds → present final floor price as take-it-or-leave-it
