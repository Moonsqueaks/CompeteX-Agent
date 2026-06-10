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

### 6.3 内置候选发现配置

“内置候选发现”是指系统不做全网搜索，而是在领域配置中维护一个可信候选池。用户只输入目标产品链接时，系统先识别领域，再从候选池加载可能竞品，后续仍由 Collection、Analysis、QA 和 Writer 判断谁是真正竞品。

它只内置候选对象，不内置分析结论：

```text
目标输入
  -> 领域识别
  -> 加载内置候选池
  -> Collection 获取候选 Evidence
  -> Analysis 评分和召回
  -> QA 检查证据
  -> Writer 输出报告
```

#### 6.3.1 猫砂盆候选池

当前 `data/snapshots/demo_sku_snapshot.json` 已经相当于猫砂盆的内置候选池。后续可以把它显式配置为：

```text
domain_key: smart_litter_box
candidate_pool_type: snapshot
candidate_pool_path: data/snapshots/demo_sku_snapshot.json
target_match_fields:
  - source_url
  - sku_id
  - product_name
candidate_roles:
  - target
  - direct_competitor
  - alternative
  - channel_alternative
  - reference
```

候选类型：

| 类型 | 说明 |
|---|---|
| 自动猫砂盆直接竞品 | 解决同类自动清理任务 |
| 低价自动猫砂盆 | 在价格带上形成拦截 |
| 半封闭/封闭猫砂盆 | 需求替代方案 |
| 猫砂/除臭用品 | 场景替代或搭配竞争 |
| 渠道型替代方案 | 不同平台、不同购买链路形成替代 |

#### 6.3.2 豆包候选池

互联网 AI 助手候选池建议独立配置：

```text
domain_key: internet_ai_assistant
candidate_pool_type: snapshot
candidate_pool_path: data/snapshots/internet_ai_assistant_snapshot.json
target_match_fields:
  - official_url
  - product_id
  - product_name
candidate_roles:
  - target
  - direct_competitor
  - alternative
  - reference
```

第一批候选：

| 产品 | 默认角色 | 说明 |
|---|---|---|
| 豆包 | target | 字节系目标产品 |
| Kimi | direct_competitor | 长文档、研究、Agent、办公生产力候选 |
| DeepSeek | direct_competitor | 推理、模型/API、开发者心智候选 |
| 千问/通义千问 | direct_competitor | 阿里生态、全能助手、办公与生产力候选 |
| 腾讯元宝 | direct_competitor | 腾讯生态、问答、创作、下载入口候选 |
| 文小言/文心助手 | reference 或候补 | 搜索生态与百度入口候选，第一版可不启用 |

#### 6.3.3 候选发现模式

新增数据模式建议命名为：

```text
builtin_candidates
```

语义：

1. 用户只输入目标链接或目标名称。
2. 系统根据领域配置加载本地候选池。
3. 命中目标后，将目标标记为 `target`，其他候选保留原候选角色。
4. 未命中目标时，创建 `user_input_unmatched` 目标，并保留候选池作为 reference，需要 QA 标记目标证据缺口。
5. 不访问搜索引擎，不发现候选池之外的新竞品。

和现有模式的区别：

| 模式 | 数据来源 | 是否发现新竞品 | 适用场景 |
|---|---|---:|---|
| `demo_snapshot` | 固定 Demo 快照 | 否 | 稳定演示 |
| `snapshot_plus_live` | 固定快照 + 已知 URL 增强 | 否 | 已知候选补证据 |
| `builtin_candidates` | 领域内置候选池 | 否 | 只输入目标，系统自动带出候选 |
| 未来 `search_discovery` | 搜索 API + 官网校验 | 是 | 增强版，不进入 MVP |

#### 6.3.4 Trace 展示

内置候选发现必须进入 Trace：

| 字段 | 说明 |
|---|---|
| `candidate_pool_id` | 使用的候选池，例如 `smart_litter_box_v1` 或 `internet_ai_assistant_v1` |
| `candidate_pool_path` | 本地候选池路径 |
| `target_match_basis` | URL、名称或用户输入未命中 |
| `candidate_count` | 候选数量 |
| `selected_target_id` | 目标产品 ID |
| `candidate_pool_loaded` | 明确标记已自动加载领域内置候选池 |
| `candidate_source_type` | `builtin_candidate_pool` |

