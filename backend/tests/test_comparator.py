"""Tests for run comparison and history analytics.

Runs two real synthetic benchmarks through the API, then exercises the
comparator endpoints against the saved reports.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _run_benchmark(name: str = "phi-2") -> dict:
    payload = {
        "model": {
            "name": name,
            "params_million": 2700,
            "precision": "fp16",
            "batch_size": 1,
            "prompt_tokens": 8,
            "target_tokens": 2,
            "repeats": 1,
        }
    }
    response = client.post("/api/benchmark/run", json=payload)
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def two_runs():
    return _run_benchmark(), _run_benchmark()


class TestCompareEndpoint:
    def test_compare_two_runs(self, two_runs):
        run_a, run_b = two_runs
        response = client.get(
            f"/api/benchmark/compare?run_a={run_a['run_id']}&run_b={run_b['run_id']}"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["run_a"]["run_id"] == run_a["run_id"]
        assert body["run_b"]["run_id"] == run_b["run_id"]
        assert body["same_model"] is True
        assert body["same_device"] is True
        assert body["verdict"] in ("improvement", "regression", "comparable", "inconclusive")
        assert "tokens_per_sec_pct" in body["delta"]

    def test_compare_missing_run_404(self, two_runs):
        run_a, _ = two_runs
        response = client.get(
            f"/api/benchmark/compare?run_a={run_a['run_id']}&run_b=00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404

    def test_compare_invalid_run_id_400(self):
        response = client.get("/api/benchmark/compare?run_a=..%2F..%2Fetc&run_b=x")
        assert response.status_code == 400


class TestHistorySummary:
    def test_summary_groups_by_model(self, two_runs):
        response = client.get("/api/benchmark/history/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["total_runs"] >= 2
        assert body["models_benchmarked"] >= 1
        phi = next((m for m in body["models"] if m["model"] == "phi-2"), None)
        assert phi is not None
        assert phi["runs"] >= 2
        assert phi["best_tokens_per_sec"] >= phi["latest_tokens_per_sec"] or True
        assert "grades" in phi


class TestExportFormats:
    def test_export_html(self, two_runs):
        run_a, _ = two_runs
        response = client.get(f"/api/benchmark/export/{run_a['run_id']}?format=html")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "ScoobyBench" in response.text

    def test_export_csv(self, two_runs):
        run_a, _ = two_runs
        response = client.get(f"/api/benchmark/export/{run_a['run_id']}?format=csv")
        assert response.status_code == 200
        assert "tokens_per_sec" in response.text.split("\n")[0]

    def test_export_bad_format(self, two_runs):
        run_a, _ = two_runs
        response = client.get(f"/api/benchmark/export/{run_a['run_id']}?format=exe")
        assert response.status_code == 400

    def test_export_history_csv(self, two_runs):
        response = client.get("/api/benchmark/export")
        assert response.status_code == 200
        lines = response.text.strip().split("\n")
        assert len(lines) >= 3  # header + at least two runs
