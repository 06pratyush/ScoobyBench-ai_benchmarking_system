"""FastAPI routes for ScoobyBench"""
import json
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, ConfigDict

from app.models.schemas import (
    BenchmarkRequest, BenchmarkReport, TelemetrySample,
    SystemStatus, ModelRecommendation, ModelConfig
)
from app.models.database import db
from app.services.benchmark import benchmark_engine
from app.services.telemetry import telemetry_agent
from app.services.model_manager import model_manager
from app.utils.hardware_detect import detector
from app.config import config, APP_VERSION

logger = logging.getLogger(__name__)
router = APIRouter()

# ============ System Info ============

@router.get("/api/system/profile")
async def get_system_profile():
    """Get full system hardware profile"""
    return detector.get_full_system_profile()

@router.get("/api/system/status")
async def get_system_status():
    """Get current system status"""
    return {
        "telemetry": telemetry_agent.get_status().dict(),
        "database": db.get_stats()
    }

# ============ Benchmarking ============

class BenchmarkProgress(BaseModel):
    stage: str
    percent: int
    message: Optional[str] = None

_progress_callbacks = {}

@router.post("/api/benchmark/run", response_model=BenchmarkReport)
async def run_benchmark(request: BenchmarkRequest, background_tasks: BackgroundTasks):
    """Run a benchmark test"""
    try:
        def progress_callback(stage, percent):
            _progress_callbacks[request.model.name] = {"stage": stage, "percent": percent}

        report = benchmark_engine.run_benchmark(request, progress_callback)
        return report
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/benchmark/progress/{model_name}")
async def get_benchmark_progress(model_name: str):
    """Get benchmark progress"""
    return _progress_callbacks.get(model_name, {"stage": "idle", "percent": 0})

@router.post("/api/benchmark/abort")
async def abort_benchmark():
    """Abort current benchmark"""
    benchmark_engine.abort()
    return {"status": "abort_requested"}

@router.get("/api/benchmark/reports")
async def list_reports(limit: int = 50, offset: int = 0):
    """List benchmark reports"""
    return db.list_benchmarks(limit=limit, offset=offset)

@router.get("/api/benchmark/report/{run_id}")
async def get_report(run_id: str):
    """Get specific benchmark report"""
    report = db.get_benchmark(run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/api/benchmark/export/{run_id}")
async def export_report(run_id: str, format: str = "json"):
    """Export report to file"""
    report = db.get_benchmark(run_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if format == "json":
        export_path = config.reports_dir / f"{run_id}.json"
        with open(export_path, 'w') as f:
            json.dump(report, f, indent=2)
        return FileResponse(export_path, filename=f"scoobybench_report_{run_id}.json")

    raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

# ============ Telemetry ============

@router.post("/api/telemetry/start")
async def start_telemetry():
    """Start telemetry monitoring"""
    telemetry_agent.start()
    return {"status": "started"}

@router.post("/api/telemetry/stop")
async def stop_telemetry():
    """Stop telemetry monitoring"""
    telemetry_agent.stop()
    return {"status": "stopped"}

@router.get("/api/telemetry/samples")
async def get_telemetry_samples(hours: int = Query(default=1, ge=1, le=168)):
    """Get telemetry samples"""
    return db.get_telemetry(hours=hours)

@router.get("/api/telemetry/stats")
async def get_telemetry_stats(hours: int = Query(default=1, ge=1, le=168)):
    """Get telemetry statistics"""
    return telemetry_agent.get_stats(hours=hours)

@router.get("/api/telemetry/status")
async def get_telemetry_status():
    """Get telemetry agent status"""
    return telemetry_agent.get_status()

# ============ Models ============

@router.get("/api/models")
async def list_models():
    """List available models"""
    return model_manager.list_models()

@router.get("/api/models/recommendations")
async def get_recommendations():
    """Get model recommendations for current hardware"""
    return model_manager.recommend_models()

@router.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """Get model details"""
    model = model_manager.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": model.id,
        "name": model.name,
        "params_million": model.params_million,
        "min_ram_gb": model.min_ram_gb,
        "min_vram_gb": model.min_vram_gb,
        "recommended_precision": model.recommended_precision,
        "description": model.description,
        "tags": model.tags
    }

# ============ Configuration ============

@router.get("/api/config")
async def get_config():
    """Get application configuration"""
    return config.to_dict()

@router.post("/api/config")
async def update_config(updates: dict):
    """Update application configuration"""
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value)
    config.save()
    return config.to_dict()

# ============ Health ============

@router.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "telemetry_running": telemetry_agent.is_running
    }


# ============ OLLAMA INTEGRATION ============
from app.services.ollama_benchmark import ollama_benchmark

@router.get("/api/ollama/status")
async def ollama_status():
    """Check if Ollama is running"""
    return {
        "available": ollama_benchmark.is_available,
        "host": ollama_benchmark.host,
        "version": ollama_benchmark._get_version() if ollama_benchmark.is_available else None
    }

@router.get("/api/ollama/models")
async def ollama_models():
    """List Ollama models"""
    if not ollama_benchmark.is_available:
        return {"error": "Ollama not running", "models": []}

    models = ollama_benchmark.list_models()
    return {
        "models": [
            {
                "name": m.name,
                "model_id": m.model_id,
                "size_gb": m.size_gb,
                "parameter_size": m.parameter_size,
                "format": m.format,
                "family": m.family,
                "quantization_level": m.quantization_level,
                "modified_at": m.modified_at
            }
            for m in models
        ]
    }

class OllamaBenchmarkRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    model_name: str
    prompt: str = "Explain quantum computing in simple terms."
    max_tokens: int = 256
    repeats: int = 3

@router.post("/api/ollama/benchmark")
async def run_ollama_benchmark(request: OllamaBenchmarkRequest):
    """Run benchmark on an Ollama model"""
    try:
        report = ollama_benchmark.benchmark_model(
            model_name=request.model_name,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            repeats=request.repeats
        )
        return report
    except Exception as e:
        logger.error(f"Ollama benchmark failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/ollama/pull/{model_name}")
async def pull_ollama_model(model_name: str):
    """Pull a model from Ollama registry"""
    success = ollama_benchmark.pull_model(model_name)
    return {"success": success, "model": model_name}
