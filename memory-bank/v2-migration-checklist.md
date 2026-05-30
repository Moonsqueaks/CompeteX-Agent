# 竞品分析系统 2.0 迁移清单

## 1. 清单目的

本文档对应 `memory-bank/v2-implementation-plan.md` 步骤 01，用于把当前 1.0 基线迁移到 2.0 产品经理竞品决策工作台之前的契约边界固定下来。

2.0 不是推翻重做。当前 FastAPI、SQLite、LangGraph、Collection/Analysis/QA/Writer 四 Agent、QA 打回、Trace、Human Review、竞争图谱、产品画像、网页报告和 Demo 冻结能力都作为基线保留。2.0 的目标是新增 PM 可读的总览、解释层、横向对比、证据与过程追踪阅读层和 Word `.docx` 正式交付，并删除用户可见 Markdown 导出。

## 2. 当前 1.0 基线

当前基线来自 `memory-bank/progress.md` 与现有代码：

1. 后端已有 `POST /tasks`、`GET /tasks/{task_id}`、`GET /tasks/{task_id}/profile`、`GET /tasks/{task_id}/battlefield`、`GET /tasks/{task_id}/trace`、`GET /tasks/{task_id}/report`、`GET /tasks/{task_id}/report/markdown` 和 `POST /tasks/{task_id}/feedback`。
2. 前端导航为任务输入、产品画像、竞争图谱、分析报告、过程追踪；创建任务后默认跳转 `/trace?task_id=<task_id>`。
3. 报告导出当前为 Markdown，后端返回 `MarkdownReport` 并保存 `.md` 文件到报告目录。
4. Demo 快照固定为 `data/snapshots/demo_sku_snapshot.json`，稳定输入为 `demo/stable-demo-input.json`，默认目标为 `sku_02`，QA 打回样例为 `sku_01` 缺失 `source.access_time`。
5. `snapshot_plus_live` 仍只是增强模式占位，不做真实外部采集。

## 3. 2.0 页面责任边界

| 页面 | 2.0 责任 | 不承担 |
|---|---|---|
| 竞争态势总览 | 默认落点；展示一句话判断、决策可用状态、分析范围、关键竞品、机会风险、行动建议和下钻入口 | 不从 profile、battlefield、report 临时拼主数据 |
| 竞争图谱 | 默认展示后端筛选的 3 到 5 条关键关系；解释入选理由、威胁等级、PM 关系标签、四段式解释和证据可信状态 | 不把裸竞争分作为默认阅读层核心 |
| 产品与竞品画像 | 横向对比目标产品、最高威胁直接竞品和最高威胁替代竞品；保留受控人工修正 | 不允许自由编辑整份报告或直接改写 Claim 正文 |
| 分析报告 | 展示 2.0 八章节工作台视图、打印视图和 Word 下载入口 | 不展示 Markdown 导出入口，不新增后端 PDF 服务 |
| 证据与过程追踪 | 按证据链、质检记录、智能体过程、差异记录四个 Tab 组织下钻信息 | 不把 Agent Run、Tool Call、Payload 等技术细节放在默认主阅读层 |

## 4. 能力迁移清单

### 4.1 保留能力

1. LangGraph 真实 DAG 与 QA 条件边。
2. Collection、Analysis、QA、Writer 四个主 Agent。
3. 结构化 `AgentMessage`、Artifact、Claim、Evidence、CompetitionEdge、ReviewTask、HumanFeedback。
4. Claim 与 Evidence 绑定，以及缺证据时的风险标记。
5. QA 真实打回、Collection 修复、Analysis 局部重算和 Trace Diff。
6. 有限 Human Review 与 before/after/reason 记录。
7. SQLite 的任务表、Artifact JSON、Trace/日志表、人工反馈表轻量存储方案。
8. 本地 Demo 快照和冻结回归测试。
9. 未配置模型 API Key 时依靠本地快照和规则流程跑通完整 Demo。

### 4.2 新增能力

1. `GET /tasks/{task_id}/overview` 总览 API。
2. 2.0 展示枚举：判断强度、决策可用状态、证据可信状态、威胁等级、PM 关系标签、行动建议优先级和责任类型。
3. 产品主图 URL 派生与可展示缺失状态。
4. 分析范围汇总服务。
5. 关键竞争关系筛选、威胁等级、PM 关系标签和四段式解释。
6. 产品与核心竞品横向画像对比。
7. 2.0 八章节报告数据结构。
8. 简化竞争关系图 PNG 生成。
9. Word `.docx` 导出 Schema、服务和 `GET /tasks/{task_id}/report/docx` API。
10. 导出失败记录进入过程追踪。
11. 证据与过程追踪视图所需的按结论组织证据链、质检记录和业务影响 Diff。
12. 前端 2.0 导航、总览页、术语解释、图谱阅读层、画像对比、报告打印视图和证据过程追踪 Tab。
13. 全站用户可见主界面中文化。

