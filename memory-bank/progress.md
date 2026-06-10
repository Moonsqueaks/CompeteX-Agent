# 项目进度记录

## 当前总览

截至 2026-05-29，实施计划已按顺序完成步骤 01 到步骤 40；按用户要求，本轮只完成步骤 39 和步骤 40，执行完即结束。步骤 28 已完成前端输入页任务创建，步骤 29 已完成 Trace 页任务状态轮询和刷新后状态恢复，步骤 30 已完成前端产品画像页，步骤 31 已完成前端竞争图谱页，步骤 32 已完成前端报告页，步骤 33 已完成前端过程追踪页真实 Trace 数据渲染，步骤 34 已完成前后端端到端任务流，步骤 35 已完成真实 QA 打回演示链路验证，步骤 36 已完成 Human Review 闭环验证，步骤 37 已完成异常与降级处理补齐，步骤 38 已完成安全与脱敏专项，步骤 39 已完成 E2E Demo 路径验证，步骤 40 已完成 Demo 冻结与稳定回归。

当前边界：

1. 已完成项目骨架、质量工具、统一 API 响应、核心 Schema、SQLite 存储层、最终 Demo 快照规范、Snapshot Loader、任务创建 API、任务状态查询 API、LangGraph 状态对象、Collection Agent 节点、CompetitionEdgeScore 评分服务、Analysis Agent 节点、QA 规则服务、QA Agent 节点、QA 打回后的 Collection 修复逻辑、QA 打回后的 Analysis 局部重算逻辑和 LangGraph 主流程组装。
2. `data/raw/` 中的真实脱敏 SKU 原始素材已作为步骤 06 的素材来源保留。
3. `data/snapshots/demo_sku_snapshot.json` 是 Snapshot Loader 的正式快照输入契约。
4. `POST /tasks` 已可创建任务并写入 SQLite；运行时应用会自动后台启动 LangGraph 任务执行，测试可通过同步执行入口稳定验证。`GET /tasks/{task_id}` 已可查询任务基础状态，`TaskGraphState` 已可从任务初始化并追加核心 Artifact，`collection_agent_node` 已可读取本地快照并写入 Product、Evidence、ReviewInsight 和 Trace 日志，也可在 QA 打回后再次运行并补齐或标记 Collection 证据，评分服务已可输出五维解释分和切片排序，`analysis_agent_node` 已可生成目标画像、Claim 和 CompetitionEdge，也可在 QA 打回 Analysis 后只重算受影响 Claim/CompetitionEdge 并保留无关边，`run_qa_rules` 已可输出结构化 ReviewTask，`qa_agent_node` 已可输出通过状态或结构化 `revision_request`，`build_analysis_workflow` 已可通过真实 LangGraph 条件边串联 Collection、Analysis、QA 和真正的 Writer Agent。
5. `writer_agent_node` 已可生成网页报告数据结构并写入 `state["reports"]`，报告包含执行摘要、产品画像、竞品发现、动态切片、决策链、用户研究、建议、QA 摘要和 Evidence 索引。
6. `markdown_renderer` 已可基于 `ReportData` 生成 Markdown 报告、保存到 `data/reports/` 或测试指定目录，并把导出元信息写入 `state["markdown_reports"]` 与 `metadata.markdown_report`。
7. `GET /tasks/{task_id}/report` 与 `GET /tasks/{task_id}/report/markdown` 已实现；完成任务可获取网页报告数据和导出 Markdown，未完成任务会返回标准错误。
8. `GET /tasks/{task_id}/profile` 已实现；完成任务可获取目标产品基础信息、FeatureTree、PricingModel、UserPersona、价格证据状态和短 Evidence 摘要。
9. `GET /tasks/{task_id}/battlefield` 已实现；完成任务可获取切片列表、竞争关系图节点与边、评分解释、决策链、Evidence 卡片和 QA 摘要，并支持 `price_band`、`persona`、`scenario` 过滤。
10. `GET /tasks/{task_id}/trace` 已实现；可返回 DAG 节点/边、Agent Run、Tool Call、Token Usage、QA Review、Revision Message、Diff View 和折叠脱敏 Prompt 预览。
11. `POST /tasks/{task_id}/feedback` 已实现；只允许有限结构化 HumanFeedback，保存 before/after/reason，将允许的人工修正应用到 profile、battlefield、trace 缓存 Artifact，并把任务标记为 `human_reviewing` 以保留人工复核状态。
12. 前端已完成工作台路由布局、统一 API Client/请求状态基础设施、从后端 FastAPI OpenAPI 生成的 `frontend/src/api/schema.ts`、类型契约检查、组件错误态展示、输入页任务创建、创建成功跳转 `/trace?task_id=<task_id>`、Trace 页基于 `GET /tasks/{task_id}` 的任务状态轮询和终止条件、Trace 页基于 `GET /tasks/{task_id}/trace` 的 LangGraph DAG、Agent Run、Tool Call、Token Usage、QA Review、打回消息、Diff View 与折叠脱敏 Prompt 预览渲染、完成态结果入口、跨页面导航保留 `task_id`、产品画像页基于 `GET /tasks/{task_id}/profile` 的五个画像模块渲染与有限 Human Review 入口、竞争图谱页基于 `GET /tasks/{task_id}/battlefield` 的 React Flow 竞争关系图、切片拨盘、评分解释、证据卡片和 QA 摘要展示，以及报告页基于 `GET /tasks/{task_id}/report` 的九章节网页报告展示和 Markdown 导出入口。
13. 第 27 步新增 `npm --prefix frontend run sync:types`，通过 `scripts/sync-openapi-types.mjs` 从后端 `create_app().openapi()` 生成 TypeScript 类型；后端接口契约变化后必须重新运行该脚本并提交生成结果。
14. 步骤 34 已补齐完整前后端端到端任务流：输入页创建任务、后端后台执行 LangGraph、前端轮询完成态、Trace 完成态刷新、再进入产品画像、竞争图谱和报告页。步骤 35 已验证真实 QA 打回演示链路：缺失证据触发 Collection 打回、补齐证据、Analysis 重算、Writer 生成更新报告、Trace 和 E2E 均可见前后差异。步骤 36 已验证 Human Review 闭环：允许范围内的人工修正会保存 HumanFeedback、刷新相关缓存结果，并在前端提交后重新拉取产品画像。步骤 37 已补齐快照缺失、模型结构化输出异常、单 Agent 失败、Markdown 导出失败和失败 Trace。步骤 38 已补齐安全与脱敏专项。步骤 39 已用 Playwright 覆盖完整 Demo 路径、Markdown 导出、QA 修复记录、图谱截图和窄屏布局。步骤 40 已冻结 Demo 快照哈希、稳定任务输入、默认目标和 QA 打回案例，并用回归测试锁定稳定结果形状。
15. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
16. 未写入真实 API Key，未在 Trace、日志或文档中记录密钥。

## 2026-05-23：步骤 01 项目骨架完成

### 当前完成情况

实施计划中的步骤 01 已完成。该步骤早于当前进度文档的细粒度记录建立，未保留单独的原始验证条目；后续步骤 02 的质量检查已持续验证基础工程可运行。

已完成内容：

1. 建立 `backend/` 后端目录，包含 FastAPI 应用入口、基础包目录和测试目录。
2. 建立 `frontend/` 前端目录，使用 Vite + React + TypeScript 基础项目。
3. 建立 `data/`、`docs/`、`demo/` 和 `memory-bank/` 目录。
4. 保留 `memory-bank/` 作为项目记忆文档目录。
5. 未在步骤 01 中实现业务逻辑。

### 后续验证覆盖

步骤 02 之后的后端测试、前端测试和前端构建均基于该项目骨架运行，说明骨架满足后续开发要求。

## 2026-05-23：步骤 02 代码质量工具配置完成

### 当前完成情况

实施计划中的步骤 02 已完成。

已完成配置：

1. 后端新增 `backend/pyproject.toml`，配置 Pytest 路径、Ruff lint 规则和 Ruff format 基础规则。
2. 后端新增 `backend/.env.test` 和 `backend/tests/conftest.py`，测试环境从本地测试环境变量文件加载，且 `DOUBAO_API_KEY` 默认为空，不依赖真实密钥。
3. 后端 `backend/requirements-dev.txt` 补充 `python-dotenv` 和 `ruff`。
4. 前端新增 `frontend/eslint.config.js`，配置 ESLint、TypeScript ESLint、React Hooks 和 React Refresh 检查。
5. 前端新增 `frontend/.prettierrc.json` 和 `frontend/.prettierignore`。
6. 前端 `frontend/package.json` 补充 `lint`、`format`、`format:check` 脚本，并补齐 ESLint、Prettier 相关开发依赖。
7. 项目根目录新增 `.gitignore`，忽略本地环境、依赖、缓存、构建产物和导出报告目录。

### 验证结果

后端使用项目内 Conda 环境 `backend/.conda312`，Python 版本为 3.12.13。

验证命令与结果：

1. `backend\.conda312\python.exe -m ruff check backend`：通过。
2. `backend\.conda312\python.exe -m pytest backend`：通过，1 个测试通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run test`：通过，1 个测试文件、1 个测试通过。
5. `npm --prefix frontend run build`：通过。
6. `npm --prefix frontend run format:check`：通过。

### 环境说明

1. 本机全局 Python 为 3.11.2，但已按技术栈约定创建项目内 Python 3.12 Conda 环境。
2. 前端当前使用本机 Node.js v20.20.2 和 npm 9.4.2；`tech-stack.md` 推荐 Node.js 24 LTS，后续如比赛环境需要可再升级。
3. 后端本地曾创建过 `backend/.venv` 和失败的 `backend/.conda` / `backend/.conda-pkgs` 缓存，均已加入 `.gitignore`。

## 2026-05-23：步骤 03 统一响应与错误格式完成

### 当前完成情况

实施计划中的步骤 03 已完成。

已完成实现：

1. 新增 `backend/app/schemas/api_response.py`，定义统一 `ApiResponse` 和 `ApiError`。
2. 新增 `backend/app/api/responses.py`，提供成功响应、错误响应、`ApiException`、Trace ID 中间件和全局异常处理器。
3. `/health` 已从裸字典响应改为统一结构，成功响应包含 `data`、`error`、`trace_id`。
4. 404、校验错误、业务异常和未捕获异常均会返回统一错误结构。
5. 响应头与响应体都会携带一致的 `X-Trace-Id` / `trace_id`。
6. 错误详情和错误消息加入基础脱敏，避免输出 API Key、Token、Secret、Password 或对应环境变量原文。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m ruff check backend`：通过。
2. `backend\.conda312\python.exe -m pytest backend`：通过，4 个测试通过。

新增测试覆盖：

1. 成功响应包含 `data`、`trace_id`，且 `error` 为 `null`。
2. 客户端传入合法 `X-Trace-Id` 时，响应体和响应头会保持一致。
3. 404 失败响应包含标准错误码、错误消息和详情。
4. 错误 payload 不返回 API Key、模型密钥或敏感环境变量原文。

## 2026-05-23：步骤 04 核心 Pydantic Schema 完成

### 当前完成情况

实施计划中的步骤 04 已完成。

已完成实现：

1. 新增 `backend/app/schemas/common.py`，集中维护任务状态、Agent 名称、数据来源、证据来源、风险标记、Claim 状态、竞争关系类型、决策阶段、审查状态、反馈动作和运行日志状态等枚举。
2. 新增 `backend/app/schemas/task.py`，定义 `AnalysisTask`。
3. 新增 `backend/app/schemas/agent_message.py`，定义结构化 `AgentMessage`。
4. 新增 `backend/app/schemas/product.py`，定义 `Product`、`FeatureTree`、`PricingModel`、`UserPersona`。
5. 新增 `backend/app/schemas/evidence.py`，定义 `Evidence`。
6. 新增 `backend/app/schemas/claim.py`，定义 `Claim`，并在缺少 `evidence_ids` 时自动加入 `missing_evidence` 风险标记、转为 `needs_review` 状态。
7. 新增 `backend/app/schemas/competition.py`，定义 `CompetitionSlice`、`ScoreBreakdown`、`CompetitionEdge`，并约束评分范围为 `0` 到 `1`。
8. 新增 `backend/app/schemas/review.py`，定义 `ReviewTask` 与 `HumanFeedback`。
9. 新增 `backend/app/schemas/trace.py`，定义 `AgentRunLog`、`ToolCallLog`、`TokenUsageLog`，其中 `total_tokens` 必须等于提示与生成 token 之和。
10. 更新 `backend/app/schemas/__init__.py`，统一导出步骤 04 的核心 Schema 和枚举。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_core_schemas.py`：通过，37 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，41 个测试通过。

新增测试覆盖：

1. 每个核心 Schema 的合法样例可以校验通过。
2. 每个核心 Schema 的必填字段缺失会校验失败。
3. 所有核心 Schema 字段名保持 `snake_case`。
4. `Claim` 缺少证据 ID 时会进入风险状态，而不是产生无证据强结论。
5. `CompetitionEdge` 总分和评分拆解维度会拒绝越界分数。
6. `TokenUsageLog` 会拒绝不一致的 token 总数。
7. 核心 Schema 可以进入 FastAPI OpenAPI 文档生成。

## 2026-05-23：步骤 05 SQLite 存储层完成

### 当前完成情况

实施计划中的步骤 05 已完成。

已完成实现：

1. 后端新增 `SQLAlchemy` 开发依赖，并已安装到项目内 `backend/.conda312` 环境用于测试。
2. 新增 `backend/app/storage/db.py`，提供 SQLite 数据库连接、默认数据库路径、Engine、Session Factory、初始化和清理入口。
3. 新增 `backend/app/storage/models.py`，建立 `analysis_tasks`、`artifact_json`、`trace_logs`、`human_feedback` 四类表。
4. 新增 `backend/app/storage/repositories.py`，建立 `TaskRepository`、`ArtifactRepository`、`TraceLogRepository`、`HumanFeedbackRepository`。
5. 更新 `backend/app/storage/__init__.py`，统一导出存储层入口。
6. 新增 `backend/tests/test_storage_repositories.py`，使用临时 SQLite 数据库验证存储层行为。
7. 更新 `.gitignore`，忽略本地 SQLite 数据库文件，避免运行产物污染仓库。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_storage_repositories.py`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，47 个测试通过。

新增测试覆盖：

1. 使用临时 SQLite 数据库初始化存储表，不污染默认真实数据目录。
2. 任务可以创建、读取和更新状态。
3. Evidence、Claim、CompetitionEdge 可以作为 Artifact JSON 保存和查询。
4. Trace 日志可以按任务 ID 查询，并覆盖 Agent Run、Tool Call、Token Usage。
5. HumanFeedback 可以保存、读取和按任务 ID 列表查询。

## 2026-05-23：步骤 06 本地 Demo 快照数据规范完成

### 素材来源

第 6 步使用用户提供的真实脱敏原始素材作为基础：

1. `data/raw/`：包含 14 个 SKU 目录。
2. `data/raw/sku_01` 到 `data/raw/sku_14`：每个目录包含 `url.txt` 和多张商品、价格、详情、评论截图。
3. `data/raw/_contact_sheets/`：由原始截图生成的缩略总览图，仅用于人工快速检查素材覆盖情况，后端流程不应依赖它。
4. `data/snapshots/link_metadata.json`：从 14 个抖音短链解析出的商品标题、商品 ID、价格区间、销量字段和主图 URL。
5. `data/snapshots/sku_catalog_draft.json`：SKU 草稿目录，保留为素材来源，不再作为最终 Snapshot Loader 输入。
6. `data/snapshots/data_quality_report.md`：数据质量报告与后续缺口说明。

### 当前完成情况

实施计划中的步骤 06 已完成。

已完成实现：

1. 新增 `data/snapshots/README.md`，说明最终 Demo 快照契约、字段结构、QA 打回样例和步骤边界。
2. 新增 `data/snapshots/demo_sku_snapshot.json`，作为最终 Demo 快照输入文件。
3. 最终快照包含 14 个 SKU，超过 MVP 至少 8 个 SKU 的要求。
4. 每个 SKU 均包含名称、品牌、价格、卖点、评论摘要和来源说明。
5. 固定 `sku_02` 为默认演示目标。
6. 固定 `sku_01` 为 QA 打回样例，并故意缺少 `source.access_time`。
7. 在 `qa_revision_fixture.repair_evidence` 中保留 `sku_01` 后续可补齐的访问时间和截图路径。
8. 新增 `backend/tests/test_demo_snapshot_contract.py`，验证最终快照格式和安全约束。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_demo_snapshot_contract.py`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，53 个测试通过。

新增测试覆盖：

1. 最终 Demo 快照文件存在，且至少包含 8 个 SKU。
2. 每个 SKU 均满足最终快照字段契约。
3. 每个 SKU 均可转换为 `Product` 和 `Evidence` Schema。
4. QA 打回 SKU 确实缺少配置的证据字段，并保留后续补齐来源。
5. 快照引用的原始素材目录和可用截图存在。
6. 快照不包含手机号、真实账号 ID、API Key 或敏感隐私字段。

## 2026-05-24：步骤 07 快照加载服务完成

### 当前完成情况

实施计划中的步骤 07 已完成。该步骤完成后曾按用户要求停在步骤 08 前；当前已继续完成步骤 08，见下节记录。

已完成实现：

1. 新增 `backend/app/schemas/review_insight.py`，定义 `ReviewInsight`，承接本地快照中的评论摘要、市场信号、证据引用和局限性说明。
2. 更新 `backend/app/schemas/__init__.py`，统一导出 `ReviewInsight`。
3. 新增 `backend/app/services/snapshot_loader.py`，实现 `load_demo_snapshot`、`SnapshotLoadResult` 和 `SnapshotLoaderError`。
4. 更新 `backend/app/services/__init__.py`，统一导出快照加载服务。
5. Loader 默认读取 `data/snapshots/demo_sku_snapshot.json`，未使用 `sku_catalog_draft.json` 作为正式输入。
6. Loader 将 14 个 Demo SKU 转换为标准 `Product`、`Evidence` 和 `ReviewInsight`。
7. Loader 保留 `sku_01` 缺失的 `source.access_time`，不会使用 `qa_revision_fixture.repair_evidence` 自动补齐。
8. Loader 对非法 JSON、缺少必需字段、默认目标 SKU 不存在等非法快照返回带 `code`、`message`、`details` 的可诊断错误。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_snapshot_loader.py`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，59 个测试通过。

新增测试覆盖：

1. Snapshot Loader 可以读取全部 14 个 Demo SKU。
2. 默认目标 `sku_02` 会被识别为 `target` 产品。
3. QA 打回样例 `sku_01` 的缺失访问时间会保留为 `Evidence.access_time = None`，并在 `metadata.missing_fields` 中记录。
4. 加载结果可以通过 `Product`、`Evidence` 和 `ReviewInsight` Pydantic Schema 校验。
5. 非法 JSON 会返回 `SNAPSHOT_INVALID_JSON` 诊断错误。
6. 缺少必需字段的非法快照会返回 `SNAPSHOT_CONTRACT_INVALID` 诊断错误。

## 2026-05-24：步骤 08 任务创建 API 完成

### 当前完成情况

实施计划中的步骤 08 已完成。该步骤完成后曾按用户要求停在步骤 09 前；当前已继续完成步骤 09，见下节记录。

已完成实现：

1. 更新 `backend/app/schemas/task.py`，新增 `TaskCreateRequest` 和 `TaskCreateResponse`。
2. 更新 `backend/app/schemas/__init__.py`，统一导出任务创建请求和响应 Schema。
3. 新增 `backend/app/services/task_creation.py`，封装任务创建逻辑、默认 Demo 目标选择和任务元数据生成。
4. 新增 `backend/app/api/routes_tasks.py`，实现 `POST /tasks`，通过 `TaskRepository` 写入 SQLite。
5. 更新 `backend/app/main.py`，注册任务路由，并允许测试创建应用时传入临时数据库 URL。
6. 更新 `backend/app/api/responses.py`，将校验错误状态码保持为 `422`，并移除 Starlette 对旧常量的弃用 warning。
7. 新增 `backend/tests/test_tasks_api.py`，验证任务创建 API 行为。

### 当前 API 行为

1. 合法请求可以创建任务，响应 HTTP 状态码为 `201`。
2. 响应继续使用统一结构：`data`、`error`、`trace_id`。
3. `data` 中包含 `task_id`、`status` 和完整 `task`。
4. 默认数据模式为 `demo_snapshot`。
5. 请求省略 `target_product_name` 或传入 `null` 时，使用最终 Demo 快照默认目标 `sku_02`。
6. 请求显式传入空白 `target_product_name` 时，返回统一校验错误。
7. 步骤 08 本身只创建任务并落库，不启动完整 Agent 流程。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_tasks_api.py`：通过，5 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，64 个测试通过。

新增测试覆盖：

1. 合法请求可以创建任务并持久化到临时 SQLite。
2. 显式空白目标产品名称会返回统一校验错误。
3. 未指定数据模式时默认使用 `demo_snapshot`。
4. 未指定目标产品时会选择默认 Demo 目标 `sku_02`。
5. 创建任务响应符合统一 API 响应格式。

## 2026-05-24：步骤 09 任务状态查询 API 完成

### 当前完成情况

实施计划中的步骤 09 已完成。该步骤完成后曾按用户要求停在步骤 10 前；当前已继续完成步骤 10，见下节记录。

已完成实现：

1. 更新 `backend/app/schemas/task.py`，新增 `TaskStatusResponse`，用于任务状态轮询接口。
2. 更新 `backend/app/schemas/__init__.py`，统一导出 `TaskStatusResponse`。
3. 更新 `backend/app/api/routes_tasks.py`，新增 `GET /tasks/{task_id}`，通过 `TaskRepository` 查询任务。
4. 扩展 `backend/tests/test_tasks_api.py`，验证任务状态查询 API 行为。

### 当前 API 行为

1. 已存在任务可以通过 `GET /tasks/{task_id}` 查询。
2. 响应继续使用统一结构：`data`、`error`、`trace_id`。
3. `data` 只包含任务基础状态信息：任务 ID、目标产品名称、目标链接、品类、子类、数据模式、状态、创建时间和更新时间。
4. 不返回完整报告、Trace、Artifact、`research_text` 或内部 `metadata`。
5. 不存在任务返回 `TASK_NOT_FOUND` 标准错误，HTTP 状态码为 `404`。
6. 步骤 09 本身只查询任务状态，不启动完整 Agent 流程。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_tasks_api.py`：通过，9 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，68 个测试通过。

新增测试覆盖：

1. 已存在任务可以查询并返回基础状态字段。
2. 不存在任务返回标准错误结构。
3. 任务状态字段只使用允许的 `TaskStatus` 枚举值。
4. 状态查询响应不返回 `research_text`、内部 `metadata`、Trace、Artifact 或敏感配置文本。

## 2026-05-24：步骤 10 LangGraph 状态对象完成

### 当前完成情况

实施计划中的步骤 10 已完成。该步骤完成后曾按用户要求停在步骤 11 前；当前已继续完成步骤 11，见下节记录。

已完成实现：

1. 新增 `backend/app/graph/state.py`，定义轻量 `TaskGraphState`。
2. 更新 `backend/app/graph/__init__.py`，统一导出 Graph 状态对象和辅助函数。
3. `TaskGraphState` 覆盖任务、产品、证据、评论洞察、结论、竞争边、QA 记录、人工反馈、Agent 消息、Agent Run、Tool Call、Token Usage 和元数据。
4. 新增 `create_initial_state`，可从 `AnalysisTask` 或任务字典生成初始状态。
5. 新增 `append_product`、`append_evidence`、`append_claim`、`append_review_task`、`append_agent_message`、`append_run_log` 等追加函数。
6. 新增 `serialize_state_for_trace`，用于输出可 JSON 序列化的 Trace 展示 payload。
7. 新增 `backend/tests/test_graph_state.py`，验证状态对象行为。

### 当前状态行为

1. 初始状态必须包含非空 `task_id`，缺少任务 ID 会失败。
2. 状态层保持轻量，只保存 JSON 化 payload；复杂业务校验继续交给 Pydantic Artifact。
3. Pydantic Artifact 会通过 `model_dump(mode="json")` 转成可序列化字典。
4. 状态追加函数只写入内存状态，不读写 SQLite、不启动后台任务、不执行任何 Agent。
5. `serialize_state_for_trace` 会输出各类 Artifact 列表和计数，供后续 Trace API 复用。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_graph_state.py`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，74 个测试通过。

新增测试覆盖：

1. 初始状态可以从任务生成。
2. 状态可以追加 Product、Evidence、Claim、ReviewTask。
3. 状态序列化后可以作为 Trace 展示 payload。
4. 缺少任务 ID 时状态初始化失败。

## 2026-05-24：步骤 11 Collection Agent 节点完成

### 当前完成情况

实施计划中的步骤 11 已完成。该步骤完成后曾按用户要求停在步骤 12 前；当前已继续完成步骤 12，见下节记录。

已完成实现：

1. 新增 `backend/app/agents/collection.py`，实现 `collection_agent_node`。
2. 更新 `backend/app/agents/__init__.py`，统一导出 Collection Agent 节点。
3. Collection Agent 复用 Snapshot Loader 读取最终 Demo 快照。
4. Collection Agent 会向 `TaskGraphState` 追加 `Product`、`Evidence` 和 `ReviewInsight`。
5. 当任务包含 `research_text` 时，额外追加一条 `user_research` Evidence，只记录来源和字符数，不在 Trace 摘要中展开原文。
6. Collection Agent 会记录 `AgentRunLog` 和 `ToolCallLog`，并在状态 metadata 中写入产物数量、缺失证据字段和用户研究读取状态。
7. Collection Agent 失败时会记录失败日志，并继续抛出 Snapshot Loader 的可诊断错误。

### 当前 Agent 行为

1. 输入任务状态后可以生成 14 个 Product、14 个快照 Evidence 和 14 个 ReviewInsight。
2. 每个 Product 至少关联一个 Evidence。
3. `sku_01` 缺失的访问时间继续保留为 `None`，不会自动使用 `qa_revision_fixture` 修复。
4. 缺失字段会汇总到 `state["metadata"]["collection_agent"]["missing_evidence_fields"]`，供后续 QA 和 Trace 使用。
5. 当前只做采集，不生成 Claim、CompetitionEdge、评分、报告或完整 DAG 执行。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_collection_agent.py`：通过，5 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，79 个测试通过。

