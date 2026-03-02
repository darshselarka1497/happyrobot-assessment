import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.auth import verify_api_key
from api.database import get_db
from api.models import Load, NegotiationSession
from api.schemas import NegotiateRequest, NegotiateResponse

router = APIRouter(prefix="/api/negotiate", tags=["Negotiation"])

CEILING_RATE_PCT = 1.10  # Max 110% of loadboard rate — the most the broker will pay


@router.post("", response_model=NegotiateResponse)
def negotiate(
    req: NegotiateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> NegotiateResponse:
    """
    Evaluate a carrier's counter-offer on a load.

    Carriers want MORE money than the loadboard rate. The broker negotiates DOWN.

    Rules:
    - Ceiling price = 110% of loadboard_rate (max the broker will pay).
    - Carrier asks <= loadboard_rate → accept immediately (great deal for broker).
    - Carrier asks <= ceiling → counter with midpoint, nudging toward loadboard_rate.
    - Carrier asks > ceiling → counter with ceiling as max.
    - Max 3 rounds, then present ceiling as final take-it-or-leave-it.
    """
    # Find the load
    load = db.query(Load).filter(Load.load_id == req.load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")

    ceiling_rate = round(load.loadboard_rate * CEILING_RATE_PCT, 2)

    # Find or create session
    session = (
        db.query(NegotiationSession)
        .filter(
            NegotiationSession.call_id == req.call_id,
            NegotiationSession.load_id == req.load_id,
            NegotiationSession.status == "active",
        )
        .first()
    )

    if not session:
        session = NegotiationSession(
            session_id=str(uuid.uuid4()),
            call_id=req.call_id,
            load_id=req.load_id,
            loadboard_rate=load.loadboard_rate,
            floor_rate=ceiling_rate,  # reusing field as ceiling
            current_offer=load.loadboard_rate,  # broker starts at loadboard rate
            rounds_completed=0,
        )
        db.add(session)
        db.flush()

    session.rounds_completed += 1
    round_num = session.rounds_completed

    # Carrier asks at or below loadboard rate → great deal, accept immediately
    if req.carrier_offer <= load.loadboard_rate:
        session.status = "accepted"
        session.current_offer = req.carrier_offer
        db.commit()
        return NegotiateResponse(
            session_id=session.session_id,
            status="accepted",
            round_number=round_num,
            carrier_offer=req.carrier_offer,
            counter_offer=None,
            loadboard_rate=load.loadboard_rate,
            message=f"That works for us! ${req.carrier_offer:,.0f} is a deal. Let me transfer you to our sales rep to finalize the booking.",
        )

    # Carrier asks within ceiling → accept (close enough)
    if req.carrier_offer <= ceiling_rate:
        # If carrier is asking only slightly above loadboard, just accept
        if req.carrier_offer <= load.loadboard_rate * 1.03:
            session.status = "accepted"
            session.current_offer = req.carrier_offer
            db.commit()
            return NegotiateResponse(
                session_id=session.session_id,
                status="accepted",
                round_number=round_num,
                carrier_offer=req.carrier_offer,
                counter_offer=None,
                loadboard_rate=load.loadboard_rate,
                message=f"We can make ${req.carrier_offer:,.0f} work. Let me transfer you to our sales rep to finalize the booking.",
            )

    # Max rounds reached → present ceiling as final offer
    if round_num >= session.max_rounds:
        session.status = "max_rounds_reached"
        db.commit()
        return NegotiateResponse(
            session_id=session.session_id,
            status="max_rounds_reached",
            round_number=round_num,
            carrier_offer=req.carrier_offer,
            counter_offer=ceiling_rate,
            loadboard_rate=load.loadboard_rate,
            message=f"I understand you're looking for ${req.carrier_offer:,.0f}, but the absolute most we can do on this load is ${ceiling_rate:,.0f}. Would you like to take it at that rate, or should we look at other available loads?",
        )

    # Counter-offer: split the difference between carrier's ask and broker's current offer
    counter = round((req.carrier_offer + session.current_offer) / 2, 2)
    # Never counter above ceiling
    counter = min(counter, ceiling_rate)
    session.current_offer = counter
    db.commit()

    return NegotiateResponse(
        session_id=session.session_id,
        status="countered",
        round_number=round_num,
        carrier_offer=req.carrier_offer,
        counter_offer=counter,
        loadboard_rate=load.loadboard_rate,
        message=f"I hear you at ${req.carrier_offer:,.0f}, but the best I can offer right now is ${counter:,.0f}. This is a {load.miles:.0f}-mile run from {load.origin} to {load.destination} with {load.commodity_type.lower()}. Can you work with that?",
    )
