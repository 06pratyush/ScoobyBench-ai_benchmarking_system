"""ScoobyBench Backend - FastAPI Application"""
import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import config, APP_VERSION
from app.api.routes import router
from app.api.websocket import ws_manager
from app.models.database import db
from app.services.telemetry import telemetry_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.logs_dir / "scoobybench.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("ScoobyBench starting up...")

    # Cleanup old telemetry on startup
    deleted = db.cleanup_old_telemetry(config.telemetry_retention_days)
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} old telemetry samples")

    yield

    # Shutdown
    logger.info("ScoobyBench shutting down...")
    telemetry_agent.stop()

app = FastAPI(
    title="ScoobyBench API",
    description="AI Benchmarking and System Telemetry API",
    version=APP_VERSION,
    lifespan=lifespan
)

# CORS for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routes
app.include_router(router)

# WebSocket endpoint for real-time telemetry
@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.handle(websocket)

# Serve frontend static files (in production)
frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint - serve frontend"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ScoobyBench API</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #6366f1; }
            .endpoint { background: #f3f4f6; padding: 10px; margin: 5px 0; border-radius: 5px; }
            code { background: #e5e7eb; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🐕 ScoobyBench API</h1>
        <p>Version: """ + APP_VERSION + """</p>
        <p>The API is running. Use the ScoobyBench desktop app or access endpoints directly.</p>

        <h2>Key Endpoints</h2>
        <div class="endpoint"><code>GET /api/health</code> - Health check</div>
        <div class="endpoint"><code>GET /api/system/profile</code> - System hardware profile</div>
        <div class="endpoint"><code>POST /api/benchmark/run</code> - Run benchmark</div>
        <div class="endpoint"><code>GET /api/models/recommendations</code> - Model recommendations</div>
        <div class="endpoint"><code>WS /ws/telemetry</code> - Real-time telemetry</div>

        <h2>Documentation</h2>
        <p>Interactive API docs: <a href="/docs">/docs</a> (Swagger UI)</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=config.host,
        port=config.port,
        reload=False,
        log_level="info"
    )
