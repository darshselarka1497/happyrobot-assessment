# Carrier Sales API

Backend API for HappyRobot inbound carrier sales automation. This service provides the external endpoints that the HappyRobot voice agent calls during carrier conversations.

## Features

- **FMCSA Carrier Verification** — Validate MC numbers against the FMCSA database
- **Load Search** — Search available loads by origin, destination, equipment type, rate, and weight
- **Negotiation Engine** — Stateful counter-offer logic with configurable floor price (90% of loadboard rate) and max 3 rounds
- **Call Logging** — Record call outcomes, sentiment, agreed rates, and extracted data
- **Metrics Dashboard** — Visual dashboard at `/dashboard` with KPIs, charts, and call history
- **API Key Authentication** — All endpoints secured with `X-API-Key` header

## Quick Start

### 1. Clone and configure

```bash
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

All endpoints require the `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check (no auth) |
| GET | `/api/fmcsa/verify/{mc_number}` | Verify carrier MC number |
| GET | `/api/loads/search` | Search loads (query params: origin, destination, equipment_type, min_rate, max_rate, max_weight) |
| GET | `/api/loads/{load_id}` | Get a specific load |
| POST | `/api/negotiate` | Submit/evaluate a counter-offer |
| POST | `/api/calls/log` | Log call data |
| GET | `/api/calls/log` | List call logs |
| GET | `/api/calls/metrics` | Aggregated metrics for dashboard |
| GET | `/dashboard` | Metrics dashboard UI |
| GET | `/docs` | Interactive API docs (Swagger) |

## HappyRobot Platform Setup

Configure the inbound agent on HappyRobot to call these endpoints as tools:

1. **Verify Carrier** → `GET /api/fmcsa/verify/{mc_number}`
2. **Search Loads** → `GET /api/loads/search?origin=X&destination=Y&equipment_type=Z`
3. **Negotiate** → `POST /api/negotiate` with body `{"call_id": "...", "load_id": "...", "carrier_offer": 2400}`
4. **Log Call** → `POST /api/calls/log` (called after call ends)

## Deployment

### Railway / Fly.io

1. Push to a Git repository
2. Connect the repo to Railway or Fly.io
3. Set environment variables (`FMCSA_API_KEY`, `API_KEY`)
4. Deploy — the Dockerfile handles the rest

### Cloud VM

```bash
git clone <repo-url>
cd carrier-sales-api
cp .env.example .env
# Edit .env
docker compose up -d
```

## Negotiation Logic

- Floor price: 90% of `loadboard_rate`
- Carrier offer >= floor → **accept**, transfer to sales rep
- Carrier offer < floor → **counter** with midpoint of (carrier offer + current ask)
- After 3 rounds → present final floor price as take-it-or-leave-it
