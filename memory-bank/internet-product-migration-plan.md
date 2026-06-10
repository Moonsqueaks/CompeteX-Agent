# 字节互联网产品竞品分析迁移计划

## 1. 文档信息

| 项目 | 内容 |
|---|---|
| 文档名称 | 字节互联网产品竞品分析迁移计划 |
| 当前日期 | 2026-06-10 |
| 目标产品 | 豆包 Doubao，字节系 AI 助手产品 |
| 第一批竞品 | Kimi、DeepSeek、千问/通义千问、腾讯元宝 |
| 迁移目标 | 在不重写现有系统的前提下，把自动猫砂盆竞品分析能力扩展到互联网产品竞品分析 |
| 实施边界 | 保留 LangGraph DAG、Evidence、Claim、QA 打回、Trace、Human Review、网页报告和 Word 导出 |
| 技术栈约束 | 继续使用 FastAPI、LangGraph、Pydantic v2、SQLite、React、TypeScript、Vite、Ant Design、TanStack Query、React Flow |

## 2. 迁移结论

系统可以迁移到互联网产品，且不建议重写。现有系统真正有价值的部分是“多 Agent 协作 + 证据链 + QA 打回 + 可追踪竞争关系评分”，这些能力与具体品类无关。

本次迁移应采用增量路线：

1. 保留当前自动猫砂盆 Demo，不破坏已有稳定链路。
2. 新增一个 `internet_ai_assistant` 领域配置和本地快照数据。
3. 第一版仍以本地脱敏快照为主，`snapshot_plus_live` 只作为已知公开 URL 增强，不做互联网搜索和自动发现竞品。
4. 先通过字段映射跑通端到端 Demo，再把硬件专属字段逐步抽象为通用互联网产品字段。

## 3. 目标产品与竞品范围

### 3.1 目标产品

| 字段 | 建议值 |
|---|---|
| 产品名称 | 豆包 Doubao |
| 公司/品牌 | 字节跳动/字节系 |
| 产品类型 | AI 助手 / 通用 AI 应用 |
| 官方入口 | `https://www.doubao.com/chat/` |
| Demo 定位 | 大众 AI 助手、内容创作、问答、学习办公、字节生态入口 |

说明：上表中的定位是待证据验证的分析方向，最终报告不得在没有 Evidence 的情况下写成确定事实。

### 3.2 第一批竞品

| 产品 | 官方入口 | 竞争关系假设 | 纳入原因 |
|---|---|---|---|
| Kimi | `https://www.kimi.com/` | 直接竞品 / 场景强化竞品 | 适合对比长文档、研究、知识工作场景 |
| DeepSeek | `https://www.deepseek.com/` | 直接竞品 / 模型心智竞品 | 适合对比推理、开发者心智、模型口碑 |
| 千问/通义千问 | `https://www.qianwen.com/` | 直接竞品 / 生态竞品 | 适合对比阿里生态、全能助手、办公与生产力场景 |
| 腾讯元宝 | `https://yuanbao.tencent.com/` | 直接竞品 / 生态竞品 | 适合对比腾讯生态、搜索问答、内容创作和大众入口 |

### 3.3 候补竞品

| 产品 | 用途 |
|---|---|
| 百度文小言 / 文心助手 | 如需补充搜索生态和百度内容入口，可作为候补竞品 |
| ChatGPT | 可作为全球标杆参照，但第一版建议先聚焦中国互联网产品 |

## 4. 需要收集的数据

### 4.1 数据原则

1. 第一版 Demo 使用本地快照，不依赖现场实时访问互联网。
2. 只使用公开页面、官方页面、应用商店公开信息、已授权的手工截图和用户提供的脱敏调研材料。
3. 不绕过登录、验证码、风控、付费墙或地域限制。
4. 找不到可靠证据时写“暂无可靠数据”，不得凭记忆补价格、排名、下载量、模型能力、市场份额或用户规模。
5. 推断内容必须在 Claim 中标记 `is_inference=true`。
6. 截图不是所有 Evidence 的硬性必填，但关键页面建议保留截图，便于 QA 和答辩展示。

