"""SQLite database for local storage"""
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from app.config import config
from app.models.schemas import BenchmarkReport, TelemetrySample

class Database:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.data_dir / "scoobybench.db"
        self._init_db()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self):
        with self._connect() as conn:
            # Benchmark reports
            conn.execute("""
                CREATE TABLE IF NOT EXISTS benchmark_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    device_info TEXT NOT NULL,
                    model_config TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    normalization TEXT NOT NULL,
                    comparator TEXT NOT NULL,
                    environment TEXT,
                    notes TEXT,
                    report_json TEXT NOT NULL
                )
            """)

            # Telemetry samples
            conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cpu_percent REAL,
                    memory_percent REAL,
                    memory_used_mb REAL,
                    gpu_percent REAL,
                    gpu_vram_used_mb REAL,
                    npu_percent REAL,
                    temperature_c REAL,
                    power_w REAL,
                    process_name TEXT,
                    process_id INTEGER
                )
            """)

            # Create index for time-based queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_time ON benchmark_runs(timestamp)")

    def save_benchmark(self, report: BenchmarkReport) -> str:
        report_payload = report.model_dump(mode="json")
        run_id = report.run_id or str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO benchmark_runs 
                (run_id, timestamp, device_info, model_config, metrics, 
                 normalization, comparator, environment, notes, report_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                report.timestamp.isoformat(),
                json.dumps(report_payload["device"]),
                json.dumps(report_payload["model"]),
                json.dumps(report_payload["metrics"]),
                json.dumps(report_payload["normalization"]),
                json.dumps(report_payload["comparator"]),
                json.dumps(report_payload["environment_snapshot"]),
                report.notes,
                json.dumps(report_payload)
            ))
        return run_id

    def get_benchmark(self, run_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT report_json FROM benchmark_runs WHERE run_id = ?", 
                (run_id,)
            ).fetchone()
            return json.loads(row["report_json"]) if row else None

    def list_benchmarks(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT run_id, timestamp, report_json FROM benchmark_runs ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [{
                "run_id": r["run_id"],
                "timestamp": r["timestamp"],
                "summary": json.loads(r["report_json"])
            } for r in rows]

    def save_telemetry(self, sample: TelemetrySample):
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO telemetry 
                (timestamp, cpu_percent, memory_percent, memory_used_mb, gpu_percent,
                 gpu_vram_used_mb, npu_percent, temperature_c, power_w, process_name, process_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sample.timestamp.isoformat(),
                sample.cpu_percent,
                sample.memory_percent,
                sample.memory_used_mb,
                sample.gpu_percent,
                sample.gpu_vram_used_mb,
                sample.npu_percent,
                sample.temperature_c,
                sample.power_w,
                sample.process_name,
                sample.process_id
            ))

    def get_telemetry(self, hours: int = 24) -> List[Dict[str, Any]]:
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM telemetry WHERE timestamp > ? ORDER BY timestamp",
                (cutoff,)
            ).fetchall()
            return [dict(r) for r in rows]

    def cleanup_old_telemetry(self, days: int = 30):
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            conn.execute("DELETE FROM telemetry WHERE timestamp < ?", (cutoff,))
            deleted = conn.total_changes
        return deleted

    def get_stats(self) -> Dict[str, Any]:
        with self._connect() as conn:
            benchmarks = conn.execute("SELECT COUNT(*) as count FROM benchmark_runs").fetchone()["count"]
            telemetry = conn.execute("SELECT COUNT(*) as count FROM telemetry").fetchone()["count"]
            oldest = conn.execute("SELECT MIN(timestamp) as t FROM telemetry").fetchone()["t"]
            return {
                "benchmark_runs": benchmarks,
                "telemetry_samples": telemetry,
                "oldest_sample": oldest
            }

db = Database()
