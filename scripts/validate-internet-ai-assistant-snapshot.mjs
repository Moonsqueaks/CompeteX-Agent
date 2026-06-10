import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const snapshotPath = path.join(
  projectRoot,
  "data",
  "snapshots",
  "internet_ai_assistant_snapshot.json",
);

const requiredProductIds = ["doubao", "kimi", "deepseek", "qianwen", "yuanbao"];
const sensitivePatterns = [
  /sk-[A-Za-z0-9_-]{20,}/,
  /api[_-]?key["'\s:=]+[A-Za-z0-9_-]{12,}/i,
  /authorization["'\s:=]+bearer/i,
  /cookie["'\s:=]+[^,"\n]{20,}/i,
  /1[3-9]\d{9}/,
];

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function collectEvidence(products) {
  return products.flatMap((product) =>
    (product.evidence_items || []).map((evidence) => ({ product, evidence })),
  );
}

async function pathExists(projectRelativePath) {
  if (!projectRelativePath) {
    return false;
  }
  try {
    const stat = await fs.stat(path.join(projectRoot, projectRelativePath));
    return stat.isFile() || stat.isDirectory();
  } catch {
    return false;
  }
}

async function main() {
  const raw = await fs.readFile(snapshotPath, "utf8");
  for (const pattern of sensitivePatterns) {
    assert(!pattern.test(raw), `Sensitive-looking pattern found: ${pattern}`);
  }
  const snapshot = JSON.parse(raw);
  assert(snapshot.domain_key === "internet_ai_assistant", "domain_key mismatch");
  assert(snapshot.default_target_product_id === "doubao", "default target must be doubao");
  assert(Array.isArray(snapshot.products), "products must be an array");
  assert(snapshot.products.length >= 5, "snapshot must include at least 5 products");

  const productIds = snapshot.products.map((product) => product.product_id);
  for (const productId of requiredProductIds) {
    assert(productIds.includes(productId), `missing product: ${productId}`);
  }

  const targetProducts = snapshot.products.filter((product) => product.role === "target");
  assert(targetProducts.length === 1, "snapshot must include exactly one target");
  assert(targetProducts[0].product_id === "doubao", "target product must be doubao");

  const gaps = [];
  const evidenceItems = collectEvidence(snapshot.products);
  assert(evidenceItems.length >= 5, "each product should have evidence");

  for (const product of snapshot.products) {
    assert(product.name, `missing name for ${product.product_id}`);
    assert(product.source?.source_url, `missing source URL for ${product.product_id}`);
    assert(product.source?.access_time, `missing access_time for ${product.product_id}`);
    assert(
      Array.isArray(product.evidence_items) && product.evidence_items.length > 0,
      `missing evidence_items for ${product.product_id}`,
    );
    if (!(await pathExists(product.source?.raw_dir))) {
      gaps.push(`${product.name}: raw_dir missing or not stored`);
    }
    if (product.source?.screenshot_path && !(await pathExists(product.source.screenshot_path))) {
      gaps.push(`${product.name}: source screenshot path does not exist`);
    }
    if (product.pricing?.pricing_band === "unknown") {
      gaps.push(`${product.name}: pricing/commercial model not verified`);
    }
    if (product.target_users?.includes("暂无可靠数据")) {
      gaps.push(`${product.name}: target users need manual evidence`);
    }
    if (product.core_scenarios?.includes("暂无可靠数据")) {
      gaps.push(`${product.name}: core scenarios need manual evidence`);
    }
  }

  for (const { product, evidence } of evidenceItems) {
    assert(evidence.evidence_id, `missing evidence_id for ${product.product_id}`);
    assert(evidence.product_id === product.product_id, `evidence product mismatch: ${evidence.evidence_id}`);
    assert(evidence.source_url, `missing evidence source_url: ${evidence.evidence_id}`);
    assert(evidence.access_time, `missing evidence access_time: ${evidence.evidence_id}`);
    const missingFields = evidence.metadata?.missing_fields || [];
    if (evidence.screenshot_path && !(await pathExists(evidence.screenshot_path))) {
      gaps.push(`${evidence.evidence_id}: screenshot path does not exist`);
    }
    if (!evidence.screenshot_path && !missingFields.includes("source.screenshot_path")) {
      gaps.push(`${evidence.evidence_id}: screenshot missing without missing_fields marker`);
    }
  }

  const fixture = snapshot.qa_revision_fixture;
  assert(fixture?.product_id === "kimi", "QA fixture should target Kimi");
  assert(
    await pathExists(fixture?.repair_evidence?.screenshot_path),
    "QA repair screenshot must exist",
  );

  const report = {
    status: "ok",
    product_count: snapshot.products.length,
    evidence_count: evidenceItems.length,
    qa_fixture: fixture,
    gaps,
  };
  const reportPath = path.join(
    projectRoot,
    "data",
    "snapshots",
    "internet_ai_assistant_data_quality_report.json",
  );
  await fs.writeFile(reportPath, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