新增测试覆盖：

1. 输入任务后可以生成至少 8 个 Product，当前为 14 个。
2. 每个 Product 至少有一个 Evidence 关联。
3. 缺失访问时间的证据不会被自动补齐。
4. Collection Agent 运行日志和工具调用日志会被写入 Trace 状态。
5. 用户研究文本会被读取为 `user_research` Evidence。

## 2026-05-24：步骤 12 CompetitionEdgeScore 评分服务完成

### 当前完成情况

实施计划中的步骤 12 已完成。该步骤完成后曾按用户要求停在步骤 13 前；当前已继续完成步骤 13，见下节记录。

已完成实现：

1. 新增 `backend/app/services/scoring.py`，实现 CompetitionEdgeScore 五维规则评分服务。
2. 更新 `backend/app/services/__init__.py`，导出评分服务入口、权重和结果对象。
3. 新增 `calculate_competition_edge_score`，输入目标产品、竞品产品、当前切片、Evidence 和 ReviewInsight，输出总分、`ScoreBreakdown` 和每维解释。
4. 新增 `rank_competitors_by_score`，用于按当前切片对候选竞品进行纯评分排序。
5. 新增轻量结果对象 `DimensionScore`、`CompetitionScoreResult` 和 `ScoredCompetitor`。
6. 新增 `backend/tests/test_scoring.py`，验证评分服务行为。

### 当前评分行为

1. 总分严格按权重计算：需求替代性 0.30、上下文匹配度 0.25、决策阶段影响力 0.20、证据置信度 0.15、市场信号强度 0.10。
2. 五个维度分数均限制在 `0` 到 `1`，并输出 `reasons` 与 `signals`。
3. 证据置信度会因低 confidence、缺少截图或缺少访问时间而下降。
4. 市场信号读取 Evidence metadata 或 ReviewInsight market_signals 中的 sales 字段。
5. 不同价格带、人群、场景切片可以改变候选竞品排序。
6. 当前只做评分服务，不生成完整 Claim 集合、不创建 CompetitionEdge、不组装完整 DAG；Analysis Agent 已在后续步骤 13 基于该服务实现。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_scoring.py`：通过，4 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，83 个测试通过。

新增测试覆盖：

1. 总分由五个维度按文档权重计算。
2. 每个维度分数必须在合法范围内，并包含解释。
3. 低证据置信度会降低总分。
4. 不同切片会产生不同竞品排序。

## 2026-05-24：步骤 13 Analysis Agent 节点完成

### 当前完成情况

实施计划中的步骤 13 已完成。该步骤完成后曾按用户要求停在步骤 14 前；当前已继续完成步骤 14，见下节记录。

已完成实现：

1. 新增 `backend/app/agents/analysis.py`，实现 `analysis_agent_node`。
2. 更新 `backend/app/agents/__init__.py`，统一导出 Collection 与 Analysis 两个 Agent 节点。
3. 更新 `backend/app/graph/state.py`，新增 `feature_trees`、`pricing_models`、`user_personas` 状态字段。
4. 更新 `backend/app/graph/__init__.py`，导出 `append_feature_tree`、`append_pricing_model` 和 `append_user_persona`。
5. Analysis Agent 会基于 Collection 输出生成目标 `FeatureTree`、`PricingModel` 和 `UserPersona`。
6. Analysis Agent 会召回直接竞品、需求替代品和内容共现候选，并调用第 12 步评分服务生成 `CompetitionEdge`。
7. 每条竞争边会生成一条 `Claim`，绑定目标和竞品 Evidence；缺少竞品证据时标记 `missing_evidence` 并进入 `needs_review`。
8. Analysis Agent 会记录 `AgentRunLog`，并在 metadata 中保存每条边的评分解释。
9. 新增 `backend/tests/test_analysis_agent.py`，验证步骤 13 行为。

### 当前 Analysis 行为

1. Demo 快照经过 Collection 后，Analysis 会为默认目标 `sku_02` 生成 1 个 `FeatureTree`、1 个 `PricingModel`、1 个 `UserPersona`、13 条 `CompetitionEdge` 和 13 条 Claim。
2. `CompetitionEdge` 包含切片、人群、场景、决策阶段、总分和五维评分拆解。
3. 评分解释保存在 `state["metadata"]["analysis_agent"]["edge_explanations"]`。
4. 当前步骤不创建 `ReviewTask`，不执行 QA 打回，不修复证据，不生成报告，不组装完整 DAG。
5. 缺少可靠证据时使用“暂无可靠数据”或风险标记，不补写无来源的价格、认证、销量或排名。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_analysis_agent.py backend\tests\test_graph_state.py`：通过，11 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，88 个测试通过。

新增测试覆盖：

1. Analysis Agent 能生成目标画像三类产物。
2. Analysis Agent 能召回直接竞品、替代品和渠道型替代品。
3. 每条竞争边包含切片、决策阶段、评分拆解和评分解释。
4. 竞品缺失 Evidence 时，Claim 与 CompetitionEdge 会标记 `missing_evidence`。
5. Analysis Agent 运行后不会启动 QA 第 14 步，`review_tasks` 保持为空。

## 2026-05-24：步骤 14 QA 规则服务完成

### 当前完成情况

实施计划中的步骤 14 已完成。该步骤完成后曾按用户要求停在步骤 15 前；当前已继续完成步骤 15，见下节记录。

已完成实现：

1. 新增 `backend/app/services/qa_rules.py`，实现纯规则型 `run_qa_rules`。
2. 更新 `backend/app/services/__init__.py`，统一导出 QA 规则服务。
3. `run_qa_rules` 可检查 Claim、Evidence 和可选 CompetitionEdge，输出结构化 `ReviewTask` 列表。
4. 实现 Claim 证据完整性检查：缺少 `evidence_ids` 或引用不存在 Evidence 会生成审查任务。
5. 实现价格、评分、评价数、销量、排名等时效类证据的 `access_time` 检查。
6. 实现关键价格或认证信息的 `screenshot_path` 检查。
7. 实现推断未标注、敏感绝对化表达、单条评论过度概括、前后矛盾和 CompetitionEdge 风险检查。
8. 新增 `backend/tests/test_qa_rules.py`，验证步骤 14 行为。

### 当前 QA 规则行为

1. 缺少证据的 Claim 会生成 `CLAIM_MISSING_EVIDENCE`，打回目标为 `analysis_agent`。
2. 缺少价格访问时间的 Evidence 会生成 `TIMELY_EVIDENCE_MISSING_ACCESS_TIME`，打回目标为 `collection_agent`。
3. 缺少关键截图的 Evidence 会生成 `CRITICAL_EVIDENCE_MISSING_SCREENSHOT`，打回目标为 `collection_agent`。
4. 推断内容未标记会生成 `INFERENCE_NOT_MARKED`，打回目标为 `analysis_agent`。
5. 单条评论被概括为普遍结论会生成 `SINGLE_REVIEW_OVERGENERALIZED` 风险任务。
6. CompetitionEdge 缺 Claim、低证据置信度、缺证据或冲突风险会生成对应 ReviewTask。
7. 当前步骤只提供规则服务；QA Agent 已在后续步骤 15 基于该服务实现。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_qa_rules.py`：通过，8 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，96 个测试通过。

新增测试覆盖：

1. 缺少证据 ID 的 Claim 会被标记。
2. 缺少价格访问时间会触发打回 Collection。
3. 缺少关键价格截图会触发打回 Collection。
4. 推断内容未标注会触发打回 Analysis。
5. 单条评论被过度概括会触发风险。
6. 敏感绝对化表达会触发保守语言审查。
7. CompetitionEdge 风险标记会被转换为 ReviewTask。
8. 合格 Claim 和边可以通过 QA 规则服务。

## 2026-05-24：步骤 15 QA Agent 节点完成

### 当前完成情况

实施计划中的步骤 15 已完成。该步骤完成后曾按用户要求停在步骤 16 前；当前已继续完成步骤 16，见下节记录。

已完成实现：

1. 新增 `backend/app/agents/qa.py`，实现 `qa_agent_node`。
2. 更新 `backend/app/agents/__init__.py`，统一导出 Collection、Analysis 和 QA 三个 Agent 节点。
3. QA Agent 会从 `TaskGraphState` 读取 Claim、Evidence 和 CompetitionEdge，并调用第 14 步的 `run_qa_rules`。
4. QA 通过时写入 `state["metadata"]["qa_agent"]["qa_status"] = "passed"`，不创建 ReviewTask 或 AgentMessage。
5. QA 失败时将 ReviewTask 追加到 `state["review_tasks"]`。
6. QA 失败时按目标 Agent 生成结构化 `revision_request` AgentMessage，接收方只允许 Collection、Analysis 或 Writer。
7. QA Agent 会记录 `AgentRunLog`；通过时状态为 `succeeded`，需要打回时状态为 `requires_revision`。
8. 新增 `backend/tests/test_qa_agent.py`，验证步骤 15 行为。

### 当前 QA Agent 行为

1. 合格 Claim、Evidence 和 CompetitionEdge 会进入通过状态，不产生打回消息。
2. 缺少价格访问时间会生成打回 Collection 的 `revision_request`。
3. 分析矛盾会生成打回 Analysis 的 `revision_request`。
4. AgentMessage payload 包含 QA 状态、目标 Agent、ReviewTask ID、issue code、严重级别统计、required action 和具体问题目标。
5. metadata 中记录 `qa_status`、`passed`、`review_task_count`、`revision_target`、`revision_targets`、`issue_counts` 和 `severity_counts`。
6. 当前步骤只生成审查结果与打回消息，不补齐 Evidence，不重跑 Collection，不重跑 Analysis，不组装完整 LangGraph DAG。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend\tests\test_qa_agent.py backend\tests\test_qa_rules.py`：通过，12 个测试通过。
2. `backend\.conda312\python.exe -m ruff check backend`：通过。
3. `backend\.conda312\python.exe -m pytest backend`：通过，100 个测试通过。

新增测试覆盖：

1. 合格数据会进入 QA 通过状态。
2. 缺少价格访问时间会生成打回 Collection 的消息。
3. 分析矛盾会生成打回 Analysis 的消息。
4. Trace/metadata 能记录 QA 检查项、问题等级和打回目标。

## 2026-05-24：步骤 16 QA 打回后的 Collection 修复逻辑完成

### 当前完成情况

实施计划中的步骤 16 已完成；按用户要求，尚未开始步骤 17。

已完成实现：

1. 更新 `backend/app/agents/collection.py`，让 `collection_agent_node` 能识别 QA 发给 Collection、状态为 `requires_revision` 的 `revision_request`。
2. Collection 初次运行仍保持原行为：读取 Demo 快照、保留 `sku_01` 缺失访问时间，不自动使用 `qa_revision_fixture`。
3. Collection 第二次运行如果检测到 QA 打回消息，会进入补采修复分支，不重复追加整批 Product、Evidence 和 ReviewInsight。
4. 修复分支读取 `qa_revision_fixture.repair_evidence`，为可补齐字段生成新的 Evidence，并通过 `metadata.repaired_from_evidence_id` 指向原 Evidence。
5. `sku_01` 的 `source.access_time` 已可补齐为 `2026-05-23T16:00:59+08:00`，并在新 Evidence 中移除已修复的 `metadata.missing_fields`。
6. 无法从本地 Demo 快照补齐的字段会生成新 Evidence，并在 `content_summary`、`limitations`、`metadata.fallback_value` 中明确写入“暂无可靠数据”。
7. 修复后的新 Evidence 会追加到对应 Product 的 `evidence_ids`，为后续 Analysis 局部重算保留输入。
8. 被处理的 QA `revision_request` 会标记为 `processed`，payload 中记录新 Evidence ID 和 diff 数量。
9. 修复过程会记录第二条 Collection `AgentRunLog` 和 `snapshot_repair_fixture` `ToolCallLog`。
10. 修复前后差异写入 `state["metadata"]["collection_agent_repair"]["diffs"]`，并同步追加到 `state["metadata"]["collection_agent"]["repair_runs"]`。

### 当前修复行为

1. 只有 QA Agent 发出面向 Collection 的打回消息后，Collection 才会尝试补采修复。
2. 可补齐字段优先使用 Demo 快照内的修复夹具，当前覆盖 `source.access_time` 和 `source.screenshot_path`。
3. 不可补齐字段不会凭空补数据，而是明确降级为“暂无可靠数据”。
4. 修复采用新增 Evidence 的方式保留原始证据，Trace 中可以同时看到 before 与 after。
5. 当前步骤不重跑 Analysis，不更新 Claim、CompetitionEdge 或评分，不组装完整 LangGraph DAG。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -m pytest backend/tests/test_collection_agent.py backend/tests/test_qa_agent.py backend/tests/test_analysis_agent.py`：通过，16 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend/tests`：通过，102 个测试通过。
3. `backend\.conda312\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. QA 打回 Collection 后再次执行 Collection。
2. 可补齐证据会生成新的修复 Evidence，并补齐访问时间。
3. 新 Evidence 会关联回对应 Product。
4. 不可补齐证据会明确标记“暂无可靠数据”。
5. Trace metadata 可查询打回前后的 before/after diff。

## 2026-05-25：步骤 17 QA 打回后的 Analysis 局部重算完成

### 当前完成情况

实施计划中的步骤 17 已完成；按用户要求，在用户验证本步测试前，不开始步骤 18。

已完成实现：

1. 更新 `backend/app/agents/analysis.py`，让 `analysis_agent_node` 能识别 QA 发给 Analysis、状态为 `requires_revision` 的 `revision_request`。
2. Analysis 初次运行路径保持不变，仍只生成目标画像、Claim、CompetitionEdge 和评分解释，不启动完整 DAG、不生成 Writer 报告。
3. Analysis 第二次运行如果检测到 QA 打回消息，会进入局部重算分支，不重复追加整批画像、Claim 或 CompetitionEdge。
4. 局部重算会解析消息中的 Claim 与 CompetitionEdge 目标，只替换受影响的 `claims` 和 `competition_edges`。
5. 如果 Collection 已经生成修复 Evidence，Analysis 会基于当前状态中的最新 Evidence 重新计算 `CompetitionEdgeScore`，并把修复 Evidence ID 纳入对应 Claim。
6. 被打回 Claim 在证据充足时会从 `needs_review` 回到 `accepted`，并移除已处理的 `conflicting_analysis` 风险。
7. 被重算 CompetitionEdge 会更新 `edge_score`、`score_breakdown`、`decision_stages`、`risk_flags` 和 `edge_explanations`。
8. 被处理的 QA `revision_request` 会标记为 `processed`，payload 中写入 `analysis_recompute` 摘要。
9. 重算前后差异写入 `state["metadata"]["analysis_agent_recompute"]`，并同步追加到 `state["metadata"]["analysis_agent"]["recompute_runs"]`。
10. 重算过程会记录第二条 Analysis `AgentRunLog`，输出重算 Claim 数、重算竞争边数和未受影响边数。

### 当前重算行为

1. 只有 QA Agent 发出面向 Analysis 的打回消息后，Analysis 才会尝试局部重算。
2. 重算目标优先来自消息 payload 中的 `claim` 或 `competition_edge`，Claim 关联的边会被一并重算。
3. 重算只更新目标 Claim 和目标 CompetitionEdge，无关竞争边保持稳定。
4. 重算使用当前 Graph State 中的 Evidence 集合，因此能消费步骤 16 产生的修复 Evidence。
5. 当前步骤不组装 LangGraph 主流程，不配置条件边，不实现 Writer Agent，不导出 Markdown。

### 验证结果

验证命令与结果：

1. `backend\.conda312\python.exe -B -m pytest backend\tests\test_analysis_agent.py -p no:cacheprovider`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -B -m pytest backend\tests\test_analysis_agent.py backend\tests\test_collection_agent.py backend\tests\test_qa_agent.py -p no:cacheprovider`：通过，17 个测试通过。
3. `backend\.conda312\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp`：通过，103 个测试通过。
4. `backend\.conda312\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. QA 打回 Analysis 后再次执行 Analysis。
2. 被打回 Claim 的状态从 `needs_review` 回到 `accepted`。
3. Collection 修复 Evidence 后，目标 CompetitionEdge 的 `evidence_confidence` 和 `edge_score` 会重新计算并提高。
4. 无关竞争边保持稳定，不被局部重算误改。
5. Trace metadata 可查询 Analysis 重算前后的 Claim/Edge diff。

## 2026-05-26：步骤 18 LangGraph 主流程组装完成

### 当前完成情况

实施计划中的步骤 18 已完成；按用户要求，尚未开始步骤 19。

已完成实现：

1. 新增 `backend/app/graph/workflow.py`，实现 `build_analysis_workflow`，用 LangGraph `StateGraph` 组装 Collection、Analysis、QA 和 Writer checkpoint。
2. Workflow 入口固定为 `collection_agent`，顺序边为 `collection_agent -> analysis_agent -> qa_agent`。
3. QA 后配置真实条件边：QA 通过进入 `writer_agent` checkpoint；QA 打回 Collection 时回到 `collection_agent`；QA 打回 Analysis 时回到 `analysis_agent`；失败时进入 END。
4. 新增最大打回次数控制，默认 `DEFAULT_MAX_REVISION_ROUNDS = 3`；超过上限时将任务状态标记为 `failed`，并在 `metadata.workflow.failure_reason` 中保留诊断原因。
5. 新增 `writer_checkpoint_node`，只记录工作流已经进入 Writer 阶段并将任务置为 `completed`；真正 Writer Agent、报告数据结构和 Markdown 导出仍留给步骤 19 及后续步骤。
6. Workflow 会在 Collection 修复证据后自动追加面向 Analysis 的结构化 `revision_request`，确保 QA 打回 Collection 后可继续触发 Analysis 局部重算。
7. 更新 `backend/app/graph/__init__.py`，导出 workflow 节点名、构建函数和路由函数。
8. 更新 `backend/app/agents/analysis.py`，在构建或重算 Claim 时优先绑定修复后的 Evidence，避免旧缺失 Evidence 导致 QA 重复打回。
9. 更新 `backend/app/agents/qa.py`，让 QA 多轮运行生成唯一 run_id，避免 Trace 中 QA run id 重复。
10. 更新 `backend/requirements-dev.txt`，补充第 18 步需要的 `langgraph` 依赖。

### 当前 Workflow 行为

1. 默认 Demo 链路会先触发一次 `sku_01` 缺少价格访问时间的 Collection 打回。
2. Collection 修复 Evidence 后，Workflow 自动创建 Analysis 重算消息，再由 Analysis 消费修复证据更新受影响 Claim 和 CompetitionEdge。
3. 第二轮 QA 通过后进入 Writer checkpoint，任务状态置为 `completed`。
4. Writer checkpoint 只证明条件边已经抵达写作阶段，不生成报告、不写 Markdown、不越过步骤 19 边界。
5. 如果最大打回次数设置过低，Workflow 会以可诊断方式失败并保留 QA metadata 与 workflow failure reason。

### 验证结果

本次验证使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。

验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_workflow.py`：通过，4 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests`：通过，107 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. 工作流可完成默认 Demo 的真实 Collection 打回、Collection 修复、Analysis 重算、QA 通过和 Writer checkpoint。
2. 工作流会记录 QA 打回 Collection 的消息和 Collection 修复后自动追加的 Analysis 重算消息。
3. `route_after_qa` 会按 QA 通过、Collection 打回、Analysis 打回返回正确 LangGraph 条件边。
4. 超过最大打回次数时，工作流进入失败状态并保留诊断信息。

## 2026-05-26：步骤 19 Writer Agent 节点完成

### 当前完成情况

实施计划中的步骤 19 已完成；按用户要求，在用户验证本步测试前，不开始步骤 20。

已完成实现：

1. 新增 `backend/app/schemas/report.py`，定义 `ReportData` 与 `ReportSection`，作为网页报告数据结构的 Pydantic 契约。
2. 更新 `backend/app/schemas/__init__.py`，统一导出报告 Schema。
3. 更新 `backend/app/graph/state.py`，为 `TaskGraphState` 新增 `reports` 状态槽，并提供 `append_report_data`。
4. 更新 `backend/app/graph/__init__.py`，导出报告追加函数。
5. 新增 `backend/app/agents/writer.py`，实现真正的 `writer_agent_node`。
6. 更新 `backend/app/agents/__init__.py`，统一导出 Writer Agent 节点。
7. 更新 `backend/app/graph/workflow.py`，默认将 QA 通过后的 `writer_agent` 节点接入真正 Writer Agent，而不是第 18 步 checkpoint；保留 `writer_checkpoint_node` 作为旧边界和测试可注入占位。
8. 新增 `backend/tests/test_writer_agent.py`，覆盖 Writer Agent 的报告章节、证据追溯、风险标注和 Trace 运行日志。
9. 更新 `backend/tests/test_workflow.py`，验证完整 LangGraph workflow 进入真正 Writer Agent 后生成 `reports`，并记录成功 Writer run。

### 当前 Writer 行为

1. Writer Agent 只读取已经存在于 Graph State 的结构化产物：Product、Evidence、FeatureTree、PricingModel、UserPersona、Claim、CompetitionEdge、ReviewInsight 和 ReviewTask。
2. Writer 输入必须满足 QA 已通过，或产物已经显式带有风险标记；否则 Writer 会失败并记录失败 run log。
3. Writer 生成 `ReportData`，包含九个网页报告章节：
   - `executive_summary`
   - `product_profile`
   - `competitor_findings`
   - `dynamic_slice_analysis`
   - `decision_chain_analysis`
   - `user_research_insights`
   - `recommendations`
   - `qa_summary`
   - `evidence_index`
4. 报告中的核心竞品发现和建议均保留 `claim_ids` 与 `evidence_ids`，不新增无来源的价格、认证、尺寸、销量或排名事实字段。
5. 风险 Claim 会在竞品发现和 QA 摘要中继续显示 `risk_flags` 与状态，避免被报告层“洗白”。
6. 用户研究章节只使用结构化 `ReviewInsight` 摘要和 Evidence 引用，不展开未脱敏原文。
7. Writer Agent 成功后追加 `writer_agent` 的 `AgentRunLog`，写入 `metadata.writer_agent`，并将任务状态置为 `completed`。
8. Workflow 的 `writer_agent` 节点包装器会写入 `metadata.workflow.writer_status = "succeeded"`，表明主流程已完成真正写作节点。

### 当前边界

1. 步骤 19 只生成网页报告数据结构，不生成 Markdown 文本。
2. 未创建 `GET /tasks/{task_id}/report` 或 `GET /tasks/{task_id}/report/markdown` API。
3. 未将报告数据持久化到 SQLite，当前仍只保存在内存 `TaskGraphState["reports"]`。
4. 未保存任何文件到 `data/reports/`。
5. 未启动 `POST /tasks` 后的后台 LangGraph 执行链路。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。

验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_workflow.py`：通过，8 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests`：通过，111 个测试通过。

新增测试覆盖：

1. Writer Agent 可生成所有必需报告章节。
2. 报告中的核心竞品发现均可追溯到 Claim 和 Evidence。
3. 风险 Claim 会在报告中标明，不会被当作无风险结论输出。
4. Writer Agent 会记录成功 Trace run log。
5. 完整 workflow 在 QA 通过后会进入真正 Writer Agent，并生成 `reports`。

## 2026-05-26：步骤 20 Markdown 报告导出服务完成

### 当前完成情况

实施计划中的步骤 20 已完成；按用户要求，在用户验证本步测试前，不开始步骤 21。

已完成实现：

1. 扩展 `backend/app/schemas/report.py`，新增 `MarkdownReport`，记录 Markdown 文本、文件路径、导出时间和统计元信息。
2. 更新 `backend/app/schemas/__init__.py`，统一导出 `MarkdownReport`。
3. 更新 `backend/app/graph/state.py`，为 `TaskGraphState` 新增 `markdown_reports` 状态槽，并提供 `append_markdown_report`。
4. 更新 `backend/app/graph/__init__.py`，导出 `append_markdown_report`。
5. 新增 `backend/app/services/markdown_renderer.py`，实现 `render_markdown_report` 与 `export_markdown_report_for_state`。
6. 更新 `backend/app/services/__init__.py`，统一导出 Markdown 导出服务入口、默认报告目录和导出异常类型。
7. 新增 `backend/tests/test_markdown_renderer.py`，覆盖 Markdown 九章节、Claim/Evidence 可见索引、缺失证据兜底和敏感 Key 模式阻断。

### 当前 Markdown 导出行为

1. 导出服务基于第 19 步 `ReportData` 渲染 Markdown，不重新推理竞争事实，不新增无证据字段。
2. Markdown 固定包含九个报告章节：执行摘要、目标产品画像、竞品发现、动态竞争切片、决策链竞争分析、用户研究洞察、可执行建议、QA 审查摘要和 Evidence 索引。
3. 竞品发现中的核心 Claim 会显示 Claim ID、正文、置信度、状态、推断标识、风险标记和 Evidence ID。
4. Evidence 索引会显示 Evidence ID、来源类型、来源 URL、截图路径、访问时间、置信度、摘要和局限性。
5. 缺失 Evidence、访问时间、截图或其他空值时，Markdown 显示“暂无可靠数据”，不凭空补字段。
6. 导出前会扫描 `sk-...`、`api_key=...`、`secret=...`、`password=...`、`token=...` 和 `Bearer ...` 等敏感模式；命中时抛出 `MarkdownRenderError`，不会写出文件。
7. 默认保存目录为 `<project-root>/data/reports/`；测试可注入临时目录，避免污染正式导出目录。
8. `export_markdown_report_for_state` 会把导出结果追加到 `state["markdown_reports"]`，并在 `metadata.markdown_report` 中记录 report_id、file_path、generated_at 和统计元信息。

### 当前边界

1. 步骤 20 只实现服务层导出，不创建 `GET /tasks/{task_id}/report` 或 `GET /tasks/{task_id}/report/markdown` API。
2. MarkdownReport 当前只写入内存 Graph State；SQLite 持久化仍留给后续步骤。
3. 未将 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。
4. 未启动前端报告页、导出按钮或网页报告 API 对接。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。

验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_markdown_renderer.py`：通过，4 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_markdown_renderer.py backend\tests\test_writer_agent.py backend\tests\test_workflow.py`：通过，12 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp`：通过，115 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. Markdown 报告包含九个必需章节，且导出文件内容与返回 Markdown 一致。
2. 核心竞品发现中的每个 Claim 都能在 Markdown 中看到 Claim ID、置信度、推断标识和关联 Evidence。
3. 缺失 Evidence 时显示“暂无可靠数据”。
4. 命中敏感环境变量或 API Key 模式时阻断导出。

