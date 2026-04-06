from collections.abc import Callable
from datetime import UTC, datetime
from threading import Thread

from scapy.all import IP, TCP, UDP, sniff  # type: ignore[import-untyped]
from scapy.packet import Packet  # type: ignore[import-untyped]

from app.config import settings
from app.detector import detector, make_observation
from app.geoip import geoip_resolver
from app.models import DetectionEvent


class PacketSnifferService:
    def __init__(self) -> None:
        self._thread: Thread | None = None
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self, on_event: Callable[[DetectionEvent], None]) -> None:
        if self._thread is not None and self._thread.is_alive():
            return

        self._running = True
        self._thread = Thread(target=self._run, args=(on_event,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    def _run(self, on_event: Callable[[DetectionEvent], None]) -> None:
        def handle_packet(packet: Packet) -> None:
            if not self._running:
                return
            event = self._to_event(packet)
            if event is None:
                return
            on_event(event)

        try:
            sniff_kwargs = {
                "filter": settings.sniff_filter,
                "store": False,
                "prn": handle_packet,
            }
            sniff_interface = settings.sniff_interface.strip().lower()
            # `any` is not universally supported by scapy/libpcap backends on Ubuntu VMs.
            # For `auto`/`any`, let scapy use its default interface.
            if sniff_interface not in {"", "auto", "any"}:
                sniff_kwargs["iface"] = settings.sniff_interface
            sniff(**sniff_kwargs)
        finally:
            self._running = False

    def _to_event(self, packet: Packet) -> DetectionEvent | None:
        if IP not in packet:
            return None

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
