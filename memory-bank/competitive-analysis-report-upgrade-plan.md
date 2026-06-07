# 竞品分析报告智能化升级调研与可行性计划

## 1. 背景与目标

当前系统已经具备 LangGraph DAG、Collection/Analysis/QA/Writer 四类 Agent、Evidence/Claim 绑定、QA 打回、Trace、网页报告和 Word 导出等 MVP 核心能力。但从实际阅读体验看，报告仍有明显的“信息搬运感”：

1. 同一 SKU 的价格、卖点、评论摘要、证据状态会在总览、画像、图谱、报告、附录中多次重复。
2. Analysis Agent 主要完成竞品召回、关系评分和证据绑定，尚未把“商业问题”抽象成一等分析产物。
3. Writer Agent 虽已加入章节级 LLM、KnowledgeArtifact 和质检修复，但输入仍以 Product/Evidence/CompetitionEdge 为主，容易把结构化字段翻译成段落。
4. 报告章节更像“系统产物展示”，不像商业竞品分析常见的“结论、格局、差距、机会、打法、风险、下一步动作”。
5. 智能分析的可解释点主要体现在 Trace，而不是体现在最终报告的推理层级上。

本文档只提供调研结论和可行性计划，不修改代码。

## 2. 外部调研摘要

### 2.1 商业竞品分析报告常见形态

商业性更强的竞品分析报告通常不是简单汇总竞品信息，而是围绕决策问题组织：

| 来源类型 | 典型做法 | 可借鉴点 |
|---|---|---|
| Gartner Magic Quadrant | 用两个高阶坐标归纳市场格局，并为每个厂商给出 strengths/cautions | 把 SKU 信息压缩成“格局位置 + 优势 + 风险”，避免流水账 |
| Forrester Wave | 按 Current Offering、Strategy、Market Presence 等维度评分，并说明选择依据 | 把评分维度和商业解释绑定，输出“为什么现在该关注它” |
| G2 Grid | 结合用户满意度、市场存在感、评论信号形成象限 | 评论不是原文摘录，而是转成满意度、阻碍、购买理由等信号 |
| Similarweb / Semrush / Ahrefs | 输出流量份额、渠道来源、关键词缺口、受众重叠和机会 | 即使本项目没有实时采集，也可借鉴“差距矩阵、机会清单、优先级” |
| Klue / Crayon 等 CI 平台 | 强调 battlecard、win/loss、竞品动态、销售打法和应答话术 | 报告要有“对抗动作”：用户问什么、竞品怎么打、我方怎么回应 |
| 电商商品竞品工具 | 关注价格带、评价痛点、卖点表达、转化阻碍、Review mining、Listing gap | 自动猫砂盆 MVP 最该吸收“评论痛点 -> 产品/表达动作”的链路 |

这些报告的共性：

1. 第一屏给判断，不先给资料。
2. 每个竞品只保留与目标产品有关的差异，不展开完整 SKU 档案。
3. 评分必须能回答商业问题，例如“谁最威胁转化”“在哪个价格带会被替代”“哪个卖点要补证据”。
4. 证据以脚注、引用、附录、风险标记出现，正文避免反复展示相同字段。
5. 报告必须有可执行建议，且建议要绑定责任方向、优先级、预期影响和所需证据。

### 2.2 GitHub / Agent 项目扩展扫描

补充检索了 `competitor-analysis`、`competitive-intelligence`、`market-research`、`product-research`、`battlecard`、`review mining`、`Amazon research`、`MCP`、`deep research agent` 等方向。按 2026-06-07 打开的 GitHub topic 页，`competitor-analysis` 显示 172 个公开仓库，`competitive-intelligence` 显示 127 个公开仓库，`market-research` 显示 488 个公开仓库。真正能直接用于本项目的代码并不多，原因是很多仓库停留在网页 Demo、Notebook、一次性爬虫、Prompt 模板或通用研究 Agent；但这些项目在“报告结构、外采证据、研究计划、评论洞察、机会排序”上有不少可吸收的模式。

本轮纳入判断的代表样本如下。这里的“分析”不是说它们都适合复用，而是把它们放到同一张雷达图里，看哪些思路值得被吸收到当前项目。

