# Demo Freeze

## Stable Version

- Freeze date: 2026-05-29
- Demo category: `smart_pet_hardware / automatic_litter_box`
- Snapshot file: `data/snapshots/demo_sku_snapshot.json`
- Snapshot SHA256: `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`
- Stable task input: `demo/stable-demo-input.json`
- Default target SKU: `sku_02`
- QA revision SKU: `sku_01`

## Frozen Demo Input

The stable recording and defense task uses `demo/stable-demo-input.json`.

This input intentionally uses `demo_snapshot` and does not depend on external collection. The optional `snapshot_plus_live` mode remains a recorded enhancement placeholder for the MVP.

## Frozen QA Revision Case

The reproducible QA revision case is fixed in the snapshot:

- `qa_revision_fixture.sku_id`: `sku_01`
- Missing field: `source.access_time`
- Repair evidence access time: `2026-05-23T16:00:59+08:00`
- Repair screenshot path: `data/raw/sku_01/QQ图片20260523155546.jpg`

The expected demo path is:

1. Start the stable task from the input page.
2. Trace shows the first QA pass creating `TIMELY_EVIDENCE_MISSING_ACCESS_TIME`.
3. Collection repairs `ev_sku_01` into `ev_sku_01_repair_001`.
4. Analysis recomputes the affected Claim and CompetitionEdge.
5. Final QA status is passed, with one resolved review task and zero open review tasks.
6. Report keeps nine sections and can export Markdown.

## Change Control

Do not edit the frozen snapshot, default target, QA revision fixture, or stable task input casually. If any of them must change, update this file, the SHA256 value, and the regression tests in the same change.
