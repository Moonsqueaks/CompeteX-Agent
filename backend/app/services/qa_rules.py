import re
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from app.schemas import (
    AgentName,
    Claim,
    CompetitionEdge,
    Evidence,
    ReviewSeverity,
    ReviewTargetType,
    ReviewTask,
    RiskFlag,
)

ClaimInput = Claim | Mapping[str, Any]
EvidenceInput = Evidence | Mapping[str, Any]
CompetitionEdgeInput = CompetitionEdge | Mapping[str, Any]

TIME_SENSITIVE_TERMS = (
    "价格",
    "价位",
    "到手价",
    "券后",
    "评分",
    "评价数",
    "评论数",
    "销量",
    "排名",
    "榜单",
    "price",
    "rating",
    "review",
    "sales",
    "rank",
)
SCREENSHOT_REQUIRED_TERMS = (
    "价格",
    "价位",
    "到手价",
    "券后",
    "认证",
    "证书",
    "安全认证",
    "price",
    "certification",
)
INFERENCE_TERMS = (
    "推断",
    "可能",
    "倾向",
    "判断",
    "规则评分",
    "竞争关系",
    "替代",
    "优势",
    "短板",
    "infer",
    "likely",
    "may ",
)
SENSITIVE_ABSOLUTE_TERMS = (
    "绝对安全",
    "完全安全",
    "100%安全",
    "保证安全",
    "无任何风险",
    "零风险",
    "安全无忧",
    "永不夹猫",
    "防夹绝对可靠",
    "符合所有认证",
    "通过所有认证",
    "认证齐全",
    "治愈",
    "治疗",
    "医疗级",
)
COMMENT_TERMS = ("评论", "评价", "用户反馈", "review")
COMMENT_OVERGENERALIZATION_TERMS = (
    "普遍",
    "都认为",
    "所有",
    "一致认为",
    "大量用户",
    "全部",
    "广泛",
)


def run_qa_rules(
    *,
    task_id: str,
    claims: Sequence[ClaimInput],
    evidences: Sequence[EvidenceInput],
    competition_edges: Sequence[CompetitionEdgeInput] | None = None,
    now: datetime | None = None,
) -> list[ReviewTask]:
    """Run deterministic MVP QA checks and return ReviewTask artifacts only."""

    checked_at = now or datetime.now(UTC)
    claim_items = [_validate_claim(item) for item in claims]
    evidence_items = [_validate_evidence(item) for item in evidences]
    edge_items = [_validate_edge(item) for item in competition_edges or ()]
    evidence_by_id = {evidence.evidence_id: evidence for evidence in evidence_items}
    claim_by_id = {claim.claim_id: claim for claim in claim_items}
    tasks: list[ReviewTask] = []
    seen: set[ReviewTaskKey] = set()

    for claim in claim_items:
        linked_evidences = _linked_evidences(claim, evidence_by_id)
        _check_claim_evidence(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            evidence_by_id=evidence_by_id,
            created_at=checked_at,
        )
        _check_access_time(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            linked_evidences=linked_evidences,
            created_at=checked_at,
        )
        _check_screenshot_path(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            linked_evidences=linked_evidences,
            created_at=checked_at,
        )
        _check_inference_marking(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            created_at=checked_at,
        )
        _check_sensitive_claim(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            created_at=checked_at,
        )
        _check_review_overgeneralization(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            linked_evidences=linked_evidences,
            created_at=checked_at,
        )
        _check_claim_conflict_flag(
            tasks,
            seen,
            task_id=task_id,
            claim=claim,
            created_at=checked_at,
        )

    _check_competition_edges(
        tasks,
        seen,
        task_id=task_id,
        edges=edge_items,
        claim_by_id=claim_by_id,
        created_at=checked_at,
    )
    return tasks


ReviewTaskKey = tuple[str, str, str, tuple[str, ...], tuple[str, ...]]