| 序号 | 仓库/项目 | 类型 | 主要观察 | 对当前项目的借鉴优先级 |
|---:|---|---|---|---|
| 1 | `brightdata/competitive-intelligence` | 多 Agent 竞品情报平台 | Researcher/Analyst/Writer 三段式，支持 Web scraping、SWOT、威胁评估、执行报告、实时进度 | 高：借鉴 agent 分工和实时 trace；不借鉴 Bright Data 依赖 |
| 2 | `damionrashford/RivalSearchMCP` | 竞品搜索 MCP | 多搜索源、社媒、学术库、新闻、实体画像、冲突检测，强调结构化输出和无内置 LLM | 高：借鉴 ToolCall 外采、conflict detection、source registry |
| 3 | `ferdinandobons/startup-skill` | Startup / CI Skill | Startup validation、competitive intelligence、planning、pricing、battle cards | 高：借鉴 battlecard、定价分析、验证清单 |
| 4 | `emotixco/claude-skills-founder` | Founder Skill Pack | 面向创始人的产品 brief、竞品分析、定价、GTM、Pitch Deck | 中高：借鉴面向决策者的报告口径 |
| 5 | `unicodeveloper/competitor-analysis` | 竞品分析应用 | 输出 competitor insights、产品、市场定位、策略 | 中：作为“从信息汇总走向商业分析”的对照样本 |
| 6 | `FardinHash/competitor-analysis` | 多源 SWOT / PDF 报告 | Google、Wikipedia、Reddit 多源输入，生成 SWOT 和 PDF | 中高：借鉴多源输入后统一成 Evidence 和报告；SWOT 必须证据化 |
| 7 | `gokborayilmaz/competitor-analysis-agent` | 网站竞品分析 Agent | 输入竞品网站，自动输出功能、价格、定位、策略洞察 | 中：借鉴 website-to-structured-report；项目较新，不能作为稳定工程参照 |
| 8 | `parallel-web/competitive-analysis-demo` | Competitive analysis Demo | 一次请求覆盖多字段，包括 Reddit sentiment、投资历史、功能一致性、竞品 mapping | 中：借鉴多字段问题集和批量结构化抽取 |
| 9 | `wizenheimer/subsignal` | Deal flow / CI 监控基础设施 | 面向 VC/Founder 的开放监控基础设施 | 中：借鉴监控对象和变化事件，不扩展到 VC 场景 |
| 10 | `ishwarjha/claude-marketing-research-skill` | Marketing research Skill | Competitor analysis、avatar profiling、positioning、value proposition、mental models | 高：借鉴人群画像、定位、价值主张的连接方式 |
| 11 | `gnurio/porter-strategy-skills` | Porter 战略 Skill | Five Forces、competitor profiling、strategic groups、market signals、competitive moves | 高：借鉴竞争轴和战略分组，不照搬过重战略术语 |
| 12 | `eph5xx/tweakidea` | Startup idea evaluation | 对创业想法做 1-5 评分，涉及市场研究、PMF、竞品 | 中：借鉴 scorecard 和 go/no-go，但不把 SKU 报告写成立项报告 |
| 13 | `domini-67/facebook-ads-library-scraper` | 广告情报采集 | Facebook Ads 数据抽取 | 低中：借鉴广告创意/话术作为未来外采源，MVP 不接入 |
| 14 | `anyin-ai/aperture` | AI visibility / brand monitoring | 监控品牌在 ChatGPT、Perplexity、Google AI Overviews 等场景的出现方式 | 中：借鉴“品牌可见性/话术占位”的报告维度 |
| 15 | `jrr996shujin-png/openclaw-seo-aeo-skills` | SEO/AEO Skill Pack | 网站健康、Reddit/Quora 问题挖掘、关键词排名、竞品内容、月报 | 中高：借鉴问题挖掘和内容 gap，不引入 SEO 平台 |
| 16 | `mshahiddigital/agentic-local-seo-audit` | Local SEO audit Agent | 21 阶段审计、24 skills、6 sub-agents、竞品分析和 roadmap | 中：借鉴审计清单和 roadmap 结构，避免流程过重 |
| 17 | `seancrowe01/ads-machine` | 广告闭环情报 | 抓竞品广告、按 longevity 打分、生成 hooks 库、写脚本 | 中：借鉴“高频卖点/钩子”沉淀，不做投放自动化 |
| 18 | `giobi/brain-seo-template` | Markdown-first SEO/竞品管理 | 用 Git/Markdown 管理关键词、内容和竞品分析 | 中：借鉴轻量知识库和文档化流程 |
| 19 | `bodapi/google-data-intelligence-hub` | Google 数据采集 | SERP、Travel、Commerce、Visual search 数据抽取 | 低中：借鉴 SERP/Commerce 作为外采方向，MVP 不接入 |
| 20 | `compiuta-origin/sonde-analytics` | LLM brand analytics | 分析品牌在 LLM 响应中的出现情况 | 中：可成为未来“AI 搜索口碑/可见性”扩展 |
| 21 | `Laksh-star/competitive-intelligence` | AI CI Monitor | CocoIndex、Tavily Search、LLM extraction，偏 pipeline | 中：借鉴检索-抽取-索引分层；不引入 PostgreSQL/CocoIndex |
| 22 | `zircote/sigint` | Market intelligence toolkit | Iterative research、trend modeling、multi-format reports、自动 issue | 中高：借鉴“趋势/假设/证据”三值逻辑和多格式报告 |
| 23 | `g-baskin/recon` | Competitive reconnaissance Skill | 网站、技术栈、API、社区、基础设施五阶段侦察 | 中：借鉴分阶段 research plan；电商 SKU 场景只取网站/社区部分 |
| 24 | `ekinciio/saas-growth-marketing-skills` | SaaS growth marketing Skills | ASO/GEO/SEO/CRO/PLG/pricing/competitor intel | 中：借鉴 funnel、pricing、CRO 视角 |
| 25 | `FlowExtractAPI/ai-powered-facebook-ads-scraper-n8n` | 广告 CI 自动化 | 自然语言查询 Facebook Ads，N8N + AI 抽取 | 低中：外采形态参考，技术栈不纳入 |
| 26 | `aj-dev-sys/awesome-competitive-intelligence` | CI 资源列表 | Competitive intelligence 工具/资源/指南集合 | 中：作为后续工具雷达入口 |
| 27 | `oxnr/repo-intel` | GitHub repo intelligence | 监控竞品 GitHub 活动并生成 strategic digests | 低中：软件竞品适用，自动猫砂盆仅借鉴 change digest 思路 |
| 28 | `Marciompi/Strategic-Competitive-Intelligence` | 专利/文本挖掘 CI | 用专利代码和文本挖掘做 emerging tech 竞争情报 | 低：方法论有价值，SKU MVP 暂不做专利 |
| 29 | `liuxiaotong/ai-dataset-radar` | 多源异步 CI 引擎 | 增量扫描、异常检测、CLI + MCP | 中：借鉴 watermark/incremental scan 概念，MVP 先不做 |
| 30 | `sikkrasmus/company-index-framework` | GTM/RevOps 知识库框架 | Schema、routing、conflict resolution、battlecards、agents.md | 高：借鉴知识库 schema 和冲突处理 |
| 31 | `mnemox-ai/idea-reality-mcp` | Idea validation MCP | 扫 GitHub、HN、npm、PyPI、Product Hunt 做 reality check | 中：借鉴 pre-check 和可行性风险评分 |
| 32 | `expectedparrot/edsl` | AI survey / market research | AI-powered surveys、experiments、合成受访者、结果分析 | 中：借鉴问卷/访谈结构化，注意不能把合成数据当演示事实 |
| 33 | `akvise/trends-checker` | Google Trends CLI | Trends、关键词、市场验证、CSV 输出 | 中：未来可作为趋势辅助；当前报告不能凭趋势缺失做判断 |
| 34 | `king-of-the-grackles/reddit-research-mcp` | Reddit research MCP | Reddit 结构化洞察、引用、语义搜索，用于竞品分析和 customer discovery | 高：借鉴 review/community signal cluster 和引用方式 |
| 35 | `AmitMY/grids` | Comparison grid standard | 标准化对比网格 | 中高：可借鉴 GapMatrix / Battlecard 的表格规范 |
| 36 | `leadita/tech-stack-datasets` | 公司/站点技术数据集 | 按技术栈聚合公司/网站开放数据 | 低：软件行业更适配，只借鉴 dataset schema |
| 37 | `Ericyoung-183/alpha-insights` | Business analysis Skill | Consulting frameworks、due diligence、market analysis | 中：借鉴咨询式结论组织 |
| 38 | `abinauv/business-consulting` | Business consulting Plugin | 16 skills、24 commands、行业 overlay、市场/竞品/定价/风险 | 中：借鉴 industry overlay，但不把 MVP 做成通用咨询平台 |
| 39 | `rhofkens/business-idea-multi-agent` | Business idea multi-agent | 多 Agent 生成和评估商业想法 | 中：借鉴评估 agent 的 scoring rubric |
| 40 | `nexscope-ai/Amazon-Skills` | Amazon 电商技能集 | 商品搜索、评论分析、榜单、Listing、价格、竞品洞察 | 很高：最贴近自动猫砂盆 SKU、review、price、listing gap |
| 41 | `majiayu000/claude-skill-registry/startup-review-mining` | Review mining Skill | 从评论/证言中抽痛点、feature gap、switching trigger、实验机会 | 很高：直接映射 `ReviewSignalCluster` 和 `OpportunityMap` |
| 42 | `karlyndiary/Amazon-Sentiment-Analysis-EDA` | Amazon Review EDA | 用 Amazon API/数据做评论情绪、Dashboard、产品改善洞察 | 中高：借鉴评论到产品改善的闭环 |
| 43 | `VaibhavAbhimanyooHiwase/Sentimental_Analysis_using_Opinion_Target_and_Opinion_Words` | Opinion target review analysis | 基于 opinion target 和 opinion words 分析 Amazon review | 中：借鉴 aspect/opinion target，但实现不必照搬 |
| 44 | `t-shah02/amazon-reviews-nlp-sentiment-analysis` | Amazon review NLP | NLTK/分类模型做评论情绪分析 | 中：评论 NLP 基线参考，报告层必须转成商业含义 |
| 45 | `aouataf-djillani/Amazon-review-sentiment-analysis` | Sentiment model comparison | Vader、SVM、Logistic Regression 对比 | 低中：模型比较参考，MVP 优先规则+LLM归纳 |

