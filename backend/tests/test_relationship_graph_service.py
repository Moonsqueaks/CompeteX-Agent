from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import (
    BattlefieldData,
    BattlefieldGraphNode,
    BattlefieldQASummary,
    BattlefieldRelationFilter,
    BattlefieldSliceSelection,
    DisplayStatus,
    EvidenceCredibilityStatus,
    PMRelationshipLabel,
    ProductRole,
    TaskStatus,
    ThreatLevel,
    TraceData,
)
from app.services import (
    RELATIONSHIP_GRAPH_ARTIFACT_TYPE,
    REPORT_ARTIFACT_TYPE,
    TRACE_ARTIFACT_TYPE,
    RelationshipGraphService,
    RelationshipGraphServiceError,
    ReportService,
    render_relationship_graph_png,
)
from app.storage import ArtifactRepository, TaskRepository

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _create_completed_task(tmp_path: Path) -> tuple[str, object]:
    database_url = f"sqlite:///{(tmp_path / 'relationship_graph.db').as_posix()}"
    api_app = create_app(database_url=database_url)
    test_client = TestClient(api_app)
    response = test_client.post(
        "/tasks",
        json={
            "target_product_name": "relationship graph target",
            "target_product_url": "https://example.com/relationship-graph",
            "category": "smart_pet_hardware",
            "subcategory": "automatic_litter_box",
            "data_source_mode": "demo_snapshot",
        },
    )
    assert response.status_code == 201
    task_id = response.json()["data"]["task_id"]

    session = api_app.state.session_factory()
    try:
        updated = TaskRepository(session).update_status(task_id, TaskStatus.COMPLETED)
        assert updated is not None
    finally:
        session.close()
    return task_id, api_app


def _repositories(api_app: object) -> tuple[object, TaskRepository, ArtifactRepository]:
    session = api_app.state.session_factory()
    return session, TaskRepository(session), ArtifactRepository(session)


def test_relationship_graph_service_generates_png_file(tmp_path: Path) -> None:
    task_id, api_app = _create_completed_task(tmp_path)
    session, task_repository, artifact_repository = _repositories(api_app)
    try:
        service = RelationshipGraphService(
            task_repository=task_repository,
            artifact_repository=artifact_repository,
            output_dir=tmp_path / "graphs",
        )

        graph_image = service.export_relationship_graph(task_id)

        output_path = Path(graph_image.file_path)
        artifacts = artifact_repository.list_by_task(
            task_id,
            RELATIONSHIP_GRAPH_ARTIFACT_TYPE,
        )
        report_artifacts = artifact_repository.list_by_task(task_id, REPORT_ARTIFACT_TYPE)
        assert output_path.exists()
        assert output_path.suffix == ".png"
        assert output_path.read_bytes()[:8] == PNG_SIGNATURE
        assert graph_image.byte_size > 0
        assert graph_image.file_name == output_path.name
        assert graph_image.metadata["security_scan"] == "passed"
        assert len(artifacts) == 1
        assert report_artifacts
    finally:
        session.close()


def test_relationship_graph_renderer_generates_placeholder_without_competitors(
    tmp_path: Path,
) -> None:
    battlefield = _minimal_battlefield()

    output_path = render_relationship_graph_png(
        battlefield,
        output_dir=tmp_path,
        file_name="placeholder.png",
    )

    assert output_path.exists()
    assert output_path.read_bytes()[:8] == PNG_SIGNATURE
    assert output_path.stat().st_size > 0


def test_relationship_graph_failure_is_recorded_without_breaking_report(
    tmp_path: Path,
) -> None:
    task_id, api_app = _create_completed_task(tmp_path)
    session, task_repository, artifact_repository = _repositories(api_app)

    def failing_renderer(*_args, **_kwargs) -> Path:
        raise OSError("api_key=should-not-leak sk-12345678")

    try:
        service = RelationshipGraphService(
            task_repository=task_repository,
            artifact_repository=artifact_repository,
            output_dir=tmp_path / "graphs",
            renderer=failing_renderer,
        )

        with pytest.raises(RelationshipGraphServiceError) as exc_info:
            service.export_relationship_graph(task_id)

        report = ReportService(
            task_repository=task_repository,
            artifact_repository=artifact_repository,
        ).get_report_data(task_id)
        trace = artifact_repository.get(
            task_id,
            TRACE_ARTIFACT_TYPE,
            f"trace_{task_id}",
            TraceData,
        )
        assert exc_info.value.code == "RELATIONSHIP_GRAPH_RENDER_FAILED"
        assert report.task_id == task_id
        assert trace is not None
        assert trace.metadata["last_failure"]["code"] == "RELATIONSHIP_GRAPH_RENDER_FAILED"
        assert trace.metadata["last_failure"]["reason"] == "OSError"
        assert "should-not-leak" not in str(trace.metadata)
        assert "api_key" not in str(trace.metadata)
    finally:
        session.close()


