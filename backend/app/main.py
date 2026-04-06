import asyncio
import contextlib
from collections import deque
from pathlib import Path

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import DetectionEvent
from app.sniffer import sniffer_service


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def broadcast(self, event: DetectionEvent) -> None:
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

app = FastAPI(title="Network IDS Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _enqueue_event(event: DetectionEvent) -> None:
    event_history.append(event)
    if main_loop is None:
        return
    main_loop.call_soon_threadsafe(event_queue.put_nowait, event)


@app.on_event("startup")
async def startup() -> None:
    global main_loop
    main_loop = asyncio.get_running_loop()
    sniffer_service.start(on_event=_enqueue_event)
    app.state.broadcast_task = asyncio.create_task(_broadcast_events())


@app.on_event("shutdown")
async def shutdown() -> None:
    sniffer_service.stop()
    task = app.state.broadcast_task
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


async def _broadcast_events() -> None:
    while True:
        event = await event_queue.get()
        await manager.broadcast(event)


@app.get("/api/status")
async def status() -> dict[str, object]:
    return {
        "sniffer_running": sniffer_service.running,
        "recent_events": len(event_history),
    }


@app.get("/api/events/recent")
async def recent_events() -> list[dict[str, object]]:
    return [event.model_dump(mode="json") for event in event_history]


@app.websocket("/ws/events")
async def ws_events(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    while True:
        await asyncio.sleep(30)


frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
if frontend_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dir)), name="assets")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(frontend_dir / "index.html")
