from datetime import datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Rider(Base, TimestampMixin):
    __tablename__ = "riders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), index=True)
    rider_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    national_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), unique=True)
    date_of_birth: Mapped[Date | None] = mapped_column(Date, nullable=True)


class Bike(Base, TimestampMixin):
    __tablename__ = "bikes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bike_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    bike_name: Mapped[str] = mapped_column(String(120))
    device_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    device_type: Mapped[str] = mapped_column(String(80), default="bike-monitor", index=True)
    hardware_revision: Mapped[str] = mapped_column(String(30), default="1.0")
    wheel_diameter_m: Mapped[float] = mapped_column(Float, default=0.65)
    wheel_circumference_m: Mapped[float] = mapped_column(Float, default=2.042)
    pulses_per_rotation: Mapped[int] = mapped_column(Integer, default=1)
    firmware_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class BikeStatus(Base, TimestampMixin):
    __tablename__ = "bike_statuses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bike_id: Mapped[int] = mapped_column(ForeignKey("bikes.id"), unique=True)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    battery_percent: Mapped[float] = mapped_column(Float, default=0.0)
    signal_health: Mapped[float] = mapped_column(Float, default=0.0)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    firmware_version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    update_status: Mapped[str] = mapped_column(String(30), default="idle")
    update_progress: Mapped[int] = mapped_column(Integer, default=0)
    target_firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_update_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    bike = relationship("Bike")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"))
    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="RWF")
    method: Mapped[str] = mapped_column(String(30), default="cash")
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="confirmed")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    rider = relationship("Rider")


class Exam(Base, TimestampMixin):
    __tablename__ = "exams"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    rider_id: Mapped[int] = mapped_column(ForeignKey("riders.id"))
    bike_id: Mapped[int] = mapped_column(ForeignKey("bikes.id"))
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    final_result: Mapped[str] = mapped_column(String(30), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, default=100)
    total_penalty_points: Mapped[int] = mapped_column(Integer, default=0)
    auto_fail_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_stage_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    last_telemetry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    finished_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    rider = relationship("Rider")
    bike = relationship("Bike")
    payment = relationship("Payment")
    stages = relationship("ExamStage", cascade="all, delete-orphan", back_populates="exam")


class ExamStage(Base, TimestampMixin):
    __tablename__ = "exam_stages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"))
    stage_key: Mapped[str] = mapped_column(String(50), index=True)
    stage_name: Mapped[str] = mapped_column(String(120))
    stage_order: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    score: Mapped[int] = mapped_column(Integer, default=25)
    penalty_points: Mapped[int] = mapped_column(Integer, default=0)
    pass_fail: Mapped[str] = mapped_column(String(30), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    min_speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    auto_fail_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status_hint: Mapped[str] = mapped_column(String(30), default="pending")
    rule_snapshot_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam = relationship("Exam", back_populates="stages")
    events = relationship("ExamEvent", cascade="all, delete-orphan", back_populates="stage")


class ExamEvent(Base, TimestampMixin):
    __tablename__ = "exam_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), index=True)
    stage_id: Mapped[int | None] = mapped_column(ForeignKey("exam_stages.id"), nullable=True)
    event_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(30), default="minor")
    penalty_points: Mapped[int] = mapped_column(Integer, default=0)
    auto_fail: Mapped[bool] = mapped_column(Boolean, default=False)
    event_second: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="system")
    detected_by: Mapped[str] = mapped_column(String(30), default="system")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    stage = relationship("ExamStage", back_populates="events")
    evidence = relationship("Evidence", cascade="all, delete-orphan", back_populates="event")


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("exam_events.id"), nullable=True)
    stage_key: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_path: Mapped[str] = mapped_column(Text)
    thumbnail_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event = relationship("ExamEvent", back_populates="evidence")


class TelemetryLog(Base, TimestampMixin):
    __tablename__ = "telemetry_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exam_id: Mapped[int | None] = mapped_column(ForeignKey("exams.id"), nullable=True)
    bike_id: Mapped[int | None] = mapped_column(ForeignKey("bikes.id"), nullable=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    pulse_count: Mapped[int] = mapped_column(Integer, default=0)
    window_ms: Mapped[int] = mapped_column(Integer, default=1000)
    speed_kmh: Mapped[float] = mapped_column(Float, default=0.0)
    battery_percent: Mapped[float] = mapped_column(Float, default=0.0)
    signal_health: Mapped[float] = mapped_column(Float, default=0.0)
    firmware_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source: Mapped[str] = mapped_column(String(30), default="mqtt")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    device_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FirmwareVersion(Base, TimestampMixin):
    __tablename__ = "firmware_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    version: Mapped[str] = mapped_column(String(50), index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    device_type: Mapped[str] = mapped_column(String(80), default="bike-monitor", index=True)
    hardware_revision_min: Mapped[str | None] = mapped_column(String(30), nullable=True)
    hardware_revision_max: Mapped[str | None] = mapped_column(String(30), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str] = mapped_column(Text)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str | None] = mapped_column(String(128), nullable=True)
    release_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class FirmwareUpdateLog(Base, TimestampMixin):
    __tablename__ = "firmware_update_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bike_id: Mapped[int | None] = mapped_column(ForeignKey("bikes.id"), nullable=True, index=True)
    device_id: Mapped[str] = mapped_column(String(120), index=True)
    firmware_version_id: Mapped[int | None] = mapped_column(ForeignKey("firmware_versions.id"), nullable=True)
    from_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_version: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    command_sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    result_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    bike = relationship("Bike")
    firmware = relationship("FirmwareVersion")


class Setting(Base, TimestampMixin):
    __tablename__ = "settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
