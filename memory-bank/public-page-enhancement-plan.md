# 公开页增强与互联网竞品发现两阶段实施计划

## 1. 文档定位

本文档用于规划 `snapshot_plus_live` 从 MVP 占位模式升级为可追溯的外部公开信息增强能力。按照实现风险和产品边界，能力拆成两个阶段：

1. 阶段一：已知 URL 公开页增强。系统只访问用户输入的 `target_product_url`、本地快照已有的 `source_url`、人工允许列表中的少量公开页，用来补齐本地快照没有的信息，并生成新的 Evidence。
2. 阶段二：互联网竞品发现。系统在合规前提下通过公开搜索或受控入口发现候选竞品 URL，再复用阶段一的公开页增强链路生成 Evidence 和竞品候选。

当前系统仍以本地脱敏 SKU 快照为稳定 Demo 数据源；截至 2026-06-10，Stage 1 已知 URL 公开页增强已完成，Stage 2 互联网竞品发现尚未启动。

实施原则：

1. 阶段一先实现、先验收；阶段二必须等阶段一的证据、Trace、QA 和降级链路稳定后再做。
2. 本地脱敏 SKU 快照仍是主数据源，公开页只做补充、校验和缺口说明。
3. 阶段一只访问用户提供或本地快照中已有的公开商品页、品牌页、平台可见页面。
4. 阶段一访问靠 `httpx` 和确定性解析器完成；事实只来自页面明确展示的字段或文本证据。
5. 大模型只作为可选的文本整理、短摘要归类或表达润色，不参与访问网页，不从原始 HTML 自由抽取事实，不新增页面没有明确展示的信息。
6. 阶段二只发现候选竞品，不直接把搜索结果写成事实结论；候选 URL 必须再经过阶段一增强链路。
7. 不绕过登录、验证码、风控、付费墙、地域限制或平台反爬机制。
8. 不引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind、复杂实时采集平台或微服务架构。
9. 未能可靠获取或解析时，必须降级为本地快照，并写入 Trace。
10. 所有外部字段必须带来源 URL、访问时间、提取方式、置信度和局限性。
11. 找不到可靠证据时仍写“暂无可靠数据”，不得凭模型或记忆补价格、销量、认证、尺寸、排名。

## 2. 当前基线

当前实现状态：

1. `data_source_mode` 支持 `demo_snapshot` 和 `snapshot_plus_live` 两个枚举值。
2. `snapshot_plus_live` 已触发 Stage 1 已知 URL 公开页增强：只访问任务输入 URL 和本地快照已有 `source_url`，失败时降级为本地快照。
3. Collection Agent 先调用本地 `load_demo_snapshot()`，再在 `snapshot_plus_live` 下尝试公开页增强。
4. `target_product_url` 仍用于匹配本地 SKU 或记录用户输入目标；在 `snapshot_plus_live` 下也会作为已知公开 URL 候选进入 Stage 1 policy。
5. Evidence 当前主要来源为 `douyin_sku_snapshot`、`user_research`、`manual_review`、派生产物和 Stage 1 `public_product_page` 公开页证据。

阶段一目标：已知 URL 公开页增强

1. 当任务选择 `snapshot_plus_live` 时，在合规前提下尝试读取已知公开页面。
2. 已知 URL 来源限定为任务输入 `target_product_url`、本地快照 SKU 的 `source_url`、人工审核允许列表。
3. 对本地快照缺失字段进行补齐候选生成，例如标题、价格、卖点、规格、主图、访问时间。
4. 对公开页与本地快照冲突的字段生成冲突记录，不静默覆盖。
5. 把获取、解析、降级、冲突、补齐结果全部写入 Trace 和 Evidence。

阶段二目标：互联网竞品发现

1. 在阶段一稳定后，基于目标产品、品类、子类、品牌、核心卖点等受控查询发现候选竞品 URL。
2. 候选竞品必须先进入候选池，不直接参与评分和报告结论。
3. 候选 URL 复用阶段一公开页增强链路，只有生成合格 Evidence 后才可转为竞品候选 Artifact。
4. 新发现竞品必须带发现来源、搜索查询、访问时间、候选理由、置信度和局限性。
5. 互联网发现失败或结果不足时，不影响本地快照主流程。

## 3. 非目标

阶段一明确不做：

1. 在互联网上搜索竞品。
2. 自动发现新竞品。
3. 抓取搜索结果页、榜单页、店铺列表或平台列表页。
4. 外部评论深度爬取和无限翻页。
5. 定时刷新、全量监控、价格历史趋势平台。
6. 以公开页数据替代本地 Demo 快照作为主链路。
7. 用 LLM 猜测页面没有展示的字段。
8. 把未经验证的外部字段直接写成高置信事实。

两个阶段都明确不做：

