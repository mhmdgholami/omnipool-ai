import os
os.environ['DATABASE_PATH']='./test_api.db'
from fastapi.testclient import TestClient
from backend.app import app

def test_health_and_trends():
    with TestClient(app) as c:
        h=c.get('/api/health'); assert h.status_code==200 and h.json()['ok'] is True
        t=c.get('/api/trends'); assert t.status_code==200 and isinstance(t.json(),list)
