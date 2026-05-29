from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import TaskStatus, TraceData
from app.services import TRACE_ARTIFACT_TYPE
from app.storage import ArtifactRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'trace_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    return TestClient(api_app), api_app


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "Trace API target",
        "target_product_url": "https://example.com/trace",
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


def _list_trace_artifacts(api_app: object, task_id: str) -> list[TraceData]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            TRACE_ARTIFACT_TYPE,
            TraceData,
        )
        return [TraceData.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def test_trace_returns_dag_nodes_and_edges(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/trace", headers={"X-Trace-Id": "trace_api"})

    payload = response.json()
    trace_data = payload["data"]
    node_ids = {node["node_id"] for node in trace_data["dag_nodes"]}
    edge_pairs = {(edge["source"], edge["target"]) for edge in trace_data["dag_edges"]}
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_api"
    assert trace_data["task_id"] == task_id
    assert {
        "collection_agent",
        "analysis_agent",
        "qa_agent",
        "writer_agent",
        "failed",
        "end",
    }.issubset(node_ids)
    assert ("collection_agent", "analysis_agent") in edge_pairs
    assert ("analysis_agent", "qa_agent") in edge_pairs
    assert ("qa_agent", "writer_agent") in edge_pairs
    assert ("qa_agent", "collection_agent") in edge_pairs
    assert ("qa_agent", "analysis_agent") in edge_pairs
    assert ("qa_agent", "failed") in edge_pairs
    assert next(node for node in trace_data["dag_nodes"] if node["node_id"] == "failed")["visible"]
    assert _list_trace_artifacts(api_app, task_id)[0].trace_view_id == trace_data[
        "trace_view_id"
    ]


def test_trace_includes_each_agent_run_log(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/trace")

    trace_data = response.json()["data"]
    agent_names = {run["agent_name"] for run in trace_data["agent_runs"]}
    node_run_refs = {
        node["node_id"]: node["run_ids"]
        for node in trace_data["dag_nodes"]
        if node["node_type"] == "agent"
    }
    assert response.status_code == 200
    assert {"collection_agent", "analysis_agent", "qa_agent", "writer_agent"}.issubset(
        agent_names
    )
    for agent_name in ["collection_agent", "analysis_agent", "qa_agent", "writer_agent"]:
        assert node_run_refs[agent_name]


def test_trace_includes_qa_revision_records_and_diff_view(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/trace")

    trace_data = response.json()["data"]
    revision_targets = {message["to_agent"] for message in trace_data["revision_messages"]}
    diff_sources = {diff["source"] for diff in trace_data["diffs"]}
    assert response.status_code == 200
    assert trace_data["qa_reviews"]
    assert trace_data["qa_reviews"][0]["status"] == "resolved"
    assert trace_data["qa_reviews"][0]["resolved_at"] is not None
    assert "collection_agent" in revision_targets
    assert "analysis_agent" in revision_targets
    assert "collection_agent_repair" in diff_sources
    assert "analysis_agent_recompute" in diff_sources
    for diff in trace_data["diffs"]:
        assert diff["target_id"]
        assert "before" in diff
        assert "after" in diff


def test_trace_redacts_sensitive_values_and_folds_prompt_previews(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(
        client,
        research_text=(
            "api_key=should-not-leak Bearer private-token sk-testsecret12345 "
            "DOUBAO_API_KEY=sk-envsecret12345 手机 13800138000 "
            "account_id=acct-private-001 地址: 北京市朝阳区幸福路88号3单元501室"
        ),
    )
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/trace")

    response_text = response.text.lower()
    trace_data = response.json()["data"]
    assert response.status_code == 200
    assert "should-not-leak" not in response_text
    assert "private-token" not in response_text
    assert "sk-testsecret12345" not in response_text
    assert "sk-envsecret12345" not in response_text
    assert "doubao_api_key" not in response_text
    assert "13800138000" not in response_text
    assert "acct-private-001" not in response_text
    assert "北京市朝阳区幸福路88号3单元501室" not in response_text
    assert "api_key" not in response_text
    assert trace_data["prompt_previews"]
    for preview in trace_data["prompt_previews"]:
        assert preview["folded"] is True
        assert preview["redacted"] is True


def test_unfinished_task_trace_returns_skeleton_dag(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}/trace")

    trace_data = response.json()["data"]
    assert response.status_code == 200
    assert trace_data["task_status"] == "created"
    assert trace_data["agent_runs"] == []
    assert {node["node_id"] for node in trace_data["dag_nodes"]}.issuperset(
        {"collection_agent", "analysis_agent", "qa_agent", "writer_agent", "failed"}
    )


def test_missing_task_trace_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.get("/tasks/missing-task/trace")

    payload = response.json()
    assert response.status_code == 404
    assert payload["data"] is None
    assert payload["error"]["code"] == "TASK_NOT_FOUND"
    assert payload["error"]["details"]["task_id"] == "missing-task"
