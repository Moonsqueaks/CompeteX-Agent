import json
from pathlib import Path

import httpx
import pytest

from app.services.llm_client import LLMClient, LLMSettings, LLMTokenUsage, load_llm_settings


def test_load_llm_settings_from_explicit_env_without_exposing_key() -> None:
    settings = load_llm_settings(
        env={
            "LLM_ENABLED": "true",
            "LLM_PROVIDER": "doubao",
            "DOUBAO_API_KEY": "sk-test-secret",
            "DOUBAO_BASE_URL": "https://ark.example.com/api/v3",
            "DOUBAO_MODEL": "Doubao-Seed-2.0-lite",
            "LLM_TIMEOUT_SECONDS": "12",
            "LLM_MAX_RETRIES": "1",
        },
        load_dotenv_file=False,
    )

    assert settings.available is True
    assert settings.timeout_seconds == 12
    assert settings.max_retries == 1
    assert "sk-test-secret" not in repr(settings)
    assert settings.safe_metadata() == {
        "enabled": True,
        "provider": "doubao",
        "base_url_configured": True,
        "api_key_configured": True,
        "model": "Doubao-Seed-2.0-lite",
        "timeout_seconds": 12.0,
        "max_retries": 1,
        "retry_backoff_seconds": 8.0,
    }


def test_load_llm_settings_can_read_backend_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    for name in (
        "LLM_ENABLED",
        "LLM_PROVIDER",
        "DOUBAO_API_KEY",
        "DOUBAO_BASE_URL",
        "DOUBAO_MODEL",
    ):
        monkeypatch.delenv(name, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "LLM_ENABLED=true",
                "LLM_PROVIDER=doubao",
                "DOUBAO_API_KEY=sk-env-secret",
                "DOUBAO_BASE_URL=https://ark.example.com/api/v3",
                "DOUBAO_MODEL=Doubao-Seed-2.0-lite",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_llm_settings(dotenv_path=env_file)

    assert settings.available is True
    assert settings.base_url == "https://ark.example.com/api/v3"
    assert "sk-env-secret" not in repr(settings)


def test_complete_json_uses_fallback_when_key_is_missing() -> None:
    settings = LLMSettings(
        enabled=True,
        provider="doubao",
        api_key="",
        base_url="https://ark.example.com/api/v3",
        model="Doubao-Seed-2.0-lite",
    )
    client = LLMClient(settings)

    result = client.complete_json(
        system_prompt="只输出 JSON。",
        user_prompt="生成报告。",
        fallback={"paragraphs": ["暂无可靠数据"]},
        schema_name="report_section",
    )

    assert result.used_fallback is True
    assert result.fallback_reason == "LLM_API_KEY_MISSING"
    assert result.attempts == 0
    assert result.data == {"paragraphs": ["暂无可靠数据"]}
    assert result.token_usage.total_tokens == 0


def test_complete_json_calls_openai_compatible_chat_completion() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        captured_request["authorization"] = request.headers.get("Authorization")
        captured_request["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"paragraphs":["结论更清楚。"]}'}}],
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                },
            },
        )

    client = LLMClient(_settings(max_retries=0), transport=httpx.MockTransport(handler))

    result = client.complete_json(
        system_prompt="只输出 JSON。",
        user_prompt="生成报告。",
        fallback={"paragraphs": ["暂无可靠数据"]},
        schema_name="report_section",
    )

    assert result.used_fallback is False
    assert result.data == {"paragraphs": ["结论更清楚。"]}
    assert result.raw_text == '{"paragraphs":["结论更清楚。"]}'
    assert result.token_usage.prompt_tokens == 11
    assert result.token_usage.completion_tokens == 7
    assert result.token_usage.total_tokens == 18
    assert captured_request["url"] == "https://ark.example.com/api/v3/chat/completions"
    assert captured_request["authorization"] == "Bearer sk-test-secret"
    assert captured_request["body"] == {
        "model": "Doubao-Seed-2.0-lite",
        "messages": [
            {"role": "system", "content": "只输出 JSON。"},
            {"role": "user", "content": "生成报告。"},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }


def test_complete_json_adds_https_scheme_when_base_url_omits_protocol() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["url"] = str(request.url)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"ok":true}'}}]},
        )

    client = LLMClient(
        LLMSettings(
            enabled=True,
            provider="doubao",
            api_key="sk-test-secret",
            base_url="ark.example.com/api/v3",
            model="Doubao-Seed-2.0-lite",
            timeout_seconds=1,
            max_retries=0,
        ),
        transport=httpx.MockTransport(handler),
    )

    result = client.complete_json(
        system_prompt="只输出 JSON。",
        user_prompt="生成报告。",
        fallback={"ok": False},
        schema_name="base_url_payload",
    )

    assert result.used_fallback is False
    assert captured_request["url"] == "https://ark.example.com/api/v3/chat/completions"


