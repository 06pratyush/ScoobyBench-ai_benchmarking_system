"""WebSocket for real-time telemetry streaming"""
import json
import asyncio
import logging
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

from app.services.telemetry import telemetry_agent, TelemetrySample

logger = logging.getLogger(__name__)

class TelemetryWebSocket:
    """Manages WebSocket connections for real-time telemetry"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        # Telemetry samples arrive on the agent's worker thread; remember the
        # server loop so the callback can hand messages back to it safely.
        self._loop = asyncio.get_running_loop()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self.active_connections)}")

        # Start broadcast if first client
        if len(self.active_connections) == 1:
            self._start_broadcast()

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self.active_connections)}")

    def _start_broadcast(self):
        """Start broadcasting telemetry to all clients"""
        if not telemetry_agent.is_running:
            telemetry_agent.start()

        # Register callback
        telemetry_agent.register_callback(self._on_telemetry_sample)

    def _on_telemetry_sample(self, sample: TelemetrySample):
        """Handle new telemetry sample (called from the telemetry thread)"""
        if not self.active_connections or self._loop is None or self._loop.is_closed():
            return

        message = {
            "type": "telemetry",
            "timestamp": sample.timestamp.isoformat(),
            "cpu_percent": sample.cpu_percent,
            "memory_percent": sample.memory_percent,
            "memory_used_mb": sample.memory_used_mb,
            "gpu_percent": sample.gpu_percent,
            "gpu_vram_used_mb": sample.gpu_vram_used_mb,
            "temperature_c": sample.temperature_c,
            "power_w": sample.power_w
        }

        asyncio.run_coroutine_threadsafe(self._broadcast(message), self._loop)

    async def _broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def handle(self, websocket: WebSocket):
        """Handle WebSocket connection lifecycle"""
        await self.connect(websocket)
        try:
            while True:
                # Keep connection alive and handle client messages
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    if msg.get("action") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif msg.get("action") == "get_status":
                        status = telemetry_agent.get_status()
                        await websocket.send_json({
                            "type": "status",
                            "data": status.model_dump(mode="json")
                        })
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            self.disconnect(websocket)

# Global instance
ws_manager = TelemetryWebSocket()
