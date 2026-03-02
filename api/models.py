from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class Load(Base):
    __tablename__ = "loads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    load_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    origin: Mapped[str] = mapped_column(String(200))
    destination: Mapped[str] = mapped_column(String(200))
    pickup_datetime: Mapped[datetime] = mapped_column(DateTime)
    delivery_datetime: Mapped[datetime] = mapped_column(DateTime)
    equipment_type: Mapped[str] = mapped_column(String(50))
    loadboard_rate: Mapped[float] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    weight: Mapped[float] = mapped_column(Float)
    commodity_type: Mapped[str] = mapped_column(String(100))
    num_of_pieces: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    miles: Mapped[float] = mapped_column(Float)
    dimensions: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="available")


class CallOutcome(str, enum.Enum):
    BOOKED = "booked"
    NO_MATCH = "no_match"
    PRICE_REJECTED = "price_rejected"
    CARRIER_INELIGIBLE = "carrier_ineligible"
    CALL_DROPPED = "call_dropped"
    TRANSFERRED = "transferred"


class CallSentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class CallLog(Base):
    __tablename__ = "call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    call_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    mc_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    carrier_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    load_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    origin: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    destination: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    loadboard_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    agreed_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    negotiation_rounds: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str] = mapped_column(
        String(30), default=CallOutcome.CALL_DROPPED.value
    )
    sentiment: Mapped[str] = mapped_column(
        String(20), default=CallSentiment.NEUTRAL.value
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class NegotiationSession(Base):
    __tablename__ = "negotiation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    call_id: Mapped[str] = mapped_column(String(100), index=True)
    load_id: Mapped[str] = mapped_column(String(50))
    loadboard_rate: Mapped[float] = mapped_column(Float)
    floor_rate: Mapped[float] = mapped_column(Float)
    current_offer: Mapped[float] = mapped_column(Float)
    rounds_completed: Mapped[int] = mapped_column(Integer, default=0)
    max_rounds: Mapped[int] = mapped_column(Integer, default=3)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
