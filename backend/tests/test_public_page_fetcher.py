from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from app.services.public_page_fetcher import PublicPageFetcher, PublicPageFetchError
from app.services.snapshot_loader import PROJECT_ROOT

NOW = datetime(2026, 6, 9, 10, 0, tzinfo=UTC)


def test_fetcher_uses_httpx_and_caches_html_inside_project() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["user-agent"].startswith("zijieagent-public-page-stage1")
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><title>Known Product</title><body>price: CNY 1999</body></html>",
        )

    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(handler),
        cache_dir=PROJECT_ROOT / ".tmp" / "public_pages" / "test_cache",
    )

    snapshot = fetcher.fetch("https://example.com/product", access_time=NOW)

    assert snapshot.url == "https://example.com/product"
    assert snapshot.http_status == 200
    assert snapshot.access_time == NOW
    assert snapshot.html_cache_path
    assert snapshot.html_cache_path.startswith(".tmp/public_pages/test_cache/")
    assert snapshot.metadata["fetcher"] == "httpx"
    assert "Known Product" in snapshot.metadata["html_text"]
    Path(PROJECT_ROOT / snapshot.html_cache_path).unlink(missing_ok=True)


def test_fetcher_ignores_environment_proxy_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_kwargs = {}

    class FakeClient:
        def __init__(self, **kwargs) -> None:
            captured_kwargs.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def get(self, url: str) -> httpx.Response:
            return httpx.Response(
                200,
                headers={"content-type": "text/html; charset=utf-8"},
                text="<html><title>Proxy Safe</title></html>",
            )

    monkeypatch.setattr(httpx, "Client", FakeClient)
    fetcher = PublicPageFetcher(cache_dir=None)

    snapshot = fetcher.fetch("https://example.com/product", access_time=NOW)

    assert captured_kwargs["trust_env"] is False
    assert "Proxy Safe" in snapshot.metadata["html_text"]


def test_fetcher_wraps_optional_http_dependency_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenClient:
        def __init__(self, **_: object) -> None:
            raise ImportError("Using SOCKS proxy, but the 'socksio' package is not installed.")

    monkeypatch.setattr(httpx, "Client", BrokenClient)
    fetcher = PublicPageFetcher(cache_dir=None)

    with pytest.raises(PublicPageFetchError) as exc_info:
        fetcher.fetch("https://example.com/product", access_time=NOW)

    assert exc_info.value.code == "fetch_dependency_error"
    assert exc_info.value.details["reason"] == "ImportError"


def test_fetcher_rejects_blocked_status_without_retrying() -> None:
    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(lambda _: httpx.Response(403, text="Forbidden")),
        cache_dir=None,
    )

    with pytest.raises(PublicPageFetchError) as exc_info:
        fetcher.fetch("https://example.com/blocked", access_time=NOW)

    assert exc_info.value.code == "fetch_blocked"
    assert exc_info.value.status_code == 403


def test_fetcher_rejects_too_large_response() -> None:
    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, text="x" * 20)),
        max_body_bytes=4,
        cache_dir=None,
    )

    with pytest.raises(PublicPageFetchError) as exc_info:
        fetcher.fetch("https://example.com/large", access_time=NOW)

    assert exc_info.value.code == "response_too_large"


def test_fetcher_rejects_login_or_captcha_page() -> None:
    fetcher = PublicPageFetcher(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, text="<html>Please login captcha</html>")
        ),
        cache_dir=None,
    )

    with pytest.raises(PublicPageFetchError) as exc_info:
        fetcher.fetch("https://example.com/login", access_time=NOW)

    assert exc_info.value.code == "blocked_or_login_page"
