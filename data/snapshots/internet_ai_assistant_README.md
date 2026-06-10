# Internet AI Assistant Snapshot Contract

`internet_ai_assistant_snapshot.json` is the first local snapshot for the ByteDance internet product migration demo. It targets Doubao as the ByteDance product and compares it with Kimi, DeepSeek, Qianwen, and Tencent Yuanbao.

## Source Boundary

The snapshot is generated from public official entry pages only. It does not bypass login, captcha, risk control, paywalls, or private pages. The raw HTML, visible text, crawl metadata, and homepage screenshots are stored under:

```text
data/raw/internet_ai_assistant/
```

## File Shape

Top-level fields:

1. `snapshot_version`
2. `generated_at`
3. `domain_key`
4. `category`
5. `subcategory`
6. `default_target_product_id`
7. `qa_revision_fixture`
8. `products`
9. `crawl_summary`

Each product includes:

1. `sku_id`
2. `product_id`
3. `role`
4. `name`
5. `brand`
6. `product_type`
7. `positioning`
8. `target_users`
9. `core_scenarios`
10. `feature_modules`
11. `pricing`
12. `platforms`
13. `official_urls`
14. `screenshots`
15. `source`
16. `evidence_items`

## QA Fixture

`ev_ip_kimi_homepage` intentionally omits `screenshot_path` in the Evidence item, while `data/raw/internet_ai_assistant/kimi/homepage.png` exists. This supports a reproducible QA rollback demo:

1. QA detects a key official-page Evidence without screenshot path.
2. QA sends a `revision_request` to Collection.
3. Collection fills the missing screenshot path from `qa_revision_fixture.repair_evidence`.
4. Trace shows the before/after Evidence diff.

## Known Gaps

The first crawl does not fully verify pricing, app store ratings, download counts, model capability rankings, logged-in workflows, or enterprise/privacy details. These fields must remain `暂无可靠数据` or `建议复核` unless later evidence is added.
