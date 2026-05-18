import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


class ApiSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "healthy")
        self.assertIn("version", payload)

    def test_models_include_catalog_metadata(self):
        response = self.client.get("/api/models")

        self.assertEqual(response.status_code, 200)
        models = response.json()
        self.assertTrue(models)
        first = models[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("huggingface_id", first)

    def test_recommendations_endpoint(self):
        response = self.client.get("/api/models/recommendations")

        self.assertEqual(response.status_code, 200)
        recommendations = response.json()
        self.assertTrue(recommendations)
        self.assertIn("ai_model_id", recommendations[0])


if __name__ == "__main__":
    unittest.main()
