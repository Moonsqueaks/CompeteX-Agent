from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import HumanFeedback, TaskStatus
from app.services import HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE
from app.storage import ArtifactRepository, HumanFeedbackRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'feedback_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    return TestClient(api_app), api_app


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "Human feedback target",
        "target_product_url": "https://example.com/feedback",
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


def _load_task(api_app: object, task_id: str):
    session = api_app.state.session_factory()
    try:
        return TaskRepository(session).get(task_id)
    finally:
        session.close()


def _list_feedback(api_app: object, task_id: str) -> list[HumanFeedback]:
    session = api_app.state.session_factory()
    try:
        return HumanFeedbackRepository(session).list_by_task(task_id)
    finally:
        session.close()


def _list_feedback_effects(api_app: object, task_id: str) -> list[dict]:
    session = api_app.state.session_factory()
    try:
        return ArtifactRepository(session).list_by_task(
            task_id,
            HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE,
        )
    finally:
        session.close()


def test_feedback_api_saves_allowed_product_profile_update(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)
    profile = client.get(f"/tasks/{task_id}/profile").json()["data"]
    product_id = profile["product"]["product_id"]
    before_brand = profile["product"]["brand"]

    response = client.post(
        f"/tasks/{task_id}/feedback",
        json={
            "target_type": "product",
            "target_id": product_id,
            "action": "update_field",
            "after_value": {"field": "brand", "value": "人工确认品牌"},
            "reason": "人工核对后修正品牌展示",
        },
        headers={"X-Trace-Id": "trace_feedback"},
    )

    payload = response.json()
    feedback = payload["data"]["feedback"]
    persisted_feedback = _list_feedback(api_app, task_id)[0]
    updated_task = _load_task(api_app, task_id)
    assert response.status_code == 201
    assert payload["trace_id"] == "trace_feedback"
    assert payload["error"] is None
    assert payload["data"]["task_status"] == "human_reviewing"
    assert payload["data"]["recompute_status"] == "applied_local_update"
    assert feedback["before_value"] == {"field": "brand", "value": before_brand}
    assert feedback["after_value"] == {"field": "brand", "value": "人工确认品牌"}
    assert persisted_feedback.feedback_id == feedback["feedback_id"]
    assert updated_task.status == TaskStatus.HUMAN_REVIEWING
    assert updated_task.metadata["requires_analysis_recompute"] is False

    refreshed_profile = client.get(f"/tasks/{task_id}/profile").json()["data"]
    assert refreshed_profile["product"]["brand"] == "人工确认品牌"


def test_feedback_api_marks_claim_status_and_records_before_after(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)
    battlefield = client.get(f"/tasks/{task_id}/battlefield").json()["data"]
    claim_id = battlefield["graph_edges"][0]["claim_ids"][0]

    response = client.post(
        f"/tasks/{task_id}/feedback",
        json={
            "target_type": "claim",
            "target_id": claim_id,
            "action": "mark_rejected",
            "after_value": {},
            "reason": "人工确认该结论暂不纳入报告",
        },
    )

    feedback = response.json()["data"]["feedback"]
    assert response.status_code == 201
    assert feedback["target_id"] == claim_id
    assert feedback["before_value"] == {"status": "accepted"}
    assert feedback["after_value"] == {"status": "rejected"}
    assert claim_id in response.json()["data"]["affected_artifact_ids"]

    refreshed_battlefield = client.get(f"/tasks/{task_id}/battlefield").json()["data"]
    refreshed_claim = refreshed_battlefield["graph_edges"][0]["claim_refs"][0]
    assert refreshed_claim["claim_id"] == claim_id
    assert refreshed_claim["status"] == "rejected"
    assert refreshed_battlefield["graph_edges"][0]["risk_status"] == "at_risk"


def test_feedback_api_rejects_free_report_rewrite(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.post(
        f"/tasks/{task_id}/feedback",
        json={
            "target_type": "claim",
            "target_id": "claim_any",
            "action": "update_field",
            "after_value": {"field": "content", "value": "直接改写整份报告"},
            "reason": "试图自由改写报告内容",
        },
    )

    payload = response.json()
    assert response.status_code == 400
    assert payload["data"] is None
    assert payload["error"]["code"] == "FEEDBACK_NOT_ALLOWED"


def test_feedback_api_writes_recompute_marker_artifact(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)
    profile = client.get(f"/tasks/{task_id}/profile").json()["data"]
    evidence_id = profile["evidence_summaries"][0]["evidence_id"]

    response = client.post(
        f"/tasks/{task_id}/feedback",
        json={
            "target_type": "evidence",
            "target_id": evidence_id,
            "action": "add_note",
            "after_value": {"note": "人工确认该截图可作为价格参考"},
            "reason": "补充人工证据备注",
        },
    )

    feedback_id = response.json()["data"]["feedback"]["feedback_id"]
    effects = _list_feedback_effects(api_app, task_id)
    assert response.status_code == 201
    assert len(effects) == 1
    assert effects[0]["feedback_id"] == feedback_id
    assert effects[0]["recompute_status"] == "applied_local_update"
    assert effects[0]["affected_artifact_ids"] == [evidence_id]
    assert effects[0]["cached_artifact_ids"]


def test_unfinished_task_feedback_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.post(
        f"/tasks/{task_id}/feedback",
        json={
            "target_type": "product",
            "target_id": "prod_missing",
            "action": "update_field",
            "after_value": {"field": "brand", "value": "人工确认"},
            "reason": "未完成任务不能反馈",
        },
    )

    payload = response.json()
    assert response.status_code == 409
    assert payload["data"] is None
    assert payload["error"]["code"] == "FEEDBACK_NOT_READY"
    assert payload["error"]["details"]["status"] == "created"


def test_missing_task_feedback_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.post(
        "/tasks/missing-task/feedback",
        json={
            "target_type": "product",
            "target_id": "prod_missing",
            "action": "update_field",
            "after_value": {"field": "brand", "value": "人工确认"},
            "reason": "缺失任务",
        },
    )

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["details"]["task_id"] == "missing-task"
