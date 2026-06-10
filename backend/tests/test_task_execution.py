from pathlib import Path

from fastapi.testclient import TestClient

from app.graph import build_analysis_workflow
from app.main import _env_flag, create_app
from app.schemas import (
    BattlefieldData,
    CompetitorBattlecard,
    GapMatrixItem,
    KnowledgeArtifact,
    OpportunityItem,
    OverviewData,
    ProductProfileData,
    ReportData,
    ReportQualityCheck,
    StrategyBrief,
    TaskStatus,
    TraceData,
)
from app.services import (
    BATTLEFIELD_ARTIFACT_TYPE,
    COMPETITOR_BATTLECARD_ARTIFACT_TYPE,
    GAP_MATRIX_ITEM_ARTIFACT_TYPE,
    KNOWLEDGE_ARTIFACT_TYPE,
    OPPORTUNITY_ITEM_ARTIFACT_TYPE,
    OVERVIEW_ARTIFACT_TYPE,
    PRODUCT_PROFILE_ARTIFACT_TYPE,
    REPORT_ARTIFACT_TYPE,
    REPORT_QUALITY_CHECK_ARTIFACT_TYPE,
    STRATEGY_BRIEF_ARTIFACT_TYPE,
    TRACE_ARTIFACT_TYPE,
)
from app.storage import ArtifactRepository, TaskRepository


def _client(tmp_path: Path) -> tuple[TestClient, object]:
    database_url = f"sqlite:///{(tmp_path / 'task_execution.db').as_posix()}"
    api_app = create_app(
        database_url=database_url,
        auto_start_task_execution=True,
        run_task_execution_inline=True,
    )
    return TestClient(api_app), api_app


def _artifact_count(api_app: object, task_id: str, artifact_type: str) -> int:
    session = api_app.state.session_factory()
    try:
        return len(ArtifactRepository(session).list_by_task(task_id, artifact_type))
    finally:
        session.close()


def _task_status(api_app: object, task_id: str) -> TaskStatus:
    session = api_app.state.session_factory()
    try:
        task = TaskRepository(session).get(task_id)
        assert task is not None
        return task.status
    finally:
        session.close()


def _task_execution_counts(api_app: object, task_id: str) -> dict[str, int]:
    session = api_app.state.session_factory()
    try:
        task = TaskRepository(session).get(task_id)
        assert task is not None
        execution = task.metadata.get("task_execution", {})
        counts = execution.get("artifact_counts", {})
        assert isinstance(counts, dict)
        return counts
    finally:
        session.close()


def _failing_analysis_node(state):
    raise RuntimeError("analysis node failed for step 37")


