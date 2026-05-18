import time
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


class TelemetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_telemetry_status_and_lifecycle(self):
        start_response = self.client.post("/api/telemetry/start")
        self.assertEqual(start_response.status_code, 200)

        time.sleep(0.3)

        status_response = self.client.get("/api/telemetry/status")
        self.assertEqual(status_response.status_code, 200)
        status = status_response.json()
        self.assertTrue(status["is_monitoring"])

        stop_response = self.client.post("/api/telemetry/stop")
        self.assertEqual(stop_response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
