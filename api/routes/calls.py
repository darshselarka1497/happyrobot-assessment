from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.auth import verify_api_key
from api.database import get_db
from api.models import CallLog
from api.schemas import CallLogOut, CallLogRequest, MetricsOut

router = APIRouter(prefix="/api/calls", tags=["Calls"])


@router.post("/log", response_model=CallLogOut)
def log_call(
    req: CallLogRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> CallLogOut:
    """Log call data after a call completes."""
    existing = db.query(CallLog).filter(CallLog.call_id == req.call_id).first()
    if existing:
        # Update existing record
        for field, value in req.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    call_log = CallLog(**req.model_dump())
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    return call_log


@router.get("/log", response_model=List[CallLogOut])
def list_calls(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    outcome: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> List[CallLogOut]:
    """List call logs with optional filtering."""
    query = db.query(CallLog)
    if outcome:
        query = query.filter(CallLog.outcome == outcome)
    if sentiment:
        query = query.filter(CallLog.sentiment == sentiment)
    return query.order_by(CallLog.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/metrics", response_model=MetricsOut)
def get_metrics(
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> MetricsOut:
    """Get aggregated call metrics for the dashboard."""
    total = db.query(CallLog).count()

    # Outcome breakdown
    outcome_rows = (
        db.query(CallLog.outcome, func.count(CallLog.id))
        .group_by(CallLog.outcome)
        .all()
    )
    outcome_breakdown = {row[0]: row[1] for row in outcome_rows}

    # Sentiment breakdown
    sentiment_rows = (
        db.query(CallLog.sentiment, func.count(CallLog.id))
        .group_by(CallLog.sentiment)
        .all()
    )
    sentiment_breakdown = {row[0]: row[1] for row in sentiment_rows}

    # Avg negotiation rounds
    avg_rounds = db.query(func.avg(CallLog.negotiation_rounds)).scalar() or 0

    # Booking rate
    booked = outcome_breakdown.get("booked", 0) + outcome_breakdown.get("transferred", 0)
    booking_rate = (booked / total * 100) if total > 0 else 0

    # Rate stats (only for calls with agreed rates)
    avg_agreed = db.query(func.avg(CallLog.agreed_rate)).filter(CallLog.agreed_rate.isnot(None)).scalar()
    avg_loadboard = db.query(func.avg(CallLog.loadboard_rate)).filter(CallLog.loadboard_rate.isnot(None)).scalar()

    avg_discount = None
    if avg_agreed and avg_loadboard and avg_loadboard > 0:
        avg_discount = round((1 - avg_agreed / avg_loadboard) * 100, 2)

    # Calls over time (group by date)
    daily_rows = (
        db.query(
            func.date(CallLog.created_at).label("date"),
            func.count(CallLog.id).label("count"),
        )
        .group_by(func.date(CallLog.created_at))
        .order_by(func.date(CallLog.created_at))
        .all()
    )
    calls_over_time = [{"date": str(row.date), "count": row.count} for row in daily_rows]

    return MetricsOut(
        total_calls=total,
        outcome_breakdown=outcome_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        avg_negotiation_rounds=round(float(avg_rounds), 2),
        booking_rate=round(booking_rate, 2),
        avg_agreed_rate=round(avg_agreed, 2) if avg_agreed else None,
        avg_loadboard_rate=round(avg_loadboard, 2) if avg_loadboard else None,
        avg_discount_pct=avg_discount,
        calls_over_time=calls_over_time,
    )