| 类别 | 代表仓库/项目 | 观察到的常见能力 | 可借鉴点 | 不建议照搬点 |
|---|---|---|---|---|
| 直接竞品分析 App | `unicodeveloper/competitor-analysis` | 输入站点或关键词后做基础竞品信息汇总 | 可作为“早期竞品分析工具长什么样”的反例：只有信息聚合会显得浅 | 项目较旧，工程和报告深度不适合直接复用 |
| 竞品搜索 MCP | `damionrashford/RivalSearchMCP` | 把竞品搜索封装成 MCP 工具，供 Agent 调用 | 可借鉴“外部检索作为 ToolCall，并进入 Trace” | MVP 不应因此引入完整 MCP 外采链路 |
| Startup/市场研究 Skill | `ferdinandobons/startup-skill` | 面向创业项目做市场、竞品、定位、机会分析 | 可借鉴“市场地图 + 定位差异 + 机会判断”的报告骨架 | 领域偏 startup，不适合照搬融资/公司维度 |
| 产品验证工具 | `Nirikshan95/VettIQ` | 产品 idea 验证、竞品检查、市场可行性评分 | 可借鉴 go/no-go、风险等级、验证清单 | 其目标是产品立项，不是 SKU 级竞品战场 |
| Amazon 电商研究 Skills | `nexscope-ai/Amazon-Skills` | 商品搜索、评论、榜单、Listing、价格等电商研究技能 | 非常贴近自动猫砂盆类目，可借鉴 Listing gap、评论信号、价格带观察 | 不直接接入其采集逻辑，避免 MVP 变成采集平台 |
| Bright Data Skills | `brightdata/skills` | 用外部采集能力获取商品页、评论、价格、社媒、搜索结果 | 可借鉴“采集结果必须带来源、时间、证据类型、可追溯” | Bright Data 依赖外部服务和大量爬取能力，超出 MVP 技术约束 |
| Competitive Intelligence Skill | `openclaw/skills/.../competitive-intelligence-market-research` | 结构化输出市场、竞品、SWOT、机会、威胁 | 可借鉴清晰的 research brief 和分析框架 | Skill 文档是方法论，不是工程实现 |
| Deep Research Agent | `assafelovic/gpt-researcher` | 多源检索、分解问题、生成带引用的研究报告 | 可借鉴 research planner、source credibility、引用密度控制 | 其通用联网研究链路较重，本项目当前不应整体迁移 |
| 多 Agent 研究框架 | `bytedance/deer-flow` 等 deep research 项目 | Planner/Researcher/Coder/Reporter 分工，多轮资料搜集和报告 | 可借鉴“先研究计划，再证据收集，再报告”的阶段结构 | 框架级替换会破坏现有 LangGraph MVP |
| CrewAI 竞品分析示例 | CrewAI 社区 competitor/market research 示例 | Researcher、Analyst、Writer 角色拆分明显 | 可借鉴角色提示词和任务分解 | 不引入 CrewAI；本项目已有 LangGraph DAG |
| LangChain/LangGraph Research Agent 示例 | LangChain/LangGraph 社区研究报告示例 | 节点化研究、工具调用、状态传递、报告生成 | 可借鉴“状态里保存中间分析 artifact” | 不需要换框架，只强化现有 Analysis 节点 |
| Battlecard Generator 类仓库 | GitHub 上多种 sales battlecard / competitor battlecard generator | 输出竞品强项、弱项、异议处理、销售话术 | 适合直接转成 `CompetitorBattlecard` Artifact | 注意宠物安全/认证表达要保守，不能自动生成夸大话术 |
| Review Mining 仓库 | Amazon/Yelp/App review mining、sentiment analysis 项目 | 评论聚类、情感、痛点、主题词、负面原因 | 可升级 `ReviewInsight` 为 `ReviewSignalCluster` | 不能只做情感正负，必须转成购买阻碍和动作 |
| Pricing Monitor 仓库 | competitor price tracking / ecommerce price monitor | 定时抓取价格、库存、折扣、变化提醒 | 可借鉴 price event、price band、变化事件的结构 | MVP 不做定时外采，不引入任务队列 |
| SEO/Traffic Gap 工具 | keyword gap、SERP competitor、Similarweb-like 示例 | 关键词缺口、流量渠道、页面表现对比 | 可借鉴 gap matrix 的表达方式 | 当前脱敏 SKU 快照不支持真实流量结论 |
| Ad/Creative Monitor 项目 | Facebook ads / Google ads library scraper 类项目 | 采集竞品广告创意和投放变化 | 可借鉴“卖点表达差距”和“话术变化事件” | 自动猫砂盆 MVP 暂无广告数据源，不应凭空推断 |
| Social Listening 项目 | Reddit/Twitter/YouTube comment monitoring | 社媒讨论、情绪、痛点、竞品口碑 | 可借鉴非结构化文本聚类方法 | 涉及平台合规和噪声过滤，MVP 暂缓 |
| Company/Market Map 工具 | company research、market map、startup landscape 项目 | 公司定位、竞品分层、相邻市场、替代方案 | 可借鉴“直接竞品/间接竞品/替代方案”分层 | 本项目核心仍是 SKU 竞争，不宜膨胀成公司研究 |
| E-commerce Listing Auditor | listing optimization / Amazon SEO analyzer | 标题、卖点、图片、FAQ、评价覆盖对比 | 可借鉴“表达差距”维度：卖点是否变成用户收益 | 图片/视频识别暂不扩展，先用已有字段和文本 |
| SWOT Generator 项目 | SWOT、Porter Five Forces、market analysis GPT 模板 | 快速生成 strengths/weaknesses/opportunities/threats | 可作为报告语言和结构参考 | SWOT 容易泛化，必须绑定证据和目标 SKU |
| RAG Research Assistant | 各类 document/web RAG research assistant | 来源管理、引用、摘要、去重、问答 | 可借鉴 evidence dedupe 和 source registry | 不需要引入向量库作为 MVP 前置条件 |
| Change Detection 工具 | website diff、price diff、content monitor | 记录网页变更、价格变动、文案变化 | 可借鉴 Trace 中展示“补采前后差异”的形式 | 当前快照数据没有持续监控，不做实时变化承诺 |
| Market Intelligence Dashboard | BI/dashboard 类开源项目 | 多维筛选、象限、趋势、指标卡 | 可借鉴前端展示：矩阵、优先级、过滤器 | 不把报告页做成复杂 BI 系统 |

