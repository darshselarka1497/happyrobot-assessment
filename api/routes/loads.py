from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.auth import verify_api_key
from api.database import get_db
from api.models import Load
from api.schemas import LoadOut

router = APIRouter(prefix="/api/loads", tags=["Loads"])


@router.get("/search", response_model=List[LoadOut])
def search_loads(
    origin: Optional[str] = Query(None, description="Origin city/state (partial match)"),
    destination: Optional[str] = Query(None, description="Destination city/state (partial match)"),
    equipment_type: Optional[str] = Query(None, description="Equipment type (e.g., Dry Van, Reefer, Flatbed)"),
    min_rate: Optional[float] = Query(None, description="Minimum loadboard rate"),
    max_rate: Optional[float] = Query(None, description="Maximum loadboard rate"),
    max_weight: Optional[float] = Query(None, description="Maximum load weight"),
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> List[LoadOut]:
    """Search available loads with optional filters."""
    query = db.query(Load).filter(Load.status == "available")

    if origin:
        query = query.filter(Load.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Load.destination.ilike(f"%{destination}%"))
    if equipment_type:
        query = query.filter(Load.equipment_type.ilike(f"%{equipment_type}%"))
    if min_rate is not None:
        query = query.filter(Load.loadboard_rate >= min_rate)
    if max_rate is not None:
        query = query.filter(Load.loadboard_rate <= max_rate)
    if max_weight is not None:
        query = query.filter(Load.weight <= max_weight)

    return query.all()


@router.get("/{load_id}", response_model=LoadOut)
def get_load(
    load_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> LoadOut:
    """Get a specific load by ID."""
    load = db.query(Load).filter(Load.load_id == load_id).first()
    if not load:
        raise HTTPException(status_code=404, detail="Load not found")
    return load
