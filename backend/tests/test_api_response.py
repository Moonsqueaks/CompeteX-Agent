from fastapi.testclient import TestClient

from app.api.responses import build_error_payload
from app.main import app


def test_success_response_uses_client_trace_id() -> None:
    client = TestClient(app)

    response = client.get("/health", headers={"X-Trace-Id": "trace_client_test"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["data"] == {"status": "ok"}
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_client_test"
    assert response.headers["x-trace-id"] == "trace_client_test"


def test_not_found_response_uses_standard_error_shape() -> None:
    client = TestClient(app)

    response = client.get("/missing")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["trace_id"].startswith("trace_")
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["error"]["message"] == "Resource not found"
    assert payload["error"]["details"]["path"] == "/missing"


def test_error_payload_redacts_sensitive_values(monkeypatch) -> None:
    monkeypatch.setenv("DOUBAO_API_KEY", "test-secret-key")

    payload = build_error_payload(
        code="TEST_ERROR",
        message="DOUBAO_API_KEY api_key=test-secret-key",
        trace_id="trace_test",
        details={
            "api_key": "test-secret-key",
            "safe": "visible",
            "nested": {"authorization": "Bearer test-secret-key"},
        },
    )

    serialized = str(payload)
    assert "test-secret-key" not in serialized
    assert "DOUBAO_API_KEY" not in serialized
    assert payload["error"]["message"] == "[REDACTED] [REDACTED]"
    assert payload["error"]["details"]["api_key"] == "[REDACTED]"
    assert payload["error"]["details"]["safe"] == "visible"
    assert payload["error"]["details"]["nested"]["authorization"] == "[REDACTED]"