def test_relationship_graph_renderer_does_not_write_sensitive_text(tmp_path: Path) -> None:
    battlefield = _minimal_battlefield(
        target_label="api_key=target-secret sk-12345678",
        competitor_name="competitor token=should-not-leak sk-abcdefghi",
    )

    output_path = render_relationship_graph_png(
        battlefield,
        output_dir=tmp_path,
        file_name="api_key=should-not-leak_sk-12345678.png",
    )
    image_bytes = output_path.read_bytes()

    assert output_path.name == "REDACTED.png"
    assert b"should-not-leak" not in image_bytes
    assert b"api_key" not in image_bytes
    assert b"sk-12345678" not in image_bytes
    assert b"sk-abcdefghi" not in image_bytes


def _minimal_battlefield(
    *,
    target_label: str = "Target product",
    competitor_name: str | None = None,
) -> BattlefieldData:
    return BattlefieldData(
        battlefield_id="battlefield_placeholder",
        task_id="task_graph_placeholder",
        generated_at=datetime.now(UTC),
        selected_slice=BattlefieldSliceSelection(),
        available_slices=[],
        graph_nodes=[
            BattlefieldGraphNode(
                node_id="target",
                product_id="target",
                label=target_label,
                role=ProductRole.TARGET,
            )
        ],
        graph_edges=[],
        key_relations=[_minimal_relation(competitor_name)] if competitor_name is not None else [],
        relation_filter=BattlefieldRelationFilter(
            include_all_relations=False,
            default_limit=5,
            total_relation_count=1 if competitor_name is not None else 0,
            visible_relation_count=1 if competitor_name is not None else 0,
            can_expand_all=False,
        ),
        score_explanations=[],
        decision_chain=[],
        evidence_cards=[],
        qa_summary=BattlefieldQASummary(
            qa_status="passed",
            review_task_count=0,
            open_review_task_count=0,
            resolved_review_task_count=0,
            revision_message_count=0,
            risk_edge_ids=[],
            risk_claim_ids=[],
            review_task_ids=[],
        ),
        metadata={"target_product_id": "target"},
    )


def _minimal_relation(competitor_name: str | None):
    from app.schemas import BattlefieldExplanationSegment, BattlefieldFourPartExplanation

    segment = BattlefieldExplanationSegment(
        text="Supported by fixture evidence.",
        claim_ids=["claim_001"],
        evidence_ids=["ev_001"],
        trace_refs=["analysis_agent:edge_001"],
    )
    return {
        "edge_id": "edge_001",
        "target_product_id": "target",
        "competitor_product_id": "competitor",
        "competitor_product_name": competitor_name or "Competitor product",
        "relationship_label": PMRelationshipLabel.HEAD_TO_HEAD,
        "relationship_label_explanation": "Same decision set.",
        "threat_level": ThreatLevel.HIGH,
        "evidence_credibility": DisplayStatus(
            value=EvidenceCredibilityStatus.DIRECTLY_ADOPTABLE,
            label="Directly adoptable",
            reason="Fixture evidence is complete.",
            evidence_ids=["ev_001"],
            trace_refs=["analysis_agent:edge_001"],
        ),
        "inclusion_reason": "Top fixture relation.",
        "four_part_explanation": BattlefieldFourPartExplanation(
            why_competitor=segment,
            strength=segment,
            decision_stage_impact=segment,
            response_suggestion=segment.model_copy(update={"is_analysis_suggestion": True}),
        ),
        "action_suggestion": "Track this relation.",
        "claim_ids": ["claim_001"],
        "evidence_ids": ["ev_001"],
        "trace_refs": ["analysis_agent:edge_001"],
    }
