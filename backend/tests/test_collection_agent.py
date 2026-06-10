from datetime import UTC, datetime

import httpx

from app.agents import analysis_agent_node, collection_agent_node, qa_agent_node
from app.graph import (
    append_claim,
    append_evidence,
    append_product,
    create_initial_state,
    serialize_state_for_trace,
)
from app.schemas import AnalysisTask, Claim, Evidence, Product
from app.services import PublicPageFetcher

NOW = datetime(2026, 5, 24, 2, 0, tzinfo=UTC)


def _task(
    research_text: str | None = None,
    task_id: str = "task_collection_agent",
) -> AnalysisTask:
    return AnalysisTask(
        task_id=task_id,
        target_product_name="Demo automatic litter box",
        target_product_url="https://example.com/products/target",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        data_source_mode="demo_snapshot",
        status="created",
        research_text=research_text,
        created_at=NOW,
        updated_at=NOW,
        metadata={"demo": True},
    )


def test_collection_agent_generates_products_evidences_and_review_insights() -> None:
    state = create_initial_state(_task())

    result = collection_agent_node(state, now=NOW)

    assert result is state
    assert len(state["products"]) >= 8
    assert len(state["products"]) == 14
    assert len(state["evidences"]) == 14
    assert len(state["review_insights"]) == 14
    assert state["claims"] == []
    assert state["competition_edges"] == []


def test_collection_agent_links_each_product_to_at_least_one_evidence() -> None:
    state = create_initial_state(_task())

    collection_agent_node(state, now=NOW)

    evidence_ids = {evidence["evidence_id"] for evidence in state["evidences"]}
    for product in state["products"]:
        assert product["evidence_ids"]
        assert set(product["evidence_ids"]).issubset(evidence_ids)


def test_collection_agent_uses_task_selected_target_sku() -> None:
    task = _task()
    task.metadata["selected_target_sku_id"] = "sku_05"
    task.metadata["target_selection"] = "matched_snapshot_sku"
    state = create_initial_state(task)

    collection_agent_node(state, now=NOW)

    targets = [product for product in state["products"] if product["role"] == "target"]
    default_product = next(
        product for product in state["products"] if product["sku_id"] == "sku_02"
    )

    assert [product["sku_id"] for product in targets] == ["sku_05"]
    assert default_product["role"] == "direct_competitor"
    assert state["metadata"]["collection_agent"]["selected_target_sku_id"] == "sku_05"


def test_collection_agent_adds_unmatched_user_input_as_evidence_gap_target() -> None:
    task = _task(task_id="task_collection_unmatched_target").model_copy(
        update={
            "target_product_name": "Snapshot external target",
            "target_product_url": "https://example.com/external-target",
        }
    )
    task.metadata["target_selection"] = "user_input_unmatched"
    task.metadata["selected_target_sku_id"] = None
    state = create_initial_state(task)

    collection_agent_node(state, now=NOW)

    targets = [product for product in state["products"] if product["role"] == "target"]

    assert len(state["products"]) == 15
    assert len(state["evidences"]) == 15
    assert len(targets) == 1
    assert targets[0]["sku_id"] is None
    assert targets[0]["name"] == "Snapshot external target"
    assert targets[0]["evidence_ids"] == [
        "ev_task_collection_unmatched_target_user_target_input"
    ]
    assert state["evidences"][-1]["product_id"] == targets[0]["product_id"]


def test_collection_agent_preserves_missing_access_time_without_auto_repair() -> None:
    state = create_initial_state(_task())

    collection_agent_node(state, now=NOW)

    qa_evidence = next(
        evidence for evidence in state["evidences"] if evidence["metadata"]["sku_id"] == "sku_01"
    )
    missing_fields = state["metadata"]["collection_agent"]["missing_evidence_fields"]

    assert qa_evidence["access_time"] is None
    assert qa_evidence["metadata"]["missing_fields"] == ["source.access_time"]
    assert missing_fields == [
        {
            "evidence_id": "ev_sku_01",
            "product_id": "prod_sku_01",
            "missing_fields": ["source.access_time"],
        }
    ]


def test_collection_agent_records_trace_run_and_tool_call_logs() -> None:
    state = create_initial_state(_task())

    collection_agent_node(state, now=NOW)

    assert len(state["run_logs"]) == 1
    assert state["run_logs"][0]["agent_name"] == "collection_agent"
    assert state["run_logs"][0]["status"] == "succeeded"
    assert "Collected 14 products" in state["run_logs"][0]["output_summary"]
    assert len(state["tool_call_logs"]) == 1
    assert state["tool_call_logs"][0]["tool_name"] == "snapshot_loader"
    assert state["tool_call_logs"][0]["status"] == "succeeded"
    assert not any(
        tool_call["tool_name"].startswith("public_page")
        for tool_call in state["tool_call_logs"]
    )


def test_collection_agent_snapshot_plus_live_generates_public_page_evidence() -> None:
    state = create_initial_state(
        _task(task_id="task_collection_public_page").model_copy(
            update={"data_source_mode": "snapshot_plus_live"}
        )
    )
    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(_public_page_handler),
        cache_dir=None,
    )

    collection_agent_node(state, now=NOW, public_page_fetcher=fetcher)

    public_evidences = [
        evidence
        for evidence in state["evidences"]
        if evidence["source_type"] == "public_product_page"
    ]
    public_tool_names = [
        tool_call["tool_name"]
        for tool_call in state["tool_call_logs"]
        if tool_call["tool_name"].startswith("public_page")
    ]
    enhanced_product_ids = {evidence["product_id"] for evidence in public_evidences}

    assert len(public_evidences) == 4
    assert "prod_sku_02" in enhanced_product_ids
    assert "prod_sku_01" in enhanced_product_ids
    assert public_evidences[0]["access_time"] == "2026-05-24T02:00:00Z"
    assert public_evidences[0]["metadata"]["llm_used"] is False
    assert public_evidences[0]["metadata"]["stage"] == "stage_1_known_url"
    assert set(public_tool_names) == {
        "public_page_policy",
        "public_page_fetcher",
        "public_page_parser",
        "public_page_enrichment",
    }
    assert state["metadata"]["public_page_enhancement"]["generated_evidence_ids"] == [
        evidence["evidence_id"] for evidence in public_evidences
    ]
    assert state["metadata"]["public_page_enhancement"]["llm_used"] is False


def test_collection_agent_snapshot_plus_live_degrades_when_fetch_fails() -> None:
    state = create_initial_state(
        _task(task_id="task_collection_public_page_fail").model_copy(
            update={"data_source_mode": "snapshot_plus_live"}
        )
    )
    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(lambda _: httpx.Response(403, text="Forbidden")),
        cache_dir=None,
    )

    collection_agent_node(state, now=NOW, public_page_fetcher=fetcher)

    assert len(state["products"]) == 14
    assert len(state["evidences"]) == 14
    assert state["metadata"]["public_page_enhancement"]["status"] == "degraded_to_snapshot"
    assert state["metadata"]["public_page_enhancement"]["generated_evidence_ids"] == []
    assert any(
        tool_call["tool_name"] == "public_page_fetcher"
        and tool_call["status"] == "failed"
        for tool_call in state["tool_call_logs"]
    )


def test_public_page_evidence_can_satisfy_missing_access_time_qa_rule() -> None:
    state = create_initial_state(
        _task(task_id="task_collection_public_page_qa").model_copy(
            update={"data_source_mode": "snapshot_plus_live"}
        )
    )
    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(_public_page_handler),
        cache_dir=None,
    )

    collection_agent_node(state, now=NOW, public_page_fetcher=fetcher)
    sku_01_public_evidence_id = next(
        evidence["evidence_id"]
        for evidence in state["evidences"]
        if evidence["source_type"] == "public_product_page"
        and evidence["product_id"] == "prod_sku_01"
    )
    append_claim(
        state,
        Claim(
            claim_id="claim_public_page_access_time",
            task_id="task_collection_public_page_qa",
            claim_type="pricing_fact",
            content=(
                "Local snapshot price and public page price evidence support current "
                "price review."
            ),
            evidence_ids=[
                "ev_sku_01",
                sku_01_public_evidence_id,
            ],
            confidence=0.72,
            is_inference=False,
            risk_flags=[],
            status="accepted",
            created_at=NOW,
        ),
    )

    qa_agent_node(state, now=NOW)

    issue_codes = [review_task["issue_code"] for review_task in state["review_tasks"]]
    assert "TIMELY_EVIDENCE_MISSING_ACCESS_TIME" not in issue_codes


def test_collection_agent_reads_user_research_text_as_evidence() -> None:
    state = create_initial_state(
        _task(research_text="Users mention odor control and easy cleaning.")
    )

    collection_agent_node(state, now=NOW)

    research_evidence = next(
        evidence for evidence in state["evidences"] if evidence["source_type"] == "user_research"
    )

    assert research_evidence["evidence_id"] == "ev_task_collection_agent_user_research"
    assert research_evidence["metadata"]["source"] == "task.research_text"
    assert state["metadata"]["collection_agent"]["research_text_loaded"] is True


