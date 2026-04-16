from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import Rider, User
from app.schemas.common import RiderCreate, RiderOut

router = APIRouter(prefix="/riders", tags=["riders"])


@router.post("", response_model=RiderOut)
def create_rider(payload: RiderCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exists = db.query(Rider).filter(or_(Rider.rider_code == payload.rider_code, Rider.national_id == payload.national_id, Rider.phone == payload.phone)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Rider code, national ID, or phone already exists")
    rider = Rider(**payload.model_dump())
    db.add(rider)
    db.commit()
    db.refresh(rider)
    return rider


@router.get("", response_model=list[RiderOut])
def list_riders(q: str | None = Query(default=None), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(Rider)
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Rider.full_name.ilike(like), Rider.rider_code.ilike(like), Rider.national_id.ilike(like)))
    return query.order_by(Rider.id.desc()).all()
