from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.config import settings
from app.models import DetectionEvent


@dataclass(slots=True)
class PacketObservation:
    source_ip: str
    destination_ip: str | None
    protocol: str
    is_syn: bool
    timestamp: datetime


class FloodDetector:
    def __init__(self) -> None:
        self.window = timedelta(seconds=settings.detection_window_seconds)
        self.by_source: dict[str, deque[PacketObservation]] = defaultdict(deque)
        self.last_alert: dict[tuple[str, str], datetime] = {}
        self.alert_cooldown = timedelta(seconds=2)

    def add_observation(self, packet: PacketObservation) -> DetectionEvent | None:
        source_window = self.by_source[packet.source_ip]
        source_window.append(packet)
        self._trim(source_window, packet.timestamp)

        packet_count = len(source_window)
        syn_count = sum(1 for p in source_window if p.is_syn)
        udp_count = sum(1 for p in source_window if p.protocol == "UDP")

        classification: Literal["VOLUMETRIC", "SYN_FLOOD", "UDP_FLOOD"] | None = None
        if syn_count >= settings.syn_rate_threshold:
            classification = "SYN_FLOOD"
        elif udp_count >= settings.udp_rate_threshold:
            classification = "UDP_FLOOD"
        elif packet_count >= settings.packet_rate_threshold:
            classification = "VOLUMETRIC"

        if classification is None:
            return None

        alert_key = (packet.source_ip, classification)
        now = packet.timestamp
        if alert_key in self.last_alert and now - self.last_alert[alert_key] < self.alert_cooldown:
            return None

        self.last_alert[alert_key] = now
        return DetectionEvent(
            timestamp=now,
            source_ip=packet.source_ip,
            destination_ip=packet.destination_ip,
            protocol=packet.protocol if packet.protocol in {"TCP", "UDP"} else "OTHER",
            packet_count_window=packet_count,
            classification=classification,
            location=None,
        )

    def _trim(self, source_window: deque[PacketObservation], now: datetime) -> None:
        threshold = now - self.window
        while source_window and source_window[0].timestamp < threshold:
            source_window.popleft()


detector = FloodDetector()


def make_observation(
    source_ip: str,
    destination_ip: str | None,
    protocol: str,
    is_syn: bool,
) -> PacketObservation:
    return PacketObservation(
        source_ip=source_ip,
        destination_ip=destination_ip,
        protocol=protocol,
        is_syn=is_syn,
        timestamp=datetime.now(UTC),
    )
