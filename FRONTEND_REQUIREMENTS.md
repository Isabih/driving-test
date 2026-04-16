# APAFORME Frontend Requirements (Updated with OTA Firmware Management)

## Roles
- **Admin**: full access, firmware upload, set latest version, trigger updates, manage users/settings.
- **Operator**: can view devices, exams, records, evidence, and live updates, but cannot upload firmware or trigger OTA unless you decide to grant it.

## New OTA / Firmware pages and widgets

### 1) Device Firmware Dashboard
Show a table with:
- Device ID
- Bike code
- Bike name
- Device type
- Hardware revision
- Online/offline badge
- Battery percentage
- Signal health
- Current firmware version
- Latest firmware version
- Target firmware version
- Update needed badge
- Update status badge
- Update progress bar
- Last seen
- Actions: `Update`, `View Logs`

### 2) Firmware Management Page
Show a table with:
- Version
- Display name
- Device type
- Release notes
- File size
- Uploaded date
- Latest flag
- Active flag
- Actions: `Set Latest`, `Edit`, `Download`

### 3) Upload Firmware Modal
Fields:
- Firmware file (`.bin` or `.zip`)
- Version
- Display name
- Release notes
- Device type
- Hardware revision min
- Hardware revision max
- `Set as latest` checkbox

### 4) Device Update Log Drawer/Page
Show device update history:
- status
- from version
- target version
- progress
- result message
- error message
- command sent time
- started time
- completed time

## New endpoints for frontend

### Firmware inventory
- `GET /firmware`
- `POST /firmware/upload`
- `PATCH /firmware/{firmware_id}`
- `PATCH /firmware/{firmware_id}/set-latest`

### Device firmware status
- `GET /firmware/devices`
- `GET /firmware/devices/{device_id}/logs`
- `POST /firmware/devices/{device_id}/update`

### Existing core pages still needed
- Dashboard summary
- Live exams
- Riders
- Bikes
- Payments
- Records/history
- Evidence gallery
- Settings
- Users

## WebSocket events to support in UI
Subscribe to `/ws` and handle at least:
- `telemetry_update`
- `event_detected`
- `evidence_uploaded`
- `stage_changed`
- `exam_finished`
- `firmware_status`

For `firmware_status`, update the device row live when an ESP32 reports OTA progress.

## UI behavior rules
- If `current firmware version != latest firmware version`, show **Update Available**.
- If device is offline, disable the **Update** button.
- Show progress states: `queued`, `command_sent`, `downloading`, `flashing`, `rebooting`, `success`, `failed`.
- After success, refresh device firmware version automatically.
- Allow admin to edit generated display name after upload.

## API contracts to implement in frontend hooks

### Hook: `useFirmwareList()`
Calls `GET /firmware`

### Hook: `useFirmwareDevices()`
Calls `GET /firmware/devices`

### Hook: `useUploadFirmware()`
Calls `POST /firmware/upload` with multipart form-data

### Hook: `useTriggerDeviceUpdate(deviceId)`
Calls `POST /firmware/devices/{device_id}/update`
Payload:
```json
{
  "target_version": "1.1.0",
  "force": false
}
```

### Hook: `useDeviceFirmwareLogs(deviceId)`
Calls `GET /firmware/devices/{device_id}/logs`

## MQTT / OTA messaging assumptions for frontend explanations
- Backend sends command to `apaforme/bikes/commands/{device_id}`
- ESP32 reports OTA progress to `apaforme/bikes/ota/status`
- Backend maps that to API + WebSocket updates

## Nice UX extras
- Progress bar in device row during update
- Firmware version badges
- Release notes modal
- Bulk update UI later
- Filter by device type, status, update needed
