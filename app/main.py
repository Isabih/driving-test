import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.db import Base, SessionLocal, engine
from app.core.security import get_password_hash
from app.models.models import User
from app.routers import auth, bikes, cameras, dashboard, exams, evidence, firmware, live, payments, records, reference, riders, settings as settings_router, system, users
from app.services.mqtt_service import mqtt_service
from app.services.settings_service import ensure_default_settings
from app.services.websocket_manager import manager

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(riders.router)
app.include_router(bikes.router)
app.include_router(cameras.router)
app.include_router(payments.router)
app.include_router(exams.router)
app.include_router(dashboard.router)
app.include_router(live.router)
app.include_router(records.router)
app.include_router(evidence.router)
app.include_router(firmware.router)
app.include_router(settings_router.router)
app.include_router(system.router)
app.include_router(reference.router)


@app.on_event("startup")
def startup():
    os.makedirs(settings.evidence_dir, exist_ok=True)
    os.makedirs(settings.firmware_dir, exist_ok=True)
    os.makedirs(settings.firmware_temp_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_settings(db)
        admin = db.query(User).filter(User.email == "admin@apaforme.rw").first()
        if not admin:
            db.add(User(full_name="System Admin", email="admin@apaforme.rw", hashed_password=get_password_hash("Admin123!"), role="admin", is_active=True))
            db.commit()
    finally:
        db.close()
    mqtt_service.start()


@app.get("/")
def root():
    return {"name": settings.app_name, "status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


app.mount("/firmware-files", StaticFiles(directory=settings.firmware_dir), name="firmware-files")
app.mount("/evidence-files", StaticFiles(directory=settings.evidence_dir), name="evidence-files")