1. 登录态采集、验证码处理、代理池、账号池、反风控绕过。
2. 大规模多平台采集平台。
3. 用户隐私、订单信息、平台后台信息采集。
4. 绕过 robots、服务条款或页面访问限制。

## 4. 数据边界

阶段一允许尝试增强的字段：

1. 商品标题、品牌或店铺展示名。
2. 页面可见价格或价格区间。
3. 页面可见卖点、规格、套餐说明。
4. 页面可见主图 URL 或公开图片 URL。
5. 页面可见评价数、评分、销量、排名等市场信号，但只有页面明确展示时才可记录。
6. 页面可见认证、质检、安全说明，但报告中必须保守表达。

阶段一禁止自动生成的字段：

1. 页面未展示的销量、排名、认证、尺寸、功效。
2. 平台后台指标、转化率、广告投放数据。
3. 用户隐私、账号信息、手机号、地址、订单信息。
4. 需要登录或绕过限制才能看到的内容。

字段优先级：

1. 本地快照字段作为基线。
2. 公开页字段只作为 `live_candidate`。
3. 缺失字段可以由公开页补齐，但必须生成新的 Evidence。
4. 冲突字段不覆盖原值，生成 `source_conflict` 记录并交给 QA 或 Human Review。
5. 报告引用公开页字段时必须显示“公开页访问时间”和证据边界。

阶段二新增候选字段：

1. `candidate_product_name`：候选竞品名称。
2. `candidate_product_url`：候选竞品公开页 URL。
3. `discovery_query`：发现候选时使用的查询或入口。
4. `discovery_source_url`：搜索结果页、公开榜单页或人工允许入口的 URL。
5. `candidate_reason`：为什么认为它可能是竞品。
6. `candidate_role_hint`：直接竞品、替代竞品、渠道替代或待判断。
7. `discovery_confidence`：发现置信度。
8. `limitations`：搜索范围、排序偏差、页面不可访问等局限。

阶段二候选转正规则：

1. 仅搜索结果标题或摘要不足以成为 Product 和 Evidence。
2. 候选 URL 必须通过阶段一抓取和解析。
3. 至少生成一条公开页 Evidence 后，才可进入 `Product.role=discovered_candidate` 或后续人工审核池。
4. 未经 Human Review 或 QA 通过前，候选竞品不得替换本地快照核心竞品。

## 5. 建议新增后端结构

阶段一新增或调整的 Schema：

1. `EvidenceSourceType.PUBLIC_PRODUCT_PAGE`：公开商品页证据。
2. `EvidenceSourceType.PUBLIC_BRAND_PAGE`：公开品牌或官方说明页证据。
3. `PublicPageSnapshot`：保存 URL、域名、HTTP 状态、访问时间、标题、正文摘要、截图路径、HTML 缓存路径、解析状态。
4. `ExtractedField`：保存字段名、字段值、来源片段摘要、选择器或提取规则、置信度、局限性。
5. `PublicPageEnrichmentResult`：保存补齐字段、冲突字段、不可用字段和降级原因。

阶段一建议文件位置：

1. `backend/app/schemas/public_page.py`
2. `backend/app/services/public_page_policy.py`
3. `backend/app/services/public_page_fetcher.py`
4. `backend/app/services/public_page_parser.py`
5. `backend/app/services/public_page_enrichment.py`
6. `backend/tests/test_public_page_policy.py`
7. `backend/tests/test_public_page_fetcher.py`
8. `backend/tests/test_public_page_parser.py`
9. `backend/tests/test_public_page_enrichment.py`

阶段二新增或调整的 Schema：

1. `CompetitorDiscoveryQuery`：保存由目标产品、品类、子类、品牌、卖点生成的受控查询。
2. `CompetitorDiscoveryResult`：保存搜索入口、查询词、候选数量、降级原因和执行状态。
3. `CompetitorCandidate`：保存候选竞品名称、候选 URL、发现来源、候选理由、角色提示、置信度、局限性。
4. `DiscoverySourceType`：区分公开搜索、公开榜单、人工允许入口、本地种子 URL。
5. `CandidateReviewStatus`：区分待解析、已生成 Evidence、QA 待复核、人工接受、人工拒绝。

阶段二建议文件位置：

1. `backend/app/schemas/competitor_discovery.py`
2. `backend/app/services/competitor_discovery_policy.py`
3. `backend/app/services/competitor_query_builder.py`
4. `backend/app/services/competitor_search_provider.py`
5. `backend/app/services/competitor_candidate_ranker.py`
6. `backend/app/services/competitor_candidate_enrichment.py`
7. `backend/tests/test_competitor_discovery_policy.py`
8. `backend/tests/test_competitor_query_builder.py`
9. `backend/tests/test_competitor_candidate_ranker.py`
10. `backend/tests/test_competitor_candidate_enrichment.py`