### 4.2 每个产品的最低数据包

每个产品至少收集以下数据：

| 数据类型 | 是否必需 | 说明 |
|---|---:|---|
| 产品基础信息 | 是 | 名称、品牌/公司、产品类型、官网 URL、访问时间 |
| 官方定位文案 | 是 | 官网首页、产品页或下载页中明确展示的定位描述 |
| 核心功能模块 | 是 | 问答、搜索、文档、写作、编程、多模态、智能体、办公协作等，以页面证据为准 |
| 目标用户与场景 | 是 | 学生、知识工作者、内容创作者、开发者、企业团队等，证据不足时标为推断 |
| 入口与平台 | 是 | Web、iOS、Android、PC 客户端、小程序等，必须有来源 |
| 商业模式/价格 | 建议 | 免费、订阅、会员、API、企业版等；没有可靠来源则写“暂无可靠数据” |
| 应用商店信息 | 建议 | App Store 或公开应用市场页面；评分、排名、评论数等属于时效信息，必须带 `access_time` |
| 更新日志/帮助文档 | 建议 | 用于证明功能存在和变化，不作为无证据的能力排名 |
| 截图 | 建议 | 官网/首页、核心对话界面、功能入口/定价/下载页 |
| 用户研究文本 | 可选 | 用户访谈、问卷、内部调研，必须脱敏 |

### 4.3 建议截图清单

每个产品建议至少 3 张截图：

1. 官网首页或产品首页截图：证明产品定位和入口。
2. 核心使用界面截图：证明对话、搜索、文档、创作或智能体入口。
3. 功能页、定价页、下载页或应用商店页截图：证明关键能力、商业模式或平台入口。

截图存储建议：

```text
data/raw/internet_ai_assistant/
  doubao/
    homepage.png
    chat_ui.png
    feature_or_download.png
  kimi/
    homepage.png
    chat_ui.png
    feature_or_download.png
  deepseek/
    homepage.png
    chat_ui.png
    feature_or_download.png
  qianwen/
    homepage.png
    chat_ui.png
    feature_or_download.png
  yuanbao/
    homepage.png
    chat_ui.png
    feature_or_download.png
```

### 4.4 禁止写入的数据

1. 真实 API Key、Cookie、Authorization、账号信息、手机号、邮箱、地址。
2. 登录后页面、内部后台页面或未经授权的私有数据。
3. 未脱敏访谈原文中的个人身份信息。
4. 未经证实的 MAU、DAU、下载量、收入、排名、模型参数规模、市场份额。

## 5. 新快照数据契约

### 5.1 文件位置

新增互联网产品快照，不覆盖现有猫砂盆快照：

```text
data/snapshots/internet_ai_assistant_snapshot.json
data/snapshots/internet_ai_assistant_README.md
```

现有文件继续保留：

```text
data/snapshots/demo_sku_snapshot.json
```

### 5.2 顶层结构

建议第一版结构如下：

```json
{
  "snapshot_version": "internet_ai_assistant_v1",
  "domain_key": "internet_ai_assistant",
  "category": "互联网产品",
  "subcategory": "AI 助手",
  "default_target_product_id": "doubao",
  "qa_revision_fixture": {},
  "products": []
}
```

### 5.3 产品结构

为了降低第一版改造风险，快照内部可以保留兼容字段 `sku_id`，但语义改为 `product_snapshot_id`。后续再统一重命名。

