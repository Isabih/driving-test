from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import BikeStatus, Evidence, Exam, ExamEvent, ExamStage, TelemetryLog, User
from app.services.stage_camera_service import get_stage_camera_payload

router = APIRouter(prefix="/live", tags=["live"])


@router.get("/exams")
def live_exams(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Exam).filter(Exam.status == "running").all()
    return [{"exam_id": e.id, "exam_code": e.exam_code, "rider_name": e.rider.full_name, "bike_code": e.bike.bike_code, "current_stage_key": e.current_stage_key, "current_speed_kmh": e.current_speed_kmh, "last_telemetry_at": e.last_telemetry_at} for e in rows]


@router.get("/exams/{exam_id}")
def live_exam_detail(exam_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = db.query(Exam).options(joinedload(Exam.stages).joinedload(ExamStage.events)).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    status = db.query(BikeStatus).filter(BikeStatus.bike_id == exam.bike_id).first()
    current_stage = next((s for s in exam.stages if s.stage_key == exam.current_stage_key), None)
    latest_events = db.query(ExamEvent).filter(ExamEvent.exam_id == exam_id).order_by(ExamEvent.captured_at.desc()).limit(20).all()
    latest_evidence = db.query(Evidence).filter(Evidence.exam_id == exam_id).order_by(Evidence.captured_at.desc()).limit(20).all()
    return {
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "status": exam.status,
        "final_result": exam.final_result,
        "rider": {"id": exam.rider.id, "full_name": exam.rider.full_name, "rider_code": exam.rider.rider_code, "national_id": exam.rider.national_id},
        "bike": {"id": exam.bike.id, "bike_code": exam.bike.bike_code, "bike_name": exam.bike.bike_name, "device_id": exam.bike.device_id, "firmware_version": exam.bike.firmware_version},
        "telemetry": {"speed_kmh": exam.current_speed_kmh, "battery_percent": status.battery_percent if status else 0, "signal_health": status.signal_health if status else 0, "last_seen_at": status.last_seen_at if status else None},
        "current_stage": None if not current_stage else {"stage_key": current_stage.stage_key, "stage_name": current_stage.stage_name, "status": current_stage.status, "started_at": current_stage.started_at, "duration_seconds": current_stage.duration_seconds, "penalty_points": current_stage.penalty_points, "score": current_stage.score, "pass_fail": current_stage.pass_fail, "max_speed_kmh": current_stage.max_speed_kmh, "min_speed_kmh": current_stage.min_speed_kmh},
        "stage_summary": [{"stage_key": s.stage_key, "status": s.status, "pass_fail": s.pass_fail, "penalty_points": s.penalty_points} for s in sorted(exam.stages, key=lambda x: x.stage_order)],
        "latest_events": [{"id": e.id, "event_type": e.event_type, "description": e.description, "severity": e.severity, "captured_at": e.captured_at} for e in latest_events],
        "latest_evidence": [{"id": e.id, "image_url": f"/exams/{exam.id}/evidence/{e.id}", "captured_at": e.captured_at, "stage_key": e.stage_key} for e in latest_evidence],
    }


@router.get("/exams/{exam_id}/events")
def live_exam_events(exam_id: int, limit: int = 50, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(ExamEvent).filter(ExamEvent.exam_id == exam_id).order_by(ExamEvent.captured_at.desc()).limit(limit).all()
    return rows


@router.get("/exams/{exam_id}/evidence")
def live_exam_evidence(exam_id: int, limit: int = 50, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Evidence).filter(Evidence.exam_id == exam_id).order_by(Evidence.captured_at.desc()).limit(limit).all()
    return [{"id": e.id, "image_url": f"/exams/{exam_id}/evidence/{e.id}", "captured_at": e.captured_at, "stage_key": e.stage_key} for e in rows]


@router.get("/exams/{exam_id}/telemetry")
def live_exam_telemetry(exam_id: int, window_minutes: int = 5, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(TelemetryLog).filter(TelemetryLog.exam_id == exam_id).order_by(TelemetryLog.timestamp.desc()).limit(200).all()
    return rows


@router.get("/stages/{stage_key}")
def exams_by_stage(stage_key: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(Exam).filter(Exam.status == "running", Exam.current_stage_key == stage_key).all()
    return {"stage_key": stage_key, "running_exams": [{"exam_id": e.id, "exam_code": e.exam_code, "rider_name": e.rider.full_name, "bike_code": e.bike.bike_code, "speed_kmh": e.current_speed_kmh, "penalty_points": e.total_penalty_points, "status_hint": "critical" if e.auto_fail_reason else ("warning" if e.total_penalty_points else "looks_good")} for e in rows]}


@router.get("/exams/{exam_id}/stage-view")
def live_exam_stage_view(exam_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = db.query(Exam).options(joinedload(Exam.stages)).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    current_stage = next((s for s in exam.stages if s.stage_key == exam.current_stage_key), None)
    stage_payload = get_stage_camera_payload(exam.current_stage_key or "figure_8")
    return {
        "exam_id": exam.id,
        "exam_code": exam.exam_code,
        "active_stage_key": exam.current_stage_key,
        "active_stage": None if not current_stage else {
            "stage_key": current_stage.stage_key,
            "stage_name": current_stage.stage_name,
            "status": current_stage.status,
            "pass_fail": current_stage.pass_fail,
            "score": current_stage.score,
            "penalty_points": current_stage.penalty_points,
            "duration_seconds": current_stage.duration_seconds,
            "max_speed_kmh": current_stage.max_speed_kmh,
            "min_speed_kmh": current_stage.min_speed_kmh,
        },
        "speed_kmh": exam.current_speed_kmh,
        "cameras": stage_payload.get("cameras", []),
        "switching_mode": "single_active_stage",
        "next_stage_enabled_only_when_current_completed": True,
    }
