from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    sniff_interface: str = Field(default="eth0", alias="SNIFF_INTERFACE")
    sniff_filter: str = Field(default="ip", alias="SNIFF_FILTER")
    detection_window_seconds: int = Field(default=5, alias="DETECTION_WINDOW_SECONDS")
    packet_rate_threshold: int = Field(default=120, alias="PACKET_RATE_THRESHOLD")
    syn_rate_threshold: int = Field(default=60, alias="SYN_RATE_THRESHOLD")
    udp_rate_threshold: int = Field(default=100, alias="UDP_RATE_THRESHOLD")
    geoip_db_path: str = Field(
        default=str(Path("data") / "GeoLite2-City.mmdb"),
        alias="GEOIP_DB_PATH",
    )
    history_limit: int = Field(default=500, alias="HISTORY_LIMIT")


settings = Settings()
