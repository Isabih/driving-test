from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, require_roles
from app.models.models import Bike, BikeStatus, FirmwareUpdateLog, FirmwareVersion, User
from app.schemas.common import FirmwareDeviceStatusOut, FirmwareEditIn, FirmwareOut, FirmwareStatusReportIn, FirmwareUpdateLogOut, FirmwareUpdateRequest
from app.services.firmware_service import (
    FirmwareValidationError,
    create_update_log,
    get_latest_firmware,
    save_uploaded_firmware,
    set_latest_firmware,
    update_status_from_report,
    version_is_newer,
)
from app.services.mqtt_service import mqtt_service

router = APIRouter(prefix="/firmware", tags=["firmware"])


@router.get("", response_model=list[FirmwareOut])
def list_firmware(device_type: str | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    query = db.query(FirmwareVersion)
    if device_type:
        query = query.filter(FirmwareVersion.device_type == device_type)
    return query.order_by(FirmwareVersion.device_type.asc(), FirmwareVersion.created_at.desc()).all()


@router.post("/upload", response_model=FirmwareOut)
def upload_firmware(
    file: UploadFile = File(...),
    version: str | None = Form(default=None),
    display_name: str | None = Form(default=None),
    release_notes: str | None = Form(default=None),
    device_type: str = Form(default="bike-monitor"),
    set_as_latest: bool = Form(default=True),
    hardware_revision_min: str | None = Form(default=None),
    hardware_revision_max: str | None = Form(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    try:
        return save_uploaded_firmware(
            db=db,
            uploaded_file=file,
            version=version,
            display_name=display_name,
            release_notes=release_notes,
            device_type=device_type,
            set_as_latest=set_as_latest,
            uploaded_by_user_id=user.id,
            hw_min=hardware_revision_min,
            hw_max=hardware_revision_max,
        )
    except FirmwareValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{firmware_id}", response_model=FirmwareOut)
def edit_firmware(firmware_id: int, payload: FirmwareEditIn, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    firmware = db.get(FirmwareVersion, firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(firmware, key, value)
    if payload.is_latest:
        set_latest_firmware(db, firmware)
        return firmware
    db.commit()
    db.refresh(firmware)
    return firmware


@router.patch("/{firmware_id}/set-latest", response_model=FirmwareOut)
def make_latest(firmware_id: int, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    firmware = db.get(FirmwareVersion, firmware_id)
    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware not found")
    return set_latest_firmware(db, firmware)


@router.get("/devices", response_model=list[FirmwareDeviceStatusOut])
def device_firmware_status(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    bikes = db.query(Bike).order_by(Bike.id.desc()).all()
    items = []
    for bike in bikes:
        status = db.query(BikeStatus).filter(BikeStatus.bike_id == bike.id).first()
        latest = get_latest_firmware(db, bike.device_type)
        current_version = (status.firmware_version if status else bike.firmware_version) or bike.firmware_version
        items.append(FirmwareDeviceStatusOut(
            bike_id=bike.id,
            bike_code=bike.bike_code,
            bike_name=bike.bike_name,
            device_id=bike.device_id,
            device_type=bike.device_type,
            hardware_revision=bike.hardware_revision,
            online=status.online if status else False,
            battery_percent=status.battery_percent if status else 0,
            signal_health=status.signal_health if status else 0,
            current_firmware_version=current_version,
            latest_firmware_version=latest.version if latest else None,
            target_firmware_version=status.target_firmware_version if status else None,
            update_status=status.update_status if status else "idle",
            update_progress=status.update_progress if status else 0,
            update_needed=version_is_newer(current_version, latest.version) if latest else False,
            last_seen_at=status.last_seen_at if status else None,
        ))
    return items


@router.get("/devices/{device_id}/logs", response_model=list[FirmwareUpdateLogOut])
def device_update_logs(device_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(FirmwareUpdateLog).filter(FirmwareUpdateLog.device_id == device_id).order_by(FirmwareUpdateLog.created_at.desc()).limit(50).all()


@router.post("/devices/{device_id}/update")
def trigger_update(device_id: str, payload: FirmwareUpdateRequest, db: Session = Depends(get_db), user: User = Depends(require_roles("admin"))):
    bike = db.query(Bike).filter(Bike.device_id == device_id).first()
    if not bike:
        raise HTTPException(status_code=404, detail="Device not found")
    status = db.query(BikeStatus).filter(BikeStatus.bike_id == bike.id).first()
    if not status or not status.online:
        raise HTTPException(status_code=400, detail="Device is offline")

    firmware = None
    if payload.firmware_id:
        firmware = db.get(FirmwareVersion, payload.firmware_id)
    elif payload.target_version:
        firmware = db.query(FirmwareVersion).filter(
            FirmwareVersion.device_type == bike.device_type,
            FirmwareVersion.version == payload.target_version,
            FirmwareVersion.is_active == True,
        ).first()
    else:
        firmware = get_latest_firmware(db, bike.device_type)
    if not firmware:
        raise HTTPException(status_code=404, detail="Firmware version not found")
    if firmware.device_type != bike.device_type:
        raise HTTPException(status_code=400, detail="Firmware device type does not match the selected bike")
    if not payload.force and firmware.version == (status.firmware_version or bike.firmware_version):
        raise HTTPException(status_code=400, detail="Device is already on this firmware version")

    log, status = create_update_log(db, bike, firmware, user.id)
    log.status = "command_sent"
    log.command_sent_at = datetime.utcnow()
    status.update_status = "command_sent"
    status.last_update_message = f"Update command sent for {firmware.version}"
    db.commit()

    mqtt_service.publish_command(device_id, "update_firmware", {
        "version": firmware.version,
        "url": firmware.file_url,
        "sha256": firmware.sha256,
        "size": firmware.file_size,
        "force": payload.force,
        "device_type": firmware.device_type,
    })
    return {
        "message": "Firmware update command sent",
        "device_id": device_id,
        "target_version": firmware.version,
        "file_url": firmware.file_url,
        "log_id": log.id,
    }


@router.post("/status-report")
def firmware_status_report(payload: FirmwareStatusReportIn, db: Session = Depends(get_db)):
    try:
        bike, status, log = update_status_from_report(db, payload.model_dump())
    except FirmwareValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "message": "Status recorded",
        "device_id": bike.device_id,
        "status": status.update_status,
        "progress": status.update_progress,
        "firmware_version": status.firmware_version,
        "log_id": log.id if log else None,
    }
