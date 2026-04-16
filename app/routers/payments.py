from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import Payment, Rider, User
from app.schemas.common import PaymentCreate, PaymentOut

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if not db.get(Rider, payload.rider_id):
        raise HTTPException(status_code=404, detail="Rider not found")
    if db.query(Payment).filter(Payment.reference == payload.reference).first():
        raise HTTPException(status_code=400, detail="Payment reference already exists")
    payment = Payment(**payload.model_dump())
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.get("/rider/{rider_id}", response_model=list[PaymentOut])
def rider_payments(rider_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Payment).filter(Payment.rider_id == rider_id).order_by(Payment.id.desc()).all()
