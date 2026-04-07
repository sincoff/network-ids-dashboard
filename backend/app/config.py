"""Network IDS Dashboard — Application configuration.

All settings are loaded from environment variables or a `.env` file.
See `.env.example` for the full list of available configuration options.
"""

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── Network interface ──────────────────────────────────────────────
    sniff_interface: str = Field(
        default="eth0",
        alias="SNIFF_INTERFACE",
        description="Network interface to monitor. Use 'auto' to let Scapy choose.",
    )
    sniff_filter: str = Field(
        default="ip",
        alias="SNIFF_FILTER",
        description="BPF filter expression for packet capture.",
    )

    # ── Detection thresholds ───────────────────────────────────────────
    detection_window_seconds: int = Field(
        default=5,
        alias="DETECTION_WINDOW_SECONDS",
        ge=1,
        le=300,
        description="Sliding window duration in seconds for rate calculation.",
    )
    packet_rate_threshold: int = Field(
        default=120,
        alias="PACKET_RATE_THRESHOLD",
        ge=1,
        description="Packets per window to trigger VOLUMETRIC classification.",
    )
    syn_rate_threshold: int = Field(
        default=60,
        alias="SYN_RATE_THRESHOLD",
        ge=1,
        description="SYN packets per window to trigger SYN_FLOOD classification.",
    )
    udp_rate_threshold: int = Field(
        default=100,
        alias="UDP_RATE_THRESHOLD",
        ge=1,
        description="UDP packets per window to trigger UDP_FLOOD classification.",
    )
    icmp_rate_threshold: int = Field(
        default=80,
        alias="ICMP_RATE_THRESHOLD",
        ge=1,
        description="ICMP packets per window to trigger ICMP_FLOOD classification.",
    )

    # ── GeoIP ──────────────────────────────────────────────────────────
    geoip_db_path: str = Field(
        default=str(Path("data") / "GeoLite2-City.mmdb"),
        alias="GEOIP_DB_PATH",
        description="Path to MaxMind GeoLite2-City database.",
    )

    # ── Application ────────────────────────────────────────────────────
    history_limit: int = Field(
        default=500,
        alias="HISTORY_LIMIT",
        ge=10,
        le=10000,
        description="Maximum number of detection events to keep in memory.",
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    cors_origins: str = Field(
        default="*",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins. Use '*' for all.",
    )
    demo_mode: bool = Field(
        default=False,
        alias="DEMO_MODE",
        description="Enable demo mode with synthetic traffic generation.",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            msg = f"log_level must be one of {allowed}, got '{v}'"
            raise ValueError(msg)
        return upper

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