存储位置：

1. 原始 HTML 或页面摘要缓存：`data/public_pages/`
2. 可选截图缓存：`data/public_pages/screenshots/`
3. 竞品发现候选摘要：`data/public_pages/discovery/`
4. 阶段一和阶段二结构化结果：继续通过 SQLite `artifact_json` 保存。
5. Tool Call、搜索查询、候选筛选和失败原因：继续进入 Trace。

## 6. 合规与访问策略

阶段一 `public_page_policy` 必须先于抓取执行：

1. URL 必须是 `http` 或 `https`。
2. URL 必须来自任务输入、快照 `source_url` 或人工审核允许列表。
3. 默认只允许每个任务访问少量页面，例如目标商品页和 Top 3 竞品页。
4. 单页面超时时间建议 5 到 10 秒。
5. 单页面最大响应体大小建议限制在 2 MB 内。
6. 默认不跟随跨域重定向。
7. 默认不发送 Cookie、Authorization、用户个人信息或模型密钥。
8. 检查 `robots.txt` 或站点公开规则；不可确认时保守跳过并记录原因。
9. HTTP 403、401、429、验证码、登录页、风控页统一视为不可用，不重试绕过。
10. User-Agent 使用清晰的项目标识，不伪装真实用户或浏览器自动化绕过。

阶段二 `competitor_discovery_policy` 必须先于搜索执行：

1. 只有当阶段一已通过验收后，才允许启用互联网竞品发现。
2. 搜索查询必须来自任务内结构化字段，例如品类、子类、目标品牌、目标商品标题、核心卖点，不允许自由扩散为无限查询。
3. 默认每个任务最多生成 3 到 5 个查询，每个查询最多保留 5 到 10 个候选。
4. 默认只使用公开搜索入口或人工允许的公开榜单/平台列表入口。
5. 不访问需要登录、付费、验证码、位置授权或账号权限的搜索结果。
6. 不抓取无限分页，不做持续监控，不做定时刷新。
7. 搜索结果只进入候选池，不能直接写入 Product、Claim 或报告结论。
8. 候选 URL 必须再次经过阶段一 `public_page_policy`、Fetcher、Parser 和 Enrichment。
9. 搜索服务返回 429、403、验证码、风控、超时或结果不可解释时，记录失败并降级。
10. 如使用第三方搜索 API，API Key 只能来自环境变量，不能写入代码、文档、Trace 或导出报告。

阶段一 Trace 中必须记录：

1. `policy_check` 是否通过。
2. 访问 URL 的脱敏版本。
3. HTTP 状态码、耗时、响应大小。
4. 是否缓存页面摘要。
5. 是否降级到本地快照。
6. 错误原因和不可用原因。

阶段二 Trace 中必须记录：

1. `discovery_policy_check` 是否通过。
2. 查询词的脱敏版本。
3. 搜索入口或来源类型。
4. 候选数量、去重数量、保留数量。
5. 每个候选的名称、URL 脱敏版本、候选理由和置信度。
6. 候选是否进入阶段一公开页增强。
7. 搜索失败、候选拒绝、候选降级的原因。

## 7. 解析与证据生成

阶段一解析策略：

1. 第一版优先使用 `httpx` 获取静态 HTML，避免引入新浏览器采集链路。
2. 使用确定性规则抽取标题、meta、JSON-LD、Open Graph、常见价格文本和规格文本。
3. 不依赖 LLM 从原始 HTML 中自由抽取事实。
4. LLM 如参与，只能对已抽取的短摘要做结构化归类，不得新增事实。
5. 页面需要 JS 渲染且静态 HTML 无有效内容时，记录 `dynamic_page_unavailable` 并降级。

阶段一 Evidence 生成规则：

1. 每个成功页面至少生成一条 `PUBLIC_PRODUCT_PAGE` 或 `PUBLIC_BRAND_PAGE` Evidence。
2. Evidence 必须包含 `source_url`、`access_time`、`content_summary`、`confidence_level`、`limitations`。
3. 价格、认证、销量、排名等敏感事实必须有字段级 `ExtractedField` 记录。
4. 未能提取字段时，不生成虚假 Evidence，只记录不可用原因。
5. 页面原文不能大段进入 Trace、报告或日志，只保存摘要和必要字段。

阶段二候选发现规则：

1. Query Builder 只能从结构化任务字段生成查询，例如“自动猫砂盆 + 目标品牌 + 核心卖点”。
2. Search Provider 返回的标题、摘要和 URL 只形成 `CompetitorCandidate`。
3. Candidate Ranker 只能根据名称相似度、品类关键词、URL 可访问性、来源可信度做初筛。
4. Candidate Enrichment 必须把候选 URL 送入阶段一公开页增强链路。
5. 只有阶段一成功生成公开页 Evidence 的候选，才允许进入 Analysis 候选池。
6. 未生成 Evidence 的候选只保留为 Trace 记录，不进入报告正文。

