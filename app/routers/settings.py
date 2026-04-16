from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import require_roles
from app.models.models import Setting, User
from app.services.settings_service import get_settings_map

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    values: dict[str, str]


@router.get("")
def get_settings(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    return get_settings_map(db)


@router.put("")
def update_settings(payload: SettingsUpdate, db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))):
    for key, value in payload.values.items():
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    db.commit()
    return get_settings_map(db)


@router.get("/public-runtime")
def public_runtime(db: Session = Depends(get_db), _: User = Depends(require_roles("admin", "operator"))):
    settings = get_settings_map(db)
    keys = ["exam_total_duration_seconds", "start_timeout_seconds", "foot_down_max_seconds", "indicator_cancel_seconds", "narrow_min_duration_seconds", "emergency_stop_min_speed_kmh", "emergency_start_max_speed_kmh"]
    return {k: settings.get(k) for k in keys}
