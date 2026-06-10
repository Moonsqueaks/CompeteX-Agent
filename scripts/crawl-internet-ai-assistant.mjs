import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(__dirname, "..");
const playwrightModule = path.join(
  projectRoot,
  "frontend",
  "node_modules",
  "playwright",
  "index.mjs",
);
const { chromium } = await import(pathToFileURL(playwrightModule).href);
const rawRoot = path.join(projectRoot, "data", "raw", "internet_ai_assistant");
const snapshotPath = path.join(
  projectRoot,
  "data",
  "snapshots",
  "internet_ai_assistant_snapshot.json",
);

const products = [
  {
    slug: "doubao",
    productId: "doubao",
    skuId: "ip_doubao",
    role: "target",
    name: "豆包",
    brand: "字节跳动",
    productType: "general_ai_assistant",
    url: "https://www.doubao.com/chat/",
  },
  {
    slug: "kimi",
    productId: "kimi",
    skuId: "ip_kimi",
    role: "direct_competitor",
    name: "Kimi",
    brand: "月之暗面",
    productType: "general_ai_assistant",
    url: "https://www.kimi.com/",
  },
  {
    slug: "deepseek",
    productId: "deepseek",
    skuId: "ip_deepseek",
    role: "direct_competitor",
    name: "DeepSeek",
    brand: "DeepSeek",
    productType: "general_ai_assistant",
    url: "https://www.deepseek.com/",
  },
  {
    slug: "qianwen",
    productId: "qianwen",
    skuId: "ip_qianwen",
    role: "direct_competitor",
    name: "千问",
    brand: "阿里巴巴",
    productType: "general_ai_assistant",
    url: "https://www.qianwen.com/",
  },
  {
    slug: "yuanbao",
    productId: "yuanbao",
    skuId: "ip_yuanbao",
    role: "direct_competitor",
    name: "腾讯元宝",
    brand: "腾讯",
    productType: "general_ai_assistant",
    url: "https://yuanbao.tencent.com/",
  },
];

const featureTerms = {
  conversation: ["对话", "聊天", "问答", "助手", "assistant", "chat"],
  search_or_research: [
    "搜索",
    "联网",
    "引用",
    "研究",
    "research",
    "deep research",
    "search",
  ],
  document_processing: ["文档", "文件", "PDF", "长文本", "长文", "document", "docs"],
  content_creation: [
    "写作",
    "创作",
    "生成",
    "文案",
    "图片",
    "视频",
    "绘画",
    "image",
    "video",
    "write",
  ],
  coding_or_reasoning: ["代码", "编程", "推理", "数学", "逻辑", "code", "coding", "reason"],
  multimodal: ["图片", "语音", "视频", "视觉", "多模态", "image", "voice", "video", "vision"],
  agent_or_workflow: ["智能体", "Agent", "agent", "工作流", "自动化", "workflow"],
  ecosystem_integration: [
    "字节",
    "抖音",
    "剪映",
    "飞书",
    "阿里",
    "腾讯",
    "微信",
    "办公",
    "下载",
    "app",
    "ios",
    "android",
    "windows",
    "mac",
  ],
};

const scenarioTerms = {
  日常问答: ["问答", "聊天", "助手", "解答", "assistant", "chat"],
  长文档研究: ["长文", "文档", "PDF", "文件", "研究", "research", "document"],
  内容创作: ["写作", "创作", "文案", "图片", "视频", "生成", "image", "video", "write"],
  编程推理: ["代码", "编程", "推理", "数学", "逻辑", "code", "reason"],
  办公协作: ["办公", "表格", "PPT", "会议", "协作", "office", "docs"],
  多模态创作: ["图片", "语音", "视频", "视觉", "多模态", "vision", "voice"],
};

const userTerms = {
  学生: ["学生", "学习", "作业", "考试", "课程"],
  知识工作者: ["办公", "文档", "研究", "总结", "报告", "工作"],
  内容创作者: ["创作", "写作", "文案", "图片", "视频", "脚本"],
  开发者: ["代码", "编程", "开发", "API", "developer", "code"],
  企业团队: ["企业", "团队", "协作", "办公", "安全", "管理"],
};

