from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import inspect

from app.schemas import (
    AgentRunLog,
    AnalysisTask,
    Claim,
    CompetitionEdge,
    Evidence,
    HumanFeedback,
    TaskStatus,
    TokenUsageLog,
    ToolCallLog,
)
from app.storage import (
    ArtifactRepository,
    HumanFeedbackRepository,
    TaskRepository,
    TraceLogRepository,
    create_database_engine,
    create_session_factory,
    default_sqlite_path,
    init_db,
)

NOW = datetime(2026, 5, 22, 2, 0, tzinfo=UTC)


def _session(tmp_path: Path):
    engine = create_database_engine(f"sqlite:///{(tmp_path / 'storage_test.db').as_posix()}")
    init_db(engine)
    session_factory = create_session_factory(engine)
    return engine, session_factory()


def _task() -> AnalysisTask:
    return AnalysisTask(
        task_id="task_001",
        target_product_name="Demo automatic litter box",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        created_at=NOW,
        updated_at=NOW,
        target_product_url="https://example.com/products/target",
        research_text="Interview summary",
        metadata={"demo": True},
    )


def _evidence() -> Evidence:
    return Evidence(
        evidence_id="ev_001",
        task_id="task_001",
        product_id="prod_target",
        source_type="douyin_sku_snapshot",
        source_url="https://example.com/products/target",
        screenshot_path="data/raw/sku_02/price.png",
        access_time=NOW,
        content_summary="Snapshot includes price and selling points.",
        confidence_level="medium",
        limitations="Local snapshot, not a live page.",
    )


def _claim() -> Claim:
    return Claim(
        claim_id="claim_001",
        task_id="task_001",
        claim_type="pricing_advantage",
        content="Competitor A is more price-attractive in this slice.",
        evidence_ids=["ev_001"],
        confidence=0.78,
        is_inference=False,
        risk_flags=[],
        status="accepted",
        created_at=NOW,
    )


def _competition_edge() -> CompetitionEdge:
    return CompetitionEdge(
        edge_id="edge_001",
        task_id="task_001",
        target_product_id="prod_target",
        competitor_product_id="prod_a",
        competition_type="direct",
        slice={
            "price_band": "1500-2000",
            "persona": "multi_cat_household",
            "scenario": "odor_control",
        },
        decision_stages=["capability_understanding", "decision_completion"],
        edge_score=0.82,
        score_breakdown={
            "demand_substitutability": 0.9,
            "context_match": 0.85,
            "decision_stage_impact": 0.75,
            "evidence_confidence": 0.7,
            "market_signal_strength": 0.75,
        },
        claim_ids=["claim_001"],
        human_adjusted=False,
        risk_flags=[],
        created_at=NOW,
    )


def _agent_run_log() -> AgentRunLog:
    return AgentRunLog(
        run_id="run_001",
        task_id="task_001",
        agent_name="collection_agent",
        status="succeeded",
        started_at=NOW,
        ended_at=NOW,
        input_summary="Load local SKU snapshots.",
        output_summary="Loaded products and evidence.",
    )


def _tool_call_log() -> ToolCallLog:
    return ToolCallLog(
        tool_call_id="tool_001",
        task_id="task_001",
        run_id="run_001",
        tool_name="snapshot_loader",
        arguments_summary={"path": "data/snapshots"},
        status="succeeded",
        started_at=NOW,
        ended_at=NOW,
        duration_ms=35,
    )


def _token_usage_log() -> TokenUsageLog:
    return TokenUsageLog(
        usage_id="usage_001",
        task_id="task_001",
        run_id="run_001",
        agent_name="analysis_agent",
        model_name="rules",
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        created_at=NOW,
    )


def _human_feedback() -> HumanFeedback:
    return HumanFeedback(
        feedback_id="hf_001",
        task_id="task_001",
        target_type="claim",
        target_id="claim_001",
        action="mark_needs_review",
        before_value={"status": "accepted"},
        after_value={"status": "needs_review"},
        reason="Evidence needs manual review.",
        created_at=NOW,
    )


def test_init_db_creates_storage_tables(tmp_path: Path) -> None:
    engine, session = _session(tmp_path)
    session.close()

    table_names = set(inspect(engine).get_table_names())

    assert {
        "analysis_tasks",
        "artifact_json",
        "trace_logs",
        "human_feedback",
    }.issubset(table_names)


def test_task_repository_creates_reads_and_updates_task_status(tmp_path: Path) -> None:
    _, session = _session(tmp_path)
    repository = TaskRepository(session)

    created = repository.create(_task())
    loaded = repository.get(created.task_id)
    updated = repository.update_status(created.task_id, TaskStatus.ANALYZING, updated_at=NOW)

    assert loaded is not None
    assert loaded.task_id == "task_001"
    assert loaded.metadata == {"demo": True}
    assert updated is not None
    assert updated.status == TaskStatus.ANALYZING
    session.close()


def test_artifact_repository_saves_and_queries_json_artifacts(tmp_path: Path) -> None:
    _, session = _session(tmp_path)
    repository = ArtifactRepository(session)
    evidence = _evidence()
    claim = _claim()
    edge = _competition_edge()

    repository.save("evidence", evidence.evidence_id, evidence)
    repository.save("claim", claim.claim_id, claim)
    repository.save("competition_edge", edge.edge_id, edge)

    loaded_evidence = repository.get("task_001", "evidence", "ev_001", Evidence)
    loaded_claims = repository.list_by_task("task_001", "claim", Claim)
    loaded_edges = repository.list_by_task("task_001", "competition_edge", CompetitionEdge)

    assert loaded_evidence == evidence
    assert loaded_claims == [claim]
    assert loaded_edges == [edge]
    session.close()


def test_trace_repository_queries_logs_by_task_id(tmp_path: Path) -> None:
    _, session = _session(tmp_path)
    repository = TraceLogRepository(session)

    repository.save("agent_run", "run_001", _agent_run_log())
    repository.save("tool_call", "tool_001", _tool_call_log())
    repository.save("token_usage", "usage_001", _token_usage_log())

    all_logs = repository.list_by_task("task_001")
    run_logs = repository.list_by_task("task_001", "agent_run", AgentRunLog)

    assert [log["log_type"] for log in all_logs] == ["agent_run", "tool_call", "token_usage"]
    assert run_logs == [_agent_run_log()]
    session.close()


def test_human_feedback_repository_saves_and_lists_feedback(tmp_path: Path) -> None:
    _, session = _session(tmp_path)
    repository = HumanFeedbackRepository(session)
    feedback = _human_feedback()

    saved = repository.save(feedback)
    loaded = repository.get(feedback.feedback_id)
    listed = repository.list_by_task("task_001")

    assert saved == feedback
    assert loaded == feedback
    assert listed == [feedback]
    session.close()


def test_storage_tests_do_not_create_default_database(tmp_path: Path) -> None:
    default_path = default_sqlite_path()
    existed_before = default_path.exists()
    mtime_before = default_path.stat().st_mtime_ns if existed_before else None

    engine, session = _session(tmp_path)
    session.close()
    engine.dispose()

    assert (tmp_path / "storage_test.db").exists()
    assert default_path.exists() is existed_before
    if existed_before:
        assert default_path.stat().st_mtime_ns == mtime_before
