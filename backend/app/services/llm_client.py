from __future__ import annotations

import os
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.schemas.common import AgentName, JsonObject
from app.schemas.trace import TokenUsageLog
from app.services.structured_output import coerce_structured_model_output

OPENAI_COMPATIBLE_CHAT_PATH = "/chat/completions"
DEFAULT_LLM_PROVIDER = "doubao"
DEFAULT_LLM_MODEL = "Doubao-Seed-2.0-lite"
DEFAULT_LLM_TIMEOUT_SECONDS = 30.0
DEFAULT_LLM_MAX_RETRIES = 2
DEFAULT_LLM_RETRY_BACKOFF_SECONDS = 8.0
MAX_LLM_RETRY_BACKOFF_SECONDS = 30.0


@dataclass(frozen=True)
class LLMSettings:
    enabled: bool
    provider: str
    api_key: str = field(repr=False)
    base_url: str
    model: str
    timeout_seconds: float = DEFAULT_LLM_TIMEOUT_SECONDS
    max_retries: int = DEFAULT_LLM_MAX_RETRIES
    retry_backoff_seconds: float = DEFAULT_LLM_RETRY_BACKOFF_SECONDS

    @property
    def available(self) -> bool:
        return self.disabled_reason is None

    @property
    def disabled_reason(self) -> str | None:
        if not self.enabled:
            return "LLM_DISABLED"
        if self.provider != DEFAULT_LLM_PROVIDER:
            return "LLM_PROVIDER_UNSUPPORTED"
        if not self.api_key:
            return "LLM_API_KEY_MISSING"
        if not self.base_url:
            return "LLM_BASE_URL_MISSING"
        if not self.model:
            return "LLM_MODEL_MISSING"
        return None

    def safe_metadata(self) -> JsonObject:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "base_url_configured": bool(self.base_url),
            "api_key_configured": bool(self.api_key),
            "model": self.model,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_backoff_seconds": self.retry_backoff_seconds,
        }


@dataclass(frozen=True)
class LLMTokenUsage:
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_log(
        self,
        *,
        task_id: str,
        run_id: str,
        agent_name: AgentName,
        usage_id: str,
    ) -> TokenUsageLog:
        return TokenUsageLog(
            usage_id=usage_id,
            task_id=task_id,
            run_id=run_id,
            agent_name=agent_name,
            model_name=self.model_name,
            prompt_tokens=self.prompt_tokens,
            completion_tokens=self.completion_tokens,
            total_tokens=self.total_tokens,
            created_at=datetime.now(UTC),
        )


@dataclass(frozen=True)
class LLMCallResult:
    data: JsonObject
    raw_text: str | None
    attempts: int
    used_fallback: bool
    fallback_reason: str | None
    errors: list[JsonObject]
    token_usage: LLMTokenUsage
    model_name: str

    @property
    def token_metadata(self) -> JsonObject:
        return {
            "model_name": self.token_usage.model_name,
            "prompt_tokens": self.token_usage.prompt_tokens,
            "completion_tokens": self.token_usage.completion_tokens,
            "total_tokens": self.token_usage.total_tokens,
        }


class LLMClient:
    def __init__(
        self,
        settings: LLMSettings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
        sleep: Any | None = None,
    ):
        self.settings = settings or load_llm_settings()
        self._transport = transport
        self._sleep = sleep or time.sleep

    def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        fallback: Mapping[str, Any],
        schema_name: str,
        temperature: float = 0.2,
    ) -> LLMCallResult:
        fallback_payload = _json_object(fallback)
        disabled_reason = self.settings.disabled_reason
        if disabled_reason is not None:
            return self._fallback_result(
                fallback_payload,
                attempts=0,
                reason=disabled_reason,
                errors=[],
            )

        errors: list[JsonObject] = []
        last_raw_text: str | None = None
        token_usage = LLMTokenUsage(model_name=self.settings.model)
        total_attempts = max(1, self.settings.max_retries + 1)

        for attempt in range(1, total_attempts + 1):
            try:
                response_payload = self._request_chat_completion(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=temperature,
                )
            except (httpx.HTTPError, ValueError) as exc:
                errors.append(_safe_error(attempt, "LLM_REQUEST_FAILED", exc))
                self._sleep_before_retry(exc, attempt=attempt, total_attempts=total_attempts)
                continue

            token_usage = _extract_token_usage(response_payload, self.settings.model)
            last_raw_text = _extract_message_content(response_payload)
            structured = coerce_structured_model_output(
                [last_raw_text],
                fallback=fallback_payload,
                schema_name=schema_name,
                max_attempts=1,
            )
            if not structured.used_fallback:
                return LLMCallResult(
                    data=structured.data,
                    raw_text=last_raw_text,
                    attempts=attempt,
                    used_fallback=False,
                    fallback_reason=None,
                    errors=errors + structured.errors,
                    token_usage=token_usage,
                    model_name=self.settings.model,
                )

            errors.extend(structured.errors)
            self._sleep_before_retry(None, attempt=attempt, total_attempts=total_attempts)

        return LLMCallResult(
            data=fallback_payload,
            raw_text=last_raw_text,
            attempts=total_attempts,
            used_fallback=True,
            fallback_reason="LLM_OUTPUT_FALLBACK_USED",
            errors=errors,
            token_usage=token_usage,
            model_name=self.settings.model,
        )

    def _request_chat_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
    ) -> JsonObject:
        endpoint = _chat_completions_url(self.settings.base_url)
        payload: JsonObject = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(
            timeout=self.settings.timeout_seconds,
            transport=self._transport,
            trust_env=False,
        ) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if not _is_response_format_unsupported(exc):
                    raise
                fallback_payload = dict(payload)
                fallback_payload.pop("response_format", None)
                response = client.post(endpoint, headers=headers, json=fallback_payload)
                response.raise_for_status()
            response_payload = response.json()

        if not isinstance(response_payload, Mapping):
            raise ValueError("LLM response body is not a JSON object.")
        return _json_object(response_payload)

    def _fallback_result(
        self,
        fallback_payload: JsonObject,
        *,
        attempts: int,
        reason: str,
        errors: list[JsonObject],
    ) -> LLMCallResult:
        return LLMCallResult(
            data=fallback_payload,
            raw_text=None,
            attempts=attempts,
            used_fallback=True,
            fallback_reason=reason,
            errors=errors,
            token_usage=LLMTokenUsage(model_name=self.settings.model or DEFAULT_LLM_MODEL),
            model_name=self.settings.model or DEFAULT_LLM_MODEL,
        )

    def _sleep_before_retry(
        self,
        exc: Exception | None,
        *,
        attempt: int,
        total_attempts: int,
    ) -> None:
        if attempt >= total_attempts:
            return

        retry_after = _retry_after_seconds(exc)
        delay = retry_after if retry_after is not None else self.settings.retry_backoff_seconds
        delay = min(max(delay, 0.0), MAX_LLM_RETRY_BACKOFF_SECONDS)
        if delay > 0:
            self._sleep(delay)