## 8. Collection Agent 改造

阶段一 Collection Agent 在 `snapshot_plus_live` 下增加已知 URL 增强分支：

1. 先照常加载本地快照，确保主链路稳定。
2. 根据任务输入和本地快照选择已知 URL。
3. 调用 `public_page_policy` 做合规检查。
4. 合规通过后调用 `public_page_fetcher`。
5. 调用 `public_page_parser` 生成字段候选。
6. 调用 `public_page_enrichment` 合并为 Evidence 和补齐候选。
7. 若任一步失败，只记录降级，不影响本地快照流程。

阶段二 Collection Agent 增加互联网竞品发现分支：

1. 仅在阶段一链路稳定且任务显式启用竞品发现时执行。
2. 先调用 `competitor_discovery_policy` 检查是否允许搜索。
3. 调用 `competitor_query_builder` 基于任务字段生成受控查询。
4. 调用 `competitor_search_provider` 获取候选 URL。
5. 调用 `competitor_candidate_ranker` 去重和初筛。
6. 对保留候选逐个调用阶段一公开页增强链路。
7. 生成 `CompetitorCandidate` Artifact 和对应公开页 Evidence。
8. 任何搜索失败都只影响候选发现，不影响本地快照主流程。

打回场景：

1. QA 要求补齐 `source.access_time` 时，公开页 Evidence 可以作为新的补齐证据。
2. QA 要求补齐 `source.screenshot_path` 时，若第一版不做截图，则应明确标记“公开页已访问但无截图”，不能伪造截图。
3. 公开页与快照冲突时，QA 应产生 `source_conflict_needs_review`，优先交给 Human Review。
4. 阶段二候选缺少合格公开页 Evidence 时，QA 应阻止其进入核心竞品结论。

## 9. Analysis / QA / Writer 改造

Analysis Agent：

1. 只消费已通过 Pydantic 校验的公开页 Evidence。
2. 公开页补齐字段影响评分前，必须检查字段置信度和冲突状态。
3. 冲突字段默认降低 `evidence_confidence`，不提升评分。
4. 新增公开页证据后，相关 Claim 必须绑定新增 evidence_id。
5. 阶段二新发现候选只进入“候选竞品池”，不得默认进入核心竞品排序。
6. 候选竞品只有在 QA 通过或 Human Review 接受后，才可生成正式 CompetitionEdge。

QA Agent：

1. 新增公开页 Evidence 完整性检查。
2. 新增 `PUBLIC_PAGE_MISSING_ACCESS_TIME` 检查。
3. 新增 `PUBLIC_PAGE_UNSUPPORTED_FIELD` 检查。
4. 新增 `SOURCE_CONFLICT_NEEDS_REVIEW` 检查。
5. 新增“公开页不可用但报告写成实时数据”的检查。
6. 阶段二新增 `DISCOVERED_CANDIDATE_MISSING_EVIDENCE` 检查。
7. 阶段二新增 `DISCOVERY_QUERY_TOO_BROAD` 检查，避免过宽搜索词污染候选池。
8. 阶段二新增 `CANDIDATE_NEEDS_HUMAN_REVIEW` 检查，控制新竞品进入正式报告。

Writer Agent：

1. 报告必须区分“本地快照证据”和“公开页增强证据”。
2. 使用公开页字段时写明访问时间和局限性。
3. 冲突字段写“建议复核”，不得选择性采用更有利结论。
4. 公开页增强失败时，报告仍保持本地快照口径。
5. 阶段二候选竞品未通过 QA 或 Human Review 前，只能出现在附录或“候选待复核”区域。
6. 阶段二搜索结果不得被写成“全网竞品覆盖完整”，只能写成“基于受控公开搜索发现的候选”。

## 10. 前端与 Trace 改造

输入页：

1. `snapshot_plus_live` 说明改为真实增强模式，但提示可能降级。
2. 增加“公开页增强将只访问公开页面，不绕过登录或验证码”的说明。
3. 若后端返回策略拒绝，应展示“已降级为本地快照”。
4. 阶段二上线后，竞品发现应作为独立高级开关，不和已知 URL 增强混在同一个开关里。
5. 阶段二开关文案必须说明“发现的是候选竞品，需要证据和人工复核”。

Trace 页：

1. Tool Call 列表展示 `public_page_policy`、`public_page_fetcher`、`public_page_parser`、`public_page_enrichment`。
2. Evidence 卡片展示公开页来源类型、访问时间、提取字段和局限性。
3. Diff 视图展示公开页补齐前后差异。
4. 冲突视图展示本地快照值、公开页候选值、来源和推荐处理方式。
5. 阶段二展示 `competitor_discovery_policy`、`competitor_query_builder`、`competitor_search_provider`、`competitor_candidate_ranker`。
6. 阶段二展示候选竞品列表、候选理由、证据状态、QA 状态和 Human Review 状态。