def test_task_creation_starts_langgraph_and_caches_end_to_end_outputs(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)

    create_response = client.post(
        "/tasks",
        json={
            "target_product_name": "端到端任务流目标",
            "target_product_url": "https://example.com/e2e-task",
            "category": "smart_pet_hardware",
            "subcategory": "automatic_litter_box",
            "data_source_mode": "demo_snapshot",
        },
    )

    task_id = create_response.json()["data"]["task_id"]
    status_response = client.get(f"/tasks/{task_id}")
    trace_response = client.get(f"/tasks/{task_id}/trace")
    profile_response = client.get(f"/tasks/{task_id}/profile")
    battlefield_response = client.get(f"/tasks/{task_id}/battlefield")
    report_response = client.get(f"/tasks/{task_id}/report")
    overview_response = client.get(f"/tasks/{task_id}/overview")

    assert create_response.status_code == 201
    assert create_response.json()["data"]["status"] == "created"
    assert status_response.status_code == 200
    assert status_response.json()["data"]["status"] == "completed"
    assert _task_status(api_app, task_id) == TaskStatus.COMPLETED

    trace = TraceData.model_validate(trace_response.json()["data"])
    profile = ProductProfileData.model_validate(profile_response.json()["data"])
    battlefield = BattlefieldData.model_validate(battlefield_response.json()["data"])
    report = ReportData.model_validate(report_response.json()["data"])
    overview = OverviewData.model_validate(overview_response.json()["data"])

    assert trace_response.status_code == 200
    assert {run.agent_name.value for run in trace.agent_runs}.issuperset(
        {"collection_agent", "analysis_agent", "qa_agent", "writer_agent"}
    )
    assert [run.agent_name.value for run in trace.agent_runs].count("collection_agent") == 2
    assert [run.agent_name.value for run in trace.agent_runs].count("analysis_agent") == 2
    assert [run.agent_name.value for run in trace.agent_runs].count("qa_agent") == 2
    assert any(
        message.message_type.value == "revision_request"
        and message.to_agent.value == "collection_agent"
        for message in trace.revision_messages
    )
    assert any(diff.source == "collection_agent_repair" for diff in trace.diffs)
    assert any(diff.source == "analysis_agent_recompute" for diff in trace.diffs)
    assert trace.qa_reviews[0].status.value == "resolved"
    assert any(record.check_item == "报告质量规则检查" for record in trace.quality_records)
    assert profile_response.status_code == 200
    assert profile.product.role == "target"
    assert battlefield_response.status_code == 200
    assert battlefield.graph_edges
    assert battlefield.qa_summary.qa_status == "passed"
    assert battlefield.qa_summary.open_review_task_count == 0
    assert battlefield.qa_summary.resolved_review_task_count == 1
    assert report_response.status_code == 200
    assert report.section_order
    assert overview_response.status_code == 200
    assert overview.key_competitors
    assert overview.metadata["source"] == "langgraph_workflow"
    competitor_items = report.core_competitor_analysis.model_dump(mode="json")["items"]
    competitor_claims = [
        claim
        for item in competitor_items
        for claim in item.get("claims", [])
    ]
    assert competitor_claims
    assert all(claim.get("evidence_ids") for claim in competitor_claims)
    assert all("missing_evidence" not in claim.get("risk_flags", []) for claim in competitor_claims)

    assert _artifact_count(api_app, task_id, TRACE_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, PRODUCT_PROFILE_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, BATTLEFIELD_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, OVERVIEW_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, REPORT_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, KNOWLEDGE_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, STRATEGY_BRIEF_ARTIFACT_TYPE) == 1
    assert _artifact_count(api_app, task_id, COMPETITOR_BATTLECARD_ARTIFACT_TYPE) >= 1
    assert _artifact_count(api_app, task_id, GAP_MATRIX_ITEM_ARTIFACT_TYPE) >= 2
    assert _artifact_count(api_app, task_id, OPPORTUNITY_ITEM_ARTIFACT_TYPE) >= 3
    assert _artifact_count(api_app, task_id, REPORT_QUALITY_CHECK_ARTIFACT_TYPE) == 1

    session = api_app.state.session_factory()
    try:
        knowledge_artifacts = ArtifactRepository(session).list_by_task(
            task_id,
            KNOWLEDGE_ARTIFACT_TYPE,
            KnowledgeArtifact,
        )
        strategy_briefs = ArtifactRepository(session).list_by_task(
            task_id,
            STRATEGY_BRIEF_ARTIFACT_TYPE,
            StrategyBrief,
        )
        battlecards = ArtifactRepository(session).list_by_task(
            task_id,
            COMPETITOR_BATTLECARD_ARTIFACT_TYPE,
            CompetitorBattlecard,
        )
        gap_items = ArtifactRepository(session).list_by_task(
            task_id,
            GAP_MATRIX_ITEM_ARTIFACT_TYPE,
            GapMatrixItem,
        )
        opportunity_items = ArtifactRepository(session).list_by_task(
            task_id,
            OPPORTUNITY_ITEM_ARTIFACT_TYPE,
            OpportunityItem,
        )
        report_quality_checks = ArtifactRepository(session).list_by_task(
            task_id,
            REPORT_QUALITY_CHECK_ARTIFACT_TYPE,
            ReportQualityCheck,
        )
    finally:
        session.close()
    assert knowledge_artifacts[0].external_search_performed is False
    assert knowledge_artifacts[0].items
    assert strategy_briefs[0].primary_competition_axis
    assert all(item.target_response for item in battlecards)
    assert {item.dimension for item in gap_items}.issuperset({"功能能力差距", "证据差距"})
    assert all(item.linked_gaps or item.linked_battlecards for item in opportunity_items)
    assert report_quality_checks[0].report_id == report.report_id

    artifact_counts = _task_execution_counts(api_app, task_id)
    assert artifact_counts["strategy_briefs"] == len(strategy_briefs)
    assert artifact_counts["competitor_battlecards"] == len(battlecards)
    assert artifact_counts["gap_matrix_items"] == len(gap_items)
    assert artifact_counts["opportunity_items"] == len(opportunity_items)
    assert artifact_counts["report_quality_checks"] == len(report_quality_checks)


