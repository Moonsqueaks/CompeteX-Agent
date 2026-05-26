from pathlib import Path

from fastapi.testclient import TestClient

from app.graph import build_analysis_workflow
from app.main import create_app
from app.schemas import BattlefieldData, TaskStatus
from app.services import BATTLEFIELD_ARTIFACT_TYPE
from app.storage import ArtifactRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'battlefield_api.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    return TestClient(api_app), api_app


def _create_task(client: TestClient, **overrides) -> str:
    payload = {
        "target_product_name": "战场接口目标",
        "target_product_url": "https://example.com/battlefield",
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


def _list_battlefield_artifacts(api_app: object, task_id: str) -> list[BattlefieldData]:
    session = api_app.state.session_factory()
    try:
        artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            BATTLEFIELD_ARTIFACT_TYPE,
            BattlefieldData,
        )
        return [BattlefieldData.model_validate(artifact) for artifact in artifacts]
    finally:
        session.close()


def test_default_battlefield_returns_direct_and_alternative_competitors(
    tmp_path: Path,
) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(
        f"/tasks/{task_id}/battlefield",
        headers={"X-Trace-Id": "trace_battlefield"},
    )

    payload = response.json()
    battlefield = payload["data"]
    edge_scores = [edge["edge_score"] for edge in battlefield["graph_edges"]]
    competition_types = {edge["competition_type"] for edge in battlefield["graph_edges"]}
    direct_scores = [
        edge["edge_score"]
        for edge in battlefield["graph_edges"]
        if edge["competition_type"] == "direct"
    ]
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["trace_id"] == "trace_battlefield"
    assert battlefield["task_id"] == task_id
    assert battlefield["graph_nodes"]
    assert battlefield["graph_edges"]
    assert battlefield["available_slices"]
    assert "direct" in competition_types
    assert {"alternative", "channel", "content_cooccurrence"}.intersection(competition_types)
    assert edge_scores == sorted(edge_scores, reverse=True)
    assert direct_scores[0] == max(direct_scores)
    assert _list_battlefield_artifacts(api_app, task_id)[0].battlefield_id == battlefield[
        "battlefield_id"
    ]


def test_battlefield_price_band_filter_changes_edges_or_explanations(
    tmp_path: Path,
) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    default_data = client.get(f"/tasks/{task_id}/battlefield").json()["data"]
    default_edge_ids = [edge["edge_id"] for edge in default_data["graph_edges"]]
    price_band = next(
        option["price_band"]
        for option in default_data["available_slices"]
        if option["edge_count"] < len(default_edge_ids)
    )

    response = client.get(f"/tasks/{task_id}/battlefield", params={"price_band": price_band})

    filtered = response.json()["data"]
    filtered_edge_ids = [edge["edge_id"] for edge in filtered["graph_edges"]]
    assert response.status_code == 200
    assert filtered["selected_slice"]["price_band"] == price_band
    assert filtered["graph_edges"]
    assert all(edge["slice"]["price_band"] == price_band for edge in filtered["graph_edges"])
    assert (
        filtered_edge_ids != default_edge_ids
        or filtered["score_explanations"] != default_data["score_explanations"]
    )


def test_battlefield_edges_include_claim_and_evidence_refs(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    response = client.get(f"/tasks/{task_id}/battlefield")

    battlefield = response.json()["data"]
    evidence_card_ids = {card["evidence_id"] for card in battlefield["evidence_cards"]}
    assert response.status_code == 200
    for edge in battlefield["graph_edges"]:
        assert edge["claim_ids"]
        assert edge["evidence_ids"]
        assert edge["claim_refs"]
        assert set(edge["evidence_ids"]).issubset(evidence_card_ids)
        for claim_ref in edge["claim_refs"]:
            assert set(claim_ref["evidence_ids"]).issubset(edge["evidence_ids"])


def test_battlefield_qa_marked_edge_has_risk_status(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    task_id = _create_task(client)
    _mark_completed(api_app, task_id)

    class RiskMarkedWorkflow:
        def invoke(self, state):
            result = build_analysis_workflow().invoke(state)
            edge = result["competition_edges"][0]
            edge["risk_flags"] = ["missing_evidence"]
            return result

    api_app.state.battlefield_workflow_factory = RiskMarkedWorkflow

    response = client.get(f"/tasks/{task_id}/battlefield")

    battlefield = response.json()["data"]
    risk_edges = [edge for edge in battlefield["graph_edges"] if edge["risk_status"] == "at_risk"]
    assert response.status_code == 200
    assert risk_edges
    assert risk_edges[0]["risk_flags"]
    assert risk_edges[0]["edge_id"] in battlefield["qa_summary"]["risk_edge_ids"]
    assert battlefield["qa_summary"]["qa_status"] == "needs_attention"


def test_unfinished_task_battlefield_returns_standard_error(tmp_path: Path) -> None:
    client, _ = _client(tmp_path)
    task_id = _create_task(client)

    response = client.get(f"/tasks/{task_id}/battlefield")

    payload = response.json()
    assert response.status_code == 409
    assert payload["data"] is None
    assert payload["error"]["code"] == "BATTLEFIELD_NOT_READY"
    assert payload["error"]["details"]["task_id"] == task_id
    assert payload["error"]["details"]["status"] == "created"
