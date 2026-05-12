"""Ollama local model benchmarking integration"""
import time
import json
import logging
import requests
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from app.config import config
from app.models.schemas import (
    BenchmarkReport, BenchmarkMetrics, LatencyMetrics,
    NormalizationData, ComparatorResult, DeviceInfo, Precision
)
from app.models.database import db
from app.utils.hardware_detect import detector

logger = logging.getLogger(__name__)

OLLAMA_HOST = "http://127.0.0.1:11434"


@dataclass
class OllamaModel:
    name: str
    model_id: str
    size_gb: float
    parameter_size: str
    format: str
    family: str
    families: List[str]
    quantization_level: str
    modified_at: str


class OllamaBenchmark:
    """Benchmark models via Ollama's local API"""
    
    def __init__(self, host: str = OLLAMA_HOST):
        self.host = host
        self._available = self._check_connection()
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def _check_connection(self) -> bool:
        """Check if Ollama server is running"""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=5)
            logger.info(f"[Ollama] Connection check: status={resp.status_code}")
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"[Ollama] Not available at {self.host}: {e}")
            return False
    
    def list_models(self) -> List[OllamaModel]:
        """List all locally available Ollama models"""
        if not self.is_available:
            logger.info("[Ollama] Not available, returning empty model list")
            return []
        
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=10)
            data = resp.json()
            models = []
            
            for m in data.get("models", []):
                details = m.get("details", {})
                models.append(OllamaModel(
                    name=m.get("name", "unknown"),
                    model_id=m.get("model", m.get("name", "unknown")),
                    size_gb=round(m.get("size", 0) / (1024**3), 2),
                    parameter_size=details.get("parameter_size", "unknown"),
                    format=details.get("format", "unknown"),
                    family=details.get("family", "unknown"),
                    families=details.get("families", []),
                    quantization_level=details.get("quantization_level", "unknown"),
                    modified_at=m.get("modified_at", "")
                ))
            
            logger.info(f"[Ollama] Found {len(models)} models: {[m.name for m in models]}")
            return models
        except Exception as e:
            logger.error(f"[Ollama] Failed to list models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry (blocking)"""
        try:
            logger.info(f"[Ollama] Pulling model: {model_name}")
            resp = requests.post(
                f"{self.host}/api/pull",
                json={"name": model_name, "stream": False},
                timeout=300
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"[Ollama] Failed to pull model {model_name}: {e}")
            return False
    
    def benchmark_model(
        self,
        model_name: str,
        prompt: str = "Explain quantum computing in simple terms.",
        max_tokens: int = 256,
        repeats: int = 3,
        progress_callback=None
    ) -> Optional[BenchmarkReport]:
        """Run benchmark on an Ollama model"""
        
        if not self.is_available:
            raise RuntimeError("Ollama is not running. Start it with: ollama serve")
        
        models = self.list_models()
        model_info = next((m for m in models if m.name == model_name or m.model_id == model_name), None)
        if not model_info:
            raise RuntimeError(f"Model '{model_name}' not found in Ollama. Run: ollama pull {model_name}")
        
        device = self._get_device_info()
        params_million = self._parse_param_size(model_info.parameter_size)
        
        all_metrics = []
        
        for i in range(repeats):
            if progress_callback:
                progress_callback(f"run_{i+1}", 10 + (80 * (i+1) // repeats))
            
            metrics = self._run_single_generate(model_name, prompt, max_tokens)
            all_metrics.append(metrics)
        
        aggregated = self._aggregate_metrics(all_metrics)
        
        normalization = NormalizationData(
            precision_adjustment=1.0,
            batch_adjustment=1.0,
            prompt_length_adjustment=1.0,
            normalized_tokens_per_sec=aggregated.tokens_per_sec
        )
        
        comparator = self._compare_to_baseline(aggregated, device, params_million)
        
        report = BenchmarkReport(
            run_id=f"ollama-{int(time.time())}",
            timestamp=datetime.utcnow(),
            device=device,
            model={
                "name": model_name,
                "onnx_path": None,
                "params_million": params_million,
                "precision": "fp16",  # Changed from "unknown"
                "batch_size": 1,
                "prompt_tokens": len(prompt.split()),
                "target_tokens": max_tokens,
                "repeats": repeats
            },
            metrics=aggregated,
            normalization=normalization,
            comparator=comparator,
            environment_snapshot={"ollama_version": self._get_version(), "model_info": model_info.__dict__},
            notes=f"Ollama benchmark for {model_name} ({model_info.parameter_size}) via {self.host}"
        )
        
        db.save_benchmark(report)
        return report
    
    def _run_single_generate(self, model_name: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Run a single generation and capture metrics"""
        import psutil
        
        process = psutil.Process()
        mem_before = process.memory_info().rss / (1024**2)
        
        start_time = time.perf_counter()
        first_token_time = None
        tokens_generated = 0
        tps_from_ollama = 0.0
        
        try:
            resp = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                stream=True,
                timeout=120
            )
            
            for line in resp.iter_lines():
                if not line:
                    continue
                
                try:
                    chunk = json.loads(line)
                    
                    if first_token_time is None and chunk.get("response"):
                        first_token_time = time.perf_counter()
                    
                    if chunk.get("done"):
                        eval_count = chunk.get("eval_count", 0)
                        eval_duration_ns = chunk.get("eval_duration", 1)
                        tps_from_ollama = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns else 0
                        tokens_generated = eval_count
                        break
                    
                    if chunk.get("response"):
                        tokens_generated += 1
                        
                except json.JSONDecodeError:
                    continue
            
            end_time = time.perf_counter()
            mem_after = process.memory_info().rss / (1024**2)
            
            total_duration = end_time - start_time
            generation_duration = end_time - first_token_time if first_token_time else total_duration
            
            tokens_per_sec = tokens_generated / generation_duration if generation_duration > 0 else 0
            
            latencies = [generation_duration / max(tokens_generated, 1) * 1000] * max(tokens_generated, 1)
            
            return {
                "latencies": latencies,
                "tokens_per_sec": tokens_per_sec,
                "peak_ram_mb": mem_after,
                "peak_vram_mb": None,
                "avg_power_w": None,
                "cpu_util_pct": psutil.cpu_percent(interval=0.1),
                "gpu_util_pct": None,
                "ttft_ms": (first_token_time - start_time) * 1000 if first_token_time else 0,
                "ollama_tps": tps_from_ollama
            }
            
        except Exception as e:
            logger.error(f"[Ollama] Generation failed: {e}")
            raise
    
    def _parse_param_size(self, size_str: str) -> int:
        """Parse '4.9B' or '7B' to millions"""
        try:
            size_str = size_str.upper().replace("B", "").strip()
            val = float(size_str)
            return int(val * 1000)
        except:
            return 7000
    
    def _get_device_info(self) -> DeviceInfo:
        profile = detector.get_full_system_profile()
        gpus = profile.get("gpus", [])
        npu = profile.get("npu")
        return DeviceInfo(
            os=profile["os"],
            os_build=profile["os_build"],
            cpu=profile["cpu"]["name"],
            cpu_cores=profile["cpu"]["cores"],
            cpu_threads=profile["cpu"]["threads"],
            gpu=gpus[0]["name"] if gpus else None,
            gpu_vram_gb=gpus[0]["vram_gb"] if gpus else None,
            npu=npu["name"] if npu else None,
            ram_gb=profile["ram"]["total_gb"],
            driver_versions={g["name"]: g["driver"] for g in gpus},
            power_plan=profile["power_plan"],
            bios_version=profile["bios"].get("version", "Unknown")
        )
    
    def _aggregate_metrics(self, runs: List[Dict[str, Any]]) -> BenchmarkMetrics:
        import statistics
        
        all_latencies = []
        for r in runs:
            all_latencies.extend(r.get("latencies", [0]))
        
        if not all_latencies:
            all_latencies = [0]
        
        sorted_lat = sorted(all_latencies)
        n = len(sorted_lat)
        
        tps_values = [r.get("tokens_per_sec", 0) for r in runs]
        
        return BenchmarkMetrics(
            latency=LatencyMetrics(
                p50_ms=sorted_lat[n // 2] if n > 0 else 0,
                p90_ms=sorted_lat[int(n * 0.9)] if n > 1 else sorted_lat[0],
                p99_ms=sorted_lat[int(n * 0.99)] if n > 1 else sorted_lat[0],
                min_ms=min(sorted_lat),
                max_ms=max(sorted_lat)
            ),
            tokens_per_sec=statistics.median(tps_values),
            peak_ram_mb=max(r.get("peak_ram_mb", 0) for r in runs),
            peak_vram_mb=None,
            avg_power_w=None,
            cpu_util_pct=statistics.mean([r.get("cpu_util_pct", 0) for r in runs]),
            gpu_util_pct=None,
            npu_util_pct=None,
            temperature_c=None,
            memory_efficiency=0.0,
            tokens_per_watt=None
        )
    
    def _compare_to_baseline(self, metrics: BenchmarkMetrics, device: DeviceInfo, params_million: int) -> ComparatorResult:
        baselines = self._load_baselines()
        baseline_key = f"ollama_{params_million}M"
        baseline = baselines.get(baseline_key)
        
        if not baseline:
            baseline = {"tokens_per_sec": 15.0, "source": "ollama_generic"}
        
        baseline_tps = baseline["tokens_per_sec"]
        delta_pct = ((metrics.tokens_per_sec - baseline_tps) / baseline_tps) * 100 if baseline_tps else 0
        
        causes = []
        if device.power_plan != "High performance":
            causes.append(f"Power plan is '{device.power_plan}'")
        
        grade = "A" if delta_pct >= -10 else "B" if delta_pct >= -25 else "C" if delta_pct >= -50 else "D"
        
        return ComparatorResult(
            baseline_source=baseline["source"],
            baseline_tokens_per_sec=baseline_tps,
            delta_pct=delta_pct,
            delta_abs=metrics.tokens_per_sec - baseline_tps,
            probable_causes=causes,
            grade=grade
        )
    
    def _load_baselines(self) -> Dict[str, Dict]:
        baseline_path = config.data_dir / "ollama_baselines.json"
        if baseline_path.exists():
            with open(baseline_path) as f:
                return json.load(f)
        return {
            "ollama_2000M": {"tokens_per_sec": 25.0, "source": "ollama_small"},
            "ollama_4000M": {"tokens_per_sec": 18.0, "source": "ollama_medium"},
            "ollama_7000M": {"tokens_per_sec": 15.0, "source": "ollama_large"},
            "ollama_8000M": {"tokens_per_sec": 12.0, "source": "ollama_xl"}
        }
    
    def _get_version(self) -> str:
        try:
            resp = requests.get(f"{self.host}/api/version", timeout=5)
            return resp.json().get("version", "unknown")
        except:
            return "unknown"


# Global instance
ollama_benchmark = OllamaBenchmark()