from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import Exam, Rider, User

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/search")
def search_records(
    q: str | None = None,
    rider_code: str | None = None,
    rider_name: str | None = None,
    national_id: str | None = None,
    bike_code: str | None = None,
    exam_code: str | None = None,
    final_result: str | None = None,
    status: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(Exam)
    if q:
        like = f"%{q}%"
        query = query.join(Rider).filter((Rider.full_name.ilike(like)) | (Rider.rider_code.ilike(like)) | (Exam.exam_code.ilike(like)))
    if rider_code:
        query = query.join(Rider).filter(Rider.rider_code == rider_code)
    if rider_name:
        query = query.join(Rider).filter(Rider.full_name.ilike(f"%{rider_name}%"))
    if national_id:
        query = query.join(Rider).filter(Rider.national_id == national_id)
    if bike_code:
        query = query.filter(Exam.bike.has(bike_code=bike_code))
    if exam_code:
        query = query.filter(Exam.exam_code == exam_code)
    if final_result:
        query = query.filter(Exam.final_result == final_result)
    if status:
        query = query.filter(Exam.status == status)
    if date_from:
        query = query.filter(Exam.created_at >= date_from)
    if date_to:
        query = query.filter(Exam.created_at <= date_to)
    total = query.count()
    rows = query.order_by(Exam.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [{"exam_id": e.id, "exam_code": e.exam_code, "rider_name": e.rider.full_name, "rider_code": e.rider.rider_code, "bike_code": e.bike.bike_code, "status": e.status, "final_result": e.final_result, "started_at": e.started_at, "ended_at": e.ended_at, "total_penalty_points": e.total_penalty_points} for e in rows]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/riders/{rider_id}/history")
def rider_history(rider_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Exam).filter(Exam.rider_id == rider_id).order_by(Exam.id.desc()).all()
    return [{"exam_id": e.id, "exam_code": e.exam_code, "status": e.status, "final_result": e.final_result, "started_at": e.started_at, "ended_at": e.ended_at} for e in rows]
