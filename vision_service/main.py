import json
import os
import time
from pathlib import Path
from typing import Dict, Any

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")
STAGE_CAMERA_CONFIG = os.getenv("STAGE_CAMERA_CONFIG", str(Path(__file__).resolve().parents[1] / "config" / "stage_cameras.json"))
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "3"))
ACTIVE_EXAM_ID = os.getenv("ACTIVE_EXAM_ID", "")


def headers() -> dict[str, str]:
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    return {}


def load_config() -> Dict[str, Any]:
    return json.loads(Path(STAGE_CAMERA_CONFIG).read_text(encoding="utf-8"))


def get_stage_view(exam_id: str) -> Dict[str, Any] | None:
    if not exam_id:
        return None
    r = requests.get(f"{API_BASE_URL}/live/exams/{exam_id}/stage-view", headers=headers(), timeout=10)
    if r.ok:
        return r.json()
    return None


def main() -> None:
    print("APAForme vision service skeleton started")
    print("This service is stage-aware and should only process the active stage cameras.")
    current_stage = None
    while True:
        try:
            if ACTIVE_EXAM_ID:
                payload = get_stage_view(ACTIVE_EXAM_ID)
                if payload:
                    stage = payload.get("active_stage_key")
                    if stage != current_stage:
                        current_stage = stage
                        cams = payload.get("cameras", [])
                        print(f"Switched active stage to {stage}. Cameras now active: {[c.get('camera_id') for c in cams]}")
                    print(f"Live speed: {payload.get('speed_kmh', 0)} km/h")
            else:
                print("Set ACTIVE_EXAM_ID environment variable or extend this service to auto-select running exams.")
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(f"Vision service error: {exc}")
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