报告页：

1. 证据边界中增加“公开页增强状态”。
2. 核心结论旁边展示来源类型标签。
3. 对公开页冲突和不可用状态提供醒目的复核提示。
4. 阶段二候选竞品默认不进入核心报告正文，除非已通过 QA 或 Human Review。
5. 报告附录可以展示“公开搜索候选池”，但必须标注候选状态和证据局限。

## 11. 两阶段实施计划

### Stage 1：已知 URL 公开页增强

Stage 1 只解决“系统访问已知 URL，补齐本地快照没有的信息，并生成新的 Evidence”。已知 URL 包括用户输入的 `target_product_url`、本地快照 SKU 的 `source_url`、人工允许列表中的少量公开页。

#### Stage 1 Phase 0：冻结需求与合规开关

目标：

1. 明确公开页增强是可选模式，不影响 `demo_snapshot`。
2. 确定允许访问的已知 URL 来源和页面数量上限。
3. 确定第一版只做静态 HTML，不做浏览器自动化。
4. 明确 Stage 1 不做互联网搜索和新竞品发现。

测试：

1. 不改代码时无测试。
2. 需求冻结后更新本文档、`design-document.md` 和 `architecture.md`。

#### Stage 1 Phase 1：Schema 与策略层

实现：

1. 新增公开页相关 Schema。
2. 新增 `EvidenceSourceType` 枚举值。
3. 新增 URL 合规策略服务。
4. 新增策略拒绝原因枚举。

测试：

1. Schema 合法样例校验。
2. 非 HTTP URL 拒绝。
3. 登录页、未知域、超限页面数拒绝。
4. 策略服务不泄露 API Key 或用户隐私。

#### Stage 1 Phase 2：Fetcher 与本地缓存

实现：

1. 基于 `httpx` 实现公开页获取。
2. 支持超时、大小限制、状态码处理。
3. 保存页面摘要或 HTML 缓存到 `data/public_pages/`。
4. 记录 Tool Call。

测试：

1. 使用 `httpx.MockTransport`，不访问真实网络。
2. 200 响应成功生成页面快照。
3. 403、429、超时、超大小响应降级。
4. 缓存文件路径保持在项目目录内。

#### Stage 1 Phase 3：Parser 与字段候选

实现：

1. 从静态 HTML 提取 title、meta、JSON-LD、Open Graph。
2. 基于规则提取价格、卖点、规格、评分等候选字段。
3. 每个字段生成 `ExtractedField`。
4. 解析失败时返回结构化不可用原因。

测试：

1. 使用本地 HTML fixture。
2. 提取标题、价格、主图、规格成功。
3. 无字段页面不生成虚假字段。
4. 原始 HTML 不进入报告或 Trace 大字段。

#### Stage 1 Phase 4：Enrichment 合并逻辑

实现：

1. 将字段候选转为公开页 Evidence。
2. 对快照缺失字段生成补齐候选。
3. 对冲突字段生成冲突记录。
4. 合并结果写入 Graph State。

测试：

1. 缺失访问时间可由公开页 Evidence 补齐。
2. 价格冲突不覆盖快照原值。
3. 冲突记录包含 before、after、source_url、access_time。
4. 无可用字段时流程仍完成。

#### Stage 1 Phase 5：Collection Agent 接入

实现：

1. `demo_snapshot` 保持原行为。
2. `snapshot_plus_live` 在本地快照加载后尝试公开页增强。
3. 降级和失败写入 Agent Run 与 Tool Call。
4. QA 打回时允许调用公开页补齐链路。

测试：

1. `demo_snapshot` 不触发公开页工具。
2. `snapshot_plus_live` 触发公开页工具。
3. 增强失败后任务仍能完成。
4. Trace 中能看到增强成功、失败和降级原因。

#### Stage 1 Phase 6：QA 与 Analysis 支撑

实现：

1. QA 新增公开页证据完整性规则。
2. Analysis 只消费可信公开页 Evidence。
3. 冲突字段降低证据置信度或进入人工复核。
4. 公开页补齐后相关竞争边局部重算。

测试：

1. 公开页 Evidence 缺访问时间会被 QA 标记。
2. 公开页字段支持的 Claim 绑定新 evidence_id。
3. 冲突字段触发 `source_conflict_needs_review`。
4. 重新分析后风险状态变化可追踪。

#### Stage 1 Phase 7：Writer、报告与 Word 导出

实现：

1. 报告中展示公开页增强状态。
2. Word 附录增加公开页 Evidence 索引。
3. 冲突和不可用状态写入风险与证据边界。
4. 不把公开页增强失败写成“实时数据已验证”。

