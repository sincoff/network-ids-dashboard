"""Network IDS Dashboard — Packet sniffer service.

Runs Scapy packet capture in a background thread and feeds observations
to the flood detection engine. Detected events are enriched with GeoIP
data and forwarded to the WebSocket broadcast layer.
"""

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from threading import Thread

from scapy.all import ICMP, IP, TCP, UDP, sniff  # type: ignore[import-untyped]
from scapy.packet import Packet  # type: ignore[import-untyped]

from app.config import settings
from app.detector import detector, make_observation
from app.geoip import geoip_resolver
from app.models import DetectionEvent

logger = logging.getLogger(__name__)


class PacketSnifferService:
    """Background packet capture service using Scapy.

    Captures packets on the configured network interface, runs them through
    the flood detection engine, resolves GeoIP locations, and emits
    detection events via a callback.
    """

    def __init__(self) -> None:
        self._thread: Thread | None = None
        self._running = False
        self._packets_processed: int = 0

    @property
    def running(self) -> bool:
        """Whether the sniffer background thread is currently active."""
        return self._running

    @property
    def packets_processed(self) -> int:
        """Total number of IP packets processed since startup."""
        return self._packets_processed

    def start(self, on_event: Callable[[DetectionEvent], None]) -> None:
        """Start the packet capture thread.

        Args:
            on_event: Callback invoked for each detection event.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Sniffer already running — ignoring duplicate start request.")
            return

        self._running = True
        self._thread = Thread(target=self._run, args=(on_event,), daemon=True, name="packet-sniffer")
        self._thread.start()
        logger.info(
            "Packet sniffer started on interface=%s filter='%s'",
            settings.sniff_interface,
            settings.sniff_filter,
        )

    def stop(self) -> None:
        """Signal the sniffer thread to stop."""
        self._running = False
        logger.info("Packet sniffer stop requested.")

    def _run(self, on_event: Callable[[DetectionEvent], None]) -> None:
        """Main capture loop executed in the background thread."""

        def handle_packet(packet: Packet) -> None:
            if not self._running:
                return
            event = self._to_event(packet)
            if event is None:
                return
            on_event(event)

        try:
            sniff_kwargs: dict = {
                "filter": settings.sniff_filter,
                "store": False,
                "prn": handle_packet,
            }
            sniff_interface = settings.sniff_interface.strip().lower()

            # `any` / `auto` — let Scapy use its default interface.
            # Explicit interface names are passed to libpcap directly.
            if sniff_interface not in {"", "auto", "any"}:
                sniff_kwargs["iface"] = settings.sniff_interface

            logger.info("Scapy sniff() starting — waiting for packets…")
            sniff(**sniff_kwargs)
        except OSError as exc:
            logger.error(
                "Failed to open network interface '%s': %s. "
                "Check that the interface exists (`ip -br a`) and the process has CAP_NET_RAW.",
                settings.sniff_interface,
                exc,
            )
        except Exception:
            logger.exception("Unexpected error in packet sniffer thread.")
        finally:
            self._running = False
            logger.info("Packet sniffer thread exited.")

    def _to_event(self, packet: Packet) -> DetectionEvent | None:
        """Convert a raw Scapy packet into a DetectionEvent (if detection triggers)."""
        if IP not in packet:
            return None

        self._packets_processed += 1
        ip_layer = packet[IP]
        source_ip = str(ip_layer.src)
        destination_ip = str(ip_layer.dst)

        protocol = "OTHER"
        is_syn = False
        if TCP in packet:
            protocol = "TCP"
            tcp = packet[TCP]
            is_syn = bool(tcp.flags & 0x02) and not bool(tcp.flags & 0x10)
        elif UDP in packet:
            protocol = "UDP"
        elif ICMP in packet:
            protocol = "ICMP"

        observation = make_observation(
            source_ip=source_ip,
            destination_ip=destination_ip,
            protocol=protocol,
            is_syn=is_syn,
        )
        event = detector.add_observation(observation)
        if event is None:
            return None

        event.location = geoip_resolver.resolve(source_ip)
        if event.timestamp.tzinfo is None:
            event.timestamp = datetime.now(UTC)
        return event


sniffer_service = PacketSnifferService()
