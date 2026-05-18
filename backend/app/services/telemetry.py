"""Real-time system telemetry collection"""
import psutil
import time
import threading
import logging
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any
from collections import deque

from app.models.schemas import TelemetrySample, SystemStatus
from app.models.database import db
from app.config import config

logger = logging.getLogger(__name__)

class TelemetryAgent:
    """Lightweight telemetry sampling agent"""

    def __init__(self):
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._interval = config.telemetry_interval
        self._samples: deque = deque(maxlen=1000)
        self._callbacks: List[Callable[[TelemetrySample], None]] = []
        self._start_time: Optional[datetime] = None
        self._lock = threading.Lock()
        self._process_filter: Optional[str] = None

        # GPU monitoring
        self._nvml_available = False
        self._try_init_nvml()

    def _try_init_nvml(self):
        try:
            from pynvml import nvmlInit, nvmlDeviceGetCount
            nvmlInit()
            self._nvml_available = True
            self._gpu_count = nvmlDeviceGetCount()
            logger.info(f"NVML initialized, found {self._gpu_count} GPU(s)")
        except Exception as e:
            logger.debug(f"NVML not available: {e}")

    @property
    def is_running(self) -> bool:
        return self._running

    def register_callback(self, callback: Callable[[TelemetrySample], None]):
        """Register a callback for real-time updates"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def set_process_filter(self, process_name: Optional[str]):
        """Filter telemetry to specific process"""
        self._process_filter = process_name

    def start(self):
        """Start telemetry collection"""
        if self._running:
            return

        self._running = True
        self._start_time = datetime.utcnow()
        self._thread = threading.Thread(target=self._collect_loop, daemon=True)
        self._thread.start()
        logger.info("Telemetry agent started")

    def stop(self):
        """Stop telemetry collection"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Telemetry agent stopped")

    def _collect_loop(self):
        """Main collection loop"""
        while self._running:
            try:
                sample = self._collect_sample()

                with self._lock:
                    self._samples.append(sample)

                # Persist to database
                db.save_telemetry(sample)

                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(sample)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")

                time.sleep(self._interval)

            except Exception as e:
                logger.error(f"Telemetry collection error: {e}")
                time.sleep(self._interval)

    def _collect_sample(self) -> TelemetrySample:
        """Collect a single telemetry sample"""
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        # GPU
        gpu_percent = None
        gpu_vram_used = None
        if self._nvml_available:
            try:
                from pynvml import nvmlDeviceGetHandleByIndex, nvmlDeviceGetUtilizationRates
                from pynvml import nvmlDeviceGetMemoryInfo

                handle = nvmlDeviceGetHandleByIndex(0)  # Primary GPU
                util = nvmlDeviceGetUtilizationRates(handle)
                mem = nvmlDeviceGetMemoryInfo(handle)

                gpu_percent = float(util.gpu)
                gpu_vram_used = mem.used / (1024**2)  # MB
            except Exception as e:
                logger.debug(f"GPU sampling failed: {e}")

        # Process-specific monitoring
        process_name = None
        process_id = None
        if self._process_filter:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                if self._process_filter.lower() in proc.info['name'].lower():
                    process_name = proc.info['name']
                    process_id = proc.info['pid']
                    break

        # Temperature (if available)
        temperature = None
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        temperature = entries[0].current
                        break
        except Exception:
            pass

        # Power (if available)
        power = None
        try:
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery and battery.power_plugged is not None:
                    power = 0 if battery.power_plugged else None
        except Exception:
            pass

        return TelemetrySample(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024**2),
            gpu_percent=gpu_percent,
            gpu_vram_used_mb=gpu_vram_used,
            npu_percent=None,  # NPU monitoring would need vendor SDK
            temperature_c=temperature,
            power_w=power,
            process_name=process_name,
            process_id=process_id
        )

    def get_recent_samples(self, count: int = 100) -> List[TelemetrySample]:
        """Get recent samples"""
        with self._lock:
            return list(self._samples)[-count:]

    def get_status(self) -> SystemStatus:
        """Get current monitoring status"""
        uptime = 0.0
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()

        last = self._samples[-1] if self._samples else None

        # Generate alerts
        alerts = []
        if last:
            if last.cpu_percent > 90:
                alerts.append("High CPU usage detected")
            if last.memory_percent > 90:
                alerts.append("High memory usage detected")
            if last.temperature_c and last.temperature_c > 85:
                alerts.append("Thermal throttling risk")

        return SystemStatus(
            is_monitoring=self._running,
            last_sample=last,
            uptime_seconds=uptime,
            samples_collected=len(self._samples),
            alerts=alerts
        )

    def get_stats(self, hours: int = 1) -> Dict[str, Any]:
        """Get aggregated statistics"""
        samples = db.get_telemetry(hours=hours)

        if not samples:
            return {}

        cpu_values = [s["cpu_percent"] for s in samples if s["cpu_percent"] is not None]
        mem_values = [s["memory_percent"] for s in samples if s["memory_percent"] is not None]
        gpu_values = [s["gpu_percent"] for s in samples if s["gpu_percent"] is not None]
        temp_values = [s["temperature_c"] for s in samples if s["temperature_c"] is not None]

        def stats(values):
            if not values:
                return {}
            return {
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max(values)
            }

        return {
            "period_hours": hours,
            "sample_count": len(samples),
            "cpu": stats(cpu_values),
            "memory": stats(mem_values),
            "gpu": stats(gpu_values),
            "temperature": stats(temp_values)
        }

# Global agent instance
telemetry_agent = TelemetryAgent()
