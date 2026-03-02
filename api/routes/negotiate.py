import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.auth import verify_api_key
from api.database import get_db
from api.models import Load, NegotiationSession
from api.schemas import NegotiateRequest, NegotiateResponse

router = APIRouter(prefix="/api/negotiate", tags=["Negotiation"])

FLOOR_RATE_PCT = 0.90  # Accept anything >= 90% of loadboard rate


@router.post("", response_model=NegotiateResponse)
def negotiate(
    req: NegotiateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> NegotiateResponse:
    """
    Evaluate a carrier's counter-offer on a load.

    Negotiation rules:
    - Floor price is 90% of loadboard_rate.
    - If carrier offer >= floor price → accept.
    - If carrier offer < floor price → counter with midpoint between offer and loadboard rate.
    - Maximum 3 negotiation rounds. After that, reject or accept the last offer.
    """
    # Find the load
    load = db.query(Load).filter(Load.load_id == req.load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")

    floor_rate = load.loadboard_rate * FLOOR_RATE_PCT

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
            floor_rate=floor_rate,
            current_offer=load.loadboard_rate,
            rounds_completed=0,
        )
        db.add(session)
        db.flush()

    session.rounds_completed += 1
    round_num = session.rounds_completed

    # Carrier offer meets or exceeds floor → accept
    if req.carrier_offer >= floor_rate:
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
            message=f"We can accept ${req.carrier_offer:,.0f}. Let me transfer you to our sales rep to finalize the booking.",
        )

    # Max rounds reached → reject
    if round_num >= session.max_rounds:
        session.status = "max_rounds_reached"
        db.commit()
        return NegotiateResponse(
            session_id=session.session_id,
            status="max_rounds_reached",
            round_number=round_num,
            carrier_offer=req.carrier_offer,
            counter_offer=None,
            loadboard_rate=load.loadboard_rate,
            message=f"Unfortunately, ${req.carrier_offer:,.0f} is below what we can offer for this load. The best we can do is ${floor_rate:,.0f}. Would you like to accept that, or should we look at other available loads?",
        )

    # Counter-offer: split the difference between carrier offer and current asking price
    counter = round((req.carrier_offer + session.current_offer) / 2, 2)
    # Don't counter below floor
    counter = max(counter, floor_rate)
    session.current_offer = counter
    db.commit()

    return NegotiateResponse(
        session_id=session.session_id,
        status="countered",
        round_number=round_num,
        carrier_offer=req.carrier_offer,
        counter_offer=counter,
        loadboard_rate=load.loadboard_rate,
        message=f"I appreciate the offer of ${req.carrier_offer:,.0f}, but the best I can do right now is ${counter:,.0f}. This is a {load.miles:.0f}-mile run from {load.origin} to {load.destination}. Can you work with that?",
    )
