from datetime import UTC, datetime
from pathlib import Path

from app.graph import (
    TaskGraphState,
    append_evidence,
    append_product,
    append_review_insight,
    append_run_log,
    append_tool_call_log,
)
from app.schemas import (
    AgentMessageStatus,
    AgentMessageType,
    AgentName,
    AgentRunLog,
    ConfidenceLevel,
    DataSourceMode,
    Evidence,
    Product,
    ToolCallLog,
)
from app.schemas.common import EvidenceSourceType, JsonObject, ToolCallStatus
from app.services.public_page_enrichment import (
    build_public_page_evidence,
    enrichment_result_payload,
)
from app.services.public_page_fetcher import (
    PublicPageFetcher,
    PublicPageFetchError,
    fetch_snapshot_payload,
    public_page_fetch_error_payload,
)
from app.services.public_page_parser import (
    PublicPageParseError,
    parse_public_page_snapshot,
    parsed_public_page_payload,
)
from app.services.public_page_policy import (
    DEFAULT_MAX_PUBLIC_PAGES_PER_TASK,
    PublicPageUrlCandidate,
    evaluate_public_page_candidates,
    policy_decisions_summary,
)
from app.services.snapshot_loader import (
    DEFAULT_SNAPSHOT_PATH,
    SnapshotLoaderError,
    load_demo_snapshot,
)

UNAVAILABLE_DATA_TEXT = "暂无可靠数据"
REPAIRABLE_SOURCE_FIELDS = {
    "source.access_time": "access_time",
    "source.screenshot_path": "screenshot_path",
}
ISSUE_TO_MISSING_FIELD = {
    "TIMELY_EVIDENCE_MISSING_ACCESS_TIME": "source.access_time",
    "CRITICAL_EVIDENCE_MISSING_SCREENSHOT": "source.screenshot_path",
}


def collection_agent_node(
    state: TaskGraphState,
    snapshot_path: Path | str | None = None,
    now: datetime | None = None,
    public_page_fetcher: PublicPageFetcher | None = None,
) -> TaskGraphState:
    started_at = now or datetime.now(UTC)
    task = state["task"]
    task_id = _require_task_id(task)
    run_id = _next_run_id(state, task_id)
    resolved_snapshot_path = (
        Path(snapshot_path) if snapshot_path is not None else DEFAULT_SNAPSHOT_PATH
    )
    revision_messages = _pending_collection_revision_messages(state)
    if revision_messages and state["evidences"]:
        return _repair_collection_from_revision_requests(
            state=state,
            task_id=task_id,
            run_id=run_id,
            snapshot_path=resolved_snapshot_path,
            revision_messages=revision_messages,
            started_at=started_at,
            now=now,
        )

    try:
        result = load_demo_snapshot(
            task_id=task_id,
            snapshot_path=resolved_snapshot_path,
            created_at=started_at,
            target_sku_id=_selected_target_sku_id(task),
            target_product_name=_unmatched_target_name(task),
            target_product_url=_unmatched_target_url(task),
        )
    except SnapshotLoaderError as exc:
        ended_at = now or datetime.now(UTC)
        _record_collection_failure(
            state=state,
            task_id=task_id,
            run_id=run_id,
            snapshot_path=resolved_snapshot_path,
            started_at=started_at,
            ended_at=ended_at,
            error=exc,
        )
        raise

    for product in result.products:
        append_product(state, product)
    for evidence in result.evidences:
        append_evidence(state, evidence)
    for review_insight in result.review_insights:
        append_review_insight(state, review_insight)

    research_evidence = _research_text_to_evidence(task, task_id, started_at)
    if research_evidence is not None:
        append_evidence(state, research_evidence)

    public_page_summary = _maybe_enhance_known_public_pages(
        state=state,
        task_id=task_id,
        run_id=run_id,
        started_at=started_at,
        now=now,
        public_page_fetcher=public_page_fetcher,
    )

    ended_at = now or datetime.now(UTC)
    missing_fields = _missing_evidence_fields(result.evidences)
    _record_collection_success(
        state=state,
        task_id=task_id,
        run_id=run_id,
        snapshot_path=resolved_snapshot_path,
        started_at=started_at,
        ended_at=ended_at,
        product_count=len(result.products),
        evidence_count=len(result.evidences) + int(research_evidence is not None),
        review_insight_count=len(result.review_insights),
        missing_fields=missing_fields,
        research_text_loaded=research_evidence is not None,
    )
    state["metadata"]["collection_agent"] = {
        "status": "succeeded",
        "snapshot_version": result.snapshot_version,
        "source_path": result.source_path,
        "default_target_sku_id": result.default_target_sku_id,
        "selected_target_sku_id": _selected_target_sku_id(task),
        "target_selection": _target_selection(task),
        "product_count": len(result.products),
        "evidence_count": len(result.evidences) + int(research_evidence is not None),
        "review_insight_count": len(result.review_insights),
        "missing_evidence_fields": missing_fields,
        "research_text_loaded": research_evidence is not None,
    }
    if public_page_summary is not None:
        state["metadata"]["collection_agent"]["public_page_enhancement"] = public_page_summary
        state["metadata"]["public_page_enhancement"] = public_page_summary
    return state


