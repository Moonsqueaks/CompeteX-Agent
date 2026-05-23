from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"] == {"status": "ok"}
    assert payload["error"] is None
    assert payload["trace_id"].startswith("trace_")
    assert response.headers["x-trace-id"] == payload["trace_id"]
