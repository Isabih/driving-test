from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.models import Bike, BikeStatus, Exam, ExamEvent, ExamStage, Payment, Rider, TelemetryLog
from app.services.constants import STAGES


def next_exam_code(db: Session) -> str:
    count = db.query(Exam).count() + 1
    return f"EXAM-{count:04d}"


def create_exam_with_stages(db: Session, rider_id: int, bike_id: int, payment_id: int, notes: str | None, created_by_user_id: int | None):
    rider = db.get(Rider, rider_id)
    bike = db.get(Bike, bike_id)
    payment = db.get(Payment, payment_id)
    if not rider or not bike or not payment:
        raise ValueError("Invalid rider, bike, or payment")
    active = db.query(Exam).filter(Exam.bike_id == bike_id, Exam.status.in_(["pending", "running"])).first()
    if active:
        raise ValueError("Bike already has an active exam")
    exam = Exam(
        exam_code=next_exam_code(db),
        rider_id=rider_id,
        bike_id=bike_id,
        payment_id=payment_id,
        notes=notes,
        created_by_user_id=created_by_user_id,
        status="pending",
        final_result="pending",
    )
    db.add(exam)
    db.flush()
    for key, name, order in STAGES:
        db.add(ExamStage(exam_id=exam.id, stage_key=key, stage_name=name, stage_order=order))
    db.commit()
    return db.query(Exam).options(joinedload(Exam.stages).joinedload(ExamStage.events)).get(exam.id)


def start_exam(db: Session, exam: Exam, user_id: int | None = None):
    exam.status = "running"
    exam.started_at = datetime.utcnow()
    exam.started_by_user_id = user_id
    first_stage = sorted(exam.stages, key=lambda x: x.stage_order)[0]
    exam.current_stage_key = first_stage.stage_key
    first_stage.status = "running"
    first_stage.started_at = datetime.utcnow()
    first_stage.status_hint = "looks_good"
    db.commit()
    db.refresh(exam)
    return exam


def transition_stage(db: Session, exam: Exam, stage_key: str):
    now = datetime.utcnow()
    current = db.query(ExamStage).filter(ExamStage.exam_id == exam.id, ExamStage.status == "running").first()
    if current:
        current.status = "finished"
        current.ended_at = now
        if current.started_at:
            current.duration_seconds = (current.ended_at - current.started_at).total_seconds()
        if current.pass_fail == "pending":
            current.pass_fail = "pass" if not current.auto_fail_reason else "fail"
    nxt = db.query(ExamStage).filter(ExamStage.exam_id == exam.id, ExamStage.stage_key == stage_key).first()
    if not nxt:
        raise ValueError("Stage not found")
    nxt.status = "running"
    nxt.started_at = nxt.started_at or now
    nxt.status_hint = "looks_good"
    exam.current_stage_key = stage_key
    db.commit()
    db.refresh(exam)
    return exam


def finish_exam(db: Session, exam: Exam, user_id: int | None = None, forced_result: str | None = None, notes: str | None = None):
    now = datetime.utcnow()
    for stage in exam.stages:
        if stage.status == "running":
            stage.status = "finished"
            stage.ended_at = now
            if stage.started_at:
                stage.duration_seconds = (stage.ended_at - stage.started_at).total_seconds()
        if stage.pass_fail == "pending":
            stage.pass_fail = "fail" if stage.auto_fail_reason else "pass"
    exam.status = "finished"
    exam.ended_at = now
    exam.finished_by_user_id = user_id
    if notes:
        exam.notes = (exam.notes or "") + f"\n{notes}"
    if forced_result:
        exam.final_result = forced_result
    elif exam.auto_fail_reason or any(s.pass_fail == "fail" for s in exam.stages):
        exam.final_result = "fail"
    else:
        exam.final_result = "pass"
    db.commit()
    db.refresh(exam)
    return exam


def add_stage_event(db: Session, exam: Exam, stage_key: str, payload: dict):
    stage = db.query(ExamStage).filter(ExamStage.exam_id == exam.id, ExamStage.stage_key == stage_key).first()
    if not stage:
        raise ValueError("Stage not found")
    event = ExamEvent(exam_id=exam.id, stage_id=stage.id, **payload)
    stage.penalty_points += payload.get("penalty_points", 0)
    stage.score = max(0, stage.score - payload.get("penalty_points", 0))
    stage.status_hint = "critical" if payload.get("auto_fail") else ("warning" if payload.get("penalty_points", 0) else "looks_good")
    if payload.get("auto_fail"):
        stage.pass_fail = "fail"
        stage.auto_fail_reason = payload.get("event_type")
        exam.auto_fail_reason = payload.get("event_type")
        exam.final_result = "fail"
    exam.total_penalty_points += payload.get("penalty_points", 0)
    exam.total_score = max(0, exam.total_score - payload.get("penalty_points", 0))
    db.add(event)
    db.commit()
    db.refresh(event)
    return event, stage


def compute_speed_kmh(pulse_count: int, window_ms: int, circumference_m: float, pulses_per_rotation: int) -> float:
    if pulse_count < 0 or window_ms <= 0 or circumference_m <= 0 or pulses_per_rotation <= 0:
        return 0.0
    rotations = pulse_count / pulses_per_rotation
    meters = rotations * circumference_m
    seconds = window_ms / 1000.0
    mps = meters / seconds if seconds else 0.0
    return round(mps * 3.6, 2)


def handle_telemetry(db: Session, payload: dict):
    bike = db.query(Bike).filter(Bike.device_id == payload["device_id"]).first()
    if not bike:
        raise ValueError("Unknown device")
    speed = compute_speed_kmh(payload["pulse_count"], payload["window_ms"], bike.wheel_circumference_m, bike.pulses_per_rotation)
    running_exam = db.query(Exam).filter(Exam.bike_id == bike.id, Exam.status == "running").first()
    log = TelemetryLog(
        exam_id=running_exam.id if running_exam else None,
        bike_id=bike.id,
        device_id=bike.device_id,
        pulse_count=payload["pulse_count"],
        window_ms=payload["window_ms"],
        speed_kmh=speed,
        battery_percent=payload.get("battery_percent", 0),
        signal_health=payload.get("signal_health", 0),
        firmware_version=payload.get("firmware_version"),
        source=payload.get("source", "mqtt"),
        timestamp=payload.get("timestamp") or datetime.utcnow(),
        device_time_ms=payload.get("device_time_ms"),
    )
    db.add(log)
    status = db.query(BikeStatus).filter(BikeStatus.bike_id == bike.id).first()
    if not status:
        status = BikeStatus(bike_id=bike.id)
        db.add(status)
    status.online = True
    status.last_seen_at = datetime.utcnow()
    status.last_speed_kmh = speed
    status.battery_percent = payload.get("battery_percent", 0)
    status.signal_health = payload.get("signal_health", 0)
    status.firmware_version = payload.get("firmware_version") or status.firmware_version
    if running_exam:
        running_exam.current_speed_kmh = speed
        running_exam.last_telemetry_at = datetime.utcnow()
        stage = db.query(ExamStage).filter(ExamStage.exam_id == running_exam.id, ExamStage.stage_key == running_exam.current_stage_key).first()
        if stage:
            stage.max_speed_kmh = max(stage.max_speed_kmh, speed)
            stage.min_speed_kmh = speed if stage.min_speed_kmh == 0 else min(stage.min_speed_kmh, speed)
    db.commit()
    return log, running_exam, bike
