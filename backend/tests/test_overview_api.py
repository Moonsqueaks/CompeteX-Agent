from pathlib import Path

from fastapi.testclient import TestClient

from app.graph import build_analysis_workflow, create_initial_state
from app.main import create_app
from app.schemas import BattlefieldData, BattlefieldSliceSelection, OverviewData, TaskStatus
from app.services import BATTLEFIELD_ARTIFACT_TYPE, OVERVIEW_ARTIFACT_TYPE
from app.services.battlefield_service import _battlefield_artifact_id, _build_battlefield_data
from app.services.overview_service import _overview_artifact_id
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


def _save_overview_artifact(api_app: object, overview: OverviewData) -> None:
    session = api_app.state.session_factory()
    try:
        ArtifactRepository(session).save(
            OVERVIEW_ARTIFACT_TYPE,
            overview.overview_id,
            overview,
        )
    finally:
        session.close()


def _get_default_battlefield(api_app: object, task_id: str) -> BattlefieldData:
    session = api_app.state.session_factory()
    try:
        artifact = ArtifactRepository(session).get(
            task_id,
            BATTLEFIELD_ARTIFACT_TYPE,
            _battlefield_artifact_id(task_id, BattlefieldSliceSelection()),
            BattlefieldData,
        )
        assert artifact is not None
        return BattlefieldData.model_validate(artifact)
    finally:
        session.close()


def _cache_battlefield_only(api_app: object, task_id: str) -> None:
    session = api_app.state.session_factory()
    try:
        task = TaskRepository(session).get(task_id)
        assert task is not None
        result = build_analysis_workflow().invoke(create_initial_state(task))
        selected_slice = BattlefieldSliceSelection()
        battlefield_id = _battlefield_artifact_id(task_id, selected_slice)
        battlefield = _build_battlefield_data(dict(result), selected_slice, battlefield_id)
        ArtifactRepository(session).save(
            BATTLEFIELD_ARTIFACT_TYPE,
            battlefield.battlefield_id,
            battlefield,
        )
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


def test_overview_uses_cached_battlefield_without_rerunning_workflow(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)
    _cache_battlefield_only(api_app, task_id)
    api_app.state.overview_workflow_factory = lambda: (_ for _ in ()).throw(
        AssertionError("overview should not rerun workflow when battlefield cache exists")
    )

    response = client.get(f"/tasks/{task_id}/overview")

    battlefield = _get_default_battlefield(api_app, task_id)
    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["metadata"]["source"] == "cached_battlefield_artifact"
    assert payload["data"]["metadata"]["battlefield_id"] == battlefield.battlefield_id
    assert _list_overview_artifacts(api_app, task_id)[0].metadata["source"] == (
        "cached_battlefield_artifact"
    )


def test_overview_sanitizes_cached_internal_standard_copy(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)
    overview_id = _overview_artifact_id(task_id, BattlefieldSliceSelection())
    overview = OverviewData.model_validate(client.get(f"/tasks/{task_id}/overview").json()["data"])
    internal_standard_copy = "按 " + "2." + "0 标准"
    stale_competitor = overview.key_competitors[0].model_copy(
        update={
            "inclusion_reason": (
                f"DeepSeek 在当前切片关系分为 0.79，{internal_standard_copy}标记为中威胁。"
            )
        }
    )
    stale_overview = overview.model_copy(
        update={
            "overview_id": overview_id,
            "key_competitors": [stale_competitor, *overview.key_competitors[1:]],
        }
    )
    _save_overview_artifact(api_app, stale_overview)
    api_app.state.overview_workflow_factory = lambda: (_ for _ in ()).throw(
        AssertionError("overview should use cached artifact")
    )

    response = client.get(f"/tasks/{task_id}/overview")

    payload = response.json()
    cached_overview = _list_overview_artifacts(api_app, task_id)[0]
    inclusion_reason = payload["data"]["key_competitors"][0]["inclusion_reason"]
    assert response.status_code == 200
    assert internal_standard_copy not in inclusion_reason
    assert "当前标记为中威胁" in inclusion_reason
    assert internal_standard_copy not in cached_overview.key_competitors[0].inclusion_reason


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