### 4.3 废弃能力

1. 删除用户可见 `GET /tasks/{task_id}/report/markdown` API，不保留兼容路由。
2. 删除前端 Markdown 导出按钮、成功提示和 E2E 覆盖。
3. 报告主章节不再使用 Evidence 索引和 QA 摘要作为独立主章节标题，改入附录。
4. 创建任务后不再默认跳转过程追踪页，改为竞争态势总览页。
5. 主界面不再默认暴露 `Agent`、`Trace`、`Tool Call`、`Payload` 等英文技术词。

## 5. API 迁移清单

| API | 2.0 动作 | 说明 |
|---|---|---|
| `POST /tasks` | 保留并调整前端成功跳转 | 后端任务创建链路不削弱，前端默认进入总览 |
| `GET /tasks/{task_id}` | 保留 | 继续用于状态轮询 |
| `GET /tasks/{task_id}/overview` | 新增 | 返回 PM 可读总览，不让前端拼接旧接口 |
| `GET /tasks/{task_id}/profile` | 升级 | 返回横向对比与图片状态，同时保留画像基础能力 |
| `GET /tasks/{task_id}/battlefield` | 升级 | 增加关键关系、入选理由、威胁等级、标签、四段式解释、应对建议和图片 |
| `GET /tasks/{task_id}/trace` | 升级 | 支撑证据与过程追踪四 Tab，下钻定位和业务影响 Diff |
| `GET /tasks/{task_id}/report` | 升级 | 返回 2.0 八章节报告结构 |
| `GET /tasks/{task_id}/report/markdown` | 删除 | 2.0 不保留用户可见入口或兼容路由 |
| `GET /tasks/{task_id}/report/docx` | 新增 | 返回真实 `.docx` 文件下载响应 |
| `POST /tasks/{task_id}/feedback` | 保留并调整文案 | 继续只允许结构化受控反馈 |

## 6. 前端迁移清单

| 区域 | 新增/调整 | 验收要点 |
|---|---|---|
| 导航 | 调整为竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪 | 创建任务后默认进入总览，跨页保留 `task_id` |
| 总览页 | 新增首屏主判断区、分析范围、关键竞品、机会风险、行动建议、切片联动 | 首屏不滚动可看到核心判断，不是卡片堆砌 |
| 图谱页 | 默认只展示关键关系，提供展开全部；弱化裸分数 | 每条关键关系显示威胁等级、入选理由和证据可信状态 |
| 画像页 | 从单目标画像变为目标与核心竞品横向对比 | 缺少竞品或图片时有合理空状态 |
| 报告页 | 八章节工作台、打印视图、Word 下载、浏览器打印 | 无 Markdown 入口，导出失败不影响网页报告 |
| 证据过程页 | Tab 为证据链、质检记录、智能体过程、差异记录 | 默认证据链，技术详情默认折叠并脱敏 |
| 中文化 | 主界面中文表达，技术字段仅在下钻详情出现 | 允许 SKU、QA、DOCX；主界面不裸露 Agent/Trace 等词 |

## 7. 后端迁移清单

1. Schema 层补充 2.0 枚举和 Overview、DOCX、扩展 Battlefield、横向 Profile、证据过程追踪结构。
2. 服务层新增 Overview、分析范围、图片 URL 派生、关键关系筛选、关系标签、四段式解释、简化关系图、Word 导出和导出失败记录。
3. Agent 层保留现有四 Agent 与 DAG，不为了 2.0 表达改版绕过 QA 或证据链。
4. 报告层从 Markdown 正式交付迁移到 Word `.docx` 正式交付；网页报告保持可读。
5. 安全层继续复用共享脱敏规则，新增 Word 文本和导出元信息扫描。
6. 类型层在 API 变化后重新运行 `npm --prefix frontend run sync:types`。

## 8. 测试迁移清单

| 类型 | 迁移重点 |
|---|---|
| 后端 Schema 测试 | 新增 2.0 枚举、Overview、DOCX、扩展图谱、横向画像和 Trace 结构验证 |
| 后端 API 测试 | 覆盖 overview、docx、Markdown 删除、未完成任务错误、导出失败不影响网页报告 |
| 后端服务测试 | 覆盖分析范围、图片派生、关键关系筛选、PM 标签、四段式解释、简化关系图、Word 导出 |
| 安全测试 | 扫描网页报告、Word 报告、Trace、错误响应和导出失败记录 |
| 前端组件测试 | 覆盖五个 2.0 页面、切片联动、术语解释、打印视图、证据 Tab 和中文化 |
| E2E 测试 | 创建任务后进入总览，覆盖总览、图谱、画像、报告、证据过程追踪和 Word 导出 |
| 冻结回归 | 继续验证默认目标、QA 打回样例、稳定结果形状和无密钥泄露 |

