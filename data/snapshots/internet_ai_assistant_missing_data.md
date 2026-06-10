# Internet AI Assistant Missing Data

Generated after the first official-page crawl on 2026-06-10.

## Collected

The following public official entry pages were fetched successfully with status 200:

| Product | URL | Raw Directory | Screenshot |
|---|---|---|---|
| Doubao | `https://www.doubao.com/chat/` | `data/raw/internet_ai_assistant/doubao/` | `data/raw/internet_ai_assistant/doubao/homepage.png` |
| Kimi | `https://www.kimi.com/` | `data/raw/internet_ai_assistant/kimi/` | `data/raw/internet_ai_assistant/kimi/homepage.png` |
| DeepSeek | `https://www.deepseek.com/` | `data/raw/internet_ai_assistant/deepseek/` | `data/raw/internet_ai_assistant/deepseek/homepage.png` |
| Qianwen | `https://www.qianwen.com/` | `data/raw/internet_ai_assistant/qianwen/` | `data/raw/internet_ai_assistant/qianwen/homepage.png` |
| Tencent Yuanbao | `https://yuanbao.tencent.com/` | `data/raw/internet_ai_assistant/yuanbao/` | `data/raw/internet_ai_assistant/yuanbao/homepage.png` |

The generated snapshot is:

```text
data/snapshots/internet_ai_assistant_snapshot.json
```

The generated quality report is:

```text
data/snapshots/internet_ai_assistant_data_quality_report.json
```

## Intentional QA Fixture

`ev_ip_kimi_homepage` intentionally has `screenshot_path: null` in the Evidence item, although `data/raw/internet_ai_assistant/kimi/homepage.png` exists. This is intentional for the QA rollback demo.

## Missing Or Needs Manual Collection

| Priority | Gap | Why It Matters | Suggested Evidence |
|---|---|---|---|
| P0 | Commercial model / pricing for all five products | Current snapshot only verifies public entry pages, not pricing or membership terms. Reports must not claim free/paid advantages without evidence. | Official pricing page, membership page, API pricing page, or screenshot showing no pricing page is available. |
| P0 | App store ratings, rankings, review counts, and download signals | These are time-sensitive market signals and require access time plus source evidence. | App Store / official app market pages with screenshot and access time. |
| P1 | Logged-in core workflow screenshots | Homepage screenshots prove entry-page capabilities, but not full workflow depth. | Manual screenshots after login if allowed by account policy, with private info removed. |
| P1 | Product help docs or release notes | Helps support feature existence beyond homepage marketing text. | Official docs, help center, changelog, model release page. |
| P1 | Enterprise/privacy/security claims | These are sensitive claims and must be conservative. | Official privacy policy, enterprise security page, terms page, or write `暂无可靠数据`. |
| P2 | User research / interview snippets | Needed for stronger persona and decision-chain analysis. | Desensitized survey/interview summaries. |

## Product-Specific Notes

| Product | Notes |
|---|---|
| Doubao | Homepage text supports AI assistant, writing, translation, programming, PPT generation, and image generation. Pricing is not verified. |
| Kimi | Homepage text supports document, deep research, website, sheet, Agent cluster, Kimi Code, and desktop app signals. Pricing is not verified. |
| DeepSeek | Homepage text supports web, App, API platform, API docs, and API price entry. API price content itself was not crawled in this first pass. |
| Qianwen | Homepage text supports task assistant, thinking/research, video/image generation, PPT, code, translation, writing, and desktop download. Pricing is not verified. |
| Tencent Yuanbao | Homepage text supports AI assistant positioning, Q&A, creation, and download center. Feature detail is sparse and should be supplemented. |
