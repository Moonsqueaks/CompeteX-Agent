from collections.abc import Mapping
import re
from typing import Any

_STANDARD_MARK_RE = re.compile(
    r"(?:按|按照|根据|基于)?\s*[12]\.0\s*标准[，,、]?\s*标记为"
)
_STANDARD_REFERENCE_RE = re.compile(
    r"(?:按|按照|根据|基于)\s*[12]\.0\s*标准[，,、]?\s*"
)


def sanitize_internal_standard_copy(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_internal_standard_copy(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_internal_standard_copy(item) for item in value)
    if isinstance(value, Mapping):
        return {key: sanitize_internal_standard_copy(item) for key, item in value.items()}
    return value


def _sanitize_text(value: str) -> str:
    sanitized = _STANDARD_MARK_RE.sub("当前标记为", value)
    sanitized = _STANDARD_REFERENCE_RE.sub("", sanitized)
    return sanitized