def _check_claim_evidence(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    evidence_by_id: Mapping[str, Evidence],
    created_at: datetime,
) -> None:
    if not claim.evidence_ids:
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="CLAIM_MISSING_EVIDENCE",
            check_name="evidence_completeness",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.CLAIM,
            target_id=claim.claim_id,
            target_agent=AgentName.ANALYSIS,
            message="核心 Claim 缺少 evidence_ids，不能作为强结论进入报告。",
            required_action="为该 Claim 绑定可靠 Evidence，或将结论保持为待复核风险项。",
            related_claim_ids=[claim.claim_id],
            evidence_ids=[],
            created_at=created_at,
        )
        return

    unknown_ids = [
        evidence_id for evidence_id in claim.evidence_ids if evidence_id not in evidence_by_id
    ]
    if unknown_ids:
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="CLAIM_EVIDENCE_NOT_FOUND",
            check_name="evidence_completeness",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.CLAIM,
            target_id=claim.claim_id,
            target_agent=AgentName.ANALYSIS,
            message="Claim 引用了当前状态中不存在的 Evidence ID。",
            required_action="修正 Claim 的 evidence_ids，或由 Collection 补齐对应 Evidence。",
            related_claim_ids=[claim.claim_id],
            evidence_ids=unknown_ids,
            created_at=created_at,
        )


def _check_access_time(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    linked_evidences: Sequence[Evidence],
    created_at: datetime,
) -> None:
    if not _claim_needs_time_sensitive_evidence(claim, linked_evidences):
        return

    for evidence in linked_evidences:
        if evidence.access_time is not None or not _is_time_sensitive_evidence(evidence, claim):
            continue
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="TIMELY_EVIDENCE_MISSING_ACCESS_TIME",
            check_name="time_sensitive_evidence_access_time",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.EVIDENCE,
            target_id=evidence.evidence_id,
            target_agent=AgentName.COLLECTION,
            message="价格、评分、评价数、销量或排名类证据缺少访问时间。",
            required_action="补齐 Evidence.access_time；如无法补齐，将相关结论降级为暂无可靠数据。",
            related_claim_ids=[claim.claim_id],
            evidence_ids=[evidence.evidence_id],
            created_at=created_at,
        )


def _check_screenshot_path(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    linked_evidences: Sequence[Evidence],
    created_at: datetime,
) -> None:
    for evidence in linked_evidences:
        if evidence.screenshot_path or not _requires_screenshot(evidence, claim):
            continue
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="CRITICAL_EVIDENCE_MISSING_SCREENSHOT",
            check_name="critical_evidence_screenshot",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.EVIDENCE,
            target_id=evidence.evidence_id,
            target_agent=AgentName.COLLECTION,
            message="关键价格或认证信息缺少截图路径。",
            required_action="补齐 Evidence.screenshot_path；如无法补齐，将该信息标记为待复核。",
            related_claim_ids=[claim.claim_id],
            evidence_ids=[evidence.evidence_id],
            created_at=created_at,
        )


def _check_inference_marking(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    created_at: datetime,
) -> None:
    if claim.is_inference or not _contains_any(claim.content, INFERENCE_TERMS):
        return
    _add_review_task(
        tasks,
        seen,
        task_id=task_id,
        issue_code="INFERENCE_NOT_MARKED",
        check_name="inference_marking",
        severity=ReviewSeverity.ERROR,
        target_type=ReviewTargetType.CLAIM,
        target_id=claim.claim_id,
        target_agent=AgentName.ANALYSIS,
        message="Claim 内容包含推断或竞争判断，但 is_inference 未标记为 true。",
        required_action="将该 Claim 标记为推断，或改写为只陈述 Evidence 可直接支持的事实。",
        related_claim_ids=[claim.claim_id],
        evidence_ids=claim.evidence_ids,
        created_at=created_at,
    )