```json
{
  "sku_id": "ip_doubao",
  "product_id": "doubao",
  "role": "target",
  "name": "豆包",
  "brand": "字节跳动",
  "product_type": "general_ai_assistant",
  "positioning": "待证据验证的产品定位摘要",
  "target_users": ["知识工作者", "学生", "内容创作者"],
  "core_scenarios": ["日常问答", "内容创作", "学习办公"],
  "feature_modules": {
    "conversation": [],
    "search_or_research": [],
    "document_processing": [],
    "content_creation": [],
    "coding_or_reasoning": [],
    "multimodal": [],
    "agent_or_workflow": [],
    "ecosystem_integration": []
  },
  "pricing": {
    "currency": "CNY",
    "pricing_band": "unknown",
    "list_price": null,
    "final_price": null,
    "pricing_note": "暂无可靠数据"
  },
  "platforms": ["web"],
  "official_urls": [],
  "screenshots": [],
  "source": {
    "platform": "official_web",
    "source_url": "https://www.doubao.com/chat/",
    "raw_dir": "data/raw/internet_ai_assistant/doubao",
    "screenshot_path": "data/raw/internet_ai_assistant/doubao/homepage.png",
    "access_time": "2026-06-10T00:00:00+08:00",
    "source_description": "官方公开页面快照",
    "limitations": "公开页面信息可能随时间变化，未登录功能不可验证"
  },
  "evidence_items": []
}
```

### 5.4 Evidence 结构

每个 Evidence 至少包含：

| 字段 | 说明 |
|---|---|
| `evidence_id` | 稳定 ID，例如 `ev_ip_doubao_homepage` |
| `product_id` | 关联产品 |
| `source_type` | 来源类型，例如官方产品页、应用商店、帮助文档、截图、用户研究 |
| `source_url` | 可公开访问的来源 URL；本地调研材料可以为空 |
| `screenshot_path` | 本地截图路径；没有则为 `null` 并记录局限性 |
| `access_time` | 访问或截图时间；时效信息必须填写 |
| `content_summary` | 只写来源可支持的摘要 |
| `confidence_level` | `high` / `medium` / `low` / `unknown` |
| `limitations` | 来源局限性 |
| `metadata` | 结构化字段，例如功能模块、平台、价格、评价数、缺失字段 |

### 5.5 QA 打回夹具

第一版必须保留一个可复现的 QA 打回案例。建议使用：

```json
{
  "qa_revision_fixture": {
    "product_id": "kimi",
    "evidence_id": "ev_ip_kimi_feature_page",
    "missing_fields": ["source.screenshot_path"],
    "repair_evidence": {
      "screenshot_path": "data/raw/internet_ai_assistant/kimi/feature_or_download.png",
      "source_note": "本地 Demo 修复夹具补齐 Kimi 功能页截图证据"
    }
  }
}
```

该案例用于演示：

1. Analysis Agent 生成“某竞品在长文档/研究场景构成较强竞争压力”的 Claim。
2. QA Agent 发现关键功能页 Evidence 缺少截图路径。
3. QA Agent 打回 Collection Agent。
4. Collection Agent 从本地修复夹具补齐截图路径。
5. Analysis Agent 重新计算相关 CompetitionEdge。
6. Trace 展示打回前后 Diff。

## 6. 领域配置方案

### 6.1 新增领域配置

新增轻量配置，不引入新框架：

```text
backend/app/services/domain_profiles.py
```

建议配置项：

| 字段 | 用途 |
|---|---|
| `domain_key` | `smart_litter_box` 或 `internet_ai_assistant` |
| `category` / `subcategory` | 前后端任务分类 |
| `snapshot_path` | 当前领域默认快照 |
| `target_url_required` | 是否要求目标 URL |
| `feature_axes` | 功能能力维度 |
| `slice_axes` | 竞争图谱切片维度 |
| `decision_stages` | 决策链展示文案 |
| `qa_terms` | QA 时效、截图、敏感表达关键词 |
| `report_template` | Writer 报告章节口径 |

### 6.2 第一版领域配置

```text
domain_key: internet_ai_assistant
category: 互联网产品
subcategory: AI 助手
snapshot_path: data/snapshots/internet_ai_assistant_snapshot.json
default_target_product_id: doubao
```

功能维度：

