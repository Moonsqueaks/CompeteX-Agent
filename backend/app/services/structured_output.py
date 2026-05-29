import json
from collections.abc import Iterable, Mapping
from json import JSONDecodeError
from typing import Any

from pydantic import Field

from app.schemas.common import JsonObject, StrictBaseModel


class StructuredModelOutputResult(StrictBaseModel):
    data: JsonObject
    attempts: int = Field(ge=0)
    used_fallback: bool
    errors: list[JsonObject] = Field(default_factory=list)


def coerce_structured_model_output(
    candidates: Iterable[str | Mapping[str, Any]],
    *,
    fallback: Mapping[str, Any],
    schema_name: str = "model_output",
    max_attempts: int = 2,
) -> StructuredModelOutputResult:
    """Parse optional model output as a JSON object, retrying candidates before fallback."""
    fallback_payload = _json_object_or_raise(fallback, source="fallback")
    errors: list[JsonObject] = []
    attempts = 0

    for candidate in candidates:
        if attempts >= max_attempts:
            break
        attempts += 1
        try:
            payload = _parse_candidate(candidate)
        except ValueError as exc:
            errors.append(
                {
                    "attempt": attempts,
                    "code": "MODEL_OUTPUT_NON_STRUCTURED",
                    "schema_name": schema_name,
                    "reason": str(exc),
                }
            )
            continue

        return StructuredModelOutputResult(
            data=payload,
            attempts=attempts,
            used_fallback=False,
            errors=errors,
        )

    errors.append(
        {
            "attempt": attempts,
            "code": "MODEL_OUTPUT_FALLBACK_USED",
            "schema_name": schema_name,
            "reason": "No candidate produced a structured JSON object.",
        }
    )
    return StructuredModelOutputResult(
        data=fallback_payload,
        attempts=attempts,
        used_fallback=True,
        errors=errors,
    )


def _parse_candidate(candidate: str | Mapping[str, Any]) -> JsonObject:
    if isinstance(candidate, Mapping):
        return _json_object_or_raise(candidate, source="candidate")
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError("Model output is empty.")

    try:
        loaded = json.loads(candidate)
    except JSONDecodeError as exc:
        raise ValueError(f"Model output is not valid JSON at {exc.lineno}:{exc.colno}.") from exc

    return _json_object_or_raise(loaded, source="candidate")


def _json_object_or_raise(value: Any, *, source: str) -> JsonObject:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a JSON object.")
    return {str(key): item for key, item in value.items()}