## 2026-05-26：步骤 21 报告 API 完成

### 当前完成情况

实施计划中的步骤 21 已完成；按用户要求，在用户验证本步测试前，不开始步骤 22。

已完成实现：

1. 新增 `backend/app/api/dependencies.py`，抽出 FastAPI app 级 SQLite session factory 与 repository session 管理，供任务 API 和报告 API 复用。
2. 更新 `backend/app/api/routes_tasks.py`，改为复用 `repository_session`，保持任务创建和任务状态查询行为不变。
3. 新增 `backend/app/services/report_service.py`，实现 `ReportService`、`ReportServiceError`、`REPORT_ARTIFACT_TYPE` 和 `MARKDOWN_REPORT_ARTIFACT_TYPE`。
4. 更新 `backend/app/services/__init__.py`，统一导出报告服务和报告 Artifact 类型常量。
5. 新增 `backend/app/api/routes_reports.py`，实现 `GET /tasks/{task_id}/report` 与 `GET /tasks/{task_id}/report/markdown`。
6. 更新 `backend/app/main.py`，注册报告路由。
7. 新增 `backend/tests/test_reports_api.py`，覆盖完成任务报告获取、Markdown 导出、未完成任务错误、导出失败不影响网页报告和缺失任务错误。

### 当前报告 API 行为

1. `GET /tasks/{task_id}/report` 只允许 `completed` 任务访问；任务不存在返回 `TASK_NOT_FOUND`，未完成返回 `REPORT_NOT_READY` 和当前任务状态。
2. 如果 SQLite `artifact_json` 中已有 `report_data`，报告 API 直接返回最新 `ReportData`。
3. 如果任务已完成但还没有缓存报告，`ReportService` 会同步运行现有 LangGraph workflow 生成 `ReportData`，并将其保存为 `report_data` Artifact。
4. `GET /tasks/{task_id}/report/markdown` 会先取得或生成 `ReportData`，再复用第 20 步 `render_markdown_report` 导出 Markdown。
5. Markdown 导出成功后会保存 `.md` 文件，并把 `MarkdownReport` 保存为 `markdown_report` Artifact。
6. Markdown 导出失败时返回 `MARKDOWN_EXPORT_FAILED` 标准错误；已缓存的网页 `ReportData` 仍可继续通过报告接口读取。
7. 测试中通过 `app.state.report_output_dir` 注入临时导出目录，正式运行默认继续使用 `<project-root>/data/reports/`。

### 当前边界

1. 步骤 21 只实现报告 API，不实现 `GET /tasks/{task_id}/profile`。
2. 报告 API 为已完成任务提供同步报告生成兜底；尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。
3. 当前只缓存 ReportData 与 MarkdownReport；Product、Evidence、Claim、CompetitionEdge、Trace 全量持久化仍留给后续步骤。
4. 未启动前端报告页、Markdown 导出按钮或轮询集成。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。

验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_reports_api.py`：通过，5 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_markdown_renderer.py backend\tests\test_workflow.py`：通过，22 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp`：通过，120 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. 完成任务可以通过 API 获取九章节网页报告数据。
2. 完成任务可以通过 API 导出 Markdown，响应包含 Markdown 文本、文件路径和符合预期的 `.md` 文件名。
3. 未完成任务请求报告会返回 `REPORT_NOT_READY` 标准错误。
4. Markdown 导出失败会返回 `MARKDOWN_EXPORT_FAILED`，但网页报告接口继续可用。
5. 不存在任务请求报告会返回 `TASK_NOT_FOUND` 标准错误。

## 2026-05-26：步骤 22 产品画像 API 完成

### 当前完成情况

实施计划中的步骤 22 已完成；按用户要求，在用户验证本步测试前，不开始步骤 23。

已完成实现：

1. 新增 `backend/app/schemas/profile.py`，定义 `ProductProfileData`、`EvidenceSummary` 和 `PricingEvidenceSummary`。
2. 更新 `backend/app/schemas/__init__.py`，统一导出产品画像响应 Schema。
3. 新增 `backend/app/services/profile_service.py`，实现 `ProfileService`、`ProfileServiceError`、`PRODUCT_PROFILE_ARTIFACT_TYPE` 和 `MAX_EVIDENCE_SUMMARY_CHARS`。
4. 更新 `backend/app/services/__init__.py`，统一导出画像服务和画像 Artifact 类型常量。
5. 新增 `backend/app/api/routes_profile.py`，实现 `GET /tasks/{task_id}/profile`。
6. 更新 `backend/app/main.py`，注册产品画像路由。
7. 新增 `backend/tests/test_profile_api.py`，覆盖完成任务画像获取、价格证据状态、Evidence 摘要长度、未完成任务错误和缺失任务错误。

### 当前产品画像 API 行为

1. `GET /tasks/{task_id}/profile` 只允许 `completed` 任务访问；任务不存在返回 `TASK_NOT_FOUND`，未完成返回 `PROFILE_NOT_READY` 和当前任务状态。
2. 如果 SQLite `artifact_json` 中已有 `product_profile`，画像 API 直接返回最新 `ProductProfileData`。
3. 如果任务已完成但还没有缓存画像，`ProfileService` 会同步运行现有 LangGraph workflow，生成目标产品画像并将其保存为 `product_profile` Artifact。
4. 响应包含目标 `Product`、目标 `FeatureTree`、目标 `PricingModel`、`PricingEvidenceSummary`、目标 `UserPersona` 和 `EvidenceSummary` 列表。
5. `pricing_evidence` 明确包含价格证据 `evidence_ids`、`access_time`、`access_time_status` 和风险标记，便于前端直接展示价格字段证据状态。
6. `EvidenceSummary.content_summary` 和 `limitations` 会压缩到 `MAX_EVIDENCE_SUMMARY_CHARS = 180` 字符以内，避免返回过长原文。
7. Evidence 摘要会标记 `access_time_status`，并在缺少访问时间或截图路径时带上对应风险标记。

### 当前边界

1. 步骤 22 只实现产品画像 API，不实现 `GET /tasks/{task_id}/battlefield`。
2. 画像 API 为已完成任务提供同步画像生成兜底；尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。
3. 当前只缓存 ProductProfileData；完整 Product、Evidence、Claim、CompetitionEdge、Trace 全量持久化仍留给后续步骤。
4. 未启动前端产品画像页或 Human Review 交互。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。

验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_profile_api.py`：通过，5 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_profile_api.py backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_workflow.py`：通过，23 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp`：通过，125 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. 完成任务可以通过 API 获取目标产品基础信息、FeatureTree、PricingModel、UserPersona 和 Evidence 摘要。
2. 价格字段包含证据引用和访问时间状态。
3. Evidence 摘要不会返回过长原文，也不会泄露测试中的私密研究文本片段。
4. 未完成任务请求画像会返回 `PROFILE_NOT_READY` 标准错误。
5. 不存在任务请求画像会返回 `TASK_NOT_FOUND` 标准错误。

## 2026-05-26：步骤 23 竞争图谱 API 完成

### 当前完成情况

实施计划中的步骤 23 已完成；按用户要求，在用户验证本步测试前，不开始步骤 24。

已完成实现：

1. 新增 `backend/app/schemas/battlefield.py`，定义 `BattlefieldData`、切片选择与候选、图节点、图边、Claim 引用、评分解释、决策链阶段、Evidence 卡片和 QA 摘要。
2. 更新 `backend/app/schemas/__init__.py`，统一导出竞争图谱响应 Schema。
3. 新增 `backend/app/services/battlefield_service.py`，实现 `BattlefieldService`、`BattlefieldServiceError`、`BATTLEFIELD_ARTIFACT_TYPE` 和 Evidence 卡片摘要长度常量。
4. 更新 `backend/app/services/__init__.py`，统一导出竞争图谱服务入口。
5. 新增 `backend/app/api/routes_battlefield.py`，实现 `GET /tasks/{task_id}/battlefield`，支持 `price_band`、`persona`、`scenario` 查询参数过滤。
6. 更新 `backend/app/main.py`，注册竞争图谱路由。
7. 新增 `backend/tests/test_battlefield_api.py`，覆盖默认竞争图谱数据、价格带切换、边的 Claim/Evidence 引用、QA 风险边和未完成任务错误。

### 当前竞争图谱 API 行为

1. `GET /tasks/{task_id}/battlefield` 只允许 `completed` 任务访问；任务不存在返回 `TASK_NOT_FOUND`，未完成返回 `BATTLEFIELD_NOT_READY`。
2. 如果 SQLite `artifact_json` 已存在对应切片的 `battlefield_data`，API 会直接返回缓存；否则同步运行现有 LangGraph workflow 生成竞争图谱数据并缓存。
3. 默认不传切片参数时返回全部竞争边，并按 `edge_score` 降序排列，前端可直接展示最高分直接竞品与替代/渠道类竞品。
4. 传入 `price_band`、`persona` 或 `scenario` 时只过滤对应维度，未传维度作为通配条件。
5. 每条 `graph_edges` 都包含 `claim_ids`、`evidence_ids` 和 `claim_refs`，并保留 `score_breakdown` 与可读评分解释。
6. `evidence_cards` 只来自边关联 Claim 的 Evidence，不新增无证据事实；缺失访问时间或截图路径时会带对应风险标记。
7. `qa_summary` 汇总 ReviewTask 数量、修复消息数量、风险边和风险 Claim；边自身风险、Claim 风险或开放 ReviewTask 都会让边进入 `at_risk`。

### 当前边界

1. 步骤 23 只实现竞争图谱 API，不实现 `GET /tasks/{task_id}/trace`。
2. 竞争图谱 API 当前复用同步 workflow 兜底生成，完整后台执行落地和全量底层 Artifact/Trace 持久化仍留给后续步骤。
3. 当前缓存粒度按任务和切片参数区分，避免不同切片互相覆盖。
4. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。

验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_battlefield_api.py`：通过，5 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_battlefield_api.py backend\tests\test_profile_api.py backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_workflow.py`：通过，28 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp`：通过，130 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. 默认竞争图谱切片返回按得分排序的直接竞品，并包含替代或渠道类竞品。
2. 切换价格带会改变竞争边集合或评分解释，并且返回边都属于所选价格带。
3. 每条竞争边都包含 Claim 和 Evidence 引用，Evidence 卡片可覆盖边引用的 Evidence。
4. 被 QA 或服务标记风险的竞争边会带 `at_risk` 状态并进入 QA 摘要。
5. 未完成任务请求竞争图谱数据会返回 `BATTLEFIELD_NOT_READY` 标准错误。

## 下一步边界：等待用户验证后再进入步骤 24

在用户明确验证第 23 步测试通过前，不开始实施计划步骤 24。

步骤 24 边界提醒：

1. 下一步才是 Trace API。
2. `GET /tasks/{task_id}/trace` 应返回 DAG 节点状态、Agent Run、Tool Call、Token Usage、QA Review 和 Diff View。
3. Prompt 只能脱敏后折叠展示，失败节点不能被隐藏。
4. Trace API 仍必须使用统一 API 响应与标准错误结构。
5. 继续禁止引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

## 2026-05-26：步骤 24 Trace API 完成

### 当前完成情况

实施计划中的步骤 24 已完成；按用户要求，在用户验证本步测试前，不开始步骤 25。
已完成实现：

1. 扩展 `backend/app/schemas/trace.py`，新增 `TraceData`、`TraceDagNode`、`TraceDagEdge`、`TraceDiff`、`TracePromptPreview`，在已有 Agent Run、Tool Call、Token Usage schema 之上形成 Trace API 响应契约。
2. 新增 `backend/app/services/trace_service.py`，实现 `TraceService`、`TraceServiceError`、`TRACE_ARTIFACT_TYPE`，负责读取/生成 Trace、组装 DAG、汇总 QA 回滚与 Diff，并执行 Trace 专用脱敏。
3. 新增 `backend/app/api/routes_trace.py`，实现 `GET /tasks/{task_id}/trace`，沿用统一 `ApiResponse` 和标准错误结构。
4. 更新 `backend/app/main.py` 注册 Trace 路由。
5. 更新 `backend/app/schemas/__init__.py` 与 `backend/app/services/__init__.py`，统一导出 Trace schema 与 service。
6. 新增 `backend/tests/test_trace_api.py`，覆盖 DAG 节点/边、每个 Agent Run Log、QA revision 与 Diff View、敏感信息脱敏、未完成任务 Trace 骨架和缺失任务错误。

### 当前 Trace API 行为

1. `GET /tasks/{task_id}/trace` 对不存在任务返回 `TASK_NOT_FOUND`。
2. 对 `completed` 任务，优先读取 SQLite `artifact_json` 中的 `trace_data`；无缓存时同步运行现有 LangGraph workflow 生成 `TraceData` 并缓存。
3. 对未完成任务，返回可轮询的 Trace 骨架：DAG 节点和边可见，Agent Run、Tool Call、QA、Diff 为空，不触发 workflow 生成。
4. DAG 包含 `collection_agent`、`analysis_agent`、`qa_agent`、`writer_agent`、`failed`、`end` 节点；`failed` 节点始终 `visible=true`。
5. Trace 响应包含 Agent Run、Tool Call、Token Usage、QA ReviewTask、Revision AgentMessage、Collection repair diff 和 Analysis recompute diff。
6. Prompt 仅以 `prompt_previews` 形式返回折叠摘要，`folded=true` 且 `redacted=true`，不返回原始 prompt。
7. Trace 专用脱敏保留 `token_usage` 等结构字段，同时清理 `api_key`、Bearer token、`sk-` 类密钥和值级敏感片段。

### 当前边界

1. 步骤 24 只实现 Trace API，不开始步骤 25。
2. 当前 Trace API 仍复用同步 workflow 兜底生成；完整后台任务执行链路和底层全量 Artifact/Trace 持久化仍留给后续步骤。
3. 当前缓存粒度为任务级 `trace_data` 聚合结果；后续后台任务落地后，可优先读取真实执行产生的持久化 TraceLog。
4. 没有引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。
验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_trace_api.py`：通过，6 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_trace_api.py backend\tests\test_battlefield_api.py backend\tests\test_profile_api.py backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_workflow.py`：通过，34 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests`：通过，136 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. Trace API 返回 DAG nodes 和 edges，并确保 failed 节点可见。
2. Trace API 确认 Collection、Analysis、QA、Writer 每个 Agent 至少有一条 run log。
3. Trace API 可查询 QA revision message、ReviewTask、Collection repair diff 和 Analysis recompute diff。
4. Trace 安全测试确认响应不包含 API Key、Bearer token、`sk-` 密钥或未脱敏私密字段。
5. 未完成任务返回 Trace 骨架，缺失任务返回标准 `TASK_NOT_FOUND`。

## 下一步边界：等待用户验证后再进入步骤 25

在用户明确验证第 24 步测试通过前，不开始实施计划步骤 25。
步骤 25 边界提醒：

1. 下一步才处理实施计划第 25 步。
2. 不在当前步继续扩展 Trace API 之外的功能。
3. 继续禁止引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

## 2026-05-26：步骤 25 Human Feedback API 完成

### 当前完成情况

实施计划中的步骤 25 已完成；按用户要求，在用户验证本步测试前，不开始步骤 26。
已完成实现：

1. 扩展 `backend/app/schemas/review.py`，新增 `HumanFeedbackCreateRequest` 与 `HumanFeedbackCreateResponse`。
2. 更新 `backend/app/schemas/__init__.py`，统一导出 Human Feedback 创建请求和响应 Schema。
3. 更新 `backend/app/storage/repositories.py`，为 `TaskRepository` 增加 `update_metadata`，用于记录待重算标记。
4. 新增 `backend/app/services/feedback_service.py`，实现 `FeedbackService`、`FeedbackServiceError` 与 `HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE`。
5. 新增 `backend/app/api/routes_feedback.py`，实现 `POST /tasks/{task_id}/feedback`，沿用统一 `ApiResponse` 和标准错误结构。
6. 更新 `backend/app/main.py` 注册 Feedback 路由。
7. 更新 `backend/app/services/__init__.py`，统一导出反馈服务和反馈影响 Artifact 类型常量。
8. 新增 `backend/tests/test_feedback_api.py`，覆盖允许范围反馈保存、禁止自由改写报告、before/after 保存、待重算标记和标准错误。

### 当前 Human Feedback API 行为

1. `POST /tasks/{task_id}/feedback` 对不存在任务返回 `TASK_NOT_FOUND`。
2. 只允许 `completed` 或 `human_reviewing` 任务提交反馈；未完成任务返回 `FEEDBACK_NOT_READY`。
3. 允许的结构化反馈范围包括：
   - 产品画像字段：`product`、`feature_tree`、`pricing_model`、`user_persona` 的 allowlist 字段更新。
   - Claim 采纳状态：`mark_accepted`、`mark_rejected`、`mark_needs_review`。
   - Evidence 备注：`add_note`。
   - 竞品集合：当前支持通过 `competition_edge` + `remove_competitor` 标记移除竞品。
   - 动态切片：当前支持 `slice` + `update_field` 更新 `price_band`、`persona` 或 `scenario`。
4. 不允许自由改写整份报告或直接改写 Claim 正文；非法目标和动作组合返回 `FEEDBACK_NOT_ALLOWED` 或 `FEEDBACK_INVALID_PAYLOAD`。
5. 服务会从当前 workflow 结构化上下文中读取目标对象，自动生成 `before_value`，并把请求中的合法修正规范化为 `after_value`。
6. 反馈保存到 `human_feedback` 表；同时保存 `human_feedback_effect` Artifact，记录 `feedback_id`、受影响对象和 `marked_for_reanalysis` 状态。
7. 提交反馈后，任务状态更新为 `human_reviewing`，任务 metadata 标记 `requires_analysis_recompute=true`，用于后续步骤触发真正的局部重算。

### 当前边界

1. 步骤 25 只实现 Human Feedback API，不开始步骤 26 的前端路由与布局。
2. 当前提交反馈后采用“标记待重算”策略，不伪造已经完成的后台局部重算。
3. 当前仍复用同步 workflow 构建反馈上下文；完整后台任务执行链路和真正的 Human Review 后局部重算留给后续步骤。
4. 没有引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

### 验证结果

本次验证继续使用 Codex bundled Python 3.12.13；当前工作区没有 `backend/.conda312`。
验证命令与结果：

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_feedback_api.py`：通过，6 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_feedback_api.py backend\tests\test_tasks_api.py backend\tests\test_profile_api.py backend\tests\test_battlefield_api.py backend\tests\test_trace_api.py backend\tests\test_reports_api.py backend\tests\test_workflow.py backend\tests\test_storage_repositories.py`：通过，46 个测试通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests`：通过，142 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend`：通过。

新增测试覆盖：

1. 允许范围内的产品画像字段反馈可以保存，并自动记录 before/after。
2. Claim 采纳状态反馈可以保存，并记录状态变更前后值。
3. 不允许通过反馈接口自由改写报告或 Claim 正文。
4. 反馈提交后写入 `human_feedback_effect` Artifact，并标记 `marked_for_reanalysis`。
5. 未完成任务反馈返回 `FEEDBACK_NOT_READY`，缺失任务返回 `TASK_NOT_FOUND`。

## 2026-05-26：步骤 26 前端路由与整体布局完成

### 当前完成情况

实施计划中的步骤 26 已完成；本次检查确认现有代码已经满足主计划第 26 步要求，因此未修改业务代码，仅同步本进度记录。

已对齐实现：

1. `frontend/src/App.tsx` 已建立五个页面入口：输入页 `/`、产品画像页 `/profile`、竞争图谱页 `/battlefield`、报告页 `/report`、过程追踪页 `/trace`。
2. 已建立统一工作台布局，包含侧边主导航、页面标题区、状态标记和页面模块骨架。
3. 页面首屏是分析工作台，不是营销型首页。
4. 当前页面结构保持数据密集型分析工具风格，并使用中文展示文案；技术路由 `/battlefield` 和 `/trace` 保持稳定。
5. `frontend/src/App.test.tsx` 已覆盖五个页面路由可访问、导航跳转和主导航 landmark。

### 本步边界

1. 步骤 26 只确认前端路由与整体布局，不在本次新增或扩展 API Client、类型同步、任务创建、任务状态轮询或页面业务数据渲染。
2. 本步不进入主计划步骤 27 的新增实施或验收推进。
3. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

### 验证结果

验证命令与结果：

