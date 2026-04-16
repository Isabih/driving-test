# ESP32 Flashing Guide

## Arduino IDE

1. Install Arduino IDE 2.x.
2. Add ESP32 board URL:
   - `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. Install board package: `ESP32 by Espressif Systems`
4. Install libraries:
   - PubSubClient
   - ArduinoJson
5. Open `apaforme_bike_device.ino`
6. Replace Wi-Fi and MQTT values at the top of the sketch
7. Select board: `ESP32 Dev Module`
8. Select COM/serial port
9. Upload

## LED behavior

- Wi-Fi LED ON = device connected to Wi-Fi
- MQTT LED ON = device connected to MQTT broker/backend
- status LED blinks when telemetry is published

## First flash vs OTA

- first install: USB with Arduino IDE
- later firmware update: backend OTA command
