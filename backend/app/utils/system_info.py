"""Lightweight runtime system summary (fast, no WMI queries).

Complements hardware_detect.py: that module answers "what hardware is this?"
(slow, cached), while this one answers "how is the machine doing right now?"
(cheap psutil calls, safe to poll frequently).
"""
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import psutil


def get_runtime_summary() -> Dict[str, Any]:
    """Return a fast snapshot of current system state."""
    mem = psutil.virtual_memory()
    disk_root = Path.cwd().anchor or "/"
    disk = psutil.disk_usage(disk_root)
    boot = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    now = datetime.now(timezone.utc)

    freq = None
    try:
        cpu_freq = psutil.cpu_freq()
        freq = round(cpu_freq.current, 0) if cpu_freq else None
    except Exception:
        pass

    return {
        "timestamp": now.isoformat(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "uptime_seconds": round((now - boot).total_seconds(), 0),
        "cpu": {
            "percent": psutil.cpu_percent(interval=0.1),
            "frequency_mhz": freq,
            "logical_cores": psutil.cpu_count(logical=True),
        },
        "memory": {
            "total_gb": round(mem.total / 1024**3, 2),
            "available_gb": round(mem.available / 1024**3, 2),
            "percent": mem.percent,
        },
        "disk": {
            "mount": disk_root,
            "total_gb": round(disk.total / 1024**3, 2),
            "free_gb": round(disk.free / 1024**3, 2),
            "percent": disk.percent,
        },
        "process_count": len(psutil.pids()),
    }


def get_process_summary() -> Dict[str, Any]:
    """Return resource usage of the ScoobyBench backend process itself."""
    proc = psutil.Process()
    with proc.oneshot():
        mem = proc.memory_info()
        return {
            "pid": proc.pid,
            "rss_mb": round(mem.rss / 1024**2, 1),
            "vms_mb": round(mem.vms / 1024**2, 1),
            "cpu_percent": proc.cpu_percent(interval=0.05),
            "threads": proc.num_threads(),
            "started_at": datetime.fromtimestamp(
                proc.create_time(), tz=timezone.utc
            ).isoformat(),
            "executable": sys.executable,
        }