这样答辩时可以清楚说明：系统“自动带出候选”，但不是不可控的全网爬虫。

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

### 7.8 证据缺口与用户补证据闭环

DeepSeek API 定价截图不应直接静态写死进初始快照，而应设计成系统能力演示闭环：

```text
系统运行初始分析
  -> QA / Evidence Gap 发现 DeepSeek API 定价缺少可靠证据
  -> 前端提示用户补充定价截图或定价页 URL
  -> 用户上传 DeepSeek API 价格截图
  -> Collection 将截图登记为新的 Evidence
  -> Analysis 局部重算 DeepSeek 相关 CompetitionEdge / Claim
  -> Writer 更新报告中的商业模式和价格边界
  -> Trace 展示“补证据前后 Diff”
```

#### 7.8.1 初始状态

初始 `internet_ai_assistant_snapshot.json` 可以只保留 DeepSeek 官网首页和 API 入口证据，不直接写 API 价格表数值。此时 DeepSeek 的 `pricing.pricing_band` 仍为 `unknown`，并在 Evidence metadata 中记录：

```json
{
  "missing_fields": ["pricing.api_price_table"],
  "missing_reason": "DeepSeek API 价格页或价格截图尚未进入本地 Evidence"
}
```

系统报告和总览必须保守表达：

1. 可以写：DeepSeek 官方入口存在 API 开放平台和 API 价格入口。
2. 不可以写：DeepSeek API 比其他竞品更便宜或更贵。
3. 应写：DeepSeek API 定价暂无可靠数据，建议补充官方价格页或截图后复核。

#### 7.8.2 系统提示

前端应在 Evidence Gap、Trace 或 Human Review 区域提示：

```text
DeepSeek 的 API 定价结论缺少可引用证据。请补充官方 API 价格页 URL 或截图。
```

提示内容需要包含：

| 字段 | 示例 |
|---|---|
| 缺口对象 | DeepSeek |
| 缺口类型 | API 定价证据 |
| 需要补充 | 官方价格页 URL 或截图 |
| 影响范围 | 商业模式切片、价格/成本相关 Claim、DeepSeek Battlecard |
| 当前处理 | 暂无可靠数据 |

#### 7.8.3 用户补充截图

用户提供截图后，系统应把它登记为 Evidence，而不是直接改写报告正文。Evidence 建议结构：

```json
{
  "evidence_id": "ev_ip_deepseek_api_pricing_user_upload_001",
  "product_id": "deepseek",
  "source_type": "manual_review",
  "source_url": "https://api.deepseek.com 或用户提供的官方价格页 URL",
  "screenshot_path": "data/raw/internet_ai_assistant/deepseek/api_pricing_user_upload_001.png",
  "access_time": "用户提交时间",
  "content_summary": "用户提供的 DeepSeek API 定价截图，显示 deepseek-v4-flash 与 deepseek-v4-pro 的输入/输出价格、上下文长度和并发限制。",
  "confidence_level": "medium",
  "limitations": "截图由用户提供，需确认来源为官方价格页；价格属于时效信息，后续引用需保留访问时间。",
  "metadata": {
    "evidence_origin": "user_upload",
    "evidence_purpose": "fill_pricing_gap",
    "field_filled": "pricing.api_price_table",
    "requires_manual_source_url_review": true
  }
}
```

#### 7.8.4 可解析字段

如果截图文字可信且人工确认来自官方页面，可以结构化提取以下字段；否则只作为截图 Evidence 保存，不自动提取价格结论：

| 字段 | 示例 |
|---|---|
| 模型 | `deepseek-v4-flash`、`deepseek-v4-pro` |
| API Base URL | `https://api.deepseek.com` |
| 上下文长度 | `1M` |
| 最大输出长度 | `384K` |
| 缓存命中输入价 | flash `0.02 元/百万 tokens`，pro `0.025 元/百万 tokens` |
| 缓存未命中输入价 | flash `1 元/百万 tokens`，pro `3 元/百万 tokens` |
| 输出价 | flash `2 元/百万 tokens`，pro `6 元/百万 tokens` |
| 并发限制 | flash `2500`，pro `500` |
| 生效/兼容说明 | 截图脚注中涉及模型兼容和日期说明，必须原样保守记录 |

