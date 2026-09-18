import os

os.environ["DATABASE_PATH"] = "./test_api.db"
os.environ["SCAN_ON_STARTUP"] = "false"
os.environ["AI_ENABLE_OLLAMA"] = "false"
os.environ["AI_ENABLE_GROQ"] = "false"
os.environ["AI_ENABLE_OPENROUTER"] = "false"

from fastapi.testclient import TestClient

from backend.app import app


def test_app_starts_and_serves_frontend_offline():
    with TestClient(app) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "OMNIPOOL AI" in page.text

        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True

        trends = client.get("/api/trends")
        assert trends.status_code == 200
        assert isinstance(trends.json(), list)

        ai_status = client.get("/api/v1/ai/status")
        assert ai_status.status_code == 200
        assert isinstance(ai_status.json(), list)