function isoWithChinaOffset(date) {
  const offsetMs = 8 * 60 * 60 * 1000;
  const shifted = new Date(date.getTime() + offsetMs);
  return `${shifted.toISOString().replace("Z", "")}+08:00`;
}

function compactText(value, limit = 12000) {
  return String(value || "")
    .replace(/\u00a0/g, " ")
    .replace(/[ \t]+\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim()
    .slice(0, limit);
}

function containsAny(text, terms) {
  const lowered = text.toLowerCase();
  return terms.some((term) => lowered.includes(term.toLowerCase()));
}

function snippetsFor(text, terms, maxItems = 4) {
  const normalized = compactText(text, 50000);
  const snippets = [];
  const lowered = normalized.toLowerCase();
  for (const term of terms) {
    const index = lowered.indexOf(term.toLowerCase());
    if (index === -1) {
      continue;
    }
    const start = Math.max(0, index - 60);
    const end = Math.min(normalized.length, index + term.length + 100);
    const snippet = normalized.slice(start, end).replace(/\s+/g, " ").trim();
    if (snippet && !snippets.includes(snippet)) {
      snippets.push(snippet);
    }
    if (snippets.length >= maxItems) {
      break;
    }
  }
  return snippets;
}

function deriveFeatureModules(text) {
  return Object.fromEntries(
    Object.entries(featureTerms).map(([axis, terms]) => [axis, snippetsFor(text, terms)]),
  );
}

function deriveListByTerms(text, mapping, fallback) {
  const values = Object.entries(mapping)
    .filter(([, terms]) => containsAny(text, terms))
    .map(([label]) => label);
  return values.length ? values : fallback;
}

function derivePlatforms(text) {
  const platforms = ["web"];
  const checks = [
    ["ios", ["iOS", "App Store", "iPhone"]],
    ["android", ["Android", "安卓", "应用宝"]],
    ["windows", ["Windows", "Win"]],
    ["macos", ["macOS", "Mac"]],
    ["wechat_or_mini_program", ["微信", "小程序"]],
  ];
  for (const [platform, terms] of checks) {
    if (containsAny(text, terms)) {
      platforms.push(platform);
    }
  }
  return [...new Set(platforms)];
}

function derivePositioning(product, crawl) {
  const candidates = [
    crawl.meta.description,
    crawl.meta.ogDescription,
    crawl.meta.ogTitle,
    crawl.title,
    ...crawl.visibleText
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length >= 8 && line.length <= 90),
  ].filter(Boolean);
  const first = candidates.find((item) => !/captcha|验证码|登录后/i.test(item));
  return first || `${product.name} 官方公开页面未提取到明确定位文案`;
}

function derivePricing(text) {
  const priceSnippet = snippetsFor(text, ["价格", "会员", "订阅", "免费", "¥", "$", "pricing"], 2);
  return {
    currency: "CNY",
    pricing_band: "unknown",
    list_price: null,
    final_price: null,
    pricing_note: priceSnippet.length
      ? `官方公开页出现价格/付费相关文本，需人工复核：${priceSnippet.join("；")}`
      : "暂无可靠定价数据；本次仅采集官方公开入口页面，未确认独立定价页。",
    evidence_snippets: priceSnippet,
  };
}