def load_llm_settings(
    *,
    env: Mapping[str, str] | None = None,
    dotenv_path: Path | None = None,
    load_dotenv_file: bool = True,
) -> LLMSettings:
    if env is None and load_dotenv_file:
        _load_backend_dotenv(dotenv_path)

    source = env or os.environ
    return LLMSettings(
        enabled=_read_bool(source.get("LLM_ENABLED"), default=False),
        provider=(source.get("LLM_PROVIDER") or DEFAULT_LLM_PROVIDER).strip().lower(),
        api_key=(source.get("DOUBAO_API_KEY") or "").strip(),
        base_url=(source.get("DOUBAO_BASE_URL") or "").strip(),
        model=(source.get("DOUBAO_MODEL") or DEFAULT_LLM_MODEL).strip(),
        timeout_seconds=_read_float(
            source.get("LLM_TIMEOUT_SECONDS"),
            DEFAULT_LLM_TIMEOUT_SECONDS,
        ),
        max_retries=_read_int(source.get("LLM_MAX_RETRIES"), DEFAULT_LLM_MAX_RETRIES),
        retry_backoff_seconds=_read_float(
            source.get("LLM_RETRY_BACKOFF_SECONDS"),
            DEFAULT_LLM_RETRY_BACKOFF_SECONDS,
        ),
    )


def _load_backend_dotenv(dotenv_path: Path | None) -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    path = dotenv_path or Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(path, override=False)


def _is_response_format_unsupported(exc: httpx.HTTPStatusError) -> bool:
    response = exc.response
    if response.status_code != 400:
        return False
    message = response.text.lower()
    return "response_format" in message and "not supported" in message


def _read_bool(value: str | None, *, default: bool) -> bool:
    if value is None or not value.strip():
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _read_float(value: str | None, default: float) -> float:
    if value is None or not value.strip():
        return default
    try:
        parsed = float(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _read_int(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed >= 0 else default


def _chat_completions_url(base_url: str) -> str:
    clean_base_url = base_url.rstrip("/")
    if not clean_base_url.startswith(("http://", "https://")):
        clean_base_url = f"https://{clean_base_url}"
    if clean_base_url.endswith(OPENAI_COMPATIBLE_CHAT_PATH):
        return clean_base_url
    return f"{clean_base_url}{OPENAI_COMPATIBLE_CHAT_PATH}"


def _extract_message_content(response_payload: Mapping[str, Any]) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("LLM response does not contain choices.")
    first_choice = choices[0]
    if not isinstance(first_choice, Mapping):
        raise ValueError("LLM choice is not a JSON object.")
    message = first_choice.get("message")
    if not isinstance(message, Mapping):
        raise ValueError("LLM choice does not contain a message.")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM message content is empty.")
    return content


def _extract_token_usage(response_payload: Mapping[str, Any], model_name: str) -> LLMTokenUsage:
    usage = response_payload.get("usage")
    if not isinstance(usage, Mapping):
        return LLMTokenUsage(model_name=model_name)

    prompt_tokens = _non_negative_int(usage.get("prompt_tokens"))
    completion_tokens = _non_negative_int(usage.get("completion_tokens"))
    total_tokens = _non_negative_int(usage.get("total_tokens"))
    if total_tokens != prompt_tokens + completion_tokens:
        total_tokens = prompt_tokens + completion_tokens

    return LLMTokenUsage(
        model_name=model_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )


def _non_negative_int(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _retry_after_seconds(exc: Exception | None) -> float | None:
    if not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code != 429:
        return None

    retry_after = exc.response.headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        seconds = float(retry_after)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def _safe_error(attempt: int, code: str, exc: Exception) -> JsonObject:
    return {
        "attempt": attempt,
        "code": code,
        "error_type": exc.__class__.__name__,
        "message": _redact_error_text(str(exc)),
    }


def _redact_error_text(value: str) -> str:
    if not value:
        return ""
    redacted = value
    for marker in ("Bearer ", "api_key=", "token=", "secret=", "password="):
        if marker in redacted:
            redacted = redacted.split(marker, 1)[0] + f"{marker}[REDACTED]"
    return redacted[:500]


def _json_object(value: Mapping[str, Any]) -> JsonObject:
    return {str(key): item for key, item in value.items()}
