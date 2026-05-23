# Demo SKU Snapshot Contract

`demo_sku_snapshot.json` is the final MVP snapshot contract for the automatic cat litter box demo. It is derived from the user-provided desensitized materials in `data/raw/` and replaces `sku_catalog_draft.json` as the input contract for later backend loading work.

## File Shape

Top-level fields:

1. `snapshot_version`: Contract version.
2. `category`: MVP category, fixed to smart pet hardware.
3. `subcategory`: MVP subcategory, fixed to automatic cat litter box.
4. `default_target_sku_id`: Default demo target SKU.
5. `qa_revision_fixture`: The intentionally incomplete evidence case for QA rollback demo.
6. `skus`: Final SKU list.

Each SKU must include:

1. `sku_id`
2. `product_id`
3. `role`
4. `name`
5. `brand`
6. `product_type`
7. `price`
8. `selling_points`
9. `review_summary`
10. `source`

The `source` object must include source URL, raw material directory, source description, limitations, access time, and screenshot path. The one SKU named in `qa_revision_fixture.sku_id` is allowed to miss the fixture field intentionally.

## QA Fixture

`sku_01` intentionally omits `source.access_time` in the final snapshot. The original source value is preserved under `qa_revision_fixture.repair_evidence.access_time` so later QA and Collection steps can demonstrate evidence completion without inventing data.

## Boundaries

This file defines and validates the final snapshot format only. Snapshot Loader implementation belongs to step 07 and must not be added as part of step 06.
