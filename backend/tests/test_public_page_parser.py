from datetime import UTC, datetime

from app.schemas import PublicPageSnapshot
from app.services.public_page_parser import parse_public_page_snapshot

NOW = datetime(2026, 6, 9, 10, 0, tzinfo=UTC)


def _snapshot(html: str) -> PublicPageSnapshot:
    return PublicPageSnapshot(
        url="https://example.com/product",
        domain="example.com",
        http_status=200,
        access_time=NOW,
        metadata={"html_text": html},
    )


def test_parser_extracts_title_price_main_image_specs_and_selling_points() -> None:
    html = """
    <html>
      <head>
        <title>Automatic Litter Box Pro</title>
        <meta property="og:image" content="https://example.com/image.jpg" />
        <script type="application/ld+json">
        {
          "@type": "Product",
          "name": "Automatic Litter Box Pro",
          "brand": {"name": "PetLab"},
          "description": "Self-cleaning and odor control",
          "image": "https://example.com/main.jpg",
          "sku": "ALB-PRO",
          "offers": {"price": "1999", "priceCurrency": "CNY"}
        }
        </script>
      </head>
      <body>selling point: quiet motor; spec: 65L capacity; price: CNY 1999</body>
    </html>
    """

    parsed = parse_public_page_snapshot(_snapshot(html))
    fields_by_name = {field.field_name for field in parsed.extracted_fields}

    assert parsed.snapshot.title == "Automatic Litter Box Pro"
    assert parsed.snapshot.parse_status == "parsed"
    assert {"title", "price", "main_image_url", "specification", "selling_point"}.issubset(
        fields_by_name
    )
    assert all(field.source_snippet for field in parsed.extracted_fields)


def test_parser_does_not_create_fake_fields_when_page_has_no_facts() -> None:
    parsed = parse_public_page_snapshot(_snapshot("<html><body>    </body></html>"))

    assert parsed.extracted_fields == []
    assert parsed.snapshot.parse_status == "no_extractable_fields"
    assert parsed.unavailable_reason == "no_extractable_fields"


def test_parser_payload_omits_raw_html() -> None:
    from app.services.public_page_parser import parsed_public_page_payload

    parsed = parse_public_page_snapshot(_snapshot("<title>Safe Title</title>"))
    payload = parsed_public_page_payload(parsed)

    assert "html_text" not in payload["snapshot"]["metadata"]