### 2.3 GitHub 样本抽象出的共性模式

从更大范围仓库看，真正有价值的不是某一个项目，而是这些反复出现的分析模式：

| 模式 | 外部项目常见做法 | 对当前项目的落地方式 |
|---|---|---|
| Research Brief 先行 | 先定义要回答的问题、受众、范围、约束 | 新增 `StrategyBrief`，让报告先回答“本次分析服务什么决策” |
| Source Registry | 每条外部资料保留 URL、时间、可信度、提取方式 | 复用 Evidence，补强 `source_type`、`access_time`、`confidence`、`is_external` |
| Battlecard | 每个竞品都有强项、弱点、异议、回应话术 | 新增 `CompetitorBattlecard`，替代报告里的 SKU 罗列 |
| Gap Matrix | 把功能、价格、评论、表达、证据缺口矩阵化 | 新增 `GapMatrix`，让 Analysis 输出“差在哪里” |
| Review Signal Mining | 评论不只是摘要，而是聚类成痛点、购买理由、顾虑 | 新增或强化 `ReviewSignalCluster` |
| Opportunity Scoring | 机会按影响、置信度、成本、紧急度排序 | 新增 `OpportunityMap`，报告必须给 P0/P1/P2 动作 |
| Change Event | 价格/文案/评价变化被当作事件，不覆盖旧事实 | 未来外采时新增 `ChangeEvent`，MVP 可先用于 QA 补证前后 Diff |
| Evidence Conflict Check | 多源数据冲突时标记，不强行合并 | QA 增加证据冲突和过期检查 |
| Report Quality Gate | 检查重复、空洞建议、无证据结论、内部字段泄漏 | QA/Writer 前增加规则型报告质检 |
| Human Review Loop | 让人修正关键事实或判断，再局部重算 | 复用现有 Human Review，优先触发 Analysis 局部重算 |

### 2.4 对当前项目的取舍

结合这些仓库，建议保持一个清醒取舍：

1. **不直接复制外部仓库代码**：公开竞品分析项目大量是 Demo、Prompt 或单脚本爬虫，稳定性和合规性不足。
2. **不在 MVP 引入复杂外采平台**：真实采集、定时监控、反爬、代理池、平台合规都会显著扩大边界。
3. **优先吸收 Artifact 形状**：Battlecard、GapMatrix、OpportunityMap、ReviewSignalCluster 这些结构能直接改善“智能分析感”。
4. **优先吸收报告叙事**：先结论、再格局、再差距、再动作、最后证据边界，而不是先展示资料。
5. **外采只作为后续增强**：如果要做，先做“单页补证据 + 标准 Evidence + Trace + QA”的窄闭环。
6. **电商/Amazon 类项目优先参考**：它们比 SaaS/公司级竞品分析更接近自动猫砂盆 SKU、评论、价格、Listing、卖点表达的真实问题。

总体判断：GitHub 上可借鉴的项目数量不少，但最适合本项目的不是“拿来运行”，而是把它们沉淀过的分析套路变成我们自己的结构化 Agent Artifact。本项目仍应坚持 FastAPI + LangGraph + Pydantic + SQLite + React + Ant Design。

## 3. 当前项目诊断

### 3.1 已具备的基础

1. `CompetitionEdge` 已有竞争关系、切片、决策阶段、评分维度、Claim 绑定和风险标记。
2. `OverviewData` 已有一句话判断、决策可用状态、关键竞品、机会、风险和行动建议。
3. Writer 已有 8 个正式章节，并且支持章节级 LLM、KnowledgeArtifact、质量审查和一次性修复。
4. QA 已能通过缺失 evidence/access_time/screenshot 等字段触发真实打回。
5. Trace 能证明系统过程，但最终报告还没有充分吸收这种“分析过程价值”。

### 3.2 主要缺口

| 缺口 | 表现 | 根因 |
|---|---|---|
| 分析问题不清 | 报告像“有哪些竞品”，不像“目标产品该怎么打” | 缺少 Problem Framing / Strategy Brief Artifact |
| 重复展示事实 | 同样价格、卖点、证据数在多处出现 | 没有区分正文证据引用和附录证据索引 |
| 差距分析弱 | 竞品强在哪里、目标缺什么、先补什么不够尖锐 | Analysis 产物缺少 gap、threat、opportunity、countermove |
| 评论洞察浅 | 评论摘要被引用，但较少转成购买阻碍/异议/购买理由 | ReviewInsight 粒度不足 |
| 报告商业语气弱 | 章节名和内容更像系统记录 | Writer 缺少商业报告模板和 executive narrative |
| 智能分析不可见 | Trace 显示智能体，但报告里看不出推理链 | 缺少“判断链”：信号 -> 解释 -> 结论 -> 动作 |

## 4. 升级原则

1. 不引入新技术栈，不新增 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或实时采集平台。
2. 不削弱 Evidence、Claim、QA 打回、Trace 和 Human Review。
3. 不把模拟数据当最终演示数据；所有事实仍来自脱敏快照、用户研究文本或明确标记的本地知识框架。
4. 报告正文减少字段搬运，附录保留证据和审计。
5. “智能分析”必须成为结构化产物，而不是只靠 Writer 改写。
6. 找不到可靠证据时继续写“暂无可靠数据”，推断必须显式标记。

## 5. 建议新增或强化的分析 Artifact

### 5.1 StrategyBrief

目的：在报告前先形成商业问题框架。

建议字段：

| 字段 | 说明 |
|---|---|
| business_question | 本次分析回答的问题，例如“目标产品在 1500-2500 元价格带如何对抗低价自动猫砂盆” |
| target_segment | 本次最重要的人群/场景 |
| primary_competition_axis | 主要竞争轴：价格、除臭、清理负担、安全信任、容量、多猫等 |
| decision_owner_view | 面向产品/运营/内容的判断视角 |
| evidence_boundary | 本次数据能支持和不能支持什么 |

落点：Analysis Agent 生成，Writer 和 Overview 读取。

### 5.2 CompetitorBattlecard

目的：把每个核心竞品从“SKU 卡片”变成“对抗卡”。

建议字段：

| 字段 | 说明 |
|---|---|
| competitor_id | 竞品产品 ID |
| why_users_compare | 用户为什么会把它放进同一候选集 |
| competitor_strengths | 竞品强项，必须绑定 Claim/Evidence |
| competitor_weaknesses | 竞品弱点或证据不足点 |
| target_response | 目标产品应该如何回应 |
| sales_objection | 用户可能提出的异议 |
| response_talk_track | 保守、可证据化的话术建议 |
| priority | P0/P1/P2 |

落点：Analysis Agent 在已选 top edges 后生成；Writer 只负责表达，不再凭空组织。

### 5.3 GapMatrix

目的：让报告像真正分析报告，有“差距”和“机会”。

建议维度：

1. 功能能力差距：清洁、除臭、容量、安全、智能、维护成本。
2. 证据差距：价格时效、截图、评论聚类、认证材料、售后信息。
3. 表达差距：卖点是否转成用户收益、是否能解释长期成本。
4. 转化差距：在哪个决策阶段容易输。

建议字段：

| 字段 | 说明 |
|---|---|
| dimension | 差距维度 |
| target_status | 目标产品当前状态 |
| competitor_reference | 参照竞品或替代方案 |
| impact_on_decision | 对用户决策的影响 |
| evidence_ids | 支撑证据 |
| confidence | 置信度 |
| recommendation | 下一步动作 |

### 5.4 ReviewSignalCluster

目的：把评论摘要从“内容转述”变成“用户信号”。

建议字段：

| 字段 | 说明 |
|---|---|
| signal_type | pain / buying_reason / objection / trust_factor / maintenance_cost |
| signal_summary | 信号摘要 |
| affected_products | 影响产品 |
| related_decision_stage | 对应决策阶段 |
| evidence_ids | 来源 |
| action_hint | 对产品或内容表达的动作 |

当前 `ReviewInsight` 可以先不推倒重来，而是在 Analysis 或 Writer 前增加归一化服务，把已有评论摘要映射成上述结构。

### 5.5 OpportunityMap

目的：把机会从“建议补证据”提升为“可排序动作组合”。

建议字段：

| 字段 | 说明 |
|---|---|
| opportunity_id | 机会 ID |
| title | 机会标题 |
| opportunity_type | product / pricing / content / evidence / review / positioning |
| target_segment | 对应人群/场景 |
| why_now | 为什么当前优先 |
| expected_impact | 预期影响 |
| effort_level | 低/中/高 |
| confidence | 置信度 |
| linked_gaps | 关联 GapMatrix |
| linked_evidence_ids | 证据 |

## 6. 报告结构建议

建议把报告从“系统产物八章节”改成“商业分析正文 + 审计附录”。仍可保留现有 `ReportData` 外壳，但章节命名和 items 结构要更商业化。

### 6.1 新报告章节

| 顺序 | 章节 | 内容重点 |
|---:|---|---|
| 1 | 执行摘要 | 一句话结论、最大威胁、最大机会、首要动作、证据等级 |
| 2 | 竞争格局 | 价格带/人群/场景下的竞争地图，不罗列全量 SKU |
| 3 | 核心竞品 Battlecard | 每个核心竞品：为什么被比较、强项、弱点、我方回应 |
| 4 | 用户决策链 | 用户从兴趣到下单在哪些环节被竞品影响 |
| 5 | 差距矩阵 | 目标产品相对核心竞品的功能/证据/表达/转化差距 |
| 6 | 机会地图与优先级 | P0/P1/P2 动作，预期影响与证据要求 |
| 7 | 风险与证据边界 | 哪些结论可采纳、哪些只能作为推断、哪些暂无可靠数据 |
| 8 | 附录 | Evidence 索引、QA 打回、Trace 摘要、数据范围 |

### 6.2 正文去重规则

1. 正文不重复展示 SKU 基础字段；只在首次出现竞品时用一句话定位。
2. 价格、销量、评分等事实只在影响判断时出现，其他放入附录。
3. 每个章节 item 必须回答“所以呢”：影响、含义、动作至少有一个。
4. Evidence 只在正文以短引用或风险标记出现，完整详情在证据附录和 Trace。
5. 同一 evidence_id 在同一章节最多展开一次。

## 7. Agent 分工调整建议

不建议新增很多 Agent。MVP 更稳的做法是在现有 Analysis 和 Writer 内增加结构化步骤。

### 7.1 Collection Agent

保持职责边界：只整理数据，不做商业判断。

可增强：

1. 给 ReviewInsight 增加更稳定的 `market_signals` 字段归一化。
2. 标准化价格、销量、评论数、访问时间、截图状态，减少后续重复判断。

### 7.2 Analysis Agent

应成为智能分析主战场。

新增职责：

1. 生成 StrategyBrief。
2. 基于 CompetitionEdge 生成 CompetitorBattlecard。
3. 基于 FeatureTree/PricingModel/UserPersona/ReviewInsight 生成 GapMatrix。
4. 生成 OpportunityMap，并按 impact/effort/evidence_confidence 排序。
5. 对每个结论保留 evidence_ids、claim_ids、is_inference、confidence。

### 7.3 QA Agent

QA 不只检查证据缺失，还应检查分析质量。

新增检查：

1. 正文结论是否没有商业含义。
2. 建议是否没有责任方向或执行对象。
3. Battlecard 是否缺少 target_response。
4. GapMatrix 是否没有 evidence_ids 或没有明确推断标记。
5. 同一事实是否在报告正文重复超过阈值。

### 7.4 Writer Agent

Writer 只做“商业报告表达”和“去重编排”，不要承担核心分析。

新增职责：

