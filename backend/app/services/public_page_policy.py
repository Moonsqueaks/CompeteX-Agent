from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from urllib.parse import urlparse

from app.schemas.common import JsonObject

KNOWN_URL_SOURCES = {
    "task.target_product_url",
    "snapshot.source_url",
    "manual_allowlist",
}
DEFAULT_MAX_PUBLIC_PAGES_PER_TASK = 4
DEFAULT_ALLOWED_DOMAINS = frozenset(
    {
        "v.douyin.com",
        "www.douyin.com",
        "douyin.com",
        "example.com",
        "example.invalid",
        "brand.example",
    }
)


@dataclass(frozen=True)
class PublicPageUrlCandidate:
    url: str
    source: str
    product_id: str | None = None
    role: str | None = None
    sku_id: str | None = None


@dataclass(frozen=True)
class PublicPagePolicyDecision:
    url: str
    source: str
    allowed: bool
    reason_code: str
    reason: str
    product_id: str | None = None
    domain: str | None = None
    metadata: JsonObject | None = None


def evaluate_public_page_candidates(
    candidates: Iterable[PublicPageUrlCandidate],
    *,
    allowed_domains: Iterable[str] | None = None,
    max_pages: int = DEFAULT_MAX_PUBLIC_PAGES_PER_TASK,
) -> list[PublicPagePolicyDecision]:
    normalized_allowed_domains = _normalized_domains(allowed_domains)
    decisions: list[PublicPagePolicyDecision] = []
    seen_urls: set[str] = set()
    accepted_count = 0

    for candidate in candidates:
        decision = evaluate_public_page_candidate(
            candidate,
            allowed_domains=normalized_allowed_domains,
            accepted_count=accepted_count,
            seen_urls=seen_urls,
            max_pages=max_pages,
        )
        decisions.append(decision)
        if decision.allowed:
            accepted_count += 1
            seen_urls.add(_normalize_url(candidate.url) or candidate.url)

    return decisions


def evaluate_public_page_candidate(
    candidate: PublicPageUrlCandidate,
    *,
    allowed_domains: Iterable[str] | None = None,
    accepted_count: int = 0,
    seen_urls: set[str] | None = None,
    max_pages: int = DEFAULT_MAX_PUBLIC_PAGES_PER_TASK,
) -> PublicPagePolicyDecision:
    url = candidate.url.strip()
    normalized_url = _normalize_url(url)
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    seen = seen_urls or set()
    normalized_allowed_domains = _normalized_domains(allowed_domains)
    metadata = {
        "known_url_source": candidate.source,
        "role": candidate.role,
        "sku_id": candidate.sku_id,
        "stage": "stage_1_known_url",
    }

    if not normalized_url:
        return _decision(candidate, False, "empty_url", "URL is empty.", metadata=metadata)
    if parsed.scheme not in {"http", "https"}:
        return _decision(
            candidate,
            False,
            "unsupported_scheme",
            "Only http and https public pages are allowed.",
            domain=domain or None,
            metadata=metadata,
        )
    if candidate.source not in KNOWN_URL_SOURCES:
        return _decision(
            candidate,
            False,
            "unknown_url_source",
            "Stage 1 only accepts task input URLs, snapshot source URLs, or manual allowlist URLs.",
            domain=domain,
            metadata=metadata,
        )
    if accepted_count >= max_pages:
        return _decision(
            candidate,
            False,
            "page_limit_exceeded",
            "Known URL enhancement page limit was reached.",
            domain=domain,
            metadata={**metadata, "max_pages": max_pages},
        )
    if normalized_url in seen:
        return _decision(
            candidate,
            False,
            "duplicate_url",
            "Duplicate known URL was skipped.",
            domain=domain,
            metadata=metadata,
        )
    if normalized_allowed_domains and not _domain_allowed(domain, normalized_allowed_domains):
        return _decision(
            candidate,
            False,
            "domain_not_allowed",
            "Domain is outside the Stage 1 allowlist.",
            domain=domain,
            metadata={
                **metadata,
                "allowed_domains": sorted(normalized_allowed_domains),
            },
        )

    return _decision(
        candidate,
        True,
        "allowed",
        "Known URL passed Stage 1 public page policy.",
        domain=domain,
        metadata=metadata,
    )


def public_page_policy_decision_payload(
    decision: PublicPagePolicyDecision,
) -> JsonObject:
    return {
        "url": decision.url,
        "source": decision.source,
        "product_id": decision.product_id,
        "domain": decision.domain,
        "allowed": decision.allowed,
        "reason_code": decision.reason_code,
        "reason": decision.reason,
        "metadata": decision.metadata or {},
    }


def policy_decisions_summary(
    decisions: Iterable[PublicPagePolicyDecision],
) -> list[JsonObject]:
    return [public_page_policy_decision_payload(decision) for decision in decisions]


def _decision(
    candidate: PublicPageUrlCandidate,
    allowed: bool,
    reason_code: str,
    reason: str,
    *,
    domain: str | None = None,
    metadata: Mapping[str, object] | None = None,
) -> PublicPagePolicyDecision:
    return PublicPagePolicyDecision(
        url=candidate.url.strip(),
        source=candidate.source,
        product_id=candidate.product_id,
        allowed=allowed,
        reason_code=reason_code,
        reason=reason,
        domain=domain,
        metadata=dict(metadata or {}),
    )


def _normalized_domains(allowed_domains: Iterable[str] | None) -> set[str]:
    if allowed_domains is None:
        allowed_domains = DEFAULT_ALLOWED_DOMAINS
    return {
        domain.strip().lower()
        for domain in allowed_domains
        if isinstance(domain, str) and domain.strip()
    }


def _domain_allowed(domain: str, allowed_domains: set[str]) -> bool:
    return any(domain == allowed or domain.endswith(f".{allowed}") for allowed in allowed_domains)


def _normalize_url(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    return stripped.rstrip("/").lower()


__all__ = [
    "DEFAULT_ALLOWED_DOMAINS",
    "DEFAULT_MAX_PUBLIC_PAGES_PER_TASK",
    "KNOWN_URL_SOURCES",
    "PublicPagePolicyDecision",
    "PublicPageUrlCandidate",
    "evaluate_public_page_candidate",
    "evaluate_public_page_candidates",
    "policy_decisions_summary",
    "public_page_policy_decision_payload",
]
