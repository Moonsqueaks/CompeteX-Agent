from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import OverviewData, TaskStatus
from app.services import OVERVIEW_ARTIFACT_TYPE
from app.storage import ArtifactRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'overview_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    return TestClient(api_app), api_app


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "总览接口目标",
        "target_product_url": "https://example.com/overview",
        "category": "smart_pet_hardware",
        "subcategory": "automatic_litter_box",
        "data_source_mode": "demo_snapshot",
        "research_text": None,
    }
    payload.update(overrides)
    response = client.post("/tasks", json=payload)
    assert response.status_code == 201
    return response.json()["data"]["task_id"]


def _mark_completed(api_app: object, task_id: str) -> None:
    session = api_app.state.session_factory()
    try:
        updated = TaskRepository(session).update_status(task_id, TaskStatus.COMPLETED)
        assert updated is not None
    finally:
        session.close()


def _list_overview_artifacts(api_app: object, task_id: str) -> list[OverviewData]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            OVERVIEW_ARTIFACT_TYPE,
            OverviewData,
        )
        return [OverviewData.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def test_completed_task_can_get_overview_data(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/overview", headers={"X-Trace-Id": "trace_overview"})

    payload = response.json()
    overview = OverviewData.model_validate(payload["data"])
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_overview"
    assert overview.task_id == task_id
    assert overview.analysis_scope.sku_count == 14
    assert overview.one_sentence_judgment.content
    assert overview.key_competitors
    assert overview.action_recommendations
    assert _list_overview_artifacts(api_app, task_id)[0].overview_id == overview.overview_id


def test_overview_query_params_are_passed_to_service(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(
        f"/tasks/{task_id}/overview",
        params={
            "price_band": "1000-1500",
            "persona": "多猫或大空间自动清理用户",
            "scenario": "自动清理",
        },
    )

    overview = response.json()["data"]
    assert response.status_code == 200
    assert overview["current_slice"] == {
        "price_band": "1000-1500",
        "persona": "多猫或大空间自动清理用户",
        "scenario": "自动清理",
    }
    assert overview["key_competitors"]


def test_unfinished_task_overview_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}/overview")

    payload = response.json()
    assert response.status_code == 409
    assert payload["data"] is None
    assert payload["error"]["code"] == "OVERVIEW_NOT_READY"
    assert payload["error"]["details"]["task_id"] == task_id
    assert payload["error"]["details"]["status"] == "created"


def test_missing_task_overview_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/tasks/task_missing/overview")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["details"]["task_id"] == "task_missing"
