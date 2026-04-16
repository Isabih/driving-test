from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.models.models import User
from app.services.stage_camera_service import load_stage_camera_config, get_stage_camera_payload

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.get("")
def list_cameras(_: User = Depends(get_current_user)):
    data = load_stage_camera_config()
    items = []
    for stage_key, stage in data.get("stages", {}).items():
        for camera in stage.get("cameras", []):
            items.append({**camera, "stage_key": stage_key, "stage_label": stage.get("label", stage_key)})
    return {
        "global": data.get("global", {}),
        "items": items,
    }


@router.get("/stages")
def stage_camera_index(_: User = Depends(get_current_user)):
    data = load_stage_camera_config()
    return [get_stage_camera_payload(stage_key) for stage_key in data.get("stages", {}).keys()]


@router.get("/stages/{stage_key}")
def stage_camera_detail(stage_key: str, _: User = Depends(get_current_user)):
    return get_stage_camera_payload(stage_key)