1. 从 StrategyBrief 开始组织 executive narrative。
2. 优先消费 Battlecard、GapMatrix、OpportunityMap，而不是直接消费所有 edges。
3. 做章节级去重：同一 evidence/claim/fact 不反复展开。
4. 把审计信息后置到附录。

## 8. 可行性实施计划

下面的 Phase 不是独立拍脑袋拆出来的，而是把前面商业报告和 GitHub 样本里的可复用模式压缩成适合当前 MVP 的落地路径。核心取舍是：先吸收“分析结构和证据治理”，暂缓“复杂实时外采和新框架”。

| 调研中学到的模式 | 对应来源/项目类型 | 当前项目落地阶段 | 为什么这样落地 |
|---|---|---|---|
| Research Brief 先行 | Gartner/Forrester 报告、GPT Researcher、startup/marketing research skills | Phase 0、Phase 1 | 先定义商业问题、目标人群、证据边界，避免报告继续从 SKU 字段开始堆材料 |
| Battlecard | Klue/Crayon、startup-skill、company-index-framework、battlecard generator 类项目 | Phase 1 | 这是把竞品从“资料卡”变成“对抗判断”的最快路径，适合 MVP 优先做 |
| Gap Matrix | G2/Grid、Similarweb/Semrush gap 类产品、comparison grid 项目 | Phase 2、Phase 4 | 用矩阵承载功能、价格、评论、表达、证据差距，比长段落更像商业分析 |
| Review Signal Mining | Amazon-Skills、startup-review-mining、Amazon review sentiment/EDA 仓库 | Phase 2 | 自动猫砂盆最有价值的数据不是评论摘要，而是痛点、购买理由、异议和转化阻碍 |
| Opportunity Scoring | 产品验证、startup idea evaluation、consulting skills | Phase 2 | 把建议从“可以考虑”升级为按影响、置信度、成本排序的动作清单 |
| Report-first Narrative | Gartner/Forrester/G2、consulting/business analysis skills | Phase 3、Phase 4 | 报告第一屏必须给结论、威胁、机会、动作；证据详情后置到附录 |
| Source Registry / Citation | RivalSearchMCP、GPT Researcher、RAG research assistant、Bright Data skills | Phase 1、Phase 3、Phase 5 | 所有新分析产物仍绑定 Evidence/Claim，保持可追溯和可打回 |
| Evidence Conflict Check | RivalSearchMCP、company-index-framework、CI monitoring 类项目 | Phase 5 | 防止多源数据或人工修正后出现冲突，避免“智能分析”变成编造 |
| Change Event / Diff | price monitor、website diff、CI monitor、repo-intel 类项目 | Phase 5，外采增强阶段 | 当前先用于 QA 补证前后差异；真实定时监控放到 MVP 之后 |
| Dashboard / Matrix UX | market intelligence dashboard、comparison grid、BI 类项目 | Phase 4 | 前端不做复杂 BI，但报告页需要矩阵、battlecard、优先级列表这些更适合扫读的形态 |

这也解释了为什么计划没有把“外采平台”放进 Phase 1：GitHub 上很多项目强在抓取和监控，但当前项目的主要短板是分析 Artifact 不够商业化。如果先上大外采，报告仍可能只是把更多外部信息搬进来；先做好 Battlecard、GapMatrix、OpportunityMap，外采进来后才有地方承接。

### Phase 0：文档与验收口径冻结

目标：先把“什么叫更像分析报告”固化为验收标准。

工作项：

1. 在 `memory-bank/design-document.md` 后续更新报告章节定义。
2. 在测试 fixture 中准备一个期望报告骨架，不改真实演示数据。
3. 明确报告正文去重规则和智能分析验收清单。

建议测试：

1. 报告章节顺序测试。
2. 正文不可出现过多内部字段 ID。
3. 正文建议必须包含 action / owner / evidence boundary。

风险：低。只改文档和测试预期时风险最小。

### Phase 1：新增 StrategyBrief 与 Battlecard

目标：让 Analysis Agent 先输出商业判断骨架。

工作项：

1. 新增 Pydantic Schema：`StrategyBrief`、`CompetitorBattlecard`。
2. Analysis Agent 在生成 CompetitionEdge 后生成 battlecard。
3. ArtifactRepository 保存新 artifact 类型。
4. Trace 展示新增 artifact 计数。

建议测试：

1. 每个核心 battlecard 必须绑定 competitor_id 和至少一个 claim/evidence。
2. `target_response` 不能为空。
3. 缺证据时 battlecard 必须带风险标记或“暂无可靠数据”。

风险：中低。新增 artifact，不破坏现有报告。

### Phase 2：新增 GapMatrix 与 OpportunityMap

目标：把智能分析从“谁像谁”推进到“差什么、做什么”。

工作项：

1. 新增 `GapMatrixItem`、`OpportunityItem` Schema。
2. 基于现有 feature/pricing/persona/review/edge 规则生成初版 gap。
3. 优先用规则，不强依赖 LLM。
4. Opportunity 排序公式建议：

```text
priority_score =
0.35 * decision_stage_impact
+ 0.25 * threat_level
+ 0.20 * evidence_confidence
+ 0.10 * expected_impact
- 0.10 * effort_level
```

建议测试：

1. 至少生成功能、证据、表达、转化四类中的两类 gap。
2. 每个 opportunity 必须关联 gap 或 battlecard。
3. P0 动作不能来自完全无证据结论。

风险：中。需要避免规则过硬导致假分析。

### Phase 3：重构 Report Planner

目标：报告先读分析 Artifact，而不是直接读所有原始结构。

工作项：

