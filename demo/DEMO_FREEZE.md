# Demo Freeze

## Stable Version

- Freeze date: 2026-05-30
- Demo category: `smart_pet_hardware / automatic_litter_box`
- Snapshot file: `data/snapshots/demo_sku_snapshot.json`
- Snapshot SHA256: `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`
- Stable task input: `demo/stable-demo-input.json`
- Default target SKU: `sku_02`
- QA revision SKU: `sku_01`

## Frozen Demo Input

The stable recording and defense task uses `demo/stable-demo-input.json`.

This input intentionally uses `demo_snapshot` and does not depend on external collection. The optional `snapshot_plus_live` mode remains a recorded enhancement placeholder for the MVP.

## Internet AI Assistant Freeze

- Freeze date: 2026-06-10
- Demo category: `互联网产品 / AI 助手`
- Snapshot file: `data/snapshots/internet_ai_assistant_snapshot.json`
- Snapshot SHA256: `500C9C018CA8E4F0B8413796A5F6DE957735E5626E863C249A464534BC15FD26`
- Stable task input: `demo/internet-ai-assistant-stable-input.json`
- Demo script: `demo/internet-ai-assistant-script.md`
- Data source mode: `builtin_candidates`
- Default target product: `doubao`
- Core competitors: Kimi, DeepSeek, 千问, 腾讯元宝
- QA revision evidence: `ev_ip_kimi_homepage`

The internet-product demo intentionally uses the local AI assistant candidate pool. It does not call search engines and does not add products outside the frozen candidate pool. Candidate loading is only a controlled starting set; final conclusions still require Evidence, Analysis, QA and Writer output.

The reproducible internet QA revision case is fixed in the snapshot:

1. The first QA pass creates `CRITICAL_EVIDENCE_MISSING_SCREENSHOT` for `ev_ip_kimi_homepage`.
2. Collection repairs the missing screenshot into `ev_ip_kimi_homepage_repair_001`.
3. Analysis recomputes the affected Claim and CompetitionEdge.
4. Final QA status is passed, with one resolved review task and zero open review tasks.
5. Trace shows candidate-pool metadata, `collection_agent_repair` and `analysis_agent_recompute` diff records.

## Frozen QA Revision Case

The reproducible QA revision case is fixed in the snapshot:

- `qa_revision_fixture.sku_id`: `sku_01`
- Missing field: `source.access_time`
- Repair evidence access time: `2026-05-23T16:00:59+08:00`
- Repair screenshot path: `data/raw/sku_01/QQ图片20260523155546.jpg`

## 2.0 Demo Path

Manual startup and acceptance steps are documented in `memory-bank/manual-runbook.md`.

The expected 2.0 demo path is:

1. Start the stable task from the input page.
2. The frontend redirects to `/overview?task_id=<task_id>`.
3. The overview shows a one-sentence judgment, decision usability, key competitors, first action, opportunities, risks and analysis scope.
4. The battlefield page shows the relationship graph, key relations, decision chain, evidence cards and resolved QA repair summary.
5. The profile page shows the target product and core competitor comparison plus controlled Human Review entry.
6. The report page shows eight 2.0 sections and offers Word `.docx` download, browser print and print-view mode.
7. The evidence and process tracking page shows evidence chains, quality records, agent process details and diffs.
8. The report page must not show a Markdown export button, and `GET /tasks/{task_id}/report/markdown` remains unavailable.

## Frozen QA Revision Case

The reproducible QA revision case remains fixed in the snapshot:

1. The first QA pass creates `TIMELY_EVIDENCE_MISSING_ACCESS_TIME`.
2. Collection repairs `ev_sku_01` into `ev_sku_01_repair_001`.
3. Analysis recomputes the affected Claim and CompetitionEdge.
4. Final QA status is passed, with one resolved review task and zero open review tasks.
5. Trace shows `collection_agent_repair` and `analysis_agent_recompute` diff records.

## 2.0 Acceptance Checks

1. `POST /tasks` with `demo/stable-demo-input.json` completes without external collection.
2. `GET /tasks/{task_id}/overview` returns the PM-readable overview and does not require frontend stitching from old endpoints.
3. `GET /tasks/{task_id}/battlefield` returns graph nodes, graph edges, key relations, evidence cards and QA summary.
4. `GET /tasks/{task_id}/profile` returns horizontal comparison data and evidence summaries.
5. `GET /tasks/{task_id}/report` returns the eight-section 2.0 web report.
6. `GET /tasks/{task_id}/report/docx` returns a readable Word `.docx` file whose bytes start with `PK`.
7. `GET /tasks/{task_id}/trace` returns evidence chains, quality records, process data and diffs.
8. Exported reports, Trace, logs, screenshots and error responses must not contain API keys, tokens, phone numbers, account IDs or addresses.
9. No Redis, Celery, PostgreSQL, Next.js, Redux, Tailwind, external live collection, microservices or backend PDF service is required for the demo.

## Change Control

Do not edit the frozen snapshot, default target, QA revision fixture, or stable task input casually. If any of them must change, update this file, the SHA256 value, and the regression tests in the same change.