注意：这些字段只有在截图来源被确认为官方价格页时，才能进入正式 Claim。否则只能写为“用户提供截图显示……，建议复核官方价格页”。

#### 7.8.5 分析重算

补充 Evidence 后，应只局部影响 DeepSeek 相关分析：

1. 更新 DeepSeek `PricingModel` 或互联网产品商业模式 metadata。
2. 更新 DeepSeek 相关 Claim 的 `evidence_ids`。
3. 更新 DeepSeek 相关 `CompetitionEdge.score_breakdown.evidence_confidence`。
4. 若商业模式切片从 `unknown` 变成 `api_pricing_verified`，竞争图谱可新增或刷新该切片。
5. Writer 更新 DeepSeek Battlecard、GapMatrix、OpportunityMap 和风险边界。

不应影响：

1. 豆包、Kimi、千问、腾讯元宝的无关功能 Claim。
2. 没有价格证据支持的市场热度、下载量、用户规模结论。
3. 现有自动猫砂盆 Demo。

#### 7.8.6 Trace 展示

Trace 中应展示：

| 模块 | 内容 |
|---|---|
| Evidence Gap | DeepSeek API 定价缺失 |
| Human Review | 用户补充截图 |
| 新 Evidence | `ev_ip_deepseek_api_pricing_user_upload_001` |
| Diff | `pricing.api_price_table: missing -> available` |
| Analysis Recompute | DeepSeek 相关 Claim/CompetitionEdge 局部刷新 |
| Writer Update | 报告中 DeepSeek 价格边界从“暂无可靠数据”变为“有截图证据，仍需保留时效边界” |

#### 7.8.7 验收口径

该闭环完成后，应满足：

1. 初始分析能明确提示 DeepSeek API 定价证据缺口。
2. 用户能补充截图或官方价格 URL。
3. 补充后生成新的 Evidence，而不是直接改报告文本。
4. DeepSeek 相关 Claim 绑定新 Evidence。
5. 报告中仍保留截图来源、访问时间和时效风险。
6. Trace 能看到补证据前后 Diff。

### 7.9 前端

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

### 7.10 Stage 2：内置候选发现

Stage 2 先实现“内置候选发现”，不做全网搜索。用户只输入目标产品链接，系统根据领域配置加载本地候选池，形成候选竞品集合；后续仍由 Evidence、QA 和 CompetitionEdgeScore 判断候选是否构成真实竞争关系。

这条能力适用于猫砂盆和豆包两条线：

```text
用户输入目标链接
  -> 识别领域
  -> 加载领域内置候选池
  -> 匹配目标产品
  -> 标记目标和候选角色
  -> Collection 读取候选 Evidence
  -> Analysis 召回和评分
  -> QA 检查缺证据/缺字段
  -> Writer 生成报告
```

#### 7.10.1 输入

豆包示例：

```json
{
  "target_product_url": "https://www.doubao.com/chat/",
  "category": "互联网产品",
  "subcategory": "AI 助手",
  "data_source_mode": "builtin_candidates"
}
```

猫砂盆示例：

```json
{
  "target_product_url": "本地快照中某个自动猫砂盆商品链接",
  "category": "智能宠物硬件",
  "subcategory": "自动猫砂盆",
  "data_source_mode": "builtin_candidates"
}
```

说明：

1. `builtin_candidates` 是新模式，语义是“从领域候选池自动带出候选竞品”。
2. 它不访问搜索引擎，不发现候选池之外的新竞品。
3. 候选池仍是本地快照或本地配置，保证 Demo 可复现。
4. `snapshot_plus_live` 继续表示“已知 URL 增强”，不承担候选发现。

#### 7.10.2 猫砂盆实现方式

猫砂盆候选池优先复用：