def _check_sensitive_claim(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    created_at: datetime,
) -> None:
    if RiskFlag.SENSITIVE_CLAIM not in claim.risk_flags and not _contains_any(
        claim.content,
        SENSITIVE_ABSOLUTE_TERMS,
    ):
        return
    _add_review_task(
        tasks,
        seen,
        task_id=task_id,
        issue_code="SENSITIVE_CLAIM_NEEDS_CONSERVATIVE_LANGUAGE",
        check_name="sensitive_claim_language",
        severity=ReviewSeverity.WARNING,
        target_type=ReviewTargetType.CLAIM,
        target_id=claim.claim_id,
        target_agent=AgentName.ANALYSIS,
        message="宠物安全、电器安全或医疗相关表达需要保持保守，避免绝对化。",
        required_action="改写为基于证据的保守表述，并保留来源局限性。",
        related_claim_ids=[claim.claim_id],
        evidence_ids=claim.evidence_ids,
        created_at=created_at,
    )


def _check_review_overgeneralization(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    linked_evidences: Sequence[Evidence],
    created_at: datetime,
) -> None:
    if RiskFlag.SINGLE_REVIEW_OVERGENERALIZED in claim.risk_flags:
        review_evidence_ids = [evidence.evidence_id for evidence in linked_evidences]
    elif not (
        _contains_any(claim.content, COMMENT_TERMS)
        and _contains_any(claim.content, COMMENT_OVERGENERALIZATION_TERMS)
    ):
        return
    else:
        review_evidence_ids = [
            evidence.evidence_id
            for evidence in linked_evidences
            if _review_sample_count(evidence) <= 1
        ]

    if not review_evidence_ids:
        return
    _add_review_task(
        tasks,
        seen,
        task_id=task_id,
        issue_code="SINGLE_REVIEW_OVERGENERALIZED",
        check_name="review_cluster_overgeneralization",
        severity=ReviewSeverity.WARNING,
        target_type=ReviewTargetType.CLAIM,
        target_id=claim.claim_id,
        target_agent=AgentName.ANALYSIS,
        message="Claim 将单条或样本过少的评论概括为普遍用户结论。",
        required_action="补充评论聚类证据，或将结论改为单条反馈方向参考。",
        related_claim_ids=[claim.claim_id],
        evidence_ids=review_evidence_ids,
        created_at=created_at,
    )


def _check_claim_conflict_flag(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    claim: Claim,
    created_at: datetime,
) -> None:
    if RiskFlag.CONFLICTING_ANALYSIS not in claim.risk_flags:
        return
    _add_review_task(
        tasks,
        seen,
        task_id=task_id,
        issue_code="CLAIM_CONFLICTING_ANALYSIS",
        check_name="analysis_consistency",
        severity=ReviewSeverity.ERROR,
        target_type=ReviewTargetType.CLAIM,
        target_id=claim.claim_id,
        target_agent=AgentName.ANALYSIS,
        message="Claim 已标记存在前后矛盾，需要重分析。",
        required_action="复核同一产品的价格带、人群、卖点或竞争关系是否互相冲突。",
        related_claim_ids=[claim.claim_id],
        evidence_ids=claim.evidence_ids,
        created_at=created_at,
    )


def _check_competition_edges(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    edges: Sequence[CompetitionEdge],
    claim_by_id: Mapping[str, Claim],
    created_at: datetime,
) -> None:
    edges_by_slice: dict[tuple[str, str, str, str, str], CompetitionEdge] = {}
    for edge in edges:
        _check_edge_claims(
            tasks,
            seen,
            task_id=task_id,
            edge=edge,
            claim_by_id=claim_by_id,
            created_at=created_at,
        )
        _check_edge_risk_flags(
            tasks,
            seen,
            task_id=task_id,
            edge=edge,
            created_at=created_at,
        )

        edge_key = (
            edge.target_product_id,
            edge.competitor_product_id,
            edge.slice.price_band,
            edge.slice.persona,
            edge.slice.scenario,
        )
        previous = edges_by_slice.get(edge_key)
        if previous is not None and previous.competition_type != edge.competition_type:
            _add_review_task(
                tasks,
                seen,
                task_id=task_id,
                issue_code="EDGE_CONFLICTING_COMPETITION_TYPE",
                check_name="analysis_consistency",
                severity=ReviewSeverity.ERROR,
                target_type=ReviewTargetType.COMPETITION_EDGE,
                target_id=edge.edge_id,
                target_agent=AgentName.ANALYSIS,
                message="同一目标、竞品和切片下出现互相冲突的竞争关系类型。",
                required_action="合并或重算该切片下的 CompetitionEdge，确保关系类型一致。",
                related_claim_ids=edge.claim_ids,
                evidence_ids=[],
                created_at=created_at,
            )
        edges_by_slice.setdefault(edge_key, edge)