def _maybe_enhance_known_public_pages(
    *,
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    started_at: datetime,
    now: datetime | None,
    public_page_fetcher: PublicPageFetcher | None,
) -> JsonObject | None:
    if state["task"].get("data_source_mode") != DataSourceMode.SNAPSHOT_PLUS_LIVE.value:
        return None

    products = [Product.model_validate(item) for item in state["products"]]
    evidences = [Evidence.model_validate(item) for item in state["evidences"]]
    product_by_id = {product.product_id: product for product in products}
    existing_evidence_ids = {evidence.evidence_id for evidence in evidences}
    candidates = _known_public_page_candidates(state["task"], products)
    decisions = evaluate_public_page_candidates(
        candidates,
        max_pages=DEFAULT_MAX_PUBLIC_PAGES_PER_TASK,
    )
    policy_ended_at = now or datetime.now(UTC)
    _record_public_page_tool_call(
        state=state,
        task_id=task_id,
        run_id=run_id,
        tool_name="public_page_policy",
        started_at=started_at,
        ended_at=policy_ended_at,
        status=ToolCallStatus.SUCCEEDED,
        arguments_summary={
            "candidate_count": len(candidates),
            "max_pages": DEFAULT_MAX_PUBLIC_PAGES_PER_TASK,
            "decisions": policy_decisions_summary(decisions),
        },
    )

    fetcher = public_page_fetcher or PublicPageFetcher()
    summary: JsonObject = {
        "status": "completed",
        "stage": "stage_1_known_url",
        "enabled": True,
        "candidate_count": len(candidates),
        "allowed_count": sum(1 for decision in decisions if decision.allowed),
        "generated_evidence_ids": [],
        "failed_urls": [],
        "skipped_urls": [
            {
                "url": decision.url,
                "reason_code": decision.reason_code,
                "reason": decision.reason,
            }
            for decision in decisions
            if not decision.allowed
        ],
        "llm_used": False,
        "note": (
            "Known URL enhancement uses httpx plus deterministic parsers; "
            "no internet competitor discovery."
        ),
    }
    evidence_index = 1
    for decision in decisions:
        if not decision.allowed:
            continue
        product = product_by_id.get(decision.product_id or "")
        if product is None:
            summary["failed_urls"].append(
                {
                    "url": decision.url,
                    "reason_code": "product_not_found",
                    "reason": "Known URL candidate did not match a local product.",
                }
            )
            continue

        fetch_started_at = now or datetime.now(UTC)
        try:
            snapshot = fetcher.fetch(decision.url, access_time=fetch_started_at)
            snapshot.metadata.update(decision.metadata or {})
            fetch_ended_at = now or datetime.now(UTC)
            _record_public_page_tool_call(
                state=state,
                task_id=task_id,
                run_id=run_id,
                tool_name="public_page_fetcher",
                started_at=fetch_started_at,
                ended_at=fetch_ended_at,
                status=ToolCallStatus.SUCCEEDED,
                arguments_summary={
                    "url": decision.url,
                    "product_id": product.product_id,
                    "snapshot": fetch_snapshot_payload(snapshot),
                },
            )
        except PublicPageFetchError as exc:
            fetch_ended_at = now or datetime.now(UTC)
            error_payload = public_page_fetch_error_payload(exc)
            summary["failed_urls"].append(error_payload)
            _record_public_page_tool_call(
                state=state,
                task_id=task_id,
                run_id=run_id,
                tool_name="public_page_fetcher",
                started_at=fetch_started_at,
                ended_at=fetch_ended_at,
                status=ToolCallStatus.FAILED,
                arguments_summary={"url": decision.url, "product_id": product.product_id},
                error_message=f"{exc.code}: {exc.message}",
            )
            continue

        parse_started_at = now or datetime.now(UTC)
        try:
            parsed = parse_public_page_snapshot(snapshot)
            parse_ended_at = now or datetime.now(UTC)
            _record_public_page_tool_call(
                state=state,
                task_id=task_id,
                run_id=run_id,
                tool_name="public_page_parser",
                started_at=parse_started_at,
                ended_at=parse_ended_at,
                status=ToolCallStatus.SUCCEEDED,
                arguments_summary={
                    "url": decision.url,
                    "product_id": product.product_id,
                    "parsed": parsed_public_page_payload(parsed),
                },
            )
        except PublicPageParseError as exc:
            parse_ended_at = now or datetime.now(UTC)
            summary["failed_urls"].append(
                {
                    "url": decision.url,
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            )
            _record_public_page_tool_call(
                state=state,
                task_id=task_id,
                run_id=run_id,
                tool_name="public_page_parser",
                started_at=parse_started_at,
                ended_at=parse_ended_at,
                status=ToolCallStatus.FAILED,
                arguments_summary={"url": decision.url, "product_id": product.product_id},
                error_message=f"{exc.code}: {exc.message}",
            )
            continue

        enrichment_started_at = now or datetime.now(UTC)
        evidence, enrichment_result = build_public_page_evidence(
            task_id=task_id,
            product=product,
            parsed_page=parsed,
            existing_evidences=evidences,
            evidence_index=evidence_index,
        )
        enrichment_ended_at = now or datetime.now(UTC)
        tool_status = ToolCallStatus.SUCCEEDED if evidence is not None else ToolCallStatus.SKIPPED
        _record_public_page_tool_call(
            state=state,
            task_id=task_id,
            run_id=run_id,
            tool_name="public_page_enrichment",
            started_at=enrichment_started_at,
            ended_at=enrichment_ended_at,
            status=tool_status,
            arguments_summary={
                "url": decision.url,
                "product_id": product.product_id,
                "result": enrichment_result_payload(enrichment_result),
            },
        )
        if evidence is None:
            summary["skipped_urls"].append(
                {
                    "url": decision.url,
                    "reason_code": enrichment_result.fallback_reason or "no_evidence",
                    "reason": (
                        "No explicit public page fields were available for Evidence "
                        "generation."
                    ),
                }
            )
            continue

        while evidence.evidence_id in existing_evidence_ids:
            evidence_index += 1
            evidence = evidence.model_copy(
                update={
                    "evidence_id": f"ev_{product.product_id}_public_page_{evidence_index:03d}"
                }
            )
        append_evidence(state, evidence)
        existing_evidence_ids.add(evidence.evidence_id)
        evidences.append(evidence)
        _link_public_page_evidence_to_product(state, product.product_id, evidence.evidence_id)
        summary["generated_evidence_ids"].append(evidence.evidence_id)
        evidence_index += 1

    if not summary["generated_evidence_ids"] and summary["failed_urls"]:
        summary["status"] = "degraded_to_snapshot"
    elif not summary["generated_evidence_ids"]:
        summary["status"] = "no_public_evidence"
    return summary


def _known_public_page_candidates(
    task: JsonObject,
    products: list[Product],
) -> list[PublicPageUrlCandidate]:
    target_products = [product for product in products if product.role.value == "target"]
    competitor_products = [
        product for product in products if product.role.value != "target"
    ][: DEFAULT_MAX_PUBLIC_PAGES_PER_TASK]
    products_for_snapshot_urls = target_products + competitor_products
    candidates: list[PublicPageUrlCandidate] = []
    task_url = _non_empty_text(task.get("target_product_url"))
    target_product = target_products[0] if target_products else None
    if task_url is not None:
        candidates.append(
            PublicPageUrlCandidate(
                url=task_url,
                source="task.target_product_url",
                product_id=target_product.product_id if target_product else None,
                role=target_product.role.value if target_product else None,
                sku_id=target_product.sku_id if target_product else None,
            )
        )
    for product in products_for_snapshot_urls:
        if not product.product_url:
            continue
        candidates.append(
            PublicPageUrlCandidate(
                url=product.product_url,
                source="snapshot.source_url",
                product_id=product.product_id,
                role=product.role.value,
                sku_id=product.sku_id,
            )
        )
    return candidates


def _link_public_page_evidence_to_product(
    state: TaskGraphState,
    product_id: str,
    evidence_id: str,
) -> None:
    for product in state["products"]:
        if product.get("product_id") != product_id:
            continue
        evidence_ids = product.setdefault("evidence_ids", [])
        if isinstance(evidence_ids, list) and evidence_id not in evidence_ids:
            evidence_ids.append(evidence_id)
        return


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _record_public_page_tool_call(
    *,
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    tool_name: str,
    started_at: datetime,
    ended_at: datetime,
    status: ToolCallStatus,
    arguments_summary: JsonObject,
    error_message: str | None = None,
) -> None:
    append_tool_call_log(
        state,
        ToolCallLog(
            tool_call_id=f"{run_id}_tool_{tool_name}_{_tool_call_index(state, tool_name):03d}",
            task_id=task_id,
            run_id=run_id,
            tool_name=tool_name,
            arguments_summary=arguments_summary,
            status=status,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=0,
            error_message=error_message,
        ),
    )


def _tool_call_index(state: TaskGraphState, tool_name: str) -> int:
    return (
        sum(1 for log in state["tool_call_logs"] if log.get("tool_name") == tool_name)
        + 1
    )


def _repair_collection_from_revision_requests(
    *,
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    snapshot_path: Path,
    revision_messages: list[JsonObject],
    started_at: datetime,
    now: datetime | None,
) -> TaskGraphState:
    try:
        result = load_demo_snapshot(
            task_id=task_id,
            snapshot_path=snapshot_path,
            created_at=started_at,
        )
    except SnapshotLoaderError as exc:
        ended_at = now or datetime.now(UTC)
        _record_collection_failure(
            state=state,
            task_id=task_id,
            run_id=run_id,
            snapshot_path=snapshot_path,
            started_at=started_at,
            ended_at=ended_at,
            error=exc,
        )
        raise

    target_evidence_ids = _revision_target_evidence_ids(revision_messages)
    evidence_by_id = {
        evidence["evidence_id"]: Evidence.model_validate(evidence)
        for evidence in state["evidences"]
    }
    existing_evidence_ids = set(evidence_by_id)
    repair_diffs: list[JsonObject] = []
    new_evidence_ids: list[str] = []

    for target_evidence_id in target_evidence_ids:
        evidence = evidence_by_id.get(target_evidence_id)
        if evidence is None:
            continue
        missing_fields = _missing_fields_for_revision(
            evidence=evidence,
            target_evidence_id=target_evidence_id,
            revision_messages=revision_messages,
        )
        repair_payload = _matching_repair_payload(
            fixture=result.qa_revision_fixture,
            evidence=evidence,
            missing_fields=missing_fields,
        )
        repaired_evidence, diff = _build_repair_evidence(
            original=evidence,
            task_id=task_id,
            missing_fields=missing_fields,
            repair_payload=repair_payload,
            revision_messages=revision_messages,
            existing_evidence_ids=existing_evidence_ids,
        )
        append_evidence(state, repaired_evidence)
        existing_evidence_ids.add(repaired_evidence.evidence_id)
        new_evidence_ids.append(repaired_evidence.evidence_id)
        repair_diffs.append(diff)
        _link_repaired_evidence_to_product(state, repaired_evidence)

    _mark_revision_messages_processed(
        revision_messages=revision_messages,
        new_evidence_ids=new_evidence_ids,
        repair_diffs=repair_diffs,
    )

    ended_at = now or datetime.now(UTC)
    repaired_count = sum(1 for diff in repair_diffs if diff["status"] == "repaired")
    partial_count = sum(1 for diff in repair_diffs if diff["status"] == "partial")
    unavailable_count = sum(1 for diff in repair_diffs if diff["status"] == "unavailable")
    repair_summary = {
        "run_id": run_id,
        "status": "succeeded",
        "operation": "qa_revision_repair",
        "snapshot_version": result.snapshot_version,
        "source_path": result.source_path,
        "revision_message_ids": [
            message["message_id"] for message in revision_messages
        ],
        "target_evidence_ids": target_evidence_ids,
        "new_evidence_ids": new_evidence_ids,
        "repaired_count": repaired_count,
        "partial_count": partial_count,
        "unavailable_count": unavailable_count,
        "diffs": repair_diffs,
    }
    collection_metadata = state["metadata"].get("collection_agent", {})
    if not isinstance(collection_metadata, dict):
        collection_metadata = {}
    repair_runs = list(collection_metadata.get("repair_runs", []))
    repair_runs.append(repair_summary)
    state["metadata"]["collection_agent"] = {
        **collection_metadata,
        "status": "succeeded",
        "last_operation": "qa_revision_repair",
        "repair_runs": repair_runs,
    }
    state["metadata"]["collection_agent_repair"] = repair_summary

    _record_collection_repair_success(
        state=state,
        task_id=task_id,
        run_id=run_id,
        snapshot_path=snapshot_path,
        started_at=started_at,
        ended_at=ended_at,
        revision_message_ids=repair_summary["revision_message_ids"],
        target_evidence_ids=target_evidence_ids,
        repaired_count=repaired_count,
        partial_count=partial_count,
        unavailable_count=unavailable_count,
        diff_count=len(repair_diffs),
    )
    return state


def _record_collection_repair_success(
    *,
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    snapshot_path: Path,
    started_at: datetime,
    ended_at: datetime,
    revision_message_ids: list[str],
    target_evidence_ids: list[str],
    repaired_count: int,
    partial_count: int,
    unavailable_count: int,
    diff_count: int,
) -> None:
    append_tool_call_log(
        state,
        ToolCallLog(
            tool_call_id=f"{run_id}_tool_snapshot_repair_fixture",
            task_id=task_id,
            run_id=run_id,
            tool_name="snapshot_repair_fixture",
            arguments_summary={
                "snapshot_path": str(snapshot_path),
                "revision_message_ids": revision_message_ids,
                "target_evidence_ids": target_evidence_ids,
            },
            status=ToolCallStatus.SUCCEEDED,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=0,
            error_message=None,
        ),
    )
    append_run_log(
        state,
        AgentRunLog(
            run_id=run_id,
            task_id=task_id,
            agent_name=AgentName.COLLECTION,
            status="succeeded",
            started_at=started_at,
            ended_at=ended_at,
            input_summary="Repair evidence requested by QA revision messages.",
            output_summary=(
                f"Processed {len(target_evidence_ids)} Collection revision targets; "
                f"repaired={repaired_count}; partial={partial_count}; "
                f"unavailable={unavailable_count}; diffs={diff_count}."
            ),
            error_message=None,
        ),
    )


def _record_collection_success(
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    snapshot_path: Path,
    started_at: datetime,
    ended_at: datetime,
    product_count: int,
    evidence_count: int,
    review_insight_count: int,
    missing_fields: list[JsonObject],
    research_text_loaded: bool,
) -> None:
    append_tool_call_log(
        state,
        ToolCallLog(
            tool_call_id=f"{run_id}_tool_snapshot_loader",
            task_id=task_id,
            run_id=run_id,
            tool_name="snapshot_loader",
            arguments_summary={
                "snapshot_path": str(snapshot_path),
                "data_source_mode": state["task"].get("data_source_mode"),
            },
            status=ToolCallStatus.SUCCEEDED,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=0,
            error_message=None,
        ),
    )
    append_run_log(
        state,
        AgentRunLog(
            run_id=run_id,
            task_id=task_id,
            agent_name="collection_agent",
            status="succeeded",
            started_at=started_at,
            ended_at=ended_at,
            input_summary="Load local demo SKU snapshot and optional user research text.",
            output_summary=(
                f"Collected {product_count} products, {evidence_count} evidences, "
                f"{review_insight_count} review insights; "
                f"missing_evidence_fields={len(missing_fields)}; "
                f"research_text_loaded={research_text_loaded}."
            ),
            error_message=None,
        ),
    )


def _record_collection_failure(
    state: TaskGraphState,
    task_id: str,
    run_id: str,
    snapshot_path: Path,
    started_at: datetime,
    ended_at: datetime,
    error: SnapshotLoaderError,
) -> None:
    append_tool_call_log(
        state,
        ToolCallLog(
            tool_call_id=f"{run_id}_tool_snapshot_loader",
            task_id=task_id,
            run_id=run_id,
            tool_name="snapshot_loader",
            arguments_summary={"snapshot_path": str(snapshot_path)},
            status=ToolCallStatus.FAILED,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=0,
            error_message=f"{error.code}: {error.message}",
        ),
    )
    append_run_log(
        state,
        AgentRunLog(
            run_id=run_id,
            task_id=task_id,
            agent_name="collection_agent",
            status="failed",
            started_at=started_at,
            ended_at=ended_at,
            input_summary="Load local demo SKU snapshot and optional user research text.",
            output_summary=None,
            error_message=f"{error.code}: {error.message}",
        ),
    )
    state["metadata"]["collection_agent"] = {
        "status": "failed",
        "error_code": error.code,
        "error_message": error.message,
        "details": error.details,
    }


def _research_text_to_evidence(
    task: JsonObject,
    task_id: str,
    created_at: datetime,
) -> Evidence | None:
    research_text = task.get("research_text")
    if not isinstance(research_text, str) or not research_text.strip():
        return None

    return Evidence(
        evidence_id=f"ev_{task_id}_user_research",
        task_id=task_id,
        product_id=None,
        source_type=EvidenceSourceType.USER_RESEARCH,
        source_url=None,
        screenshot_path=None,
        access_time=created_at,
        content_summary=(
            f"User research text was provided with the task; "
            f"character_count={len(research_text.strip())}."
        ),
        confidence_level=ConfidenceLevel.LOW,
        limitations=(
            "User research text is task-provided input and has not been independently "
            "clustered."
        ),
        metadata={
            "source": "task.research_text",
            "character_count": len(research_text.strip()),
            "raw_text_stored_in_task": True,
        },
    )


def _missing_evidence_fields(evidences: list[Evidence]) -> list[JsonObject]:
    missing_fields = []
    for evidence in evidences:
        fields = evidence.metadata.get("missing_fields", [])
        if fields:
            missing_fields.append(
                {
                    "evidence_id": evidence.evidence_id,
                    "product_id": evidence.product_id,
                    "missing_fields": fields,
                }
            )
    return missing_fields


def _next_run_id(state: TaskGraphState, task_id: str) -> str:
    collection_run_count = sum(
        1 for run_log in state["run_logs"] if run_log.get("agent_name") == "collection_agent"
    )
    return f"run_{task_id}_collection_{collection_run_count + 1:03d}"


def _require_task_id(task: JsonObject) -> str:
    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("Collection Agent requires a non-empty task_id.")
    return task_id


def _selected_target_sku_id(task: JsonObject) -> str | None:
    metadata = task.get("metadata", {})
    if not isinstance(metadata, dict):
        return None
    sku_id = metadata.get("selected_target_sku_id")
    return sku_id if isinstance(sku_id, str) and sku_id.strip() else None


def _target_selection(task: JsonObject) -> str:
    metadata = task.get("metadata", {})
    if not isinstance(metadata, dict):
        return "unknown"
    selection = metadata.get("target_selection")
    return selection if isinstance(selection, str) and selection.strip() else "unknown"


def _unmatched_target_name(task: JsonObject) -> str | None:
    if _target_selection(task) != "user_input_unmatched":
        return None
    value = task.get("target_product_name")
    return value if isinstance(value, str) and value.strip() else None


def _unmatched_target_url(task: JsonObject) -> str | None:
    if _target_selection(task) != "user_input_unmatched":
        return None
    value = task.get("target_product_url")
    return value if isinstance(value, str) and value.strip() else None


def _pending_collection_revision_messages(state: TaskGraphState) -> list[JsonObject]:
    return [
        message
        for message in state["agent_messages"]
        if message.get("from_agent") == AgentName.QA.value
        and message.get("to_agent") == AgentName.COLLECTION.value
        and message.get("message_type") == AgentMessageType.REVISION_REQUEST.value
        and message.get("status") == AgentMessageStatus.REQUIRES_REVISION.value
    ]


def _revision_target_evidence_ids(revision_messages: list[JsonObject]) -> list[str]:
    evidence_ids: list[str] = []
    for message in revision_messages:
        evidence_ids.extend(_string_items(message.get("evidence_ids")))
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            continue
        for target in payload.get("targets", []):
            if not isinstance(target, dict):
                continue
            evidence_ids.extend(_string_items(target.get("evidence_ids")))
            if target.get("target_type") == "evidence":
                target_id = target.get("target_id")
                if isinstance(target_id, str):
                    evidence_ids.append(target_id)
    return _dedupe(evidence_ids)


def _missing_fields_for_revision(
    *,
    evidence: Evidence,
    target_evidence_id: str,
    revision_messages: list[JsonObject],
) -> list[str]:
    missing_fields = _string_items(evidence.metadata.get("missing_fields"))
    for message in revision_messages:
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            continue
        payload_issue_codes = _string_items(payload.get("issue_codes"))
        issue_codes: list[str] = []
        targets = payload.get("targets", [])
        for target in targets:
            if not isinstance(target, dict):
                continue
            target_ids = _string_items(target.get("evidence_ids"))
            if target.get("target_type") == "evidence":
                target_id = target.get("target_id")
                if isinstance(target_id, str):
                    target_ids.append(target_id)
            if target_evidence_id not in target_ids:
                continue
            issue_codes.extend(_string_items([target.get("issue_code")]))
        if not targets and target_evidence_id in _string_items(message.get("evidence_ids")):
            issue_codes.extend(payload_issue_codes)
        for issue_code in issue_codes:
            missing_field = ISSUE_TO_MISSING_FIELD.get(issue_code)
            if missing_field:
                missing_fields.append(missing_field)
    return _dedupe(missing_fields)


def _matching_repair_payload(
    *,
    fixture: JsonObject,
    evidence: Evidence,
    missing_fields: list[str],
) -> JsonObject | None:
    if not fixture:
        return None
    if fixture.get("sku_id") != evidence.metadata.get("sku_id"):
        return None
    fixture_fields = _string_items(fixture.get("missing_fields"))
    if fixture_fields and not set(fixture_fields).intersection(missing_fields):
        return None
    repair_evidence = fixture.get("repair_evidence")
    if not isinstance(repair_evidence, dict):
        return None
    return repair_evidence


def _build_repair_evidence(
    *,
    original: Evidence,
    task_id: str,
    missing_fields: list[str],
    repair_payload: JsonObject | None,
    revision_messages: list[JsonObject],
    existing_evidence_ids: set[str],
) -> tuple[Evidence, JsonObject]:
    repaired_values: JsonObject = {}
    repaired_fields: list[str] = []
    unavailable_fields: list[str] = []
    for field_name in missing_fields:
        evidence_field = REPAIRABLE_SOURCE_FIELDS.get(field_name)
        if evidence_field is None:
            unavailable_fields.append(field_name)
            continue
        repair_value = repair_payload.get(evidence_field) if repair_payload else None
        if repair_value:
            repaired_values[evidence_field] = repair_value
            repaired_fields.append(field_name)
        else:
            unavailable_fields.append(field_name)

    remaining_missing_fields = [
        field_name
        for field_name in _string_items(original.metadata.get("missing_fields"))
        if field_name not in repaired_fields
    ]
    metadata = dict(original.metadata)
    metadata["missing_fields"] = remaining_missing_fields
    metadata["repaired_from_evidence_id"] = original.evidence_id
    metadata["repair_revision_message_ids"] = [
        message["message_id"] for message in revision_messages
    ]
    metadata["repaired_fields"] = repaired_fields
    metadata["unavailable_fields"] = unavailable_fields
    metadata["repair_status"] = _repair_status(repaired_fields, unavailable_fields)
    if repaired_fields:
        metadata["repair_source"] = "qa_revision_fixture"
        metadata["repair_note"] = str(
            repair_payload.get("source_note", "本地 Demo 修复夹具补齐。")
            if repair_payload
            else "本地 Demo 修复夹具补齐。"
        )
    if unavailable_fields:
        metadata["fallback_value"] = UNAVAILABLE_DATA_TEXT
        metadata["repair_note"] = (
            "本地 Demo 快照未提供可补齐来源，按合规要求标记为暂无可靠数据。"
        )

    repaired_evidence = Evidence(
        evidence_id=_next_repair_evidence_id(original.evidence_id, existing_evidence_ids),
        task_id=task_id,
        product_id=original.product_id,
        source_type=original.source_type,
        source_url=original.source_url,
        screenshot_path=repaired_values.get("screenshot_path", original.screenshot_path),
        access_time=repaired_values.get("access_time", original.access_time),
        content_summary=_repair_content_summary(
            original=original,
            repaired_fields=repaired_fields,
            unavailable_fields=unavailable_fields,
        ),
        confidence_level=_repair_confidence(repaired_fields, unavailable_fields),
        limitations=_repair_limitations(
            original=original,
            repaired_fields=repaired_fields,
            unavailable_fields=unavailable_fields,
        ),
        metadata=metadata,
    )
    diff = {
        "target_evidence_id": original.evidence_id,
        "new_evidence_id": repaired_evidence.evidence_id,
        "status": metadata["repair_status"],
        "revision_message_ids": [
            message["message_id"] for message in revision_messages
        ],
        "before": _evidence_diff_snapshot(original),
        "after": _evidence_diff_snapshot(repaired_evidence),
        "repaired_fields": repaired_fields,
        "unavailable_fields": unavailable_fields,
    }
    return repaired_evidence, diff


def _repair_status(repaired_fields: list[str], unavailable_fields: list[str]) -> str:
    if repaired_fields and unavailable_fields:
        return "partial"
    if repaired_fields:
        return "repaired"
    return "unavailable"


def _repair_confidence(
    repaired_fields: list[str],
    unavailable_fields: list[str],
) -> ConfidenceLevel:
    if repaired_fields and not unavailable_fields:
        return ConfidenceLevel.MEDIUM
    if repaired_fields:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.UNKNOWN


def _repair_content_summary(
    *,
    original: Evidence,
    repaired_fields: list[str],
    unavailable_fields: list[str],
) -> str:
    summary = original.content_summary
    if repaired_fields:
        summary += f"；QA 打回后补齐字段：{'、'.join(repaired_fields)}。"
    if unavailable_fields:
        summary += (
            f"；QA 打回后仍无法补齐字段 {'、'.join(unavailable_fields)}，"
            f"标记为{UNAVAILABLE_DATA_TEXT}。"
        )
    return summary


def _repair_limitations(
    *,
    original: Evidence,
    repaired_fields: list[str],
    unavailable_fields: list[str],
) -> str:
    limitations = original.limitations
    if repaired_fields:
        limitations += "；QA 打回后由本地修复证据补齐，仍不代表实时页面。"
    if unavailable_fields:
        limitations += f"；QA 打回后本地快照无法补齐，相关字段为{UNAVAILABLE_DATA_TEXT}。"
    return limitations


def _evidence_diff_snapshot(evidence: Evidence) -> JsonObject:
    return {
        "evidence_id": evidence.evidence_id,
        "product_id": evidence.product_id,
        "access_time": evidence.access_time.isoformat() if evidence.access_time else None,
        "screenshot_path": evidence.screenshot_path,
        "confidence_level": evidence.confidence_level.value,
        "missing_fields": _string_items(evidence.metadata.get("missing_fields")),
        "repair_status": evidence.metadata.get("repair_status"),
        "fallback_value": evidence.metadata.get("fallback_value"),
    }


def _link_repaired_evidence_to_product(
    state: TaskGraphState,
    repaired_evidence: Evidence,
) -> None:
    if repaired_evidence.product_id is None:
        return
    for product in state["products"]:
        if product.get("product_id") != repaired_evidence.product_id:
            continue
        evidence_ids = product.setdefault("evidence_ids", [])
        if isinstance(evidence_ids, list) and repaired_evidence.evidence_id not in evidence_ids:
            evidence_ids.append(repaired_evidence.evidence_id)
        return


def _mark_revision_messages_processed(
    *,
    revision_messages: list[JsonObject],
    new_evidence_ids: list[str],
    repair_diffs: list[JsonObject],
) -> None:
    for message in revision_messages:
        message["status"] = AgentMessageStatus.PROCESSED.value
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            payload = {}
        payload["collection_repair"] = {
            "status": "processed",
            "new_evidence_ids": new_evidence_ids,
            "diff_count": len(repair_diffs),
        }
        message["payload"] = payload


def _next_repair_evidence_id(
    original_evidence_id: str,
    existing_evidence_ids: set[str],
) -> str:
    base_id = f"{original_evidence_id}_repair"
    index = 1
    candidate = f"{base_id}_{index:03d}"
    while candidate in existing_evidence_ids:
        index += 1
        candidate = f"{base_id}_{index:03d}"
    return candidate


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list | tuple | set):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _dedupe(items: list[str]) -> list[str]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped
