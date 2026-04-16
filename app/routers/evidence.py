from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user, require_roles
from app.models.models import Evidence, User

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("")
def list_evidence(stage_key: str | None = None, event_type: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None, page: int = 1, page_size: int = 20, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(Evidence)
    if stage_key:
        query = query.filter(Evidence.stage_key == stage_key)
    if date_from:
        query = query.filter(Evidence.captured_at >= date_from)
    if date_to:
        query = query.filter(Evidence.captured_at <= date_to)
    if event_type:
        query = query.filter(Evidence.event.has(event_type=event_type))
    total = query.count()
    rows = query.order_by(Evidence.captured_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = [{"id": e.id, "exam_id": e.exam_id, "event_id": e.event_id, "rider_name": e.event.stage.exam.rider.full_name if e.event else None, "rider_code": e.event.stage.exam.rider.rider_code if e.event else None, "stage_key": e.stage_key, "event_type": e.event.event_type if e.event else None, "severity": e.event.severity if e.event else None, "description": e.description, "captured_at": e.captured_at, "image_url": f"/exams/{e.exam_id}/evidence/{e.id}"} for e in rows]
    return {"items": items, "page": page, "page_size": page_size, "total": total}
