import os

os.environ["DATABASE_PATH"] = "./test_api.db"

from fastapi.testclient import TestClient

from backend.app import app


def test_health_and_trends():
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["ok"] is True

        trends = client.get("/api/trends")
        assert trends.status_code == 200
        assert isinstance(trends.json(), list)
