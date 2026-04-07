"""Network IDS Dashboard — Flood detection engine.

Implements a sliding-window rate detector that classifies traffic patterns
as SYN floods, UDP floods, ICMP floods, or volumetric attacks based on
configurable packet-rate thresholds.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from app.config import settings
from app.models import DetectionEvent

logger = logging.getLogger(__name__)

# Maximum number of unique source IPs to track simultaneously.
# Prevents unbounded memory growth during large-scale attacks.
MAX_TRACKED_SOURCES = 50_000


@dataclass(slots=True)
class PacketObservation:
    """A single observed packet's metadata for detection analysis."""

    source_ip: str
    destination_ip: str | None
    protocol: str
    is_syn: bool
    timestamp: datetime


class FloodDetector:
    """Sliding-window flood detection engine.

    Maintains per-source-IP packet observation windows and triggers
    classification alerts when thresholds are exceeded.
    """

    def __init__(self) -> None:
        self.window = timedelta(seconds=settings.detection_window_seconds)
        self.by_source: dict[str, deque[PacketObservation]] = defaultdict(deque)
        self.last_alert: dict[tuple[str, str], datetime] = {}
        self.alert_cooldown = timedelta(seconds=2)
        self._total_observations: int = 0
        self._total_alerts: int = 0

    @property
    def total_observations(self) -> int:
        """Total packet observations processed since startup."""
        return self._total_observations

    @property
    def total_alerts(self) -> int:
        """Total detection alerts generated since startup."""
        return self._total_alerts

    @property
    def tracked_sources(self) -> int:
        """Number of unique source IPs currently being tracked."""
        return len(self.by_source)

    def add_observation(self, packet: PacketObservation) -> DetectionEvent | None:
        """Analyze a new packet observation and return a DetectionEvent if thresholds exceeded."""
        self._total_observations += 1

        # Memory bound — evict oldest sources if limit reached
        if len(self.by_source) >= MAX_TRACKED_SOURCES and packet.source_ip not in self.by_source:
            self._evict_oldest_source()

        source_window = self.by_source[packet.source_ip]
        source_window.append(packet)
        self._trim(source_window, packet.timestamp)

        packet_count = len(source_window)
        syn_count = sum(1 for p in source_window if p.is_syn)
        udp_count = sum(1 for p in source_window if p.protocol == "UDP")
        icmp_count = sum(1 for p in source_window if p.protocol == "ICMP")

        classification: Literal["VOLUMETRIC", "SYN_FLOOD", "UDP_FLOOD", "ICMP_FLOOD"] | None = None
        if syn_count >= settings.syn_rate_threshold:
            classification = "SYN_FLOOD"
        elif udp_count >= settings.udp_rate_threshold:
            classification = "UDP_FLOOD"
        elif icmp_count >= settings.icmp_rate_threshold:
            classification = "ICMP_FLOOD"
        elif packet_count >= settings.packet_rate_threshold:
            classification = "VOLUMETRIC"

        if classification is None:
            return None

        # Cooldown — suppress duplicate alerts for the same source + classification
        alert_key = (packet.source_ip, classification)
        now = packet.timestamp
        if alert_key in self.last_alert and now - self.last_alert[alert_key] < self.alert_cooldown:
            return None

        self.last_alert[alert_key] = now
        self._total_alerts += 1

        logger.info(
            "Detection alert: %s from %s (%d packets in window)",
            classification,
            packet.source_ip,
            packet_count,
        )

        return DetectionEvent(
            timestamp=now,
            source_ip=packet.source_ip,
            destination_ip=packet.destination_ip,
            protocol=packet.protocol if packet.protocol in {"TCP", "UDP", "ICMP"} else "OTHER",
            packet_count_window=packet_count,
            classification=classification,
            location=None,
        )

    def _trim(self, source_window: deque[PacketObservation], now: datetime) -> None:
        """Remove observations outside the detection window."""
        threshold = now - self.window
        while source_window and source_window[0].timestamp < threshold:
            source_window.popleft()

    def _evict_oldest_source(self) -> None:
        """Evict the source IP with the oldest latest observation."""
        if not self.by_source:
            return
        oldest_ip = min(
            self.by_source,
            key=lambda ip: self.by_source[ip][-1].timestamp if self.by_source[ip] else datetime.min.replace(tzinfo=UTC),
        )
        del self.by_source[oldest_ip]
        logger.debug("Evicted tracked source %s (memory bound reached)", oldest_ip)


detector = FloodDetector()


def make_observation(
    source_ip: str,
    destination_ip: str | None,
    protocol: str,
    is_syn: bool,
) -> PacketObservation:
    """Create a new PacketObservation with the current UTC timestamp."""
    return PacketObservation(
        source_ip=source_ip,
        destination_ip=destination_ip,
        protocol=protocol,
        is_syn=is_syn,
        timestamp=datetime.now(UTC),
    )