function buildEvidence(product, crawl, accessTime, screenshotPathForEvidence, missingFields) {
  const metadata = {
    page_title: crawl.title,
    meta_description: crawl.meta.description || null,
    og_title: crawl.meta.ogTitle || null,
    og_description: crawl.meta.ogDescription || null,
    feature_modules: deriveFeatureModules(crawl.visibleText),
    platforms: derivePlatforms(crawl.visibleText),
    pricing: derivePricing(crawl.visibleText),
    crawl_status: crawl.status,
    html_path: `data/raw/internet_ai_assistant/${product.slug}/homepage.html`,
    text_path: `data/raw/internet_ai_assistant/${product.slug}/visible_text.txt`,
    missing_fields: missingFields,
  };
  return {
    evidence_id: `ev_ip_${product.slug}_homepage`,
    product_id: product.productId,
    source_type: "official_product_page",
    source_url: product.url,
    screenshot_path: screenshotPathForEvidence,
    access_time: accessTime,
    content_summary: [
      `${product.name} 官方公开页面：${derivePositioning(product, crawl)}`,
      `可见功能线索：${Object.entries(metadata.feature_modules)
        .filter(([, items]) => items.length)
        .map(([axis]) => axis)
        .join("、") || "暂无可靠数据"}`,
    ].join("；"),
    confidence_level: crawl.ok ? "medium" : "low",
    limitations:
      "来源为官方公开入口页的自动化快照；动态渲染、登录后功能、付费信息和应用商店信息可能未完整覆盖。",
    metadata,
  };
}

function buildProductSnapshot(product, crawl, accessTime, screenshotPath, evidence) {
  const fullText = crawl.visibleText;
  const featureModules = deriveFeatureModules(fullText);
  return {
    sku_id: product.skuId,
    product_id: product.productId,
    role: product.role,
    name: product.name,
    brand: product.brand,
    product_type: product.productType,
    positioning: derivePositioning(product, crawl),
    target_users: deriveListByTerms(fullText, userTerms, ["暂无可靠数据"]),
    core_scenarios: deriveListByTerms(fullText, scenarioTerms, ["暂无可靠数据"]),
    feature_modules: featureModules,
    pricing: derivePricing(fullText),
    platforms: derivePlatforms(fullText),
    official_urls: [
      product.url,
      ...crawl.links
        .filter((link) => link.href && link.href.startsWith(new URL(product.url).origin))
        .map((link) => link.href),
    ].slice(0, 12),
    screenshots: screenshotPath ? [screenshotPath] : [],
    source: {
      platform: "official_web",
      source_url: product.url,
      raw_dir: `data/raw/internet_ai_assistant/${product.slug}`,
      screenshot_path: screenshotPath,
      access_time: accessTime,
      source_description: "官方公开入口页自动化快照",
      limitations:
        "仅采集无登录公开页面；若页面依赖客户端渲染、登录或地域策略，部分功能、定价、平台入口可能缺失。",
    },
    evidence_items: [evidence],
  };
}

async function crawlProduct(browser, product, accessTime) {
  const productDir = path.join(rawRoot, product.slug);
  await fs.mkdir(productDir, { recursive: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1200 },
    locale: "zh-CN",
    userAgent:
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  });
  const startedAt = isoWithChinaOffset(new Date());
  let responseStatus = null;
  let error = null;
  try {
    const response = await page.goto(product.url, {
      waitUntil: "domcontentloaded",
      timeout: 35000,
    });
    responseStatus = response?.status() ?? null;
    await page.waitForTimeout(4500);
  } catch (caught) {
    error = caught instanceof Error ? caught.message : String(caught);
  }

  const title = await page.title().catch(() => "");
  const meta = await page
    .evaluate(() => {
      const metaContent = (selector) =>
        document.querySelector(selector)?.getAttribute("content")?.trim() || "";
      return {
        description: metaContent('meta[name="description"]'),
        keywords: metaContent('meta[name="keywords"]'),
        ogTitle: metaContent('meta[property="og:title"]'),
        ogDescription: metaContent('meta[property="og:description"]'),
      };
    })
    .catch(() => ({ description: "", keywords: "", ogTitle: "", ogDescription: "" }));
  const visibleText = await page
    .locator("body")
    .innerText({ timeout: 8000 })
    .then((text) => compactText(text, 20000))
    .catch(() => "");
  const links = await page
    .evaluate(() =>
      Array.from(document.querySelectorAll("a"))
        .map((anchor) => ({
          text: anchor.textContent?.replace(/\s+/g, " ").trim().slice(0, 120) || "",
          href: anchor.href || "",
        }))
        .filter((link) => link.href),
    )
    .catch(() => []);
  const html = await page.content().catch(() => "");

  const htmlPath = path.join(productDir, "homepage.html");
  const textPath = path.join(productDir, "visible_text.txt");
  const crawlPath = path.join(productDir, "crawl.json");
  const screenshotFilePath = path.join(productDir, "homepage.png");
  let screenshotPath = null;
  let screenshotError = null;
  try {
    await page.screenshot({ path: screenshotFilePath, fullPage: true, timeout: 20000 });
    screenshotPath = `data/raw/internet_ai_assistant/${product.slug}/homepage.png`;
  } catch (caught) {
    screenshotError = caught instanceof Error ? caught.message : String(caught);
  }
  await page.close().catch(() => undefined);

  const crawl = {
    product_id: product.productId,
    name: product.name,
    url: product.url,
    started_at: startedAt,
    access_time: accessTime,
    status: responseStatus,
    ok: responseStatus !== null && responseStatus >= 200 && responseStatus < 400 && !error,
    error,
    title,
    meta,
    visibleText,
    links,
    screenshot_path: screenshotPath,
    screenshot_error: screenshotError,
  };
  await fs.writeFile(htmlPath, html, "utf8");
  await fs.writeFile(textPath, visibleText, "utf8");
  await fs.writeFile(crawlPath, JSON.stringify(crawl, null, 2), "utf8");
  return { crawl, screenshotPath };
}