测试：

1. 网页报告显示公开页证据来源。
2. Word 报告包含公开页 Evidence 附录。
3. 增强失败时报告保留本地快照口径。
4. 安全测试确认不泄露 HTML 原文中的敏感字段。

#### Stage 1 Phase 8：前端展示与 Human Review

实现：

1. 输入页更新增强模式文案。
2. Trace 页展示公开页工具调用和 Diff。
3. Evidence 卡片展示公开页字段级证据。
4. Human Review 支持接受或拒绝冲突字段候选。

测试：

1. 前端组件测试覆盖增强模式提示。
2. Trace 组件测试覆盖公开页 Tool Call。
3. Evidence 卡片测试覆盖字段级来源。
4. Human Review 测试覆盖冲突字段采纳/拒绝。

#### Stage 1 Phase 9：端到端与演示冻结

实现：

1. 使用本地 mock 公开页完成端到端演示路径。
2. 固定一个“公开页补齐缺失证据”的演示样例。
3. 固定一个“公开页与快照冲突，交给 Human Review”的演示样例。
4. 更新 demo runbook 和答辩话术。

测试：

1. 后端完整测试通过。
2. 前端测试和构建通过。
3. Playwright 演示路径通过。
4. 无网络环境下仍可用 mock 或降级路径完成 Demo。

### Stage 2：互联网竞品发现

Stage 2 在 Stage 1 完成后再启动，只解决“系统通过受控公开搜索发现候选竞品 URL”。搜索结果不能直接进入报告结论，必须复用 Stage 1 的公开页增强链路生成 Evidence 后，才可进入候选竞品池。

#### Stage 2 Phase 0：冻结搜索边界

目标：

1. 明确 Stage 2 默认关闭，必须显式启用。
2. 确定允许的搜索入口，例如公开搜索 API、人工允许的公开榜单页或平台公开列表页。
3. 确定每个任务的查询数量、候选数量和访问上限。
4. 明确候选竞品默认需要 QA 或 Human Review 后才能进入正式分析。

测试：

1. 不改代码时无测试。
2. 需求冻结后更新本文档、`design-document.md` 和 `architecture.md`。

#### Stage 2 Phase 1：Discovery Schema 与策略层

实现：

1. 新增 `CompetitorDiscoveryQuery`、`CompetitorDiscoveryResult`、`CompetitorCandidate`。
2. 新增 `DiscoverySourceType` 与 `CandidateReviewStatus`。
3. 新增 `competitor_discovery_policy`。
4. 新增搜索数量、候选数量、查询范围和来源限制。

测试：

1. Discovery Schema 合法样例校验。
2. 过宽查询被拒绝。
3. 超出候选数量上限被截断。
4. 策略服务不泄露 API Key、搜索 API 密钥或用户隐私。

#### Stage 2 Phase 2：Query Builder

实现：

1. 从任务品类、子类、目标商品标题、品牌、卖点生成受控查询。
2. 查询必须可解释，不能由 LLM 自由扩散。
3. 查询记录进入 Trace。
4. 无足够结构化输入时不生成查询。

测试：

1. 自动猫砂盆任务生成有限查询。
2. 空品类或不支持品类不生成查询。
3. 查询数量不超过上限。
4. 查询文本不包含隐私或密钥。

#### Stage 2 Phase 3：Search Provider

实现：

1. 接入公开搜索入口或本地 mock 搜索 provider。
2. 返回标题、摘要、URL、来源、排序位置。
3. 处理 403、429、超时、验证码、无结果等降级。
4. 真实网络访问必须可关闭，测试默认使用 mock。

测试：

1. Mock 搜索返回候选列表。
2. 搜索失败不影响本地快照主流程。
3. 搜索结果 URL 进入阶段一 policy 前不抓取。
4. 搜索 API Key 不进入 Trace、日志或报告。

#### Stage 2 Phase 4：Candidate Ranker

实现：

1. 对搜索结果去重。
2. 根据品类关键词、标题相关性、URL 来源、摘要信号做初筛。
3. 生成候选理由和发现置信度。
4. 明确拒绝原因，例如不相关、重复、不可访问、来源不允许。

测试：

1. 重复 URL 去重。
2. 非自动猫砂盆候选被降低置信度或拒绝。
3. 每个保留候选有候选理由。
4. 拒绝候选进入 Trace 但不进入 Product。

#### Stage 2 Phase 5：Candidate Enrichment 复用 Stage 1

实现：

1. 对保留候选 URL 调用 Stage 1 policy、fetcher、parser、enrichment。
2. 成功生成公开页 Evidence 的候选进入候选竞品池。
3. 失败候选只保留 Trace 记录。
4. 候选不会自动覆盖本地核心竞品集合。

测试：

