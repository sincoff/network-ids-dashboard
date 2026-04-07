"""Network IDS Dashboard — Pydantic data models.

Defines the schema for detection events and geolocation data
used across the backend and transmitted to frontend clients.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    """Geographic location resolved from a source IP address."""

    source_ip: str = Field(description="The IP address that was resolved.")
    country: str | None = Field(default=None, description="Country name.")
    city: str | None = Field(default=None, description="City name.")
    latitude: float | None = Field(default=None, description="Latitude coordinate.")
    longitude: float | None = Field(default=None, description="Longitude coordinate.")


class DetectionEvent(BaseModel):
    """A single intrusion detection event.

    Created when packet rates from a source IP exceed configured thresholds
    within the detection window.
    """

    timestamp: datetime = Field(description="UTC timestamp when the event was detected.")
    source_ip: str = Field(description="Source IP address of the suspicious traffic.")
    destination_ip: str | None = Field(
        default=None,
        description="Destination IP address targeted by the traffic.",
    )
    protocol: Literal["TCP", "UDP", "ICMP", "OTHER"] = Field(
        description="Network protocol of the detected traffic.",
    )
    packet_count_window: int = Field(
        description="Number of packets observed in the detection window.",
    )
    classification: Literal["VOLUMETRIC", "SYN_FLOOD", "UDP_FLOOD", "ICMP_FLOOD"] = Field(
        description="Attack classification based on traffic pattern analysis.",
    )
    location: SourceLocation | None = Field(
        default=None,
        description="Resolved geographic location of the source IP.",
    )