def test_complete_json_retries_without_response_format_when_model_rejects_it() -> None:
    bodies: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        bodies.append(body)
        if len(bodies) == 1:
            return httpx.Response(
                400,
                json={
                    "error": {
                        "code": "InvalidParameter",
                        "message": (
                            "response_format.type json_object is not supported by this model."
                        ),
                    }
                },
            )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"ok":true}'}}],
                "usage": {"prompt_tokens": 4, "completion_tokens": 5, "total_tokens": 9},
            },
        )

    client = LLMClient(_settings(max_retries=0), transport=httpx.MockTransport(handler))

    result = client.complete_json(
        system_prompt="Only output JSON.",
        user_prompt="Return ok true.",
        fallback={"ok": False},
        schema_name="response_format_fallback",
    )

    assert len(bodies) == 2
    assert bodies[0]["response_format"] == {"type": "json_object"}
    assert "response_format" not in bodies[1]
    assert result.used_fallback is False
    assert result.attempts == 1
    assert result.data == {"ok": True}
    assert result.token_usage.total_tokens == 9


def test_complete_json_retries_non_json_output_then_succeeds() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(200, json={"choices": [{"message": {"content": "不是 JSON"}}]})
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"ok":true}'}}],
                "usage": {"total_tokens": 5},
            },
        )

    client = LLMClient(_settings(max_retries=1), transport=httpx.MockTransport(handler))

    result = client.complete_json(
        system_prompt="只输出 JSON。",
        user_prompt="生成报告。",
        fallback={"ok": False},
        schema_name="retry_payload",
    )

    assert calls == 2
    assert result.used_fallback is False
    assert result.attempts == 2
    assert result.data == {"ok": True}
    assert any(error["code"] == "MODEL_OUTPUT_NON_STRUCTURED" for error in result.errors)


def test_complete_json_backs_off_after_rate_limit_then_succeeds() -> None:
    calls = 0
    sleeps: list[float] = []

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "2.5"},
                json={"error": {"message": "too many requests"}},
            )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"ok":true}'}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            },
        )

    client = LLMClient(
        _settings(max_retries=1),
        sleep=sleeps.append,
        transport=httpx.MockTransport(handler),
    )

    result = client.complete_json(
        system_prompt="只输出 JSON。",
        user_prompt="生成报告。",
        fallback={"ok": False},
        schema_name="rate_limit_retry",
    )

    assert calls == 2
    assert sleeps == [2.5]
    assert result.used_fallback is False
    assert result.data == {"ok": True}
    assert result.token_usage.total_tokens == 5


def test_complete_json_falls_back_after_request_failures_without_leaking_key() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("failed with Bearer sk-test-secret and token=abc")

    client = LLMClient(_settings(max_retries=1), transport=httpx.MockTransport(handler))

    result = client.complete_json(
        system_prompt="只输出 JSON。",
        user_prompt="生成报告。",
        fallback={"paragraphs": ["本地规则兜底"]},
        schema_name="request_failure",
    )

    assert result.used_fallback is True
    assert result.fallback_reason == "LLM_OUTPUT_FALLBACK_USED"
    assert result.attempts == 2
    assert result.data == {"paragraphs": ["本地规则兜底"]}
    assert len(result.errors) == 2
    assert "sk-test-secret" not in repr(result.errors)
    assert "token=abc" not in repr(result.errors)


def test_token_usage_can_be_converted_to_trace_log() -> None:
    usage_log = LLMTokenUsage(
        model_name="Doubao-Seed-2.0-lite",
        prompt_tokens=3,
        completion_tokens=4,
        total_tokens=7,
    ).to_log(
        task_id="task_001",
        run_id="run_writer",
        agent_name="writer_agent",
        usage_id="usage_writer_llm",
    )

    assert usage_log.task_id == "task_001"
    assert usage_log.run_id == "run_writer"
    assert usage_log.agent_name == "writer_agent"
    assert usage_log.model_name == "Doubao-Seed-2.0-lite"
    assert usage_log.total_tokens == 7


def _settings(max_retries: int = 0) -> LLMSettings:
    return LLMSettings(
        enabled=True,
        provider="doubao",
        api_key="sk-test-secret",
        base_url="https://ark.example.com/api/v3",
        model="Doubao-Seed-2.0-lite",
        timeout_seconds=1,
        max_retries=max_retries,
    )
