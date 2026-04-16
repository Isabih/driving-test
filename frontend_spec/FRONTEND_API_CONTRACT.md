# Frontend API Contract

## Live monitor

### GET /live/exams/{exam_id}/stage-view
Returns the active stage, live speed, and the camera list for the stage.

Example:
```json
{
  "exam_id": 12,
  "exam_code": "EXAM-012",
  "active_stage_key": "figure_8",
  "active_stage": {
    "stage_key": "figure_8",
    "stage_name": "Kunyura mu Munani (8-Course)",
    "status": "running",
    "pass_fail": "pending",
    "score": 25,
    "penalty_points": 0,
    "duration_seconds": 18.2,
    "max_speed_kmh": 11.6,
    "min_speed_kmh": 4.1
  },
  "speed_kmh": 9.5,
  "cameras": [
    {
      "camera_id": "cam_s1_overhead",
      "name": "Stage 1 Overhead",
      "role": "overhead",
      "viewer_url": "http://localhost:8889/stage1_overhead",
      "enabled": true
    },
    {
      "camera_id": "cam_s1_side_a",
      "name": "Stage 1 Side",
      "role": "side",
      "viewer_url": "http://localhost:8889/stage1_side_a",
      "enabled": true
    }
  ],
  "switching_mode": "single_active_stage",
  "next_stage_enabled_only_when_current_completed": true
}
```

## System meaning endpoint

### GET /system/connection-meaning
```json
{
  "backend_mqtt": "server -> broker",
  "device_mqtt": "ESP32 -> broker",
  "device_wifi": "ESP32 -> Wi-Fi access point"
}
```

## Camera stage endpoint

### GET /cameras/stages/{stage_key}
Returns the configured streams for a given stage.

## Frontend rendering rules

- Render all cameras in the active stage payload.
- Do not show other stage cameras in the main live area while one stage is active.
- Always render the speed gauge from `speed_kmh`.
- Show current stage metrics from `active_stage`.
- Show evidence below or beside the camera grid.