## 9. 非目标与禁止纳入范围

以下能力不属于 2.0 实施范围，不得作为“新增能力”落地：

1. 真实外部实时采集平台。
2. Celery、Redis、PostgreSQL、微服务架构或任务队列。
3. Next.js、Redux、Tailwind 或新的前端主框架。
4. 后端 PDF 服务、Headless Office、Graphviz 系统依赖。
5. PPT 导出、复杂 BI 图表、多任务协同。
6. 自由编辑整份报告或直接改写 Claim 正文。
7. 依赖模型 API Key 才能完成 Demo。
8. 在无证据情况下新增价格、认证、尺寸、销量、排名等事实。

## 10. 后续步骤验证矩阵

| 步骤 | 验证方式摘要 |
|---:|---|
| 02 | Schema 枚举、OpenAPI、核心 Schema 回归 |
| 03 | Snapshot Loader 图片 URL 或缺失状态、Product Schema、Demo 冻结 |
| 04 | 分析范围单元测试、缺访问时间兜底、安全扫描 |
| 05 | OverviewData Schema、行动建议必填、风险结论引用规则 |
| 06 | Overview 服务单元测试、未解决 QA 风险、切片变化、无裸技术字段主文案 |
| 07 | Overview API 完成/未完成/切片/缺失任务测试 |
| 08 | Battlefield Schema 兼容、关键关系合约、四段式解释合约 |
| 09 | 关键关系数量、证据不足高分需复核、展开全部、切片回归 |
| 10 | PM 标签覆盖、低可信高分复核、标签解释非空 |
| 11 | 四段解释、每段引用、无证据事实风险标记 |
| 12 | Profile 横向对比、缺竞品空态、证据下钻、Human Feedback 回归 |
| 13 | Writer 2.0 八章节、判断强度、建议优先级和 Evidence 追溯 |
| 14 | PNG 生成、缺图占位、失败记录、安全扫描 |
| 15 | `.docx` 可读、封面目录正文附录、缺图成功、安全扫描 |
| 16 | DOCX API、未完成错误、Markdown API 删除、网页报告不受导出失败影响 |
| 17 | 导出目录不可写模拟、Trace 失败记录、网页报告成功 |
| 18 | Trace 证据链、QA 记录、业务影响 Diff、安全扫描 |
| 19 | OpenAPI 类型同步、API Client 成功/错误、无过期 Markdown 类型 |
| 20 | 五个 2.0 导航、创建后跳总览、保留 `task_id`、中文化 |
| 21 | 总览首屏五项、缺图文案、关键竞品下钻、桌面首屏视觉 |
| 22 | 切片控件、切片请求、展示刷新 |
| 23 | 术语解释覆盖、鼠标/键盘触达、无裸英文技术词 |
| 24 | 图谱默认关键关系、展开全部、威胁和入选理由、视觉不重叠 |
| 25 | 四段解释、五维解释、依据入口、自然中文 |
| 26 | 三列对比、缺竞品空态、依据入口、窄屏不溢出 |
| 27 | 业务中文入口、禁止自由覆盖报告、before/after/reason、Trace 差异 |
| 28 | 八章节渲染、无 Markdown 入口、Word 下载、导出失败保留网页报告 |
| 29 | 打印视图隐藏交互、静态图谱摘要、Playwright 非空不重叠、中文化 |
| 30 | 默认证据链 Tab、按结论组织、技术详情折叠、安全扫描 |
| 31 | QA 打回记录、状态区分、业务影响 Diff、E2E 冻结案例 |
| 32 | 前端中文化扫描、后端报告中文章节、E2E 标题按钮、人审技术字段位置 |
| 33 | 前端 Mock、后端 fixture、Demo 冻结、安全 fixture |
| 34 | 2.0 Demo 路径、总览首屏、Word 导出、无 Markdown 按钮 |
| 35 | 桌面/窄屏截图、导航不重叠、图谱图片按钮不遮挡 |
| 36 | Word/Trace/导出失败/前端密钥扫描、QA 敏感表达规则 |
| 37 | 2.0 文档、架构记录、新依赖与禁止项、相对路径检查 |
| 38 | 后端全量 Pytest、Ruff、Demo 冻结、DOCX/Overview/Battlefield/Trace/Security 新测 |
| 39 | 前端 Vitest、ESLint、Prettier、TypeScript、生产构建 |
| 40 | Playwright 全量、冻结 Demo、DOCX 可读、Markdown 删除回归、全量质量检查 |

## 11. 步骤 01 自检结论

1. 本清单覆盖总览、图谱、画像、报告、证据与过程追踪、DOCX 和中文化。
2. 本清单只记录 2.0 目标范围，非目标能力均列入禁止纳入范围。
3. 后续步骤 02 到 40 均在验证矩阵中保留明确验证方式。
