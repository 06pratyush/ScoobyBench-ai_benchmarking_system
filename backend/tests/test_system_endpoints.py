from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestSystemSummary:
    def test_summary_shape(self):
        response = client.get("/api/system/summary")
        assert response.status_code == 200
        body = response.json()
        assert body["system"]["memory"]["total_gb"] > 0
        assert body["system"]["cpu"]["logical_cores"] >= 1
        assert body["backend_process"]["rss_mb"] > 0

    def test_profile_is_cached_static_hardware(self):
        first = client.get("/api/system/profile").json()
        second = client.get("/api/system/profile").json()
        assert first["cpu"]["name"] == second["cpu"]["name"]
        assert "ram" in first and "power_plan" in first


class TestConfigEndpoint:
    def test_roundtrip_preserves_mutable_key(self):
        original = client.get("/api/config").json()
        try:
            response = client.post("/api/config", json={"default_repeats": 4})
            assert response.status_code == 200
            assert response.json()["default_repeats"] == 4
        finally:
            client.post("/api/config", json={"default_repeats": original["default_repeats"]})

    def test_readonly_keys_are_ignored(self):
        before = client.get("/api/config").json()
        response = client.post("/api/config", json={"port": 1234})
        assert response.status_code == 200
        assert response.json()["port"] == before["port"]

    def test_invalid_value_rejected(self):
        response = client.post("/api/config", json={"telemetry_interval": 0.001})
        assert response.status_code == 400