def _check_edge_claims(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    edge: CompetitionEdge,
    claim_by_id: Mapping[str, Claim],
    created_at: datetime,
) -> None:
    if not edge.claim_ids:
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="EDGE_MISSING_CLAIM",
            check_name="edge_claim_binding",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.COMPETITION_EDGE,
            target_id=edge.edge_id,
            target_agent=AgentName.ANALYSIS,
            message="CompetitionEdge 缺少 claim_ids，无法追溯竞争判断。",
            required_action="为该边绑定至少一个 Claim，或移除该边。",
            related_claim_ids=[],
            evidence_ids=[],
            created_at=created_at,
        )
        return

    unknown_claim_ids = [claim_id for claim_id in edge.claim_ids if claim_id not in claim_by_id]
    if unknown_claim_ids:
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="EDGE_CLAIM_NOT_FOUND",
            check_name="edge_claim_binding",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.COMPETITION_EDGE,
            target_id=edge.edge_id,
            target_agent=AgentName.ANALYSIS,
            message="CompetitionEdge 引用了当前状态中不存在的 Claim ID。",
            required_action="修正 edge.claim_ids，确保边可以追溯到真实 Claim。",
            related_claim_ids=unknown_claim_ids,
            evidence_ids=[],
            created_at=created_at,
        )


def _check_edge_risk_flags(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    edge: CompetitionEdge,
    created_at: datetime,
) -> None:
    if RiskFlag.MISSING_EVIDENCE in edge.risk_flags:
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="EDGE_MISSING_EVIDENCE",
            check_name="edge_risk_flags",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.COMPETITION_EDGE,
            target_id=edge.edge_id,
            target_agent=AgentName.ANALYSIS,
            message="CompetitionEdge 已标记缺少证据，不能作为无风险边展示。",
            required_action="补齐边关联 Claim 的 Evidence，或保留风险状态等待人工复核。",
            related_claim_ids=edge.claim_ids,
            evidence_ids=[],
            created_at=created_at,
        )
    if (
        RiskFlag.UNRELIABLE_DATA in edge.risk_flags
        or edge.score_breakdown.evidence_confidence < 0.45
    ):
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="EDGE_UNRELIABLE_DATA",
            check_name="edge_risk_flags",
            severity=ReviewSeverity.WARNING,
            target_type=ReviewTargetType.COMPETITION_EDGE,
            target_id=edge.edge_id,
            target_agent=AgentName.ANALYSIS,
            message="CompetitionEdge 的证据置信度偏低。",
            required_action="补充更完整证据，或在前端和报告中展示低置信风险。",
            related_claim_ids=edge.claim_ids,
            evidence_ids=[],
            created_at=created_at,
        )
    if RiskFlag.CONFLICTING_ANALYSIS in edge.risk_flags:
        _add_review_task(
            tasks,
            seen,
            task_id=task_id,
            issue_code="EDGE_CONFLICTING_ANALYSIS",
            check_name="analysis_consistency",
            severity=ReviewSeverity.ERROR,
            target_type=ReviewTargetType.COMPETITION_EDGE,
            target_id=edge.edge_id,
            target_agent=AgentName.ANALYSIS,
            message="CompetitionEdge 已标记存在分析矛盾，需要重算。",
            required_action="复核同一切片下的竞争类型、评分和 Claim 是否一致。",
            related_claim_ids=edge.claim_ids,
            evidence_ids=[],
            created_at=created_at,
        )