1. 候选 URL 成功生成公开页 Evidence。
2. 候选 URL 抓取失败不会生成 Product。
3. 候选 Evidence 绑定候选 ID。
4. 候选进入 Analysis 前保留待复核状态。

#### Stage 2 Phase 6：Analysis、QA 与 Human Review

实现：

1. Analysis 为合格候选生成低置信候选 CompetitionEdge 或候选 Battlecard。
2. QA 检查候选是否有足够 Evidence。
3. Human Review 支持接受、拒绝或延后候选竞品。
4. 被接受候选才进入正式竞品集合和报告正文。

测试：

1. 无 Evidence 候选被 QA 阻止。
2. 通过 Evidence 的候选可生成低置信分析产物。
3. Human Review 接受后候选进入正式分析。
4. Human Review 拒绝后候选不进入报告正文。

#### Stage 2 Phase 7：前端与报告展示

实现：

1. 输入页增加独立“互联网竞品发现”高级开关。
2. Trace 页展示搜索查询、候选池、候选筛选和候选增强状态。
3. 竞争图谱页可显示“候选待复核”分组。
4. 报告附录展示候选池；正文只展示已通过候选。

测试：

1. 前端组件测试覆盖高级开关。
2. Trace 组件测试覆盖候选发现链路。
3. 报告页不把待复核候选写入核心正文。
4. Human Review 流程可接受或拒绝候选。

#### Stage 2 Phase 8：端到端与演示冻结

实现：

1. 使用 mock 搜索结果完成端到端演示。
2. 固定一个“搜索发现候选竞品，公开页补齐 Evidence，人工接受”的演示样例。
3. 固定一个“搜索发现候选但证据不足，被 QA 阻止”的演示样例。
4. 更新 demo runbook 和答辩话术。

测试：

1. 后端完整测试通过。
2. 前端测试和构建通过。
3. Playwright 演示路径通过。
4. 无真实网络时仍能使用 mock 搜索完成演示。

## 12. 最小验收标准

Stage 1 已知 URL 公开页增强完成后至少满足：

1. `demo_snapshot` 行为完全不变。
2. `snapshot_plus_live` 可以在 mock 网络下生成公开页 Evidence。
3. 公开页 Evidence 必须有 URL、访问时间、置信度、局限性。
4. 获取失败、策略拒绝、解析失败都会进入 Trace。
5. 冲突字段不静默覆盖本地快照。
6. QA 可以检查公开页 Evidence 的完整性。
7. Writer 不会把公开页增强失败写成实时验证成功。
8. 导出报告、Trace、日志不包含 API Key、Cookie、Authorization 或未脱敏隐私。
9. 不引入复杂实时采集平台或新基础设施。

Stage 2 互联网竞品发现完成后至少满足：

1. Stage 1 全部验收标准仍满足。
2. 互联网竞品发现默认关闭，显式开启后才执行。
3. 搜索查询来自结构化任务字段，不自由扩散。
4. 搜索结果只进入候选池，不直接进入 Product、Claim 或报告正文。
5. 候选 URL 必须通过 Stage 1 并生成 Evidence 后，才可进入候选分析。
6. 候选竞品进入正式报告前必须通过 QA 或 Human Review。
7. 搜索失败、候选拒绝、候选证据不足都进入 Trace。
8. 无真实网络时，mock 搜索路径仍可完成演示。
9. 不引入复杂采集平台、代理池、账号池或反风控绕过。

## 13. 实施前需要确认的问题

Stage 1 实施前需要确认：

1. 第一版允许访问哪些已知 URL 域名或平台页面？
2. 是否允许保存 HTML 缓存，还是只保存摘要和字段级证据？
3. 是否需要截图证据；如果需要，是否接受后续单独评估浏览器自动化方案？
4. 公开页字段与本地快照冲突时，默认是否全部交给 Human Review？
5. 演示是否使用真实公开页，还是统一使用本地 HTML fixture 和 mock 网络？

Stage 2 实施前需要确认：

1. 是否允许接入公开搜索 API；如果允许，使用哪个 provider？
2. 如果不接入搜索 API，是否使用人工允许的公开榜单页或本地 mock 搜索 fixture？
3. 每个任务最多生成多少查询、保留多少候选？
4. 新发现候选是否默认必须由 Human Review 接受后才能进入报告正文？
5. 是否需要在报告中展示“候选池”，还是只在 Trace 中展示？

## 14. Stage 1 执行结果与默认决策（2026-06-10）

Stage 1 已按本计划完成，且没有进入 Stage 2。系统现在只尝试访问已知公开 URL：任务输入的 `target_product_url`、本地快照产品已有 `source_url`，以及后续可配置的人工允许列表。互联网搜索竞品、搜索结果页抓取、候选竞品发现、搜索 provider、候选池和 discovered competitor 均未实现。

### 已完成范围