```text
data/snapshots/demo_sku_snapshot.json
```

流程：

1. 用户输入某个自动猫砂盆商品链接。
2. TaskCreation 根据 URL 在快照中匹配目标 SKU。
3. Snapshot Loader 将命中 SKU 标为 `target`，其余 SKU 保留为候选。
4. Analysis Agent 按同类相似、需求替代、内容共现、渠道替代召回竞品。
5. QA 继续检查价格访问时间、截图、Claim Evidence 绑定等。

这相当于把当前猫砂盆快照显式产品化为“候选池”，而不是改变现有分析逻辑。

#### 7.10.3 豆包实现方式

豆包候选池优先复用：

```text
data/snapshots/internet_ai_assistant_snapshot.json
```

流程：

1. 用户输入 `https://www.doubao.com/chat/`。
2. TaskCreation 根据 URL 或产品名识别目标为豆包。
3. Candidate Pool 自动带出 Kimi、DeepSeek、千问、腾讯元宝。
4. Collection 读取这些候选已有官网快照和截图 Evidence。
5. Analysis Agent 按日常问答、长文档研究、内容创作、编程推理、办公协作、生态入口等维度评分。
6. QA 对 DeepSeek 定价、应用市场、登录后截图等缺口给出补证据提示。

#### 7.10.4 候选池文件

建议新增统一候选池配置，而不是把逻辑散落在 Agent 中：

```text
backend/app/services/candidate_pool.py
```

配置示例：

```json
{
  "domain_key": "internet_ai_assistant",
  "pool_id": "internet_ai_assistant_v1",
  "snapshot_path": "data/snapshots/internet_ai_assistant_snapshot.json",
  "default_candidates": ["kimi", "deepseek", "qianwen", "yuanbao"],
  "target_match_fields": ["product_url", "official_urls", "name", "product_id"]
}
```

猫砂盆配置示例：

```json
{
  "domain_key": "smart_litter_box",
  "pool_id": "smart_litter_box_v1",
  "snapshot_path": "data/snapshots/demo_sku_snapshot.json",
  "default_candidates": "all_snapshot_skus_except_target",
  "target_match_fields": ["source_url", "name", "sku_id", "product_id"]
}
```

#### 7.10.5 候选状态

内置候选应有状态，避免把“候选”误写成“确定竞品”：

```text
candidate_loaded
target_matched
target_unmatched
selected_for_analysis
excluded_by_rules
needs_evidence
```

状态说明：

| 状态 | 含义 |
|---|---|
| `candidate_loaded` | 从领域候选池加载，但尚未评分 |
| `target_matched` | 用户输入命中候选池目标 |
| `target_unmatched` | 用户输入未命中候选池，只能创建低置信目标 |
| `selected_for_analysis` | Analysis 召回进入竞品关系评分 |
| `excluded_by_rules` | 候选与目标关系弱，暂不进入报告重点 |
| `needs_evidence` | 候选存在关键证据缺口 |

#### 7.10.6 QA 与证据缺口

内置候选发现后，QA 必须明确区分三类问题：

1. 候选池问题：候选是否应该纳入本领域。
2. 目标匹配问题：用户输入是否命中候选池目标。
3. 证据缺口问题：候选虽然存在，但定价、截图、应用市场、功能页等证据不足。

示例：

```text
DeepSeek 已从 AI 助手候选池加载，但 API 定价缺少可引用 Evidence。
请补充官方价格页 URL 或截图；补充前报告只能写“暂无可靠定价数据”。
```

#### 7.10.7 前端交互

输入页新增模式：

```text
数据模式：
  demo_snapshot
  snapshot_plus_live
  builtin_candidates
```

`builtin_candidates` 启动后，前端应展示候选池摘要：

| 区域 | 猫砂盆 | 豆包 |
|---|---|---|
| 目标识别 | 命中的目标 SKU | 豆包 |
| 候选池 | 14 个本地 SKU | Kimi、DeepSeek、千问、腾讯元宝 |
| 候选来源 | 本地脱敏 SKU 快照 | 官方公开页快照 |
| 加载方式 | 自动加载猫砂盆内置候选池 | 自动加载 AI 助手内置候选池 |
| 缺口提示 | 价格访问时间/截图等 | 定价、应用市场、登录后截图等 |

