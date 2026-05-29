import re
from collections.abc import Iterable, Mapping
from typing import Any

REDACTION_TEXT = "[REDACTED]"
REDACTED_KEY = "[REDACTED_KEY]"

SENSITIVE_KEY_NAMES = {
    "api_key",
    "apikey",
    "authorization",
    "bearer_token",
    "password",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "account_id",
    "account_ids",
    "acct_id",
    "open_id",
    "open_ids",
    "openid",
    "union_id",
    "union_ids",
    "unionid",
    "user_id",
    "user_ids",
    "userid",
    "uid",
    "uids",
    "phone",
    "phone_number",
    "phone_numbers",
    "mobile",
    "mobile_phone",
    "address",
    "addresses",
    "addr",
}
SENSITIVE_KEY_SUFFIXES = (
    "_api_key",
    "_secret",
    "_password",
    "_token",
    "_account_id",
    "_account_ids",
    "_open_id",
    "_open_ids",
    "_union_id",
    "_union_ids",
    "_user_id",
    "_user_ids",
    "_phone",
    "_phone_number",
    "_phone_numbers",
    "_address",
    "_addresses",
)

SENSITIVE_ENV_NAME_PATTERN = re.compile(
    r"\b[A-Z][A-Z0-9_]*(API_KEY|TOKEN|SECRET|PASSWORD)[A-Z0-9_]*\b"
)
SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9._-]{8,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"(?i)\b(api[_-]?key|authorization|secret|password|access[_-]?token|"
        r"refresh[_-]?token|token)\b\s*[:=]\s*[^,\s;]+"
    ),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]+"),
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b"),
    re.compile(
        r"(?i)\b(account[_-]?id|acct[_-]?id|open[_-]?id|openid|union[_-]?id|"
        r"unionid|user[_-]?id|userid|uid)\b\s*[:=]\s*[A-Za-z0-9._:-]{4,}"
    ),
    re.compile(r"(账号|账户|用户ID|用户编号)\s*[:：=]\s*[\w.\-:]{4,}"),
    re.compile(r"(?i)\b(address|addr)\b\s*[:=]\s*[^,;\n]+"),
    re.compile(r"(地址|住址|收货地址)\s*[:：=]\s*[^,，;；\n]+"),
    re.compile(
        r"[\u4e00-\u9fff]{2,}(?:自治区|自治州|省|市|区|县)"
        r"[\u4e00-\u9fffA-Za-z0-9#_.\-]{0,40}"
        r"(?:路|街|道|巷|弄|小区|村|镇|号|栋|幢|单元|室)"
        r"[\u4e00-\u9fffA-Za-z0-9#_.\-号栋幢单元室楼层座路街道巷弄小区村镇]*"
    ),
)


def redact_sensitive_text(
    value: str,
    *,
    replacement: str = REDACTION_TEXT,
    extra_values: Iterable[str] = (),
) -> str:
    redacted = SENSITIVE_ENV_NAME_PATTERN.sub(replacement, value)
    for secret_value in extra_values:
        if secret_value:
            redacted = redacted.replace(secret_value, replacement)
    for pattern in SENSITIVE_TEXT_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_sensitive_value(
    value: Any,
    *,
    replacement: str = REDACTION_TEXT,
    redact_key_names: bool = False,
    extra_values: Iterable[str] = (),
    depth: int = 0,
) -> Any:
    if depth > 8:
        return replacement
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if is_sensitive_key(key_text):
                safe_key = REDACTED_KEY if redact_key_names else key_text
                redacted[safe_key] = replacement
            else:
                redacted[key_text] = redact_sensitive_value(
                    item,
                    replacement=replacement,
                    redact_key_names=redact_key_names,
                    extra_values=extra_values,
                    depth=depth + 1,
                )
        return redacted
    if isinstance(value, list | tuple):
        return [
            redact_sensitive_value(
                item,
                replacement=replacement,
                redact_key_names=redact_key_names,
                extra_values=extra_values,
                depth=depth + 1,
            )
            for item in value
        ]
    if isinstance(value, str):
        return redact_sensitive_text(
            value,
            replacement=replacement,
            extra_values=extra_values,
        )
    return value


def contains_sensitive_text(value: str) -> bool:
    if SENSITIVE_ENV_NAME_PATTERN.search(value):
        return True
    return any(pattern.search(value) for pattern in SENSITIVE_TEXT_PATTERNS)


def is_sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return normalized in SENSITIVE_KEY_NAMES or any(
        normalized.endswith(suffix) for suffix in SENSITIVE_KEY_SUFFIXES
    )
