import asyncio
import hashlib
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from packaging.version import InvalidVersion, Version
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Bike, BikeStatus, FirmwareUpdateLog, FirmwareVersion
from app.services.websocket_manager import manager


class FirmwareValidationError(ValueError):
    pass


def parse_version(value: str) -> Version:
    try:
        return Version(value.strip())
    except InvalidVersion as exc:
        raise FirmwareValidationError(f"Invalid semantic version: {value}") from exc


def version_is_newer(current: str | None, latest: str | None) -> bool:
    if not current or not latest:
        return False
    try:
        return parse_version(latest) > parse_version(current)
    except FirmwareValidationError:
        return latest != current


def firmware_storage_dir(device_type: str, version: str) -> Path:
    return Path(settings.firmware_dir) / device_type / version


def sha256_for_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_public_file_url(device_type: str, version: str, filename: str) -> str:
    base = settings.public_base_url.rstrip("/")
    if not base:
        return f"/firmware-files/{device_type}/{version}/{filename}"
    return f"{base}/firmware-files/{device_type}/{version}/{filename}"


def _extract_zip(zip_path: Path, target_dir: Path) -> tuple[Path, dict]:
    manifest = {}
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(target_dir)
    manifest_path = next(iter(target_dir.rglob("manifest.json")), None)
    if manifest_path and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
    bin_candidates = list(target_dir.rglob("*.bin"))
    if not bin_candidates:
        raise FirmwareValidationError("ZIP package does not contain a .bin firmware file")
    return bin_candidates[0], manifest