def _add_review_task(
    tasks: list[ReviewTask],
    seen: set[ReviewTaskKey],
    *,
    task_id: str,
    issue_code: str,
    check_name: str,
    severity: ReviewSeverity,
    target_type: ReviewTargetType,
    target_id: str,
    target_agent: AgentName,
    message: str,
    required_action: str,
    related_claim_ids: Sequence[str],
    evidence_ids: Sequence[str],
    created_at: datetime,
) -> None:
    normalized_claim_ids = tuple(sorted(_dedupe(related_claim_ids)))
    normalized_evidence_ids = tuple(sorted(_dedupe(evidence_ids)))
    key = (
        issue_code,
        target_type.value,
        target_id,
        normalized_claim_ids,
        normalized_evidence_ids,
    )
    if key in seen:
        return
    seen.add(key)
    tasks.append(
        ReviewTask(
            review_task_id=_review_task_id(issue_code, target_id, len(tasks) + 1),
            task_id=task_id,
            check_name=check_name,
            issue_code=issue_code,
            severity=severity,
            target_type=target_type,
            target_id=target_id,
            message=message,
            required_action=required_action,
            target_agent=target_agent,
            related_claim_ids=list(normalized_claim_ids),
            evidence_ids=list(normalized_evidence_ids),
            created_at=created_at,
        )
    )


def _linked_evidences(
    claim: Claim,
    evidence_by_id: Mapping[str, Evidence],
) -> list[Evidence]:
    return [
        evidence_by_id[evidence_id]
        for evidence_id in claim.evidence_ids
        if evidence_id in evidence_by_id
    ]


def _claim_needs_time_sensitive_evidence(
    claim: Claim,
    evidences: Sequence[Evidence],
) -> bool:
    return _contains_any(claim.content, TIME_SENSITIVE_TERMS) or any(
        _is_time_sensitive_evidence(evidence, claim) for evidence in evidences
    )


def _is_time_sensitive_evidence(evidence: Evidence, claim: Claim) -> bool:
    if _contains_any(_evidence_text(evidence, claim), TIME_SENSITIVE_TERMS):
        return True
    return any(
        key in evidence.metadata
        for key in ("price", "sales", "rating", "review_count", "ranking", "rank")
    )


def _requires_screenshot(evidence: Evidence, claim: Claim) -> bool:
    if _contains_any(_evidence_text(evidence, claim), SCREENSHOT_REQUIRED_TERMS):
        return True
    price = evidence.metadata.get("price")
    if isinstance(price, dict) and price:
        return True
    return any(key in evidence.metadata for key in ("certification", "certificate"))


def _review_sample_count(evidence: Evidence) -> int:
    for key in ("cluster_size", "review_count", "comment_count", "sample_size"):
        value = _coerce_int(evidence.metadata.get(key))
        if value is not None:
            return value
    if str(evidence.source_type) == "douyin_review_snapshot":
        return 1
    return 0


def _evidence_text(evidence: Evidence, claim: Claim) -> str:
    return " ".join(
        part
        for part in (
            claim.claim_type,
            claim.content,
            evidence.content_summary,
            str(evidence.metadata),
        )
        if part
    )


def _contains_any(text: str, terms: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _coerce_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        digits = re.sub(r"\D", "", value)
        if digits:
            return int(digits)
    return None


def _dedupe(items: Sequence[str]) -> list[str]:
    deduped = []
    for item in items:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _review_task_id(issue_code: str, target_id: str, index: int) -> str:
    return f"review_{index:03d}_{_slug(issue_code)}_{_slug(target_id)}"


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    return slug.strip("_") or "item"


def _validate_claim(item: ClaimInput) -> Claim:
    if isinstance(item, Claim):
        return item
    return Claim.model_validate(item)


def _validate_evidence(item: EvidenceInput) -> Evidence:
    if isinstance(item, Evidence):
        return item
    return Evidence.model_validate(item)


def _validate_edge(item: CompetitionEdgeInput) -> CompetitionEdge:
    if isinstance(item, CompetitionEdge):
        return item
    return CompetitionEdge.model_validate(item)


__all__ = ["run_qa_rules"]
