from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import Bike, BikeStatus, User
from app.schemas.common import BikeCreate, BikeOut

router = APIRouter(prefix="/bikes", tags=["bikes"])


@router.post("", response_model=BikeOut)
def create_bike(payload: BikeCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exists = db.query(Bike).filter(or_(Bike.bike_code == payload.bike_code, Bike.device_id == payload.device_id)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Bike code or device ID already exists")
    bike = Bike(**payload.model_dump())
    db.add(bike)
    db.commit()
    db.refresh(bike)
    if not db.query(BikeStatus).filter(BikeStatus.bike_id == bike.id).first():
        db.add(BikeStatus(bike_id=bike.id, firmware_version=bike.firmware_version))
        db.commit()
    return bike


@router.get("", response_model=list[BikeOut])
def list_bikes(q: str | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(Bike)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Bike.bike_name.ilike(like), Bike.bike_code.ilike(like), Bike.device_id.ilike(like)))
    return query.order_by(Bike.id.desc()).all()