async function main() {
  await fs.mkdir(rawRoot, { recursive: true });
  await fs.mkdir(path.dirname(snapshotPath), { recursive: true });

  const accessTime = isoWithChinaOffset(new Date());
  const browser = await chromium.launch({ headless: true });
  const snapshots = [];
  const crawlSummary = [];

  try {
    for (const product of products) {
      console.log(`Crawling ${product.name}: ${product.url}`);
      const { crawl, screenshotPath } = await crawlProduct(browser, product, accessTime);
      const isQaFixtureProduct = product.productId === "kimi";
      const evidenceScreenshotPath = isQaFixtureProduct ? null : screenshotPath;
      const missingFields = [];
      if (!evidenceScreenshotPath) {
        missingFields.push("source.screenshot_path");
      }
      if (!crawl.ok) {
        missingFields.push("source.page_fetch");
      }
      const evidence = buildEvidence(
        product,
        crawl,
        accessTime,
        evidenceScreenshotPath,
        missingFields,
      );
      snapshots.push(buildProductSnapshot(product, crawl, accessTime, screenshotPath, evidence));
      crawlSummary.push({
        product_id: product.productId,
        url: product.url,
        status: crawl.status,
        ok: crawl.ok,
        title: crawl.title,
        visible_text_chars: crawl.visibleText.length,
        screenshot_path: screenshotPath,
        evidence_screenshot_path: evidenceScreenshotPath,
        missing_fields: missingFields,
        error: crawl.error,
      });
    }
  } finally {
    await browser.close().catch(() => undefined);
  }

  const snapshot = {
    snapshot_version: "internet_ai_assistant_v1",
    generated_at: accessTime,
    domain_key: "internet_ai_assistant",
    category: "互联网产品",
    subcategory: "AI 助手",
    default_target_product_id: "doubao",
    qa_revision_fixture: {
      product_id: "kimi",
      evidence_id: "ev_ip_kimi_homepage",
      missing_fields: ["source.screenshot_path"],
      repair_evidence: {
        screenshot_path: "data/raw/internet_ai_assistant/kimi/homepage.png",
        source_note: "本地公开页截图已采集；快照中故意留空用于 QA 打回补齐演示。",
      },
    },
    products: snapshots,
    crawl_summary: crawlSummary,
  };

  await fs.writeFile(snapshotPath, JSON.stringify(snapshot, null, 2), "utf8");
  await fs.writeFile(
    path.join(rawRoot, "crawl_summary.json"),
    JSON.stringify(crawlSummary, null, 2),
    "utf8",
  );
  console.log(`Wrote ${snapshotPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