def test_collection_agent_repairs_qa_collection_revision_and_records_trace_diff() -> None:
    state = create_initial_state(_task(task_id="task_collection_repair"))
    collection_agent_node(state, now=NOW)
    analysis_agent_node(state, now=NOW)
    qa_agent_node(state, now=NOW)

    revision_message = next(
        message
        for message in state["agent_messages"]
        if message["to_agent"] == "collection_agent"
    )

    assert revision_message["status"] == "requires_revision"
    assert revision_message["evidence_ids"] == ["ev_sku_01"]

    collection_agent_node(state, now=NOW)

    repair_summary = state["metadata"]["collection_agent_repair"]
    repair_diff = repair_summary["diffs"][0]
    repaired_evidence = next(
        evidence
        for evidence in state["evidences"]
        if evidence["evidence_id"] == repair_diff["new_evidence_id"]
    )
    repaired_product = next(
        product for product in state["products"] if product["product_id"] == "prod_sku_01"
    )
    trace_payload = serialize_state_for_trace(state)

    assert len(
        [
            run_log
            for run_log in state["run_logs"]
            if run_log["agent_name"] == "collection_agent"
        ]
    ) == 2
    assert state["agent_messages"][0]["status"] == "processed"
    assert repaired_evidence["access_time"] == "2026-05-23T16:00:59+08:00"
    assert repaired_evidence["screenshot_path"] == "data/raw/sku_01/QQ图片20260523155546.jpg"
    assert repaired_evidence["metadata"]["repaired_from_evidence_id"] == "ev_sku_01"
    assert repaired_evidence["metadata"]["repaired_fields"] == ["source.access_time"]
    assert repaired_evidence["metadata"]["missing_fields"] == []
    assert repaired_evidence["evidence_id"] in repaired_product["evidence_ids"]
    assert repair_summary["repaired_count"] == 1
    assert repair_diff["before"]["access_time"] is None
    assert repair_diff["after"]["access_time"] == "2026-05-23T16:00:59+08:00"
    assert repair_diff["status"] == "repaired"
    assert (
        trace_payload["metadata"]["collection_agent_repair"]["diffs"][0]
        == repair_diff
    )
    assert state["tool_call_logs"][-1]["tool_name"] == "snapshot_repair_fixture"


def test_collection_agent_marks_unrepairable_revision_as_unavailable_data() -> None:
    task_id = "task_collection_unavailable"
    state = create_initial_state(_task(task_id=task_id))
    append_product(state, _unrepairable_product(task_id))
    append_evidence(state, _unrepairable_evidence(task_id))
    append_claim(state, _price_claim(task_id))

    qa_agent_node(state, now=NOW)
    collection_agent_node(state, now=NOW)

    repaired_evidence = next(
        evidence
        for evidence in state["evidences"]
        if evidence["metadata"].get("repaired_from_evidence_id") == "ev_unavailable_001"
    )
    repair_diff = state["metadata"]["collection_agent_repair"]["diffs"][0]

    assert repaired_evidence["access_time"] is None
    assert repaired_evidence["metadata"]["repair_status"] == "unavailable"
    assert repaired_evidence["metadata"]["fallback_value"] == "暂无可靠数据"
    assert repaired_evidence["metadata"]["unavailable_fields"] == ["source.access_time"]
    assert "暂无可靠数据" in repaired_evidence["content_summary"]
    assert repair_diff["status"] == "unavailable"
    assert repair_diff["after"]["fallback_value"] == "暂无可靠数据"


def _unrepairable_product(task_id: str) -> Product:
    return Product(
        product_id="prod_unavailable_001",
        task_id=task_id,
        sku_id="sku_unavailable",
        role="direct_competitor",
        name="Unrepairable demo competitor",
        brand="Demo Brand",
        category="smart_pet_hardware",
        subcategory="automatic_litter_box",
        product_url="https://example.com/unrepairable",
        evidence_ids=["ev_unavailable_001"],
        tags=["automatic_litter_box", "500-1000", "direct_competitor"],
        created_at=NOW,
    )


def _unrepairable_evidence(task_id: str) -> Evidence:
    return Evidence(
        evidence_id="ev_unavailable_001",
        task_id=task_id,
        product_id="prod_unavailable_001",
        source_type="douyin_sku_snapshot",
        source_url="https://example.com/unrepairable",
        screenshot_path="data/raw/unavailable/price.png",
        access_time=None,
        content_summary="商品页显示到手价 999 CNY，并用于价格带判断。",
        confidence_level="medium",
        limitations="Local snapshot intentionally lacks access time.",
        metadata={
            "sku_id": "sku_unavailable",
            "price": {"display_price_yuan": 999, "price_band": "500-1000"},
            "missing_fields": ["source.access_time"],
        },
    )


def _price_claim(task_id: str) -> Claim:
    return Claim(
        claim_id="claim_unavailable_price",
        task_id=task_id,
        claim_type="pricing_fact",
        content="商品页证据显示该竞品到手价约 999 CNY，位于 500-1000 价格带。",
        evidence_ids=["ev_unavailable_001"],
        confidence=0.78,
        is_inference=False,
        risk_flags=[],
        status="accepted",
        created_at=NOW,
    )


def _public_page_handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path.strip("/") or "target"
    html = f"""
    <html>
      <head>
        <title>Public Product {path}</title>
        <meta property="og:image" content="https://example.com/{path}.jpg" />
        <script type="application/ld+json">
        {{
          "@type": "Product",
          "name": "Public Product {path}",
          "description": "Visible public page selling point for automatic litter box",
          "image": "https://example.com/{path}.jpg",
          "offers": {{"price": "1599", "priceCurrency": "CNY"}}
        }}
        </script>
      </head>
      <body>selling point: quiet cleaning; spec: 65L; price: CNY 1599</body>
    </html>
    """
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8"},
        text=html,
    )