1. Writer `_build_report_data` 优先读取 StrategyBrief、Battlecard、GapMatrix、OpportunityMap。
2. 保留现有 8 章节数量，但替换章节语义和 items 结构。
3. 正文只展开 top 3-5 个最重要判断。
4. Evidence/QA/Trace 进入附录。

建议测试：

1. 报告正文必须包含“最大威胁、最大机会、首要动作”。
2. 核心竞品章节必须出现 battlecard 字段。
3. 差距矩阵章节必须出现 gap dimension 和 recommendation。
4. 同一 `content_summary` 不应在多个正文章节重复展开。

风险：中高。会影响前端展示和 Word 导出，应小步兼容。

### Phase 4：前端报告阅读体验调整

目标：让网页报告像商业报告，而不是 Artifact 浏览器。

工作项：

1. 报告页第一屏改为 executive brief：结论、威胁、机会、动作、证据等级。
2. Battlecard 使用紧凑对比卡：竞品强项、我方回应、风险。
3. GapMatrix 使用表格或矩阵，不用长段落堆叠。
4. OpportunityMap 使用优先级列表，支持跳转 evidence/trace。

建议测试：

1. 前端组件能渲染新旧两种 report item，保证历史兼容。
2. 移动端和桌面端不重叠。
3. Word 导出包含新章节标题和矩阵摘要。

风险：中。前端当前 ReportPage 对通用 item 已有大量格式化逻辑，需要谨慎替换。

### Phase 5：QA 增加报告质量规则

目标：防止报告再次退化成信息搬运。

工作项：

1. 新增 ReportQualityRules 服务。
2. 检查重复事实、无动作建议、无商业含义、证据越界、内部 ID 泄漏。
3. Writer 质检 LLM 继续保留，但规则检查先行。
4. Trace 中展示报告质量检查结果。

建议测试：

1. 构造重复段落，QA 必须标记。
2. 构造没有 action 的建议，QA 必须标记。
3. 构造证据不足却绝对化表达，QA 必须标记。

风险：中低。主要是新增检查，不改变核心 DAG。

## 9. MVP 优先级建议

如果时间有限，建议只做前三个最能体现“智能分析”的改造：

1. `CompetitorBattlecard`：最容易让报告从 SKU 汇总变成竞争对抗分析。
2. `GapMatrix`：最容易展示“分析而不是整理”。
3. `OpportunityMap`：最容易让报告有商业交付价值。

暂缓：

1. 真实外部采集。
2. 复杂市场份额/流量/关键词分析。
3. 多行业配置化。
4. 新增独立 Strategy Agent。
5. 大规模数据库表拆分。

## 10. 验收清单

升级后报告应满足：

1. 第一屏能回答：谁最威胁目标产品、为什么、先做什么。
2. 每个核心竞品都有 Battlecard，而不是 SKU 字段列表。
3. 至少有一张 GapMatrix，展示目标产品相对竞品的差距。
4. 至少有 3 条 Opportunity，带优先级、预期影响、证据边界。
5. 正文中相同价格/卖点/证据摘要不反复出现。
6. 所有事实判断仍能跳转 Evidence 或 Trace。
7. 推断内容显式标记，证据不足写“暂无可靠数据”或“建议复核”。
8. QA 打回仍真实发生，且打回前后差异能在 Trace 展示。
9. Word 导出和网页报告结构一致。
10. 未配置模型 API Key 时，规则流程仍可生成完整报告。

## 11. 参考资料

1. Gartner Magic Quadrant methodology: https://www.gartner.com/en/research/methodologies/magic-quadrants-research
2. Gartner Magic Quadrant FAQ: https://www.gartner.com/en/about/magic-quadrant-faq
3. Forrester Wave methodology: https://www.forrester.com
4. G2 Research Scoring Methodologies: https://documentation.g2.com/docs/research-scoring-methodologies
5. Similarweb competitive analysis product materials: https://www.similarweb.com
6. Klue competitive intelligence and battlecards: https://www.klue.com
7. Crayon competitive intelligence and battlecards: https://www.crayon.co
8. Bright Data competitive intelligence examples on GitHub: https://github.com/brightdata/skills
9. Openclaw competitive intelligence market research skill: https://github.com/openclaw/skills/blob/main/skills/shashwatgtm/competitive-intelligence-market-research/SKILL.md
10. GitHub topic `competitor-analysis`: https://github.com/topics/competitor-analysis
11. GitHub topic `competitive-intelligence`: https://github.com/topics/competitive-intelligence
12. GitHub topic `market-research`: https://github.com/topics/market-research
13. Bright Data multi-agent competitive intelligence platform: https://github.com/brightdata/competitive-intelligence
14. RivalSearchMCP: https://github.com/damionrashford/RivalSearchMCP
15. Startup Skill: https://github.com/ferdinandobons/startup-skill
16. Amazon Skills by Nexscope: https://github.com/nexscope-ai/Amazon-Skills
17. Competitive analysis demo by Parallel Web: https://github.com/parallel-web/competitive-analysis-demo
18. GPT Researcher: https://github.com/assafelovic/gpt-researcher
19. DeerFlow: https://github.com/bytedance/deer-flow

## 12. 结论

当前系统的问题不是“没有 Agent”，而是 Agent 的核心分析产物还不够商业化。下一步不应继续只优化 Writer 文案，而应让 Analysis Agent 产出 StrategyBrief、Battlecard、GapMatrix 和 OpportunityMap。Writer 再基于这些产物组织报告，才能明显减少重复搬运，并让最终交付看起来像真正的竞品分析报告。
