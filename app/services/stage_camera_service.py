from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from app.core.config import settings

_DEFAULT = {
    "global": {
        "stream_base_url": "http://localhost:8889",
        "player_protocol": "webrtc_hls",
        "notes": "Replace placeholder stream URLs with your MediaMTX, Frigate, NVR/VMS, or camera RTSP restream URLs."
    },
    "stages": {
        "figure_8": {
            "label": "Kunyura mu Munani (8-Course)",
            "activation_mode": "exclusive",
            "cameras": [
                {
                    "camera_id": "cam_s1_overhead",
                    "name": "Stage 1 Overhead",
                    "role": "overhead",
                    "position": "pole_center",
                    "stream_name": "stage1_overhead",
                    "viewer_url": "http://localhost:8889/stage1_overhead",
                    "rtsp_url": "rtsp://USERNAME:PASSWORD@192.168.10.101:554/cam/realmonitor?channel=1&subtype=0",
                    "enabled": True,
                },
                {
                    "camera_id": "cam_s1_side_a",
                    "name": "Stage 1 Side",
                    "role": "side",
                    "position": "entry_diagonal",
                    "stream_name": "stage1_side_a",
                    "viewer_url": "http://localhost:8889/stage1_side_a",
                    "rtsp_url": "rtsp://USERNAME:PASSWORD@192.168.10.102:554/cam/realmonitor?channel=1&subtype=0",
                    "enabled": True,
                },
            ],
        },
        "zigzag": {
            "label": "Guhunga Inzitizi (Zigzag)",
            "activation_mode": "exclusive",
            "cameras": [
                {
                    "camera_id": "cam_s2_main",
                    "name": "Stage 2 Main",
                    "role": "diagonal",
                    "position": "mid_elevated",
                    "stream_name": "stage2_main",
                    "viewer_url": "http://localhost:8889/stage2_main",
                    "rtsp_url": "rtsp://USERNAME:PASSWORD@192.168.10.103:554/cam/realmonitor?channel=1&subtype=0",
                    "enabled": True,
                }
            ],
        },
        "narrow": {
            "label": "Kunyura mu Kayira Gafunganye (Narrow)",
            "activation_mode": "exclusive",
            "cameras": [
                {
                    "camera_id": "cam_s3_main",
                    "name": "Stage 3 Main",
                    "role": "overhead",
                    "position": "mid_overhead",
                    "stream_name": "stage3_main",
                    "viewer_url": "http://localhost:8889/stage3_main",
                    "rtsp_url": "rtsp://USERNAME:PASSWORD@192.168.10.104:554/cam/realmonitor?channel=1&subtype=0",
                    "enabled": True,
                }
            ],
        },
        "emergency_stop": {
            "label": "Guhagarara Bitunguranye (Emergency Stop)",
            "activation_mode": "exclusive",
            "cameras": [
                {
                    "camera_id": "cam_s4_main",
                    "name": "Stage 4 Main",
                    "role": "long_side",
                    "position": "runway_side",
                    "stream_name": "stage4_main",
                    "viewer_url": "http://localhost:8889/stage4_main",
                    "rtsp_url": "rtsp://USERNAME:PASSWORD@192.168.10.105:554/cam/realmonitor?channel=1&subtype=0",
                    "enabled": True,
                }
            ],
        },
    },
}


def _config_path() -> Path:
    return Path(settings.base_dir) / "config" / "stage_cameras.json"


def load_stage_camera_config() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_DEFAULT, indent=2), encoding="utf-8")
        return _DEFAULT
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _DEFAULT


def get_stage_cameras(stage_key: str) -> list[dict[str, Any]]:
    data = load_stage_camera_config()
    return data.get("stages", {}).get(stage_key, {}).get("cameras", [])


def get_stage_camera_payload(stage_key: str) -> dict[str, Any]:
    data = load_stage_camera_config()
    stage = data.get("stages", {}).get(stage_key, {})
    return {
        "stage_key": stage_key,
        "label": stage.get("label", stage_key),
        "activation_mode": stage.get("activation_mode", "exclusive"),
        "cameras": stage.get("cameras", []),
    }