用户可以：

1. 继续使用默认候选池。
2. 移除某个候选。
3. 标记某个候选为 reference。
4. 补充候选证据，例如 DeepSeek API 价格截图。

#### 7.10.8 Trace 展示

Trace 中应展示候选发现过程：

| 字段 | 说明 |
|---|---|
| `candidate_discovery_mode` | `builtin_candidates` |
| `candidate_pool_id` | 候选池 ID |
| `candidate_pool_path` | 候选池路径 |
| `target_match_basis` | URL / 名称 / 未命中 |
| `candidate_count` | 候选数量 |
| `selected_for_analysis_count` | 进入评分的候选数量 |
| `candidate_pool_loaded` | `true` |
| `candidate_source_type` | `builtin_candidate_pool` |

#### 7.10.9 未来搜索发现边界

真正的全网搜索不进入当前 MVP。如果后续要做，应单独命名为：

```text
search_discovery
```

并必须满足：

1. 使用受控搜索 API，不直接抓搜索结果 HTML 作为稳定依赖。
2. 搜索结果只作为候选 URL，不作为事实 Evidence。
3. 官网校验通过后才抓取。
4. 非官网、媒体、论坛、榜单、下载站不进入正式评分。
5. 需要单独的 QA 和人工确认入口。

#### 7.10.10 验收口径

该能力完成后，应满足：

1. 猫砂盆用户只输入目标商品链接，也能从本地候选池带出候选 SKU。
2. 豆包用户只输入 `https://www.doubao.com/chat/`，也能带出 Kimi、DeepSeek、千问、腾讯元宝。
3. 前端和 Trace 明确显示“已自动加载内置候选池”，并展示候选池名称、来源和候选数量。
4. 候选进入分析前仍需 Evidence 和 QA 检查。
5. 候选不等于结论，报告只展示经过评分和证据支持的竞争关系。
6. 缺定价、缺截图、缺应用市场数据会被明确提示并允许用户补证据。

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

完成记录：

1. 已新增本迁移计划文档和 `data/snapshots/internet_ai_assistant_README.md`，定义 AI 助手本地快照、Evidence 字段、缺失证据边界和 QA 打回 fixture。
2. 已新增 `backend/tests/test_internet_product_snapshot_contract.py`，锁定不少于 5 个产品、默认目标豆包、核心竞品集合、每个产品 Evidence 和敏感字段扫描。
3. 已通过互联网产品快照契约测试，并在后续后端全量回归中持续覆盖。

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

完成记录：

1. 已新增 `data/snapshots/internet_ai_assistant_snapshot.json`，覆盖豆包、Kimi、DeepSeek、千问、腾讯元宝，并保留本地公开页 HTML、可见文本和截图路径。
2. 已新增 `data/snapshots/internet_ai_assistant_missing_data.md` 和 `data/snapshots/internet_ai_assistant_data_quality_report.json`，说明缺失字段、证据边界和 QA 打回样例。
3. 已固定 Kimi 官方首页 `ev_ip_kimi_homepage` 缺少 Evidence 截图字段，修复夹具指向 `data/raw/internet_ai_assistant/kimi/homepage.png`。
4. 已通过快照 JSON 解析、Evidence 来源、访问时间和 QA fixture 相关契约测试。

### 步骤 03：新增领域配置服务

任务：

1. 新增 `backend/app/services/domain_profiles.py`。
2. 根据 `category/subcategory` 推导 `domain_key`。
3. 返回当前领域的快照路径、标签、切片、QA 关键词和报告模板。
4. 在领域配置中声明候选池 ID、候选池路径、目标匹配字段和候选池加载展示文案。

测试：

1. 猫砂盆领域仍返回旧快照路径。
2. AI 助手领域返回新快照路径。
3. 未知领域返回标准错误或保守兜底。
4. 猫砂盆和 AI 助手领域都能返回候选池配置。

完成记录：

