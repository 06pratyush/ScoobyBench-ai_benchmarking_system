"""Run-to-run comparison and benchmark history analytics."""
import logging
import statistics
from typing import Any, Dict, List, Optional

from app.models.database import db

logger = logging.getLogger(__name__)


def _pct_change(new: Optional[float], old: Optional[float]) -> Optional[float]:
    if new is None or old is None or old == 0:
        return None
    return round(((new - old) / old) * 100, 2)


def _metric(report: Dict[str, Any], *path: str) -> Optional[float]:
    node: Any = report
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return None
        node = node[key]
    return node


class RunComparator:
    """Compares saved benchmark reports against each other."""

    def compare_runs(self, run_id_a: str, run_id_b: str) -> Dict[str, Any]:
        """Compare two saved runs. Run A is the reference, run B the candidate."""
        report_a = db.get_benchmark(run_id_a)
        report_b = db.get_benchmark(run_id_b)

        if report_a is None:
            raise KeyError(f"Report not found: {run_id_a}")
        if report_b is None:
            raise KeyError(f"Report not found: {run_id_b}")

        tps_a = _metric(report_a, "metrics", "tokens_per_sec")
        tps_b = _metric(report_b, "metrics", "tokens_per_sec")
        p50_a = _metric(report_a, "metrics", "latency", "p50_ms")
        p50_b = _metric(report_b, "metrics", "latency", "p50_ms")
        p99_a = _metric(report_a, "metrics", "latency", "p99_ms")
        p99_b = _metric(report_b, "metrics", "latency", "p99_ms")
        ram_a = _metric(report_a, "metrics", "peak_ram_mb")
        ram_b = _metric(report_b, "metrics", "peak_ram_mb")

        tps_change = _pct_change(tps_b, tps_a)

        if tps_change is None:
            verdict = "inconclusive"
        elif tps_change > 5:
            verdict = "improvement"
        elif tps_change < -5:
            verdict = "regression"
        else:
            verdict = "comparable"

        same_model = (
            _metric(report_a, "model", "name") == _metric(report_b, "model", "name")
        )
        same_device = (
            _metric(report_a, "device", "cpu") == _metric(report_b, "device", "cpu")
            and _metric(report_a, "device", "gpu") == _metric(report_b, "device", "gpu")
        )

        return {
            "run_a": {
                "run_id": run_id_a,
                "timestamp": report_a.get("timestamp"),
                "model": _metric(report_a, "model", "name"),
                "tokens_per_sec": tps_a,
                "p50_ms": p50_a,
                "p99_ms": p99_a,
                "peak_ram_mb": ram_a,
                "grade": _metric(report_a, "comparator", "grade"),
            },
            "run_b": {
                "run_id": run_id_b,
                "timestamp": report_b.get("timestamp"),
                "model": _metric(report_b, "model", "name"),
                "tokens_per_sec": tps_b,
                "p50_ms": p50_b,
                "p99_ms": p99_b,
                "peak_ram_mb": ram_b,
                "grade": _metric(report_b, "comparator", "grade"),
            },
            "delta": {
                "tokens_per_sec_pct": tps_change,
                "p50_latency_pct": _pct_change(p50_b, p50_a),
                "p99_latency_pct": _pct_change(p99_b, p99_a),
                "peak_ram_pct": _pct_change(ram_b, ram_a),
            },
            "same_model": same_model,
            "same_device": same_device,
            "verdict": verdict,
            "notes": self._verdict_notes(verdict, same_model, same_device, tps_change),
        }

    @staticmethod
    def _verdict_notes(
        verdict: str, same_model: bool, same_device: bool, tps_change: Optional[float]
    ) -> List[str]:
        notes = []
        if not same_model:
            notes.append("Runs used different models — deltas are not apples-to-apples.")
        if not same_device:
            notes.append("Runs were captured on different hardware.")
        if verdict == "improvement":
            notes.append(f"Run B is {tps_change:+.1f}% faster than run A.")
        elif verdict == "regression":
            notes.append(f"Run B is {tps_change:+.1f}% slower than run A.")
        elif verdict == "comparable":
            notes.append("Throughput within +/-5% — effectively the same performance.")
        return notes

    def history_summary(self, limit: int = 200) -> Dict[str, Any]:
        """Aggregate stats across saved benchmark history, grouped by model."""
        rows = db.list_benchmarks(limit=limit, offset=0)

        by_model: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            report = row.get("summary") or {}
            model_name = _metric(report, "model", "name") or "unknown"
            by_model.setdefault(model_name, []).append(report)

        models = []
        for name, reports in by_model.items():
            tps_values = [
                t for t in (_metric(r, "metrics", "tokens_per_sec") for r in reports)
                if t is not None
            ]
            grades = [
                g for g in (_metric(r, "comparator", "grade") for r in reports) if g
            ]
            if not tps_values:
                continue
            best = max(tps_values)
            latest = tps_values[0]  # list_benchmarks is ordered newest-first
            models.append({
                "model": name,
                "runs": len(reports),
                "best_tokens_per_sec": round(best, 2),
                "latest_tokens_per_sec": round(latest, 2),
                "mean_tokens_per_sec": round(statistics.mean(tps_values), 2),
                "stdev_tokens_per_sec": (
                    round(statistics.stdev(tps_values), 2) if len(tps_values) > 1 else 0.0
                ),
                "latest_vs_best_pct": _pct_change(latest, best),
                "grades": {g: grades.count(g) for g in sorted(set(grades))},
            })

        models.sort(key=lambda m: m["runs"], reverse=True)

        return {
            "total_runs": len(rows),
            "models_benchmarked": len(models),
            "models": models,
        }


# Global instance
run_comparator = RunComparator()