1. 对话问答
2. 搜索与深度研究
3. 文档处理
4. 内容创作
5. 编程与推理
6. 多模态能力
7. 智能体/工作流
8. 生态与分发入口
9. 隐私、安全与企业能力

切片维度：

1. 用户人群：学生、知识工作者、内容创作者、开发者、企业团队。
2. 使用场景：日常问答、长文档研究、内容创作、办公协作、编程推理、多模态创作。
3. 商业模式：免费、Freemium、订阅、API/开发者、企业版、暂无可靠数据。

说明：为了兼容现有 `CompetitionSlice.price_band` 字段，第一版可把“商业模式”暂时写入 `price_band`，前端按领域把标签显示为“商业模式/付费层”。后续再重命名 Schema。

## 7. 现有代码修改计划

### 7.1 后端 Schema

第一阶段尽量少改核心 Schema：

1. 保留 `Product`、`Evidence`、`Claim`、`CompetitionEdge`。
2. `Product.category` 和 `Product.subcategory` 使用“互联网产品 / AI 助手”。
3. `Product.tags` 写入产品类型、平台、核心场景和商业模式标签。
4. `Evidence.metadata` 承接互联网产品专属字段，例如功能模块、平台、价格、应用商店信息。
5. `PricingModel.price_band` 第一版复用为商业模式分层。

建议新增或扩展：

1. `EvidenceSourceType.OFFICIAL_PRODUCT_PAGE`
2. `EvidenceSourceType.OFFICIAL_HELP_DOC`
3. `EvidenceSourceType.APP_STORE_PAGE`
4. `EvidenceSourceType.OFFICIAL_RELEASE_NOTE`
5. `RiskFlag.MISSING_OFFICIAL_SOURCE`，如确有必要再加。

第二阶段再引入更通用的画像 Artifact：

```text
ProductCapabilityProfile
  conversation
  search_or_research
  document_processing
  content_creation
  coding_or_reasoning
  multimodal
  agent_or_workflow
  ecosystem_integration
  privacy_security
```

### 7.2 Snapshot Loader

新增互联网产品加载服务，避免改坏现有猫砂盆 Loader：

```text
backend/app/services/internet_product_snapshot_loader.py
```

职责：

1. 读取 `data/snapshots/internet_ai_assistant_snapshot.json`。
2. 校验顶层字段、产品字段、Evidence 字段和 QA 修复夹具。
3. 转换为现有 `Product`、`Evidence`、`ReviewInsight`。
4. 缺失字段只记录到 `metadata.missing_fields`，不得自动补造。
5. 将截图路径转换为可被前端访问的 `/assets/raw/...` 路径。

任务创建和 Collection Agent 需要根据领域选择 Loader：

```text
if domain_key == "internet_ai_assistant":
    load_internet_product_snapshot(...)
else:
    load_demo_snapshot(...)
```

### 7.3 任务创建 API

当前 `POST /tasks` 已支持 `category`、`subcategory` 和 `data_source_mode`。需要补充：

1. 前端新增“互联网产品 / AI 助手”选项。
2. 后端根据 `category/subcategory` 推导 `domain_key`。
3. 任务 metadata 写入：

```json
{
  "domain_key": "internet_ai_assistant",
  "selected_target_product_id": "doubao",
  "target_selection": "matched_internet_product_snapshot",
  "target_selection_basis": "target_product_url",
  "target_match_confidence": "high"
}
```

4. 若用户选择互联网产品但 URL 未命中快照，保守创建 `user_input_unmatched` 目标，只记录身份 Evidence，不生成事实 Claim。

### 7.4 Collection Agent

修改点：

1. 根据 `domain_key` 选择猫砂盆快照或互联网产品快照。
2. 对互联网产品生成 `official_product_page`、`app_store_page`、`official_help_doc` 等 Evidence。
3. 保持 `snapshot_plus_live` Stage 1 边界：只访问任务输入 URL 和快照中已有公开 URL，不搜索新竞品。
4. QA 打回后从 `qa_revision_fixture` 补齐缺失截图或访问时间。
5. Trace 中明确记录数据来源为本地互联网产品快照，避免误认为实时采集。