1. `npm --prefix frontend run test -- App.test.tsx`：通过，1 个测试文件、7 个测试通过，覆盖五个页面路由可访问、导航跳转和主导航 landmark。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format`：通过，已完成第 26 步验收前的前端 Prettier 格式修复，仅调整既有前端文件排版，不改变业务逻辑。
5. `npm --prefix frontend run format:check`：通过，所有匹配文件符合 Prettier 格式规则。

## 2026-05-26：步骤 27 前端 API Client 和类型同步完成

### 当前完成情况

实施计划中的步骤 27 已完成；本步补齐主计划要求的前端 API Client、后端 OpenAPI 类型同步、类型契约检查和组件错误态展示。按用户要求，在用户验证本步测试前，不开始步骤 28。

已完成实现：

1. 保留并复用 `frontend/src/api/client.ts` 的统一 `ApiClient`、`FetchApiTransport`、`MockApiTransport`、`ApiClientError` 和后端统一响应解析。
2. 保留并复用 `frontend/src/api/state.ts` 的 `idle`、`loading`、`success`、`empty`、`error`、`retrying` 请求状态工具。
3. 新增 `openapi-typescript` 前端开发依赖，用于从 FastAPI OpenAPI 生成 TypeScript 类型。
4. 新增 `scripts/sync-openapi-types.mjs`，直接调用后端 `create_app().openapi()` 导出 OpenAPI，再生成 `frontend/src/api/schema.ts`。
5. 新增 `npm --prefix frontend run sync:types` 脚本，后端接口契约变化后可重复同步前端类型。
6. 新增 `frontend/src/api/contracts.test.ts`，用生成的 `operations`、`paths`、`components` 检查任务创建、任务状态、画像、竞争图谱、Trace、报告和 Human Feedback 接口字段。
7. 新增 `frontend/src/api/RequestStateMessage.tsx`，统一展示加载、空数据、错误和重试入口，后续页面可复用，不在组件里散落错误渲染逻辑。
8. 新增 `frontend/src/api/RequestStateMessage.test.tsx`，确认 API 错误状态会显示错误消息、错误码、Trace ID 和重试按钮，而不是静默失败。
9. 更新 `frontend/src/api/index.ts`，集中导出 API Client、请求状态、错误展示组件和 OpenAPI 生成类型。

### 本步边界

1. 步骤 27 只处理 API Client、类型同步、请求状态和错误态展示，不实现输入页表单。
2. 未调用 `POST /tasks` 创建任务，未处理创建成功跳转，也未实现任务轮询。
3. `frontend/src/types/domain.ts` 和 `frontend/src/mocks/*` 仍作为前端开发 fixture 的临时类型和开发数据保留；真实业务接口字段以 `frontend/src/api/schema.ts` 的 OpenAPI 生成类型为准。
4. 本步未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

### 验证结果

验证命令与结果：

1. `npm --prefix frontend run sync:types`：通过，已从后端 FastAPI OpenAPI 生成 `frontend/src/api/schema.ts`。
2. `npm --prefix frontend run test -- api/client.test.ts api/state.test.ts api/contracts.test.ts api/RequestStateMessage.test.tsx`：通过，覆盖 API 成功响应、错误响应、请求状态、OpenAPI 类型契约和组件错误态。
3. `npm --prefix frontend run test`：通过。
4. `npm --prefix frontend run lint`：通过。
5. `npm --prefix frontend run build`：通过。
6. `npm --prefix frontend run format:check`：通过。

### 环境说明

1. 安装 `openapi-typescript` 时，默认 npm 缓存目录 `d:\nodejs-16.13.2\node_cache` 存在权限问题；已通过 `--cache .\frontend\.npm-cache` 使用工作区临时缓存完成安装，临时缓存已由 `.gitignore` 忽略。
2. 安装过程中出现 npm engine warning：`@redocly/openapi-core` 要求 npm `>=9.5.0`，当前 npm 为 `9.4.2`；当前 Node.js v20.20.2 满足依赖要求，且类型同步、测试、lint、build 均通过。

## 当时边界记录：等待用户验证后再进入步骤 28

当时约定为：在用户明确验证第 27 步测试通过前，不开始实施计划步骤 28。

步骤 28 边界提醒：

1. 下一步才实现输入页表单。
2. 下一步才调用 `POST /tasks` 创建任务。
3. 下一步才处理创建成功后默认跳转到过程追踪页。
4. 继续禁止绕过 API Client 直接在组件中拼接原始请求。

## 2026-05-27：步骤 28 前端输入页完成

### 当前完成情况

实施计划中的步骤 28 已完成；按用户要求，在用户验证本步测试前，不开始步骤 29。

已完成实现：

1. 更新 `frontend/src/App.tsx`，将 `/` 输入页从占位模块替换为真实任务创建表单。
2. 输入页已实现目标产品名称、商品链接、品类、子类、数据模式和用户研究文本输入。
3. 默认数据模式为 `demo_snapshot`，默认目标沿用 Demo 主线产品“小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆”。
4. 选择 `snapshot_plus_live` 时显示稳定性提示，说明 MVP 会记录增强模式并使用本地快照兜底。
5. 提交时只通过统一 `ApiClient.post("/tasks", payload)` 调用后端任务创建 API，不绕过第 27 步 API Client。
6. 创建成功后跳转到 `/trace?task_id=<task_id>`，保持“创建任务后默认进入过程追踪页”的产品决策。
7. API 错误复用 `RequestStateMessage` 展示错误消息、错误码和 Trace ID。
8. 更新 `frontend/src/App.css`，补齐输入页表单、数据模式、提交摘要、稳定性提示和错误态样式。
9. 更新 `frontend/src/App.test.tsx`，新增第 28 步表单与任务创建测试。
10. 更新 `frontend/vite.config.ts`，将 Vitest pool 调整为 `vmThreads`，解决旧中文路径工作区下 `threads` worker 启动超时导致默认测试命令不稳定的问题。

### 本步边界

1. 步骤 28 只实现输入页表单、任务创建调用、错误展示和创建成功跳转。
2. 尚未实现步骤 29 的任务状态轮询。
3. 尚未在 Trace 页根据 URL `task_id` 请求任务状态或 Trace 数据。
4. 尚未接入 TanStack Query；轮询能力留到步骤 29。
5. 未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

### 验证结果

验证命令与结果：

1. `npm --prefix frontend run test -- App.test.tsx`：通过，1 个测试文件、12 个测试通过。

新增测试覆盖：

1. 必填目标产品名称缺失时不能提交，且不会调用任务创建 API。
2. 默认数据模式为本地快照。
3. 合法表单提交会创建任务，并跳转到 `/trace?task_id=<task_id>`。
4. 选择 `snapshot_plus_live` 会展示稳定性提示。
5. API 错误会展示给用户，包含错误消息、错误码和 Trace ID。

## 当时边界记录：等待用户验证后再进入步骤 29

当时约定为：在用户明确验证第 28 步测试通过前，不开始实施计划步骤 29。

步骤 29 边界提醒：

1. 下一步才实现任务状态轮询。
2. 下一步才调用 `GET /tasks/{task_id}` 恢复和刷新任务状态。
3. 下一步才处理运行中、完成、失败状态的轮询停止条件。
4. 继续禁止把轮询逻辑混入第 28 步输入页实现。

## 2026-05-27：项目迁移与第 28 步联调收尾

### 当前完成情况

项目根目录已迁移到 `D:\pythonproject\zijieagent`。旧路径中迁移失败的 `frontend/` 已补齐到新目录；只复制源码、配置与 lock 文件，未复制 `node_modules/`、`dist/`、`.npm-cache/` 等可再生成产物。

本次同时完成第 28 步真实前后端联调收尾：后端新增本地 Vite CORS 白名单，解决输入页从 `http://127.0.0.1:5173` 调用 `POST /tasks` 时浏览器预检被拦的问题。CORS 白名单限定在本地开发 Origin 范围内。

迁移后还修复了 Vitest 路径稳定性问题：移除全局 `setupFiles`，改为在需要 `@testing-library/jest-dom` matcher 的测试文件内显式导入 `@testing-library/jest-dom/vitest`。该调整只影响测试配置，不改变输入页业务逻辑，也不进入步骤 29。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_cors.py backend\tests\test_tasks_api.py backend\tests\test_api_response.py -p no:cacheprovider`：通过，14 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests -p no:cacheprovider`：通过，144 个测试通过。
3. `backend\.conda312\python.exe -m ruff check backend`：通过。
4. `npm --prefix frontend run test`：通过，6 个测试文件、27 个测试通过。
5. `npm --prefix frontend run lint`：通过。
6. `npm --prefix frontend run build`：通过。
7. `npm --prefix frontend run format:check`：通过。
8. 新路径后端使用临时 SQLite 运行库完成真实 HTTP 联调：`OPTIONS /tasks` CORS 预检返回 200，`POST /tasks` 返回 201，并正确记录 `snapshot_plus_live` 模式。

### 本步边界

1. 项目后续以 `D:\pythonproject\zijieagent` 为根目录。
2. 本节仍属于第 28 步收尾：输入页创建任务、错误展示、增强模式提示、成功跳转 Trace。
3. 第 29 步轮询能力在下一节单独记录，避免把第 28 步联调和第 29 步实现混在一起。

## 2026-05-27：步骤 29 前端任务状态轮询完成

### 当前完成情况

实施计划中的步骤 29 已完成；按用户要求，在用户验证本步测试前，不开始步骤 30。

已完成实现：

1. 新增前端依赖 `@tanstack/react-query`，用于管理任务状态轮询。
2. `frontend/src/App.tsx` 新增 `QueryClientProvider`，为当前和后续页面提供统一服务端状态入口。
3. `/trace?task_id=<task_id>` 现在会从 URL 读取任务 ID，并通过统一 `ApiClient.get("/tasks/{task_id}")` 获取任务状态。
4. 运行中任务每 1000ms 轮询一次，覆盖 `created`、`collecting`、`analyzing`、`reviewing`、`writing`。
5. 任务进入 `completed`、`failed`、`partial_failed` 或 `human_reviewing` 后停止轮询。
6. 失败和部分失败任务会显示明确错误提示；没有 `task_id` 时显示空态提示。
7. Trace 页继续保留流程状态、运行记录、质检打回、差异视图四个模块骨架，但本步不调用 Trace API。
8. 更新 `frontend/src/App.css`，补齐任务状态面板、状态徽标、失败提示和空态样式。
9. 更新 `frontend/src/App.test.tsx`，新增运行中持续轮询、完成后停止轮询、失败态展示和刷新恢复状态测试。
10. 更新 `frontend/vite.config.ts`，显式固定 `root` 到前端目录，并把 Vite 缓存目录改为 `.vite-cache`。
11. 更新 `frontend/package.json`，将测试脚本固定为 `vitest run --configLoader runner`，避免 Vite 配置临时文件在 Windows/Codex 沙箱中被锁或路径错位。
12. 更新 `.gitignore`、`frontend/.prettierignore` 和 `frontend/eslint.config.js`，忽略 `.vite-cache` 缓存产物。

### 验证结果

1. `npm --prefix frontend run test`：通过，6 个测试文件、31 个测试通过。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format:check`：通过。

新增测试覆盖：

1. 运行中任务会持续请求状态。
2. 完成任务会停止轮询。
3. 失败任务会显示错误提示。
4. 页面刷新后仍可根据 URL `task_id` 恢复任务状态。

### 本步边界

1. 步骤 29 只实现任务状态轮询、终止条件和刷新后状态恢复。
2. 尚未实现步骤 30 的产品画像页。
3. 尚未调用 `GET /tasks/{task_id}/profile`。
4. 尚未调用 `GET /tasks/{task_id}/trace` 或渲染真实 DAG、Agent Run、Tool Call、Token、QA 打回、Diff。
5. 未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

## 2026-05-27：步骤 29 验收期间按钮联调修复

### 问题背景

用户在 `http://127.0.0.1:5173/` 点击“启动分析任务”时，先后遇到 `CLIENT_ERROR`、`NETWORK_ERROR`，最终诊断面板显示：

1. 当前页面：`http://127.0.0.1:5173/`
2. 请求地址：`http://127.0.0.1:8000/tasks`
3. 底层原因：`'fetch' called on an object that does not implement interface Window.`

本节记录的是第 29 步用户验收期间的联调修复，不代表进入步骤 30。

### 修复内容

1. 后端 `CORSMiddleware` 启用 `allow_private_network=True`，并新增覆盖 Private Network Access 预检的 CORS 测试。
2. 后端 CORS 配置扩展为只允许本机 `127.0.0.1` / `localhost` 的 Vite 常用 51xx 端口和预览 41xx 端口，避免 Vite 自动换端口时被浏览器拦截。
3. 前端 `getDefaultApiBaseUrl` 改为本地开发时跟随页面 hostname：从 `localhost` 打开时请求 `localhost:8000`，从 `127.0.0.1` 打开时请求 `127.0.0.1:8000`；仍保留 `VITE_API_BASE_URL` 显式覆盖能力。
4. 前端 API Client 将 fetch 网络层失败转为 `NETWORK_ERROR`，并在错误详情中保留请求 URL 和原始 cause，避免继续显示泛化 `CLIENT_ERROR`。
5. `RequestStateMessage` 临时增强错误诊断展示，显示当前页面、请求地址和底层原因，用于辅助本地联调定位。
6. 最终根因确认不是后端、CORS 或 SQLite，而是 `FetchApiTransport` 默认保存浏览器原生 `fetch` 后再调用时丢失 `Window/globalThis` 绑定；已将默认 fetcher 改为 `globalThis.fetch.bind(globalThis)`，并新增回归测试覆盖。

### 验证结果

1. `GET http://127.0.0.1:8000/health`：返回 200。
2. 携带 `Access-Control-Request-Private-Network: true` 的 `OPTIONS /tasks`：返回 200，并带 `Access-Control-Allow-Private-Network: true`。
3. 使用前端同款 `TaskCreateRequest` payload 调用 `POST http://127.0.0.1:8000/tasks`：返回 201，成功创建任务。
4. `backend\.conda312\python.exe -m pytest backend\tests\test_cors.py backend\tests\test_tasks_api.py backend\tests\test_api_response.py -p no:cacheprovider`：通过，16 个测试通过。
5. `backend\.conda312\python.exe -m ruff check backend --no-cache`：通过。
6. `npm --prefix frontend run test -- --pool=threads api/client.test.ts`：通过，7 个测试通过。
7. `npm --prefix frontend run lint`：通过。
8. `npm --prefix frontend run test`：通过，6 个测试文件、33 个测试通过。
9. `npm --prefix frontend run build`：通过。
10. `npm --prefix frontend run format:check`：通过。

### 下一步边界：等待用户验证后再进入步骤 30

在用户明确验证第 29 步测试通过前，不开始实施计划步骤 30。

步骤 30 边界提醒：

1. 下一步才实现产品画像页。
2. 下一步才调用 `GET /tasks/{task_id}/profile`。
3. 下一步才展示 FeatureTree、PricingModel、UserPersona 和 Evidence 摘要。
4. 继续禁止自由编辑整份报告或绕过 Human Feedback API。

## 2026-05-27：步骤 30 前端产品画像页完成

### 当前完成情况

实施计划中的步骤 30 已完成；按用户要求，在用户验证本步测试前，不开始步骤 31。

已完成实现：

1. `/profile?task_id=<task_id>` 现在会读取 URL 中的任务 ID，并通过统一 `ApiClient.get("/tasks/{task_id}/profile")` 获取产品画像数据。
2. 产品画像页已渲染基础信息、FeatureTree、PricingModel、UserPersona 和 Evidence 摘要五个模块。
3. 基础信息展示品牌、店铺、商品链接、价格区间、产品标签和风险标记。
4. FeatureTree 展示清洁能力、除臭能力、安全能力和维护体验，缺失列表显示“暂无可靠数据”。
5. PricingModel 展示价格带、价格区间、促销、套装说明和价格证据状态；缺少价格访问时间时展示“价格证据：暂无可靠数据”和风险标记。
6. UserPersona 展示目标人群、痛点、使用场景和决策因素；推断内容保留推断提示。
7. Evidence 摘要展示证据 ID、来源、摘要、访问时间状态和风险标记，缺失访问时间时保守显示“暂无可靠数据”。
8. 新增有限 Human Review 面板，只允许修正产品画像结构化 allowlist 字段，并通过 `POST /tasks/{task_id}/feedback` 提交 `HumanFeedbackCreateRequest`。
9. Human Review 不暴露“整份报告”或“Claim 正文”等自由编辑入口；提交成功后页面显示已标记 Analysis 局部重算。
10. 页面顶部状态标记对 `/profile` 显示“画像数据就绪”，避免仍显示占位态。
11. 更新 `frontend/src/App.css`，补齐产品画像双栏布局、画像卡片、Evidence 列表、风险标记、有限 Human Review 面板和移动端响应式样式。
12. 更新 `frontend/src/App.test.tsx`，新增第 30 步画像页组件与反馈提交测试。

### 验证结果

1. `npm --prefix frontend run test`：通过，6 个测试文件、38 个测试通过。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format:check`：通过。

补充说明：

1. 曾执行 `npm run test -- src/App.test.tsx` 定向测试；该命令在本机偶发把测试文件解析为 `/src/App.test.tsx` 并报 `Cannot find module '/src/App.test.tsx'`，0 个测试实际运行。随后使用项目标准命令 `npm --prefix frontend run test` 全量通过，已覆盖 `App.test.tsx` 中的 20 个测试。

新增测试覆盖：

1. 五个产品画像模块均可从 Profile API 数据渲染。
2. 缺失价格访问时间时显示风险状态和“暂无可靠数据”。
3. Human Review 表单只暴露允许的产品画像字段，不暴露整份报告或 Claim 正文。
4. 提交 Human Review 后调用 Feedback API，并在页面显示提交成功状态。

### 本步边界

1. 步骤 30 只实现前端产品画像页，不实现竞争图谱页。
2. 尚未开始步骤 31，未使用 React Flow 渲染竞争关系图。
3. 尚未实现价格带、人群、使用场景切片拨盘。
4. 尚未调用 `GET /tasks/{task_id}/battlefield`。
5. Human Review 仍通过后端反馈 API 保存和标记待局部重算，不允许自由编辑整份报告。

## 2026-05-27：步骤 31 前端竞争图谱页完成

### 当前完成情况

实施计划中的步骤 31 已完成；按用户要求，在用户验证本步测试前，不开始步骤 32。

已完成实现：

1. 新增前端运行时依赖 `@xyflow/react`，用于渲染竞争关系图，符合 `memory-bank/tech-stack.md` 推荐栈。
2. `/battlefield?task_id=<task_id>` 现在会读取 URL 中的任务 ID，并通过统一 `ApiClient.get("/tasks/{task_id}/battlefield", { query })` 获取竞争图谱数据。
3. 竞争图谱页使用 TanStack Query 管理服务端状态，并把 `price_band`、`persona`、`scenario` 作为 query key 和后端 query 参数。
4. 切片拨盘已支持价格带、人群和使用场景切换；切换后会重置当前选中边，并重新请求 Battlefield API。
5. 切片刷新时使用 `placeholderData: previousData => previousData` 保留上一帧图谱，避免 refetch 期间图谱闪空。
6. React Flow 图展示目标产品、直接竞品、渠道替代和需求替代节点，并用边标签展示竞争分数。
7. 右侧详情面板展示选中竞争边的评分解释、五维评分拆解、Claim 与 Evidence 绑定关系、证据卡片和 QA 打回摘要。
8. 决策链面板展示各决策阶段的平均竞争分、关联边、Claim 和 Evidence。
9. 页面顶部状态标记对 `/battlefield` 显示“图谱数据就绪”，避免竞争图谱页仍呈现占位态。
10. 更新 `frontend/src/App.css`，补齐竞争图谱双栏布局、切片控件、React Flow 容器、评分条、证据卡片、QA 摘要和窄屏响应式样式。
11. 更新 `frontend/src/App.test.tsx`，新增 ResizeObserver mock，覆盖 jsdom 环境下 React Flow 组件渲染。

### 验证结果

1. `npm --prefix frontend run test`：通过，6 个测试文件、41 个测试通过。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format:check`：通过。

补充说明：

1. 曾误执行一次 `npm --prefix frontend exec prettier -- src/App.tsx src/App.test.tsx --write`，因路径相对 `frontend/` 解析失败；随后使用 `frontend/src/...` 路径纠正并完成格式化。

新增测试覆盖：

1. 竞争关系图可以从 Battlefield API 数据渲染节点和边。
2. 切换价格带会更新选中切片文案。
3. 切片变化后会重新请求 `GET /tasks/{task_id}/battlefield`，并携带对应 query 参数。
4. 竞争边详情包含评分解释、五维评分拆解、Claim 与 Evidence 绑定和证据卡片。
5. QA 打回记录摘要可在竞争图谱页展示。
6. Playwright 视觉验证确认桌面宽度下竞争关系图和右侧详情面板不重叠，并生成截图运行产物。

### 本步边界

1. 步骤 31 只实现前端竞争图谱页，不实现报告页。
2. 尚未开始步骤 32，未调用 `GET /tasks/{task_id}/report` 或 Markdown 导出接口。
3. 尚未实现报告九章节渲染、报告等待态或导出按钮。
4. 尚未实现 Trace API 真实 DAG 渲染；过程追踪页仍留给步骤 33。
5. 未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

### 下一步边界：等待用户验证后再进入步骤 32

在用户明确验证第 31 步测试通过前，不开始实施计划步骤 32。

步骤 32 边界提醒：

1. 下一步才实现报告页。
2. 下一步才调用 `GET /tasks/{task_id}/report`。
3. 下一步才展示执行摘要、产品画像、竞品发现、动态切片、用户研究、建议、QA 摘要和 Evidence 索引。
4. 下一步才提供 Markdown 导出按钮并调用 `GET /tasks/{task_id}/report/markdown`。

## 2026-05-28：Playwright 工具链补齐

### 当前完成情况

按用户确认，前端已补齐 Playwright 依赖，用于后续视觉截图、端到端演示路径和实施计划步骤 39 的验证。该补齐只调整测试工具链，不开始步骤 32 的报告页实现。

已完成内容：

1. 新增前端开发依赖 `@playwright/test@1.60.0`。
2. 更新 `frontend/package.json` 和 `frontend/package-lock.json`。
3. 安装 Playwright Chromium 浏览器二进制、headless shell、FFmpeg 和 Winldd 到本机 Playwright 缓存目录。

### 验证结果

1. `npm --prefix frontend exec playwright -- --version`：通过，输出 `Version 1.60.0`。
2. `npm --prefix frontend exec playwright -- install chromium`：通过，Chromium 已安装。
3. Playwright headless Chromium 最小启动检查通过，可打开 `frontend/dist/index.html` 并读取页面标题“竞析智能体”。
4. `npm --prefix frontend run test`：通过，6 个测试文件、41 个测试通过。
5. `npm --prefix frontend run lint`：通过。
6. `npm --prefix frontend run build`：通过。
7. `npm --prefix frontend run format:check`：通过。

### 补充说明

1. 安装依赖时出现 `@redocly/openapi-core` 对 npm `>=9.5.0` 的 engine warning；当前 Node.js `v20.20.2` 满足要求，npm 为 `9.4.2`，现有测试、lint、build 均通过。
2. 初次安装 Chromium 因默认写入 `C:\Users\15298\AppData\Local\ms-playwright` 被沙箱拦截；经用户授权后已提权安装成功。
3. 并行运行前端测试时曾触发一次已知 Vitest Windows 路径解析抖动，测试文件被解析为 `/src/...`；随后单独重跑标准命令 `npm --prefix frontend run test` 通过。
4. 本次安装时尚未编写新的 Playwright E2E 用例；第 31 步视觉补测已在下一节补齐，完整演示路径仍留给后续相应步骤。

## 2026-05-28：步骤 31 Playwright 视觉验证补齐

### 当前完成情况

在安装 Playwright 后，已补齐实施计划步骤 31 的视觉验证项。该补充只验证竞争图谱页桌面布局，不开始步骤 32 的报告页。

已完成内容：

1. 新增 `frontend/playwright.config.ts`，配置 Chromium 项目、测试产物目录和基础运行参数。
2. 新增 `frontend/e2e/battlefield.visual.spec.ts`，只覆盖 `/battlefield?task_id=task_battlefield_visual`。
3. E2E 用例通过 `page.route` 拦截 Battlefield API，使用本地结构化测试数据，不依赖真实后端任务或外部网络。
4. 用例启动 Vite preview，验证竞争关系图区域、React Flow 节点/边、右侧详情面板均可见。
5. 用例通过元素 bounding box 检查桌面宽度下竞争关系图和右侧详情面板没有水平重叠，并保存 `battlefield-desktop.png` 截图到 Playwright 测试产物目录。
6. `npm --prefix frontend run test:e2e` 已作为前端 E2E 入口加入 `package.json`。
7. `.gitignore`、`frontend/.prettierignore` 和 `frontend/eslint.config.js` 已忽略 Playwright 运行产物 `frontend/test-results/` 与 `frontend/playwright-report/`。
8. `frontend/vite.config.ts` 已排除 `e2e/**`，避免 Vitest 把 Playwright 测试当作单元测试执行。

### 验证结果

1. `npm --prefix frontend run test`：通过，6 个测试文件、41 个测试通过。
2. `npm --prefix frontend run test:e2e -- e2e/battlefield.visual.spec.ts`：通过，1 个 Playwright 用例通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run build`：通过。
5. `npm --prefix frontend run format:check`：通过。

### 边界

1. 本次只补第 31 步竞争图谱页视觉验证，不实现报告页。
2. 尚未调用 `GET /tasks/{task_id}/report` 或 Markdown 导出接口。
3. 第 39 步完整 Playwright 演示路径仍未开始。

## 2026-05-28：步骤 32 前端报告页完成

### 当前完成情况

实施计划中的步骤 32 已完成；按用户要求，在用户验证本步测试前，不开始步骤 33。

已完成实现：

1. `/report?task_id=<task_id>` 现在会读取 URL 中的任务 ID，并通过统一 `ApiClient.get("/tasks/{task_id}/report")` 获取网页报告数据。
2. 报告页按固定顺序展示九个章节：执行摘要、目标产品画像、竞品发现、动态竞争切片、决策链竞争分析、用户研究洞察、可执行建议、QA 审查摘要和 Evidence 索引。
3. 每个报告章节展示章节摘要、结构化条目、Claim 索引、Evidence 索引和风险标记；复杂嵌套字段会以结构化列表展示，缺失值统一显示“暂无可靠数据”。
4. 报告页展示 Report ID、生成时间和章节数量，保持网页报告可阅读、可汇报。
5. 当 `GET /tasks/{task_id}/report` 返回 `REPORT_NOT_READY` 时，页面显示“报告尚未生成”的等待态和当前任务状态，不渲染最终报告内容。
6. 页面提供“导出 Markdown”按钮，点击后调用 `GET /tasks/{task_id}/report/markdown`。
7. Markdown 导出成功时展示后端返回的 `file_path`；导出失败时显示错误信息，但不隐藏已加载的网页报告。
8. 报告章节渲染保持九章固定顺序；如果后端局部缺少某章，前端在对应位置显示占位章节，不改变后续章节顺序。
9. 更新 `frontend/src/App.css`，补齐报告页布局、报告工具栏、章节网格、结构化条目、引用区、等待态和窄屏响应式样式。
10. 更新 `frontend/src/App.test.tsx`，新增第 32 步报告页组件与 Markdown 导出测试。

### 验证结果

1. `npm --prefix frontend run test`：通过，6 个测试文件、45 个测试通过。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format:check`：通过。

新增测试覆盖：

1. 报告页可以从 Report API 数据渲染全部九个报告章节。
2. 报告未完成并返回 `REPORT_NOT_READY` 时只显示等待态，不展示最终报告章节。
3. 点击“导出 Markdown”会调用 `/tasks/{task_id}/report/markdown`。
4. Markdown 导出失败会显示错误提示，同时保留网页报告内容。

### 本步边界

1. 步骤 32 只实现前端报告页、报告等待态和 Markdown 导出入口。
2. 尚未开始步骤 33，未调用 `GET /tasks/{task_id}/trace` 渲染真实 Trace 数据。
3. 尚未使用 React Flow 展示 LangGraph DAG 状态。
4. 尚未在过程追踪页展示真实 Agent Run、Tool Call、Token Usage、QA Review 或 Diff View。
5. 未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

### 下一步边界：等待用户验证后再进入步骤 33

在用户明确验证第 32 步测试通过前，不开始实施计划步骤 33。

步骤 33 边界提醒：

1. 下一步才在过程追踪页调用 `GET /tasks/{task_id}/trace`。
2. 下一步才使用 React Flow 渲染 LangGraph DAG 状态。
3. 下一步才展示真实 Agent Run、Tool Call、Token Usage、QA Review 和 Diff View。
4. 下一步必须继续保证 Prompt 信息默认折叠展示并经过脱敏处理。

## 2026-05-28：步骤 33 前端过程追踪页完成

### 当前完成情况

实施计划中的步骤 33 已完成；按用户要求，在用户验证本步测试前，不开始步骤 34。

已完成实现：

1. `/trace?task_id=<task_id>` 在保留第 29 步任务状态轮询的基础上，新增通过统一 `ApiClient.get("/tasks/{task_id}/trace")` 获取真实 Trace 数据。
2. Trace 查询使用 TanStack Query 管理服务端状态；当任务仍处于 `created`、`collecting`、`analyzing`、`reviewing` 或 `writing` 时，Trace 与任务状态同步轮询，任务终态后停止轮询。
3. 过程追踪页使用 React Flow 渲染后端 `dag_nodes` 和 `dag_edges`，展示 LangGraph DAG 节点状态、当前节点、失败节点和 QA 打回边。
4. 页面展示真实 `AgentRunLog`、`ToolCallLog` 和 `TokenUsageLog`，覆盖 Collection、Analysis、QA、Writer 四类 Agent 的运行摘要、工具调用和 token 统计。
5. 页面展示 `ReviewTask`、`revision_messages` 与 `diffs`，能看到 QA 打回记录和 Collection 修复前后的 Evidence 差异。
6. 页面展示 `prompt_previews`，Prompt 预览默认使用 `<details>` 折叠，并在前端继续对 API Key、token、secret、password、authorization 等敏感片段做二次脱敏。
7. 更新 `frontend/src/App.css`，补齐 Trace 概览、DAG 双栏布局、运行记录列表、Diff 双列对比、Prompt 折叠块和窄屏响应式样式。
8. 新增 `frontend/e2e/trace.visual.spec.ts`，只覆盖过程追踪页桌面视觉 smoke，不推进第 34 步端到端任务流。
9. 更新 `frontend/src/App.test.tsx`，新增第 33 步真实 Trace 数据渲染、QA 打回/Diff 展示、Prompt 折叠与脱敏测试。

### 验证结果

1. `npm --prefix frontend run test`：通过，6 个测试文件、48 个测试通过。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format:check`：通过。
5. `npm --prefix frontend run test:e2e -- e2e/trace.visual.spec.ts`：通过，1 个 Chromium 用例通过。

新增测试覆盖：

1. 过程追踪页会调用 `/tasks/{task_id}/trace` 并渲染 LangGraph DAG 区域。
2. Agent Run 列表展示 Collection、Analysis、QA 和 Writer。
3. Tool Call 与 Token Usage 列表可见，并展示 token 总量。
4. QA Review、打回消息和 Diff View 可见，能展示打回前后的 Evidence 差异。
5. Prompt 预览默认折叠，且敏感凭据样式文本不会明文出现在页面中。
6. Playwright 视觉 smoke 确认桌面宽度下 Trace DAG、右侧摘要、QA/Diff/Prompt 长内容不遮挡主导航和主内容区。

### 本步边界

1. 步骤 33 只实现前端过程追踪页真实 Trace 数据渲染和本页视觉验证。
2. 未开始步骤 34，未把输入页创建任务、后端后台 LangGraph 启动、前端轮询和最终页面跳转串成完整端到端任务流。
3. 未改变后端 Trace API 契约，未引入新的基础设施。
4. 未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

### 下一步边界：等待用户验证后再进入步骤 34

在用户明确验证第 33 步测试通过前，不开始实施计划步骤 34。

步骤 34 边界提醒：

1. 下一步才处理从输入页创建任务到后端启动 LangGraph 流程的端到端闭环。
2. 下一步才验证前端轮询任务状态和 Trace 后，在任务完成后展示产品画像、竞争图谱和报告。
3. 下一步仍不得依赖真实外部采集，必须继续使用本地快照兜底。

## 2026-05-28：步骤 34 前后端端到端任务流完成

### 当前完成情况

实施计划中的步骤 34 已完成；按用户要求，在用户验证本步测试前，不开始步骤 35。

已完成实现：

1. 新增后端 `TaskExecutionService`，负责从任务表读取任务、构造 `TaskGraphState`、调用真实 LangGraph `build_analysis_workflow()`，并在执行完成后缓存 Trace、产品画像、竞争图谱和网页报告 Artifact。
2. `POST /tasks` 在运行时应用中会自动启动任务执行；默认使用 FastAPI `BackgroundTasks`，测试可通过 `create_app(auto_start_task_execution=True, run_task_execution_inline=True)` 使用同步执行入口。
3. 后端任务执行继续使用本地快照和规则流程；未配置模型 API Key 时仍可完成 Collection、Analysis、QA、Writer 全流程，不做真实外部采集。
4. 前端 Trace 页在任务完成后显示结果入口，可直接进入产品画像、竞争图谱和分析报告。
5. 前端主导航在非输入页之间跳转时保留当前 `task_id`，刷新或跨页面切换不会丢失任务上下文。
6. Trace 页在任务状态进入 `completed` 后会按 `task_id + updated_at` 触发一次 Trace 刷新，避免页面停留在任务早期的空 Trace。
7. 新增真实前后端 Playwright E2E：启动临时 SQLite 后端和 Vite preview，从输入页创建任务，等待 Trace 完成，再验证产品画像、竞争图谱和报告页均可打开并展示真实 API 数据。
8. 新增后端集成测试，验证 `POST /tasks` 同步执行入口会产出完成态任务，以及 Trace、产品画像、竞争图谱和报告缓存 Artifact。
9. 新增前端组件测试，验证完成态 Trace 页结果入口和侧边导航在跳转产品画像、竞争图谱、报告时持续保留 `task_id`。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_tasks_api.py backend\tests\test_task_execution.py backend\tests\test_trace_api.py backend\tests\test_profile_api.py backend\tests\test_battlefield_api.py backend\tests\test_reports_api.py`：通过，31 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
3. `npm --prefix frontend run test -- App.test.tsx`：通过，31 个测试通过。
4. `npm --prefix frontend run lint`：通过。
5. `npm --prefix frontend run build`：通过。
6. `npm --prefix frontend run format:check`：通过。
7. `npm --prefix frontend run test:e2e -- e2e/task-flow.e2e.spec.ts`：通过，1 个 Chromium 用例通过。

### 本步边界

1. 步骤 34 只打通创建任务、后台执行、前端轮询、Trace 和结果页展示的端到端闭环。
2. 未开始步骤 35 的 QA 打回专项验证。
3. 未新增真实外部采集；`snapshot_plus_live` 仍只是增强模式占位。
4. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
5. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

### 下一步边界：等待用户验证后再进入步骤 35

在用户明确验证第 34 步测试通过前，不开始实施计划步骤 35。

步骤 35 边界提醒：

1. 下一步才做 QA 打回专项 E2E。
2. 下一步才专门验证“补齐一条缺失证据”的打回前后差异。
3. 下一步才确认报告中不再出现无证据强结论。

## 2026-05-28：步骤 35 真实 QA 打回演示链路完成

### 当前完成情况

实施计划中的步骤 35 已完成；按用户要求，在用户验证本步测试前，不开始步骤 36。

已完成实现：

1. QA Agent 现在会在后续 QA 轮次中同步 ReviewTask 状态：当旧问题不再被当前规则命中时，将原 `open` ReviewTask 标记为 `resolved` 并写入 `resolved_at`。
2. 真实缺失证据样例继续使用 `sku_01`，首次 QA 会生成 `TIMELY_EVIDENCE_MISSING_ACCESS_TIME`，打回目标为 `collection_agent`。
3. Collection Agent 通过 `qa_revision_fixture.repair_evidence` 补齐 `ev_sku_01` 的访问时间，生成 `ev_sku_01_repair_001`，并记录 `collection_agent_repair` Diff。
4. Workflow 在 Collection 修复后自动追加 Analysis 重算消息，Analysis Agent 重新计算相关 Claim 和 CompetitionEdge，记录 `analysis_agent_recompute` Diff，评分发生变化。
5. 第二次 QA 通过后 Writer Agent 生成最终报告；报告中的竞品发现 Claim 使用修复后的 Evidence，不再把原缺失访问时间证据作为强结论依据。
6. Battlefield QA 摘要在完整链路完成后显示 `passed`、开放 ReviewTask 为 0、已解决 ReviewTask 为 1。
7. 新增真实前后端 Playwright E2E `frontend/e2e/qa-revision.e2e.spec.ts`，从输入页创建任务，验证 Trace 页、竞争图谱页和报告页中的 QA 打回链路。
8. Playwright 配置改为 `workers: 1`，避免多个 E2E 并行构建同一个 `dist/` 目录导致偶发互相影响。
9. 后端集成测试补强了真实 LangGraph 条件边、ReviewTask resolved 状态、Collection 修复 Diff、Analysis 重算 Diff 和报告证据更新。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_qa_agent.py backend\tests\test_collection_agent.py backend\tests\test_analysis_agent.py backend\tests\test_workflow.py backend\tests\test_trace_api.py backend\tests\test_task_execution.py backend\tests\test_battlefield_api.py backend\tests\test_reports_api.py`：通过，39 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
3. `npm --prefix frontend run test -- App.test.tsx`：通过，31 个测试通过。
4. `npm --prefix frontend run lint`：通过。
5. `npm --prefix frontend run build`：通过。
6. `npm --prefix frontend run format:check`：通过。
7. `npm --prefix frontend run test:e2e -- e2e/qa-revision.e2e.spec.ts`：通过，1 个 Chromium 用例通过。
8. `npm --prefix frontend run test:e2e`：通过，4 个 Chromium 用例通过。

### 本步边界

1. 步骤 35 只验证和加固真实 QA 打回演示链路。
2. 未开始步骤 36 的 Human Review 闭环验证。
3. 未改变 HumanFeedback API 或产品画像页人工修正交互。
4. 未新增真实外部采集；`snapshot_plus_live` 仍只是增强模式占位。
5. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
6. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

### 下一步边界：等待用户验证后再进入步骤 36

在用户明确验证第 35 步测试通过前，不开始实施计划步骤 36。

步骤 36 边界提醒：

1. 下一步才验证 Human Review 闭环。
2. 下一步才从产品画像页或竞争图谱页提交允许范围内的人工修正。
3. 下一步才验证反馈保存后相关 Claim 或 CompetitionEdge 状态变化，以及前端刷新相关结果。

## 2026-05-28：步骤 36 Human Review 闭环完成

### 当前完成情况

实施计划中的步骤 36 已完成；按用户要求，在用户验证本步测试前，不开始步骤 37。

已完成实现：

1. `FeedbackService` 在保存 `HumanFeedback` 后，会把允许范围内的人工修正应用到当前工作流状态，并重新缓存 `product_profile`、默认切片 `battlefield_data` 和 `trace_data` Artifact。
2. 产品画像结构化字段更新会直接反映在 `GET /tasks/{task_id}/profile` 返回结果中。
3. Claim 状态反馈会更新相关 Claim 的 `status`，并让竞争图谱中的 `claim_refs` 与 `risk_status` 同步变化。
4. Evidence 备注、CompetitionEdge 移除反馈和 Slice 字段更新会写入局部更新状态；CompetitionEdge 反馈会标记 `human_adjusted` 并降低边分，便于后续图谱识别人工修正。
5. `human_feedback_effect` Artifact 记录 before/after、受影响目标、缓存 Artifact ID 和 `applied_local_update` 状态。
6. profile、battlefield、report、trace 读取服务允许 `human_reviewing` 任务读取既有结果；trace 在人工复核态优先返回缓存 Trace。
7. 产品画像页 Human Review 表单提交成功后会重新拉取产品画像，并显示“相关结果已刷新”。
8. 自由改写报告或 Claim 正文仍被 Feedback API 拒绝，Human Review 仍只允许 allowlist 内结构化字段和受控动作。

### 验证结果

1. `backend\.conda312\python.exe -m pytest tests\test_feedback_api.py`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -m pytest tests\test_feedback_api.py tests\test_profile_api.py tests\test_battlefield_api.py tests\test_trace_api.py tests\test_reports_api.py`：通过，27 个测试通过。
3. `backend\.conda312\python.exe -m ruff check app\services\feedback_service.py app\services\profile_service.py app\services\battlefield_service.py app\services\report_service.py app\services\trace_service.py tests\test_feedback_api.py`：通过。
4. `npm test -- src/App.test.tsx`：通过，31 个测试通过。
5. `npx tsc --noEmit`：通过。
6. `npx vite build --configLoader runner --outDir ../.codex-run/frontend-dist-step36-verify`：通过。

### 验证备注

1. 直接运行 `npm run build` 时，Vite 默认配置加载器尝试写入 `frontend/node_modules/.vite-temp`，随后默认输出目录清理 `frontend/dist` 时又遇到 Windows `EPERM`；这两个失败点都是本地目录权限问题。
2. 使用项目测试同款 `--configLoader runner` 并输出到 `.codex-run/frontend-dist-step36-verify` 后，Vite 构建成功，说明本次前端代码和类型检查通过。

### 本步边界

1. 步骤 36 只验证 Human Review 提交、保存、局部缓存更新和前端刷新闭环。
2. 未开始步骤 37。
3. 未新增真实外部采集；`snapshot_plus_live` 仍只是增强模式占位。
4. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
5. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

### 下一步边界：等待用户验证后再进入步骤 37

在用户明确验证第 36 步测试通过前，不开始实施计划步骤 37。

## 2026-05-29：步骤 37 异常与降级处理完成

### 当前完成情况

实施计划中的步骤 37 已完成；按用户要求，在用户验证本步测试前，不开始步骤 38。

已完成实现：

1. Snapshot Loader 增加快照文件缺失专项测试，确认 `SNAPSHOT_NOT_FOUND` 会返回包含路径的可诊断错误。
2. 新增 `backend/app/services/structured_output.py`，为可选模型增强提供结构化输出解析、最多两次候选重试和兜底结果返回能力；当前不引入真实外部模型调用。
3. LangGraph 工作流的 Collection、Analysis、QA、Writer 节点现在会把单个 Agent 异常转换为 `failed` 工作流状态，并写入失败 Agent Run Log，避免异常静默丢失或绕过 Trace。
4. `TaskExecutionService` 在工作流异常或失败态下会把任务状态更新为 `failed`，并缓存一份可由 `GET /tasks/{task_id}/trace` 查询的失败 Trace。
5. `TraceService` 支持读取失败任务的缓存 Trace；如果失败任务缺少缓存，则返回任务记录级失败骨架 Trace，不重新触发工作流。
6. Markdown 导出失败仍返回 `MARKDOWN_EXPORT_FAILED`，且不会影响已有网页报告；失败信息会写入 Trace metadata 的 `markdown_export_failures` 与 `last_failure`。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_snapshot_loader.py backend\tests\test_structured_output.py backend\tests\test_workflow.py backend\tests\test_task_execution.py backend\tests\test_reports_api.py backend\tests\test_trace_api.py`：通过，29 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\graph\__init__.py backend\app\graph\workflow.py backend\app\services\task_execution.py backend\app\services\trace_service.py backend\app\services\report_service.py backend\app\services\structured_output.py backend\tests\test_snapshot_loader.py backend\tests\test_structured_output.py backend\tests\test_workflow.py backend\tests\test_task_execution.py backend\tests\test_reports_api.py`：通过。
3. `backend\.conda312\python.exe -m pytest backend\tests`：通过，154 个测试通过。
4. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。

### 本步边界

1. 步骤 37 只补齐异常、失败 Trace 与降级处理。
2. 本步骤没有开始步骤 38 的安全与脱敏专项检查。
3. 本步骤没有引入外部采集、模型网络调用、队列、缓存服务或新前端框架。
4. `snapshot_plus_live` 仍只是增强模式占位，不进行真实外部采集。
5. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

### 下一步边界：等待用户验证后再进入步骤 38

在用户明确验证第 37 步测试通过前，不开始实施计划步骤 38。

## 2026-05-29：步骤 38 安全与脱敏专项完成

### 当前完成情况

实施计划中的步骤 38 已完成；按用户要求，在用户验证本步测试前，不开始步骤 39。

已完成实现：

1. 新增 `backend/app/security.py` 作为共享脱敏模块，统一识别 API Key、Bearer、token、密码、环境变量名、手机号、地址和账号 ID。
2. API 错误响应、Trace、Markdown 导出和任务创建服务改用共享脱敏规则，减少各出口规则不一致导致的泄漏风险。
3. `TaskCreationService` 在保存和返回 `research_text` 前进行基础脱敏；如发生脱敏，任务 metadata 记录 `research_text_redacted = true`。
4. `TraceService` 对 Trace JSON 做递归脱敏，并在 Trace 内部字典中改写敏感 key 名，避免出现 `api_key`、完整环境变量名、手机号、地址或账号 ID。
5. Markdown 导出在渲染字段、列表、标题和摘要时先脱敏，随后执行安全扫描；导出的 Markdown 文件不保留密钥、手机号、地址或账号 ID 原文。
6. 前端 Trace 展示的 `sanitizeTraceText()` 同步补齐 Bearer、环境变量名、手机号、地址和账号 ID 脱敏规则，Prompt 预览仍默认折叠。
7. QA 规则扩展宠物安全、电器认证相关绝对化表达，如“安全无忧”“通过所有认证”“认证齐全”等，继续要求改写为保守表述。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_api_response.py backend\tests\test_tasks_api.py backend\tests\test_trace_api.py backend\tests\test_markdown_renderer.py backend\tests\test_qa_rules.py -q`：通过，31 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests -q`：通过，155 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
4. `npx eslint src/App.tsx src/App.test.tsx`：通过。
5. `npx prettier src/App.tsx src/App.test.tsx --check`：通过。
6. `npx vitest run .\src\App.test.tsx -t "keeps prompt previews folded and redacts sensitive trace text" --configLoader runner`：通过，1 个测试通过，30 个测试跳过。

### 本步边界

1. 步骤 38 只做安全扫描、脱敏规则和敏感表达 QA 补强。
2. 未开始步骤 39。
3. 未新增真实外部采集；`snapshot_plus_live` 仍只是增强模式占位。
4. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
5. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

### 下一步边界：等待用户验证后再进入步骤 39

在用户明确验证第 38 步测试通过前，不开始实施计划步骤 39。

## 2026-05-29：步骤 39 E2E Demo 路径验证完成

### 当前完成情况

实施计划中的步骤 39 已完成；本轮随后按用户最新要求继续完成步骤 40。

已完成实现：

1. 新增 `frontend/e2e/demo-path.e2e.spec.ts`，覆盖输入页、Trace 页、产品画像页、竞争图谱页、报告页和 Markdown 导出按钮。
2. Demo 路径 E2E 使用临时 SQLite、临时报告目录、临时前端构建目录、真实 Uvicorn 后端和 Vite preview；通过 `RUN_TASK_EXECUTION_INLINE=1` 保证测试中任务执行可复现。
3. E2E 明确验证 QA 打回记录、Collection 修复 Diff、Analysis 重算 Diff、最终 QA 已通过且已解决 1 条 ReviewTask。
4. E2E 截图覆盖输入页、Trace、产品画像、竞争图谱、报告，以及窄屏 Trace、窄屏图谱、窄屏报告。
5. 竞争图谱截图验证 React Flow 节点和边非空。
6. 窄屏检查验证主导航与主内容不重叠，页面无严重水平溢出。
7. 既有 Playwright 用例改为使用临时前端产物目录和 `configLoader: "runner"`，避免多个 E2E 用例共享或清理 `frontend/dist` 导致 Windows 下不稳定。
8. 前端报告相关样式补齐 `min-width: 0` 与 `overflow-wrap`，解决窄屏报告长文本溢出。

### 验证结果

1. `npm run test:e2e`：通过，5 个 Chromium 用例通过，包含完整 Demo 路径、QA 打回链路、任务流、Trace 视觉和图谱视觉。
2. `npx eslint e2e`：通过。
3. `npx prettier e2e --check`：通过。

### 本步边界

1. 步骤 39 只新增和加固 E2E Demo 验证，不改变业务模型或报告结论。
2. 未引入外部采集；`snapshot_plus_live` 仍只是增强模式占位。
3. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
4. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

## 2026-05-29：步骤 40 Demo 冻结与稳定回归完成

### 当前完成情况

实施计划中的步骤 40 已完成；本轮执行完步骤 40 后结束，不继续推进新的实施计划步骤。

已完成实现：

1. 新增稳定任务输入，冻结答辩与录屏使用的任务参数。
2. 新增冻结说明，记录冻结日期、快照文件、快照 SHA256、默认目标 SKU、QA 打回 SKU 和打回补齐路径。
3. 固定 Demo 快照哈希为 `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`。
4. 固定默认目标为 `sku_02`，固定可复现 QA 打回案例为 `sku_01` 缺失 `source.access_time`。
5. 新增 `backend/tests/test_demo_freeze.py`，验证冻结文件、稳定输入、快照哈希、QA fixture、重复 Demo 输入的稳定结果形状和报告九章节完整性。
6. `backend/app/main.py` 支持运行时环境变量 `RUN_TASK_EXECUTION_INLINE` 和 `REPORT_OUTPUT_DIR`，用于 E2E 与冻结回归的隔离执行；默认运行行为不变。
7. `frontend/package.json` 的 build/test 脚本使用 Vite/Vitest runner 加载器，规避本地 `.vite-temp` 权限问题；Vitest 脚本显式使用 `--root .` 保持 Windows 路径解析稳定。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_demo_freeze.py -q`：通过，3 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests -q`：通过，159 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
4. `npm run test`：通过，6 个测试文件、49 个测试通过。
5. `npm run test:e2e`：通过，5 个 Chromium 用例通过。
6. `npm run lint`：通过。
7. `npm run format:check`：通过。
8. `npx tsc --noEmit`：通过。
9. `npx vite build --configLoader runner --outDir C:\Users\15298\AppData\Local\Temp\zijieagent-frontend-build-step40 --emptyOutDir false`：通过。

### 验证备注

1. 直接运行 `npm run build` 时，Vite 在清理既有 `frontend/dist/assets/index-BcnAjEgV.js` 时遇到 Windows `EPERM`；该文件位于既有构建产物目录，当前沙箱提权构建请求被系统自动拒绝。
2. 因此本步使用不触碰既有 `dist` 的临时输出目录完成生产 Vite 构建验证；TypeScript 检查、Vitest、ESLint、Prettier、后端全测和全量 E2E 均已通过。

### 本步边界

1. 步骤 40 只冻结 Demo 数据、默认输入、QA 打回案例和稳定回归测试。
2. 未新增真实外部采集、模型网络调用、队列、缓存服务或新前端框架。
3. `snapshot_plus_live` 仍只是增强模式占位，不进行真实外部采集。
4. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

## 2026-05-29：v2 步骤 01 建立 2.0 契约清单完成

### 当前完成情况

v2 实施计划步骤 01 已完成。本步只建立 2.0 迁移契约清单，不改动后端业务代码、前端页面代码或 Demo 冻结数据。

已完成实现：

1. 形成 2.0 迁移清单，记录 1.0 基线、2.0 页面责任边界、保留能力、新增能力、废弃能力、API 迁移、前端迁移、后端迁移、测试迁移、非目标范围和后续步骤验证矩阵。
2. 明确 `GET /tasks/{task_id}/report/markdown` 在 2.0 中必须删除，不保留用户可见入口或兼容路由；正式交付替换为 Word `.docx`。
3. 明确 `overview`、`battlefield`、`profile`、`report`、`trace` 在 2.0 中的责任边界，避免前端从旧接口临时拼接总览主数据。
4. 明确非目标能力不得纳入实施范围，包括真实外部实时采集、Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind、后端 PDF 服务、Headless Office、Graphviz、PPT 导出和自由编辑整份报告。
5. 为 v2 步骤 02 到步骤 40 建立验证矩阵，确保后续每一步都有明确验证方式。

### 验证结果

1. 文档检查确认迁移清单覆盖竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪、DOCX、中文化、总览 API 和 Word 导出 API：通过。
2. 文档检查确认存在非目标范围章节和“不得作为新增能力落地”的范围排除说明：通过。
3. 文档检查确认明确删除旧 Markdown 导出 API：通过。
4. 文档检查确认后续步骤 02 到步骤 40 均出现在验证矩阵中：通过。
5. 文档检查确认没有写成继续保留 Markdown 导出正式入口：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 02。
2. 本步骤没有修改后端 Schema、API、Agent、服务层、前端页面或测试代码。
3. 本步骤没有引入新依赖或复杂基础设施。
4. 未写入真实 API Key，未在文档中记录密钥。

## 2026-05-29：v2 步骤 02 后端 2.0 枚举与展示状态 Schema 完成

### 当前完成情况

v2 实施计划步骤 02 已完成。本步只补充后端 2.0 PM 展示枚举和轻量展示状态 Schema，不改变现有 `Claim`、`Evidence`、`CompetitionEdge`、`ReviewTask` 或 Agent 传递协议。

已完成实现：

1. `backend/app/schemas/common.py` 新增 2.0 展示枚举：`JudgmentStrength`、`DecisionUsabilityStatus`、`EvidenceCredibilityStatus`、`ThreatLevel`、`PMRelationshipLabel`、`ActionPriority` 和 `ResponsibilityType`。
2. 新增 `backend/app/schemas/display.py`，定义 `DisplayStatus`，用于统一表达状态值、中文标签、原因说明、Evidence 引用、Trace 引用和风险标记。
3. 更新 `backend/app/schemas/__init__.py`，统一导出新增枚举和 `DisplayStatus`，确保后续服务、API 和 OpenAPI 可以复用。
4. 新增 `backend/tests/test_v2_display_schemas.py`，覆盖新增枚举允许值、展示状态合法/非法值和 OpenAPI 导出。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_v2_display_schemas.py backend\tests\test_core_schemas.py -q`：通过，47 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\common.py backend\app\schemas\display.py backend\app\schemas\__init__.py backend\tests\test_v2_display_schemas.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 03。
2. 本步骤没有修改 Product 主图字段、Snapshot Loader、API 路由、Agent 节点、服务层或前端页面。
3. 本步骤没有新增依赖或复杂基础设施。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 03 Product 主图路径推导完成

### 当前完成情况

v2 实施计划步骤 03 已完成。本步只扩展 Product 主图字段、Snapshot Loader 主图推导和本地 raw 截图静态访问，不改动冻结快照 JSON、Agent 分析逻辑或前端页面。

已完成实现：

1. `backend/app/schemas/common.py` 新增 `ProductImageStatus`，支持 `available` 与 `missing` 两种主图状态。
2. `backend/app/schemas/product.py` 为 `Product` 增加 `primary_image_path`、`primary_image_url`、`primary_image_source_path` 和 `primary_image_status`。
3. `backend/app/services/snapshot_loader.py` 从快照图片字段、本地 `source.screenshot_path` 和 `source.raw_dir` 依次推导主图，输出浏览器可访问的 `/assets/raw/...` URL；找不到可靠图片时明确标记为 `missing`。
4. `backend/app/main.py` 将 `data/raw` 以只读静态资源方式挂载到 `/assets/raw`，避免向前端暴露本机绝对路径或完整快照目录。
5. 更新 `backend/tests/test_snapshot_loader.py` 和 `backend/tests/test_core_schemas.py`，覆盖主图 URL 推导、缺失状态、静态文件可访问性、Schema 枚举校验和 OpenAPI 导出。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_snapshot_loader.py backend\tests\test_core_schemas.py backend\tests\test_demo_freeze.py -q`：通过，52 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\main.py backend\app\schemas\common.py backend\app\schemas\product.py backend\app\schemas\__init__.py backend\app\services\snapshot_loader.py backend\tests\test_snapshot_loader.py backend\tests\test_core_schemas.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 04。
2. 本步骤没有修改 Demo 快照文件，因此冻结快照 SHA256、默认目标 `sku_02` 和 QA fixture 仍由 `test_demo_freeze.py` 锁定。
3. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 04 分析范围汇总服务完成

### 当前完成情况

v2 实施计划步骤 04 已完成。本步只新增分析范围汇总 Schema 与服务，不新增 API、不修改 Agent DAG、不改变报告生成逻辑。

已完成实现：

1. 新增 `backend/app/schemas/overview.py`，定义 `AnalysisScopeSummary`，用于承载任务品类、子类、数据源说明、SKU 数、Product 数、Evidence 数、平台、来源说明、快照版本、快照日期、访问时间范围、缺失字段和 Evidence 引用。
2. 更新 `backend/app/schemas/__init__.py`，导出 `AnalysisScopeSummary`。
3. 新增 `backend/app/services/analysis_scope_service.py`，实现 `build_analysis_scope_summary`，基于 `AnalysisTask`、`Product`、`Evidence` 和快照版本汇总分析范围。
4. 服务固定输出“本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。”，并在访问时间不完整时输出“暂无可靠数据”。
5. 服务只读取 Evidence metadata 中的平台和来源说明，不向输出透传 `raw_dir`、本机绝对路径或密钥类字段。
6. 新增 `backend/tests/test_analysis_scope_service.py`，覆盖冻结 Demo SKU 数、来源说明、访问时间缺失状态和安全输出边界。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_analysis_scope_service.py backend\tests\test_snapshot_loader.py backend\tests\test_core_schemas.py -q`：通过，52 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\overview.py backend\app\schemas\__init__.py backend\app\services\analysis_scope_service.py backend\tests\test_analysis_scope_service.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 05。
2. 本步骤没有新增 OverviewData、Overview API、前端页面或导航改造。
3. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 05 总览数据结构完成

### 当前完成情况

v2 实施计划步骤 05 已完成。本步只定义总览页后端 Schema 契约，不实现总览服务、不新增 API、不修改前端。

已完成实现：

1. 在 `backend/app/schemas/overview.py` 中新增 `OverviewData` 及子结构：`OverviewConclusion`、`OverviewKeyCompetitor`、`OverviewFinding`、`OverviewActionRecommendation`、`OverviewDrilldownReference` 和相关类型枚举。
2. `OverviewData` 覆盖一句话判断、判断强度、决策可用状态、状态原因、分析范围、关键竞品、机会点、风险点、行动建议、当前切片和下钻引用。
3. 判断强度强制使用 `JudgmentStrength`，决策可用状态强制使用 `DecisionUsabilityStatus`，关键竞品证据可信状态强制使用 `EvidenceCredibilityStatus`。
4. 行动建议必须包含 `ActionPriority` 和 `ResponsibilityType`。
5. 机会点最多 3 条、风险点最多 3 条、行动建议最多 5 条。
6. 每个关键结论类结构缺少 Evidence 或 Trace 引用时，会自动标记 `missing_evidence` 风险并写入缺失原因；空内容等完全不可展示数据会校验失败。
7. 更新 `backend/app/schemas/__init__.py`，统一导出 Overview 相关 Schema。
8. 新增 `backend/tests/test_v2_overview_schemas.py`，覆盖合法样例、行动建议必填字段、缺引用风险标记、不可展示数据拒绝和 OpenAPI 导出。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_v2_overview_schemas.py backend\tests\test_v2_display_schemas.py backend\tests\test_core_schemas.py -q`：通过，55 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\overview.py backend\app\schemas\__init__.py backend\tests\test_v2_overview_schemas.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 06。
2. 本步骤没有实现 Overview 服务、API 路由、缓存产物或前端页面。
3. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 06 总览服务完成

### 当前完成情况

v2 实施计划步骤 06 已完成。本步实现后端总览服务，不新增 API、不修改前端。

已完成实现：

1. 新增 `backend/app/services/overview_service.py`，提供 `OverviewService`、`OverviewServiceError`、`OVERVIEW_ARTIFACT_TYPE` 和 `_build_overview_data`。
2. 总览服务基于 LangGraph Workflow 产物中的 `Product`、`Evidence`、`Claim`、`CompetitionEdge`、`ReviewTask` 和 Agent Message 生成 PM 可读 `OverviewData`，不要求前端从 Profile、Battlefield、Report 拼接。
3. 一句话判断采用“先给结论，再补证据风险状态”的中文文案。
4. 决策可用状态根据判断强度、关键竞品证据可信状态、未解决 QA 风险共同决定；存在未解决高严重度 QA 风险时不会返回“可用于初步决策”。
5. 关键竞品按当前切片过滤和排序，并默认选择最高威胁直接竞品、最高威胁替代竞品、需复核高分竞品；不存在的类别不硬补。
6. 总览服务按 2.0 状态与分数标准输出判断强度、证据可信状态、决策可用状态、威胁等级、优先级和责任类型。
7. 机会点、风险点和行动建议会随切片变化引用不同竞品与证据。
8. 更新 `backend/app/services/__init__.py`，导出 Overview 服务相关对象。
9. 新增 `backend/tests/test_overview_service.py`，覆盖冻结 Demo 总览生成、未解决 QA 风险、切片变化和主文案字段名安全。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_overview_service.py backend\tests\test_v2_overview_schemas.py backend\tests\test_demo_freeze.py -q`：通过，13 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\services\overview_service.py backend\app\services\__init__.py backend\tests\test_overview_service.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 07。
2. 本步骤没有新增 `GET /tasks/{task_id}/overview` API 或前端页面。
3. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 07 总览 API 完成

### 当前完成情况

v2 实施计划步骤 07 已完成。本步新增总览 HTTP API，不修改前端页面。

已完成实现：

1. 新增 `backend/app/api/routes_overview.py`，实现 `GET /tasks/{task_id}/overview`。
2. 接口支持 `price_band`、`persona`、`scenario` 查询参数，并透传给 `OverviewService`。
3. 接口只在任务状态为 `completed` 或 `human_reviewing` 时返回 `OverviewData`；未完成任务返回标准 `OVERVIEW_NOT_READY`。
4. 不存在任务返回标准 `TASK_NOT_FOUND`。
5. 接口统一使用现有 `ApiResponse` 响应外壳和 Trace ID。
6. 更新 `backend/app/main.py`，挂载 Overview 路由。
7. 新增 `backend/tests/test_overview_api.py`，覆盖完成任务获取总览、切片参数传递、未完成任务错误和不存在任务错误。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_overview_api.py backend\tests\test_overview_service.py backend\tests\test_tasks_api.py -q`：通过，18 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\api\routes_overview.py backend\app\main.py backend\tests\test_overview_api.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 08。
2. 本步骤没有修改竞争图谱接口、报告接口、前端页面或导航。
3. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 08 竞争图谱后端契约升级完成

### 当前完成情况

v2 实施计划步骤 08 已完成。本步只扩展竞争图谱后端返回契约，不做关键关系数量筛选。

已完成实现：

1. `backend/app/schemas/battlefield.py` 新增 `BattlefieldKeyRelation` 和 `BattlefieldFourPartExplanation`。
2. `BattlefieldData` 新增 `key_relations`，同时保留原有 `graph_nodes`、`graph_edges`、`score_explanations`、`decision_chain`、`evidence_cards` 和 `qa_summary`。
3. `BattlefieldGraphNode` 新增 `primary_image_path`，用于前端展示产品图片。
4. `BattlefieldKeyRelation` 包含入选理由、威胁等级、PM 关系标签、标签解释、四段式解释、应对建议、证据可信状态、产品图片路径、Evidence/Claim/Trace 引用和风险标记。
5. `backend/app/services/battlefield_service.py` 生成 `key_relations`，并为每条关系补充证据可信状态、威胁等级、关系标签、四段式解释和应对建议。
6. 更新 `backend/app/schemas/__init__.py`，导出新增 Battlefield Schema。
7. 新增 `backend/tests/test_v2_battlefield_schemas.py`，验证扩展后的 `BattlefieldData` 兼容旧字段。
8. 更新 `backend/tests/test_battlefield_api.py`，验证 API 关键关系包含入选理由、威胁等级和四段式解释。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_v2_battlefield_schemas.py backend\tests\test_battlefield_api.py backend\tests\test_overview_service.py -q`：通过，12 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\battlefield.py backend\app\schemas\__init__.py backend\app\services\battlefield_service.py backend\tests\test_v2_battlefield_schemas.py backend\tests\test_battlefield_api.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 09。
2. 本步骤没有限制默认关键关系数量到 3 到 5 条，筛选策略留给步骤 09。
3. 本步骤没有修改前端页面、导航或报告导出。
4. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
5. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 09 关键竞争关系筛选完成

### 当前完成情况

v2 实施计划步骤 09 已完成。本步在后端完成默认关键竞争关系筛选，并支持展开全部关系。

已完成实现：

1. `BattlefieldData` 新增 `relation_filter`，记录是否展开全部、默认限制、候选总数、当前可见数和是否可展开。
2. `BattlefieldKeyRelation` 新增 `is_default_visible`，用于展开全部时标记哪些关系属于默认展示集合。
3. `BattlefieldService.get_battlefield` 和 `GET /tasks/{task_id}/battlefield` 新增 `include_all_relations` 参数。
4. 默认关键关系筛选覆盖最高威胁直接竞品、最高威胁替代/渠道替代竞品、需复核高分竞品和对策略动作最有启发的竞品。
5. 默认展示关系数量控制在 3 到 5 条，除非当前切片候选关系本身不足。
6. `include_all_relations=true` 时返回当前切片下完整关键关系集合，同时保留默认可见标记。
7. 高分但证据不足的关系会标记为 `high_score_needs_review`，不会直接标为 `high_threat`。
8. 更新 `backend/tests/test_battlefield_api.py`，覆盖默认数量、展开全部、高分需复核和切片过滤回归。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_battlefield_api.py backend\tests\test_v2_battlefield_schemas.py backend\tests\test_overview_service.py backend\tests\test_task_execution.py -q`：通过，17 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\battlefield.py backend\app\schemas\__init__.py backend\app\services\battlefield_service.py backend\app\api\routes_battlefield.py backend\tests\test_battlefield_api.py backend\tests\test_v2_battlefield_schemas.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 10。
2. 本步骤没有进一步细化 PM 关系标签与威胁等级规则，细化留给步骤 10。
3. 本步骤没有修改前端页面、导航或报告导出。
4. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
5. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 10 PM 关系标签与威胁等级规则完成

### 当前完成情况

v2 实施计划步骤 10 已完成。本步细化后端 PM 关系标签和威胁等级规则。

已完成实现：

1. `battlefield_service` 的 PM 关系标签不再只按底层 `competition_type` 简单映射。
2. 正面硬碰：同类直接竞争且不存在低价、内容种草或信任压制优先信号。
3. 低价截流：渠道替代，或竞品到手价显著低于目标产品。
4. 场景替代：非同类替代关系，用于解决同一使用场景问题。
5. 信任压制：竞品证据或产品信息出现安全、认证、防夹、口碑、评价、售后、信任、质保等信任信号。
6. 内容种草竞争：底层关系为内容共现/种草竞争。
7. 每个 PM 关系标签均有非空中文解释。
8. 威胁等级继续同时考虑竞争分与证据可信状态；证据不足时高分边标记为 `high_score_needs_review`，不会直接标为 `high_threat`。
9. 新增 `backend/tests/test_battlefield_relationship_rules.py`，覆盖五类 PM 标签、低可信高分降级和标签解释。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_battlefield_relationship_rules.py backend\tests\test_battlefield_api.py backend\tests\test_overview_service.py -q`：通过，25 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\services\battlefield_service.py backend\tests\test_battlefield_relationship_rules.py backend\tests\test_battlefield_api.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 11。
2. 本步骤没有重写四段式解释字段结构，四段式进一步强化留给步骤 11。
3. 本步骤没有修改前端页面、导航或报告导出。
4. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
5. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 11 竞争边四段式解释完成

### 当前完成情况

v2 实施计划步骤 11 已完成。本步强化关键竞争边解释结构。

已完成实现：

1. `BattlefieldFourPartExplanation` 从四个字符串升级为四个带引用的段落对象：`why_competitor`、`strength`、`decision_stage_impact`、`response_suggestion`。
2. 新增 `BattlefieldExplanationSegment`，每段携带正文、Claim 引用、Evidence 引用、Trace 引用、风险标记和是否为分析建议。
3. 缺少 Claim 与 Evidence 引用的解释段会自动标记 `missing_evidence` 风险。
4. `response_suggestion` 必须显式标记 `is_analysis_suggestion=true`，否则 Schema 校验失败。
5. `battlefield_service` 为每条关键关系生成“为什么它是竞品”“它强在哪里”“它会在哪个决策阶段抢走用户”“我们该怎么应对”四段解释。
6. 四段解释均绑定对应 Claim、Evidence 和 Analysis Trace 引用。
7. 更新 `backend/tests/test_battlefield_api.py`，验证 API 中每条关键关系四段解释均有可追溯引用。
8. 新增 `backend/tests/test_battlefield_explanations.py`，验证无引用解释风险标记和应对建议分析建议标记。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_battlefield_explanations.py backend\tests\test_battlefield_api.py backend\tests\test_v2_battlefield_schemas.py -q`：通过，12 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\battlefield.py backend\app\schemas\__init__.py backend\app\services\battlefield_service.py backend\tests\test_battlefield_explanations.py backend\tests\test_battlefield_api.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 12。
2. 本步骤没有修改前端页面、导航或报告导出。
3. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
4. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 12 产品画像横向对比完成

### 当前完成情况

v2 实施计划步骤 12 已完成。本步升级产品画像后端数据，增加第一屏横向对比对象。

已完成实现：

1. `backend/app/schemas/profile.py` 新增 `ProductProfileComparison`、`ProfileComparisonProduct`、`ProfileComparisonDimension`、`ProfileComparisonValue` 和相关枚举。
2. `ProductProfileData` 新增 `horizontal_comparison`。
3. 横向对比默认包含目标产品、最高威胁直接竞品、最高威胁替代/渠道替代竞品；缺少直接或替代关系时不硬补假对象。
4. 第一屏对比维度包含价格带、核心卖点、主要人群、使用场景和证据可信状态。
5. 每个维度输出目标产品状态：`advantage`、`parity`、`weakness` 或 `insufficient_evidence`。
6. 每个优劣判断携带 Evidence 下钻引用和 Profile Trace 引用。
7. 功能树、截图证据和其他细节继续保留在原有下钻数据中，不放入横向对比第一层。
8. 更新 `backend/tests/test_profile_api.py`，验证画像接口返回横向对比对象。
9. 新增 `backend/tests/test_profile_comparison.py`，验证缺替代竞品不硬补、每个判断可下钻到证据。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_profile_api.py backend\tests\test_profile_comparison.py backend\tests\test_feedback_api.py -q`：通过，14 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\profile.py backend\app\schemas\__init__.py backend\app\services\profile_service.py backend\tests\test_profile_api.py backend\tests\test_profile_comparison.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 13。
2. 本步骤没有扩大 Human Feedback 范围，仍未允许自由编辑整份报告。
3. 本步骤没有修改前端页面、导航或报告导出。
4. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
5. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-29：v2 步骤 13 网页报告 2.0 结构完成

### 当前完成情况

v2 实施计划步骤 13 已完成。本步升级 Writer Agent 输出的网页报告数据结构。

已完成实现：

1. `ReportData` 新增 2.0 八个章节字段：结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。
2. `ReportData.section_order` 改为 2.0 八章节顺序。
3. 旧 1.0 报告字段在 Schema 中暂时保留为可选字段，用于兼容旧缓存读取；Writer 新产物不再把旧字段放入 `section_order`。
4. Writer Agent 将 Evidence 索引和 QA 摘要合并进“证据与质检附录”，不再作为主章节标题。
5. 每个核心竞品判断补充 `judgment_strength`。
6. 每条产品策略建议补充 `priority` 和 `responsibility_type`。
7. 报告章节标题改为自然中文表达，避免主章节裸露技术字段。
8. 更新 `backend/tests/test_writer_agent.py`、`backend/tests/test_reports_api.py` 和 `backend/tests/test_demo_freeze.py`，覆盖 2.0 章节结构、判断强度、建议优先级/责任类型和冻结 Demo 报告形状。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_reports_api.py backend\tests\test_demo_freeze.py -q`：通过，12 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\report.py backend\app\agents\writer.py backend\tests\test_writer_agent.py backend\tests\test_reports_api.py backend\tests\test_demo_freeze.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 14。
2. 本步骤没有删除 Markdown 导出 API，删除留给步骤 16。
3. 本步骤没有实现 DOCX、关系图 PNG、前端报告页或导航。
4. 本步骤没有引入外部采集、模型调用、队列、缓存、数据库或新前端技术。
5. 未写入真实 API Key，未在代码、测试或文档中记录密钥。

## 2026-05-30：v2 步骤 14 简化竞争关系图 PNG 服务完成

### 当前完成情况

v2 实施计划步骤 14 已完成。本步骤新增后端简化关系图 PNG 生成能力，供后续 Word 报告导出复用；不新增 HTTP API，不引入 Graphviz、浏览器渲染服务或后端 PDF 服务。

已完成实现：

1. `ReportData` 同模块已包含 `RelationshipGraphImage` 导出产物 Schema，并在 `backend/app/schemas/__init__.py` 统一导出。
2. 新增 `backend/app/services/relationship_graph_service.py`，提供 `render_relationship_graph_png`、`RelationshipGraphService`、`RelationshipGraphServiceError` 和 `RELATIONSHIP_GRAPH_ARTIFACT_TYPE`。
3. PNG 使用 Pillow 静态布局生成，只展示目标产品、3 到 5 条关键竞争关系、威胁等级、PM 关系标签和证据可信状态。
4. 缺少关键关系或竞品时生成可用占位图，不阻断网页报告阅读。
5. 关系图渲染失败时写入 Trace metadata 的 `relationship_graph_failures` 和 `last_failure`，且只记录异常类型，不写入异常消息中的敏感文本。
6. 关系图文本和文件名在写入前经过敏感信息脱敏；导出元信息不记录产品名、API Key、Token 或本地隐私路径。
7. 更新 `backend/app/services/__init__.py`，统一导出关系图服务能力。
8. 新增 `backend/tests/test_relationship_graph_service.py`，覆盖 PNG 生成、无竞品占位、失败记录不影响网页报告、敏感信息不落盘。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_relationship_graph_service.py backend\tests\test_reports_api.py -q`：通过，9 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\__init__.py backend\app\services\__init__.py backend\app\services\relationship_graph_service.py backend\tests\test_relationship_graph_service.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 15。
2. 本步骤没有实现 DOCX 导出接口或 Word 报告模板，关系图仅作为后续 DOCX 的后端素材能力。
3. 本步骤没有删除 Markdown 导出 API，删除留给步骤 16。
4. 本步骤没有修改前端页面、导航或 OpenAPI 同步产物。
5. 本步骤没有引入 Graphviz、浏览器渲染服务、后端 PDF 服务、队列、缓存或新数据库。
6. 未写入真实 API Key，未在 PNG、Trace、导出元信息、代码、测试或文档中记录密钥。

## 2026-05-30：v2 步骤 15 Word 报告 Schema 与导出服务完成

### 当前完成情况

v2 实施计划步骤 15 已完成。本步骤新增真实 `.docx` Word 报告导出服务，不新增 HTTP API；API 替换留给步骤 16。

已完成实现：

1. `backend/app/schemas/report.py` 新增 `WordReport` Schema，记录报告 ID、任务 ID、生成时间、文件路径、文件名、字节大小和导出元信息。
2. `backend/app/schemas/__init__.py` 统一导出 `WordReport`。
3. 新增 `backend/app/services/word_report_service.py`，提供 `WordReportService`、`WordReportServiceError`、`WordRenderError`、`render_word_report` 和 `WORD_REPORT_ARTIFACT_TYPE`。
4. Word 报告使用 `python-docx` 生成真实 `.docx` 文件，默认保存到 `data/reports/` 或测试传入的输出目录。
5. Word 报告包含封面、静态目录、产品图片摘要、目标产品缩略图、核心竞品缩略图、简化竞争关系图、正文和两类附录。
6. 产品缩略图只解析本地可用素材，不联网抓取远程图片；图片缺失、不可读或不支持时写入“暂无可靠图片”，不导致导出失败。
7. Word 导出复用第 14 步关系图 PNG 服务，并保存关系图 Artifact；关系图生成失败时在 Word 导出元信息中记录失败类型并继续生成报告占位内容。
8. Word 文本、文件名和导出元信息在写入前进行敏感信息脱敏；安全扫描不允许 API Key、Token、手机号或账号 ID 进入 Word 文本。
9. 更新 `backend/app/services/__init__.py`，统一导出 Word 报告服务能力。
10. 新增 `backend/tests/test_word_report_service.py`，覆盖 DOCX 可打开、封面/目录/正文/附录、图片缺失占位和敏感信息脱敏。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_word_report_service.py backend\tests\test_relationship_graph_service.py -q`：通过，8 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests\test_reports_api.py -q`：通过，5 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\report.py backend\app\schemas\__init__.py backend\app\services\__init__.py backend\app\services\word_report_service.py backend\tests\test_word_report_service.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 16。
2. 本步骤没有新增 `GET /tasks/{task_id}/report/docx` API，HTTP 下载响应留给步骤 16。
3. 本步骤没有删除 `GET /tasks/{task_id}/report/markdown`，删除留给步骤 16。
4. 本步骤没有修改前端页面、导航或 OpenAPI TypeScript 同步产物。
5. 本步骤没有引入 Graphviz、浏览器渲染服务、Headless Office、后端 PDF 服务、队列、缓存或新数据库。
6. 未写入真实 API Key，未在 Word、Trace、导出元信息、代码、测试或文档中记录密钥。

## 2026-05-30：v2 步骤 16 Word 报告 API 与 Markdown API 废弃完成

### 当前完成情况

v2 实施计划步骤 16 已完成。本步骤新增 Word `.docx` 下载 API，并删除旧 Markdown 用户可见 API；同时同步 OpenAPI 类型和前端报告页导出入口。

已完成实现：

1. `backend/app/api/routes_reports.py` 新增 `GET /tasks/{task_id}/report/docx`，成功时直接返回真实 `.docx` 文件下载响应。
2. `GET /tasks/{task_id}/report/markdown` 已从 HTTP 路由删除，OpenAPI 中不再出现旧 Markdown 路径。
3. Word 下载失败返回标准错误响应，错误码为 `WORD_REPORT_EXPORT_FAILED`，网页报告读取接口不受影响。
4. 未完成任务请求 Word 下载返回标准 `WORD_REPORT_NOT_READY` 错误。
5. `frontend/src/api/client.ts` 新增文件下载能力，能处理成功 Blob 响应和失败时的标准 JSON 错误响应。
6. `frontend/src/App.tsx` 报告页导出按钮从 Markdown 改为 Word 下载，不再调用或展示 Markdown 导出入口。
7. 更新 `frontend/src/App.test.tsx` 和 `frontend/e2e/demo-path.e2e.spec.ts`，改为验证 Word 下载路径。
8. 运行 `npm --prefix frontend run sync:types` 同步 `frontend/src/api/schema.ts`，新增 docx 路由类型并移除 Markdown 路由类型。
9. 更新前端 mock/domain 中的导出命名，从 `markdown_export` 改为 `word_export`。
10. 将本地 Playwright 浏览器下载目录加入 ESLint 与 Prettier ignore，避免生成物干扰前端全量质量检查。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_reports_api.py backend\tests\test_word_report_service.py -q`：通过，11 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\api\routes_reports.py backend\tests\test_reports_api.py backend\app\services\word_report_service.py backend\app\services\relationship_graph_service.py`：通过。
3. `npm --prefix frontend run sync:types`：通过。
4. `npm --prefix frontend run test -- App.test.tsx src/api/client.test.ts`：通过，38 个测试通过。
5. `npm --prefix frontend run test -- src/api/contracts.test.tsx src/mocks/fixtures.test.tsx`：通过，4 个测试通过。
6. `npm --prefix frontend run lint`：通过。
7. `npm --prefix frontend run format:check`：通过。
8. `rg -n "Markdown|markdown|report/markdown|导出 Markdown|Markdown 已导出" frontend\src frontend\e2e -g "!node_modules/**"`：无结果，前端源码和 E2E 不再依赖 Markdown 导出入口。

### 本步边界

1. 本步骤没有开始 v2 步骤 17。
2. 本步骤只删除旧 Markdown 用户可见 HTTP API；历史 Markdown 渲染服务和旧单元测试暂未清理，后续若不再需要可在专项清理中移除。
3. 本步骤没有实现 Word 导出失败写入 Trace 的新逻辑，失败追踪留给步骤 17。
4. 本步骤没有引入 Graphviz、浏览器渲染服务、Headless Office、后端 PDF 服务、队列、缓存或新数据库。
5. 未写入真实 API Key，未在 Word、Trace、导出元信息、代码、测试或文档中记录密钥。

## 2026-05-30：v2 步骤 17 Word 导出失败追踪完成

### 当前完成情况

v2 实施计划步骤 17 已完成。本步骤补齐 Word 导出失败的 Trace 记录能力，确保下载失败可诊断且不影响网页报告阅读。

已完成实现：

1. `WordReportService.export_word_report()` 在 DOCX 渲染或写文件失败时调用 `_record_word_export_failure()`。
2. 失败记录写入任务对应 Trace artifact 的 `metadata.word_export_failures`，并同步更新 `metadata.last_failure`。
3. 失败记录包含 `code`、`status`、`report_id`、`phase`、`error_type`、`readable_reason`、脱敏 `details` 和 `recorded_at`。
4. 失败记录不保存异常消息正文、不保存本地绝对路径、不保存输出目录原文，避免泄露路径或敏感信息。
5. 若失败前没有 Trace artifact，会基于任务记录创建最小 Trace，再写入失败 metadata。
6. 更新 `backend/tests/test_reports_api.py`，模拟导出目录不可写，验证 Word API 返回标准错误、Trace 可查询、网页报告仍返回成功。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_reports_api.py backend\tests\test_trace_api.py -q`：通过，13 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests\test_word_report_service.py -q`：通过，4 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\services\word_report_service.py backend\tests\test_reports_api.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 18。
2. 本步骤只记录 Word 导出失败；关系图生成失败仍按步骤 14 的 `relationship_graph_failures` 记录或 Word 元信息降级处理。
3. 本步骤没有重构 Trace 为证据与过程追踪新视图，Trace 数据升级留给步骤 18。
4. 本步骤没有修改前端页面、导航或 OpenAPI TypeScript 同步产物。
5. 未写入真实 API Key，未在 Word、Trace、导出元信息、代码、测试或文档中记录密钥。

## 2026-05-30：v2 步骤 18 Trace 证据与过程追踪结构升级完成

### 当前完成情况

v2 实施计划步骤 18 已完成。本步骤将后端 Trace 数据升级为“证据与过程追踪”视图所需结构，前端页面重构留给后续步骤。

已完成实现：

1. `backend/app/schemas/trace.py` 新增 `TraceEvidenceItem`、`TraceEvidenceChain`、`TraceQualityRecord`、`TraceProcessView` 和 `TraceDrilldownTarget`。
2. `TraceDiff` 新增 `business_impact` 字段，用业务语言解释 QA 打回、证据补齐或 Analysis 重算带来的影响。
3. `TraceData` 新增 `evidence_chains`、`quality_records`、`process_view` 和 `drilldown_targets`，保留原有 DAG、Agent Run、Tool Call、Token Usage、Prompt Preview、QA Review 和 Diff 字段。
4. `TraceService` 以 Claim 为中心组织证据链，绑定 Evidence 摘要、可信等级、访问时间状态、风险标记、报告章节和下钻 query。
5. QA Review 会转换为质检记录，展示检查项、问题等级、打回目标、处理结果、是否已解决和是否仍需关注。
6. 技术过程视图默认标记 `technical_details_folded=True`，供前端默认折叠 Token、Tool Call、Payload 和 Prompt Preview 等技术细节。
7. 下钻入口统一提供 `trace_tab` query，并在有对象 ID 时附带 `claim_id`、`review_task_id` 或 `diff_id`，便于后续高亮目标条目。
8. `frontend/src/api/schema.ts` 已通过 OpenAPI 同步，包含新的 Trace 2.0 字段。
9. 顺手修正端到端任务执行测试中仍读取旧 `competitor_findings` 的断言，改为读取当前 2.0 正式章节 `core_competitor_analysis`。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_trace_api.py -q`：通过，9 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests\test_trace_api.py backend\tests\test_task_execution.py backend\tests\test_workflow.py -q`：通过，19 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\schemas\trace.py backend\app\schemas\__init__.py backend\app\services\trace_service.py backend\tests\test_trace_api.py backend\tests\test_task_execution.py backend\tests\test_workflow.py`：通过。
4. `backend\.conda312\python.exe -m pytest backend\tests\test_reports_api.py -q`：通过，7 个测试通过。
5. `npm --prefix frontend run sync:types`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 19。
2. 本步骤只升级后端 Trace 数据契约和类型同步；前端 Trace 页面 Tab 重构留给步骤 30 和 31。
3. 本步骤没有修改任务创建后的默认跳转、导航结构、总览页或页面布局。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Collection 修复或 Analysis 重算语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、队列、缓存、数据库或前端框架。
6. 未写入真实 API Key，Trace 响应和失败记录继续执行敏感信息脱敏。

## 2026-05-30：v2 步骤 19 OpenAPI 类型与前端 API Client 同步完成

### 当前完成情况

v2 实施计划步骤 19 已完成。本步骤同步 2.0 OpenAPI 类型，并在前端 API Client 增加受控请求封装。

已完成实现：

1. 运行 `npm --prefix frontend run sync:types`，`frontend/src/api/schema.ts` 已包含 Overview、DOCX、扩展 Battlefield、横向画像和 Trace 2.0 字段。
2. `frontend/src/api/client.ts` 新增 `TaskSliceQuery`、`BattlefieldQuery` 和 2.0 数据类型导出。
3. `ApiClient` 新增 `getOverview()`、`getBattlefield()`、`getProductProfile()`、`getReport()`、`getTrace()` 和 `downloadWordReport()`。
4. 新封装统一通过 `taskApiPath()` 编码 `task_id`，避免页面组件直接拼接不受控临时字段。
5. `frontend/src/api/index.ts` 导出新增 API 类型，供后续页面步骤复用。
6. `frontend/src/api/client.test.ts` 覆盖总览成功响应、总览标准错误响应、扩展图谱请求、画像请求、报告请求、Trace 请求和 Word 下载路径。
7. `frontend/src/api/contracts.test.ts` 覆盖 2.0 路径、Overview Schema、Trace 2.0 字段、DOCX 响应类型，并确认旧 Markdown 路径、旧 Markdown 操作和 `MarkdownReport` Schema 不在前端 OpenAPI 类型中。
8. 补齐 `frontend/src/App.test.tsx` fixture 与 2.0 Schema 的差异：`TraceDiff.business_impact`、Product 图片状态和 Report 2.0 必需章节。

### 验证结果

1. `npm --prefix frontend run sync:types`：通过。
2. `npm --prefix frontend run test -- src/api/client.test.ts src/api/contracts.test.ts`：通过，14 个测试通过。
3. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
4. `npm --prefix frontend run test -- App.test.tsx src/api/client.test.ts src/api/contracts.test.ts`：通过，45 个测试通过。
5. `npm --prefix frontend run lint`：通过。
6. `npm --prefix frontend run format:check`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 20。
2. 本步骤只补 API 类型和 Client 封装，尚未调整导航、默认落点或页面可见文案。
3. 页面组件仍会在后续步骤逐步改用新封装；本步骤不重构页面布局。
4. 本步骤没有引入 Redux、Next.js、Tailwind、复杂状态管理、新后端依赖或外部采集能力。
5. 未写入真实 API Key，新增测试数据不包含真实密钥。

## 2026-05-30：v2 步骤 20 前端导航与默认落点调整完成

### 当前完成情况

v2 实施计划步骤 20 已完成。本步骤调整前端主导航和创建任务后的默认页面落点，不实现总览首屏业务内容。

已完成实现：

1. 主导航调整为五个 2.0 工作台入口：竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪。
2. 保留 `/` 任务输入页，但不再把“任务输入”放入主导航五项中。
3. 新增 `/overview` 轻量落点页，用于接收创建任务后的 `task_id`，并提供通往图谱、画像、报告和追踪的入口。
4. 创建任务成功后默认跳转到 `/overview?task_id=<task_id>`。
5. 主导航跨页面跳转继续保留 `task_id` query。
6. 过程追踪页默认可见文案去除 `Trace`、`Agent Run`、`Tool Call`、`Token Usage`、`Diff View` 等英文标题，改为中文表达。
7. 智能体展示名从英文 `Collection Agent` 等改为采集智能体、分析智能体、质检智能体和报告智能体。

### 验证结果

1. `npm --prefix frontend run test -- App.test.tsx`：通过，34 个测试通过。
2. `npm --prefix frontend run test -- App.test.tsx src/api/client.test.ts src/api/contracts.test.ts`：通过，48 个测试通过。
3. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
4. `npm --prefix frontend run lint`：通过。
5. `npm --prefix frontend run format:check`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 21。
2. `/overview` 仅作为导航落点和任务 ID 承接页；一句话判断、关键竞品、行动建议和证据风险首屏展示留给步骤 21。
3. 本步骤没有改造 E2E Demo 路径；E2E 路径更新按计划留给步骤 34。
4. 本步骤没有改造竞争图谱、画像页、报告页或 Trace Tab 结构。
5. 本步骤没有引入新技术栈、复杂状态管理、外部采集、模型必需链路或新后端依赖。

## 2026-05-30：v2 步骤 21 竞争态势总览页首屏完成

### 当前完成情况

v2 实施计划步骤 21 已完成。本步骤把 `/overview` 从任务承接占位页升级为 Overview API 驱动的竞争态势总览首屏。

已完成实现：

1. `/overview?task_id=<task_id>` 调用 `GET /tasks/{task_id}/overview`，优先使用 `ApiClient.getOverview()`，测试客户端缺省时回退到受控 `get()` 路径。
2. 首屏展示一句话竞争判断、判断强度、决策可用状态、分析范围统计、首要行动建议和证据风险提醒。
3. 首屏明确展示分析范围说明：报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。
4. 关键竞品区展示产品缩略图、产品名称、关系标签、威胁等级、证据可信度、纳入原因和“查看竞争关系”下钻入口。
5. 缺少竞品图片或图片加载失败时展示“暂无可靠图片”，不凭空补图。
6. “查看竞争关系”会跳转到 `/battlefield`，保留当前 `task_id`，并携带 Overview 下钻引用中的 `edge_id`。
7. 新增 `frontend/e2e/overview.visual.spec.ts`，验证 1366x900 桌面首屏无需滚动即可看到核心判断、范围说明、行动建议和无图兜底。

### 验证结果

1. `npm --prefix frontend run test -- App.test.tsx`：通过，37 个测试通过。
2. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run format:check`：通过。
5. `npm --prefix frontend run test:e2e -- overview.visual.spec.ts`：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 22。
2. 本步骤只实现总览首屏，不改造竞争图谱的交互与切片细节。
3. 本步骤不改变后端 Overview 数据生成逻辑、LangGraph DAG、四 Agent、QA 打回、Human Review 或报告导出语义。
4. 本步骤新增的视觉测试使用开发测试 fixture，不作为最终演示数据。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 22 总览页切片联动完成

### 当前完成情况

v2 实施计划步骤 22 已完成。本步骤为竞争态势总览页增加价格带、人群和使用场景切片联动。

已完成实现：

1. `/overview` 新增“动态切片”控件，包含价格带切片、人群切片和使用场景切片三个下拉选择。
2. 切片可选项复用 `GET /tasks/{task_id}/battlefield?include_all_relations=true` 返回的 `available_slices`，避免前端硬编码业务选项。
3. 切片变化后，Overview Query Key 携带 `price_band`、`persona`、`scenario`，并重新请求 `GET /tasks/{task_id}/overview`。
4. Overview 请求只提交非空切片字段，默认全量视角仍调用不带切片 query 的 Overview 接口。
5. 总览页机会点和风险点增加可见区域；一句话判断、关键竞品、机会点、风险点和首要行动建议都来自最新 Overview 响应。
6. 关键竞品下钻继续保留 `task_id` 和 `edge_id`，不受切片控件实现影响。
7. Overview 视觉测试补充 Battlefield 切片选项 mock，避免视觉用例触发真实后端请求。

### 验证结果

1. `npm --prefix frontend run test -- App.test.tsx`：通过，40 个测试通过。
2. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run format:check`：通过。
5. `npm --prefix frontend run test:e2e -- overview.visual.spec.ts`：通过，1 个 Playwright 视觉用例通过。
6. `git diff --check -- frontend\src\App.tsx frontend\src\App.css frontend\src\App.test.tsx frontend\e2e\overview.visual.spec.ts memory-bank\progress.md memory-bank\architecture.md`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 23。
2. 本步骤没有新增后端接口字段；切片控件选项来自现有 Battlefield 2.0 数据。
3. 本步骤没有改造竞争图谱默认阅读层、术语解释组件、画像页、报告页或证据与过程追踪页。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、Word 导出或 Overview 生成语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 23 统一术语解释组件完成

### 当前完成情况

v2 实施计划步骤 23 已完成。本步骤新增统一术语解释组件，并在总览、图谱评分、证据和质检附近接入。

已完成实现：

1. 新增 `frontend/src/termExplanations.ts`，集中维护术语标签和短解释文案。
2. 新增 `frontend/src/TermHint.tsx`，提供统一的问号解释按钮，支持鼠标悬停和键盘聚焦展示 tooltip。
3. 覆盖 10 个必需术语：需求替代性、上下文匹配度、决策阶段影响力、证据置信度、市场信号强度、质检、证据可信状态、动态切片、威胁等级、判断强度。
4. 在总览动态切片、判断强度、威胁等级、证据可信度、竞争图谱评分拆解、证据置信度和 QA 打回记录附近接入 `TermHint`。
5. 术语解释文案保持短句中文，不使用裸英文技术词。
6. `TermHint` 触发按钮与原标签文本分离，避免破坏既有精确文本断言和阅读层结构。

### 验证结果

1. `npm --prefix frontend run test -- App.test.tsx src/TermHint.test.tsx`：通过，43 个测试通过。
2. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run format:check`：通过。
5. `npm --prefix frontend run test:e2e -- overview.visual.spec.ts`：通过，1 个 Playwright 视觉用例通过。
6. `git diff --check -- frontend\src\App.tsx frontend\src\App.css frontend\src\App.test.tsx frontend\src\TermHint.tsx frontend\src\TermHint.test.tsx frontend\src\termExplanations.ts frontend\e2e\overview.visual.spec.ts memory-bank\progress.md memory-bank\architecture.md`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 24。
2. 本步骤只新增术语解释组件和就近接入，不重构竞争图谱默认阅读层。
3. 本步骤没有改变后端 API、Overview/Battlefield 数据生成逻辑、LangGraph DAG、QA 打回或报告导出语义。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 24 竞争图谱默认阅读层完成

### 当前完成情况

v2 实施计划步骤 24 已完成。本步骤重构竞争图谱页默认阅读层，使 PM 先看到后端筛选出的关键竞争关系，再按需展开全部关系。

已完成实现：

1. 竞争图谱页默认调用 `GET /tasks/{task_id}/battlefield`，只渲染后端 `key_relations` 对应的关键关系边和相关节点。
2. 新增“展开全部关系”开关；开启后请求携带 `include_all_relations=true`，显示后端返回的全部关系。
3. 切换价格带、人群或使用场景切片时会重置为默认关键关系视图，避免跨切片沿用旧的展开状态。
4. 新增关键关系阅读面板，默认展示竞品名称、PM 关系标签、威胁等级、证据可信度、纳入原因和关系说明。
5. 竞争图谱连线不再直接显示原始竞争分；原始分数保留在右侧“评分拆解”区域中。
6. 图谱节点范围按当前可见关系裁剪，目标产品节点始终保留；无关键关系时回退展示后端返回的图谱数据。
7. 视觉测试扩展为桌面和窄屏两种视口，验证图谱与详情面板没有重叠。

### 验证结果

1. `npm --prefix frontend run test -- App.test.tsx src/TermHint.test.tsx`：通过，46 个测试通过。
2. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run format:check`：通过。
5. `npm --prefix frontend run test:e2e -- battlefield.visual.spec.ts`：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 25。
2. 本步骤只改造竞争图谱页默认阅读层，不改变 Battlefield 后端数据生成逻辑。
3. 本步骤没有改变 Overview、画像、报告、Trace 页面或任务创建默认跳转语义。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、Markdown/Word 导出语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 25 竞争边详情重构完成

### 当前完成情况

v2 实施计划步骤 25 已完成。本步骤将竞争边详情从技术字段陈列升级为可阅读、可追溯的四段式解释层。

已完成实现：

1. 竞争边详情默认展示“为什么是竞品、强在哪、影响哪个决策阶段、应对建议”四段式解释。
2. 四段解释直接消费后端 `key_relations.four_part_explanation`，前端不自行编造竞争判断。
3. “应对建议”段落在 UI 中显式标记为“分析建议”。
4. 每个解释段落提供“查看依据”入口，展开后展示相关结论 ID、证据 ID 和证据卡片。
5. 五维评分保留原维度名称，并为每个维度增加一句自然中文解释。
6. 竞争边详情默认可见文案从 `Edge Detail`、`Claims`、`Evidence` 等裸英文改为中文业务表达。
7. 详情页仍保留原始竞争分、评分拆解、结论与证据、证据卡片和质检打回记录。

### 验证结果

1. `npm --prefix frontend run test -- App.test.tsx src/TermHint.test.tsx`：通过，50 个测试通过。
2. `frontend\node_modules\.bin\tsc.cmd --noEmit`：通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run format:check`：通过。
5. `npm --prefix frontend run test:e2e -- battlefield.visual.spec.ts`：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 26。
2. 本步骤只重构竞争边详情，不改造产品与竞品画像页。
3. 本步骤没有改变后端 Battlefield 数据生成逻辑、OpenAPI Schema、Overview、报告或 Trace 语义。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、Markdown/Word 导出语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 26 产品与竞品画像页重构完成

### 当前完成情况

v2 实施计划步骤 26 已完成。本步骤将产品画像页从单一目标产品模块升级为目标产品与核心竞品横向对比首屏，同时保留原有画像信息作为下钻区域。

已完成实现：

1. `frontend/src/App.tsx` 新增产品画像横向对比工作台，直接消费后端 `ProductProfileData.horizontal_comparison`。
2. 首屏默认展示三列：目标产品、最高威胁直接竞品、最高威胁替代竞品。
3. 三列卡片展示产品名称、品牌和主图状态；缺少图片时统一显示“暂无可靠图片”，缺少竞品时显示明确空状态，不硬补假竞品。
4. 对比维度展示价格带、核心卖点、主要人群、使用场景和证据可信状态。
5. 每个维度展示目标产品判断状态：优势、持平、短板或证据不足，并展示后端给出的状态原因。
6. 每个优劣判断提供“查看依据”入口，下钻到证据与过程追踪页并携带 `task_id`、`tab=evidence` 和首个 `evidence_id`。
7. 原有基础信息、功能树、价格模型、用户人群、Evidence 摘要和有限人工修正面板继续保留，作为横向对比后的下钻与修正能力。
8. 新增 `frontend/e2e/profile.visual.spec.ts`，验证窄屏下横向对比不会严重水平溢出。

### 验证结果

1. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，52 个测试通过。
2. `frontend\node_modules\.bin\tsc.cmd --noEmit --project frontend\tsconfig.json`：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `npm --prefix frontend run test:e2e -- profile.visual.spec.ts`：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 27。
2. 本步骤只改造前端产品与竞品画像页，不改变后端 `ProfileService`、OpenAPI Schema 或横向对比生成规则。
3. 本步骤没有扩大 Human Review 允许范围，仍只允许受控结构化字段修正。
4. 本步骤没有改变 Overview、Battlefield、Report、Trace、任务创建跳转、LangGraph DAG、四 Agent、QA 打回或导出语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 27 人工修正文案与入口调整完成

### 当前完成情况

v2 实施计划步骤 27 已完成。本步骤将前端人工复核入口改为业务中文命名，并补齐人工修正差异在 Trace 中的可查询能力。

已完成实现：

1. `frontend/src/App.tsx` 将画像页右侧入口从“有限人工修正 / Human Review”改为“修正画像 / 受控复核”。
2. 用户可见动作明确展示为“修正画像、标记不采纳、补充证据备注”。
3. 表单字段文案改为“画像字段、修正后的值、修正原因”，提交按钮改为“提交修正画像”。
4. 表单仍只提交 `update_field` 到产品画像结构化字段，不开放自由编辑整份报告或直接改写 Claim 正文。
5. `backend/app/services/feedback_service.py` 在反馈元数据中保存 before/after/reason，供 Trace 差异记录消费。
6. `backend/app/services/trace_service.py` 新增 `human_feedback` 差异记录生成，展示人工修正的业务影响和反馈原因。
7. `backend/tests/test_feedback_api.py` 补充拒绝直接改写 Claim 正文和画像修正可在 Trace 差异中查询的测试。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_feedback_api.py backend\tests\test_trace_api.py`：通过，17 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\services\feedback_service.py backend\app\services\trace_service.py backend\tests\test_feedback_api.py`：通过。
3. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，52 个测试通过。
4. `frontend\node_modules\.bin\tsc.cmd --noEmit --project frontend\tsconfig.json`：通过。
5. `npm run lint`（工作目录 `frontend/`）：通过。
6. `npm run format:check`（工作目录 `frontend/`）：通过。
7. `git diff --check -- backend\app\services\feedback_service.py backend\app\services\trace_service.py backend\tests\test_feedback_api.py frontend\src\App.tsx frontend\src\App.css frontend\src\App.test.tsx`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 28。
2. 本步骤没有扩大后端反馈接口自由度；Claim 仍只能标记状态，Evidence 仍只能补备注，画像字段仍受 allowlist 控制。
3. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Overview、Battlefield、Report 或 Word 导出语义。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。
5. Ruff 默认缓存目录在当前 Windows 沙箱下不可写，验证时使用 `--no-cache`，不影响代码质量结论。

## 2026-05-30：v2 步骤 28 分析报告页工作台视图完成

### 当前完成情况

v2 实施计划步骤 28 已完成。本步骤将分析报告页调整为 2.0 工作台视图，保留网页报告阅读能力，并把正式交付入口切换为 Word 下载。

已完成实现：

1. `frontend/src/App.tsx` 的报告页按 2.0 八章节渲染：结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。
2. 报告页顶部提供报告编号、生成时间、章节数量和工具栏。
3. 工具栏提供“下载 Word 报告”“打印或另存 PDF”“切换打印视图”三个入口。
4. 页面不再展示 Markdown 导出入口、Markdown 成功提示或旧 Markdown 文案。
5. Word 下载调用 `GET /tasks/{task_id}/report/docx`；导出失败时显示错误，但继续保留网页报告章节。
6. 报告页增加静态图谱摘要区域，供打印视图和离线阅读使用。
7. 每个报告章节保留 Claim、Evidence、风险标记，并新增“查看依据”“查看过程”下钻入口，跳转到证据与过程追踪页。
8. 报告未生成时显示等待状态，不展示最终报告章节。

### 验证结果

1. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，54 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 29。
2. 本步骤只改造分析报告页工作台视图，不新增后端 PDF 服务。
3. 本步骤没有改动后端 ReportData、Word 导出服务、LangGraph DAG、四 Agent、QA 打回或 Human Review 语义。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 29 报告打印视图完成

### 当前完成情况

v2 实施计划步骤 29 已完成。本步骤补齐分析报告页的打印视图语义，使其适合浏览器打印或另存 PDF，同时不新增后端 PDF 服务。

已完成实现：

1. 切换打印视图后，页面在 `body` 上标记 `data-report-view="print"`，用于隐藏主导航和页面头部。
2. 打印视图隐藏报告工具栏和章节下钻按钮，只保留正式报告内容。
3. CSS 增加 `@media print` 规则，浏览器打印时隐藏导航、按钮和交互控件。
4. 打印视图保留静态图谱摘要和八个报告章节。
5. 新增 `frontend/e2e/report.visual.spec.ts`，验证打印视图非空、导航和工具栏隐藏、静态图谱摘要可见、核心报告文案首屏可见。

### 验证结果

1. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，54 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `npm run test:e2e -- report.visual.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 30。
2. 本步骤只实现前端打印视图和浏览器打印样式，不新增后端 PDF 服务、Headless Office 或复杂导出依赖。
3. 本步骤没有改动后端报告生成、Word 导出、LangGraph DAG、四 Agent、QA 打回或 Human Review 语义。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 30 证据与过程追踪页 Tab 重构完成

### 当前完成情况

v2 实施计划步骤 30 已完成。本步骤将旧过程追踪页重构为“证据与过程追踪”四 Tab 阅读层。

已完成实现：

1. `TraceContent` 新增四个 Tab：证据链、质检记录、智能体过程、差异记录。
2. 默认 Tab 为证据链，优先使用后端 `process_view.default_tab`，默认兜底为 `evidence_chain`。
3. 证据链 Tab 按结论组织 `evidence_chains`，展示结论内容、采纳状态、置信度、推断标记、报告章节和引用证据。
4. 每条证据展示来源类型、访问时间状态、置信度、局限性、来源链接和风险标记。
5. 质检记录 Tab 优先展示 `quality_records`，并保留 `qa_reviews` 兜底。
6. 智能体过程 Tab 保留 LangGraph 流程图和 Agent Run 列表。
7. Tool Call、模型用量和 Prompt 摘要被放入“技术详情”折叠区，默认折叠。
8. Prompt 摘要继续通过 `sanitizeTraceText` 脱敏展示。
9. 差异记录 Tab 保留 before/after，并展示 `business_impact` 业务影响说明。
10. 更新 Trace 组件测试和 `trace.visual.spec.ts`，验证默认 Tab、技术详情折叠、脱敏和视觉布局。

### 验证结果

1. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，54 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `npm run test:e2e -- trace.visual.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 31。
2. 本步骤只重构 Trace 页 Tab 和默认阅读层，不改变后端 Trace 生成语义。
3. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、Overview、Battlefield、Report 或 Word 导出语义。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 31 质检记录和差异记录展示重构完成

### 当前完成情况

v2 实施计划步骤 31 已完成。本步骤强化“证据与过程追踪”页中质检记录和差异记录的业务阅读层，让 QA 打回、已解决状态、仍需关注状态和人工修正影响更容易判断。

已完成实现：

1. `TraceQualityRecords` 新增质检状态汇总，分别统计仍需关注、已解决、待处理或豁免记录。
2. 每条质检记录显式展示 QA 检查项、问题等级、质检打回对象、打回目标、处理要求、处理结论和是否仍需关注。
3. 已解决、仍需关注和待处理状态使用不同状态标签与视觉边框，避免用户只看到同质化列表。
4. `TraceDiffView` 将差异来源翻译为业务分类：QA 打回修复、QA 打回后的分析重算、人工修正差异和流程差异。
5. Diff 默认优先展示变化来源、影响对象、关联打回和业务影响说明。
6. Diff 的 before/after 结构化值被放入“查看结构化前后值”折叠区，作为佐证材料而不是默认主阅读层。
7. 组件测试补充仍需关注的 QA 记录和人工修正差异，E2E Trace 视觉测试补充 QA 修复业务影响断言。

### 验证结果

1. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，55 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `npm run test:e2e -- trace.visual.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 视觉用例通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 32。
2. 本步骤只改造 Trace 页质检记录和差异记录展示，不改变后端 TraceService、Trace API、QA 规则或 Human Review 语义。
3. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Overview、Battlefield、Report 或 Word 导出语义。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 32 全站中文化专项完成

### 当前完成情况

v2 实施计划步骤 32 已完成。本步骤检查并补齐主导航、页面标题、模块标题、按钮、状态、Mock 文案、图谱说明、报告导出内容和过程追踪展示中的主界面中文化。

已完成实现：

1. 产品与竞品画像页将默认可见模块标题从 `FeatureTree`、`PricingModel`、`UserPersona`、`Evidence 摘要` 调整为“功能能力树”“价格与证据”“用户人群画像”“证据摘要”。
2. 画像页模块 eyebrow 从 `Target`、`Capabilities`、`Price`、`Audience`、`Evidence` 调整为中文业务表达。
3. 证据与过程追踪页智能体流程图标题从裸技术表达调整为“协作流程图”。
4. 追踪流程图边标签在前端渲染层将 Collection、Analysis、QA、Writer 等原始标签翻译为采集、分析、质检、报告等中文表达。
5. Prompt 预览标题在前端渲染层由 `Collection prompt` 等原始标题翻译为“采集智能体提示摘要”等中文标题，并继续保留脱敏状态。
6. 旧 E2E 断言同步到 2.0 中文页面结构：证据链、质检记录、智能体过程、差异记录、运行记录列表和修正画像入口。
7. 新增前端中文化组件测试，扫描默认用户可见工作台文案，防止 `Agent Run`、`Tool Call`、`Payload`、`Diff View`、`FeatureTree`、`PricingModel` 等裸英文技术词回流。

### 验证结果

1. `npm run test -- App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，56 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `npm run test:e2e -- trace.visual.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 视觉用例通过。
6. `npm run test:e2e -- report.visual.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 视觉用例通过。
7. `backend\.conda312\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_reports_api.py backend\tests\test_word_report_service.py`：通过，15 个测试通过。
8. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\agents\writer.py backend\app\services\word_report_service.py backend\tests\test_writer_agent.py backend\tests\test_reports_api.py backend\tests\test_word_report_service.py`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 33。
2. 本步骤只改造主界面可见文案和测试断言，不改变后端 API、OpenAPI Schema 或 Agent 数据协议。
3. 技术详情中仍允许保留中文名称加原始字段、SKU、QA、DOCX 和 Word 等必要缩写或交付名。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、Overview、Battlefield、Report 或 Word 导出语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 33 Mock、Fixture 和测试数据更新完成

### 当前完成情况

v2 实施计划步骤 33 已完成。本步骤将前端开发 Mock、后端 fixture 合约测试和冻结 Demo 回归对齐到 2.0 API 契约。

已完成实现：

1. 前端 `frontend/src/types/domain.ts` 改为基于 OpenAPI 生成类型定义 `OverviewFixture`、`ProductProfileData`、`BattlefieldData`、`TraceData` 和 `ReportData` 的开发 fixture。
2. 新增 `mockOverviewFixture`，并将 `ALL_DEVELOPMENT_MOCKS` 扩展为总览、画像、图谱、追踪和报告五类开发数据。
3. 重写 `mockBattlefieldFixture`，移除旧 `task/products/graph/competition_edges/claims/evidences` 1.0 结构，改为 2.0 `graph_nodes`、`graph_edges`、`key_relations`、`evidence_cards`、`qa_summary`、`score_explanations` 和 `decision_chain`。
4. 报告 Mock 固定 2.0 八章节：结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。
5. Trace Mock 固定使用 `evidence_chains`、`quality_records`、`diffs`、`prompt_previews` 和 `process_view`，保留 QA 打回和差异业务影响。
6. 前端 fixture 测试更新为五页面区域 typed preview，并增加 2.0 八章节、非最终演示数据标记和敏感信息扫描断言。
7. 新增 `backend/tests/test_v2_fixture_contracts.py`，集中验证冻结 Demo 产出的总览、关键关系、证据链组织、DOCX 缺图兜底和 fixture 脱敏安全。
8. 未改动冻结 Demo 快照文件、哈希、稳定输入或最终演示数据。

### 验证结果

1. `npm run test -- src/mocks/fixtures.test.tsx App.test.tsx src/TermHint.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，62 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `backend\.conda312\python.exe -m pytest backend\tests\test_v2_fixture_contracts.py backend\tests\test_demo_freeze.py backend\tests\test_overview_service.py backend\tests\test_overview_api.py backend\tests\test_battlefield_api.py backend\tests\test_trace_api.py backend\tests\test_reports_api.py backend\tests\test_word_report_service.py`：通过，43 个测试通过。
6. `backend\.conda312\python.exe -m ruff check --no-cache backend\tests\test_v2_fixture_contracts.py`：通过。
7. `git diff --check`（本步骤触达文件）：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 34。
2. 本步骤只更新开发 Mock、测试 fixture 和 fixture 合约测试，不改变 OpenAPI Schema、后端业务生成语义或冻结 Demo 数据。
3. 前端 Mock 均显式标记为 `development_mock` 和 `final_demo_data: false`，不得作为最终演示数据。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、Overview、Battlefield、Report 或 Word 导出语义。
5. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 34 端到端 Demo 路径更新完成

### 当前完成情况

v2 实施计划步骤 34 已完成。本步骤把真实后端 E2E Demo 路径切换到 2.0 信息架构：创建任务后进入竞争态势总览，再覆盖总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪和 Word 导出。

已完成实现：

1. `task-flow.e2e.spec.ts` 由旧“创建后进 Trace”改为“创建后进入竞争态势总览”，并依次验证总览、图谱、画像、报告和证据与过程追踪。
2. `demo-path.e2e.spec.ts` 更新为完整 2.0 Demo 路径：输入页截图、总览首屏、竞争图谱、产品画像、报告、Word 导出、证据与过程追踪和窄屏布局。
3. `qa-revision.e2e.spec.ts` 从总览入口开始，继续验证真实 QA 打回、采集补证、Analysis 重算、Trace 差异记录和报告中修复后证据链。
4. QA 修正路径新增受控人工修正入口验证：画像页展示修正画像、标记不采纳、补充证据备注，提交画像字段修正后 Trace 出现 `human_feedback` 差异。
5. E2E 报告断言从旧“执行摘要 / QA 审查摘要”迁移到 2.0 八章节中的“结论摘要、竞争格局判断、核心竞品拆解、证据与质检附录”。
6. Demo 路径覆盖 `GET /tasks/{task_id}/report/docx`，确认返回可打开的 Word `.docx` 字节头，不再覆盖 Markdown 导出。
7. 前端报告字段展示将 `Collection 修复`、`Analysis 重算` 调整为“采集智能体修复”“分析智能体重算”，报告模块摘要也切换到 2.0 章节名称。

### 验证结果

1. `npm run test:e2e -- task-flow.e2e.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 用例通过。
2. `npm run test:e2e -- qa-revision.e2e.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 用例通过。
3. `npm run test:e2e -- demo-path.e2e.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 用例通过。
4. `npm run test -- App.test.tsx src/TermHint.test.tsx src/mocks/fixtures.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，62 个测试通过。
5. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
6. `npm run lint`（工作目录 `frontend/`）：通过。
7. `npm run format:check`（工作目录 `frontend/`）：通过。
8. `backend\.conda312\python.exe -m pytest backend\tests\test_reports_api.py backend\tests\test_trace_api.py backend\tests\test_feedback_api.py backend\tests\test_demo_freeze.py`：通过，27 个测试通过。
9. `git diff --check`（本步骤触达文件）：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 35。
2. 本步骤只更新 E2E Demo 路径、相关报告字段中文化和测试断言，不改变后端 API、OpenAPI Schema、LangGraph DAG 或数据生成语义。
3. 本步骤没有恢复 Markdown 导出入口，也没有新增 PDF 服务或复杂导出依赖。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 35 响应式和视觉验证完成

### 当前完成情况

v2 实施计划步骤 35 已完成。本步骤补齐总览、图谱、画像、报告、证据与过程追踪在桌面和窄屏下的布局验证，重点检查主导航与内容区、图谱节点、关键竞品图片和报告按钮不发生遮挡或严重溢出。

已完成实现：

1. 新增 `frontend/e2e/responsive.visual.spec.ts`，使用 2.0 开发 fixture mock API，一次覆盖五个页面的桌面和窄屏截图。
2. 响应式视觉用例验证竞争态势总览首屏、关键竞品与“暂无可靠图片”缩略图在桌面和窄屏下可见且不互相遮挡。
3. 响应式视觉用例验证竞争图谱的 React Flow 节点和边非空，图谱容器保持稳定高度，窄屏下无严重水平溢出。
4. 响应式视觉用例验证产品画像横向对比在窄屏下堆叠，关键竞品图片占位与标题文本不重叠。
5. 响应式视觉用例验证报告工具栏中 Word 下载和浏览器打印按钮不互相遮挡，并确认没有 Markdown 导出按钮。
6. 响应式视觉用例验证证据与过程追踪的流程图容器稳定，默认证据链和智能体过程在桌面/窄屏下可读。
7. 复跑已有 `overview.visual`、`battlefield.visual`、`profile.visual`、`report.visual`、`trace.visual`，确认既有视觉断言仍通过。

### 验证结果

1. `npm run test:e2e -- responsive.visual.spec.ts`（工作目录 `frontend/`）：通过，1 个 Playwright 响应式视觉用例通过。
2. `npm run test:e2e -- overview.visual.spec.ts battlefield.visual.spec.ts profile.visual.spec.ts report.visual.spec.ts trace.visual.spec.ts`（工作目录 `frontend/`）：通过，5 个 Playwright 视觉用例通过。
3. `npm run test -- App.test.tsx src/TermHint.test.tsx src/mocks/fixtures.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，62 个测试通过。
4. `.\node_modules\.bin\tsc.cmd --noEmit --project tsconfig.json`（工作目录 `frontend/`）：通过。
5. `npm run lint`（工作目录 `frontend/`）：通过。
6. `npm run format:check`（工作目录 `frontend/`）：通过。
7. `git diff --check -- frontend\e2e\responsive.visual.spec.ts`：通过。

### 本步边界

1. 本步骤没有开始 v2 步骤 36。
2. 本步骤只新增响应式视觉回归测试，不改变后端 API、OpenAPI Schema、数据生成语义、LangGraph DAG、四 Agent、QA 打回或 Word 导出。
3. 本步骤没有引入新 UI 框架、视觉库、截图服务、外部采集、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 36 安全与合规回归完成

### 当前完成情况

v2 实施计划步骤 36 已完成。本步骤补齐网页报告、Word 报告、Trace、导出失败记录、前端报告渲染和 QA 规则的安全合规回归。

已完成实现：

1. `ReportService` 新增 `redact_report_data`，网页报告生成和缓存读取前统一对 `ReportData` 做敏感内容脱敏。
2. `WordReportService` 在报告缓存写入和读取时复用同一份报告脱敏逻辑，确保 DOCX 文本与缓存报告保持一致的安全边界。
3. `routes_reports.py` 支持测试注入 `report_workflow_factory`，用于安全回归构造敏感报告输入，不改变生产默认 workflow。
4. 新增 `backend/tests/test_v2_security_compliance.py`，集中扫描网页报告、缓存报告、Word 文本、Trace 响应、导出失败响应和 Trace 失败元信息。
5. QA 规则测试扩展为参数化用例，覆盖宠物安全、电器认证、零风险和医疗级/治疗等敏感绝对化表达。
6. 前端报告渲染复用脱敏函数展示报告摘要、字段值、数组值、嵌套字段和敏感字段标签，避免异常 API 数据直出。
7. 新增前端报告页面安全测试，确认页面不渲染 `api_key`、Token、手机号、账号 ID 和地址等敏感模式。
8. Writer Agent 当前仍只基于结构化 Product、Evidence、Claim、CompetitionEdge 和 QA 结果拼装报告，没有引入模型润色新增事实链路；既有 Writer 测试继续约束建议为推断且绑定证据。

### 验证结果

1. `backend\.conda312\python.exe -m pytest backend\tests\test_v2_security_compliance.py backend\tests\test_qa_rules.py backend\tests\test_trace_api.py backend\tests\test_reports_api.py backend\tests\test_word_report_service.py backend\tests\test_api_response.py`：通过，37 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests\test_v2_security_compliance.py backend\tests\test_qa_rules.py backend\tests\test_reports_api.py backend\tests\test_word_report_service.py`：通过，25 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\services\report_service.py backend\app\services\word_report_service.py backend\app\api\routes_reports.py backend\tests\test_v2_security_compliance.py backend\tests\test_qa_rules.py`：通过。
4. `npm run test -- App.test.tsx src/TermHint.test.tsx src/mocks/fixtures.test.tsx`（工作目录 `frontend/`，`VITE_CACHE_DIR=.vite-cache-codex`）：通过，63 个测试通过。
5. `npx tsc --noEmit`（工作目录 `frontend/`）：通过。
6. `npm run lint`（工作目录 `frontend/`）：通过。
7. `npm run format:check`（工作目录 `frontend/`）：通过。
8. `git diff --check -- backend\app\services\report_service.py backend\app\services\word_report_service.py backend\app\api\routes_reports.py backend\tests\test_v2_security_compliance.py backend\tests\test_qa_rules.py frontend\src\App.tsx frontend\src\App.test.tsx`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 37。
2. 本步骤只收紧报告、Trace、导出失败和前端渲染安全边界，不改变 OpenAPI Schema、LangGraph DAG、四 Agent、QA 打回、Human Review 或冻结 Demo 数据。
3. 本步骤没有把模型 API Key、Token、Secret、手机号、账号 ID、地址等敏感内容写入代码、文档、日志、Trace、截图或导出报告。
4. 本步骤没有引入新技术栈、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 37 文档与架构记录更新完成

### 当前完成情况

v2 实施计划步骤 37 已完成。本步骤把当前 2.0 产品定位、信息架构、报告交付方式、API 协作契约和技术栈约束同步到项目文档。

已完成实现：

1. `memory-bank/design-document.md` 从 v1.0 更新为 v2.0，记录创建任务后默认进入竞争态势总览、五个核心工作台页面和 2.0 报告交付方式。
2. `memory-bank/design-document.md` 将正式报告交付从 Markdown 改为网页报告 + Word `.docx` + 浏览器打印/另存 PDF。
3. `memory-bank/design-document.md` 新增竞争态势总览页说明，并把画像、图谱、报告、证据与过程追踪章节改为 2.0 中文信息架构。
4. `memory-bank/design-document.md` 更新 API 表，加入 `GET /tasks/{task_id}/overview` 和 `GET /tasks/{task_id}/report/docx`，移除 Markdown 作为正式导出入口。
5. `memory-bank/tech-stack.md` 将当前依赖口径同步为 `python-docx` 和 `Pillow`，记录 Word 导出和简化竞争关系图生成，并保留禁止引入复杂基础设施的约束。
6. `memory-bank/tech-stack.md` 将启动命令改为相对项目根目录的 `cd backend` / `cd frontend` 描述。
7. 新增 API 契约说明，记录 2.0 核心 API、任务流、Word 报告交付、Trace 契约和安全合规契约。
8. `memory-bank/architecture.md` 已包含 Overview、DOCX、简化关系图、证据与过程追踪、Word API、OpenAPI 类型同步和安全回归的架构记录；本步骤复核并保留这些记录。

### 验证结果

1. `rg -n "Markdown 导出|后端导出 Markdown|正式.*Markdown|Markdown 足够|导出的 Markdown|Markdown 报告默认|GET \`/tasks/\{task_id\}/report/markdown\` \| 导出|Markdown 作为正式" memory-bank\design-document.md memory-bank\tech-stack.md docs\api-contract.md`：通过；当前文档不再把 Markdown 作为正式交付。
2. `rg -n "D:\\|C:\\" memory-bank\design-document.md memory-bank\tech-stack.md docs\api-contract.md`：通过；当前设计、技术栈和 API 文档没有新增本机绝对路径。
3. `rg -n "Overview|overview|DOCX|docx|Word|Pillow|python-docx|禁止|不引入|Celery|Redis|PostgreSQL|Next.js|Redux|Tailwind|相对于项目根目录|路径" memory-bank\design-document.md memory-bank\tech-stack.md memory-bank\architecture.md docs\api-contract.md`：通过；文档包含 Overview、DOCX、Pillow/python-docx 和禁止引入项记录。
4. `git diff --check -- memory-bank\design-document.md memory-bank\tech-stack.md memory-bank\architecture.md memory-bank\progress.md docs\api-contract.md`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 38。
2. 本步骤只更新文档和架构记录，不改变后端 API、OpenAPI Schema、前端页面、LangGraph DAG、四 Agent、QA 打回、Human Review、Word 导出实现或冻结 Demo 数据。
3. 本步骤没有引入新依赖、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 38 后端完整回归完成

### 当前完成情况

v2 实施计划步骤 38 已完成。本步骤运行后端全量 Pytest 和 Ruff，并修复全量回归暴露的历史 Markdown 服务测试与 2.0 报告结构不一致问题。

已完成实现：

1. `backend/app/services/markdown_renderer.py` 的历史 Markdown 渲染服务兼容 2.0 `core_competitor_analysis`、`product_strategy_recommendations` 和 `evidence_quality_appendix`。
2. `evidence_quality_appendix` 中的 `appendix_type=evidence_index` 会被历史 Markdown 服务识别并渲染 Evidence 索引，保持安全和可追溯回归可测。
3. `backend/tests/test_markdown_renderer.py` 从旧九章节断言更新为 2.0 八章节断言。
4. Markdown 历史服务测试继续覆盖 Claim/Evidence、置信度、访问时间、“暂无可靠数据”和敏感信息脱敏，但不再代表 2.0 正式交付入口。

### 验证结果

1. 首次 `backend\.conda312\python.exe -m pytest backend\tests` 发现 `backend/tests/test_markdown_renderer.py` 仍按旧九章节和旧字段断言，4 个测试失败；修复后已复跑通过。
2. `backend\.conda312\python.exe -m pytest backend\tests\test_markdown_renderer.py backend\tests\test_reports_api.py backend\tests\test_word_report_service.py backend\tests\test_v2_security_compliance.py`：通过，18 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\services\markdown_renderer.py backend\tests\test_markdown_renderer.py`：通过。
4. `backend\.conda312\python.exe -m pytest backend\tests`：通过，237 个测试通过。
5. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
6. `git diff --check -- backend\app\services\markdown_renderer.py backend\tests\test_markdown_renderer.py memory-bank\progress.md memory-bank\architecture.md`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 39。
2. 本步骤只修复后端回归中暴露的历史 Markdown 服务兼容测试，不恢复 Markdown 用户可见导出入口。
3. 本步骤没有改变 Word `.docx` 正式交付、OpenAPI Schema、前端页面、LangGraph DAG、四 Agent、QA 打回、Human Review 或冻结 Demo 数据。
4. 本步骤没有引入新依赖、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 39 前端完整回归完成

### 当前完成情况

v2 实施计划步骤 39 已完成。本步骤运行前端全量 Vitest、ESLint、Prettier、TypeScript 和生产构建，确认中文化、响应式和 Word 导出入口回归仍通过。

### 验证结果

1. 首次 `$env:VITE_CACHE_DIR='.vite-cache-codex'; npm run test` 命中 Codex 沙箱 `/@fs/D:/...` 路径映射问题，7 个测试文件导入失败、0 个测试执行；按既有处理方式单独重跑同一命令后通过。
2. `$env:VITE_CACHE_DIR='.vite-cache-codex'; npm run test`（重跑，工作目录 `frontend/`）：通过，7 个测试文件、81 个测试通过。
3. `npm run lint`（工作目录 `frontend/`）：通过。
4. `npm run format:check`（工作目录 `frontend/`）：通过。
5. `npx tsc --noEmit`（工作目录 `frontend/`）：通过。
6. `npm run build -- --outDir ..\.codex-run\frontend-dist-step39-verify --emptyOutDir false`（工作目录 `frontend/`）：通过；仅有 Vite chunk 大于 500 kB 的既有警告。
7. `git diff --check -- frontend memory-bank\progress.md memory-bank\architecture.md`：通过，仅有 Windows CRLF 提示。

### 本步边界

1. 本步骤没有开始 v2 步骤 40。
2. 本步骤只执行前端完整回归，不改变前端功能、后端 API、OpenAPI Schema、LangGraph DAG、四 Agent、QA 打回、Human Review、Word 导出实现或冻结 Demo 数据。
3. 本步骤没有引入新依赖、外部采集、模型必需链路、Redux、Next.js、Tailwind、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 40 E2E 与冻结回归完成

### 当前完成情况

v2 实施计划步骤 40 已完成。本步骤完成 2.0 全路径 Playwright 回归、冻结 Demo 文档更新、冻结快照校验、前后端质量门禁复核和安全/架构边界确认。

已完成实现：

1. 冻结演示口径已更新为 2.0，记录输入页、竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪、Word `.docx` 下载和旧 Markdown 路由不可用的验收路径。
2. `frontend/e2e/demo-path.e2e.spec.ts` 使用动态后端端口和 4100-4199 范围内的前端端口，避免组合 Playwright 回归中端口占用和 CORS 白名单冲突。
3. `frontend/e2e/responsive.visual.spec.ts` 的 mock 路由改为覆盖带查询参数的 2.0 页面请求，保证画像、报告和追踪页在响应式视觉用例中稳定命中 fixture。
4. `frontend/src/App.tsx` 将任务提交摘要中的默认跳转说明同步为“竞争态势总览”，与 2.0 创建任务后默认页面一致。
5. 冻结快照 `data/snapshots/demo_sku_snapshot.json` 未改动，SHA256 仍为 `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`。

### 验证结果

1. `npm run test:e2e -- task-flow.e2e.spec.ts qa-revision.e2e.spec.ts demo-path.e2e.spec.ts responsive.visual.spec.ts overview.visual.spec.ts battlefield.visual.spec.ts profile.visual.spec.ts report.visual.spec.ts trace.visual.spec.ts`（工作目录 `frontend/`）：通过，9 个 Playwright 用例通过；仅有 Vite chunk 大于 500 kB 的既有警告。
2. `backend\.conda312\python.exe -m pytest backend\tests`：通过，237 个测试通过，覆盖冻结 Demo、DOCX、Overview、Battlefield、Profile、Trace、QA 打回、Human Review、安全合规和旧 Markdown 路由不可用回归。
3. `Get-FileHash data\snapshots\demo_sku_snapshot.json -Algorithm SHA256`：通过，哈希为 `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`。
4. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
5. `$env:VITE_CACHE_DIR='.vite-cache-codex'; npm run test -- App.test.tsx src/TermHint.test.tsx src/mocks/fixtures.test.tsx`（工作目录 `frontend/`）：通过，3 个测试文件、63 个测试通过。
6. `$env:VITE_CACHE_DIR='.vite-cache-codex'; npm run test`（工作目录 `frontend/`）：通过，7 个测试文件、81 个测试通过。
7. `npx tsc --noEmit`（工作目录 `frontend/`）：通过。
8. `npm run lint`（工作目录 `frontend/`）：通过。
9. `npm run format:check`（工作目录 `frontend/`）：通过。
10. `npm run build -- --outDir ..\.codex-run\frontend-dist-step40-verify --emptyOutDir false`（工作目录 `frontend/`）：通过；仅有 Vite chunk 大于 500 kB 的既有警告。
11. `git diff --check -- frontend\e2e\demo-path.e2e.spec.ts frontend\e2e\responsive.visual.spec.ts frontend\src\App.tsx memory-bank\progress.md memory-bank\architecture.md`：通过，仅有 Windows CRLF 提示。
12. `rg -n "report/markdown|导出 Markdown|Markdown 导出|Markdown 已导出" frontend\src frontend\e2e -g "!node_modules/**"`：通过；仅命中前端合约测试中“旧 Markdown 导出不可见”的类型断言，未发现用户可见入口。
13. `rg -n "report/markdown" backend\app backend\tests memory-bank`：通过；仅命中后端旧路由不可用回归测试和 2.0 文档说明，后端应用路由未暴露旧 Markdown 导出入口。
14. `rg -n "真实外部采集|Celery|Redis|PostgreSQL|Next\.js|Redux|Tailwind" backend\app frontend\src frontend\e2e backend\requirements-dev.txt frontend\package.json frontend\package-lock.json`：通过；仅命中 `analysis_scope_service.py` 中“未执行真实外部采集”的增强模式占位说明。
15. `rg -n "sk-[A-Za-z0-9]|api[_-]?key\s*[:=]|Bearer\s+[A-Za-z0-9]|secret\s*[:=]|password\s*[:=]" backend\app frontend\src demo docs memory-bank -g "!**/.vite-cache-codex/**"`：通过；命中均为脱敏规则说明、历史记录或测试中的假密钥样式断言，没有真实密钥。

### 本步边界

1. v2 实施计划 40 个步骤已全部完成。
2. 本步骤没有改动冻结 Demo 快照、稳定输入、默认目标 SKU 或 QA revision fixture。
3. 本步骤没有恢复 Markdown 用户可见导出入口；2.0 正式报告交付仍为网页报告、Word `.docx` 下载和浏览器打印/另存 PDF。
4. 本步骤没有改变 LangGraph DAG、四 Agent、QA 打回、Human Review、OpenAPI 契约、SQLite 存储方案或模型可选增强策略。
5. 本步骤没有新增真实外部采集、模型必需链路、Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind、微服务、后端 PDF 服务或其他未批准技术栈。
