from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import BikeStatus, Exam, ExamEvent, Evidence, User
from app.services.mqtt_service import mqtt_state

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    exams_today = db.query(Exam).filter(Exam.created_at >= start, Exam.created_at < end).count()
    passed_today = db.query(Exam).filter(Exam.ended_at >= start, Exam.ended_at < end, Exam.final_result == "pass").count()
    failed_today = db.query(Exam).filter(Exam.ended_at >= start, Exam.ended_at < end, Exam.final_result == "fail").count()
    latest = db.query(Exam).filter(Exam.last_telemetry_at.isnot(None)).order_by(Exam.last_telemetry_at.desc()).first()
    return {
        "active_exams": db.query(Exam).filter(Exam.status == "running").count(),
        "online_bikes": db.query(BikeStatus).filter(BikeStatus.online == True).count(),
        "mqtt_connected": mqtt_state.connected,
        "exams_today": exams_today,
        "passed_today": passed_today,
        "failed_today": failed_today,
        "pending_exams": db.query(Exam).filter(Exam.status == "pending").count(),
        "latest_telemetry_at": latest.last_telemetry_at if latest else None,
    }


@router.get("/recent-violations")
def recent_violations(limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(ExamEvent).order_by(ExamEvent.captured_at.desc()).limit(limit).all()
    return [{"event_id": r.id, "exam_id": r.exam_id, "stage_key": r.stage.stage_key if r.stage else None, "event_type": r.event_type, "severity": r.severity, "description": r.description, "captured_at": r.captured_at} for r in rows]


@router.get("/recent-results")
def recent_results(limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Exam).filter(Exam.status == "finished").order_by(Exam.ended_at.desc()).limit(limit).all()
    return [{"exam_id": r.id, "exam_code": r.exam_code, "final_result": r.final_result, "total_score": r.total_score, "ended_at": r.ended_at} for r in rows]


@router.get("/running-exams")
def running_exams(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Exam).filter(Exam.status == "running").order_by(Exam.started_at.desc()).all()
    return [{"exam_id": e.id, "exam_code": e.exam_code, "rider_name": e.rider.full_name, "rider_code": e.rider.rider_code, "bike_code": e.bike.bike_code, "current_stage_key": e.current_stage_key, "status": e.status, "total_penalty_points": e.total_penalty_points, "current_speed_kmh": e.current_speed_kmh, "last_telemetry_at": e.last_telemetry_at} for e in rows]