### 7.5 Analysis Agent

当前 `analysis.py` 中大量关键词仍是猫砂盆领域，例如自动清理、除臭、安全、多猫、维护成本。迁移需要做领域分流。

新增互联网产品关键词组：

```text
GENERAL_AI_TERMS: AI 助手、问答、聊天、助手
LONG_CONTEXT_TERMS: 长文档、文档、PDF、研究、总结
SEARCH_RESEARCH_TERMS: 搜索、联网、引用、研究、Deep Research
CONTENT_CREATION_TERMS: 写作、改写、生成、图片、视频、脚本
CODING_REASONING_TERMS: 代码、编程、推理、数学、逻辑
MULTIMODAL_TERMS: 图片、语音、视频、视觉、多模态
AGENT_WORKFLOW_TERMS: 智能体、Agent、工作流、自动化
ECOSYSTEM_TERMS: 微信、阿里、字节、腾讯、办公、浏览器、应用
```

召回逻辑：

1. 同类直接竞品：同为通用 AI 助手。
2. 场景竞品：在长文档研究、编程推理、内容创作、办公协作等场景强相关。
3. 生态竞品：与字节、阿里、腾讯、百度等生态入口产生竞争。
4. 替代方案：搜索引擎、办公套件、垂直 AI 工具等可作为后续扩展。

评分公式保持不变，但解释语义改为：

| 评分维度 | 互联网产品解释 |
|---|---|
| `demand_substitutability` | 是否解决同一用户任务，例如问答、写作、研究、编程 |
| `context_match` | 是否匹配当前人群、场景和商业模式切片 |
| `decision_stage_impact` | 是否影响认知、试用、留存、付费或生态迁移 |
| `evidence_confidence` | 是否有官网、截图、应用商店、帮助文档等可靠证据 |
| `market_signal_strength` | 是否有公开可验证的用户反馈、平台入口、生态信号 |

### 7.6 QA Rules

新增互联网产品 QA 规则，不放松现有规则：

1. 价格、订阅、会员、API 费用、App 评分、榜单、下载量、模型发布时间都属于时效信息，必须有 `access_time`。
2. 功能存在性 Claim 必须绑定官方页面、帮助文档、截图或可验证的本地快照 Evidence。
3. “最好用”“最强”“第一”“领先”“完全免费”“绝对安全”“不会泄露隐私”等表达必须打回或降级。
4. “用户普遍认为”“大量用户反馈”等结论必须有评论聚类或足够样本来源。
5. 涉及隐私、安全、合规、企业数据保护的表述必须保守，证据不足写“建议复核”。
6. 截图缺失不必阻塞所有 Claim，但对定价页、应用商店页、关键功能入口和核心对比结论应触发 QA 风险。

### 7.7 Writer Agent 与报告

互联网产品报告建议章节：

1. 执行摘要：一句话判断、最大威胁、最大机会、首要动作、证据等级。
2. 产品定位与竞争边界：豆包与 Kimi、DeepSeek、千问、腾讯元宝分别在哪些场景竞争。
3. 场景化竞争格局：按日常问答、长文档研究、内容创作、编程推理、办公协作切片展示。
4. 核心竞品 Battlecard：为什么用户会比较、竞品强项、豆包回应方向、风险边界。
5. AI 能力与体验差距矩阵：功能、入口、使用链路、证据完整度。
6. 用户决策链：认知、试用、信任、迁移、留存、付费。
7. 增长与生态机会：入口、内容生态、办公生态、开发者生态和分发渠道。
8. 机会地图与优先级：P0/P1/P2 动作、责任方向、预期影响、所需证据。
9. 风险与证据边界：可采纳结论、推断结论、暂无可靠数据、建议复核事项。
10. 附录：Evidence 索引、QA 打回、Trace 摘要和数据范围。

Writer 禁止：