def test_task_execution_uses_frontend_selected_snapshot_sku_as_analysis_target(
    tmp_path: Path,
) -> None:
    client, _api_app = _client(tmp_path)

    create_response = client.post(
        "/tasks",
        json={
            "target_product_url": "https://v.douyin.com/DHU7x44omIs/",
            "category": "smart_pet_hardware",
            "subcategory": "automatic_litter_box",
            "data_source_mode": "demo_snapshot",
        },
    )

    task_id = create_response.json()["data"]["task_id"]
    profile_response = client.get(f"/tasks/{task_id}/profile")
    battlefield_response = client.get(f"/tasks/{task_id}/battlefield")

    profile = ProductProfileData.model_validate(profile_response.json()["data"])
    battlefield = BattlefieldData.model_validate(battlefield_response.json()["data"])

    assert create_response.status_code == 201
    assert create_response.json()["data"]["task"]["metadata"]["selected_target_sku_id"] == "sku_05"
    assert profile_response.status_code == 200
    assert profile.product.role == "target"
    assert profile.product.sku_id == "sku_05"
    assert battlefield_response.status_code == 200
    assert battlefield.metadata["target_product_id"] == profile.product.product_id
    assert all(
        edge.target_product_id == profile.product.product_id
        for edge in battlefield.graph_edges
    )


def test_task_execution_agent_failure_marks_failed_and_caches_trace(tmp_path: Path) -> None:
    client, api_app = _client(tmp_path)
    api_app.state.task_execution_workflow_factory = lambda: build_analysis_workflow(
        analysis_node=_failing_analysis_node
    )

    create_response = client.post(
        "/tasks",
        json={
            "target_product_name": "异常降级目标",
            "target_product_url": "https://example.com/failing-agent",
            "category": "smart_pet_hardware",
            "subcategory": "automatic_litter_box",
            "data_source_mode": "demo_snapshot",
        },
    )

    task_id = create_response.json()["data"]["task_id"]
    status_response = client.get(f"/tasks/{task_id}")
    trace_response = client.get(f"/tasks/{task_id}/trace")

    trace = TraceData.model_validate(trace_response.json()["data"])
    failed_node = next(node for node in trace.dag_nodes if node.node_id == "failed")
    analysis_node = next(node for node in trace.dag_nodes if node.node_id == "analysis_agent")
    analysis_runs = [run for run in trace.agent_runs if run.agent_name.value == "analysis_agent"]

    assert create_response.status_code == 201
    assert status_response.json()["data"]["status"] == "failed"
    assert _task_status(api_app, task_id) == TaskStatus.FAILED
    assert trace_response.status_code == 200
    assert trace.task_status == "failed"
    assert trace.workflow_status == "failed"
    assert failed_node.failed is True
    assert analysis_node.failed is True
    assert analysis_runs[-1].status.value == "failed"
    assert "analysis node failed for step 37" in (analysis_runs[-1].error_message or "")
    assert _artifact_count(api_app, task_id, TRACE_ARTIFACT_TYPE) == 1


def test_inline_execution_env_flag_accepts_common_truthy_values(monkeypatch) -> None:
    monkeypatch.setenv("RUN_TASK_EXECUTION_INLINE", "true")
    assert _env_flag("RUN_TASK_EXECUTION_INLINE") is True

    monkeypatch.setenv("RUN_TASK_EXECUTION_INLINE", "0")
    assert _env_flag("RUN_TASK_EXECUTION_INLINE") is False