1. 已新增 `backend/app/services/domain_profiles.py`，集中提供猫砂盆与 AI 助手领域配置、快照路径、标签、切片、QA 关键词、报告语境和候选池配置。
2. 已支持根据 `category/subcategory`、目标 URL 和目标名称推导 `domain_key`，豆包 URL 可推导到 `internet_ai_assistant`。
3. 已新增 `backend/tests/test_domain_profiles.py`，覆盖猫砂盆旧快照、AI 助手新快照、未知领域兜底和候选池配置。
4. 已通过领域配置服务相关测试，并在任务创建、Collection、Analysis、Writer 回归中持续覆盖。

### 步骤 04：新增内置候选池服务

任务：

1. 新增 `backend/app/services/candidate_pool.py`。
2. 支持 `builtin_candidates` 数据模式：读取领域配置，加载本地候选池，并根据 URL、名称或 ID 匹配目标产品。
3. 猫砂盆候选池复用 `data/snapshots/demo_sku_snapshot.json`：命中目标 SKU 后，其余 SKU 作为候选进入 Collection。
4. 豆包候选池复用 `data/snapshots/internet_ai_assistant_snapshot.json`：命中豆包后，自动带出 Kimi、DeepSeek、千问、腾讯元宝。
5. 写入候选发现 Trace metadata：`candidate_discovery_mode`、`candidate_pool_id`、`candidate_pool_path`、`target_match_basis`、`candidate_count`、`selected_target_id`、`candidate_pool_loaded=true`、`candidate_source_type=builtin_candidate_pool`。
6. 不调用搜索引擎，不抓取候选池之外的新竞品；候选只表示“待分析对象”，不表示已经形成竞争结论。

测试：

1. 猫砂盆用户只输入快照中某个商品链接时，可以匹配目标 SKU 并加载同池候选。
2. 豆包用户只输入 `https://www.doubao.com/chat/` 时，可以匹配豆包并加载 Kimi、DeepSeek、千问、腾讯元宝。
3. 未命中目标时生成 `target_unmatched` 或等价保守状态，并提示目标证据缺口。
4. Trace 中明确记录 `candidate_discovery_mode=builtin_candidates`、`candidate_pool_loaded=true` 和候选池名称。
5. 候选状态保持为 `candidate_loaded` / `needs_evidence`，不得在候选池阶段写成确定竞品。

完成记录：

1. 已新增 `backend/app/services/candidate_pool.py`，支持 `builtin_candidates` 从领域候选池按 URL、名称或 ID 匹配目标产品。
2. 猫砂盆候选池复用 `demo_sku_snapshot.json`；AI 助手候选池复用 `internet_ai_assistant_snapshot.json`，豆包输入稳定加载 Kimi、DeepSeek、千问、腾讯元宝。
3. 候选池 metadata 已写入任务和 Collection Trace，包括 `candidate_discovery_mode`、`candidate_pool_id`、`candidate_pool_loaded`、`candidate_source_type`、`target_match_basis` 和候选数量。
4. 未命中目标时保持证据缺口状态，不调用搜索引擎，也不把候选池加载结果写成确定竞争结论。
5. 已新增并通过 `backend/tests/test_candidate_pool.py`，并由任务创建、Collection 和端到端测试继续验证。

### 步骤 05：新增互联网产品 Snapshot Loader

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

完成记录：

1. 已新增 `backend/app/services/internet_product_snapshot_loader.py`，将 AI 助手快照转换为 `Product`、`Evidence` 和 `ReviewInsight`。
2. Loader 保留缺失字段和缺失原因，不补造定价、下载量、用户规模、模型能力、排名或隐私安全事实。
3. 本地截图路径已转换为前端可访问的 `/assets/raw/internet_ai_assistant/...` 资源路径。
4. 已新增并通过 `backend/tests/test_internet_product_snapshot_loader.py`，覆盖加载 5 个产品、豆包目标标记、竞品角色、Evidence 关联、缺失字段和 Pydantic JSON 输出。

### 步骤 06：任务创建和 Collection 接入领域分流

任务：