1. 编造 MAU、DAU、下载量、收入、排名、模型参数或价格。
2. 把“模型能力强弱”写成无证据排名。
3. 把竞品营销文案当作客观事实。
4. 展示内部 `task_id`、`claim_id`、`evidence_id` 等审计字段到报告正文。

### 7.8 前端

需要修改：

1. 输入页新增领域选择：
   - 智能宠物硬件 / 自动猫砂盆
   - 互联网产品 / AI 助手
2. 默认 Demo 可选择“豆包 AI 助手”。
3. 产品画像页按领域切换标签：
   - 猫砂盆：清洁、除臭、安全、智能、维护成本
   - AI 助手：问答、研究、文档、创作、编程、多模态、智能体、生态
4. 竞争图谱页按领域切换切片标签：
   - 猫砂盆：价格带、人群、使用场景
   - AI 助手：商业模式、人群、使用场景
5. 报告页根据 `domain_key` 展示互联网产品章节名。
6. Trace 页展示互联网产品快照、公开页 Evidence、QA 打回和 Diff，不新增复杂交互。

建议在现有 `frontend/src/domain/labels.ts` 中扩展领域文案，不引入新状态管理库。

## 8. 实施步骤

### 步骤 01：新增迁移文档与数据契约

任务：

1. 新增本计划文档。
2. 新增 `data/snapshots/internet_ai_assistant_README.md`。
3. 定义 `internet_ai_assistant_snapshot.json` 的必填字段、Evidence 字段和 QA fixture。

测试：

1. 新增快照契约测试，验证不少于 5 个产品。
2. 验证目标产品为豆包。
3. 验证竞品包含 Kimi、DeepSeek、千问、腾讯元宝。
4. 验证每个产品至少有一个 Evidence。
5. 验证不包含 API Key、Cookie、手机号、账号等敏感字段。

### 步骤 02：准备本地互联网产品快照

任务：

1. 手工收集官方公开页面和截图。
2. 生成 `data/snapshots/internet_ai_assistant_snapshot.json`。
3. 准备一个故意缺少截图或访问时间的 QA 打回样例。

测试：

1. 快照 JSON 可解析。
2. 每个 Evidence 有 `source_url` 或明确本地来源说明。
3. 时效信息有 `access_time`。
4. QA 打回样例确实缺少指定字段，且修复夹具存在。

### 步骤 03：新增领域配置服务

任务：

1. 新增 `backend/app/services/domain_profiles.py`。
2. 根据 `category/subcategory` 推导 `domain_key`。
3. 返回当前领域的快照路径、标签、切片、QA 关键词和报告模板。

测试：

1. 猫砂盆领域仍返回旧快照路径。
2. AI 助手领域返回新快照路径。
3. 未知领域返回标准错误或保守兜底。

### 步骤 04：新增互联网产品 Snapshot Loader

任务：

1. 新增 `internet_product_snapshot_loader.py`。
2. 将新快照转换为 `Product`、`Evidence`、`ReviewInsight`。
3. 保留缺失字段，不补造事实。
4. 将截图路径适配为前端可访问资源。

测试：

1. Loader 能加载 5 个产品。
2. 豆包被标记为 `ProductRole.TARGET`。
3. 竞品角色正确。
4. 每个产品关联 Evidence。
5. 缺失字段进入 `metadata.missing_fields`。

### 步骤 05：任务创建和 Collection 接入领域分流

任务：

1. `POST /tasks` 支持创建 AI 助手分析任务。
2. 任务 metadata 写入 `domain_key`。
3. Collection Agent 根据 `domain_key` 调用对应 Loader。
4. `snapshot_plus_live` 对新领域仍只访问已知 URL。

测试：

1. 创建豆包任务成功。
2. Collection 产出豆包和 4 个竞品。
3. 旧猫砂盆任务不受影响。
4. Trace 中能看到正确的快照文件和领域信息。

### 步骤 06：Analysis Agent 领域化

任务：

