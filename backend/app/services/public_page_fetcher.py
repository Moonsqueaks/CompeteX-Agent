import hashlib
import time
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

import httpx

from app.schemas import PublicPageSnapshot
from app.schemas.common import JsonObject
from app.services.snapshot_loader import PROJECT_ROOT

DEFAULT_PUBLIC_PAGE_CACHE_DIR = PROJECT_ROOT / "data" / "public_pages"
DEFAULT_TIMEOUT_SECONDS = 6.0
DEFAULT_MAX_BODY_BYTES = 2 * 1024 * 1024
BLOCKED_STATUS_CODES = {401, 403, 407, 429}
PROJECT_USER_AGENT = "zijieagent-public-page-stage1/1.0"


class PublicPageFetchError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        url: str,
        status_code: int | None = None,
        details: JsonObject | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.url = url
        self.status_code = status_code
        self.details = details or {}


class PublicPageFetcher:
    def __init__(
        self,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_body_bytes: int = DEFAULT_MAX_BODY_BYTES,
        cache_dir: Path | str | None = DEFAULT_PUBLIC_PAGE_CACHE_DIR,
    ) -> None:
        self.transport = transport
        self.timeout_seconds = timeout_seconds
        self.max_body_bytes = max_body_bytes
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None

    def fetch(
        self,
        url: str,
        *,
        access_time: datetime | None = None,
    ) -> PublicPageSnapshot:
        fetched_at = access_time or datetime.now(UTC)
        started_at = time.perf_counter()
        try:
            with httpx.Client(
                follow_redirects=False,
                timeout=self.timeout_seconds,
                transport=self.transport,
                headers={"User-Agent": PROJECT_USER_AGENT},
            ) as client:
                response = client.get(url)
        except httpx.TimeoutException as exc:
            raise PublicPageFetchError(
                "fetch_timeout",
                "Known public page request timed out.",
                url=url,
            ) from exc
        except httpx.HTTPError as exc:
            raise PublicPageFetchError(
                "fetch_http_error",
                "Known public page request failed.",
                url=url,
                details={"reason": exc.__class__.__name__},
            ) from exc

        duration_ms = int((time.perf_counter() - started_at) * 1000)
        status_code = response.status_code
        if status_code in BLOCKED_STATUS_CODES:
            raise PublicPageFetchError(
                "fetch_blocked",
                "Public page is blocked, login-gated, rate-limited, or unavailable.",
                url=url,
                status_code=status_code,
                details={"duration_ms": duration_ms},
            )
        if 300 <= status_code < 400:
            raise PublicPageFetchError(
                "redirect_not_followed",
                "Cross-page redirects are not followed in Stage 1.",
                url=url,
                status_code=status_code,
                details={
                    "location_present": bool(response.headers.get("location")),
                    "duration_ms": duration_ms,
                },
            )
        if status_code >= 400:
            raise PublicPageFetchError(
                "fetch_status_error",
                "Public page returned an error status.",
                url=url,
                status_code=status_code,
                details={"duration_ms": duration_ms},
            )

        body = response.content[: self.max_body_bytes + 1]
        if len(body) > self.max_body_bytes:
            raise PublicPageFetchError(
                "response_too_large",
                "Public page response exceeds the Stage 1 size limit.",
                url=url,
                status_code=status_code,
                details={"max_body_bytes": self.max_body_bytes},
            )

        html_text = response.text
        if _looks_blocked_or_login(html_text):
            raise PublicPageFetchError(
                "blocked_or_login_page",
                "Public page appears to be a login, captcha, or risk-control page.",
                url=url,
                status_code=status_code,
            )

        content_type = response.headers.get("content-type")
        if content_type and "html" not in content_type.lower():
            raise PublicPageFetchError(
                "unsupported_content_type",
                "Stage 1 only parses HTML public pages.",
                url=url,
                status_code=status_code,
                details={"content_type": content_type},
            )

        html_cache_path = _write_html_cache(
            url=url,
            html_text=html_text,
            cache_dir=self.cache_dir,
        )
        return PublicPageSnapshot(
            url=url,
            domain=urlparse(url).netloc.lower(),
            http_status=status_code,
            access_time=fetched_at,
            title=None,
            text_summary=_short_text(html_text),
            html_cache_path=html_cache_path,
            screenshot_path=None,
            parse_status="fetched",
            content_type=content_type,
            response_size_bytes=len(response.content),
            metadata={
                "html_text": html_text,
                "duration_ms": duration_ms,
                "fetcher": "httpx",
                "max_body_bytes": self.max_body_bytes,
                "user_agent": PROJECT_USER_AGENT,
            },
        )


def public_page_fetch_error_payload(error: PublicPageFetchError) -> JsonObject:
    return {
        "code": error.code,
        "message": error.message,
        "url": error.url,
        "status_code": error.status_code,
        "details": error.details,
    }


def fetch_snapshot_payload(snapshot: PublicPageSnapshot) -> JsonObject:
    payload = snapshot.model_dump(mode="json")
    metadata = payload.get("metadata")
    if isinstance(metadata, Mapping):
        metadata = dict(metadata)
        metadata.pop("html_text", None)
        payload["metadata"] = metadata
    return payload


def _write_html_cache(
    *,
    url: str,
    html_text: str,
    cache_dir: Path | None,
) -> str | None:
    if cache_dir is None:
        return None
    cache_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    path = (cache_dir / f"{digest}.html").resolve()
    project_root = PROJECT_ROOT.resolve()
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise PublicPageFetchError(
            "cache_path_outside_project",
            "Public page cache path is outside the project root.",
            url=url,
        ) from exc
    path.write_text(html_text, encoding="utf-8")
    return path.relative_to(project_root).as_posix()


def _looks_blocked_or_login(html_text: str) -> bool:
    lowered = html_text.lower()
    blocked_markers = (
        "captcha",
        "verify you are human",
        "access denied",
        "login required",
        "please login",
        "risk control",
        "security check",
        "验证码",
        "登录",
        "风控",
    )
    return any(marker in lowered for marker in blocked_markers)


def _short_text(text: str, max_chars: int = 240) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


__all__ = [
    "BLOCKED_STATUS_CODES",
    "DEFAULT_MAX_BODY_BYTES",
    "DEFAULT_PUBLIC_PAGE_CACHE_DIR",
    "DEFAULT_TIMEOUT_SECONDS",
    "PROJECT_USER_AGENT",
    "PublicPageFetchError",
    "PublicPageFetcher",
    "fetch_snapshot_payload",
    "public_page_fetch_error_payload",
]
