from app.services import coerce_structured_model_output


def test_structured_model_output_retries_until_json_object() -> None:
    result = coerce_structured_model_output(
        ["not-json", '{"claim": "structured"}'],
        fallback={"claim": "fallback"},
        schema_name="claim_candidate",
    )

    assert result.data == {"claim": "structured"}
    assert result.attempts == 2
    assert result.used_fallback is False
    assert result.errors[0]["code"] == "MODEL_OUTPUT_NON_STRUCTURED"


def test_structured_model_output_extracts_json_from_markdown_explanation() -> None:
    result = coerce_structured_model_output(
        [
            """
            以下是结构化结果：
            ```json
            {"ok": true, "summary": "已生成"}
            ```
            后续说明不应影响解析。
            """
        ],
        fallback={"ok": False},
        schema_name="markdown_json_candidate",
    )

    assert result.data == {"ok": True, "summary": "已生成"}
    assert result.attempts == 1
    assert result.used_fallback is False
    assert result.errors == []


def test_structured_model_output_uses_fallback_after_unstructured_candidates() -> None:
    result = coerce_structured_model_output(
        ["not-json", '["still", "not", "object"]'],
        fallback={"claim": "暂无可靠数据", "risk_flags": ["unreliable_data"]},
        schema_name="claim_candidate",
    )

    assert result.data == {"claim": "暂无可靠数据", "risk_flags": ["unreliable_data"]}
    assert result.attempts == 2
    assert result.used_fallback is True
    assert [error["code"] for error in result.errors] == [
        "MODEL_OUTPUT_NON_STRUCTURED",
        "MODEL_OUTPUT_NON_STRUCTURED",
        "MODEL_OUTPUT_FALLBACK_USED",
    ]