1. 抽出硬件关键词和 AI 助手关键词。
2. 按 `domain_key` 选择召回逻辑、切片逻辑和解释模板。
3. 互联网产品使用“商业模式 / 人群 / 场景”切片。
4. 保持 CompetitionEdgeScore 公式不变。

测试：

1. 豆包任务能生成至少 4 条 CompetitionEdge。
2. 每条 CompetitionEdge 绑定 Claim。
3. 每条 Claim 绑定 Evidence 或被标记风险。
4. 不同场景切片下竞品排序或解释发生变化。
5. 猫砂盆既有 Analysis 测试仍通过。

### 步骤 07：QA 规则扩展与真实打回

任务：

1. 增加互联网产品时效字段和敏感表达规则。
2. 对缺截图或缺访问时间的样例触发打回。
3. Collection Agent 从互联网产品 `qa_revision_fixture` 补齐证据。
4. Analysis Agent 重算相关边。

测试：

1. QA 真实生成 `revision_request`。
2. LangGraph 条件边真实回到 Collection。
3. 修复后新增或更新 Evidence。
4. Trace 展示打回前后 Diff。
5. 报告不再出现无证据强结论。

### 步骤 08：报告和 Word 导出适配

任务：

1. Writer 根据 `domain_key` 选择互联网产品报告章节。
2. Battlecard、GapMatrix、OpportunityMap 使用 AI 助手语境。
3. Word 导出保留 Evidence、Claim、置信度、访问时间和推断标识。

测试：

1. 网页报告展示互联网产品章节。
2. Word 导出成功。
3. 报告不包含 API Key、Cookie 或未脱敏隐私。
4. 无证据信息显示“暂无可靠数据”或“建议复核”。

### 步骤 09：前端页面适配

任务：

1. 输入页支持选择 AI 助手 Demo。
2. 总览页、画像页、竞争图谱页、报告页按领域显示标签。
3. 竞争图谱切片从“价格带”显示为“商业模式/付费层”。
4. 保留 Trace 页 DAG、QA 打回、Diff 展示。

测试：

1. 前端组件测试覆盖新领域标签。
2. TypeScript 类型检查通过。
3. 前端构建通过。
4. Playwright 能创建豆包任务并看到报告。

### 步骤 10：演示冻结

任务：

1. 固定豆包 Demo 输入。
2. 固定 4 个核心竞品。
3. 固定 QA 打回样例。
4. 固定答辩演示路径和录屏脚本。

测试：

1. 后端相关测试全通过。
2. 前端相关测试全通过。
3. 端到端 Demo 可稳定跑通。
4. 同一输入能稳定生成同类结论。

## 9. 代码影响范围

### 9.1 后端文件

预计新增：

```text
backend/app/services/domain_profiles.py
backend/app/services/internet_product_snapshot_loader.py
backend/tests/test_domain_profiles.py
backend/tests/test_internet_product_snapshot_contract.py
backend/tests/test_internet_product_snapshot_loader.py
```

预计修改：

```text
backend/app/schemas/common.py
backend/app/services/task_creation.py
backend/app/agents/collection.py
backend/app/agents/analysis.py
backend/app/services/qa_rules.py
backend/app/agents/writer.py
backend/app/services/profile_service.py
backend/app/services/overview_service.py
backend/app/services/word_report_service.py
backend/tests/test_tasks_api.py
backend/tests/test_collection_agent.py
backend/tests/test_task_execution.py
backend/tests/test_qa_rules.py
backend/tests/test_reports_api.py
```

### 9.2 前端文件

预计修改：

```text
frontend/src/pages/TaskInputPage.tsx
frontend/src/pages/OverviewPage.tsx
frontend/src/pages/ProfilePage.tsx
frontend/src/pages/BattlefieldPage.tsx
frontend/src/pages/ReportPage.tsx
frontend/src/domain/labels.ts
frontend/src/api/schema.ts
frontend/src/App.test.tsx
frontend/src/api/contracts.test.ts
```