def save_uploaded_firmware(db: Session, uploaded_file, version: str | None, display_name: str | None,
                           release_notes: str | None, device_type: str, set_as_latest: bool,
                           uploaded_by_user_id: int | None, hw_min: str | None = None, hw_max: str | None = None):
    original_name = uploaded_file.filename or "firmware.bin"
    suffix = Path(original_name).suffix.lower()
    temp_dir = Path(settings.firmware_temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_upload = temp_dir / original_name
    with temp_upload.open("wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)

    manifest = {}
    if suffix == ".zip":
        extract_dir = temp_dir / f"extract_{datetime.utcnow().timestamp()}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        bin_file, manifest = _extract_zip(temp_upload, extract_dir)
    elif suffix == ".bin":
        bin_file = temp_upload
    else:
        raise FirmwareValidationError("Only .bin or .zip firmware uploads are supported")

    resolved_version = (version or manifest.get("version") or "").strip()
    if not resolved_version:
        raise FirmwareValidationError("Firmware version is required either in form field or manifest.json")
    parse_version(resolved_version)

    device_type = (device_type or manifest.get("device_type") or "bike-monitor").strip()
    display_name = (display_name or f"{device_type.replace('-', ' ').title()} Firmware v{resolved_version}").strip()
    release_notes = release_notes if release_notes is not None else manifest.get("release_notes")
    hw_min = hw_min or manifest.get("min_hardware_rev")
    hw_max = hw_max or manifest.get("max_hardware_rev")

    existing = db.query(FirmwareVersion).filter(FirmwareVersion.device_type == device_type, FirmwareVersion.version == resolved_version).first()
    if existing:
        raise FirmwareValidationError(f"Firmware version {resolved_version} already exists for {device_type}")

    store_dir = firmware_storage_dir(device_type, resolved_version)
    store_dir.mkdir(parents=True, exist_ok=True)
    stored_filename = "firmware.bin"
    final_path = store_dir / stored_filename
    shutil.copy2(bin_file, final_path)
    file_size = final_path.stat().st_size
    digest = sha256_for_file(final_path)
    file_url = build_public_file_url(device_type, resolved_version, stored_filename)

    if set_as_latest:
        db.query(FirmwareVersion).filter(FirmwareVersion.device_type == device_type, FirmwareVersion.is_latest == True).update({FirmwareVersion.is_latest: False})

    record = FirmwareVersion(
        version=resolved_version,
        display_name=display_name,
        device_type=device_type,
        hardware_revision_min=hw_min,
        hardware_revision_max=hw_max,
        filename=stored_filename,
        original_filename=original_name,
        file_path=str(final_path),
        file_url=file_url,
        file_size=file_size,
        sha256=digest,
        release_notes=release_notes,
        is_latest=set_as_latest,
        is_active=True,
        uploaded_by_user_id=uploaded_by_user_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def set_latest_firmware(db: Session, firmware: FirmwareVersion):
    db.query(FirmwareVersion).filter(FirmwareVersion.device_type == firmware.device_type, FirmwareVersion.is_latest == True).update({FirmwareVersion.is_latest: False})
    firmware.is_latest = True
    db.commit()
    db.refresh(firmware)
    return firmware


def get_latest_firmware(db: Session, device_type: str) -> FirmwareVersion | None:
    return db.query(FirmwareVersion).filter(FirmwareVersion.device_type == device_type, FirmwareVersion.is_active == True, FirmwareVersion.is_latest == True).order_by(FirmwareVersion.created_at.desc()).first()


def create_update_log(db: Session, bike: Bike, firmware: FirmwareVersion, requested_by_user_id: int | None):
    status = db.query(BikeStatus).filter(BikeStatus.bike_id == bike.id).first()
    if not status:
        status = BikeStatus(bike_id=bike.id, firmware_version=bike.firmware_version)
        db.add(status)
        db.flush()
    status.update_status = "queued"
    status.update_progress = 0
    status.target_firmware_version = firmware.version
    status.last_update_message = f"Queued update to {firmware.version}"
    log = FirmwareUpdateLog(
        bike_id=bike.id,
        device_id=bike.device_id,
        firmware_version_id=firmware.id,
        from_version=status.firmware_version or bike.firmware_version,
        target_version=firmware.version,
        status="queued",
        progress=0,
        requested_by_user_id=requested_by_user_id,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log, status


def update_status_from_report(db: Session, payload: dict):
    bike = db.query(Bike).filter(Bike.device_id == payload["device_id"]).first()
    if not bike:
        raise FirmwareValidationError("Unknown device ID")
    status = db.query(BikeStatus).filter(BikeStatus.bike_id == bike.id).first()
    if not status:
        status = BikeStatus(bike_id=bike.id, firmware_version=bike.firmware_version)
        db.add(status)
        db.flush()
    status.online = True
    status.last_seen_at = datetime.utcnow()
    status.ip_address = payload.get("ip_address") or status.ip_address
    status.update_status = payload.get("status", status.update_status)
    status.update_progress = max(0, min(100, int(payload.get("progress", status.update_progress or 0))))
    status.last_update_message = payload.get("message") or status.last_update_message
    if payload.get("target_version"):
        status.target_firmware_version = payload["target_version"]
    if payload.get("firmware_version"):
        status.firmware_version = payload["firmware_version"]
        bike.firmware_version = payload["firmware_version"]

    log = db.query(FirmwareUpdateLog).filter(
        FirmwareUpdateLog.device_id == bike.device_id,
        FirmwareUpdateLog.status.in_(["queued", "command_sent", "downloading", "flashing", "rebooting"]),
    ).order_by(FirmwareUpdateLog.created_at.desc()).first()
    if log:
        log.status = status.update_status
        log.progress = status.update_progress
        if status.update_status in {"downloading", "flashing", "rebooting"} and not log.started_at:
            log.started_at = datetime.utcnow()
        if status.update_status == "success":
            log.completed_at = datetime.utcnow()
            log.result_message = payload.get("message") or "Firmware updated successfully"
            log.progress = 100
            status.update_progress = 100
        elif status.update_status == "failed":
            log.completed_at = datetime.utcnow()
            log.error_message = payload.get("message") or "Firmware update failed"
    db.commit()
    try:
        asyncio.run(manager.broadcast({"type": "firmware_status", "device_id": bike.device_id, "status": status.update_status, "progress": status.update_progress, "message": status.last_update_message, "firmware_version": status.firmware_version, "target_version": status.target_firmware_version}))
    except RuntimeError:
        pass
    return bike, status, log