1. `POST /tasks` 支持创建 AI 助手分析任务。
2. 任务 metadata 写入 `domain_key`。
3. Collection Agent 根据 `domain_key` 调用对应 Loader。
4. `snapshot_plus_live` 对新领域仍只访问已知 URL。
5. `builtin_candidates` 模式先调用候选池服务，再把命中的目标和候选交给对应 Loader。

测试：

1. 创建豆包任务成功。
2. Collection 产出豆包和 4 个竞品。
3. 旧猫砂盆任务不受影响。
4. Trace 中能看到正确的快照文件和领域信息。
5. 猫砂盆与豆包的 `builtin_candidates` 创建链路都能进入 Collection。

完成记录：

1. `POST /tasks` 已支持创建 AI 助手任务，并在 metadata 中写入 `domain_key=internet_ai_assistant`、候选池匹配结果和目标选择信息。
2. Collection Agent 已按 `domain_key` 分流到猫砂盆 Snapshot Loader 或 AI 助手 Snapshot Loader，并把候选池 metadata 复制到 Collection Trace。
3. `builtin_candidates` 已接入任务创建与 Collection，豆包输入可稳定产出豆包和 4 个核心竞品；猫砂盆旧链路保持兼容。
4. `snapshot_plus_live` 对新领域仍限定为已知 URL 增强，不做互联网竞品发现。
5. 已通过 `backend/tests/test_tasks_api.py`、`backend/tests/test_collection_agent.py` 和相关端到端任务执行测试。

### 步骤 07：Analysis Agent 领域化

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

完成记录：

1. Analysis Agent 已根据 `domain_key` 切换硬件/猫砂盆关键词与 AI 助手关键词、召回逻辑、切片解释和证据边界。
2. AI 助手领域已使用“商业模式 / 人群 / 场景”切片，并保持既有 `CompetitionEdgeScore` 评分公式不变。
3. 豆包任务可生成至少 4 条竞争边，每条边绑定 Claim；Claim 绑定 Evidence 或显式标记风险/缺证据。
4. 已新增并通过 AI 助手 Analysis 覆盖测试，猫砂盆既有 Analysis 回归仍通过。

### 步骤 08：QA 规则扩展与真实打回

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

完成记录：

1. 已扩展 AI 助手时效字段、关键截图和敏感绝对化表达 QA 规则。
2. 已固定 Kimi 官方首页 `ev_ip_kimi_homepage` 缺失截图为可复现打回样例。
3. 已验证豆包 `builtin_candidates` 端到端任务会触发 Collection 打回、补齐截图、Analysis 重算、二轮 QA 通过并生成报告。
4. 已通过 `test_qa_rules.py`、Kimi 修复单测和 `test_task_execution.py` 相关端到端测试。

### 步骤 09：报告和 Word 导出适配

任务：

1. Writer 根据 `domain_key` 选择互联网产品报告章节。
2. Battlecard、GapMatrix、OpportunityMap 使用 AI 助手语境。
3. Word 导出保留 Evidence、Claim、置信度、访问时间和推断标识。

测试：

1. 网页报告展示互联网产品章节。
2. Word 导出成功。
3. 报告不包含 API Key、Cookie 或未脱敏隐私。
4. 无证据信息显示“暂无可靠数据”或“建议复核”。

完成记录：

1. Writer 已根据 `domain_key=internet_ai_assistant` 生成 AI 助手语境的正式报告章节，报告标题、研究范围、竞争格局、Battlecard、GapMatrix、OpportunityMap 和风险边界均使用互联网产品口径。
2. Markdown 导出后端接口已恢复用于后端导出适配验证，前端仍不新增 Markdown 用户入口。
3. Word 导出已适配 AI 助手报告标题、主题、切片轴和证据边界，保留 Evidence、Claim、置信度、访问时间、QA 记录和 Trace 附录。
4. 已清理 AI 助手报告中的自动猫砂盆、自动清理、除臭、铲屎、销量和认证等硬件/电商语境泄漏；无证据的定价、用户规模、下载量、模型能力和隐私安全结论继续写“暂无可靠数据”或“建议复核”。
5. 已通过报告 API、Writer、Markdown 渲染、Word 导出、报告质量规则和豆包端到端 QA 打回链路相关测试。

