from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import ProductProfileData, TaskStatus
from app.services import MAX_EVIDENCE_SUMMARY_CHARS, PRODUCT_PROFILE_ARTIFACT_TYPE
from app.storage import ArtifactRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'profile_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    return TestClient(api_app), api_app


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "画像接口目标",
        "target_product_url": "https://example.com/profile",
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


def _list_profile_artifacts(api_app: object, task_id: str) -> list[ProductProfileData]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            PRODUCT_PROFILE_ARTIFACT_TYPE,
            ProductProfileData,
        )
        return [ProductProfileData.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def test_completed_task_can_get_product_profile_modules(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/profile", headers={"X-Trace-Id": "trace_profile"})

    payload = response.json()
    profile = payload["data"]
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_profile"
    assert profile["task_id"] == task_id
    assert profile["product"]["role"] == "target"
    assert profile["feature_tree"]["product_id"] == profile["product"]["product_id"]
    assert profile["pricing_model"]["product_id"] == profile["product"]["product_id"]
    assert profile["user_persona"]["product_id"] == profile["product"]["product_id"]
    assert profile["evidence_summaries"]
    assert _list_profile_artifacts(api_app, task_id)[0].profile_id == profile["profile_id"]


def test_profile_price_fields_include_evidence_refs_and_access_time_status(
    tmp_path: Path,
) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/profile")

    profile = response.json()["data"]
    pricing_model = profile["pricing_model"]
    pricing_evidence = profile["pricing_evidence"]
    evidence_ids = {item["evidence_id"] for item in profile["evidence_summaries"]}
    assert pricing_model["evidence_ids"]
    assert pricing_evidence["evidence_ids"] == pricing_model["evidence_ids"]
    assert pricing_evidence["access_time_status"] in {"available", "missing"}
    assert set(pricing_model["evidence_ids"]).issubset(evidence_ids)
    if pricing_evidence["access_time_status"] == "available":
        assert pricing_evidence["access_time"] is not None


def test_profile_returns_horizontal_comparison_first_layer(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/profile")

    comparison = response.json()["data"]["horizontal_comparison"]
    assert response.status_code == 200
    assert comparison["target_product_id"]
    slots = {product["slot"] for product in comparison["compared_products"]}
    assert "target" in slots
    assert "highest_threat_direct_competitor" in slots
    assert "highest_threat_alternative" in slots
    dimension_keys = {dimension["dimension_key"] for dimension in comparison["dimensions"]}
    assert dimension_keys == {
        "price_band",
        "core_selling_points",
        "persona",
        "scenario",
        "evidence_credibility",
    }
    for dimension in comparison["dimensions"]:
        assert dimension["target_status"] in {
            "advantage",
            "parity",
            "weakness",
            "insufficient_evidence",
        }
        assert dimension["evidence_ids"]


def test_profile_evidence_summary_is_short_and_does_not_leak_research_text(
    tmp_path: Path,
) -> None:
    client, api_app = _client(tmp_path)
    private_research = "用户访谈原文 api_key=should-not-leak " * 20
    task_id = _create_task(client, research_text=private_research)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/profile")

    serialized = response.text.lower()
    profile = response.json()["data"]
    for evidence in profile["evidence_summaries"]:
        assert len(evidence["content_summary"]) <= MAX_EVIDENCE_SUMMARY_CHARS
        assert len(evidence["limitations"]) <= MAX_EVIDENCE_SUMMARY_CHARS
    assert "should-not-leak" not in serialized
    assert "api_key" not in serialized


def test_unfinished_task_profile_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}/profile")

    payload = response.json()
    assert response.status_code == 409
    assert payload["data"] is None
    assert payload["error"]["code"] == "PROFILE_NOT_READY"
    assert payload["error"]["details"]["task_id"] == task_id
    assert payload["error"]["details"]["status"] == "created"


def test_missing_task_profile_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/tasks/task_missing/profile")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["details"]["task_id"] == "task_missing"
