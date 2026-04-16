# APAFORME Smart Riding Exam System — Final Bundle

This package combines the main cloud/backend API, local field server deployment files, ESP32 firmware, stage-aware camera mapping, firmware OTA support, and frontend handoff files for V0.

## What is included

- FastAPI backend for riders, bikes, payments, exams, scoring, evidence, dashboard, live monitor, OTA, settings, records, and user roles.
- Local field server deployment files for:
  - Mosquitto (MQTT)
  - MediaMTX (RTSP/WebRTC/HLS restreaming)
  - Vision service skeleton
- ESP32 firmware for telemetry + Wi-Fi LED + MQTT LED + OTA commands.
- Frontend handoff files for V0 with live streaming dashboard requirements.
- Stage camera mapping so only the active stage cameras are processed.

## Important reality check

This bundle is designed to be as close to turnkey as possible, but you still must fill in a few site-specific values:

- actual camera RTSP credentials/IPs
- actual Wi-Fi SSID/password for ESP32
- actual MQTT host/IP if different from the default compose setup
- optional domain / HTTPS configuration for production cloud deployment

## Core architecture

- Cloud/backend: main API, database, dashboard, reports, OTA metadata.
- Local field server: camera ingest, live restreaming, active-stage-only vision processing.
- ESP32: bike telemetry + MQTT control.

## Quick start options

### Option A — local all-in-one field demo

1. Copy `.env.example` to `.env`
2. Edit values if needed
3. Start local stack:

```bash
cd deployments/local-server
cp ../../.env.example ../../.env
sudo docker compose up -d --build
```

This starts:
- backend API
- Postgres
- Mosquitto
- MediaMTX
- vision service skeleton

### Option B — backend only

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Default login

- Email: `admin@apaforme.rw`
- Password: `Admin123!`

Change it after first login.

## Key live monitor endpoints

- `GET /dashboard/summary`
- `GET /dashboard/running-exams`
- `GET /live/exams`
- `GET /live/exams/{exam_id}`
- `GET /live/exams/{exam_id}/stage-view`
- `GET /cameras/stages`
- `GET /cameras/stages/{stage_key}`
- `GET /system/connection-meaning`

## Stage-aware switching model

Only one stage is active at a time.

- Stage 1 runs → only Stage 1 cameras are processed
- When Stage 1 is finished → Stage 2 becomes active
- Stage 1 processing stops → Stage 2 cameras start
- Repeat through Stage 4

This reduces compute load and matches the exam workflow.

## Main folders

- `app/` backend code
- `esp32/` ESP32 sketch and flashing guide
- `config/stage_cameras.json` stage-camera mapping
- `deployments/local-server/` local server compose stack
- `vision_service/` local inference service skeleton
- `frontend_spec/` V0 prompts and API contract
- `docs/` deployment and camera placement docs
- `scripts/` helper scripts
.env example links 


CAM1_RTSP=rtsp://admin:iSabih123!@192.168.1.57:554/Streaming/Channels/101
CAM2_RTSP=rtsp://admin:iSabih123!@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0
CAM3_RTSP=rtsp://admin:123456@192.168.1.188:554/ch01.264
CAM4_RTSP=rtsp://admin:iSabih123!@192.168.1.79:554/media/video1

YOLO_MODEL=yolo11n.pt
FRAME_WIDTH=960
FRAME_HEIGHT=540
JPEG_QUALITY=80
DETECTION_CONFIDENCE=0.35
ACTIVE_CAMERA=cam3