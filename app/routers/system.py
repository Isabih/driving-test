from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.models import BikeStatus, Exam, User
from app.services.mqtt_service import mqtt_state

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/status")
def system_status(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return {
        "mqtt_enabled": True,
        "mqtt_connected": mqtt_state.connected,
        "active_exams": db.query(Exam).filter(Exam.status == "running").count(),
        "online_bikes": db.query(BikeStatus).filter(BikeStatus.online == True).count(),
        "server_time": datetime.utcnow().isoformat() + "Z",
    }


@router.get('/connection-meaning')
def connection_meaning(_: User = Depends(get_current_user)):
    return {
        'backend_mqtt': 'server -> broker',
        'device_mqtt': 'ESP32 -> broker',
        'device_wifi': 'ESP32 -> Wi-Fi access point',
    }
