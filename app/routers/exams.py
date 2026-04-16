from datetime import datetime
import os
import shutil
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import Evidence, Exam, ExamEvent, ExamStage, User
from app.schemas.common import ExamCreate, ExamOut, FinishExamIn, StageEventCreate, StageTransitionIn, TelemetryIn
from app.services.exam_service import add_stage_event, create_exam_with_stages, finish_exam, handle_telemetry, start_exam, transition_stage
from app.services.mqtt_service import mqtt_service
from app.services.websocket_manager import manager

router = APIRouter(prefix="/exams", tags=["exams"])


def exam_query(db: Session):
    return db.query(Exam).options(joinedload(Exam.stages).joinedload(ExamStage.events)).order_by(Exam.id.desc())


@router.post("", response_model=ExamOut)
async def create_exam(payload: ExamCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        exam = create_exam_with_stages(db, payload.rider_id, payload.bike_id, payload.payment_id, payload.notes, current_user.id)
        return exam
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[ExamOut])
def list_exams(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return exam_query(db).all()


@router.get("/{exam_id}", response_model=ExamOut)
def get_exam(exam_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = exam_query(db).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.post("/{exam_id}/start", response_model=ExamOut)
async def start_exam_route(exam_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam = exam_query(db).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam = start_exam(db, exam, current_user.id)
    mqtt_service.publish_command(exam.bike.device_id, "start_exam", {"exam_code": exam.exam_code})
    await manager.broadcast({"type": "stage_changed", "exam_id": exam.id, "payload": {"from_stage": None, "to_stage": exam.current_stage_key, "changed_at": datetime.utcnow().isoformat()}})
    return exam_query(db).filter(Exam.id == exam_id).first()


@router.post("/{exam_id}/transition", response_model=ExamOut)
async def transition_exam_route(exam_id: int, payload: StageTransitionIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = exam_query(db).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    old = exam.current_stage_key
    try:
        exam = transition_stage(db, exam, payload.stage_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await manager.broadcast({"type": "stage_changed", "exam_id": exam.id, "payload": {"from_stage": old, "to_stage": payload.stage_key, "changed_at": datetime.utcnow().isoformat()}})
    return exam_query(db).filter(Exam.id == exam_id).first()


@router.post("/{exam_id}/finish", response_model=ExamOut)
async def finish_exam_route(exam_id: int, payload: FinishExamIn, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exam = exam_query(db).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam = finish_exam(db, exam, current_user.id, payload.final_result, payload.notes)
    mqtt_service.publish_command(exam.bike.device_id, "finish_exam", {"exam_code": exam.exam_code, "result": exam.final_result})
    await manager.broadcast({"type": "exam_finished", "exam_id": exam.id, "payload": {"final_result": exam.final_result, "total_score": exam.total_score, "total_penalty_points": exam.total_penalty_points, "auto_fail_reason": exam.auto_fail_reason}})
    return exam_query(db).filter(Exam.id == exam_id).first()


@router.post("/{exam_id}/stages/{stage_key}/events")
async def create_stage_event(exam_id: int, stage_key: str, payload: StageEventCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = exam_query(db).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    event, _stage = add_stage_event(db, exam, stage_key, payload.model_dump())
    await manager.broadcast({"type": "event_detected", "exam_id": exam.id, "stage_key": stage_key, "payload": {"event_id": event.id, "event_type": event.event_type, "severity": event.severity, "description": event.description, "penalty_points": event.penalty_points, "auto_fail": event.auto_fail, "captured_at": event.captured_at.isoformat()}})
    return {"event_id": event.id, "ok": True}


@router.post("/{exam_id}/events/{event_id}/evidence")
async def upload_evidence(exam_id: int, event_id: int, file: UploadFile = File(...), description: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    event = db.query(ExamEvent).filter(ExamEvent.id == event_id, ExamEvent.exam_id == exam_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    os.makedirs(settings.evidence_dir, exist_ok=True)
    safe_name = f"exam_{exam_id}_event_{event_id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
    path = os.path.join(settings.evidence_dir, safe_name)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    ev = Evidence(exam_id=exam_id, event_id=event_id, stage_key=event.stage.stage_key if event.stage else None, file_path=path, mime_type=file.content_type, file_size=os.path.getsize(path), description=description)
    db.add(ev)
    db.commit()
    db.refresh(ev)
    await manager.broadcast({"type": "evidence_uploaded", "exam_id": exam_id, "stage_key": ev.stage_key, "payload": {"evidence_id": ev.id, "image_url": f"/exams/{exam_id}/evidence/{ev.id}", "event_id": event_id}})
    return {"id": ev.id, "image_url": f"/exams/{exam_id}/evidence/{ev.id}"}


@router.get("/{exam_id}/evidence/{evidence_id}")
def get_evidence_file(exam_id: int, evidence_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id, Evidence.exam_id == exam_id).first()
    if not evidence or not os.path.exists(evidence.file_path):
        raise HTTPException(status_code=404, detail="Evidence not found")
    return FileResponse(evidence.file_path)


@router.post("/{exam_id}/telemetry")
async def telemetry_for_exam(exam_id: int, payload: TelemetryIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    try:
        log, running_exam, bike = handle_telemetry(db, payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if running_exam:
        await manager.broadcast({"type": "telemetry_update", "exam_id": running_exam.id, "bike_id": bike.id, "device_id": bike.device_id, "payload": {"speed_kmh": log.speed_kmh, "battery_percent": log.battery_percent, "signal_health": log.signal_health, "timestamp": log.timestamp.isoformat()}})
    return {"ok": True, "speed_kmh": log.speed_kmh}


@router.post("/telemetry/live")
async def telemetry_live(payload: TelemetryIn, db: Session = Depends(get_db)):
    log, running_exam, bike = handle_telemetry(db, payload.model_dump())
    if running_exam:
        await manager.broadcast({"type": "telemetry_update", "exam_id": running_exam.id, "bike_id": bike.id, "device_id": bike.device_id, "payload": {"speed_kmh": log.speed_kmh, "battery_percent": log.battery_percent, "signal_health": log.signal_health, "timestamp": log.timestamp.isoformat()}})
    return {"ok": True, "speed_kmh": log.speed_kmh}


@router.get("/{exam_id}/report")
def exam_report(exam_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = exam_query(db).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return {
        "exam_code": exam.exam_code,
        "rider_name": exam.rider.full_name,
        "rider_code": exam.rider.rider_code,
        "national_id": exam.rider.national_id,
        "bike_code": exam.bike.bike_code,
        "bike_name": exam.bike.bike_name,
        "status": exam.status,
        "final_result": exam.final_result,
        "total_score": exam.total_score,
        "total_penalty_points": exam.total_penalty_points,
        "auto_fail_reason": exam.auto_fail_reason,
        "started_at": exam.started_at,
        "ended_at": exam.ended_at,
        "stages": [
            {
                "stage_key": s.stage_key,
                "stage_name": s.stage_name,
                "score": s.score,
                "penalty_points": s.penalty_points,
                "pass_fail": s.pass_fail,
                "duration_seconds": s.duration_seconds,
                "max_speed_kmh": s.max_speed_kmh,
                "min_speed_kmh": s.min_speed_kmh,
                "summary": s.summary,
                "violations": [{"event_type": e.event_type, "description": e.description, "severity": e.severity} for e in s.events],
            }
            for s in exam.stages
        ],
    }
