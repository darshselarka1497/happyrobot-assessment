import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from api.models import Load


def seed_loads(db: Session):
    existing = db.query(Load).count()
    if existing > 0:
        return

    seed_file = Path(__file__).resolve().parent.parent / "data" / "loads_seed.json"
    with open(seed_file) as f:
        loads_data = json.load(f)

    for item in loads_data:
        load = Load(
            load_id=item["load_id"],
            origin=item["origin"],
            destination=item["destination"],
            pickup_datetime=datetime.fromisoformat(item["pickup_datetime"]),
            delivery_datetime=datetime.fromisoformat(item["delivery_datetime"]),
            equipment_type=item["equipment_type"],
            loadboard_rate=item["loadboard_rate"],
            notes=item.get("notes"),
            weight=item["weight"],
            commodity_type=item["commodity_type"],
            num_of_pieces=item.get("num_of_pieces"),
            miles=item["miles"],
            dimensions=item.get("dimensions"),
            status="available",
        )
        db.add(load)

    db.commit()
