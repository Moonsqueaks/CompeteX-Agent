# 项目进度记录

## 当前总览

截至 2026-05-25，实施计划已按顺序完成步骤 01 到步骤 17；步骤 18 尚未开始，需等待用户验证步骤 17 测试后再继续。

当前边界：

1. 已完成项目骨架、质量工具、统一 API 响应、核心 Schema、SQLite 存储层、最终 Demo 快照规范、Snapshot Loader、任务创建 API、任务状态查询 API、LangGraph 状态对象、Collection Agent 节点、CompetitionEdgeScore 评分服务、Analysis Agent 节点、QA 规则服务、QA Agent 节点、QA 打回后的 Collection 修复逻辑和 QA 打回后的 Analysis 局部重算逻辑。
2. `data/raw/` 中的真实脱敏 SKU 原始素材已作为步骤 06 的素材来源保留。
3. `data/snapshots/demo_sku_snapshot.json` 是 Snapshot Loader 的正式快照输入契约。
4. `POST /tasks` 已可创建任务并写入 SQLite，`GET /tasks/{task_id}` 已可查询任务基础状态，`TaskGraphState` 已可从任务初始化并追加核心 Artifact，`collection_agent_node` 已可读取本地快照并写入 Product、Evidence、ReviewInsight 和 Trace 日志，也可在 QA 打回后再次运行并补齐或标记 Collection 证据，评分服务已可输出五维解释分和切片排序，`analysis_agent_node` 已可生成目标画像、Claim 和 CompetitionEdge，也可在 QA 打回 Analysis 后只重算受影响 Claim/CompetitionEdge 并保留无关边，`run_qa_rules` 已可输出结构化 ReviewTask，`qa_agent_node` 已可输出通过状态或结构化 `revision_request`。
5. 尚未实现完整 Agent DAG、Writer Agent 或报告导出。
6. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
7. 未写入真实 API Key，未在 Trace、日志或文档中记录密钥。

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

## 下一步边界：等待用户验证测试后再进入步骤 18

在用户验证步骤 17 测试前，不开始实施计划步骤 18。

步骤 18 边界提醒：

1. 下一步才是组装 LangGraph 主流程。
2. 步骤 18 需要配置 QA 通过到 Writer、QA 打回到 Collection 和 Analysis 的条件边。
3. 步骤 18 才能设置最大打回次数，避免无限循环。
4. 步骤 18 仍不实现 Writer Agent 或 Markdown 导出，除非实施计划明确到对应步骤。
5. 继续禁止引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
