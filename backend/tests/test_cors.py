from fastapi.testclient import TestClient

from app.main import create_app


def test_local_vite_origin_can_preflight_tasks_create() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "content-type" in response.headers["access-control-allow-headers"].lower()


def test_unknown_origin_is_not_allowed_for_preflight() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/tasks",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_local_vite_origin_can_preflight_private_network_requests() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
            "Access-Control-Request-Private-Network": "true",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers["access-control-allow-private-network"] == "true"


def test_local_vite_fallback_port_can_preflight_tasks_create() -> None:
    client = TestClient(create_app())

    response = client.options(
        "/tasks",
        headers={
            "Origin": "http://127.0.0.1:5175",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5175"