如现有前端类型不足，新增：

```text
frontend/src/domain/domainProfiles.ts
```

### 9.3 数据与文档

预计新增：

```text
data/snapshots/internet_ai_assistant_snapshot.json
data/snapshots/internet_ai_assistant_README.md
data/raw/internet_ai_assistant/
memory-bank/internet-product-migration-plan.md
demo/internet-ai-assistant-script.md
```

## 10. 验收标准

### 10.1 功能验收

1. 可以创建“互联网产品 / AI 助手 / 豆包”分析任务。
2. 系统可以基于本地互联网产品快照跑通 Collection、Analysis、QA、Writer。
3. 输出豆包 + Kimi + DeepSeek + 千问 + 腾讯元宝的结构化产品信息。
4. 每条核心 Claim 绑定 Evidence 或明确风险。
5. QA Agent 至少真实触发一次打回。
6. 打回后 Collection 或 Analysis 真实重跑，并更新结果。
7. 竞争图谱支持按人群、场景、商业模式切换。
8. Trace 展示 DAG、Agent Run、Tool Call、Token、QA 打回和 Diff。
9. 网页报告展示互联网产品竞品分析章节。
10. Word 导出成功，且不泄露敏感信息。

### 10.2 质量验收

1. 不破坏现有自动猫砂盆 Demo。
2. 不引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或微服务架构。
3. 没有把模拟数据当作最终演示数据。
4. 所有价格、评分、排名、下载量、模型能力、商业模式等事实必须有 Evidence。
5. 推断内容显式标记。
6. 缺证据时写“暂无可靠数据”或“建议复核”。

## 11. 演示路径

建议答辩演示顺序：

1. 在输入页选择“互联网产品 / AI 助手”，目标产品为豆包。
2. 启动任务，进入竞争态势总览。
3. 展示一句话判断：豆包与 Kimi、DeepSeek、千问、腾讯元宝在不同 AI 助手场景下形成竞争关系。
4. 打开产品画像页，展示豆包和核心竞品的功能/场景/平台对比。
5. 打开竞争图谱页，切换“长文档研究”“内容创作”“编程推理”等场景。
6. 展示某条 CompetitionEdge 的 Claim、Evidence 和评分解释。
7. 展示 QA 打回：某个关键功能或时效证据缺少截图/访问时间，系统打回 Collection 补齐。
8. 展示打回前后 Diff。
9. 打开报告页和 Word 导出。
10. 总结系统不是只列竞品，而是重建可追溯、可打回、可人工修正的竞争关系。

## 12. 风险与对策

| 风险 | 对策 |
|---|---|
| 官网页面变化快 | Demo 使用本地快照，记录 `access_time` 和局限性 |
| 截图收集成本高 | 截图作为关键 Evidence 推荐项，不要求所有 Evidence 必填 |
| 互联网产品字段与硬件字段差异大 | 第一版用领域标签和 `metadata` 兼容，第二阶段再抽象 Schema |
| 竞品功能容易凭印象补写 | 所有功能 Claim 必须绑定官方页面、截图、帮助文档或本地快照 Evidence |
| 评分解释泛化 | 为 AI 助手单独配置关键词、切片和解释模板 |
| 破坏猫砂盆 Demo | 新 Loader、新快照、新领域配置并存，回归测试覆盖旧链路 |

## 13. 推荐优先级

P0：

1. 新快照契约与本地数据。
2. 领域配置。
3. 新 Snapshot Loader。
4. Collection/Analysis/QA/Writer 跑通豆包 Demo。
5. QA 真实打回。

P1：

1. 前端领域标签适配。
2. 互联网产品报告章节优化。
3. Word 导出适配。
4. Playwright 演示路径。

P2：

1. 更通用的 `ProductCapabilityProfile`。
2. 更多互联网产品类别，例如协作文档、短视频工具、设计工具、SaaS。
3. 更完善的公开页增强，但仍必须遵守已知 URL 边界。

