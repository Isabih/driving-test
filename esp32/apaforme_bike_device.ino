#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===== USER SETTINGS =====
const char* WIFI_SSID = "YOUR_WIFI_NAME";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_HOST = "192.168.1.100";
const int MQTT_PORT = 1883;
const char* MQTT_USERNAME = "";
const char* MQTT_PASSWORD = "";
const char* DEVICE_ID = "ESP32_BIKE_001";
const char* FIRMWARE_VERSION = "1.0.0";

// ===== TOPICS =====
String telemetryTopic = "apaforme/bikes/telemetry";
String statusTopic = "apaforme/bikes/status";
String commandTopic = String("apaforme/bikes/commands/") + DEVICE_ID;

// ===== PINS =====
const int HALL_SENSOR_PIN = 27;
const int WIFI_LED_PIN = 2;      // ON when WiFi connected
const int MQTT_LED_PIN = 4;      // ON when MQTT connected to backend
const int STATUS_LED_PIN = 5;    // blinks on publish

volatile unsigned long pulseCount = 0;
unsigned long lastPublishMs = 0;
unsigned long publishIntervalMs = 1000;
unsigned long lastStatusMs = 0;
unsigned long statusIntervalMs = 5000;

float batteryPercent = 100.0;
float signalHealth = 100.0;
bool examActive = false;

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void IRAM_ATTR onPulse() {
  pulseCount++;
}

void connectWiFi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    digitalWrite(WIFI_LED_PIN, LOW);
    delay(300);
  }
  digitalWrite(WIFI_LED_PIN, HIGH);
}

void publishStatus(const char* state) {
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["state"] = state;
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["wifi_rssi"] = WiFi.RSSI();
  doc["signal_health"] = signalHealth;
  char buffer[256];
  serializeJson(doc, buffer);
  mqttClient.publish(statusTopic.c_str(), buffer, true);
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) return;

  const char* action = doc["action"] | "";
  if (strcmp(action, "start_exam") == 0) {
    examActive = true;
    publishStatus("exam_started");
  } else if (strcmp(action, "finish_exam") == 0) {
    examActive = false;
    publishStatus("exam_finished");
  } else if (strcmp(action, "ping") == 0) {
    publishStatus("online");
  }
}

void connectMQTT() {
  mqttClient.setServer(MQTT_HOST, MQTT_PORT);
  mqttClient.setCallback(mqttCallback);

  while (!mqttClient.connected()) {
    digitalWrite(MQTT_LED_PIN, LOW);
    String clientId = String("apaforme-") + DEVICE_ID;
    bool ok;
    if (strlen(MQTT_USERNAME) > 0) {
      ok = mqttClient.connect(clientId.c_str(), MQTT_USERNAME, MQTT_PASSWORD);
    } else {
      ok = mqttClient.connect(clientId.c_str());
    }
    if (ok) {
      digitalWrite(MQTT_LED_PIN, HIGH);
      mqttClient.subscribe(commandTopic.c_str());
      publishStatus("online");
    } else {
      delay(1000);
    }
  }
}

void publishTelemetry() {
  noInterrupts();
  unsigned long pulses = pulseCount;
  pulseCount = 0;
  interrupts();

  signalHealth = map(constrain(-WiFi.RSSI(), 40, 100), 40, 100, 100, 20);
  batteryPercent = 85.0; // replace with real ADC battery reading if available

  StaticJsonDocument<384> doc;
  doc["device_id"] = DEVICE_ID;
  doc["pulse_count"] = (int)pulses;
  doc["window_ms"] = (int)publishIntervalMs;
  doc["battery_percent"] = batteryPercent;
  doc["signal_health"] = signalHealth;
  doc["source"] = "mqtt";
  doc["firmware_version"] = FIRMWARE_VERSION;
  doc["device_time_ms"] = millis();
  doc["exam_active"] = examActive;

  char buffer[384];
  serializeJson(doc, buffer);
  mqttClient.publish(telemetryTopic.c_str(), buffer);

  digitalWrite(STATUS_LED_PIN, HIGH);
  delay(50);
  digitalWrite(STATUS_LED_PIN, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(WIFI_LED_PIN, OUTPUT);
  pinMode(MQTT_LED_PIN, OUTPUT);
  pinMode(STATUS_LED_PIN, OUTPUT);
  pinMode(HALL_SENSOR_PIN, INPUT_PULLUP);

  digitalWrite(WIFI_LED_PIN, LOW);
  digitalWrite(MQTT_LED_PIN, LOW);
  digitalWrite(STATUS_LED_PIN, LOW);

  attachInterrupt(digitalPinToInterrupt(HALL_SENSOR_PIN), onPulse, FALLING);

  connectWiFi();
  connectMQTT();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    digitalWrite(WIFI_LED_PIN, LOW);
    connectWiFi();
  }

  if (!mqttClient.connected()) {
    digitalWrite(MQTT_LED_PIN, LOW);
    connectMQTT();
  }

  mqttClient.loop();

  unsigned long now = millis();
  if (now - lastPublishMs >= publishIntervalMs) {
    lastPublishMs = now;
    publishTelemetry();
  }

  if (now - lastStatusMs >= statusIntervalMs) {
    lastStatusMs = now;
    publishStatus(examActive ? "exam_active" : "online");
  }
}
