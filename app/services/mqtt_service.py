import json
import threading
import paho.mqtt.client as mqtt
from app.core.config import settings
from app.core.db import SessionLocal
from app.services.exam_service import handle_telemetry
from app.services.firmware_service import update_status_from_report


class MqttState:
    connected = False


mqtt_state = MqttState()


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client()
        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        mqtt_state.connected = rc == 0
        if rc == 0:
            client.subscribe(settings.mqtt_telemetry_topic)
            client.subscribe(settings.mqtt_status_topic)
            client.subscribe(settings.mqtt_ota_status_topic)

    def on_disconnect(self, client, userdata, rc):
        mqtt_state.connected = False

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            db = SessionLocal()
            try:
                if msg.topic == settings.mqtt_telemetry_topic:
                    handle_telemetry(db, payload)
                elif msg.topic in {settings.mqtt_status_topic, settings.mqtt_ota_status_topic}:
                    update_status_from_report(db, payload)
            finally:
                db.close()
        except Exception:
            pass

    def start(self):
        if not settings.mqtt_enabled:
            return
        def runner():
            try:
                self.client.connect(settings.mqtt_host, settings.mqtt_port, 60)
                self.client.loop_forever()
            except Exception:
                mqtt_state.connected = False
        threading.Thread(target=runner, daemon=True).start()

    def publish_command(self, device_id: str, action: str, payload: dict | None = None):
        topic = f"{settings.mqtt_command_topic_prefix}/{device_id}"
        message = {"action": action, **(payload or {})}
        self.client.publish(topic, json.dumps(message))


mqtt_service = MQTTService()
