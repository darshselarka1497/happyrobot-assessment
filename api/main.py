from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.database import SessionLocal, init_db
from api.routes import calls, fmcsa, loads, negotiate
from api.seed import seed_loads

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_loads(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Carrier Sales API",
    description="Backend API for HappyRobot inbound carrier sales automation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fmcsa.router)
app.include_router(loads.router)
app.include_router(negotiate.router)
app.include_router(calls.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/dashboard")
async def dashboard():
    return FileResponse(DASHBOARD_DIR / "index.html")
