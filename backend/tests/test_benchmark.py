import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


class BenchmarkWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_synthetic_benchmark_run_and_fetch(self):
        payload = {
            "model": {
                "name": "phi-2",
                "params_million": 2700,
                "precision": "fp16",
                "batch_size": 1,
                "prompt_tokens": 8,
                "target_tokens": 2,
                "repeats": 1,
            }
        }

        response = self.client.post("/api/benchmark/run", json=payload)
        self.assertEqual(response.status_code, 200)

        report = response.json()
        self.assertIn("run_id", report)
        self.assertGreater(report["metrics"]["tokens_per_sec"], 0)

        fetch_response = self.client.get(f"/api/benchmark/report/{report['run_id']}")
        self.assertEqual(fetch_response.status_code, 200)
        fetched = fetch_response.json()
        self.assertEqual(fetched["run_id"], report["run_id"])

    def test_benchmark_progress_defaults_to_idle(self):
        response = self.client.get("/api/benchmark/progress/non-existent-model")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["stage"], "idle")


if __name__ == "__main__":
    unittest.main()
