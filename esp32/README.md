# ESP32 Bike Device Notes

## LEDs
- `WIFI_LED_PIN`: turns ON when Wi-Fi is connected.
- `MQTT_LED_PIN`: turns ON when MQTT/backend connection is alive.
- `STATUS_LED_PIN`: quick blink when telemetry is published.

## Main behavior
- reads Hall sensor pulses
- publishes telemetry every second to `apaforme/bikes/telemetry`
- subscribes to `apaforme/bikes/commands/<DEVICE_ID>`
- reacts to `start_exam`, `finish_exam`, and `ping`

## Required Arduino libraries
- WiFi
- PubSubClient
- ArduinoJson

## Example command from backend/manual publish
```json
{"action":"start_exam","exam_code":"EXAM-0001"}
```


## OTA additions required
- Add `FW_VERSION`, `DEVICE_TYPE`, and `HARDWARE_REV` constants.
- Subscribe to firmware update command on `apaforme/bikes/commands/<DEVICE_ID>`.
- When action is `update_firmware`, read:
  - `version`
  - `url`
  - `sha256`
  - `size`
  - `force`
- Download the `.bin` file from the backend static URL and flash it with OTA.
- Publish update progress/status to `apaforme/bikes/ota/status` or call `POST /firmware/status-report`.
- After reboot, report the new firmware version in normal device status/heartbeat.
