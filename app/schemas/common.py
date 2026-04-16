from datetime import date, datetime
from pydantic import BaseModel


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    full_name: str
    role: str


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "operator"
    is_active: bool = True


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class RiderCreate(BaseModel):
    full_name: str
    rider_code: str
    national_id: str
    phone: str
    date_of_birth: date | None = None


class RiderOut(RiderCreate):
    id: int

    class Config:
        from_attributes = True


class BikeCreate(BaseModel):
    bike_code: str
    bike_name: str
    device_id: str
    device_type: str = "bike-monitor"
    hardware_revision: str = "1.0"
    wheel_diameter_m: float = 0.65
    wheel_circumference_m: float = 2.042
    pulses_per_rotation: int = 1
    firmware_version: str = "1.0.0"
    is_active: bool = True


class BikeOut(BikeCreate):
    id: int

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    rider_id: int
    amount: float
    currency: str = "RWF"
    method: str = "cash"
    reference: str
    status: str = "confirmed"
    notes: str | None = None


class PaymentOut(PaymentCreate):
    id: int

    class Config:
        from_attributes = True


class ExamCreate(BaseModel):
    rider_id: int
    bike_id: int
    payment_id: int
    notes: str | None = None


class StageTransitionIn(BaseModel):
    stage_key: str


class StageEventCreate(BaseModel):
    event_type: str
    description: str
    severity: str = "minor"
    penalty_points: int = 0
    auto_fail: bool = False
    event_second: float | None = None
    speed_kmh: float | None = None
    source: str = "vision"
    detected_by: str = "vision"
    metadata_json: str | None = None


class TelemetryIn(BaseModel):
    device_id: str
    pulse_count: int
    window_ms: int = 1000
    battery_percent: float = 0.0
    signal_health: float = 0.0
    source: str = "mqtt"
    firmware_version: str | None = None
    timestamp: datetime | None = None
    device_time_ms: int | None = None


class FinishExamIn(BaseModel):
    notes: str | None = None
    final_result: str | None = None


class ExamEventOut(BaseModel):
    id: int
    event_type: str
    description: str
    severity: str
    penalty_points: int
    auto_fail: bool
    event_second: float | None = None
    speed_kmh: float | None = None
    source: str
    detected_by: str
    captured_at: datetime

    class Config:
        from_attributes = True


class ExamStageOut(BaseModel):
    id: int
    stage_key: str
    stage_name: str
    stage_order: int
    status: str
    score: int
    penalty_points: int
    pass_fail: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    duration_seconds: float | None = None
    max_speed_kmh: float
    min_speed_kmh: float
    auto_fail_reason: str | None = None
    summary: str | None = None
    status_hint: str
    events: list[ExamEventOut] = []

    class Config:
        from_attributes = True


class ExamOut(BaseModel):
    id: int
    exam_code: str
    rider_id: int
    bike_id: int
    payment_id: int
    status: str
    final_result: str
    started_at: datetime | None = None
    ended_at: datetime | None = None
    total_score: int
    total_penalty_points: int
    auto_fail_reason: str | None = None
    notes: str | None = None
    current_stage_key: str | None = None
    current_speed_kmh: float
    last_telemetry_at: datetime | None = None
    created_at: datetime
    stages: list[ExamStageOut] = []

    class Config:
        from_attributes = True


class PaginatedOut(BaseModel):
    items: list
    page: int
    page_size: int
    total: int


class FirmwareOut(BaseModel):
    id: int
    version: str
    display_name: str
    device_type: str
    hardware_revision_min: str | None = None
    hardware_revision_max: str | None = None
    filename: str
    file_url: str | None = None
    file_size: int
    sha256: str | None = None
    release_notes: str | None = None
    is_latest: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class FirmwareUpdateRequest(BaseModel):
    target_version: str | None = None
    firmware_id: int | None = None
    force: bool = False


class FirmwareEditIn(BaseModel):
    display_name: str | None = None
    release_notes: str | None = None
    is_active: bool | None = None
    is_latest: bool | None = None


class FirmwareDeviceStatusOut(BaseModel):
    bike_id: int
    bike_code: str
    bike_name: str
    device_id: str
    device_type: str
    hardware_revision: str
    online: bool
    battery_percent: float
    signal_health: float
    current_firmware_version: str
    latest_firmware_version: str | None = None
    target_firmware_version: str | None = None
    update_status: str
    update_progress: int
    update_needed: bool
    last_seen_at: datetime | None = None


class FirmwareStatusReportIn(BaseModel):
    device_id: str
    status: str
    progress: int = 0
    message: str | None = None
    firmware_version: str | None = None
    target_version: str | None = None
    ip_address: str | None = None


class FirmwareUpdateLogOut(BaseModel):
    id: int
    device_id: str
    from_version: str | None = None
    target_version: str
    status: str
    progress: int
    result_message: str | None = None
    error_message: str | None = None
    command_sent_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
