from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "APAFORME Smart Riding Exam System API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 720
    database_url: str = "sqlite:///./apaforme_exam.db"
    mqtt_enabled: bool = True
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_telemetry_topic: str = "apaforme/bikes/telemetry"
    mqtt_status_topic: str = "apaforme/bikes/status"
    mqtt_command_topic_prefix: str = "apaforme/bikes/commands"
    evidence_dir: str = "uploads/evidence"
    firmware_dir: str = "uploads/firmware"
    firmware_temp_dir: str = "uploads/firmware_tmp"
    public_base_url: str = "http://localhost:8000"
    mqtt_ota_status_topic: str = "apaforme/bikes/ota/status"
    base_dir: str = str(Path(__file__).resolve().parents[2])

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