### 步骤 10：前端页面适配

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

完成记录：

1. 输入页已支持选择“互联网产品 / AI 助手”，默认填入 `https://www.doubao.com/chat/`，并在 `builtin_candidates` 模式下展示 AI 助手内置候选池提示。
2. 总览页、画像页、竞争图谱页和报告页已根据领域切换展示标签；AI 助手语境下将价格相关标签改为“商业模式/付费层”“商业模式与证据”“产品入口”等。
3. 竞争图谱页、报告页和 Trace 页已补齐 `builtin_candidates`、`builtin_candidate_pool`、`internet_ai_assistant` 以及官方来源类型的用户可读翻译，保留 DAG、QA 打回和 Diff 展示。
4. 已新增 `frontend/src/domain/domainProfiles.ts`，集中管理猫砂盆和 AI 助手前端领域标签，避免在页面中散落硬编码判断。
5. 已新增 Playwright 用例 `frontend/e2e/doubao-report.e2e.spec.ts`，使用真实后端和 Vite 预览创建豆包内置候选池任务，并验证报告页可见豆包、Kimi、商业模式/付费层、AI 助手语境和 Word 下载入口。
6. 已通过前端组件/契约测试、TypeScript 类型检查、生产构建和豆包 Playwright 端到端验证。

### 步骤 11：演示冻结

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

完成记录：

1. 已新增稳定输入 `demo/internet-ai-assistant-stable-input.json`，固定目标入口为 `https://www.doubao.com/chat/`，领域为“互联网产品 / AI 助手”，数据模式为 `builtin_candidates`，并保持目标名称可由候选池匹配补全。
2. 已新增答辩脚本 `demo/internet-ai-assistant-script.md`，固定豆包演示路径、4 个核心竞品、QA 打回样例、Trace 展示点和证据边界讲法。
3. 已扩展 `backend/tests/test_demo_freeze.py`，锁定互联网产品快照 SHA256、稳定输入、核心竞品集合、Kimi 缺截图 QA fixture、同一输入稳定结果形状、AI 助手报告章节和硬件语境不泄漏。
4. 已验证同一豆包冻结输入稳定匹配豆包，稳定带出 Kimi、DeepSeek、千问、腾讯元宝，稳定触发并修复 `CRITICAL_EVIDENCE_MISSING_SCREENSHOT`，最终 QA 通过并生成 AI 助手语境报告。
5. 已通过 `backend\.conda312\python.exe -m pytest backend\tests\test_demo_freeze.py -q`，6 个冻结回归测试通过。

## 9. 代码影响范围

### 9.1 后端文件

预计新增：

```text
backend/app/services/domain_profiles.py
backend/app/services/candidate_pool.py
backend/app/services/internet_product_snapshot_loader.py
backend/tests/test_domain_profiles.py
backend/tests/test_candidate_pool.py
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
11. 猫砂盆在 `builtin_candidates` 模式下，只输入目标商品链接即可从 `demo_sku_snapshot.json` 加载候选 SKU。
12. 豆包在 `builtin_candidates` 模式下，只输入 `https://www.doubao.com/chat/` 即可加载 Kimi、DeepSeek、千问、腾讯元宝候选。
13. Trace 和前端候选摘要明确展示“已自动加载内置候选池”、候选池来源和候选数量。
14. 候选池阶段不直接输出竞争结论，最终报告只展示经过 Evidence、QA 和 Analysis 支持的竞争关系。

### 10.2 质量验收

1. 不破坏现有自动猫砂盆 Demo。
2. 不引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或微服务架构。
3. 没有把模拟数据当作最终演示数据。
4. 所有价格、评分、排名、下载量、模型能力、商业模式等事实必须有 Evidence。
5. 推断内容显式标记。
6. 缺证据时写“暂无可靠数据”或“建议复核”。
7. `builtin_candidates` 不得调用搜索引擎，也不得把候选池之外的产品自动纳入评分。
8. 用户补充截图或 URL 只能作为新增 Evidence 进入局部重算，不能覆盖原始快照事实。

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
