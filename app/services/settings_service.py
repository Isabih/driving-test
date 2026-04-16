from sqlalchemy.orm import Session
from app.models.models import Setting
from app.services.constants import DEFAULT_SETTINGS


def ensure_default_settings(db: Session):
    for key, value in DEFAULT_SETTINGS.items():
        exists = db.query(Setting).filter(Setting.key == key).first()
        if not exists:
            db.add(Setting(key=key, value=value))
    db.commit()


def get_settings_map(db: Session) -> dict[str, str]:
    ensure_default_settings(db)
    rows = db.query(Setting).all()
    return {r.key: r.value for r in rows}
