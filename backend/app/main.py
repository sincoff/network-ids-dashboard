"""Network IDS Dashboard — FastAPI application entry point.

Provides the REST API, WebSocket event broadcasting, and serves the
static frontend dashboard. Uses the modern lifespan context manager
pattern for startup/shutdown lifecycle management.
"""

import asyncio
import contextlib
import logging
import sys
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.detector import detector
from app.geoip import geoip_resolver
from app.models import DetectionEvent
from app.sniffer import sniffer_service

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Version ──────────────────────────────────────────────────────────
__version__ = "1.0.0"

# ── Startup time ─────────────────────────────────────────────────────
_start_time: float = 0.0


# ── WebSocket connection manager ─────────────────────────────────────
class ConnectionManager:
    """Manages active WebSocket connections for real-time event broadcasting."""

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info("WebSocket client connected. Active connections: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)
        logger.info("WebSocket client disconnected. Active connections: %d", len(self.active_connections))

    async def broadcast(self, event: DetectionEvent) -> None:
        """Broadcast a detection event to all connected WebSocket clients."""
        disconnected: list[WebSocket] = []
        payload = event.model_dump(mode="json")
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()
event_history: deque[DetectionEvent] = deque(maxlen=settings.history_limit)
event_queue: asyncio.Queue[DetectionEvent] = asyncio.Queue()
main_loop: asyncio.AbstractEventLoop | None = None


def _enqueue_event(event: DetectionEvent) -> None:
    """Thread-safe callback to enqueue detection events from the sniffer thread."""
    event_history.append(event)
    if main_loop is None:
        return
    main_loop.call_soon_threadsafe(event_queue.put_nowait, event)


async def _broadcast_events() -> None:
    """Consume events from the queue and broadcast to WebSocket clients."""
    while True:
        event = await event_queue.get()
        await manager.broadcast(event)


# ── Lifespan ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — start sniffer on startup, stop on shutdown."""
    global main_loop, _start_time
    _start_time = time.monotonic()
    main_loop = asyncio.get_running_loop()

    logger.info("Network IDS Dashboard v%s starting up…", __version__)
    logger.info(
        "Configuration: interface=%s window=%ds thresholds=(pkt=%d syn=%d udp=%d icmp=%d)",
        settings.sniff_interface,
        settings.detection_window_seconds,
        settings.packet_rate_threshold,
        settings.syn_rate_threshold,
        settings.udp_rate_threshold,
        settings.icmp_rate_threshold,
    )

    sniffer_service.start(on_event=_enqueue_event)
    broadcast_task = asyncio.create_task(_broadcast_events())

    yield

    logger.info("Shutting down…")
    sniffer_service.stop()
    geoip_resolver.close()
    broadcast_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await broadcast_task
    logger.info("Shutdown complete.")


# ── FastAPI app ──────────────────────────────────────────────────────
app = FastAPI(
    title="Network IDS Dashboard",
    description="Real-time network intrusion detection and DDoS visualization dashboard.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── API routes ───────────────────────────────────────────────────────
@app.get("/api/health", tags=["monitoring"])
async def health() -> dict[str, object]:
    """Health check endpoint for monitoring and load balancers."""
    uptime = time.monotonic() - _start_time if _start_time else 0
    return {
        "status": "healthy",
        "version": __version__,
        "uptime_seconds": round(uptime, 1),
        "sniffer_running": sniffer_service.running,
    }


@app.get("/api/status", tags=["monitoring"])
async def status() -> dict[str, object]:
    """System status with operational metrics."""
    return {
        "sniffer_running": sniffer_service.running,
        "recent_events": len(event_history),
        "websocket_clients": len(manager.active_connections),
        "packets_processed": sniffer_service.packets_processed,
        "version": __version__,
    }


@app.get("/api/stats", tags=["dashboard"])
async def stats() -> dict[str, object]:
    """Aggregated statistics for the dashboard counters."""
    unique_sources: set[str] = set()
    classification_counts: dict[str, int] = {}
    for event in event_history:
        unique_sources.add(event.source_ip)
        classification_counts[event.classification] = classification_counts.get(event.classification, 0) + 1

    # Determine threat level based on recent alert volume
    total = len(event_history)
    if total >= 100:
        threat_level = "CRITICAL"
    elif total >= 50:
        threat_level = "HIGH"
    elif total >= 10:
        threat_level = "MEDIUM"
    elif total > 0:
        threat_level = "LOW"
    else:
        threat_level = "NONE"

    return {
        "total_alerts": total,
        "unique_sources": len(unique_sources),
        "threat_level": threat_level,
        "classifications": classification_counts,
        "tracked_sources": detector.tracked_sources,
        "total_observations": detector.total_observations,
    }


@app.get("/api/events/recent", tags=["events"])
async def recent_events() -> list[dict[str, object]]:
    """Return the most recent detection events from the in-memory buffer."""
    return [event.model_dump(mode="json") for event in event_history]


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time detection event streaming."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; client doesn't send data, but we listen
            # to detect disconnects cleanly.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# ── Static frontend serving ──────────────────────────────────────────
frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="assets")

    @app.get("/", tags=["frontend"])
    async def index() -> FileResponse:
        """Serve the main dashboard HTML page."""
        return FileResponse(frontend_dir / "index.html")
