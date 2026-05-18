"""AI Model Benchmarking Engine"""
import time
import uuid
import json
import statistics
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from app.config import config
from app.models.schemas import (
    BenchmarkRequest, BenchmarkReport, BenchmarkMetrics, 
    LatencyMetrics, NormalizationData, ComparatorResult,
    ModelConfig, DeviceInfo, Precision
)
from app.models.database import db
from app.utils.hardware_detect import detector
from app.services.telemetry import telemetry_agent

def softmax(x):
    e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e_x / np.sum(e_x, axis=-1, keepdims=True)

logger = logging.getLogger(__name__)

class BenchmarkEngine:
    """Core benchmarking engine for ONNX models"""

    def __init__(self):
        self._current_run: Optional[str] = None
        self._abort_flag = False
        self._onnx_runtime_available = self._check_onnx()

    def _check_onnx(self) -> bool:
        try:
            import onnxruntime as ort
            logger.info(f"ONNX Runtime available: {ort.get_device()}")
            return True
        except ImportError:
            logger.warning("ONNX Runtime not installed")
            return False

    def abort(self):
        """Abort current benchmark"""
        self._abort_flag = True
        logger.info("Benchmark abort requested")

    def run_benchmark(self, request: BenchmarkRequest, progress_callback=None) -> BenchmarkReport:
        """Execute full benchmark workflow"""
        self._abort_flag = False
        run_id = str(uuid.uuid4())
        self._current_run = run_id

        logger.info(f"Starting benchmark {run_id} for model {request.model.name}")

        # 1. Pre-flight checks
        self._preflight_check(request)
        if progress_callback:
            progress_callback("preflight", 10)

        # 2. Collect device info
        device = request.device_info or self._get_device_info()
        if progress_callback:
            progress_callback("device_detect", 20)

        # 3. Environment snapshot
        env_snapshot = self._capture_environment()
        if progress_callback:
            progress_callback("env_capture", 30)

        # 4. Warmup
        warmup_metrics = self._run_warmup(request.model)
        if progress_callback:
            progress_callback("warmup", 40)

        # 5. Main benchmark runs
        all_metrics = []
        for i in range(request.model.repeats):
            if self._abort_flag:
                raise RuntimeError("Benchmark aborted by user")

            metrics = self._run_inference_test(request.model)
            all_metrics.append(metrics)

            if progress_callback:
                progress_callback(f"run_{i+1}", 40 + (50 * (i+1) // request.model.repeats))

        # 6. Aggregate metrics
        aggregated = self._aggregate_metrics(all_metrics)
        if progress_callback:
            progress_callback("aggregate", 95)

        # 7. Normalization
        normalization = self._normalize_metrics(aggregated, request.model)

        # 8. Comparison
        comparator = self._compare_to_baseline(aggregated, device, request.model)

        # 9. Generate report
        report = BenchmarkReport(
            run_id=run_id,
            timestamp=datetime.utcnow(),
            device=device,
            model=request.model,
            metrics=aggregated,
            normalization=normalization,
            comparator=comparator,
            environment_snapshot=env_snapshot,
            notes=self._generate_notes(aggregated, comparator)
        )

        # 10. Save to database
        db.save_benchmark(report)

        if progress_callback:
            progress_callback("complete", 100)

        logger.info(f"Benchmark {run_id} completed")
        return report

    def _preflight_check(self, request: BenchmarkRequest):
        """Validate system readiness"""
        import psutil

        # Check RAM
        mem = psutil.virtual_memory()
        required_ram = request.model.params_million * 2  # Rough estimate: 2MB per million params
        if mem.available < required_ram * 1024 * 1024:
            logger.warning(f"Low RAM: {mem.available/1024**3:.1f}GB available, {required_ram/1024:.1f}MB recommended")

        # Check if model exists
        if request.model.onnx_path and not Path(request.model.onnx_path).exists():
            raise FileNotFoundError(f"Model not found: {request.model.onnx_path}")

        # Check ONNX Runtime
        if request.model.onnx_path and not self._onnx_runtime_available:
            raise RuntimeError("ONNX Runtime not available")

    def _get_device_info(self) -> DeviceInfo:
        """Get current device information"""
        profile = detector.get_full_system_profile()

        gpus = profile.get("gpus", [])
        gpu_name = gpus[0]["name"] if gpus else None
        gpu_vram = gpus[0]["vram_gb"] if gpus else None

        npu = profile.get("npu")
        npu_name = npu["name"] if npu else None

        return DeviceInfo(
            os=profile["os"],
            os_build=profile["os_build"],
            cpu=profile["cpu"]["name"],
            cpu_cores=profile["cpu"]["cores"],
            cpu_threads=profile["cpu"]["threads"],
            gpu=gpu_name,
            gpu_vram_gb=gpu_vram,
            npu=npu_name,
            ram_gb=profile["ram"]["total_gb"],
            driver_versions={g["name"]: g["driver"] for g in gpus},
            power_plan=profile["power_plan"],
            bios_version=profile["bios"].get("version", "Unknown")
        )

    def _capture_environment(self) -> Dict[str, Any]:
        """Capture system environment snapshot"""
        import psutil
        disk_root = Path.cwd().anchor or str(Path.cwd().drive) or "/"
        cpu_freq = psutil.cpu_freq()

        return {
            "cpu_freq_mhz": cpu_freq.current if cpu_freq else None,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_free_gb": psutil.disk_usage(disk_root).free / (1024**3),
            "process_count": len(psutil.pids()),
            "boot_time": psutil.boot_time(),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _run_warmup(self, model: ModelConfig) -> Dict[str, float]:
        """Run warmup inference to stabilize system"""
        logger.info("Running warmup...")

        # Simple synthetic warmup if no model provided
        if not model.onnx_path:
            time.sleep(1.0)  # Simulate warmup
            return {"tokens_per_sec": 0, "latency_ms": 0}

        try:
            import onnxruntime as ort

            session = ort.InferenceSession(
                model.onnx_path,
                providers=['CPUExecutionProvider']
            )

            # Get input info
            input_meta = session.get_inputs()[0]
            shape = input_meta.shape

            # Create dummy input
            if isinstance(shape[1], str):
                seq_len = model.prompt_tokens
            else:
                seq_len = shape[1] if shape[1] else model.prompt_tokens

            dummy_input = np.random.randn(1, seq_len).astype(np.int64)

            # Run warmup iterations
            for _ in range(3):
                session.run(None, {input_meta.name: dummy_input})

            return {"tokens_per_sec": 0, "latency_ms": 0}

        except Exception as e:
            logger.warning(f"Warmup failed: {e}")
            return {"tokens_per_sec": 0, "latency_ms": 0}

    def _run_inference_test(self, model: ModelConfig) -> Dict[str, Any]:
        """Run a single inference test"""
        if not model.onnx_path:
            return self._run_synthetic_test(model)

        try:
            import onnxruntime as ort
            import psutil

            # Determine execution provider
            providers = ['CPUExecutionProvider']
            if model.precision == Precision.FP16:
                providers.insert(0, 'CUDAExecutionProvider')

            session = ort.InferenceSession(model.onnx_path, providers=providers)

            # Prepare input
            input_meta = session.get_inputs()[0]
            seq_len = model.prompt_tokens
            dummy_input = np.random.randint(0, 32000, size=(model.batch_size, seq_len)).astype(np.int64)

            # Monitor resources
            process = psutil.Process()
            mem_before = process.memory_info().rss / (1024**2)

            # Run inference with timing
            latencies = []
            tokens_generated = 0

            for _ in range(model.target_tokens // model.batch_size):
                start = time.perf_counter()
                outputs = session.run(None, {input_meta.name: dummy_input})
                end = time.perf_counter()

                latencies.append((end - start) * 1000)  # ms
                tokens_generated += model.batch_size

                # Update input for next token (simplified)
                if len(outputs) > 0:
                    next_token = np.argmax(outputs[0][:, -1, :], axis=-1, keepdims=True)
                    dummy_input = np.concatenate([dummy_input[:, 1:], next_token], axis=1)

            mem_after = process.memory_info().rss / (1024**2)

            total_time = sum(latencies) / 1000  # seconds
            tokens_per_sec = tokens_generated / total_time if total_time > 0 else 0

            return {
                "latencies": latencies,
                "tokens_per_sec": tokens_per_sec,
                "peak_ram_mb": mem_after,
                "peak_vram_mb": None,  # Would need NVML
                "avg_power_w": None,
                "cpu_util_pct": psutil.cpu_percent(interval=0.1),
                "gpu_util_pct": None
            }

        except Exception as e:
            logger.error(f"Inference test failed: {e}")
            return self._run_synthetic_test(model)

    def _run_synthetic_test(self, model: ModelConfig) -> Dict[str, Any]:
        """Run synthetic benchmark when no model is available"""
        import psutil

        process = psutil.Process()
        peak_ram_mb = process.memory_info().rss / (1024**2)

        latencies = []
        tokens_generated = 0

        hidden_dim = max(64, min(1024, int((model.params_million ** 0.5) * 6)))
        seq = max(8, min(model.prompt_tokens, 256))
        ff_dim = hidden_dim * 2
        batch = max(1, model.batch_size)

        q = np.random.randn(batch, seq, hidden_dim).astype(np.float32)
        k = np.random.randn(batch, seq, hidden_dim).astype(np.float32)
        v = np.random.randn(batch, seq, hidden_dim).astype(np.float32)
        ff1 = np.random.randn(hidden_dim, ff_dim).astype(np.float32)
        ff2 = np.random.randn(ff_dim, hidden_dim).astype(np.float32)

        for _ in range(model.target_tokens):
            start = time.perf_counter()

            scores = np.matmul(q, k.transpose(0, 2, 1)) / np.sqrt(hidden_dim)
            attn = softmax(scores)
            output = np.matmul(attn, v)
            hidden = np.tanh(np.matmul(output, ff1))
            result = np.matmul(hidden, ff2)
            q = 0.8 * q + 0.2 * result.astype(np.float32)

            end = time.perf_counter()
            latencies.append((end - start) * 1000)
            tokens_generated += 1
            peak_ram_mb = max(peak_ram_mb, process.memory_info().rss / (1024**2))

            if self._abort_flag:
                break

        total_time = sum(latencies) / 1000
        avg_power = None
        recent_sample = telemetry_agent.get_status().last_sample
        if recent_sample:
            avg_power = recent_sample.power_w

        model_size_mb = max(model.params_million * 2 / 1024, 1)
        memory_efficiency = model_size_mb / max(peak_ram_mb, 1)

        return {
            "latencies": latencies,
            "tokens_per_sec": tokens_generated / total_time if total_time > 0 else 0,
            "peak_ram_mb": peak_ram_mb,
            "peak_vram_mb": None,
            "avg_power_w": avg_power,
            "cpu_util_pct": psutil.cpu_percent(interval=0.1),
            "gpu_util_pct": None
        }

    def _aggregate_metrics(self, runs: List[Dict[str, Any]]) -> BenchmarkMetrics:
        """Aggregate metrics from multiple runs"""
        all_latencies = []
        for r in runs:
            all_latencies.extend(r["latencies"])

        if not all_latencies:
            all_latencies = [0]

        sorted_lat = sorted(all_latencies)
        n = len(sorted_lat)

        tokens_per_sec_values = [r["tokens_per_sec"] for r in runs]

        avg_power = statistics.mean([r["avg_power_w"] for r in runs if r["avg_power_w"] is not None]) if any(r["avg_power_w"] is not None for r in runs) else None
        peak_ram = max(r["peak_ram_mb"] for r in runs)
        tokens_per_sec = statistics.median(tokens_per_sec_values)
        peak_vram = max((r["peak_vram_mb"] for r in runs if r["peak_vram_mb"] is not None), default=None)
        tokens_per_watt = (tokens_per_sec / avg_power) if avg_power and avg_power > 0 else None

        return BenchmarkMetrics(
            latency=LatencyMetrics(
                p50_ms=sorted_lat[n // 2] if n > 0 else 0,
                p90_ms=sorted_lat[int(n * 0.9)] if n > 1 else sorted_lat[0],
                p99_ms=sorted_lat[int(n * 0.99)] if n > 1 else sorted_lat[0],
                min_ms=min(sorted_lat),
                max_ms=max(sorted_lat)
            ),
            tokens_per_sec=tokens_per_sec,
            peak_ram_mb=peak_ram,
            peak_vram_mb=peak_vram,
            avg_power_w=avg_power,
            cpu_util_pct=statistics.mean([r["cpu_util_pct"] for r in runs]),
            gpu_util_pct=statistics.mean([r["gpu_util_pct"] for r in runs if r["gpu_util_pct"] is not None]) if any(r["gpu_util_pct"] is not None for r in runs) else None,
            npu_util_pct=None,
            temperature_c=None,
            memory_efficiency=max(0.0, (peak_ram / 1024) / max(tokens_per_sec, 0.001)),
            tokens_per_watt=tokens_per_watt
        )

    def _normalize_metrics(self, metrics: BenchmarkMetrics, model: ModelConfig) -> NormalizationData:
        """Normalize metrics for fair comparison"""
        # Precision adjustment factors (relative to FP16 baseline)
        precision_factors = {
            Precision.FP32: 0.5,  # Slower due to more compute
            Precision.FP16: 1.0,  # Baseline
            Precision.INT8: 2.0,  # Faster
            Precision.INT4: 3.5   # Much faster
        }

        prec_adj = precision_factors.get(model.precision, 1.0)
        batch_adj = 1.0 / model.batch_size  # Normalize to batch=1
        prompt_adj = 128.0 / model.prompt_tokens  # Normalize to 128 tokens

        normalized = metrics.tokens_per_sec * prec_adj * batch_adj * prompt_adj

        return NormalizationData(
            precision_adjustment=prec_adj,
            batch_adjustment=batch_adj,
            prompt_length_adjustment=prompt_adj,
            normalized_tokens_per_sec=normalized
        )

    def _compare_to_baseline(self, metrics: BenchmarkMetrics, device: DeviceInfo, model: ModelConfig) -> ComparatorResult:
        """Compare results to baseline expectations"""
        # Load baselines from config
        baselines = self._load_baselines()

        # Find matching baseline
        baseline_key = f"{device.cpu}_{model.name}_{model.precision.value}"
        baseline = baselines.get(baseline_key)

        if not baseline:
            # Use generic baseline based on device class
            if device.gpu:
                baseline = {"tokens_per_sec": 50.0, "source": "generic_gpu"}
            else:
                baseline = {"tokens_per_sec": 5.0, "source": "generic_cpu"}

        baseline_tps = baseline["tokens_per_sec"]
        delta_pct = ((metrics.tokens_per_sec - baseline_tps) / baseline_tps) * 100
        delta_abs = metrics.tokens_per_sec - baseline_tps

        # Determine probable causes
        causes = []
        if metrics.temperature_c and metrics.temperature_c > 80:
            causes.append("Thermal throttling detected")
        if device.power_plan != "High performance":
            causes.append(f"Power plan is '{device.power_plan}', recommend 'High performance'")
        if metrics.peak_ram_mb > (device.ram_gb * 1024 * 0.9):
            causes.append("RAM saturation during test")
        if metrics.gpu_util_pct and metrics.gpu_util_pct < 50:
            causes.append("Low GPU utilization - possible CPU bottleneck")

        # Grade
        if delta_pct >= -10:
            grade = "A"
        elif delta_pct >= -25:
            grade = "B"
        elif delta_pct >= -50:
            grade = "C"
        else:
            grade = "D"

        return ComparatorResult(
            baseline_source=baseline["source"],
            baseline_tokens_per_sec=baseline_tps,
            delta_pct=delta_pct,
            delta_abs=delta_abs,
            probable_causes=causes,
            grade=grade
        )

    def _load_baselines(self) -> Dict[str, Dict]:
        """Load baseline performance data"""
        baseline_path = Path(__file__).parent.parent.parent / "config" / "mlperf_baselines.json"
        if baseline_path.exists():
            with open(baseline_path) as f:
                return json.load(f)
        return {}

    def _generate_notes(self, metrics: BenchmarkMetrics, comparator: ComparatorResult) -> str:
        """Generate human-readable notes"""
        notes = []
        notes.append(f"Performance grade: {comparator.grade}")
        notes.append(f"Tokens/sec: {metrics.tokens_per_sec:.2f} (baseline: {comparator.baseline_tokens_per_sec:.2f})")

        if comparator.probable_causes:
            notes.append("Issues detected:")
            for cause in comparator.probable_causes:
                notes.append(f"  - {cause}")

        return "\n".join(notes)

# Global engine instance
benchmark_engine = BenchmarkEngine()
