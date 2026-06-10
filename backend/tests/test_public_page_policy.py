from app.services.public_page_policy import (
    PublicPageUrlCandidate,
    evaluate_public_page_candidates,
)


def test_policy_allows_known_http_url_from_task_input() -> None:
    decisions = evaluate_public_page_candidates(
        [
            PublicPageUrlCandidate(
                url="https://example.com/product",
                source="task.target_product_url",
                product_id="prod_1",
            )
        ],
        allowed_domains={"example.com"},
    )

    assert decisions[0].allowed is True
    assert decisions[0].reason_code == "allowed"
    assert decisions[0].domain == "example.com"


def test_policy_rejects_non_http_unknown_source_and_page_limit() -> None:
    decisions = evaluate_public_page_candidates(
        [
            PublicPageUrlCandidate(url="file:///tmp/item.html", source="task.target_product_url"),
            PublicPageUrlCandidate(url="https://example.com/a", source="search_result"),
            PublicPageUrlCandidate(url="https://example.com/b", source="snapshot.source_url"),
            PublicPageUrlCandidate(url="https://example.com/c", source="snapshot.source_url"),
        ],
        allowed_domains={"example.com"},
        max_pages=1,
    )

    assert [decision.reason_code for decision in decisions] == [
        "unsupported_scheme",
        "unknown_url_source",
        "allowed",
        "page_limit_exceeded",
    ]


def test_policy_rejects_domain_outside_allowlist_and_duplicate_url() -> None:
    decisions = evaluate_public_page_candidates(
        [
            PublicPageUrlCandidate(url="https://not-allowed.test/a", source="snapshot.source_url"),
            PublicPageUrlCandidate(url="https://example.com/a/", source="snapshot.source_url"),
            PublicPageUrlCandidate(url="https://example.com/a", source="snapshot.source_url"),
        ],
        allowed_domains={"example.com"},
    )

    assert decisions[0].reason_code == "domain_not_allowed"
    assert decisions[1].allowed is True
    assert decisions[2].reason_code == "duplicate_url"
