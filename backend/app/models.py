from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class SourceLocation(BaseModel):
    source_ip: str
    country: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class DetectionEvent(BaseModel):
    timestamp: datetime
    source_ip: str
    destination_ip: str | None = None
    protocol: Literal["TCP", "UDP", "OTHER"]
    packet_count_window: int
    classification: Literal["VOLUMETRIC", "SYN_FLOOD", "UDP_FLOOD"]
    location: SourceLocation | None = None
