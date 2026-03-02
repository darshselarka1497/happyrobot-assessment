from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


# --- Loads ---
class LoadOut(BaseModel):
    load_id: str
    origin: str
    destination: str
    pickup_datetime: datetime
    delivery_datetime: datetime
    equipment_type: str
    loadboard_rate: float
    notes: Optional[str] = None
    weight: float
    commodity_type: str
    num_of_pieces: Optional[int] = None
    miles: float
    dimensions: Optional[str] = None
    status: str

    model_config = {"from_attributes": True}


class LoadSearchParams(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    equipment_type: Optional[str] = None
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None
    max_weight: Optional[float] = None


# --- FMCSA ---
class FMCSAResult(BaseModel):
    mc_number: str
    legal_name: Optional[str] = None
    dot_number: Optional[str] = None
    is_authorized: bool
    operating_status: Optional[str] = None
    out_of_service: bool = False
    reason: Optional[str] = None


# --- Negotiation ---
class NegotiateRequest(BaseModel):
    call_id: str
    load_id: str
    carrier_offer: float


class NegotiateResponse(BaseModel):
    session_id: str
    status: str  # "accepted", "countered", "rejected", "max_rounds_reached"
    round_number: int
    carrier_offer: float
    counter_offer: Optional[float] = None
    loadboard_rate: float
    message: str


# --- Call Logging ---
class CallLogRequest(BaseModel):
    call_id: str
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    load_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    loadboard_rate: Optional[float] = None
    agreed_rate: Optional[float] = None
    negotiation_rounds: int = 0
    outcome: str = "call_dropped"
    sentiment: str = "neutral"
    notes: Optional[str] = None


class CallLogOut(BaseModel):
    call_id: str
    mc_number: Optional[str] = None
    carrier_name: Optional[str] = None
    load_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    loadboard_rate: Optional[float] = None
    agreed_rate: Optional[float] = None
    negotiation_rounds: int
    outcome: str
    sentiment: str
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Metrics ---
class MetricsOut(BaseModel):
    total_calls: int
    outcome_breakdown: Dict[str, int]
    sentiment_breakdown: Dict[str, int]
    avg_negotiation_rounds: float
    booking_rate: float
    avg_agreed_rate: Optional[float]
    avg_loadboard_rate: Optional[float]
    avg_discount_pct: Optional[float]
    calls_over_time: List[Dict]
