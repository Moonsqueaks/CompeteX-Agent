from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import TaskStatus
from app.storage import TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'tasks_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    return TestClient(api_app), api_app


def _load_task(api_app: object, task_id: str):
    session = api_app.state.session_factory()
    try:
        return TaskRepository(session).get(task_id)
    finally:
        session.close()


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "状态查询目标",
        "target_product_url": "https://example.com/status",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "data_source_mode": "demo_snapshot",
        "research_text": "用户访谈摘要",
    }
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()["data"]["task_id"]


def test_create_task_api_creates_task_and_persists_it(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)

    response = client.post(
        "/tasks",
        json={
            "target_product_name": "Demo 自动猫砂盆",
            "target_product_url": "https://example.com/demo",
            "category": "smart_pet_hardware",
            "subcategory": "automatic_litter_box",
            "data_source_mode": "demo_snapshot",
            "research_text": "用户访谈摘要",
        },
        headers={"X-Trace-Id": "trace_create_task"},
    )

    payload = response.json()
    assert response.status_code == 201
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_create_task"
    assert payload["data"]["status"] == "created"
    assert payload["data"]["task"]["target_product_name"] == "Demo 自动猫砂盆"

    persisted = _load_task(api_app, payload["data"]["task_id"])
    assert persisted is not None
    assert persisted.task_id == payload["data"]["task_id"]
    assert persisted.target_product_url == "https://example.com/demo"


def test_create_task_rejects_blank_target_product_name(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.post("/tasks", json={"target_product_name": "   "})

    payload = response.json()
    assert response.status_code == 422
    assert payload["data"] is None
    assert payload["error"]["code"] == "VALIDATION_ERROR"


def test_create_task_defaults_to_demo_snapshot_mode(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.post("/tasks", json={"target_product_name": "手动输入目标"})

    payload = response.json()
    assert response.status_code == 201
    assert payload["data"]["task"]["data_source_mode"] == "demo_snapshot"
    assert payload["data"]["task"]["status"] == "created"


def test_create_task_uses_default_demo_target_when_target_is_omitted(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)

    response = client.post("/tasks", json={})

    payload = response.json()
    task = payload["data"]["task"]
    assert response.status_code == 201
    assert task["target_product_name"] == "小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆"
    assert task["target_product_url"] == "https://v.douyin.com/mv8e4KRLLwc/"
    assert task["metadata"]["default_target_sku_id"] == "sku_02"
    assert task["metadata"]["target_selection"] == "demo_default_target"

    persisted = _load_task(api_app, payload["data"]["task_id"])
    assert persisted is not None
    assert persisted.target_product_name == task["target_product_name"]


def test_create_task_response_uses_unified_api_shape(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.post("/tasks", json={"target_product_name": "统一响应测试"})

    payload = response.json()
    assert set(payload) == {"data", "error", "trace_id"}
    assert payload["data"]["task_id"].startswith("task_")
    assert payload["data"]["task"]["task_id"] == payload["data"]["task_id"]
    assert payload["error"] is None


def test_get_task_status_returns_existing_task(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}", headers={"X-Trace-Id": "trace_get_task"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_get_task"
    assert payload["data"]["task_id"] == task_id
    assert payload["data"]["target_product_name"] == "状态查询目标"
    assert payload["data"]["status"] == "created"
    assert payload["data"]["created_at"]
    assert payload["data"]["updated_at"]


def test_get_task_status_missing_task_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/tasks/task_missing")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["message"] == "Task not found"
    assert payload["error"]["details"]["task_id"] == "task_missing"
    assert payload["trace_id"].startswith("trace_")


def test_get_task_status_uses_allowed_status_enum_value(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}")

    allowed_statuses = {status.value for status in TaskStatus}
    assert response.json()["data"]["status"] in allowed_statuses


def test_get_task_status_does_not_return_sensitive_or_large_fields(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client, research_text="api_key=should-not-leak")

    response = client.get(f"/tasks/{task_id}")

    serialized = response.text.lower()
    data = response.json()["data"]
    assert "research_text" not in data
    assert "metadata" not in data
    assert "api_key" not in serialized
    assert "should-not-leak" not in serialized
    assert "trace_logs" not in serialized
    assert "artifact_json" not in serialized
