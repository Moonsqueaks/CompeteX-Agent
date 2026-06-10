import json
import re
from html import unescape
from html.parser import HTMLParser
from typing import Any

from app.schemas import ConfidenceLevel, ExtractedField, PublicPageSnapshot
from app.schemas.common import JsonObject

MAX_FIELD_VALUE_CHARS = 260
MAX_SNIPPET_CHARS = 180


class PublicPageParseError(Exception):
    def __init__(self, code: str, message: str, details: JsonObject | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class ParsedPublicPage:
    def __init__(
        self,
        *,
        snapshot: PublicPageSnapshot,
        extracted_fields: list[ExtractedField],
        unavailable_reason: str | None = None,
    ) -> None:
        self.snapshot = snapshot
        self.extracted_fields = extracted_fields
        self.unavailable_reason = unavailable_reason


def parse_public_page_snapshot(snapshot: PublicPageSnapshot) -> ParsedPublicPage:
    html_text = snapshot.metadata.get("html_text")
    if not isinstance(html_text, str) or not html_text.strip():
        raise PublicPageParseError(
            "missing_html_text",
            "Public page snapshot does not contain parseable HTML text.",
            {"url": snapshot.url},
        )

    document = _HTMLDocument()
    document.feed(html_text)
    visible_text = " ".join(document.visible_text.split())
    fields = _dedupe_fields(
        [
            *_title_fields(document),
            *_meta_fields(document),
            *_json_ld_fields(document.json_ld_objects),
            *_text_pattern_fields(visible_text),
        ]
    )
    parsed_snapshot = snapshot.model_copy(
        update={
            "title": _first_field_value(fields, "title"),
            "text_summary": _shorten(visible_text, 320) if visible_text else snapshot.text_summary,
            "parse_status": "parsed" if fields else "no_extractable_fields",
        }
    )
    return ParsedPublicPage(
        snapshot=parsed_snapshot,
        extracted_fields=fields,
        unavailable_reason=None if fields else "no_extractable_fields",
    )


def parsed_public_page_payload(parsed: ParsedPublicPage) -> JsonObject:
    snapshot_payload = parsed.snapshot.model_dump(mode="json")
    metadata = dict(snapshot_payload.get("metadata", {}))
    metadata.pop("html_text", None)
    snapshot_payload["metadata"] = metadata
    return {
        "snapshot": snapshot_payload,
        "extracted_fields": [
            field.model_dump(mode="json") for field in parsed.extracted_fields
        ],
        "unavailable_reason": parsed.unavailable_reason,
    }


class _HTMLDocument(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.meta: dict[str, str] = {}
        self.json_ld_objects: list[Any] = []
        self.visible_text_parts: list[str] = []
        self._capture_title = False
        self._capture_json_ld = False
        self._title_parts: list[str] = []
        self._json_ld_parts: list[str] = []
        self._ignored_depth = 0

    @property
    def visible_text(self) -> str:
        return " ".join(self.visible_text_parts)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        if tag in {"script", "style", "noscript"}:
            if (
                tag == "script"
                and attrs_dict.get("type", "").lower() == "application/ld+json"
            ):
                self._capture_json_ld = True
                self._json_ld_parts = []
            else:
                self._ignored_depth += 1
            return
        if tag == "title":
            self._capture_title = True
            self._title_parts = []
            return
        if tag == "meta":
            key = (
                attrs_dict.get("property")
                or attrs_dict.get("name")
                or attrs_dict.get("itemprop")
            ).strip().lower()
            content = attrs_dict.get("content", "").strip()
            if key and content:
                self.meta[key] = content

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"}:
            if self._capture_json_ld and tag == "script":
                raw = "".join(self._json_ld_parts).strip()
                self._capture_json_ld = False
                self._json_ld_parts = []
                if raw:
                    self.json_ld_objects.extend(_load_json_ld(raw))
            elif self._ignored_depth:
                self._ignored_depth -= 1
            return
        if tag == "title" and self._capture_title:
            self.title = " ".join("".join(self._title_parts).split())
            self._capture_title = False
            self._title_parts = []

    def handle_data(self, data: str) -> None:
        if self._capture_json_ld:
            self._json_ld_parts.append(data)
            return
        if self._ignored_depth:
            return
        if self._capture_title:
            self._title_parts.append(data)
        stripped = data.strip()
        if stripped:
            self.visible_text_parts.append(stripped)


def _title_fields(document: _HTMLDocument) -> list[ExtractedField]:
    if not document.title:
        return []
    return [
        _field(
            "title",
            document.title,
            document.title,
            "html_title",
            ConfidenceLevel.HIGH,
            "Title is taken from the public page <title> tag.",
        )
    ]


def _meta_fields(document: _HTMLDocument) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    meta_map = {
        "og:title": "title",
        "twitter:title": "title",
        "description": "selling_point",
        "og:description": "selling_point",
        "twitter:description": "selling_point",
        "og:image": "main_image_url",
        "twitter:image": "main_image_url",
        "product:price:amount": "price",
        "og:price:amount": "price",
    }
    for key, field_name in meta_map.items():
        value = document.meta.get(key)
        if value:
            fields.append(
                _field(
                    field_name,
                    value,
                    value,
                    f"meta:{key}",
                    (
                        ConfidenceLevel.MEDIUM
                        if field_name == "selling_point"
                        else ConfidenceLevel.HIGH
                    ),
                    "Extracted from explicit public page metadata.",
                )
            )
    return fields


def _json_ld_fields(objects: list[Any]) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    for item in _flatten_json_ld(objects):
        if not isinstance(item, dict):
            continue
        name = _string_value(item.get("name"))
        image = _image_value(item.get("image"))
        description = _string_value(item.get("description"))
        brand = _brand_value(item.get("brand"))
        offers = item.get("offers")
        price = _price_from_offers(offers)
        specs = _spec_fields_from_json_ld(item)
        if name:
            fields.append(
                _field(
                    "title",
                    name,
                    name,
                    "json_ld:name",
                    ConfidenceLevel.HIGH,
                    "Extracted from JSON-LD name.",
                )
            )
        if brand:
            fields.append(
                _field(
                    "brand",
                    brand,
                    brand,
                    "json_ld:brand",
                    ConfidenceLevel.MEDIUM,
                    "Extracted from JSON-LD brand.",
                )
            )
        if image:
            fields.append(
                _field(
                    "main_image_url",
                    image,
                    image,
                    "json_ld:image",
                    ConfidenceLevel.HIGH,
                    "Extracted from JSON-LD image.",
                )
            )
        if description:
            fields.append(
                _field(
                    "selling_point",
                    description,
                    description,
                    "json_ld:description",
                    ConfidenceLevel.MEDIUM,
                    "Extracted from JSON-LD description.",
                )
            )
        if price:
            fields.append(
                _field(
                    "price",
                    price,
                    json.dumps(offers, ensure_ascii=False),
                    "json_ld:offers.price",
                    ConfidenceLevel.HIGH,
                    "Price is only recorded because it is explicit in JSON-LD offers.",
                )
            )
        fields.extend(specs)
    return fields


def _text_pattern_fields(visible_text: str) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    price_match = re.search(
        (
            r"(?:\u00a5|\uffe5|CNY|RMB|\$)\s?[\d,]+(?:\.\d{1,2})?"
            r"|[\d,]+(?:\.\d{1,2})?\s?(?:\u5143|yuan)"
        ),
        visible_text,
        flags=re.IGNORECASE,
    )
    if price_match:
        value = price_match.group(0)
        fields.append(
            _field(
                "price",
                value,
                _snippet_around(visible_text, price_match.start(), price_match.end()),
                "visible_text:price_pattern",
                ConfidenceLevel.MEDIUM,
                (
                    "Price-like text was explicitly visible on the public page; currency "
                    "and promotion context may be incomplete."
                ),
            )
        )

    for label, field_name in (
        ("\u5356\u70b9", "selling_point"),
        ("\u4eae\u70b9", "selling_point"),
        ("selling point", "selling_point"),
        ("highlight", "selling_point"),
        ("\u89c4\u683c", "specification"),
        ("\u53c2\u6570", "specification"),
        ("\u5c3a\u5bf8", "specification"),
        ("spec", "specification"),
    ):
        pattern = rf"{label}[:\uff1a]\s*([^\u3002\uff1b;\n]{{2,120}})"
        for match in re.finditer(pattern, visible_text):
            fields.append(
                _field(
                    field_name,
                    match.group(1),
                    _snippet_around(visible_text, match.start(), match.end()),
                    f"visible_text:{label}",
                    ConfidenceLevel.MEDIUM,
                    "Field was extracted from explicit visible label text.",
                )
            )
    return fields


def _spec_fields_from_json_ld(item: dict[str, Any]) -> list[ExtractedField]:
    fields: list[ExtractedField] = []
    for key in ("sku", "model", "color", "size", "material"):
        value = _string_value(item.get(key))
        if value:
            fields.append(
                _field(
                    "specification",
                    f"{key}: {value}",
                    f"{key}: {value}",
                    f"json_ld:{key}",
                    ConfidenceLevel.MEDIUM,
                    "Extracted from explicit JSON-LD specification-like field.",
                )
            )
    return fields


def _load_json_ld(raw: str) -> list[Any]:
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return loaded if isinstance(loaded, list) else [loaded]


def _flatten_json_ld(objects: list[Any]) -> list[Any]:
    flattened: list[Any] = []
    for item in objects:
        if isinstance(item, list):
            flattened.extend(_flatten_json_ld(item))
            continue
        if isinstance(item, dict):
            flattened.append(item)
            graph = item.get("@graph")
            if isinstance(graph, list):
                flattened.extend(_flatten_json_ld(graph))
    return flattened


def _brand_value(value: Any) -> str | None:
    if isinstance(value, dict):
        return _string_value(value.get("name"))
    return _string_value(value)


def _image_value(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip() or None
    if isinstance(value, list):
        for item in value:
            image = _image_value(item)
            if image:
                return image
    if isinstance(value, dict):
        return _string_value(value.get("url"))
    return None


def _price_from_offers(value: Any) -> str | None:
    if isinstance(value, list):
        for item in value:
            price = _price_from_offers(item)
            if price:
                return price
    if not isinstance(value, dict):
        return None
    price = _string_value(value.get("price")) or _string_value(value.get("lowPrice"))
    currency = _string_value(value.get("priceCurrency"))
    if price and currency:
        return f"{price} {currency}"
    return price


def _string_value(value: Any) -> str | None:
    if isinstance(value, int | float):
        return str(value)
    if not isinstance(value, str):
        return None
    stripped = unescape(value).strip()
    return stripped or None


def _field(
    field_name: str,
    value: str,
    source_snippet: str,
    extraction_method: str,
    confidence_level: ConfidenceLevel,
    limitations: str,
) -> ExtractedField:
    return ExtractedField(
        field_name=field_name,
        value=_shorten(value, MAX_FIELD_VALUE_CHARS),
        source_snippet=_shorten(source_snippet, MAX_SNIPPET_CHARS),
        extraction_method=extraction_method,
        confidence_level=confidence_level,
        limitations=limitations,
    )


def _dedupe_fields(fields: list[ExtractedField]) -> list[ExtractedField]:
    deduped: list[ExtractedField] = []
    seen: set[tuple[str, str]] = set()
    for field in fields:
        key = (field.field_name, field.value.strip().lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(field)
    return deduped


def _first_field_value(fields: list[ExtractedField], field_name: str) -> str | None:
    for field in fields:
        if field.field_name == field_name:
            return field.value
    return None


def _snippet_around(text: str, start: int, end: int) -> str:
    snippet_start = max(0, start - 60)
    snippet_end = min(len(text), end + 60)
    return text[snippet_start:snippet_end]


def _shorten(value: str, max_chars: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."


__all__ = [
    "ParsedPublicPage",
    "PublicPageParseError",
    "parse_public_page_snapshot",
    "parsed_public_page_payload",
]