1. Schema：新增 `public_product_page` / `public_brand_page` 来源类型，以及 `PublicPageSnapshot`、`ExtractedField`、`PublicPageEnrichmentResult`。
2. Policy：Stage 1 只接受 `task.target_product_url`、`snapshot.source_url`、`manual_allowlist` 来源；拒绝非 HTTP(S)、未知来源、重复 URL、超出页面上限、非允许域名。
3. Fetcher：使用 `httpx` 获取静态 HTML，默认不跟随重定向，不发送 Cookie/Auth，限制响应大小，拒绝登录、验证码、风控、403/401/407/429 和非 HTML 响应。
4. Parser：使用确定性 HTML 解析器提取 title、meta/OG/Twitter、JSON-LD Product 字段、页面明确可见的价格、卖点、规格和主图 URL。
5. Enrichment：成功页面生成新的公开页 Evidence，记录 URL、访问时间、置信度、局限性、字段级证据、补齐字段和冲突；不覆盖本地快照。
6. Collection：`snapshot_plus_live` 在本地快照加载后尝试公开页增强；目标产品和本地竞品的已知 URL 都会进入策略评估，默认最多生成 4 个公开页 Evidence。
7. QA：公开页 Evidence 可以补齐同产品本地快照缺失的 `source.access_time`；缺截图仍保持保守，不伪造截图。
8. Trace/报告/前端：Tool Call 和 Evidence 可以展示公开页来源、访问时间、局限性和降级状态；输入页说明改为“已知公开 URL 增强”。

### 默认决策

1. 允许域名：默认只允许抖音短链/商品页域名、后续人工配置 allowlist，以及测试域名；未知域名默认拒绝并写入 Trace。
2. 页面数量：默认每个任务最多 4 个已知公开页，优先目标商品 URL，再取本地竞品已知 URL；这覆盖“目标 + 少量本地竞品”的演示需求。
3. 缓存策略：允许把 HTML 缓存在项目目录内 `data/public_pages/` 或测试用 `.tmp/public_pages/`；Trace、日志和报告不输出原始 HTML，只输出摘要和字段级证据。
4. 截图策略：Stage 1 第一版不引入浏览器自动化截图，不伪造截图；缺截图通过局限性和 `missing_screenshot` 风险标记表达。
5. 冲突处理：公开页字段与本地快照冲突时，记录 `source_conflict_needs_review`，交给 QA/Human Review；不静默覆盖本地快照，也不选择性采用更有利字段。
6. 演示策略：测试和稳定演示统一使用本地 HTML fixture / `httpx.MockTransport`；真实公开页只作为运行时 best-effort，不作为测试前提。
7. 模型边界：访问靠 `httpx`，事实靠页面明确证据，LLM 仅可选做文本整理；当前实现公开页增强 `llm_used=false`。
8. Stage 2：保持未启动。不得把当前 Stage 1 的已知 URL 增强解释为互联网竞品搜索或自动发现新竞品。

### 验证记录

1. `$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; backend\.conda312\python.exe -m pytest tests\test_public_page_policy.py tests\test_public_page_fetcher.py tests\test_public_page_parser.py tests\test_public_page_enrichment.py tests\test_collection_agent.py tests\test_qa_rules.py tests\test_tasks_api.py tests\test_trace_api.py tests\test_reports_api.py -q`：通过，68 个测试通过，3 个 Pydantic 枚举序列化 warning。
2. `$env:RUFF_CACHE_DIR='D:\pythonproject\zijieagent\.tmp\ruff_cache'; backend\.conda312\python.exe -m ruff check backend\app\services\public_page_policy.py backend\app\services\public_page_fetcher.py backend\app\services\public_page_parser.py backend\app\services\public_page_enrichment.py backend\app\services\__init__.py backend\app\agents\collection.py backend\app\services\qa_rules.py backend\tests\test_public_page_policy.py backend\tests\test_public_page_fetcher.py backend\tests\test_public_page_parser.py backend\tests\test_public_page_enrichment.py backend\tests\test_collection_agent.py`：通过。
3. 在 `frontend/` 目录执行 `$env:VITE_CACHE_DIR='.vitest-cache-goal-audit-final2'; npm run test -- --run src/api/contracts.test.ts`：通过，4 个测试通过。
4. 在 `frontend/` 目录执行 `.\node_modules\.bin\tsc.cmd --noEmit`：通过。
5. 在 `frontend/` 目录执行 `$env:VITE_CACHE_DIR='.vite-build-check-public-page-stage1-final-alt-cache'; npm run build -- --outDir .vite-build-check-public-page-stage1-final-out`：通过。默认 `dist/` 构建曾因 Windows 拒绝删除旧产物 `dist/assets/index-BcnAjEgV.js` 报 `EPERM`，改用独立输出目录后验证当前代码可完成构建。
