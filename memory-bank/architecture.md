# 系统架构记录

## 2026-05-23：工程与质量基线

当前项目处于实施计划步骤 02 完成后的工程基线状态，尚未进入步骤 03 的统一 API 响应与错误格式实现。

### 当前目录基线

1. `backend/`：FastAPI 后端骨架，包含 `app/main.py` 健康检查、基础包目录和 Pytest 测试目录。
2. `frontend/`：Vite + React + TypeScript 前端骨架，包含默认应用壳、Vitest + Testing Library 测试配置。
3. `data/`：用户提供的脱敏 Demo 原始素材和草稿快照目录。
4. `docs/`、`demo/`：预留文档和演示材料目录。
5. `memory-bank/`：项目设计、技术栈、实施计划、架构和进度记录。

### 后端质量基线

1. 后端使用项目内 Conda 环境 `backend/.conda312` 运行质量检查，Python 版本为 3.12.13。
2. `backend/pyproject.toml` 管理 Pytest 和 Ruff 配置。
3. 测试环境通过 `backend/.env.test` 和 `backend/tests/conftest.py` 加载，不依赖真实模型 API Key。
4. 当前已验证 `ruff check backend` 和 `pytest backend` 通过。

### 前端质量基线

1. 前端继续使用 Vite React TypeScript，不引入 Next.js、Redux 或 Tailwind。
2. `frontend/eslint.config.js` 管理 ESLint、TypeScript ESLint、React Hooks 和 React Refresh 检查。
3. `frontend/.prettierrc.json` 管理 Prettier 格式。
4. 当前已验证 `npm --prefix frontend run lint`、`test`、`build` 和 `format:check` 通过。

### 未开始事项

1. 尚未实现统一 API 响应结构。
2. 尚未实现统一错误对象。
3. 尚未实现任何业务 Schema、存储层、Agent DAG 或前端业务页面。

## 2026-05-23：步骤 03 统一 API 响应与错误格式

当前项目已完成实施计划步骤 03，后端 API 具备统一响应外壳和标准错误对象；尚未进入步骤 04 的核心业务 Pydantic Schema。

### 后端响应契约

1. 新增 `backend/app/schemas/api_response.py`，定义通用 `ApiResponse` 与 `ApiError`。
2. 所有成功响应统一包含 `data`、`error`、`trace_id`，成功时 `error` 为 `null`。
3. 所有错误响应统一包含 `data`、`error`、`trace_id`，错误时 `data` 为 `null`。
4. `ApiError` 固定包含 `code`、`message`、`details`。

### Trace 与异常处理

1. 新增 `backend/app/api/responses.py`，集中提供响应构造、`ApiException`、Trace ID 中间件和异常处理器。
2. 每个请求都会生成或透传合法的 `X-Trace-Id`，并在响应体与响应头中保持一致。
3. 已接管 `ApiException`、HTTP 异常、请求校验异常和未捕获异常，返回标准错误格式。
4. 错误详情会进行基础敏感信息脱敏，避免返回 API Key、Token、Secret、Password 等内容或对应环境变量原文。

### 当前 API 状态

1. `/health` 已改为统一响应结构，返回 `{"data":{"status":"ok"},"error":null,"trace_id":"..."}`。
2. 不存在路径的 404 响应已改为统一错误结构，错误码为 `NOT_FOUND`。
3. 尚未定义 `AnalysisTask`、`Product`、`Evidence`、`Claim`、`CompetitionEdge` 等步骤 04 业务 Schema。

## 2026-05-23：步骤 04 核心 Pydantic Schema

当前项目已完成实施计划步骤 04，后端具备核心业务 Schema、枚举约束和基础风险校验；尚未进入步骤 05 的 SQLite 存储层。

### Schema 分层

1. 新增 `backend/app/schemas/common.py`，集中定义任务状态、Agent 名称、数据来源、风险标记、Claim 状态、竞争关系类型、决策阶段、审查状态、反馈动作和运行日志状态等枚举。
2. 新增 `backend/app/schemas/task.py`，定义 `AnalysisTask`。
3. 新增 `backend/app/schemas/agent_message.py`，定义结构化 `AgentMessage`。
4. 新增 `backend/app/schemas/product.py`，定义 `Product`、`FeatureTree`、`PricingModel`、`UserPersona`。
5. 新增 `backend/app/schemas/evidence.py`，定义 `Evidence`。
6. 新增 `backend/app/schemas/claim.py`，定义 `Claim`。
7. 新增 `backend/app/schemas/competition.py`，定义 `CompetitionSlice`、`ScoreBreakdown`、`CompetitionEdge`。
8. 新增 `backend/app/schemas/review.py`，定义 `ReviewTask` 与 `HumanFeedback`。
9. 新增 `backend/app/schemas/trace.py`，定义 `AgentRunLog`、`ToolCallLog`、`TokenUsageLog`。

### 当前 Schema 契约

1. 字段命名统一使用 `snake_case`，并通过测试覆盖。
2. 核心对象使用 Pydantic v2 校验，禁止未声明字段进入业务对象。
3. `Claim` 在缺少 `evidence_ids` 时不会校验失败，但会自动标记 `missing_evidence`，并将状态改为 `needs_review`，供后续 QA 流程处理。
4. `CompetitionEdge.edge_score` 和 `ScoreBreakdown` 五个维度均限制在 `0` 到 `1`。
5. `TokenUsageLog.total_tokens` 必须等于 `prompt_tokens + completion_tokens`。
6. 当前 Schema 可被 FastAPI 纳入 OpenAPI 文档生成。

### 未开始事项

1. 尚未建立 SQLite 数据库连接、数据表或 Repository。
2. 尚未定义 Snapshot Loader、Agent DAG、任务 API 或报告导出。
3. 尚未对真实 Demo 快照执行结构化加载，步骤 04 只完成业务协议层。

## 2026-05-23：步骤 05 SQLite 存储层

当前项目已完成实施计划步骤 05，后端具备 SQLite + SQLAlchemy 存储层、基础表结构和 Repository 访问边界；按用户要求，尚未继续进入步骤 06。

### 存储层结构

1. 新增 `backend/app/storage/db.py`，集中提供数据库 URL 解析、SQLite Engine 创建、Session Factory、初始化和测试清理入口。
2. 默认数据库路径为 `<project-root>/data/competitive_intelligence.db`；测试通过显式临时 SQLite 路径运行，避免污染真实数据目录。
3. 新增 `backend/app/storage/models.py`，定义四类轻量表：
   - `analysis_tasks`：保存任务基础信息和状态。
   - `artifact_json`：保存 Evidence、Claim、CompetitionEdge 等结构化 Artifact JSON。
   - `trace_logs`：保存 Agent Run、Tool Call、Token Usage 等 Trace/运行日志 JSON。
   - `human_feedback`：保存人工反馈及前后值。
4. 新增 `backend/app/storage/repositories.py`，提供 `TaskRepository`、`ArtifactRepository`、`TraceLogRepository` 和 `HumanFeedbackRepository`，API 路由后续不得直接操作数据库表。
5. 新增 `.gitignore` 规则忽略 `data/*.db`、`data/*.sqlite`、`data/*.sqlite3`，避免本地 SQLite 运行产物入库。

### 当前存储契约

1. 任务可以创建、读取并更新状态，状态值仍使用步骤 04 的 `TaskStatus` 枚举。
2. Artifact 使用统一 JSON 表保存，当前已验证 Evidence、Claim、CompetitionEdge 可按任务 ID 和类型保存、读取、列表查询。
3. Trace 使用统一日志表保存，当前已验证 AgentRunLog、ToolCallLog、TokenUsageLog 可按任务 ID 查询。
4. HumanFeedback 独立入表，保留目标对象、动作、before/after 和原因。
5. Repository 接收和返回 Pydantic Schema，数据库 JSON 只作为持久化载体，不绕过 Schema 校验。

### 未开始事项

1. 尚未开始步骤 06 的本地 Demo 快照数据规范整理。
2. 尚未实现 Snapshot Loader、任务 API、Agent DAG、QA 打回链路或报告导出。
3. 尚未在 FastAPI 路由中接入 Repository。

## 2026-05-23：步骤 06 本地 Demo 快照数据规范

当前项目已完成实施计划步骤 06，本地 Demo 快照已从草稿素材整理为可校验的最终数据契约；按用户要求，尚未开始步骤 07 的 Snapshot Loader 实现。

### 快照文件结构

1. 新增 `data/snapshots/README.md`，定义最终 Demo 快照文件结构、字段约束、QA 打回样例和步骤边界。
2. 新增 `data/snapshots/demo_sku_snapshot.json`，作为后续步骤 07 的正式输入契约。
3. 原 `data/snapshots/sku_catalog_draft.json` 保留为草稿来源，不再作为最终 Snapshot Loader 输出格式。
4. 最终快照包含 14 个 SKU，覆盖默认目标、自动猫砂盆直接竞品、需求替代方案和渠道型替代方案。
5. 每个 SKU 固定包含名称、品牌、价格、卖点、评论摘要和来源说明。

### QA 打回样例

1. `sku_01` 被固定为 QA 打回演示样例。
2. `sku_01.source.access_time` 在最终快照中故意置为 `null`，用于触发“价格证据缺少访问时间”的 QA 检查。
3. 补齐用的原始访问时间和截图路径保存在 `qa_revision_fixture.repair_evidence`，供后续 Collection 修复逻辑使用。

### 验证契约

1. 新增 `backend/tests/test_demo_snapshot_contract.py`，验证最终 Demo 快照不少于 8 个 SKU。
2. 验证每个 SKU 均满足最终快照字段契约。
3. 验证每个 SKU 均可转换为步骤 04 定义的 `Product` 和 `Evidence` Pydantic Schema。
4. 验证 QA 打回样例确实缺少指定证据字段，且保留补齐来源。
5. 验证快照引用的原始素材目录和可用截图存在。
6. 验证最终快照不包含手机号、真实账号 ID、API Key 或敏感隐私字段。

### 未开始事项

1. 尚未实现步骤 07 的 Snapshot Loader。
2. 尚未将快照转换逻辑固化为服务层代码；当前转换只存在于测试辅助函数中，用于验证数据契约。
3. 尚未实现 Collection Agent、任务 API、Agent DAG 或 QA 规则服务。

## 2026-05-24：步骤 07 快照加载服务

该里程碑完成后，后端具备正式 Snapshot Loader 服务，可读取最终 Demo 快照并转换为标准 `Product`、`Evidence` 与 `ReviewInsight`；随后已在用户确认后继续完成步骤 08，见下一节记录。

### 加载服务结构

1. 新增 `backend/app/schemas/review_insight.py`，定义轻量 `ReviewInsight`，用于承接 SKU 快照中的评论摘要与市场信号。
2. 更新 `backend/app/schemas/__init__.py`，统一导出 `ReviewInsight`。
3. 新增 `backend/app/services/snapshot_loader.py`，集中提供 `load_demo_snapshot`、`SnapshotLoadResult` 与 `SnapshotLoaderError`。
4. 更新 `backend/app/services/__init__.py`，统一导出快照加载服务入口。
5. Snapshot Loader 默认只读取 `data/snapshots/demo_sku_snapshot.json`，不读取 `sku_catalog_draft.json` 作为正式输入。

### 当前加载契约

1. 加载结果包含快照版本、品类、子类、默认目标 SKU、源文件路径、`products`、`evidences`、`review_insights` 和 `qa_revision_fixture`。
2. 每个 SKU 会转换为一个 `Product`、一个 `Evidence` 和一个 `ReviewInsight`。
3. `sku_02` 继续作为默认演示目标，转换后的 `Product.role` 保持为 `target`。
4. `sku_01.source.access_time` 继续保留为缺失，转换后的 `Evidence.access_time` 为 `None`，并在 `Evidence.metadata.missing_fields` 中记录 `source.access_time`。
5. Loader 只保留和标记缺失状态，不使用 `qa_revision_fixture.repair_evidence` 自动补齐数据；补齐逻辑仍留给后续 QA 打回后的 Collection 修复步骤。
6. 非法 JSON、缺少顶层字段、缺少 SKU 字段、默认目标不存在等问题会抛出带 `code`、`message`、`details` 的 `SnapshotLoaderError`，便于后续 API 或 Agent Trace 诊断。

### 验证契约

1. 新增 `backend/tests/test_snapshot_loader.py`，覆盖完整 Demo 快照加载、默认目标识别、缺失字段保留、Pydantic Schema 输出和非法文件诊断错误。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_snapshot_loader.py` 通过，6 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，59 个测试通过。

### 未开始事项

1. 尚未实现步骤 08 的 `POST /tasks` 任务创建 API。
2. 尚未在 FastAPI 路由中接入 Snapshot Loader 或 Repository。
3. 尚未实现 Collection Agent、Agent DAG、QA 规则服务、QA 打回修复或报告导出。

## 2026-05-24：步骤 08 任务创建 API

该里程碑完成后，后端具备 `POST /tasks` 任务创建 API，可按统一响应格式创建 `AnalysisTask` 并写入 SQLite；随后已在用户确认后继续完成步骤 09，见下一节记录。

### API 与服务结构

1. 更新 `backend/app/schemas/task.py`，新增 `TaskCreateRequest` 与 `TaskCreateResponse`。
2. 新增 `backend/app/services/task_creation.py`，封装任务创建逻辑、默认 Demo 目标选择和任务元数据生成。
3. 新增 `backend/app/api/routes_tasks.py`，提供 `POST /tasks` 路由，并通过 `TaskRepository` 写入数据库。
4. 更新 `backend/app/main.py`，在应用创建时注册任务路由，并支持测试传入临时 `database_url`。
5. 数据库连接采用按需初始化：健康检查不会创建 SQLite 文件；调用任务创建 API 时才初始化对应数据库。

### 当前任务创建契约

1. `POST /tasks` 支持 `target_product_name`、`target_product_url`、`category`、`subcategory`、`data_source_mode` 和 `research_text`。
2. 成功创建时返回统一响应结构，HTTP 状态码为 `201`，`data` 内包含 `task_id`、`status` 和完整 `task`。
3. 默认 `data_source_mode` 为 `demo_snapshot`。
4. 如果请求省略 `target_product_name` 或传入 `null`，服务会读取最终 Demo 快照并选择 `sku_02` 作为默认目标产品。
5. 如果请求显式传入空白 `target_product_name`，返回统一校验错误，避免创建空目标任务。
6. 步骤 08 只创建任务和写库，不启动 Collection Agent、LangGraph 工作流或后台任务。
7. `snapshot_plus_live` 在任务元数据中记录 MVP 降级说明，但仍不做真实外部采集。

### 验证契约

1. 新增 `backend/tests/test_tasks_api.py`，覆盖合法创建、空白目标校验、默认数据模式、默认 Demo 目标选择和统一响应结构。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_tasks_api.py` 通过，5 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，64 个测试通过。

### 未开始事项

1. 尚未实现步骤 09 的 `GET /tasks/{task_id}` 任务状态查询 API。
2. 尚未启动完整 Agent 流程或后台任务。
3. 尚未实现 Collection Agent、Agent DAG、QA 规则服务、QA 打回修复或报告导出。

## 2026-05-24：步骤 09 任务状态查询 API

该里程碑完成后，后端具备 `GET /tasks/{task_id}` 任务状态查询 API，可按统一响应格式返回任务基础状态；随后已在用户确认后继续完成步骤 10，见下一节记录。

### API 与 Schema 结构

1. 更新 `backend/app/schemas/task.py`，新增 `TaskStatusResponse`，用于任务状态轮询场景。
2. 更新 `backend/app/schemas/__init__.py`，统一导出 `TaskStatusResponse`。
3. 更新 `backend/app/api/routes_tasks.py`，新增 `GET /tasks/{task_id}` 路由，并复用 `TaskRepository` 查询 SQLite。
4. 查询不存在任务时返回标准错误结构，错误码为 `TASK_NOT_FOUND`，HTTP 状态码为 `404`。

### 当前任务状态查询契约

1. `GET /tasks/{task_id}` 返回统一响应结构，`data` 内包含任务 ID、目标产品名称、目标链接、品类、子类、数据模式、任务状态、创建时间和更新时间。
2. 状态字段继续使用 `TaskStatus` 枚举值。
3. 响应不返回完整报告、Trace、Artifact、`research_text` 或任务内部 `metadata`。
4. 任务查询接口不启动任何 Agent 流程，也不改变任务状态。

### 验证契约

1. 更新 `backend/tests/test_tasks_api.py`，覆盖已存在任务查询、不存在任务标准错误、状态枚举合法性和敏感/大型字段不返回。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_tasks_api.py` 通过，9 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，68 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 10 的 LangGraph `TaskGraphState`；当前已完成，见下一节记录。
2. 尚未启动完整 Agent 流程或后台任务。
3. 尚未实现 Collection Agent、Agent DAG、QA 规则服务、QA 打回修复或报告导出。

## 2026-05-24：步骤 10 LangGraph 状态对象

该里程碑完成后，后端具备轻量 `TaskGraphState`，可作为后续 LangGraph DAG 的共享状态容器；随后已在用户确认后继续完成步骤 11，见下一节记录。

### Graph 状态结构

1. 新增 `backend/app/graph/state.py`，定义 `TaskGraphState` TypedDict。
2. 状态字段覆盖 `task`、`products`、`evidences`、`review_insights`、`feature_trees`、`pricing_models`、`user_personas`、`claims`、`competition_edges`、`review_tasks`、`human_feedback`、`agent_messages`、`run_logs`、`tool_call_logs`、`token_usage_logs` 和 `metadata`。
3. 状态对象只保存 JSON 化后的轻量 payload；复杂字段校验仍由 `AnalysisTask`、`Product`、`Evidence`、`FeatureTree`、`PricingModel`、`UserPersona`、`Claim`、`CompetitionEdge`、`ReviewTask`、`HumanFeedback`、`AgentMessage` 和 Trace 日志等 Pydantic Artifact 负责。
4. 提供 `create_initial_state`，用于从任务对象初始化状态，并要求任务 payload 必须包含非空 `task_id`。
5. 提供 `append_product`、`append_evidence`、`append_feature_tree`、`append_pricing_model`、`append_user_persona`、`append_claim`、`append_review_task`、`append_agent_message`、`append_run_log` 等追加辅助函数，供后续 Agent 节点小步写入状态。
6. 提供 `serialize_state_for_trace`，可输出面向 Trace 展示的 JSON payload 和各类 Artifact 计数。
7. 更新 `backend/app/graph/__init__.py`，统一导出 Graph 状态对象与辅助函数。

### 当前状态契约

1. `TaskGraphState` 不启动 Agent、不读写数据库、不运行后台任务，只描述 LangGraph 节点之间传递的状态形状。
2. Pydantic Artifact 会通过 `model_dump(mode="json")` 转换为可序列化结构，枚举和时间字段会被转成 JSON 友好值。
3. 直接传入字典 payload 时，状态层只做轻量 JSON 化和 `task_id` 存在性检查，不替代 Pydantic Schema 校验。
4. `serialize_state_for_trace` 保留任务、Artifact、QA 记录、人工反馈、Agent 消息和运行日志，可作为后续 Trace API 的数据基础。

### 验证契约

1. 新增 `backend/tests/test_graph_state.py`，覆盖初始状态生成、核心 Artifact 追加、Trace 序列化和缺少任务 ID 的失败路径。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_graph_state.py` 通过，6 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，74 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 11 的 Collection Agent 节点；当前已完成，见下一节记录。
2. 尚未启动完整 Agent 流程或后台任务。
3. 尚未实现 Analysis Agent、QA 规则服务、QA 打回修复、Writer Agent 或报告导出。

## 2026-05-24：步骤 11 Collection Agent 节点

该里程碑完成后，后端具备可被 LangGraph 调用的 `collection_agent_node`，负责读取本地 Demo 快照和任务中的用户研究文本，并将标准 `Product`、`Evidence` 与 `ReviewInsight` 写入 `TaskGraphState`；随后已在用户确认后继续完成步骤 12，见下一节记录。

### Agent 节点结构

1. 新增 `backend/app/agents/collection.py`，实现 `collection_agent_node`。
2. 更新 `backend/app/agents/__init__.py`，统一导出 Collection Agent 节点。
3. Collection Agent 复用步骤 07 的 `load_demo_snapshot`，默认读取 `data/snapshots/demo_sku_snapshot.json`。
4. 节点将快照输出的 `Product`、`Evidence` 和 `ReviewInsight` 追加到 `TaskGraphState`。
5. 当任务包含 `research_text` 时，节点会额外生成一条 `user_research` 类型 Evidence，记录文本来源和字符数，但不在 Trace 摘要中展开原文。
6. 节点会记录 `AgentRunLog` 和 `ToolCallLog`，为后续 Trace API 展示 Collection 运行过程提供数据。
7. 节点会在 `state["metadata"]["collection_agent"]` 中记录快照版本、来源路径、产物数量、缺失证据字段和用户研究文本读取状态。

### 当前 Collection 契约

1. Collection Agent 只负责采集和结构化输入，不生成 Claim、CompetitionEdge、评分或最终报告。
2. `sku_01` 缺失的 `source.access_time` 继续保留为 `Evidence.access_time = None`，不会使用 `qa_revision_fixture` 自动补齐。
3. 缺失证据字段会写入 Evidence metadata，并汇总进入 Collection Agent metadata，供后续 QA 与 Trace 使用。
4. Snapshot Loader 失败时，节点会记录失败的 Tool Call 和 Agent Run，再抛出原始 `SnapshotLoaderError`。
5. 当前节点只写入内存 Graph State，不读写 SQLite，不启动后台任务，不组装完整 LangGraph 工作流。

### 验证契约

1. 新增 `backend/tests/test_collection_agent.py`，覆盖 Collection Agent 成功采集、证据关联、缺失访问时间保留、Trace 日志和用户研究 Evidence。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_collection_agent.py` 通过，5 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，79 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 12 的 CompetitionEdgeScore 评分服务；当前已完成，见下一节记录。
2. 尚未实现 Analysis Agent、QA 规则服务、QA 打回修复、Writer Agent 或报告导出。
3. 尚未组装完整 LangGraph DAG 或后台任务执行链路。

## 2026-05-24：步骤 12 CompetitionEdgeScore 评分服务

该里程碑完成后，后端具备独立五维规则评分服务，可为后续 Analysis Agent 生成 `CompetitionEdge` 提供 `edge_score`、`ScoreBreakdown` 和可解释维度说明；随后已在用户确认后继续完成步骤 13，见下一节记录。

### 评分服务结构

1. 新增 `backend/app/services/scoring.py`，实现 CompetitionEdgeScore 规则评分服务。
2. 更新 `backend/app/services/__init__.py`，导出评分服务入口、权重和结果对象。
3. 评分服务提供 `calculate_competition_edge_score`，输入目标产品、竞品产品、当前切片、Evidence 和 ReviewInsight，输出 `CompetitionScoreResult`。
4. 评分服务提供 `rank_competitors_by_score`，用于按当前切片对候选竞品进行纯评分排序；该函数不生成 `CompetitionEdge`。
5. 新增轻量结果对象 `DimensionScore`、`CompetitionScoreResult` 和 `ScoredCompetitor`，用于承载每维分数、权重、原因和信号。
6. 总分严格按文档权重聚合：需求替代性 0.30、上下文匹配度 0.25、决策阶段影响力 0.20、证据置信度 0.15、市场信号强度 0.10。

### 当前评分契约

1. 评分维度固定为 `demand_substitutability`、`context_match`、`decision_stage_impact`、`evidence_confidence` 和 `market_signal_strength`。
2. 每个维度分数和总分均限制在 `0` 到 `1`。
3. 每个维度都会返回可解释 `reasons` 和用于排查的 `signals`。
4. 证据置信度会综合 Evidence 的 `confidence_level`、来源 URL、截图路径、访问时间和 `missing_fields`；缺失访问时间会降低分数。
5. 市场信号优先读取 Evidence metadata 或 ReviewInsight market_signals 中的 sales 字段，并按区间转为稳定规则分。
6. 上下文匹配会结合价格带、人群和场景；不同切片可以改变竞品排序。
7. 当前服务不创建 Claim、不创建 CompetitionEdge、不实现 Analysis Agent、不组装完整 DAG，也不调用模型或复杂预测算法。

### 验证契约

1. 新增 `backend/tests/test_scoring.py`，覆盖权重聚合、维度范围、低证据置信度降分和不同切片排序变化。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_scoring.py` 通过，4 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，83 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 13 的 Analysis Agent 节点；当前已完成，见下一节记录。
2. 尚未实现 QA 规则服务、QA 打回修复、Writer Agent 或报告导出。
3. 尚未组装完整 LangGraph DAG 或后台任务执行链路。

## 2026-05-24：步骤 13 Analysis Agent 节点

该里程碑完成后，后端具备可被 LangGraph 调用的 `analysis_agent_node`，可基于 Collection 输出和第 12 步评分服务生成目标产品画像、竞争关系 Claim 和 `CompetitionEdge`；随后已在用户确认后继续完成步骤 14，见下一节记录。

### Agent 节点结构

1. 新增 `backend/app/agents/analysis.py`，实现 `analysis_agent_node`。
2. 更新 `backend/app/agents/__init__.py`，统一导出 Analysis Agent 节点。
3. 更新 `backend/app/graph/state.py` 和 `backend/app/graph/__init__.py`，补充 `FeatureTree`、`PricingModel` 和 `UserPersona` 的状态字段与追加函数。
4. Analysis Agent 会从 `TaskGraphState` 读取 `Product`、`Evidence` 和 `ReviewInsight`，定位 `target` 产品。
5. 节点会为目标产品生成 `FeatureTree`、`PricingModel` 和 `UserPersona`，并绑定目标 Evidence ID；找不到可靠证据的字段写入“暂无可靠数据”或风险标记。
6. 节点会召回直接竞品、需求替代品和内容共现候选，并调用 `calculate_competition_edge_score` 生成 `ScoreBreakdown` 与总分。
7. 节点会为每条竞争边生成对应 Claim；核心 Claim 绑定目标和竞品 Evidence ID，缺少竞品证据时标记 `missing_evidence` 并进入 `needs_review`。
8. 节点会记录 `AgentRunLog`，并在 `state["metadata"]["analysis_agent"]["edge_explanations"]` 中保存每条边的评分解释，供后续 Trace 展示。

### 当前 Analysis 契约

1. Analysis Agent 只读写内存 Graph State，不读写 SQLite，不启动后台任务，不组装完整 LangGraph 工作流。
2. 竞争关系类型覆盖 `direct`、`alternative`、`channel` 和 `content_cooccurrence`；当前 Demo 快照会生成 13 条目标对竞品边。
3. 每条 `CompetitionEdge` 均包含切片、决策阶段、总分、五维评分拆解和 Claim 引用。
4. 当前节点不创建 `ReviewTask`，不执行 QA 打回，不修复 Collection 证据，不生成报告。
5. 推断型用户画像与竞争判断通过 `is_inference=True` 或 Claim 内容显式标记为推断。

### 验证契约

1. 新增 `backend/tests/test_analysis_agent.py`，覆盖目标画像生成、直接/替代/渠道竞品召回、边的切片与评分解释、缺证据风险和不启动 QA 步骤。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_analysis_agent.py backend\tests\test_graph_state.py` 通过，11 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，88 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 14 的 QA 规则服务；当前已完成，见下一节记录。
2. 尚未实现 QA Agent、QA 打回修复、Writer Agent、Markdown 导出或完整 LangGraph DAG。
3. 尚未把 Collection 与 Analysis 节点接入任务后台执行链路。

## 2026-05-24：步骤 14 QA 规则服务

该里程碑完成后，后端具备纯规则型 `run_qa_rules` 服务，可审查 Claim、Evidence 与 CompetitionEdge 并输出结构化 `ReviewTask`；随后已在用户确认后继续完成步骤 15，见下一节记录。

### 服务结构

1. 新增 `backend/app/services/qa_rules.py`，实现 `run_qa_rules`。
2. 更新 `backend/app/services/__init__.py`，导出 QA 规则服务入口。
3. `run_qa_rules` 输入 `task_id`、Claim 列表、Evidence 列表、可选 CompetitionEdge 列表和检查时间，输出 `ReviewTask` 列表。
4. 服务只做确定性规则检查，不读写 SQLite，不修改 `TaskGraphState`，不生成 `AgentMessage` 或 `revision_request`。
5. ReviewTask 的 `target_agent` 会按问题归因标记为 `collection_agent` 或 `analysis_agent`，供后续 QA Agent 使用。

### 当前 QA 规则契约

1. 证据完整性：Claim 缺少 `evidence_ids` 或引用不存在的 Evidence 会生成 `ReviewTask`。
2. 时效字段：价格、评分、评价数、销量、排名等时效类证据缺少 `access_time` 时打回 Collection。
3. 截图证据：关键价格或认证信息缺少 `screenshot_path` 时打回 Collection。
4. 推断标注：包含推断或竞争判断但未设置 `is_inference=true` 的 Claim 会打回 Analysis。
5. 敏感表达：宠物安全、电器安全或医疗相关绝对化表达会生成保守表述审查任务。
6. 评论聚类：将单条或样本过少评论概括为普遍用户结论会生成风险任务。
7. 前后矛盾与边风险：Claim 或 CompetitionEdge 的冲突风险、缺证据风险、低证据置信度、缺少 Claim 绑定等会生成对应 `ReviewTask`。

### 验证契约

1. 新增 `backend/tests/test_qa_rules.py`，覆盖缺证据 Claim、缺少价格访问时间、缺少关键截图、推断未标注、单条评论过度概括、敏感绝对表达、竞争边风险和合格 Claim 通过。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_qa_rules.py` 通过，8 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，96 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 15 的 QA Agent 节点；当前已完成，见下一节记录。
2. 尚未配置 QA 通过或打回条件边。
3. 尚未实现 QA 打回后的 Collection 修复、Analysis 重算、Writer Agent、Markdown 导出或完整 LangGraph DAG。

## 2026-05-24：步骤 15 QA Agent 节点

当前项目已完成实施计划步骤 15，后端具备可被 LangGraph 调用的 `qa_agent_node`，可调用第 14 步 QA 规则服务审查当前状态，并在失败时输出结构化 `revision_request`；随后已在用户确认后继续完成步骤 16，见下一节记录。

### Agent 节点结构

1. 新增 `backend/app/agents/qa.py`，实现 `qa_agent_node`。
2. 更新 `backend/app/agents/__init__.py`，统一导出 QA Agent 节点。
3. QA Agent 从 `TaskGraphState` 读取 Claim、Evidence 和 CompetitionEdge，调用 `run_qa_rules`。
4. QA 通过时不创建 ReviewTask 或 AgentMessage，只在 `state["metadata"]["qa_agent"]` 中写入 `qa_status=passed`，并记录成功 `AgentRunLog`。
5. QA 失败时将规则服务输出的 `ReviewTask` 追加到 `state["review_tasks"]`。
6. QA 失败时按目标 Agent 分组生成 `AgentMessage`，消息类型为 `revision_request`，接收方只允许 `collection_agent`、`analysis_agent` 或 `writer_agent`。
7. QA Agent 会在 metadata 中记录 `review_task_ids`、`revision_targets`、`issue_counts` 和 `severity_counts`，供后续 Trace API 展示。

### 当前 QA Agent 契约

1. QA Agent 只做审查与打回消息生成，不修复 Evidence、不重跑 Collection、不重跑 Analysis、不写报告。
2. 当存在 Collection 目标问题时，`revision_target` 优先为 `collection_agent`；否则按 Analysis、Writer 顺序选择主打回目标。
3. `revision_request` payload 包含 QA 状态、目标 Agent、ReviewTask ID、issue code、严重级别统计、required action 和具体问题目标。
4. QA 失败时 AgentRunLog 状态为 `requires_revision`；QA 通过时状态为 `succeeded`。
5. 当前节点只写入内存 Graph State，不读写 SQLite，不配置 LangGraph 条件边。

### 验证契约

1. 新增 `backend/tests/test_qa_agent.py`，覆盖合格数据通过、缺少价格访问时间打回 Collection、分析矛盾打回 Analysis，以及 Trace metadata 中的检查项、严重级别和打回目标。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend\tests\test_qa_agent.py backend\tests\test_qa_rules.py` 通过，12 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。
4. 当前已验证 `backend\.conda312\python.exe -m pytest backend` 通过，100 个测试通过。

### 当时未开始事项

1. 当时尚未实现步骤 16 的 QA 打回后的 Collection 修复逻辑；当前已完成，见下一节记录。
2. 尚未实现 QA 打回后的 Analysis 重算、Writer Agent、Markdown 导出或完整 LangGraph DAG。

## 2026-05-24：步骤 16 QA 打回后的 Collection 修复逻辑

当前项目已完成实施计划步骤 16，`collection_agent_node` 支持在 QA Agent 发出面向 Collection 的 `revision_request` 后再次运行，并基于 Demo 快照修复夹具补齐可补齐证据；按用户要求，在用户测试前不会进入步骤 17 的 QA 打回后的 Analysis 局部重算。

### Agent 修复结构

1. 更新 `backend/app/agents/collection.py`，在初次采集路径之外新增 QA 打回复修分支。
2. Collection 初次运行仍只读取快照并保留缺失字段，不使用 `qa_revision_fixture` 自动补齐。
3. 当 `TaskGraphState.agent_messages` 中存在 QA 发给 Collection、状态为 `requires_revision` 的 `revision_request` 时，Collection 再次运行会进入修复分支。
4. 修复分支复用 `load_demo_snapshot` 读取 `qa_revision_fixture`，并通过 `snapshot_repair_fixture` ToolCallLog 记录修复来源。
5. 可补齐字段会生成新的 Evidence，而不是覆盖原 Evidence；新 Evidence 通过 `metadata.repaired_from_evidence_id` 指向原始证据。
6. `sku_01` 的 `source.access_time` 会由 `qa_revision_fixture.repair_evidence.access_time` 补齐，新 Evidence 保留原截图路径并移除已修复的 `metadata.missing_fields`。
7. 无法从本地 Demo 快照补齐的字段会生成新 Evidence，并在 `content_summary`、`limitations` 和 metadata 中明确写入“暂无可靠数据”。

### Trace 与差异记录

1. 修复结果会写入 `state["metadata"]["collection_agent_repair"]`，并同步追加到 `state["metadata"]["collection_agent"]["repair_runs"]`。
2. 每条修复记录包含 `target_evidence_id`、`new_evidence_id`、`status`、`repaired_fields`、`unavailable_fields`、`before` 和 `after`，供后续 Trace API 查询前后差异。
3. 修复后的 Evidence ID 会追加到对应 Product 的 `evidence_ids`，为后续步骤 17 的 Analysis 局部重算提供输入。
4. 被处理的 QA `revision_request` 消息状态会从 `requires_revision` 更新为 `processed`，payload 中记录 Collection 修复产生的新 Evidence ID 和 diff 数量。
5. 修复运行会追加第二条 Collection `AgentRunLog`，输出修复目标数、已修复数、不可补齐数和 diff 数量。

### 验证契约

1. 更新 `backend/tests/test_collection_agent.py`，覆盖 QA 打回 Collection 后再次执行 Collection、补齐访问时间、补齐后 Evidence 与 Product 关联、不可补齐字段写入“暂无可靠数据”，以及 Trace metadata 可查询 before/after diff。
2. 当前已验证 `backend\.conda312\python.exe -m pytest backend/tests/test_collection_agent.py backend/tests/test_qa_agent.py backend/tests/test_analysis_agent.py` 通过，16 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -m pytest backend/tests` 通过，102 个测试通过。
4. 当前已验证 `backend\.conda312\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp` 通过，103 个测试通过。
5. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 尚未实现步骤 17 的 QA 打回后的 Analysis 局部重算。
2. 尚未让 Analysis 自动消费修复后的 Evidence 重新生成受影响 Claim、CompetitionEdge 或评分。
3. 尚未实现 Writer Agent、Markdown 导出、完整 LangGraph DAG 或后台任务执行链路。

## 2026-05-25：步骤 17 QA 打回后的 Analysis 局部重算

当前项目已完成实施计划步骤 17，`analysis_agent_node` 支持在 QA Agent 发出面向 Analysis 的 `revision_request` 后再次运行，并只重算被打回的 Claim 或 CompetitionEdge；按用户要求，在用户验证测试前不会进入步骤 18 的 LangGraph 主流程组装。

### Agent 重算结构

1. 更新 `backend/app/agents/analysis.py`，在初次分析路径之外新增 QA 打回后的局部重算分支。
2. Analysis 初次运行仍保持原行为：生成目标产品画像、Claim、CompetitionEdge 和评分解释，不启动 QA、不写报告、不组装完整 DAG。
3. 当 `TaskGraphState.agent_messages` 中存在 QA 发给 Analysis、状态为 `requires_revision` 的 `revision_request` 时，Analysis 再次运行会进入重算分支。
4. 重算分支会解析消息 payload 中的 Claim 与 CompetitionEdge 目标，只替换受影响的 `claims` 和 `competition_edges`，不会追加整批重复产物。
5. 如果 Collection 已在步骤 16 生成修复 Evidence，Analysis 会在重算评分时使用当前状态中的最新 Evidence 集合，并把修复后的 Evidence ID 纳入重算 Claim。
6. 重算后的 Claim 会移除已处理的分析冲突风险；证据充足时状态回到 `accepted`，证据不足时仍保留 `needs_review` 和风险标记。
7. 重算后的 CompetitionEdge 会更新 `edge_score`、`score_breakdown`、`decision_stages`、`risk_flags` 和对应 `edge_explanations`。

### Trace 与差异记录

1. 重算结果会写入 `state["metadata"]["analysis_agent_recompute"]`，并同步追加到 `state["metadata"]["analysis_agent"]["recompute_runs"]`。
2. 每次重算记录包含 `revision_message_ids`、`target_claim_ids`、`target_edge_ids`、`recomputed_claim_ids`、`recomputed_edge_ids`、`unaffected_edge_ids`、边 diff 和 Claim diff。
3. 被处理的 QA `revision_request` 消息状态会从 `requires_revision` 更新为 `processed`，payload 中记录 Analysis 重算产生的 Claim ID、CompetitionEdge ID 和 run ID。
4. 重算运行会追加第二条 Analysis `AgentRunLog`，输出重算 Claim 数、重算竞争边数和未受影响边数。
5. 无关竞争边在列表中保持原样，便于后续 Trace API 展示局部重算的影响范围。

### 验证契约

1. 更新 `backend/tests/test_analysis_agent.py`，覆盖 QA 打回 Analysis 后再次执行 Analysis、被打回 Claim 状态变化、Collection 修复 Evidence 参与 CompetitionEdgeScore 重算，以及无关竞争边保持稳定。
2. 当前已验证 `backend\.conda312\python.exe -B -m pytest backend\tests\test_analysis_agent.py -p no:cacheprovider` 通过，6 个测试通过。
3. 当前已验证 `backend\.conda312\python.exe -B -m pytest backend\tests\test_analysis_agent.py backend\tests\test_collection_agent.py backend\tests\test_qa_agent.py -p no:cacheprovider` 通过，17 个测试通过。
4. 当前已验证 `backend\.conda312\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 尚未实现步骤 18 的 LangGraph 主流程组装。
2. 尚未配置 QA 通过到 Writer、QA 打回到 Collection 或 Analysis 的真实 LangGraph 条件边。
3. 尚未实现最大打回次数控制、Writer Agent、Markdown 导出或后台任务执行链路。

## 2026-05-26：步骤 18 LangGraph 主流程组装

当前项目已完成实施计划步骤 18，后端具备真实 LangGraph 主流程，可将 Collection、Analysis、QA 和 Writer checkpoint 串为可执行状态图；按用户要求，尚未开始步骤 19 的真正 Writer Agent。

### Workflow 文件职责

1. `backend/app/graph/workflow.py`：第 18 步新增的主流程编排文件，负责构建 LangGraph `StateGraph`、注册节点、配置条件边、控制最大打回次数和记录 workflow metadata。
2. `build_analysis_workflow`：主入口函数，默认组装 `collection_agent_node`、`analysis_agent_node`、`qa_agent_node` 和 `writer_checkpoint_node`，返回编译后的 LangGraph workflow；测试可注入替代节点。
3. `route_after_qa`：QA 后的条件路由函数，根据 `metadata.qa_agent.qa_status` 和 `revision_target` 将流程导向 Writer checkpoint、Collection、Analysis 或失败结束。
4. `writer_checkpoint_node`：步骤 18 的写作阶段占位节点，只记录流程已到达 Writer、追加一条 `writer_agent` 的 `AgentRunLog`，并将任务状态置为 `completed`；不生成报告数据、不导出 Markdown。
5. `_append_analysis_revision_after_collection_repair`：Collection 修复 Evidence 后的 workflow 桥接逻辑，用结构化 `AgentMessage` 自动创建面向 Analysis 的重算请求，确保 Collection 打回闭环可以继续收敛。
6. `_qa_workflow_node`：QA 节点包装器，负责更新任务状态、累计 `revision_rounds`、写入 `max_revision_rounds`，并在超过上限时把任务标记为 `failed`。
7. `_collection_workflow_node` 和 `_status_wrapped_node`：节点包装器，负责在进入 Collection、Analysis、QA 前更新 `TaskGraphState.task.status` 和 `metadata.workflow.current_node`，不改变各 Agent 节点自身职责。

### 相关文件调整

1. `backend/app/graph/__init__.py`：新增导出 workflow 节点名、`build_analysis_workflow`、`route_after_qa` 和 `writer_checkpoint_node`，让后续 API、后台任务或测试可以从 graph 包统一导入主流程入口。
2. `backend/app/agents/analysis.py`：新增 `_preferred_claim_evidence_ids`，在 Claim 绑定证据时优先排除已经被修复 Evidence 替代的原始缺失 Evidence，避免 QA 因旧 Evidence 重复打回。
3. `backend/app/agents/qa.py`：新增 `_next_qa_run_id`，让同一工作流内多轮 QA 运行拥有唯一 run_id，避免 Trace 日志 identity 冲突。
4. `backend/requirements-dev.txt`：补充 `langgraph`，与 `memory-bank/tech-stack.md` 的后端技术栈约定对齐。
5. `backend/tests/test_workflow.py`：新增 workflow 层测试，覆盖默认 Demo 完整收敛、Collection 打回后 Analysis 重算消息、QA 条件路由和最大打回次数失败。

### 当前 LangGraph DAG

```text
collection_agent -> analysis_agent -> qa_agent
qa_agent -- passed --> writer_agent checkpoint -> END
qa_agent -- collection revision --> collection_agent
qa_agent -- analysis revision --> analysis_agent
qa_agent -- failed/max revisions --> END
```

### 当前状态与边界

1. Workflow 使用现有 `TaskGraphState` 作为 LangGraph 状态对象，仍由 Pydantic Artifact 负责业务校验。
2. Workflow metadata 统一写入 `state["metadata"]["workflow"]`，包含 `current_node`、`next_node`、`revision_rounds`、`max_revision_rounds`、`status` 和失败原因等信息。
3. 默认 Demo 工作流会经历一次 Collection 打回：QA 发现 `sku_01` 价格证据缺少访问时间，Collection 使用本地修复夹具生成修复 Evidence，Workflow 随后补发 Analysis 重算消息。
4. Analysis 重算后 Claim 优先绑定修复 Evidence，第二轮 QA 可以通过并进入 Writer checkpoint。
5. Writer checkpoint 只是第 18 步的流程终点占位，不代表步骤 19 Writer Agent 已完成。
6. 当前 workflow 仍只在内存中运行，不读写 SQLite Artifact 表，不接入 FastAPI 后台任务；任务后台执行链路留给后续步骤。
7. Markdown 导出、报告 API、产品画像 API、竞争图谱 API、Trace API 和 Human Feedback API 仍未实现。

### 验证契约

1. 新增 `backend/tests/test_workflow.py`，验证 workflow 可完成默认 Demo 的真实 Collection 打回、修复、Analysis 重算、QA 通过和 Writer checkpoint。
2. 验证 Collection 修复后会自动创建 Analysis 重算消息，且相关 `AgentMessage` 最终被标记为 `processed`。
3. 验证 `route_after_qa` 对 QA 通过、Collection 打回、Analysis 打回的路由结果稳定。
4. 验证 `max_revision_rounds` 超限时，任务进入 `failed`，并保留 `metadata.workflow.failure_reason`。
5. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_workflow.py` 通过，4 个测试通过。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests` 通过，107 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 尚未实现步骤 19 的真正 Writer Agent 节点。
2. 尚未生成网页报告数据结构，也尚未导出 Markdown。
3. 尚未将 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。
4. 尚未持久化 workflow 产出的 Artifact 与 Trace 到 SQLite。

## 2026-05-26：步骤 19 Writer Agent 节点

当前项目已完成实施计划步骤 19，后端具备真正的 `writer_agent_node`，可在 QA 通过后将现有结构化 Artifact 汇总为网页报告数据结构；按用户要求，在用户验证测试前不会进入步骤 20 的 Markdown 报告导出服务。

### 报告 Schema 与状态结构

1. `backend/app/schemas/report.py`：第 19 步新增的报告数据契约文件，定义 `ReportData` 和 `ReportSection`。`ReportData` 是网页报告的顶层结构，固定包含执行摘要、产品画像、竞品发现、动态切片、决策链、用户研究、建议、QA 摘要和 Evidence 索引九个章节；`ReportSection` 是各章节通用结构，保留 `items`、`claim_ids`、`evidence_ids` 和 `risk_flags`。
2. `backend/app/schemas/__init__.py`：新增导出 `ReportData` 与 `ReportSection`，让 Agent、后续 API 和测试可统一从 schema 包导入报告契约。
3. `backend/app/graph/state.py`：`TaskGraphState` 新增 `reports` 列表字段，并纳入 `STATE_LIST_FIELDS` 与 Trace 序列化计数；新增 `append_report_data` 用于把通过 Pydantic 校验的报告结构写入状态。
4. `backend/app/graph/__init__.py`：新增导出 `append_report_data`，保持 Graph 状态辅助函数的统一入口。

### Writer Agent 文件职责

1. `backend/app/agents/writer.py`：第 19 步新增的 Writer Agent 节点文件，负责从 Graph State 读取 Product、Evidence、FeatureTree、PricingModel、UserPersona、Claim、CompetitionEdge、ReviewInsight 和 ReviewTask，并生成网页报告数据结构。
2. `writer_agent_node`：主入口函数，校验输入是否为 QA 已通过或显式带风险标记的结构化产物，生成 `ReportData` 后追加到 `state["reports"]`，写入 `metadata.writer_agent`，追加 Writer `AgentRunLog`，并将任务状态置为 `completed`。
3. `_build_report_data`：报告组装函数，只重组已有结构化 Artifact，不新增无来源事实字段。它会把竞品发现、动态切片和决策链中的核心结论与 `claim_ids`、`evidence_ids` 绑定，保证后续网页报告和 Markdown 导出可以追溯证据。
4. `_competitor_findings_section`：把高分 CompetitionEdge 转换为前端可渲染的竞品发现项，每项包含竞品摘要、切片、决策阶段、评分拆解、Claim 引用、Evidence 引用和风险标记。
5. `_qa_summary_section`：汇总 QA metadata、ReviewTask、revision message、Collection 修复摘要、Analysis 重算摘要和风险 Claim，避免风险结论在报告层被隐藏。
6. `_recommendations_section`：生成基于已有 CompetitionEdge/Claim/Evidence 的建议项，并显式标记为推断；该函数不得补写新的价格、认证、尺寸、销量或排名事实。
7. `_evidence_index_section`：生成 Evidence 索引，保留来源类型、来源 URL、截图路径、访问时间、置信度、摘要和局限性，为前端证据卡片和后续 Markdown 导出提供统一来源。
8. `backend/app/agents/__init__.py`：新增导出 `writer_agent_node`，让 workflow 默认可以从 `app.agents` 获取四个主 Agent。

### Workflow 接入变化

1. `backend/app/graph/workflow.py`：`build_analysis_workflow` 现在默认导入并使用 `writer_agent_node`，QA 通过后的 `writer_agent` 节点不再停在第 18 步 checkpoint。
2. `_writer_workflow_node`：第 19 步新增的 workflow 包装器，在进入 Writer 前将任务状态置为 `writing`、更新 `metadata.workflow.current_node`，Writer 完成后写入 `metadata.workflow.writer_status = "succeeded"` 和 `metadata.workflow.status = "completed"`。
3. `writer_checkpoint_node`：继续保留为显式占位节点，供测试注入或排查第 18 步边界使用；默认 workflow 已不再使用它。

### 当前报告数据结构

```text
state["reports"][-1]
  ├─ report_id
  ├─ task_id
  ├─ generated_at
  ├─ section_order
  ├─ executive_summary
  ├─ product_profile
  ├─ competitor_findings
  ├─ dynamic_slice_analysis
  ├─ decision_chain_analysis
  ├─ user_research_insights
  ├─ recommendations
  ├─ qa_summary
  └─ evidence_index
```

每个章节都使用 `ReportSection`，字段为：

```text
section_id
title
summary
items
claim_ids
evidence_ids
risk_flags
```

### 当前边界

1. Writer Agent 只生成网页报告数据结构，不生成 Markdown 文本。
2. 当前报告仍保存在内存 `TaskGraphState["reports"]`，尚未持久化到 SQLite。
3. 尚未实现 `GET /tasks/{task_id}/report` 或 `GET /tasks/{task_id}/report/markdown`。
4. 尚未保存任何报告文件到 `data/reports/`。
5. 尚未把 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

### 验证契约

1. 新增 `backend/tests/test_writer_agent.py`，覆盖报告九个必需章节、核心竞品发现的 Claim/Evidence 追溯、风险 Claim 标明和 Writer run log。
2. 更新 `backend/tests/test_workflow.py`，验证默认 workflow 经过真实 QA 打回闭环后进入真正 Writer Agent，生成 `reports`，并记录成功 Writer run。
3. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。
4. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_workflow.py` 通过，8 个测试通过。
5. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests` 通过，111 个测试通过。

### 未开始事项

1. 步骤 20 的 Markdown 报告导出服务已由下一个架构记录补充完成。
2. 尚未实现步骤 21 的报告 API。
3. 尚未持久化 workflow 产出的 ReportData、Artifact、Trace 与 MarkdownReport 到 SQLite。

## 2026-05-26：步骤 20 Markdown 报告导出服务

当前项目已完成实施计划步骤 20，后端具备基于 `ReportData` 的 Markdown 报告导出服务。该步骤只增加服务层导出能力，不创建报告 API，不推进步骤 21。

### 新增与调整文件职责

1. `backend/app/services/markdown_renderer.py`：第 20 步新增的 Markdown 导出服务文件。它负责把第 19 步的 `ReportData` 渲染为 Markdown、执行敏感内容扫描、保存 `.md` 文件，并生成 `MarkdownReport` 元信息。该文件是后续 `GET /tasks/{task_id}/report/markdown` API 应复用的唯一导出入口。
2. `backend/app/schemas/report.py`：在原有 `ReportData` 和 `ReportSection` 基础上新增 `MarkdownReport`。`MarkdownReport` 记录 Markdown 文本、文件路径、导出时间、关联 task/report ID 和统计 metadata，是服务层导出的结构化返回契约。
3. `backend/app/schemas/__init__.py`：新增导出 `MarkdownReport`，保持 Agent、服务、API 和测试从 schema 包统一导入契约。
4. `backend/app/graph/state.py`：`TaskGraphState` 新增 `markdown_reports` 列表字段，并纳入 `STATE_LIST_FIELDS` 和 Trace 序列化计数；新增 `append_markdown_report`，用于把 Markdown 导出结果追加到内存状态。
5. `backend/app/graph/__init__.py`：新增导出 `append_markdown_report`，保持 Graph 状态辅助函数的统一入口。
6. `backend/app/services/__init__.py`：新增导出 `DEFAULT_REPORTS_DIR`、`NO_RELIABLE_DATA`、`MarkdownRenderError`、`render_markdown_report` 和 `export_markdown_report_for_state`，方便后续 API 层复用导出服务。
7. `backend/tests/test_markdown_renderer.py`：第 20 步新增测试文件，覆盖 Markdown 章节结构、Claim/Evidence 可追溯性、缺失证据兜底文案和敏感 Key 模式阻断。

### Markdown Renderer 核心函数

1. `render_markdown_report(report_data, output_dir=None, generated_at=None)`：纯服务入口，接收 `ReportData` 或等价 mapping，渲染 Markdown，完成敏感扫描后写入文件，并返回 `MarkdownReport`。默认输出目录是 `<project-root>/data/reports/`，测试可传入临时目录。
2. `export_markdown_report_for_state(state, output_dir=None, generated_at=None)`：Graph State 入口，读取 `state["reports"][-1]` 作为最近报告，调用 `render_markdown_report`，再把结果追加到 `state["markdown_reports"]`，同时写入 `metadata.markdown_report`。
3. `_render_report`：顶层模板渲染函数，输出报告标题、Report ID、Task ID、ReportData 生成时间、Markdown 导出时间和九个章节。
4. `_render_section`：通用章节模板渲染函数，统一输出章节标题、摘要、主体、Claim 索引和 Evidence 索引。
5. `_render_competitor_findings` 与 `_render_claims`：竞品发现专用渲染逻辑，逐条输出竞品关系、评分、决策阶段、Evidence 列表，以及每个 Claim 的 Claim ID、正文、置信度、推断标识、状态、Evidence ID 和风险标记。
6. `_render_evidence_index`：Evidence 索引专用渲染逻辑，逐条输出 Evidence ID、Product ID、来源类型、来源 URL、截图路径、访问时间、置信度、摘要和局限性。
7. `_render_recommendations`：建议章节专用渲染逻辑，保留建议、基础 Edge、Claim/Evidence 索引和推断标识，不新增无证据事实。
8. `_render_generic_items`：其他章节的通用渲染兜底，用结构化键值展示已有 ReportData item，同时跳过内部 metadata。
9. `_assert_markdown_is_safe`：导出前安全扫描，阻断 `sk-...`、`api_key=...`、`secret=...`、`password=...`、`token=...` 和 `Bearer ...` 等敏感模式。

### 当前 Markdown 数据流

```text
LangGraph workflow
  -> writer_agent_node
  -> state["reports"][-1] as ReportData
  -> export_markdown_report_for_state
  -> render_markdown_report
  -> Markdown text + local .md file
  -> state["markdown_reports"][-1] as MarkdownReport
  -> metadata.markdown_report
```

### 设计约束

1. Markdown 只消费 `ReportData` 中已经存在的结构化内容，不读取真实环境变量，不调用模型，不访问外网。
2. Markdown 中的核心 Claim 必须显示 Claim、Evidence、置信度和推断标识；Evidence 索引必须显示访问时间。
3. 缺失 Evidence、访问时间、截图或其他空值时统一显示“暂无可靠数据”，不得凭记忆补价格、认证、尺寸、销量或排名。
4. 用户研究章节继续只展示结构化摘要，不展开未脱敏原文。
5. 命中敏感 Key 模式时，导出服务抛出 `MarkdownRenderError`，不会写出报告文件。
6. 文件名由 task_id 和 report_id 生成，并做文件名安全清理，避免把任意字符直接写入路径。
7. 第 20 步没有创建任何 FastAPI route；报告 API 留给步骤 21。

### 当前验证契约

1. 新增 `backend/tests/test_markdown_renderer.py`，验证 Markdown 包含九个二级报告章节，且导出文件内容与返回文本一致。
2. 验证核心竞品发现中的每个 Claim 都能看到 Claim ID、置信度、推断标识和关联 Evidence，并且 Evidence 索引展示访问时间与置信度。
3. 验证缺失 Evidence 时输出“暂无可靠数据”。
4. 验证敏感环境变量或 API Key 模式会阻断导出。
5. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_markdown_renderer.py` 通过，4 个测试通过。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_markdown_renderer.py backend\tests\test_writer_agent.py backend\tests\test_workflow.py` 通过，12 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp` 通过，115 个测试通过。
8. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 步骤 21 的报告 API 已由下一个架构记录补充完成。
2. 尚未实现步骤 22 的产品画像 API。
3. 尚未将 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 21 报告 API

当前项目已完成实施计划步骤 21，后端具备报告读取与 Markdown 导出的 HTTP API。该步骤只实现报告 API，不创建产品画像 API，不推进步骤 22。

### 新增与调整文件职责

1. `backend/app/api/dependencies.py`：第 21 步新增的 API 依赖文件，集中管理从 FastAPI app state 获取或创建 SQLite engine、session factory 和 repository session，避免任务 API 与报告 API 重复数据库初始化逻辑。
2. `backend/app/api/routes_tasks.py`：改为复用 `repository_session`，任务创建与任务状态查询的外部行为不变。
3. `backend/app/services/report_service.py`：第 21 步新增的报告应用服务，负责校验任务状态、读取或生成 `ReportData`、缓存报告 Artifact、调用 Markdown renderer 并处理导出失败。
4. `backend/app/services/__init__.py`：新增导出 `ReportService`、`ReportServiceError`、`REPORT_ARTIFACT_TYPE` 和 `MARKDOWN_REPORT_ARTIFACT_TYPE`。
5. `backend/app/api/routes_reports.py`：第 21 步新增的报告路由文件，提供 `GET /tasks/{task_id}/report` 与 `GET /tasks/{task_id}/report/markdown`。
6. `backend/app/main.py`：注册报告路由，让报告 API 进入 FastAPI 应用。
7. `backend/tests/test_reports_api.py`：第 21 步新增测试文件，覆盖完成任务报告读取、Markdown 导出、未完成任务错误、导出失败降级和缺失任务错误。

### ReportService 核心职责

1. `get_report_data(task_id)`：报告读取入口。它先确认任务存在且状态为 `completed`；如果存在缓存的 `report_data` Artifact，直接返回最新报告；如果没有缓存，则同步运行现有 LangGraph workflow 生成 `ReportData` 并缓存。
2. `export_markdown_report(task_id)`：Markdown 导出入口。它复用 `get_report_data` 取得网页报告数据，再调用第 20 步 `render_markdown_report` 写出 `.md` 文件，最后把 `MarkdownReport` 保存为 `markdown_report` Artifact。
3. `_get_completed_task`：任务门禁函数。不存在任务返回 `TASK_NOT_FOUND`；非完成任务返回 `REPORT_NOT_READY`，details 中保留当前任务状态，供前端展示等待态。
4. `_generate_and_cache_report`：同步报告生成兜底函数。它从已完成任务创建 `TaskGraphState`，运行 `build_analysis_workflow()`，读取 `state["reports"][-1]`，并保存为 `report_data` Artifact。
5. `ReportServiceError`：报告服务统一错误类型，路由层会转换成项目标准 `ApiException`，保持统一响应结构。

### 当前报告 API 数据流

```text
GET /tasks/{task_id}/report
  -> TaskRepository.get
  -> status must be completed
  -> ArtifactRepository.list_by_task(report_data)
  -> cached ReportData or build_analysis_workflow().invoke(...)
  -> ArtifactRepository.save(report_data)
  -> ApiResponse[ReportData]

GET /tasks/{task_id}/report/markdown
  -> ReportService.get_report_data
  -> render_markdown_report
  -> local .md file
  -> ArtifactRepository.save(markdown_report)
  -> ApiResponse[MarkdownReport]
```

### 当前 API 行为

1. `GET /tasks/{task_id}/report` 返回统一响应结构，`data` 为完整 `ReportData`。
2. `GET /tasks/{task_id}/report/markdown` 返回统一响应结构，`data` 为 `MarkdownReport`，包含 Markdown 文本、文件路径、导出时间和 `metadata.file_name`。
3. 未完成任务不会触发报告生成，返回 HTTP 409，错误码 `REPORT_NOT_READY`。
4. 不存在任务返回 HTTP 404，错误码 `TASK_NOT_FOUND`。
5. Markdown 导出失败返回 HTTP 500，错误码 `MARKDOWN_EXPORT_FAILED`，并保留网页报告接口可用。
6. 正式导出默认使用 `<project-root>/data/reports/`；测试可通过 `app.state.report_output_dir` 注入临时目录。
7. 报告 API 当前只缓存 ReportData 与 MarkdownReport，不尝试持久化完整 Product、Evidence、Claim、CompetitionEdge 或 Trace。

### 边界与后续接口关系

1. 报告 API 只面向报告页和 Markdown 导出，不返回产品画像专用结构。
2. `GET /tasks/{task_id}/profile` 尚未实现，留给步骤 22。
3. 当前同步生成报告是报告 API 的兜底能力，用来弥补后台 workflow 尚未接入 `POST /tasks` 的阶段性空缺；后续后台任务落地后，报告 API 可以优先读取已持久化的 ReportData。
4. 没有引入新基础设施；仍使用 FastAPI、Pydantic、LangGraph、SQLite 和 SQLAlchemy。

### 当前验证契约

1. 新增 `backend/tests/test_reports_api.py`，验证完成任务可以获取网页报告数据，并缓存 `report_data` Artifact。
2. 验证完成任务可以导出 Markdown，响应包含 Markdown 文本、文件路径和 `.md` 文件名，且文件真实存在。
3. 验证未完成任务请求报告返回 `REPORT_NOT_READY`。
4. 验证 Markdown 导出目录异常时返回 `MARKDOWN_EXPORT_FAILED`，同时 `GET /report` 继续可用。
5. 验证缺失任务请求报告返回 `TASK_NOT_FOUND`。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_reports_api.py` 通过，5 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_markdown_renderer.py backend\tests\test_workflow.py` 通过，22 个测试通过。
8. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp` 通过，120 个测试通过。
9. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 步骤 22 的产品画像 API 已由下一个架构记录补充完成。
2. 尚未实现竞争图谱 API、Trace API 或 Human Feedback API。
3. 尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 22 产品画像 API

当前项目已完成实施计划步骤 22，后端具备目标产品画像读取 HTTP API。该步骤只实现产品画像 API，不创建竞争图谱 API，不推进步骤 23。

### 新增与调整文件职责

1. `backend/app/schemas/profile.py`：第 22 步新增的产品画像响应契约文件，定义 `ProductProfileData`、`EvidenceSummary` 和 `PricingEvidenceSummary`，用于前端产品画像页直接渲染。
2. `backend/app/schemas/__init__.py`：新增导出 `ProductProfileData`、`EvidenceSummary` 和 `PricingEvidenceSummary`。
3. `backend/app/services/profile_service.py`：第 22 步新增的产品画像应用服务，负责校验任务状态、读取或生成目标产品画像、压缩 Evidence 摘要、缓存画像 Artifact。
4. `backend/app/services/__init__.py`：新增导出 `ProfileService`、`ProfileServiceError`、`PRODUCT_PROFILE_ARTIFACT_TYPE` 和 `MAX_EVIDENCE_SUMMARY_CHARS`。
5. `backend/app/api/routes_profile.py`：第 22 步新增的画像路由文件，提供 `GET /tasks/{task_id}/profile`。
6. `backend/app/main.py`：注册产品画像路由，让画像 API 进入 FastAPI 应用。
7. `backend/tests/test_profile_api.py`：第 22 步新增测试文件，覆盖画像模块完整性、价格证据状态、Evidence 摘要长度、未完成任务错误和缺失任务错误。

### ProductProfileData 结构

```text
ProductProfileData
  ├─ profile_id
  ├─ task_id
  ├─ generated_at
  ├─ product
  ├─ feature_tree
  ├─ pricing_model
  ├─ pricing_evidence
  ├─ user_persona
  ├─ evidence_summaries
  └─ metadata
```

1. `product`：目标 `Product`，包含品牌、店铺、SKU 名称、链接、标签和 Evidence 引用。
2. `feature_tree`：目标 `FeatureTree`，包含清洁、除臭、安全、智能、维护成本等结构化能力项。
3. `pricing_model`：目标 `PricingModel`，包含价格带、币种、标价、到手价、促销、套餐、证据引用和访问时间。
4. `pricing_evidence`：价格字段专用证据摘要，包含 `evidence_ids`、`access_time`、`access_time_status` 和价格证据风险标记，便于前端突出价格证据状态。
5. `user_persona`：目标 `UserPersona`，包含人群、痛点、场景、决策因素、证据引用和推断标识。
6. `evidence_summaries`：目标产品相关 Evidence 的短摘要列表，保留来源、访问时间、截图、置信度、局限性和风险标记。

### ProfileService 核心职责

1. `get_product_profile(task_id)`：画像读取入口。它先确认任务存在且状态为 `completed`；如果存在缓存的 `product_profile` Artifact，直接返回最新画像；如果没有缓存，则同步运行现有 LangGraph workflow 生成画像并缓存。
2. `_generate_and_cache_profile`：同步画像生成兜底函数。它从已完成任务创建 `TaskGraphState`，运行 `build_analysis_workflow()`，再从 Graph State 中读取目标 Product、FeatureTree、PricingModel、UserPersona 和 Evidence。
3. `_build_product_profile`：画像组装函数，只读取当前 workflow 已生成结构化产物，不新增无证据事实。
4. `_pricing_evidence_summary`：价格证据摘要函数，统一输出价格证据 ID、访问时间、访问时间状态和风险标记。
5. `_evidence_summary`：Evidence 摘要函数，输出短摘要并根据缺失访问时间或截图路径补充风险标记。
6. `_shorten`：摘要压缩函数，确保 `content_summary` 和 `limitations` 不超过 `MAX_EVIDENCE_SUMMARY_CHARS = 180` 字符，避免 API 返回过长原文。

### 当前画像 API 数据流

```text
GET /tasks/{task_id}/profile
  -> TaskRepository.get
  -> status must be completed
  -> ArtifactRepository.list_by_task(product_profile)
  -> cached ProductProfileData or build_analysis_workflow().invoke(...)
  -> target Product + FeatureTree + PricingModel + UserPersona + EvidenceSummary
  -> ArtifactRepository.save(product_profile)
  -> ApiResponse[ProductProfileData]
```

### 当前 API 行为

1. `GET /tasks/{task_id}/profile` 返回统一响应结构，`data` 为完整 `ProductProfileData`。
2. 未完成任务不会触发画像生成，返回 HTTP 409，错误码 `PROFILE_NOT_READY`。
3. 不存在任务返回 HTTP 404，错误码 `TASK_NOT_FOUND`。
4. 正常响应不会返回 `research_text` 原文，也不会展开未脱敏访谈内容。
5. Evidence 摘要中的 `access_time_status` 取值为 `available` 或 `missing`，用于前端直观展示访问时间状态。
6. 当前画像 API 只缓存 `ProductProfileData`，不尝试持久化完整 Product、Evidence、Claim、CompetitionEdge 或 Trace。

### 边界与后续接口关系

1. 产品画像 API 只面向产品画像页，不返回竞品关系图、切片列表、边评分解释或竞争图谱筛选数据。
2. `GET /tasks/{task_id}/battlefield` 尚未实现，留给步骤 23。
3. 当前同步生成画像是画像 API 的兜底能力，用来弥补后台 workflow 尚未接入 `POST /tasks` 的阶段性空缺；后续后台任务落地后，画像 API 可以优先读取已持久化的 ProductProfileData 或底层 Artifact。
4. 没有引入新基础设施；仍使用 FastAPI、Pydantic、LangGraph、SQLite 和 SQLAlchemy。

### 当前验证契约

1. 新增 `backend/tests/test_profile_api.py`，验证完成任务可以获取目标 Product、FeatureTree、PricingModel、UserPersona 和 EvidenceSummary。
2. 验证价格字段包含证据引用和访问时间状态。
3. 验证 Evidence 摘要不会返回过长原文，也不会泄露测试中的私密研究文本片段。
4. 验证未完成任务请求画像返回 `PROFILE_NOT_READY`。
5. 验证缺失任务请求画像返回 `TASK_NOT_FOUND`。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_profile_api.py` 通过，5 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_profile_api.py backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_workflow.py` 通过，23 个测试通过。
8. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp` 通过，125 个测试通过。
9. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 步骤 23 的 `GET /tasks/{task_id}/battlefield` 已由下一条架构记录补充完成。
2. 尚未实现 Trace API 或 Human Feedback API。
3. 尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 23 竞争图谱 API

当前项目已完成实施计划步骤 23，后端具备面向竞争图谱页的 HTTP API。该步骤只实现 `GET /tasks/{task_id}/battlefield`，不推进 Trace API，也不改变后台任务执行方式。

### 新增与调整文件职责

1. `backend/app/schemas/battlefield.py`：第 23 步新增的竞争图谱响应契约文件。它把前端竞争图谱页需要的数据拆成 `BattlefieldData`、`BattlefieldSliceSelection`、`BattlefieldSliceOption`、`BattlefieldGraphNode`、`BattlefieldGraphEdge`、`BattlefieldClaimReference`、`BattlefieldScoreExplanation`、`BattlefieldDecisionChainStage`、`BattlefieldEvidenceCard` 和 `BattlefieldQASummary`，确保图、切片、评分、证据和 QA 状态都有稳定结构。
2. `backend/app/schemas/__init__.py`：新增导出所有 battlefield schema，保证 FastAPI OpenAPI 与后续前端类型同步能发现第 23 步接口契约。
3. `backend/app/services/battlefield_service.py`：第 23 步新增的竞争图谱聚合服务。它负责校验任务状态、按切片读取或生成缓存、同步调用现有 LangGraph workflow、把 Product/Claim/Evidence/CompetitionEdge/ReviewTask/AgentMessage 组装成竞争图谱视图，并维护 `BATTLEFIELD_ARTIFACT_TYPE` 与 Evidence 卡片摘要长度常量。
4. `backend/app/services/__init__.py`：新增导出 `BattlefieldService`、`BattlefieldServiceError`、`BATTLEFIELD_ARTIFACT_TYPE` 和 `MAX_EVIDENCE_CARD_SUMMARY_CHARS`，与 report/profile service 保持一致的服务入口模式。
5. `backend/app/api/routes_battlefield.py`：第 23 步新增的 FastAPI 路由文件，提供 `GET /tasks/{task_id}/battlefield`，接收 `price_band`、`persona`、`scenario` 三个可选查询参数，负责把 service error 转换成统一 `ApiException`。
6. `backend/app/main.py`：注册 battlefield router，让竞争图谱 API 进入应用路由表。
7. `backend/tests/test_battlefield_api.py`：第 23 步新增 API 测试，覆盖默认竞争图谱数据、价格带过滤、Claim/Evidence 引用、风险边状态和未完成任务错误。

### BattlefieldService 核心职责

1. `get_battlefield(task_id, price_band, persona, scenario)`：竞争图谱 API 的服务入口。它先确认任务存在且状态为 `completed`，再按任务与切片参数生成稳定 `battlefield_id`，优先读取 SQLite `artifact_json` 中缓存的 `battlefield_data`；缓存缺失时同步生成。
2. `_generate_and_cache_battlefield`：同步生成兜底函数。它从已完成任务创建 `TaskGraphState`，运行 `build_analysis_workflow().invoke(...)`，确认 workflow 完成后组装 `BattlefieldData` 并写入 Artifact 缓存。
3. `_build_battlefield_data`：竞争图谱视图组装函数。它只消费现有 workflow 结构化产物，不新增无证据事实；默认返回所有竞争边并按 `edge_score` 降序排列，显式传入切片参数时按对应维度过滤。
4. `_graph_edge` 与 `_claim_ref`：把 `CompetitionEdge` 和关联 `Claim` 转成前端可渲染的图边结构，每条边保留 `claim_ids`、`evidence_ids`、`claim_refs`、`score_breakdown` 和 `score_explanations`。
5. `_edge_risk_flags`：聚合边本身风险、Claim 风险、非 accepted Claim 状态和开放 ReviewTask，把问题边标记为 `risk_status = "at_risk"`。
6. `_available_slices`：基于所有 `CompetitionEdge.slice` 生成可选切片列表，每个切片包含边数量和最高边得分。
7. `_decision_chain`：按 `DecisionStage` 汇总边、Claim、Evidence 和平均得分，供前端竞争图谱页展示决策链。
8. `_evidence_card`：从边引用的 Evidence 生成卡片，保留来源、截图、访问时间、置信度、摘要、局限和缺失字段风险。
9. `_qa_summary`：汇总 ReviewTask、revision message、风险边和风险 Claim，用于竞争图谱页展示 QA 总状态。

### 当前竞争图谱 API 数据流

```text
GET /tasks/{task_id}/battlefield
  -> TaskRepository.get
  -> status must be completed
  -> ArtifactRepository.get(battlefield_data, slice artifact_id)
  -> cached BattlefieldData or build_analysis_workflow().invoke(...)
  -> Product + Claim + Evidence + CompetitionEdge + ReviewTask + AgentMessage
  -> graph nodes / graph edges / score explanations / decision chain / evidence cards / QA summary
  -> ArtifactRepository.save(battlefield_data)
  -> ApiResponse[BattlefieldData]
```

### 当前 API 行为

1. `GET /tasks/{task_id}/battlefield` 返回统一响应结构，`data` 为完整 `BattlefieldData`。
2. 任务不存在返回 HTTP 404，错误码 `TASK_NOT_FOUND`。
3. 任务未完成返回 HTTP 409，错误码 `BATTLEFIELD_NOT_READY`，`details.status` 保留当前任务状态。
4. 不传切片参数时返回全部边，按 `edge_score` 降序排列，包含直接竞品和替代/渠道类竞品。
5. 传入 `price_band`、`persona` 或 `scenario` 时只过滤对应维度；未传维度作为通配条件。
6. 每条图边必须包含 Claim 与 Evidence 引用；如果 Claim 缺失、Evidence 缺失或 QA/Review 标记仍开放，则边会进入风险状态。
7. 当前只缓存 `BattlefieldData` 聚合结果，不尝试在步骤 23 全量持久化 Product、Evidence、Claim、CompetitionEdge 或 Trace。

### 边界与后续接口关系

1. 竞争图谱 API 面向竞争图谱页，不返回 Agent Run、Tool Call、Token Usage 或 Diff View；这些留给步骤 24 的 Trace API。
2. 竞争图谱 API 复用同步 workflow 生成作为阶段性兜底，后续后台任务落地后可以优先读取已持久化的底层 Artifact 或已缓存 `BattlefieldData`。
3. 缓存粒度包含任务 ID 和切片参数，避免默认竞争图谱、价格带竞争图谱、人群竞争图谱、场景竞争图谱互相覆盖。
4. 没有引入新基础设施；仍使用 FastAPI、Pydantic、LangGraph、SQLite 和 SQLAlchemy。

### 当前验证契约

1. 新增 `backend/tests/test_battlefield_api.py`，验证默认竞争图谱返回直接竞品和替代/渠道类竞品，且边按分数降序。
2. 验证切换 `price_band` 会改变返回边集合或评分解释，并保证边切片与查询参数一致。
3. 验证每条边包含 `claim_ids`、`evidence_ids` 和 `claim_refs`，Evidence 卡片覆盖边引用的 Evidence。
4. 验证被 QA 或服务标记的问题边带 `at_risk` 状态，并进入 `qa_summary.risk_edge_ids`。
5. 验证未完成任务请求竞争图谱数据返回 `BATTLEFIELD_NOT_READY`。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_battlefield_api.py` 通过，5 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_battlefield_api.py backend\tests\test_profile_api.py backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_workflow.py` 通过，28 个测试通过。
8. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -B -m pytest backend\tests -p no:cacheprovider --basetemp backend\.ruff_cache\pytest-basetemp` 通过，130 个测试通过。
9. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 尚未实现步骤 24 的 `GET /tasks/{task_id}/trace`。
2. 尚未实现 Human Feedback API。
3. 尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 24 Trace API

当前项目已完成实施计划步骤 24，后端具备面向 Agent Trace 页的 `GET /tasks/{task_id}/trace` HTTP API。该步骤只实现 Trace API，不推进步骤 25，也不改变后台任务执行方式。

### 新增与调整文件职责

1. `backend/app/schemas/trace.py`：在原有 `AgentRunLog`、`ToolCallLog`、`TokenUsageLog` 基础上新增 Trace 视图契约。`TraceData` 是 API 顶层数据结构；`TraceDagNode` 和 `TraceDagEdge` 描述前端 Trace DAG；`TraceDiff` 描述 QA 打回后的 Collection repair 与 Analysis recompute 差异；`TracePromptPreview` 只返回折叠且脱敏后的 prompt 摘要，不暴露原始 prompt。
2. `backend/app/schemas/__init__.py`：新增导出 `TraceData`、`TraceDagNode`、`TraceDagEdge`、`TraceDiff`、`TracePromptPreview`，保证 FastAPI response model 和后续前端类型同步可以统一从 `app.schemas` 发现 Trace 契约。
3. `backend/app/services/trace_service.py`：第 24 步新增的 Trace 聚合服务。它负责读取任务、判断是否可复用缓存、同步运行现有 LangGraph workflow 兜底生成 Trace、组装 DAG 节点/边、提取 Agent Run/Tool Call/Token Usage/QA Review/Revision Message/Diff，并在返回前执行 Trace 专用脱敏。该服务定义 `TRACE_ARTIFACT_TYPE = "trace_data"`，当前以任务级聚合结果写入 SQLite `artifact_json`。
4. `backend/app/services/__init__.py`：新增导出 `TraceService`、`TraceServiceError` 和 `TRACE_ARTIFACT_TYPE`，与 report/profile/battlefield service 保持同一入口模式。
5. `backend/app/api/routes_trace.py`：第 24 步新增的 FastAPI 路由文件，提供 `GET /tasks/{task_id}/trace`。路由层只负责打开 repository session、创建 `TraceService`、把 service error 转换为统一 `ApiException`，不直接拼装 Trace 数据。
6. `backend/app/main.py`：注册 Trace router，让 Trace API 进入应用路由表。
7. `backend/tests/test_trace_api.py`：第 24 步新增 API 测试，覆盖 DAG nodes/edges、每个 Agent 的 run log、QA revision 与 diff 查询、敏感信息脱敏、未完成任务 Trace 骨架和缺失任务标准错误。

### TraceData 结构

```text
TraceData
  ├─ trace_view_id
  ├─ task_id
  ├─ task_status
  ├─ workflow_status
  ├─ generated_at
  ├─ dag_nodes
  ├─ dag_edges
  ├─ agent_runs
  ├─ tool_calls
  ├─ token_usage
  ├─ qa_reviews
  ├─ revision_messages
  ├─ diffs
  ├─ prompt_previews
  └─ metadata
```

1. `dag_nodes` 固定包含 `collection_agent`、`analysis_agent`、`qa_agent`、`writer_agent`、`failed`、`end`。`failed` 节点始终 `visible=true`，即使 workflow 正常完成也不会从图中隐藏。
2. `dag_edges` 表达真实 LangGraph 走向和 QA 条件边：Collection -> Analysis -> QA，QA 可路由到 Writer、Collection、Analysis 或 Failed，Writer -> End。
3. `agent_runs`、`tool_calls`、`token_usage` 直接复用已有 trace schema，保证第 24 步不发明第二套运行日志格式。
4. `qa_reviews` 来自 workflow state 中的 `ReviewTask`；`revision_messages` 只筛选 `AgentMessageType.REVISION_REQUEST`，用于展示 QA 打回和后续局部重算触发。
5. `diffs` 当前从 `metadata.collection_agent_repair.diffs` 和 `metadata.analysis_agent_recompute.diffs/claim_diffs` 提取，统一为前端可渲染的 `TraceDiff`。
6. `prompt_previews` 只使用 run log 的输入摘要生成折叠预览；不返回完整 prompt、不返回未脱敏研究文本。

### TraceService 核心职责

1. `get_trace(task_id)`：Trace API 的服务入口。任务不存在时抛出 `TASK_NOT_FOUND`；任务完成时优先读取缓存，否则同步生成；任务未完成时返回骨架 DAG，便于前端轮询 Trace 页。
2. `_generate_and_cache_trace`：同步生成兜底。它从已存在任务创建 `TaskGraphState`，运行 `build_analysis_workflow().invoke(...)`，再把结果交给 `_build_trace_data` 组装，并保存为 `trace_data` Artifact。
3. `_build_trace_data`：Trace 聚合函数。它读取 workflow metadata、run logs、tool call logs、token usage logs、review tasks、agent messages 和 diff metadata，构建完整 `TraceData`。
4. `_dag_nodes` 与 `_dag_edges`：把 LangGraph 节点常量和 QA 条件边转换为前端图结构；节点状态来自对应 Agent 最后一条 run log，当前节点来自 workflow metadata。
5. `_trace_diffs`：把 Collection Agent 修复证据产生的 diff、Analysis Agent 局部重算产生的 edge/claim diff 统一转换为 `TraceDiff`。
6. `_prompt_previews`：从 run log `input_summary` 生成短摘要，固定标记 `folded=true` 和 `redacted=true`。
7. `_redact_trace_value`：Trace 专用脱敏逻辑。它保留 `token_usage` 这类合法结构字段，但会清理 `api_key`、`authorization`、`password`、`secret`、Bearer token 和 `sk-` 密钥模式。

### 当前 Trace API 数据流

```text
GET /tasks/{task_id}/trace
  -> TaskRepository.get
  -> if task missing: TASK_NOT_FOUND
  -> if task not completed: skeleton TraceData
  -> if task completed:
       ArtifactRepository.get(trace_data)
       or build_analysis_workflow().invoke(create_initial_state(task))
       -> Agent Run / Tool Call / Token Usage / QA Review / Revision Message / Diff
       -> TraceData redaction
       -> ArtifactRepository.save(trace_data)
  -> ApiResponse[TraceData]
```

### 当前 API 行为

1. `GET /tasks/{task_id}/trace` 返回统一响应结构，`data` 为完整 `TraceData`。
2. 不存在任务返回 HTTP 404，错误码 `TASK_NOT_FOUND`。
3. 未完成任务返回 HTTP 200 和 Trace 骨架，不触发同步 workflow，方便前端 Trace 页创建任务后立即跳转和轮询。
4. 完成任务若无缓存，会同步运行现有 LangGraph workflow 生成 TraceData；若已有 `trace_data` Artifact，则直接返回缓存。
5. Trace 响应不包含 `task.research_text` 原文，不包含原始 prompt，也不会暴露 API Key、Bearer token 或 `sk-` 类密钥。
6. 当前只缓存任务级 `TraceData` 聚合结果，不在第 24 步落地完整底层 TraceLog 执行流水；后续后台任务接入后可替换为优先读取真实持久化 TraceLog。

### 边界与后续接口关系

1. Trace API 面向 Agent Trace 页，返回 DAG、Agent Run、Tool Call、Token Usage、QA Review 和 Diff View；不返回竞争图谱页切片聚合结构，也不承担 Human Feedback 提交。
2. `GET /tasks/{task_id}/trace` 当前允许未完成任务访问骨架 DAG，这与创建任务后默认跳转 Agent Trace 页的产品决策保持一致。
3. 与 report/profile/battlefield API 一样，Trace API 当前使用同步 workflow 兜底生成，弥补后台 workflow 尚未接入 `POST /tasks` 的阶段性空缺。
4. 没有引入新基础设施；仍使用 FastAPI、Pydantic、LangGraph、SQLite 和 SQLAlchemy。

### 当前验证契约

1. 新增 `backend/tests/test_trace_api.py`，验证 Trace 返回 DAG nodes 和 edges，并保证 `failed` 节点可见。
2. 验证完成任务的 Trace 至少包含 Collection、Analysis、QA、Writer 每个 Agent 的 run log。
3. 验证 Trace 可查询 QA revision message、ReviewTask、Collection repair diff 和 Analysis recompute diff。
4. 验证 Trace 响应不包含 API Key、Bearer token、`sk-` 密钥或未脱敏私密字段，且 prompt preview 固定折叠和脱敏。
5. 验证未完成任务返回 Trace 骨架，缺失任务返回 `TASK_NOT_FOUND`。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_trace_api.py` 通过，6 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_trace_api.py backend\tests\test_battlefield_api.py backend\tests\test_profile_api.py backend\tests\test_reports_api.py backend\tests\test_tasks_api.py backend\tests\test_workflow.py` 通过，34 个测试通过。
8. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests` 通过，136 个测试通过。
9. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 尚未开始步骤 25。
2. 尚未实现 Human Feedback API。
3. 尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 25 Human Feedback API

当前项目已完成实施计划步骤 25，后端具备有限 Human Review 提交接口 `POST /tasks/{task_id}/feedback`。该步骤只实现 Human Feedback API 和待重算标记，不推进步骤 26 的前端路由与布局，也不伪造后台局部重算已经完成。

### 新增与调整文件职责

1. `backend/app/schemas/review.py`：在既有 `HumanFeedback` 基础上新增 `HumanFeedbackCreateRequest` 和 `HumanFeedbackCreateResponse`。请求只包含目标类型、目标 ID、动作、修正后值和原因；响应返回保存后的 `HumanFeedback`、任务状态、重算标记状态、受影响对象和少量 metadata。
2. `backend/app/schemas/__init__.py`：新增导出 Human Feedback 创建请求与响应 Schema，保证 FastAPI response model 和后续前端类型同步可发现第 25 步接口契约。
3. `backend/app/storage/repositories.py`：为 `TaskRepository` 新增 `update_metadata`。该方法只更新任务 metadata 和 `updated_at`，用于保存 `requires_analysis_recompute` 与 Human Feedback 重算历史，不绕过现有任务状态更新入口。
4. `backend/app/services/feedback_service.py`：第 25 步新增的反馈应用服务。它负责校验任务状态、构建当前 workflow 上下文、限制可反馈目标和动作、自动计算 `before_value`、规范化 `after_value`、保存反馈、写入反馈影响 Artifact，并把任务标记为 `human_reviewing`。
5. `backend/app/services/__init__.py`：新增导出 `FeedbackService`、`FeedbackServiceError` 和 `HUMAN_FEEDBACK_EFFECT_ARTIFACT_TYPE`，与 report/profile/battlefield/trace service 保持一致的服务入口模式。
6. `backend/app/api/routes_feedback.py`：第 25 步新增的 FastAPI 路由文件，提供 `POST /tasks/{task_id}/feedback`。路由层负责创建 service、转换 service error 为统一 `ApiException`，不直接处理反馈业务规则。
7. `backend/app/main.py`：注册 feedback router，让 Human Feedback API 进入应用路由表。
8. `backend/tests/test_feedback_api.py`：第 25 步新增 API 测试，覆盖允许范围反馈、Claim 状态反馈、禁止自由改写报告、反馈影响 Artifact、未完成任务错误和缺失任务错误。

### Human Feedback 允许范围

第 25 步明确把自由改写报告关在接口外，只允许结构化、小范围反馈：

1. `product` + `update_field`：允许更新 `name`、`brand`、`shop_name`、`product_url`、`tags`。
2. `feature_tree` + `update_field`：允许更新 `cleaning_capability`、`odor_control`、`safety_features`、`smart_features`、`maintenance_cost`。
3. `pricing_model` + `update_field`：允许更新 `price_band`、`promotions`、`bundle_description`。
4. `user_persona` + `update_field`：允许更新 `personas`、`pain_points`、`scenarios`、`decision_factors`。
5. `claim` + `mark_accepted` / `mark_rejected` / `mark_needs_review`：只允许修改 Claim 采纳状态，不允许直接改写 Claim 正文。
6. `evidence` + `add_note`：允许补充人工备注，保存到反馈记录中等待后续重算消费。
7. `competition_edge` + `remove_competitor`：允许标记移除某条竞争边对应竞品，保存为待重算意图。
8. `slice` + `update_field`：允许更新动态切片字段 `price_band`、`persona`、`scenario`，保存为待重算意图。

任何越界动作会返回：

1. `FEEDBACK_NOT_ALLOWED`：目标类型与动作组合不允许，例如试图对 Claim 执行 `update_field` 改写正文。
2. `FEEDBACK_INVALID_PAYLOAD`：允许组合下的 payload 缺少必需字段或字段不在 allowlist。
3. `FEEDBACK_TARGET_NOT_FOUND`：当前 workflow 上下文中找不到目标对象。

### FeedbackService 核心职责

1. `submit_feedback(task_id, payload)`：Feedback API 服务入口。它确认任务存在且状态为 `completed` 或 `human_reviewing`，构建当前分析上下文，生成 before/after，保存反馈，写入重算标记，并返回标准响应。
2. `_get_reviewable_task`：任务门禁。不存在任务返回 `TASK_NOT_FOUND`；未完成任务返回 `FEEDBACK_NOT_READY`，避免用户在没有分析结果时提交修正。
3. `_build_context_state`：反馈上下文生成。当前阶段复用 `build_analysis_workflow().invoke(create_initial_state(task))` 同步生成结构化上下文，用来查找 Product、FeatureTree、PricingModel、UserPersona、Claim、Evidence、CompetitionEdge 和 Slice。
4. `_feedback_values`：反馈规则分发。按目标类型进入画像字段、Claim 状态、Evidence 备注、竞品集合或动态切片处理逻辑。
5. `_profile_update_values`：画像字段反馈处理。它使用 allowlist 验证字段，自动从当前 Artifact 读取 `before_value`，并规范化 `after_value` 为 `{field, value}`。
6. `_claim_status_values`：Claim 采纳状态反馈处理。它只接受三类状态动作，并把受影响 Claim 与关联 Evidence ID 返回给重算标记。
7. `_save_feedback_effect`：写入 `human_feedback_effect` Artifact，记录 `feedback_id`、`affected_artifact_ids`、before/after 和 `marked_for_reanalysis`。
8. `_mark_task_for_reanalysis`：更新任务 metadata 和状态。metadata 写入 `human_feedback_reanalysis` 历史和 `requires_analysis_recompute=true`，任务状态更新为 `human_reviewing`。

### 当前 Feedback API 数据流

```text
POST /tasks/{task_id}/feedback
  -> TaskRepository.get
  -> status must be completed or human_reviewing
  -> build_analysis_workflow().invoke(create_initial_state(task))
  -> validate target/action allowlist
  -> compute before_value from current structured artifact
  -> normalize after_value
  -> HumanFeedbackRepository.save
  -> ArtifactRepository.save(human_feedback_effect)
  -> TaskRepository.update_metadata(requires_analysis_recompute=true)
  -> TaskRepository.update_status(human_reviewing)
  -> ApiResponse[HumanFeedbackCreateResponse]
```

### 当前 API 行为

1. `POST /tasks/{task_id}/feedback` 返回统一响应结构，`data` 为 `HumanFeedbackCreateResponse`。
2. 不存在任务返回 HTTP 404，错误码 `TASK_NOT_FOUND`。
3. 未完成任务返回 HTTP 409，错误码 `FEEDBACK_NOT_READY`。
4. 成功反馈返回 HTTP 201，保存后的 `feedback.before_value` 和 `feedback.after_value` 都会出现在响应中。
5. 成功反馈会写入 `human_feedback` 表，并额外写入 `human_feedback_effect` Artifact。
6. 成功反馈后任务进入 `human_reviewing`，metadata 带 `requires_analysis_recompute=true` 和 `human_feedback_reanalysis` 历史。
7. 当前不会直接修改已缓存的 report/profile/battlefield/trace 聚合结果；后续真正局部重算完成后再由重算流程刷新这些产物。

### 边界与后续接口关系

1. 第 25 步实现的是“保存反馈 + 标记待重算”，不是完整 Human Review 闭环；完整闭环在后续步骤 36 验证。
2. 当前 API 不允许自由改写整份报告，也不允许通过 Claim `update_field` 改写结论正文，避免绕过证据链和 QA。
3. 当前仍复用同步 workflow 生成反馈上下文，后续后台任务和底层 Artifact 持久化落地后，可改为优先读取已持久化的结构化 Artifact。
4. 没有引入新基础设施；仍使用 FastAPI、Pydantic、LangGraph、SQLite 和 SQLAlchemy。

### 当前验证契约

1. 新增 `backend/tests/test_feedback_api.py`，验证允许范围内的产品画像字段反馈可以保存，且自动记录 before/after。
2. 验证 Claim 采纳状态反馈可以保存，且记录状态变更前后值。
3. 验证不允许通过 Feedback API 自由改写报告或 Claim 正文。
4. 验证反馈提交后写入 `human_feedback_effect` Artifact，并标记 `marked_for_reanalysis`。
5. 验证未完成任务反馈返回 `FEEDBACK_NOT_READY`，缺失任务返回 `TASK_NOT_FOUND`。
6. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_feedback_api.py` 通过，6 个测试通过。
7. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_feedback_api.py backend\tests\test_tasks_api.py backend\tests\test_profile_api.py backend\tests\test_battlefield_api.py backend\tests\test_trace_api.py backend\tests\test_reports_api.py backend\tests\test_workflow.py backend\tests\test_storage_repositories.py` 通过，46 个测试通过。
8. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests` 通过，142 个测试通过。
9. 当前已验证 `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend` 通过。

### 未开始事项

1. 尚未开始步骤 26 的前端路由与整体布局。
2. 尚未实现真正的 Human Feedback 后 Analysis 局部重算后台执行。
3. 尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 27 前端 API Client 与 OpenAPI 类型同步

当前项目已完成实施计划步骤 27，前端 API 边界由统一 `ApiClient`、统一请求状态、OpenAPI 生成类型和可复用错误态组件组成。该步骤只完成接口基础设施和类型同步，不进入步骤 28 的输入页表单或任务创建调用。

### API Client 边界

1. `frontend/src/api/client.ts` 是前端唯一真实 HTTP 请求入口。真实接口通过 `FetchApiTransport` 拼接 Base URL、路径、query、请求体和请求头，并统一解析后端 `data`、`error`、`trace_id` 响应结构。
2. 后端错误响应会转为 `ApiClientError`，保留 `code`、`message`、`details`、HTTP `status` 和 `traceId`，供页面统一展示。
3. `MockApiTransport` 仍作为显式开发数据入口存在；只有传入 `sourceMode: "mock"` 和 `mockTransport` 时才启用，避免真实请求和开发 fixture 混在页面组件里。
4. `frontend/src/api/state.ts` 统一表达 `idle`、`loading`、`success`、`empty`、`error` 和 `retrying` 状态，后续页面不需要各自发明请求状态结构。
5. `frontend/src/api/RequestStateMessage.tsx` 统一展示加载、空态、错误消息、错误码、Trace ID 和重试入口，避免接口失败时静默吞掉。

### OpenAPI 类型同步

1. `frontend/src/api/schema.ts` 由后端 FastAPI OpenAPI 自动生成，不手工维护。
2. `scripts/sync-openapi-types.mjs` 会调用后端 `create_app().openapi()` 导出当前 OpenAPI schema，再通过 `openapi-typescript` 生成 TypeScript `paths`、`operations` 和 `components` 类型。
3. `npm --prefix frontend run sync:types` 是当前类型同步入口。后端 API response model、request schema、路径或 query 参数变化后，应重新运行该脚本并提交生成结果。
4. `frontend/src/api/contracts.test.ts` 使用生成的 `operations`、`paths` 和 `components` 做类型级契约检查，覆盖 `POST /tasks`、`GET /tasks/{task_id}`、profile、battlefield、trace、report 和 feedback 接口。
5. `frontend/src/api/index.ts` 统一导出 API Client、请求状态工具、错误态组件和生成类型；后续页面应从该层引用接口能力，不绕过该层直接拼请求。

### 与临时类型和开发 fixture 的关系

1. `frontend/src/types/domain.ts` 仍保留为前端开发 fixture 的临时业务类型层，用于组件开发和测试。
2. 真实后端接口字段以 `frontend/src/api/schema.ts` 为准；后续页面联调时如果临时类型和 OpenAPI 生成类型冲突，优先修正临时类型或页面映射。
3. `frontend/src/mocks/*` 仍只用于开发和组件测试，不能作为最终 Demo 数据或真实 Trace/报告能力。

### 当前验证契约

1. `frontend/src/api/client.test.ts` 覆盖成功响应解析、错误响应解析、真实请求入口和 mock 入口切换。
2. `frontend/src/api/state.test.ts` 覆盖加载、错误、空数据和重试状态。
3. `frontend/src/api/contracts.test.ts` 覆盖 OpenAPI 生成类型与前端 API 契约字段一致性。
4. `frontend/src/api/RequestStateMessage.test.tsx` 覆盖组件错误态展示，确认错误消息、错误码、Trace ID 和重试入口可见。
5. 当前已验证 `npm --prefix frontend run sync:types`、`npm --prefix frontend run test`、`npm --prefix frontend run lint`、`npm --prefix frontend run build` 和 `npm --prefix frontend run format:check` 通过。

### 未开始事项

1. 尚未开始步骤 28 的输入页实现。
2. 尚未在页面中调用 `POST /tasks` 创建任务。
3. 尚未实现创建成功后的过程追踪页跳转。
4. 尚未实现步骤 29 的任务状态轮询。

## 2026-05-27：步骤 28 前端输入页

当前项目已完成实施计划步骤 28，前端输入页具备真实任务创建表单，可通过统一 `ApiClient` 调用 `POST /tasks`，并在创建成功后跳转到过程追踪页。该步骤只实现输入页、任务创建 mutation、错误展示和跳转，不进入步骤 29 的任务状态轮询。

### 输入页结构

1. `frontend/src/App.tsx` 将 `/` 路由从占位模块替换为 `TaskInputPage`，保留产品画像、竞争图谱、报告和过程追踪页的既有占位骨架。
2. 输入页包含 `target_product_name`、`target_product_url`、`category`、`subcategory`、`data_source_mode` 和 `research_text` 六个任务创建字段。
3. 表单默认使用 Demo 主线目标产品“小佩自动猫砂盆 MAX PRO 2 可视电动猫砂盆”，品类为 `smart_pet_hardware`，子类为 `automatic_litter_box`，数据模式为 `demo_snapshot`。
4. 数据模式提供 `demo_snapshot` 和 `snapshot_plus_live` 两个单选项；选择 `snapshot_plus_live` 时展示稳定性提示，说明 MVP 会记录该模式并使用本地快照兜底。
5. 提交摘要侧栏展示默认目标、提交后页面和当前数据模式，避免用户误以为步骤 28 已经实现状态轮询或完整结果页。

### API 调用与错误处理

1. 任务创建只通过第 27 步的统一 `ApiClient.post("/tasks", payload)` 完成，不在组件中直接拼接 `fetch` 或裸 URL。
2. 表单提交前执行前端必填校验：目标产品名称、品类和子类不能为空；校验失败时不调用 API。
3. 提交 payload 使用 `frontend/src/api/schema.ts` 生成的 `TaskCreateRequest` 类型，保持与后端 OpenAPI 契约一致。
4. API 错误继续复用 `RequestStateMessage` 展示错误消息、错误码和 Trace ID，避免任务创建失败时静默吞掉。
5. 创建成功后跳转到 `/trace?task_id=<task_id>`，符合“创建任务后默认跳转 Agent Trace 页”的既有产品决策。

### 样式与测试配置

1. `frontend/src/App.css` 新增输入表单、数据模式选项、稳定性提示、提交摘要和错误态样式，继续保持数据密集型工作台风格，不做营销页。
2. `frontend/src/App.test.tsx` 扩展为输入页组件与集成测试，覆盖必填校验、默认本地快照模式、合法表单创建任务、增强模式提示和 API 错误展示。
3. `frontend/vite.config.ts` 将 Vitest pool 调整为 `vmThreads`。旧中文路径工作区下默认 `threads` worker 在本机出现启动超时；`vmThreads` 能保持同一测试命令稳定通过，不改变业务逻辑。

### 当前边界

1. 步骤 28 不实现任务状态轮询，不调用 `GET /tasks/{task_id}`。
2. 步骤 28 不拉取 Trace、Profile、Battlefield 或 Report 数据。
3. 创建任务后只完成页面跳转，Trace 页仍保持第 26 步占位骨架；运行态刷新留给步骤 29。
4. 未引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL 或其他未批准复杂基础设施。

### 当前验证契约

1. `App.test.tsx` 确认必填字段缺失时不会提交任务。
2. `App.test.tsx` 确认默认数据模式为本地快照。
3. `App.test.tsx` 确认提交合法表单会调用 `POST /tasks`，并跳转到 `/trace?task_id=...`。
4. `App.test.tsx` 确认选择 `snapshot_plus_live` 会展示稳定性提示。
5. `App.test.tsx` 确认任务创建 API 错误会展示给用户。
6. 当前已验证 `npm --prefix frontend run test -- App.test.tsx` 通过，12 个测试通过。

### 未开始事项

1. 尚未开始步骤 29 的任务状态轮询。
2. 尚未实现页面刷新后基于任务 ID 恢复状态。
3. 尚未在过程追踪页调用 Trace API。

## 2026-05-27：项目根目录迁移到 D:\pythonproject\zijieagent

当前项目根目录已从旧中文路径迁移到 `D:\pythonproject\zijieagent`，用于规避 Vite 8 / Rolldown 在中文绝对路径下构建 `index.html` 时的路径解析问题。迁移本身不改变业务架构、API 契约或实施计划边界。

### 迁移处理

1. 新根目录保留 `backend/`、`data/`、`demo/`、`docs/`、`memory-bank/`、`scripts/`、`third_party/`、`AGENTS.md` 和项目根文档。
2. 旧路径中迁移失败的 `frontend/` 已补齐到 `D:\pythonproject\zijieagent\frontend`。
3. 前端只迁移源码、配置和 lock 文件；`node_modules/`、`dist/`、`.npm-cache/` 作为可再生成产物未从旧路径复制。
4. 后端依赖按 `backend/requirements-dev.txt` 在新路径环境补齐，`langgraph` 已安装到 `backend/.conda312`。
5. `backend/app/main.py` 新增本地 Vite CORS 白名单，允许 `http://127.0.0.1:5173`、`http://localhost:5173` 以及 Vite 备用端口 5174 调用任务创建等 API；未知 Origin 预检不会放行。

### 迁移后验证

1. `backend\.conda312\python.exe -m pytest backend\tests -p no:cacheprovider`：通过，144 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests\test_cors.py backend\tests\test_tasks_api.py backend\tests\test_api_response.py -p no:cacheprovider`：通过，14 个测试通过。
3. `backend\.conda312\python.exe -m ruff check backend`：通过。
4. `npm --prefix frontend run test`：通过，6 个测试文件、27 个测试通过。
5. `npm --prefix frontend run lint`：通过。
6. `npm --prefix frontend run build`：通过。
7. `npm --prefix frontend run format:check`：通过。

### 边界

1. 本次迁移与 CORS 联调仍属于步骤 28 收尾，不进入步骤 29。
2. 尚未实现任务状态轮询、刷新后任务状态恢复或 Trace 页真实数据拉取。

### Vitest setupFiles 路径修复

迁移后前端测试不再依赖全局 `setupFiles` 加载 `src/test/setup.ts`，避免 Codex 沙箱映射与宿主绝对路径不一致时解析失败。需要 `@testing-library/jest-dom` matcher 的测试文件改为本地显式导入 `@testing-library/jest-dom/vitest`。该调整属于测试运行环境稳定性修复，不改变前端路由、任务创建 API 调用、成功跳转或步骤 28/29 边界。

### 本地联调运行约束

1. 前端开发页继续使用 `http://127.0.0.1:5173/`。
2. 后端开发服务继续使用 `http://127.0.0.1:8000/`，但必须从真实项目根目录 `D:\pythonproject\zijieagent` 启动，确保默认 SQLite `data/competitive_intelligence.db` 可写。
3. CORS 只放行本地开发 Origin：`http://127.0.0.1` / `http://localhost` 的 Vite 常用端口 51xx，以及预览端口 41xx；未知远程 Origin 预检不会放行。
4. 为兼容 Chrome Private Network Access 预检，后端 `CORSMiddleware` 启用 `allow_private_network=True`；否则前端点击“启动分析任务”可能在到达 `POST /tasks` 前被浏览器拦截并显示客户端请求失败。
5. 本地联调若出现 `sqlite3.OperationalError: attempt to write a readonly database`，优先检查后端是否误从沙箱镜像或旧路径启动；这属于运行目录问题，不属于 `POST /tasks` 契约变化。
6. 前端默认 API Base URL 会跟随页面 hostname：从 `http://localhost:5173/` 打开时请求 `http://localhost:8000`，从 `http://127.0.0.1:5173/` 打开时请求 `http://127.0.0.1:8000`；仍可通过 `VITE_API_BASE_URL` 显式覆盖。
7. 前端 fetch 网络层失败会显示 `NETWORK_ERROR`，用于区分“浏览器未能连接后端/CORS 拦截/服务未重载”和后端已返回的标准业务错误。
8. `FetchApiTransport` 保存浏览器原生 `fetch` 时必须绑定 `globalThis`，避免把 `fetch` 作为普通函数调用后触发浏览器 `fetch called on an object that does not implement interface Window` 错误。

## 2026-05-27：步骤 29 前端任务状态轮询

当前项目已完成实施计划步骤 29，前端过程追踪页可以基于 URL 中的 `task_id` 恢复任务状态，并通过 TanStack Query 轮询 `GET /tasks/{task_id}`。该步骤只实现任务状态轮询与刷新恢复，不拉取真实 Trace 数据，也不进入步骤 30 的产品画像页。

### 前端轮询架构

1. 新增前端运行时依赖 `@tanstack/react-query`，符合 `memory-bank/tech-stack.md` 推荐栈，未引入 Redux、Zustand、Next.js 或 Tailwind。
2. `frontend/src/App.tsx` 在应用根部创建 `QueryClientProvider`，作为后续页面复用 TanStack Query 的服务端状态入口。
3. `/trace?task_id=<task_id>` 由 `TraceTaskStatusPage` 读取 URL 参数并调用 `ApiClient.get("/tasks/{task_id}")`，不绕过第 27 步统一 API Client。
4. 轮询间隔固定为 1000ms，满足实施计划“任务运行中每 1 到 2 秒刷新”的约束。
5. 运行中状态包括 `created`、`collecting`、`analyzing`、`reviewing`、`writing`；终止轮询状态包括 `completed`、`failed`、`partial_failed`、`human_reviewing`。
6. 当任务状态为 `failed` 或 `partial_failed` 时，页面显示明确失败提示；当任务完成或进入人工复核态时显示“已停止轮询”。
7. `/trace` 没有 `task_id` 时显示空态提示，引导用户从输入页创建任务或使用 `/trace?task_id=<task_id>` 恢复。

### 当前 Trace 页边界

1. 第 29 步只展示任务基础状态、目标产品、数据模式、更新时间和轮询状态。
2. Trace 页仍保留流程状态、运行记录、质检打回、差异视图四个模块骨架，但不调用 `GET /tasks/{task_id}/trace`。
3. 不展示 DAG、Agent Run、Tool Call、Token、QA 打回或 Diff 真实数据；这些仍留给后续步骤 33。
4. 不实现产品画像、竞争图谱或报告数据渲染；步骤 30 之前不调用 profile API。

### 测试与工具链稳定性

1. `frontend/src/App.test.tsx` 新增第 29 步测试，覆盖运行中任务持续轮询、完成任务停止轮询、失败任务错误提示和刷新后从 URL 恢复状态。
2. `frontend/vite.config.ts` 显式固定 `root` 为前端目录，并将 Vite 缓存目录调整为 `frontend/.vite-cache`，避免 Codex 沙箱映射下 Vitest 把测试文件解析成宿主 `/@fs/D:/...` 路径后加载失败。
3. `frontend/package.json` 的 `test` 脚本改为 `vitest run --configLoader runner`，绕开 Vite 默认配置打包写入 `node_modules/.vite-temp` 时的 Windows 文件锁问题。
4. `.gitignore`、`frontend/.prettierignore` 和 `frontend/eslint.config.js` 已忽略 `frontend/.vite-cache`，避免缓存产物进入版本控制、lint 或格式检查。

### 当前验证契约

1. `npm --prefix frontend run test`：通过，6 个测试文件、31 个测试通过。
2. `npm --prefix frontend run lint`：通过。
3. `npm --prefix frontend run build`：通过。
4. `npm --prefix frontend run format:check`：通过。

### 未开始事项

1. 尚未开始步骤 30 的产品画像页。
2. 尚未调用 `GET /tasks/{task_id}/profile`。
3. 尚未实现 Trace API 数据拉取或真实 DAG 渲染。

## 2026-05-27：步骤 30 前端产品画像页

当前项目已完成实施计划步骤 30，前端产品画像页可以基于 URL 中的 `task_id` 调用 `GET /tasks/{task_id}/profile`，并渲染基础信息、FeatureTree、PricingModel、UserPersona 和 Evidence 摘要。该步骤只实现产品画像页和有限 Human Review 入口；随后已按用户确认继续完成步骤 31，见下一节记录。

### 前端画像页架构

1. `frontend/src/App.tsx` 在 `/profile?task_id=<task_id>` 路由下渲染 `ProductProfilePage`，从 URL 读取任务 ID，并通过 TanStack Query 调用统一 `ApiClient.get("/tasks/{task_id}/profile")`。
2. 页面请求状态继续复用第 27 步的 `RequestStateMessage` 和请求状态工具，Profile API 加载、错误和重试入口不在组件里散落实现。
3. `ProductBasicsCard` 渲染目标产品基础信息，包括品牌、店铺、商品链接、价格区间、标签和风险标记。
4. `FeatureTreeCard` 渲染清洁能力、除臭能力、安全能力和维护体验，缺失列表统一显示“暂无可靠数据”。
5. `PricingModelCard` 渲染价格带、价格区间、促销、套装说明和价格证据状态；当价格 Evidence 缺少访问时间时，页面显示“价格证据：暂无可靠数据”和风险标记。
6. `UserPersonaCard` 渲染目标人群、痛点、使用场景和决策因素，并在 `is_inference=true` 时显示推断提示。
7. `EvidenceSummaryCard` 渲染短 Evidence 摘要、来源、访问时间状态和风险标记，继续保持证据链可追溯展示。
8. 页面顶部状态标记对 `/profile` 显示“画像数据就绪”，避免产品画像页仍呈现占位状态。

### Human Review 边界

1. `HumanReviewPanel` 只暴露产品画像结构化字段，不提供自由改写整份报告的入口。
2. 当前允许修正的产品字段包括 `brand`、`shop_name`、`product_url` 和 `tags`。
3. 当前允许修正的 FeatureTree 字段包括 `cleaning_capability`、`odor_control` 和 `safety_features`。
4. 当前允许修正的 PricingModel 字段包括 `price_band`、`promotions` 和 `bundle_description`。
5. 当前允许修正的 UserPersona 字段包括 `personas`、`pain_points`、`scenarios` 和 `decision_factors`。
6. 表单提交通过 `ApiClient.post("/tasks/{task_id}/feedback", payload)` 调用第 25 步 Feedback API，payload 使用 OpenAPI 生成的 `HumanFeedbackCreateRequest` 类型。
7. 列表字段在前端按换行、中英文逗号切分为数组；单值字段按文本提交，空值会被前端拦截。
8. 成功提交后页面显示“人工修正已提交，已标记 Analysis 局部重算”；真正重算闭环仍由后续步骤处理。

### 样式与响应式

1. `frontend/src/App.css` 新增产品画像双栏布局：左侧为画像卡片网格，右侧为有限 Human Review 面板。
2. 卡片用于独立画像模块和 Evidence 条目，不把页面大区块做成嵌套卡片。
3. 风险标记、缺失数据和推断提示使用稳定的文本与颜色样式表达，避免把无证据内容伪装成确定结论。
4. 窄屏下画像内容和 Human Review 面板改为单列展示，避免 Evidence 列表和表单控件重叠。

### 当前验证契约

1. `frontend/src/App.test.tsx` 覆盖产品画像五个模块渲染。
2. `frontend/src/App.test.tsx` 覆盖缺失价格访问时间时显示风险状态。
3. `frontend/src/App.test.tsx` 覆盖 Human Review 表单只暴露允许字段，不暴露“整份报告”或“Claim 正文”。
4. `frontend/src/App.test.tsx` 覆盖提交 Human Review 后调用 Feedback API，并在页面显示成功状态。
5. 当前已验证 `npm --prefix frontend run test` 通过，6 个测试文件、38 个测试通过。
6. 当前已验证 `npm --prefix frontend run lint`、`npm --prefix frontend run build` 和 `npm --prefix frontend run format:check` 通过。

### 当时未开始事项

1. 当时尚未开始步骤 31 的竞争图谱页；当前已完成，见下一节记录。
2. 当时尚未调用 `GET /tasks/{task_id}/battlefield`；当前已完成前端接入。
3. 当时尚未使用 React Flow 展示竞争关系图；当前已通过 `@xyflow/react` 渲染。
4. 当时尚未实现价格带、人群、使用场景切片切换；当前已完成切片拨盘和重新请求。

## 2026-05-27：步骤 31 前端竞争图谱页

当前项目已完成实施计划步骤 31，前端竞争图谱页可以基于 URL 中的 `task_id` 调用 `GET /tasks/{task_id}/battlefield`，使用 React Flow 展示竞争关系图，并支持价格带、人群和使用场景切片切换。该步骤只实现竞争图谱页，不进入步骤 32 的报告页。

### 前端图谱架构

1. 新增运行时依赖 `@xyflow/react`，继续使用 `memory-bank/tech-stack.md` 推荐的 React Flow 技术选择，没有引入 AntV G6、ECharts、Redux、Tailwind 或新的基础设施。
2. `frontend/src/App.tsx` 在 `/battlefield?task_id=<task_id>` 路由下渲染 `BattlefieldPage`，从 URL 读取任务 ID，并通过 TanStack Query 调用统一 `ApiClient.get("/tasks/{task_id}/battlefield", { query })`。
3. Battlefield 查询 key 包含 `taskId`、`price_band`、`persona` 和 `scenario`，确保切片变化会触发重新请求。
4. 查询参数直接来自本地 `selectedSlice`，只发送当前选中的切片字段；没有选中时发送空 query。
5. Battlefield 查询使用 `placeholderData: previousData => previousData` 保留上一帧图谱，降低切片 refetch 时图谱闪空风险。
6. 页面请求状态继续复用第 27 步的 `RequestStateMessage`，加载、错误和重试入口不在图谱组件内分散实现。

### 竞争关系图与详情面板

1. `toBattlefieldFlowElements` 将后端返回的 `graph_nodes` 和 `graph_edges` 映射为 React Flow 节点与边。
2. 节点展示目标产品、直接竞品、渠道替代和需求替代等角色标签，并展示品牌或店铺信息；目标产品固定在左侧，竞品按两列布局展开。
3. 边标签展示 `edge_score` 百分分值，`risk_status=at_risk` 的边使用动画和风险色提示。
4. 点击 React Flow 边会更新右侧选中竞争边；没有手动选择时默认展示第一条竞争边。
5. `SliceDial` 提供价格带、人群、使用场景三个切片控件，选项来自 `available_slices` 去重结果。
6. 切片摘要使用前端本地 `selectedSlice` 渲染，避免在后端响应尚未返回时显示旧切片。
7. `DecisionChainPanel` 展示决策链阶段、平均竞争分、关联边数量、Claim 数和 Evidence 数。
8. `BattlefieldInsightPanel` 展示选中边的竞争类型、总分、风险状态、五维评分拆解、评分说明、Claim 与 Evidence 绑定、证据卡片和 QA 打回记录。

### 证据与 QA 展示边界

1. 证据卡片来自 Battlefield API 的 `evidence_cards`，并优先按当前选中边的 `evidence_ids` 过滤。
2. Claim 区域展示 `claim_id`、正文、置信度、状态和绑定 Evidence ID，继续保留 Claim 与 Evidence 的追溯关系。
3. QA 摘要展示 `qa_status`、ReviewTask 数量、打回消息数量、风险 Claim 和风险 Edge 数量。
4. 本步只展示 Battlefield API 已返回的 QA 摘要，不拉取 `GET /tasks/{task_id}/trace`，不渲染真实 LangGraph DAG。

### 布局与响应式

1. `frontend/src/App.css` 新增 `.battlefield-layout`，桌面宽度使用 `minmax(0, 1fr) 360px` 双栏布局，左侧承载切片、图谱和决策链，右侧承载竞争边详情。
2. React Flow 容器 `.competition-flow` 使用稳定高度和最小高度约束，避免图谱加载、边标签和节点内容导致布局跳动。
3. `.battlefield-side` 在桌面宽度使用 sticky 侧栏，窄屏下随主内容自然堆叠。
4. `@media (max-width: 920px)` 下竞争图谱布局折叠为单列，降低窄屏下图谱与说明面板重叠风险。

### 当前验证契约

1. `frontend/src/App.test.tsx` 新增 ResizeObserver mock，以便 React Flow 在 jsdom 环境稳定渲染。
2. 组件测试覆盖 Battlefield API 节点和边渲染。
3. 组件测试覆盖切换价格带后更新选中状态文案。
4. 集成测试覆盖切片变化后重新请求 Battlefield API，并携带 query 参数。
5. 组件测试覆盖评分解释、五维评分拆解、Evidence 卡片和 QA 打回记录渲染。
6. 当前已验证 `npm --prefix frontend run test` 通过，6 个测试文件、41 个测试通过。
7. 当前已验证 `npm --prefix frontend run lint`、`npm --prefix frontend run build` 和 `npm --prefix frontend run format:check` 通过。
8. 当前已补齐 Playwright 视觉截图验证，确认桌面宽度下竞争关系图和右侧详情面板不重叠。

### 未开始事项

1. 尚未开始步骤 32 的报告页。
2. 尚未调用 `GET /tasks/{task_id}/report`。
3. 尚未实现报告九章节渲染、等待态或 Markdown 导出按钮。
4. 尚未实现步骤 33 的 Trace API 真实 DAG、Agent Run、Tool Call、Token、QA 打回和 Diff 渲染。

## 2026-05-28：Playwright 工具链补齐

当前项目已按用户确认补齐 Playwright 前端测试工具链，用于后续视觉截图和端到端演示路径验证。该调整属于测试工具链准备，不改变第 31 步竞争图谱页架构，也不开始步骤 32 的报告页。

### 工具链状态

1. `frontend/package.json` 新增开发依赖 `@playwright/test@1.60.0`。
2. `frontend/package-lock.json` 已锁定 `@playwright/test`、`playwright` 和 `playwright-core` 依赖版本。
3. Playwright Chromium、Chromium headless shell、FFmpeg 和 Winldd 已安装到本机 Playwright 缓存目录 `C:\Users\15298\AppData\Local\ms-playwright`。
4. 已新增竞争图谱页专用 Playwright 视觉测试；完整端到端路径和报告页截图验证留给后续步骤。

### 验证契约

1. `npm --prefix frontend exec playwright -- --version` 已验证 CLI 可用，版本为 `1.60.0`。
2. Playwright headless Chromium 已通过最小启动检查，可打开 `frontend/dist/index.html` 并读取页面标题。
3. 现有前端质量门禁在依赖安装后仍通过：`npm --prefix frontend run test`、`lint`、`build` 和 `format:check`。
4. 由于浏览器二进制写入用户缓存目录，初次安装需要在沙箱外运行；后续本机重复运行通常不需要再次下载。

### 后续使用边界

1. 第 31 步竞争图谱页已有组件测试和 Playwright 桌面视觉 smoke 覆盖。
2. 第 39 步仍负责完整演示路径 Playwright 测试，覆盖输入页、过程追踪页、产品画像页、竞争图谱页、报告页、Markdown 导出和 QA 打回记录。

## 2026-05-28：步骤 31 Playwright 视觉验证补齐

当前项目已补齐实施计划步骤 31 的桌面视觉验证。该补充只面向竞争图谱页，不改变业务 API 契约，不进入步骤 32 的报告页。

### 新增测试结构

1. `frontend/playwright.config.ts`：Playwright 配置入口，测试目录为 `frontend/e2e`，输出目录为 `frontend/test-results`，HTML 报告目录为 `frontend/playwright-report`，项目使用 Chromium 桌面视口 `1366x900`。
2. `frontend/e2e/battlefield.visual.spec.ts`：竞争图谱页视觉 smoke。测试在进程内先调用 Vite `build()`，再用 Vite `preview()` 启动本地静态预览服务。
3. 用例通过 `page.route("**/tasks/task_battlefield_visual/battlefield**", ...)` 拦截 Battlefield API，返回稳定结构化数据，避免依赖真实后端数据库状态。
4. 测试断言 React Flow 至少渲染 2 个节点和 1 条边，竞争关系图区域和右侧详情面板均可见。
5. 测试读取图谱区域与详情面板的 bounding box，确认桌面宽度下图谱右边界不超过详情面板左边界，覆盖“图和说明面板不重叠”的步骤 31 视觉验收项。
6. 测试会保存 `battlefield-desktop.png` 截图到 Playwright 当前测试输出目录，供失败排查或本地复核。

### 工具链边界

1. `npm --prefix frontend run test:e2e` 是当前 Playwright 测试入口。
2. `frontend/vite.config.ts` 排除 `e2e/**`，避免 Vitest 误加载 Playwright 测试。
3. `.gitignore`、`frontend/.prettierignore` 和 `frontend/eslint.config.js` 忽略 `frontend/test-results/` 与 `frontend/playwright-report/`，避免截图、trace 和 HTML 报告进入常规检查或版本控制。
4. Playwright 视觉 smoke 只验证竞争图谱页，不覆盖输入页、报告页、Trace 页完整演示链路；完整链路仍留给步骤 39。

### 当前验证契约

1. `npm --prefix frontend run test:e2e -- e2e/battlefield.visual.spec.ts`：通过，1 个 Chromium 用例通过。
2. `npm --prefix frontend run test`：通过，6 个测试文件、41 个测试通过。
3. `npm --prefix frontend run lint`：通过。
4. `npm --prefix frontend run build`：通过。
5. `npm --prefix frontend run format:check`：通过。

## 2026-05-28：步骤 32 前端报告页

当前项目已完成实施计划步骤 32，前端报告页可以基于 URL 中的 `task_id` 调用 `GET /tasks/{task_id}/report` 渲染网页报告，并通过 `GET /tasks/{task_id}/report/markdown` 触发 Markdown 导出。该步骤只实现报告页，不进入步骤 33 的真实 Trace DAG 渲染。

### 前端报告页架构

1. `frontend/src/App.tsx` 在 `/report?task_id=<task_id>` 路由下渲染 `ReportPage`，从 URL 读取任务 ID，并通过 TanStack Query 调用统一 `ApiClient.get("/tasks/{task_id}/report")`。
2. 报告页继续复用第 27 步的统一 API Client 与 `RequestStateMessage`，加载、错误、重试和导出失败展示不绕过统一请求状态处理。
3. 报告数据使用后端 OpenAPI 类型 `ReportData` 和 `ReportSection`，不手写临时接口字段。
4. 报告章节按固定 `REPORT_SECTION_KEYS` 顺序输出九章：执行摘要、目标产品画像、竞品发现、动态竞争切片、决策链竞争分析、用户研究洞察、可执行建议、QA 审查摘要和 Evidence 索引。
5. 如果后端响应缺少某个章节，前端在对应顺序位置生成占位章节并显示“暂无可靠数据”，避免报告结构跳动或把后续章节提前。

### 报告内容展示

1. 页面顶部展示 Report ID、生成时间和章节数量，便于演示和导出核对。
2. `ReportSectionCard` 展示章节 ID、标题、摘要、结构化条目、Claim 引用、Evidence 引用和风险标记。
3. `renderReportValue` 负责展示布尔值、分数、访问时间、数组和嵌套对象；缺失值统一显示“暂无可靠数据”。
4. 竞品发现、建议和 Evidence 索引章节会把关键字段提升为条目标题，降低评委阅读成本。
5. 风险标记继续复用现有 `RiskFlagList`，不把缺证据或推断内容伪装成确定结论。

### 等待态与 Markdown 导出

1. 当报告接口返回标准错误 `REPORT_NOT_READY` 时，页面显示 `ReportWaitingState`，展示当前任务状态和“重新检查”按钮。
2. `REPORT_NOT_READY` 不会被当作最终报告内容渲染，也不会显示九章报告网格。
3. `ReportContent` 中的 Markdown 导出按钮调用 `GET /tasks/{task_id}/report/markdown`。
4. 导出成功时展示后端返回的 `file_path`；导出失败时显示错误信息，同时保留已加载的网页报告。

### 布局与响应式

1. `frontend/src/App.css` 新增 `.report-layout`、`.report-toolbar`、`.report-section-grid`、`.report-section-card`、`.report-item`、`.report-reference-strip` 等样式。
2. 报告页保持数据密集型工作台风格，报告章节使用独立卡片，不嵌套页面级大卡片。
3. 窄屏下报告工具栏和章节网格折叠为单列，避免导出状态、章节内容和引用区重叠。

### 当前验证契约

1. `frontend/src/App.test.tsx` 覆盖九个报告章节渲染。
2. `frontend/src/App.test.tsx` 覆盖 `REPORT_NOT_READY` 等待态，确认未完成任务不会展示最终报告。
3. `frontend/src/App.test.tsx` 覆盖 Markdown 导出成功并调用 `/tasks/{task_id}/report/markdown`。
4. `frontend/src/App.test.tsx` 覆盖 Markdown 导出失败时显示错误且保留网页报告。
5. 当前已验证 `npm --prefix frontend run test` 通过，6 个测试文件、45 个测试通过。
6. 当前已验证 `npm --prefix frontend run lint`、`npm --prefix frontend run build` 和 `npm --prefix frontend run format:check` 通过。

### 未开始事项

1. 尚未开始步骤 33 的过程追踪页真实数据渲染。
2. 尚未在前端调用 `GET /tasks/{task_id}/trace`。
3. 尚未使用 React Flow 渲染 LangGraph DAG 状态。
4. 尚未展示真实 Agent Run、Tool Call、Token Usage、QA Review 和 Diff View。

## 2026-05-28：步骤 33 前端过程追踪页

当前项目已完成实施计划步骤 33，前端过程追踪页可以基于 URL 中的 `task_id` 调用 `GET /tasks/{task_id}/trace`，使用 React Flow 展示 LangGraph DAG 状态，并展示真实 Agent Run、Tool Call、Token Usage、QA Review、QA 打回消息、Diff View 和折叠脱敏 Prompt 预览。该步骤只实现过程追踪页真实数据渲染，不进入步骤 34 的前后端端到端任务流。

### 前端 Trace 页架构

1. `frontend/src/App.tsx` 在 `/trace?task_id=<task_id>` 路由下继续渲染 `TraceTaskStatusPage`，保留第 29 步基于 `GET /tasks/{task_id}` 的任务状态轮询。
2. `TraceTaskStatusPage` 新增 TanStack Query 查询 `ApiClient.get("/tasks/{task_id}/trace")`，查询 key 为 `["task-trace", taskId]`。
3. Trace 查询与任务状态共用运行中判断：任务处于 `created`、`collecting`、`analyzing`、`reviewing` 或 `writing` 时持续轮询，进入 `completed`、`failed`、`partial_failed` 或 `human_reviewing` 后停止。
4. Trace 数据使用后端 OpenAPI 生成的 `TraceData`、`TraceDagNode`、`TraceDagEdge`、`AgentRunLog`、`ToolCallLog`、`TokenUsageLog`、`ReviewTask`、`AgentMessage`、`TraceDiff` 和 `TracePromptPreview` 类型，不手写临时接口字段。
5. Trace 请求继续复用统一 `ApiClient` 与 `RequestStateMessage`，加载、错误和重试状态不在组件内分散实现。

### DAG 与过程数据展示

1. `TraceContent` 汇总展示 Trace View ID、workflow 状态、任务状态、生成时间、Agent Run 数量和 token 总量。
2. `toTraceFlowElements` 将后端 `dag_nodes` 与 `dag_edges` 映射为 React Flow 节点和边；不可见节点会被过滤，失败节点、当前节点和 QA 打回边保留视觉区分。
3. `TraceAgentRuns` 展示 Agent 名称、运行状态、Run ID、开始/结束时间、输入摘要、输出摘要和错误信息。
4. `TraceToolCalls` 展示工具名称、状态、Run ID、耗时、参数摘要和错误信息。
5. `TraceTokenUsage` 展示模型名、prompt tokens、completion tokens、total tokens 和总 token 统计。
6. `TraceQaReviews` 展示 QA 检查项、严重级别、issue code、目标对象、打回目标、状态和 required action。
7. `TraceRevisionMessages` 展示 QA 打回消息的发送方、接收方、消息类型、artifact 类型和结构化 payload。
8. `TraceDiffView` 以 Before/After 双列展示打回前后的 Evidence 或 Artifact 差异。

### Prompt 脱敏与安全边界

1. Prompt 预览使用 `<details>` 默认折叠展示，展开前只显示标题、Agent 和“已脱敏”状态。
2. `sanitizeTraceText` 会在前端二次替换 `sk-...`、`AKIA...` 以及 `api_key`、`token`、`secret`、`password`、`authorization` 等凭据样式文本。
3. `renderTraceValue` 对敏感 key 直接显示 `[已脱敏]`，避免嵌套 payload 中泄露凭据字段值。
4. 本步不展示完整系统 Prompt，不改变后端 Trace API 的脱敏职责，只在前端增加展示层保护。

### 样式与视觉验证

1. `frontend/src/App.css` 新增 Trace 相关布局：`.trace-layout`、`.trace-graph-panel`、`.trace-flow`、`.trace-side-panel`、`.trace-detail-grid`、`.trace-diff-grid` 和 `.trace-prompt-details`。
2. 桌面宽度下 Trace 页采用左侧 DAG、右侧摘要的双栏布局，下方承载 QA Review、打回消息、Diff 和 Prompt 预览。
3. 窄屏下 Trace 布局折叠为单列，Diff 与 Token 字段也切换为单列，避免长内容遮挡导航和主操作区。
4. `frontend/e2e/trace.visual.spec.ts` 使用 Playwright 拦截 Trace API 和任务状态 API，验证 Trace 页在桌面宽度下 DAG、摘要、QA、Diff 和折叠 Prompt 均可见，且页面无水平溢出。

### 当前验证契约

1. `frontend/src/App.test.tsx` 覆盖 Trace API 调用、DAG 区域渲染、Agent Run 列表、Tool Call 列表和 Token Usage 总量。
2. `frontend/src/App.test.tsx` 覆盖 QA Review、QA 打回消息和 Diff View 展示。
3. `frontend/src/App.test.tsx` 覆盖 Prompt 预览默认折叠和敏感凭据样式文本脱敏。
4. 当前已验证 `npm --prefix frontend run test` 通过，6 个测试文件、48 个测试通过。
5. 当前已验证 `npm --prefix frontend run lint`、`npm --prefix frontend run build` 和 `npm --prefix frontend run format:check` 通过。
6. 当前已验证 `npm --prefix frontend run test:e2e -- e2e/trace.visual.spec.ts` 通过，1 个 Chromium 用例通过。

### 后续边界

1. 尚未开始步骤 34 的前后端端到端任务流。
2. 本步不改变 `POST /tasks` 的后台任务执行方式，也不把创建任务、LangGraph 后台执行、前端轮询和最终页面跳转串成完整闭环。
3. 完整演示路径 Playwright 验证仍留给后续步骤 39。

## 2026-05-28：步骤 34 前后端端到端任务流

当前项目已完成实施计划步骤 34，`POST /tasks` 到 LangGraph 执行、Artifact 缓存、前端 Trace 轮询和结果页跳转已形成完整闭环。该步骤只打通常规任务完成链路，不进入步骤 35 的 QA 打回专项验证。

### 后端执行架构

1. 新增 `backend/app/services/task_execution.py`，提供 `TaskExecutionService` 作为任务执行编排层。
2. `TaskExecutionService.execute_task(task_id)` 从 `TaskRepository` 读取任务，将任务状态推进到 `collecting`，基于 `create_initial_state(task)` 构造 LangGraph 初始状态，并调用 `build_analysis_workflow()`。
3. Workflow 完成后，服务将最终状态转换并缓存为四类 Artifact：`trace_data`、`product_profile`、`battlefield_data` 和 `report_data`。
4. Trace、产品画像和竞争图谱复用既有服务层的结构化构造逻辑，保证 API 返回契约与前端页面一致；报告使用 Writer Agent 产出的最新 `ReportData`。
5. 任务执行成功后写回 `completed` 状态和执行摘要 metadata；执行异常时写回 `failed` 状态，并保留错误类型，避免前端无限轮询。
6. 执行链路继续依赖本地快照和规则流程；未配置模型 API Key 时仍可完成 Demo，不做真实外部采集。

### 任务 API 启动方式

1. `backend/app/main.py` 的 `create_app()` 新增 `auto_start_task_execution` 与 `run_task_execution_inline` 参数。
2. 运行时全局 `app = create_app(auto_start_task_execution=True)`，因此 Uvicorn 启动的后端会在 `POST /tasks` 成功后通过 FastAPI `BackgroundTasks` 自动执行任务。
3. 测试环境默认仍保持旧的只创建任务行为；需要验证完整链路时显式使用 `create_app(auto_start_task_execution=True, run_task_execution_inline=True)`，让任务同步执行并便于断言。
4. `routes_tasks.py` 在创建任务成功后统一调用启动钩子，并为测试保留 `app.state.task_execution_workflow_factory` 覆盖点。
5. 本设计没有引入 Celery、Redis、消息队列或独立 worker，符合 MVP 的后台任务与前端轮询约束。

### 前端闭环架构

1. 输入页沿用第 28 步的 `POST /tasks` 提交逻辑，创建成功后跳转 `/trace?task_id=<task_id>`。
2. `TraceTaskStatusPage` 同时轮询任务状态和 Trace；任务进入 `completed` 后，会按 `task_id + updated_at` 触发一次 Trace 重取，解决状态已完成但 Trace 仍是早期空数据的时序问题。
3. Trace 完成态展示结果入口：查看画像、查看图谱、查看报告，分别跳转到 `/profile`、`/battlefield`、`/report` 并保留同一个 `task_id`。
4. 工作台侧边导航在非输入页之间切换时通过 `routePathForTask()` 保留当前 `task_id`，支持从 Trace 到结果页、结果页之间以及刷新后的连续演示。
5. 产品画像页、竞争图谱页和报告页继续使用既有 API 与页面结构，不引入新的前端状态管理库。

### E2E 验证结构

1. 新增 `frontend/e2e/task-flow.e2e.spec.ts`，作为步骤 34 的真实前后端端到端验证。
2. 用例在测试进程中创建临时 SQLite 文件，启动后端 Uvicorn `app.main:app`，再用 `VITE_API_BASE_URL` 指向该后端构建并启动 Vite preview。
3. 浏览器从输入页点击“启动分析任务”，等待 `/trace?task_id=task_...`，确认任务完成、Trace Agent Run 和 LangGraph DAG 可见。
4. 用例随后打开产品画像、竞争图谱和分析报告，确认这些页面均使用真实 API 返回的数据渲染。
5. 后端新增 `backend/tests/test_task_execution.py`，覆盖同步执行入口和四类缓存 Artifact。
6. 前端组件测试补充完成态结果入口与跨页面 `task_id` 保留行为。

### 当前验证契约

1. `backend\.conda312\python.exe -m pytest backend\tests\test_tasks_api.py backend\tests\test_task_execution.py backend\tests\test_trace_api.py backend\tests\test_profile_api.py backend\tests\test_battlefield_api.py backend\tests\test_reports_api.py`：通过，31 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
3. `npm --prefix frontend run test -- App.test.tsx`：通过，31 个测试通过。
4. `npm --prefix frontend run lint`：通过。
5. `npm --prefix frontend run build`：通过。
6. `npm --prefix frontend run format:check`：通过。
7. `npm --prefix frontend run test:e2e -- e2e/task-flow.e2e.spec.ts`：通过，1 个 Chromium 用例通过。

### 后续边界

1. 尚未开始步骤 35 的 QA 打回专项验证。
2. 尚未编写“补齐一条缺失证据”的专项 E2E。
3. `snapshot_plus_live` 仍是增强模式占位，不进行真实外部采集。
4. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

## 2026-05-28：步骤 35 真实 QA 打回演示链路

当前项目已完成实施计划步骤 35，真实 QA 打回演示链路已从后端工作流、Trace API、竞争图谱 QA 摘要、报告数据和浏览器 E2E 多层验证。该步骤只加固 QA 打回专项链路，不进入步骤 36 的 Human Review 闭环。

### QA 状态同步架构

1. `backend/app/agents/qa.py` 新增 ReviewTask 同步逻辑：每次 QA 运行后，用当前规则结果和历史 `state["review_tasks"]` 对齐。
2. 如果历史 ReviewTask 仍被当前规则命中，则保持为当前打开问题；如果历史 `open` ReviewTask 已不再被命中，则标记为 `resolved` 并写入 `resolved_at`。
3. 最终 QA 元数据新增 `resolved_review_task_ids`，用于 Trace、报告和调试说明当前轮次解决了哪些历史问题。
4. 该逻辑不删除历史 ReviewTask，保证过程追踪页仍能展示最初的打回原因，同时下游 QA 摘要不会把已解决问题误判为开放风险。

### 真实打回链路

1. Demo 快照仍固定使用 `sku_01` 作为缺失证据样例，其原始 Evidence `ev_sku_01` 缺少 `source.access_time`。
2. 首次 QA 会生成 `TIMELY_EVIDENCE_MISSING_ACCESS_TIME` ReviewTask，目标 Agent 为 `collection_agent`，并生成 `revision_request`。
3. LangGraph 条件边根据 `metadata.qa_agent.revision_target == "collection_agent"` 回到 Collection Agent。
4. Collection Agent 读取 `qa_revision_fixture.repair_evidence`，生成修复证据 `ev_sku_01_repair_001`，写入 `collection_agent_repair` metadata 和 Diff。
5. Workflow 在 Collection 修复后追加 Analysis 重算消息，Analysis Agent 只重算受影响 Claim 和 CompetitionEdge，写入 `analysis_agent_recompute` metadata 和 Diff。
6. 第二次 QA 不再命中缺失访问时间问题，旧 ReviewTask 变为 `resolved`，随后 Writer Agent 生成最终报告。

### 报告与图谱输出约束

1. 竞争图谱 QA 摘要现在可以在完整链路完成后显示 `qa_status = passed`、开放 ReviewTask 为 0、已解决 ReviewTask 为 1。
2. 报告中的竞品发现 Claim 会使用修复后的 `ev_sku_01_repair_001`，不再把原始缺失访问时间的 `ev_sku_01` 作为强结论依据。
3. Trace Diff View 同时展示 Collection 修复前后 Evidence 差异和 Analysis 重算前后 Edge/Claim 差异。
4. Evidence 索引仍可保留原始 `ev_sku_01`，用于追溯打回来源；强结论引用的是修复后的 Evidence。

### E2E 验证结构

1. 新增 `frontend/e2e/qa-revision.e2e.spec.ts`，使用临时 SQLite 数据库和真实 Uvicorn 后端，不拦截 QA/Trace/Report API。
2. 用例从输入页启动任务，等待 Trace 完成后通过真实 API 断言 Collection、Analysis、QA 各运行两次，Writer 运行一次。
3. 用例验证 Trace API 中存在 Collection `revision_request`、`collection_agent_repair` Diff、`analysis_agent_recompute` Diff，且 ReviewTask 状态为 `resolved`。
4. 用例验证 Trace 页面可见 QA Review、QA 打回消息和 Diff View；竞争图谱页可见 QA 已通过、开放 0 条、已解决 1 条；报告页可见 QA 审查摘要、Collection 修复和 Analysis 重算。
5. 用例验证报告 API 中竞品发现 Claim 均有 Evidence，且不含 `missing_evidence` 或 `missing_access_time` 风险标记。
6. `frontend/playwright.config.ts` 设置 `workers: 1`，避免多个 E2E 并行运行时同时构建并写入 `frontend/dist/`。

### 当前验证契约

1. `backend\.conda312\python.exe -m pytest backend\tests\test_qa_agent.py backend\tests\test_collection_agent.py backend\tests\test_analysis_agent.py backend\tests\test_workflow.py backend\tests\test_trace_api.py backend\tests\test_task_execution.py backend\tests\test_battlefield_api.py backend\tests\test_reports_api.py`：通过，39 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
3. `npm --prefix frontend run test -- App.test.tsx`：通过，31 个测试通过。
4. `npm --prefix frontend run lint`：通过。
5. `npm --prefix frontend run build`：通过。
6. `npm --prefix frontend run format:check`：通过。
7. `npm --prefix frontend run test:e2e -- e2e/qa-revision.e2e.spec.ts`：通过，1 个 Chromium 用例通过。
8. `npm --prefix frontend run test:e2e`：通过，4 个 Chromium 用例通过。

### 后续边界

1. 尚未开始步骤 36 的 Human Review 闭环验证。
2. 本步未改变 HumanFeedback API、Human Review 表单或 Analysis 局部重算触发策略。
3. `snapshot_plus_live` 仍是增强模式占位，不进行真实外部采集。
4. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。

## 2026-05-28：步骤 36 Human Review 闭环

当前项目已完成实施计划步骤 36，Human Review 从“保存反馈并标记待重算”升级为“保存反馈、应用受控局部更新、刷新相关缓存结果、前端重新读取”的闭环。该步骤只完成 Human Review 闭环验证，不进入步骤 37。

### 后端闭环架构

1. `backend/app/services/feedback_service.py` 继续作为 `POST /tasks/{task_id}/feedback` 的唯一业务入口，仍只接受 `FeedbackTargetType` 与 `FeedbackAction` allowlist 内的受控反馈。
2. 提交反馈时，服务先基于当前任务构建工作流上下文，再计算 `before_value`、`after_value` 和受影响目标，生成并保存 `HumanFeedback`。
3. 允许的人工修正会应用到内存状态：
   - 产品画像字段更新会修改 `products`、`feature_trees`、`pricing_models` 或 `user_personas` 中对应结构化字段。
   - Claim 状态反馈会修改对应 Claim 的 `status`，并在非 accepted 状态下添加 `unreliable_data` 风险标记。
   - Evidence 备注会写入 `metadata.human_note`。
   - CompetitionEdge 移除反馈会标记 `human_adjusted`、降低 `edge_score` 并添加 `unreliable_data`。
   - Slice 更新会修改匹配竞争边的 `slice` 字段并标记人工调整。
4. 局部更新后重新构建并缓存三类结果 Artifact：
   - `product_profile`：用于产品画像页刷新。
   - 默认切片 `battlefield_data`：用于 Claim 状态和竞争边风险状态变化可见。
   - `trace_data`：用于 Trace 中保留人工反馈后的任务状态和局部更新 Diff。
5. `human_feedback_effect` Artifact 记录 `before_value`、`after_value`、受影响目标、缓存 Artifact ID 和 `applied_local_update` 状态，便于审计。
6. 任务状态继续更新为 `human_reviewing`，用于表达人工复核链路已介入；任务元数据 `requires_analysis_recompute` 设为 `false`，因为本步骤已完成本地受控更新。

### 读取服务调整

1. `ProfileService` 和 `BattlefieldService` 允许 `completed` 与 `human_reviewing` 两种状态读取结果。
2. `ReportService` 允许 `human_reviewing` 任务继续读取已有报告，避免人工复核后报告页不可访问。
3. `TraceService` 在 `human_reviewing` 状态优先读取缓存 Trace；如果缓存不存在，则返回任务记录级 Trace。
4. 这些读取放宽不改变未完成任务的保护边界，`created`、`collecting`、`analyzing` 等状态仍返回 not ready 错误。

### 前端闭环架构

1. 产品画像页的 `HumanReviewPanel` 继续只展示产品画像结构化 allowlist 字段，不提供整份报告或 Claim 正文自由编辑入口。
2. 提交成功后，面板清空输入并调用产品画像 query 的 `refetch()`。
3. 成功提示改为“人工修正已提交，相关结果已刷新”，与后端 `applied_local_update` 状态一致。
4. 组件测试验证反馈提交后 API 被调用、页面触发第二次 profile 拉取，并展示刷新后的品牌字段。

### 验证契约

1. `backend\.conda312\python.exe -m pytest tests\test_feedback_api.py`：通过，6 个测试通过。
2. `backend\.conda312\python.exe -m pytest tests\test_feedback_api.py tests\test_profile_api.py tests\test_battlefield_api.py tests\test_trace_api.py tests\test_reports_api.py`：通过，27 个测试通过。
3. `backend\.conda312\python.exe -m ruff check app\services\feedback_service.py app\services\profile_service.py app\services\battlefield_service.py app\services\report_service.py app\services\trace_service.py tests\test_feedback_api.py`：通过。
4. `npm test -- src/App.test.tsx`：通过，31 个测试通过。
5. `npx tsc --noEmit`：通过。
6. `npx vite build --configLoader runner --outDir ../.codex-run/frontend-dist-step36-verify`：通过。

### 边界

1. 本步骤没有放开自由文本改写报告，也没有允许人工覆盖任意 Markdown。
2. 本步骤没有引入外部采集、队列、缓存服务或新前端框架。
3. 本步骤没有开始步骤 37；在用户验证前继续停在步骤 36。

## 2026-05-29：步骤 37 异常与降级处理

当前项目已完成实施计划步骤 37，异常处理从“局部抛错或 API 返回错误”补齐为“快照缺失可诊断、模型结构化输出可重试/兜底、单 Agent 失败进入工作流失败态、Markdown 导出失败进入 Trace”。该步骤只完成异常与降级处理，不进入步骤 38 的安全与脱敏专项检查。

### 工作流失败态架构

1. `backend/app/graph/workflow.py` 为 Collection、Analysis、QA、Writer 节点增加异常包装：单个 Agent 抛出异常时，工作流会写入失败 Agent Run Log，并将任务状态设为 `failed`。
2. Collection 与 Analysis 节点后改为条件路由：如果工作流已经失败，直接进入终止分支，不再继续执行后续 Agent。
3. 失败元数据统一写入 `metadata.workflow`，包含 `status = failed`、`current_node`、`next_node = failed` 与 `failure_reason`。
4. Agent 自身已经记录失败日志时，工作流包装器不会重复写入同一 Agent 的失败 Run Log；如果异常发生在 Agent 自身日志生成之前，则由包装器补一条兜底失败 Run Log。

### 任务执行与 Trace

1. `TaskExecutionService` 继续作为后台任务执行编排层；当工作流返回失败态时，会缓存 `trace_data`，但不会缓存产品画像、竞争图谱或报告结果。
2. 如果工作流创建或执行阶段发生无法返回状态的异常，`TaskExecutionService` 会把任务标记为 `failed`，写入 `task_execution.failure_reason`，并缓存一份失败 Trace。
3. `TraceService` 支持读取 `failed` 任务的缓存 Trace；没有缓存时返回任务记录级失败骨架 Trace，避免失败任务查询 Trace 时重新触发工作流。
4. 失败 Trace 中 `failed` 终止节点保持可见，失败 Agent 节点会带有失败状态和对应 run id。

### 快照与模型降级

1. `SnapshotLoaderError` 的 `SNAPSHOT_NOT_FOUND` 路径保持为快照缺失的统一诊断入口，并通过测试覆盖缺失路径、错误码和错误消息。
2. 新增 `backend/app/services/structured_output.py`，提供 `coerce_structured_model_output()`，用于可选模型增强输出的结构化 JSON 对象解析。
3. 结构化输出处理最多读取两个候选输出；非 JSON、空文本或 JSON 非对象都会记录 `MODEL_OUTPUT_NON_STRUCTURED`，全部失败后返回调用方提供的 fallback。
4. 该能力不引入真实模型网络调用，只为后续可选 Doubao 增强提供本地可测的重试/兜底边界。

### Markdown 导出失败

1. `ReportService.export_markdown_report()` 在 Markdown 渲染或写文件失败时继续返回 `MARKDOWN_EXPORT_FAILED`，不删除或覆盖已有网页报告 Artifact。
2. Markdown 导出失败会写入 Trace metadata：`markdown_export_failures` 保留历史失败列表，`last_failure` 指向最近一次失败。
3. 失败记录包含 `report_id`、失败原因类型和记录时间，便于前端或调试时通过 Trace API 追溯。

### 验证契约

1. `backend\.conda312\python.exe -m pytest backend\tests\test_snapshot_loader.py backend\tests\test_structured_output.py backend\tests\test_workflow.py backend\tests\test_task_execution.py backend\tests\test_reports_api.py backend\tests\test_trace_api.py`：通过，29 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend\app\graph\__init__.py backend\app\graph\workflow.py backend\app\services\task_execution.py backend\app\services\trace_service.py backend\app\services\report_service.py backend\app\services\structured_output.py backend\tests\test_snapshot_loader.py backend\tests\test_structured_output.py backend\tests\test_workflow.py backend\tests\test_task_execution.py backend\tests\test_reports_api.py`：通过。
3. `backend\.conda312\python.exe -m pytest backend\tests`：通过，154 个测试通过。
4. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。

### 边界

1. 本步骤没有开始步骤 38 的安全与脱敏专项检查。
2. 本步骤没有引入外部采集、模型网络调用、Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
3. `snapshot_plus_live` 仍是增强模式占位，不进行真实外部采集。
4. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

## 2026-05-29：步骤 38 安全与脱敏专项

当前项目已完成实施计划步骤 38，安全与合规能力从“局部出口各自脱敏”收敛为“共享脱敏规则 + 关键出口递归扫描 + 前端兜底展示 + QA 敏感表达规则”。该步骤只完成安全与脱敏专项，不进入步骤 39。

### 共享脱敏层

1. 新增 `backend/app/security.py`，集中维护敏感 key、敏感文本模式和递归脱敏方法。
2. 脱敏规则覆盖 API Key、`sk-` 风格密钥、AWS `AKIA` 风格标识、Bearer、token、password、secret、完整环境变量名、手机号、地址、账号 ID、open_id、union_id、user_id 等。
3. `redact_sensitive_text()` 用于字符串出口，`redact_sensitive_value()` 用于 dict/list/tuple 递归出口，`contains_sensitive_text()` 用于导出前安全扫描。
4. Trace 专用调用启用 `redact_key_names=True`，在任意嵌套 metadata/payload/diff 中遇到敏感 key 时会改写 key 名，避免前端或 API 响应出现 `api_key` 等字段名。

### 后端出口约束

1. `backend/app/api/responses.py` 继续保留统一错误响应结构，但错误 message/details 现在复用共享脱敏规则，并结合当前环境变量值进行替换。
2. `backend/app/services/task_creation.py` 在创建任务时先脱敏 `research_text`，再保存到 SQLite 并返回给前端；如发生脱敏，任务 metadata 增加 `research_text_redacted = true`。
3. `backend/app/services/trace_service.py` 在构建 `TraceData` 后做递归脱敏，覆盖 Agent Run、Tool Call、QA Review、Revision Message、Diff 和 metadata。
4. `backend/app/services/markdown_renderer.py` 在 Markdown 渲染过程中对标题、摘要、正文值和索引列表逐项脱敏，最终再执行 `contains_sensitive_text()` 安全扫描；通过后才写入 `data/reports/`。
5. 这些改动不改变任务表 + Artifact JSON + 日志表的轻量存储方案，也不引入新的安全基础设施或外部依赖。

### 前端展示约束

1. `frontend/src/App.tsx` 的 Trace 渲染继续通过 `renderTraceValue()` 和 `sanitizeTraceText()` 兜底处理嵌套值。
2. Prompt 预览仍默认折叠，标题中展示“已脱敏”；展开后只展示脱敏摘要，不展示原始 Prompt。
3. 前端兜底规则同步覆盖 Bearer、环境变量名、手机号、地址和账号 ID，避免后端遗漏时直接在 Trace 页暴露原文。

### QA 敏感表达约束

1. `backend/app/services/qa_rules.py` 扩展 `SENSITIVE_ABSOLUTE_TERMS`，增加宠物安全和电器认证相关绝对化表述，如“安全无忧”“永不夹猫”“防夹绝对可靠”“通过所有认证”“认证齐全”。
2. 命中后继续生成 `SENSITIVE_CLAIM_NEEDS_CONSERVATIVE_LANGUAGE` ReviewTask，要求改写为基于证据的保守表述，并保留来源局限性。
3. 该规则仍只做本地确定性 QA 检查，不调用外部模型，也不自动补写缺失证据。

### 验证契约

1. `backend\.conda312\python.exe -m pytest backend\tests\test_api_response.py backend\tests\test_tasks_api.py backend\tests\test_trace_api.py backend\tests\test_markdown_renderer.py backend\tests\test_qa_rules.py -q`：通过，31 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests -q`：通过，155 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
4. `npx eslint src/App.tsx src/App.test.tsx`：通过。
5. `npx prettier src/App.tsx src/App.test.tsx --check`：通过。
6. `npx vitest run .\src\App.test.tsx -t "keeps prompt previews folded and redacts sensitive trace text" --configLoader runner`：通过，1 个测试通过，30 个测试跳过。

### 边界

1. 本步骤没有开始步骤 39。
2. 本步骤没有引入外部采集、模型网络调用、Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
3. `snapshot_plus_live` 仍是增强模式占位，不进行真实外部采集。
4. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

## 2026-05-29：步骤 39 E2E Demo 路径验证

当前项目已完成实施计划步骤 39，前端端到端验证从单页/专项 smoke 扩展为完整 Demo 演示路径。该步骤只加固演示路径验证，不改变业务模型或 Agent 流程。

### E2E 运行架构

1. `frontend/e2e/demo-path.e2e.spec.ts` 使用真实 Uvicorn 后端、临时 SQLite 数据库、临时报告目录和 Vite preview。
2. E2E 后端通过 `RUN_TASK_EXECUTION_INLINE=1` 同步执行任务，避免后台任务时序导致浏览器等待不稳定。
3. E2E 前端构建使用临时 `frontend-dist` 目录和 Vite `configLoader: "runner"`，避免多个测试共用或清理 `frontend/dist`。
4. 既有 `task-flow`、`qa-revision`、`trace.visual`、`battlefield.visual` 用例也改为临时构建目录，保证全量 Playwright 套件可串行稳定运行。

### Demo 覆盖契约

1. 输入页验证“启动分析任务”可见，并截图确认页面非空。
2. Trace 页验证 LangGraph DAG、Agent Run、QA Review、Collection 修复 Diff、Analysis 重算 Diff 和 Writer Agent 可见。
3. 产品画像页验证基础信息、PricingModel 和有限 Human Review 区域可见。
4. 竞争图谱页验证 React Flow 节点和边非空，QA 打回记录显示最终通过且已解决 1 条。
5. 报告页验证九章节报告中的执行摘要和 QA 审查摘要可见，并通过真实 `GET /tasks/{task_id}/report/markdown` 验证 Markdown 导出。
6. 窄屏验证覆盖 Trace、竞争图谱和报告页，要求主导航与内容区不重叠且页面没有严重水平溢出。

### 前端布局约束

1. 报告页长文本容器增加 `min-width: 0` 与 `overflow-wrap`，避免移动宽度下长标题、导出提示或嵌套报告项撑破布局。
2. 这些样式只影响文本折行与窄屏稳定性，不改变报告数据结构、章节顺序或 API 契约。

### 验证契约

1. `npm run test:e2e`：通过，5 个 Chromium 用例通过。
2. `npx eslint e2e`：通过。
3. `npx prettier e2e --check`：通过。

## 2026-05-29：步骤 40 Demo 冻结与稳定回归

当前项目已完成实施计划步骤 40，Demo 输入、快照哈希、默认目标和 QA 打回样例已冻结，并通过后端回归测试和全量 E2E 锁定稳定演示形状。该步骤执行后不继续推进新的实施计划步骤。

### 冻结产物

1. `demo/stable-demo-input.json` 是答辩和录屏的稳定任务输入。
2. `demo/DEMO_FREEZE.md` 记录冻结日期、品类、快照路径、快照 SHA256、默认目标 SKU 和 QA 打回 SKU。
3. 当前快照哈希固定为 `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`。
4. 默认目标继续固定为 `sku_02`。
5. 可复现 QA 打回案例继续固定为 `sku_01` 缺失 `source.access_time`，修复证据为 `ev_sku_01_repair_001`。

### 稳定回归契约

1. `backend/tests/test_demo_freeze.py` 校验冻结输入、快照哈希、Snapshot 版本、默认目标和 QA fixture。
2. 同一冻结输入重复运行两次 LangGraph，结果摘要形状必须一致。
3. 稳定结果必须包含 2 次 Collection、2 次 Analysis、2 次 QA、1 次 Writer。
4. 稳定结果必须触发 `TIMELY_EVIDENCE_MISSING_ACCESS_TIME`，且最终 ReviewTask 状态为 `resolved`。
5. 稳定结果必须保留 `collection_agent_repair` 和 `analysis_agent_recompute` 两类 Diff。
6. 最终报告必须保留九个章节，并确认竞品发现 Claim 使用修复后的 `ev_sku_01_repair_001`。

### 运行时测试约定

1. `backend/app/main.py` 支持 `RUN_TASK_EXECUTION_INLINE`，用于浏览器 E2E 或冻结回归中的同步任务执行；生产默认仍使用后台任务。
2. `backend/app/main.py` 支持 `REPORT_OUTPUT_DIR`，用于测试隔离 Markdown 导出目录；未设置时仍使用默认 `data/reports/`。
3. `frontend/package.json` 的 build/test 脚本使用 Vite/Vitest runner 加载器；Vitest 显式设置 `--root .`，以避免 Windows 下配置加载和路径解析不稳定。
4. 当前沙箱无法直接清理既有 `frontend/dist` 产物，`npm run build` 会在删除旧 asset 时遇到 Windows `EPERM`；生产构建已通过临时输出目录验证。

### 验证契约

1. `backend\.conda312\python.exe -m pytest backend\tests\test_demo_freeze.py -q`：通过，3 个测试通过。
2. `backend\.conda312\python.exe -m pytest backend\tests -q`：通过，159 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
4. `npm run test`：通过，49 个测试通过。
5. `npm run test:e2e`：通过，5 个 Chromium 用例通过。
6. `npm run lint`：通过。
7. `npm run format:check`：通过。
8. `npx tsc --noEmit`：通过。
9. `npx vite build --configLoader runner --outDir C:\Users\15298\AppData\Local\Temp\zijieagent-frontend-build-step40 --emptyOutDir false`：通过。

### 边界

1. 本步骤没有新增真实外部采集，`snapshot_plus_live` 仍是增强模式占位。
2. 本步骤没有引入模型网络调用、Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
3. 未写入真实 API Key，未在 Trace、日志、截图或报告中记录密钥。

## 2026-05-29：v2 步骤 01 2.0 契约清单

当前项目进入 2.0 改版实施前的契约确认阶段。本阶段只新增迁移清单文档，不改变 1.0 已冻结的运行架构。

### 迁移清单产物

1. 新增 `memory-bank/v2-migration-checklist.md`，作为 2.0 后续开发的契约边界清单。
2. 清单将 2.0 页面划分为竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪五个责任区。
3. 清单明确保留 LangGraph 真实 DAG、四 Agent、QA 打回、证据链、Trace、Human Review、SQLite 轻量存储和冻结 Demo。
4. 清单明确新增 Overview、DOCX 导出、简化关系图、关键关系筛选、横向画像和证据与过程追踪阅读层。
5. 清单明确删除旧 Markdown 用户可见导出入口，后续必须移除 `GET /tasks/{task_id}/report/markdown` 并新增 `GET /tasks/{task_id}/report/docx`。

### 架构边界

1. 本阶段不修改 `backend/`、`frontend/`、`data/` 或 `demo/` 的运行逻辑。
2. 本阶段不引入 `python-docx`、`Pillow` 或其他新依赖；依赖调整留给后续 DOCX 与关系图步骤。
3. 本阶段不新增真实外部采集、模型必需链路、队列、缓存服务、微服务或新前端框架。
4. 后续每个 v2 步骤必须先实现并通过对应验证，再进入下一步。

## 2026-05-29：v2 步骤 02 后端 2.0 展示状态 Schema

当前项目已完成 2.0 展示枚举与状态原因 Schema 的后端契约补充。本阶段只扩展 Schema 层，不改变现有 Agent 协议和运行链路。

### Schema 扩展

1. `backend/app/schemas/common.py` 新增 `JudgmentStrength`、`DecisionUsabilityStatus`、`EvidenceCredibilityStatus`、`ThreatLevel`、`PMRelationshipLabel`、`ActionPriority` 和 `ResponsibilityType`。
2. 新增 `backend/app/schemas/display.py`，定义 `DisplayStatus`，统一承载 2.0 状态枚举值、用户可读标签、原因说明、Evidence 引用、Trace 引用和风险标记。
3. `backend/app/schemas/__init__.py` 统一导出新增枚举和 `DisplayStatus`，保证 FastAPI OpenAPI 和后续前端类型同步可发现这些契约。

### 架构边界

1. 新增枚举只服务于 PM 可读表达，不替代底层任务状态、Agent 状态、Claim 状态或竞争关系类型。
2. 现有 `Claim`、`Evidence`、`CompetitionEdge`、`ReviewTask`、`AgentMessage` 和 Trace 日志结构未被修改。
3. 本阶段未修改 API 路由、服务层、Agent 节点、前端页面或 Demo 数据。
4. 本阶段未引入新依赖、外部采集、模型必需链路或复杂基础设施。

## 2026-05-29：v2 步骤 03 Product 主图访问契约

当前项目已完成 Product 主图字段和快照主图推导。本阶段只补齐产品基础展示所需的图片入口，不改变竞品分析、QA 打回或报告生成链路。

### Schema 与加载契约

1. `Product` 新增 `primary_image_path`、`primary_image_url`、`primary_image_source_path` 和 `primary_image_status`。
2. `ProductImageStatus` 使用 `available` 与 `missing` 两态表达主图是否可用于前端展示。
3. Snapshot Loader 按远程图片字段、本地 `source.screenshot_path`、本地 `source.raw_dir` 首张图片的顺序推导主图。
4. 本地图片只允许映射到项目 `data/raw` 目录下的 `.jpg`、`.jpeg`、`.png` 和 `.webp` 文件。
5. 对前端暴露的图片地址统一为 `/assets/raw/...`，不返回本机绝对路径；缺失时返回 `primary_image_path = None`、`primary_image_url = None` 且状态为 `missing`。

### 静态资源边界

1. FastAPI 在应用创建时将 `data/raw` 挂载到 `/assets/raw`，用于 Demo 脱敏图片展示。
2. 静态挂载不暴露 `data/snapshots`、`data/reports` 或完整 `data` 目录。
3. 该能力只服务本地快照图片展示，不代表 `snapshot_plus_live` 已具备真实外部采集能力。

### 架构边界

1. 冻结快照 JSON 未修改，默认目标、QA fixture 和快照哈希仍由 Demo freeze 测试保护。
2. 现有 Agent DAG、Claim/Evidence 绑定、QA 打回和 Markdown 报告链路未被改动。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务或新前端框架。

## 2026-05-29：v2 步骤 04 分析范围汇总服务

当前项目已完成分析范围汇总的后端服务层能力，为后续 OverviewData 和总览页提供可复用的数据来源说明。本阶段只新增服务和 Schema，不暴露新 API。

### Schema 与服务契约

1. `AnalysisScopeSummary` 位于 `backend/app/schemas/overview.py`，当前只承载分析范围，不包含总览页的一句话判断、机会点、风险点或行动建议。
2. `build_analysis_scope_summary` 位于 `backend/app/services/analysis_scope_service.py`，输入为 `AnalysisTask`、`Product`、`Evidence` 和可选快照版本。
3. 汇总字段包括品类、子类、数据源模式、数据源中文说明、SKU 数、Product 数、Evidence 数、平台、来源说明、快照版本、快照日期、访问时间范围、缺失字段和 Evidence 引用。
4. 服务固定输出“本报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。”，避免将本地快照解读为实时全网覆盖。
5. 当 Evidence 访问时间不完整或缺失时，`access_time_range` 输出“暂无可靠数据”，并在 `missing_fields` 中记录 `Evidence.access_time`。

### 安全边界

1. 服务不输出 `raw_dir`、`screenshot_path`、`source_url`、本机绝对路径、API Key 或环境变量内容。
2. 服务不根据产品页短链推断实时销量、全网覆盖、排名、认证或外部市场数据。
3. `snapshot_plus_live` 仍只作为增强模式占位；当前数据源说明会明确未执行真实外部采集。

### 架构边界

1. 本阶段不修改 LangGraph DAG、四 Agent、QA 打回、Trace、报告生成或 Human Review 链路。
2. 本阶段不新增 Overview API 或前端总览页；这些能力留给后续 v2 步骤。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务或新前端框架。

## 2026-05-29：v2 步骤 05 总览数据结构

当前项目已完成 2.0 总览页后端数据契约。该阶段只定义 Schema，不生成真实总览数据，也不暴露 API。

### OverviewData 契约

1. `OverviewData` 位于 `backend/app/schemas/overview.py`，承载一句话判断、判断强度、决策可用状态、状态原因、分析范围、关键竞品、机会点、风险点、行动建议、当前切片和下钻引用。
2. `analysis_scope` 复用步骤 04 的 `AnalysisScopeSummary`，避免总览页重复拼接分析范围。
3. `current_slice` 复用 `BattlefieldSliceSelection`，保证后续总览与竞争图谱使用同一切片参数。
4. `judgment_strength` 和 `decision_usability` 使用 `DisplayStatus` 包装，但分别强制限定为 `JudgmentStrength` 与 `DecisionUsabilityStatus`。
5. 关键竞品使用 `OverviewKeyCompetitor`，包含竞品类型、产品标识、产品名称、主图路径、PM 关系标签、威胁等级、证据可信状态、入选理由、Evidence 引用、Trace 引用和下钻引用。
6. 机会点与风险点统一使用 `OverviewFinding`，其中机会点最多 3 条，风险点最多 3 条。
7. 行动建议使用 `OverviewActionRecommendation`，最多 5 条，且必须包含 `ActionPriority` 和 `ResponsibilityType`。

### 证据与风险契约

1. `ReferencedOverviewItem` 作为关键结论类结构的基类，统一携带 `evidence_ids`、`trace_refs`、`drilldown_refs`、`risk_flags` 和 `missing_reference_reason`。
2. 关键结论缺少 Evidence 或 Trace 引用时，Schema 会标记 `missing_evidence` 并写入“缺少 Evidence 或 Trace 下钻引用。”。
3. 空的一句话判断、空标题、空描述、空产品名或空下钻目标会被 Pydantic 拒绝，避免完全不可展示的数据进入总览。

### 架构边界

1. 本阶段未实现 Overview 服务、Overview API、前端总览页或缓存产物。
2. 本阶段不改变 LangGraph DAG、四 Agent、QA 打回、Trace、报告生成或 Human Review 链路。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务或新前端框架。

## 2026-05-29：v2 步骤 06 总览服务

当前项目已完成总览页后端服务层。该阶段提供生成 `OverviewData` 的服务能力，但尚未暴露 HTTP API。

### 服务契约

1. `OverviewService` 位于 `backend/app/services/overview_service.py`，使用 `TaskRepository`、`ArtifactRepository` 和 LangGraph Workflow 生成或缓存总览数据。
2. `OVERVIEW_ARTIFACT_TYPE` 固定为 `overview_data`，后续 API 可按任务和切片读取缓存产物。
3. `_build_overview_data` 直接基于 Workflow 产物生成 PM 可读总览，输入包含任务、产品、证据、声明、竞争边、审查任务和 Agent 消息。
4. 服务不要求前端从 Profile、Battlefield、Report 拼接总览，前端后续只消费专用 Overview API。
5. 服务复用步骤 04 的 `build_analysis_scope_summary`，统一分析范围口径。

### 状态与排序契约

1. 判断强度按 2.0 标准计算：平均置信度、证据可追溯性和未解决高严重度 QA 风险共同决定明确判断、倾向判断或仅作假设。
2. 证据可信状态按关键证据完整性和相关未解决 QA 风险决定可直接采纳、谨慎参考或证据不足。
3. 决策可用状态由判断强度、关键竞品证据可信状态和全局未解决 QA 风险决定；未解决高严重度 QA 风险会降级为“仅供方向参考”。
4. 威胁等级按竞争分与证据可信状态决定；证据不足时即使高分也标为“高分需复核”。
5. 关键竞品在当前切片内排序，默认尝试选择最高威胁直接竞品、最高威胁替代竞品和需复核高分竞品，不存在的类别不硬补。
6. 机会点、风险点和行动建议均随切片变化引用不同竞品、证据和 Trace。

### 文案与安全边界

1. 服务生成的主文案使用 PM 可读中文表达，不在主文案中裸露 `Product`、`Claim`、`Evidence` 等后端 Schema 名称。
2. 服务不输出本机绝对路径、API Key、环境变量或外部实时采集结论。
3. `snapshot_plus_live` 仍只是增强模式占位，当前服务不执行真实外部采集。

### 架构边界

1. 本阶段未新增 Overview API、前端总览页或导航改造。
2. 本阶段不改变 LangGraph DAG、四 Agent、QA 打回、Trace、报告生成或 Human Review 链路。
3. 本阶段未引入新依赖、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 07 总览 API

当前项目已暴露 2.0 总览专用后端接口，前端后续可以直接消费总览数据，不需要从多个旧页面接口拼装。

### API 契约

1. 新增 `GET /tasks/{task_id}/overview`，路由位于 `backend/app/api/routes_overview.py`。
2. 响应类型为 `ApiResponse[OverviewData]`，继续使用统一成功/错误外壳和 `X-Trace-Id`。
3. 接口支持 `price_band`、`persona`、`scenario` 查询参数，并透传为 `BattlefieldSliceSelection`。
4. 接口只允许 `completed` 和 `human_reviewing` 任务读取总览；其他状态返回 `OVERVIEW_NOT_READY`。
5. 任务不存在时返回 `TASK_NOT_FOUND`。
6. `backend/app/main.py` 已挂载 Overview 路由。

### 服务衔接

1. API 层只负责参数接收、标准响应和错误转换，总览生成仍由 `OverviewService` 完成。
2. 测试环境可通过 `app.state.overview_workflow_factory` 注入替代 Workflow，保持与 Battlefield/Profile 服务同类扩展方式。
3. 总览结果按任务和切片缓存为 `overview_data` Artifact。

### 架构边界

1. 本阶段未修改竞争图谱、画像、报告、Trace 或 Human Review API。
2. 本阶段未新增前端页面、导航或 OpenAPI TypeScript 同步；前端迁移留给后续步骤。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 08 竞争图谱后端契约升级

当前项目已在竞争图谱后端契约中加入 2.0 展示层所需的关键关系结构。该阶段只扩展返回结构，不改变默认关系筛选数量。

### Schema 契约

1. `BattlefieldData` 保留既有 `graph_nodes`、`graph_edges`、`score_explanations`、`decision_chain`、`evidence_cards` 和 `qa_summary`。
2. `BattlefieldData` 新增 `key_relations`，用于承载 2.0 默认展示层的关键关系候选。
3. `BattlefieldKeyRelation` 包含关系 ID、目标/竞品产品 ID、竞品名称、竞品品牌、竞品主图路径、PM 关系标签、标签解释、威胁等级、证据可信状态、入选理由、四段式解释、应对建议、Claim/Evidence/Trace 引用和风险标记。
4. `BattlefieldFourPartExplanation` 当前包含关系概述、需求重叠、证据依据和行动提示四段。
5. `BattlefieldGraphNode` 新增 `primary_image_path`，用于前端图谱节点和列表展示图片。

### 服务契约

1. `battlefield_service` 基于现有 `CompetitionEdge`、`Claim`、`Evidence` 和 `ReviewTask` 生成 `key_relations`。
2. 证据可信状态按是否存在关键证据、证据是否可追溯、是否存在相关未解决 QA 风险决定。
3. 威胁等级按竞争分和证据可信状态决定；证据不足时高分关系会被标记为“高分需复核”。
4. PM 关系标签先按现有竞争类型映射，后续步骤会继续细化标签规则。
5. 竞争分仍保留在 `graph_edges` 和 `score_explanations` 中，`key_relations` 默认展示层不直接强调裸分数。

### 架构边界

1. 本阶段未实现 3 到 5 条默认关键关系筛选，`key_relations` 当前仍覆盖当前切片下的候选关系集合。
2. 本阶段未修改前端页面、导航、报告导出或 OpenAPI TypeScript 同步。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 09 关键竞争关系筛选

当前项目已将竞争图谱的 `key_relations` 从候选全集调整为默认展示集合，并提供展开全部关系所需的后端标记。

### 筛选契约

1. `BattlefieldData.relation_filter` 记录 `include_all_relations`、`default_limit`、`total_relation_count`、`visible_relation_count` 和 `can_expand_all`。
2. `BattlefieldKeyRelation.is_default_visible` 标记关系是否属于默认展示集合；展开全部时前端可据此区分默认关系和补充关系。
3. 默认展示集合最多 5 条，数据充足时至少 3 条；当前切片候选不足时不硬补。
4. 默认筛选优先覆盖最高威胁直接竞品、最高威胁替代/渠道替代竞品、需复核高分竞品和对策略动作最有启发的竞品。
5. 对策略动作最有启发的关系要求证据可信状态不是“证据不足”、威胁等级为高或中，并能生成明确行动建议。

### API 契约

1. `GET /tasks/{task_id}/battlefield` 新增 `include_all_relations` 查询参数，默认 `false`。
2. 默认请求返回筛选后的 `key_relations`，但 `graph_edges` 仍保留完整当前切片边集合。
3. `include_all_relations=true` 返回当前切片下完整 `key_relations`，并保留 `is_default_visible` 标记。
4. Battlefield Artifact ID 已纳入 `include_all_relations` 维度，避免默认视图和展开视图缓存互相覆盖。

### 风险契约

1. 高分但证据不足、关键证据缺失或存在相关未解决 QA 风险的关系标为 `high_score_needs_review`。
2. 证据不足的高分关系不会直接标为 `high_threat`。
3. 原有价格带、人群和场景切片过滤继续作用于 `graph_edges` 与 `key_relations`。

### 架构边界

1. 本阶段未进一步细化 PM 关系标签和威胁等级规则；标签细化留给后续步骤。
2. 本阶段未修改前端页面、导航、报告导出或 OpenAPI TypeScript 同步。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 10 PM 关系标签与威胁等级规则

当前项目已细化竞争图谱后端的 PM 关系标签规则和威胁等级规则。

### 标签规则

1. `正面硬碰` 对应 `head_to_head`，用于同类产品在同一价格、人群、场景中直接竞争。
2. `低价截流` 对应 `low_price_interception`，用于渠道替代关系，或竞品到手价显著低于目标产品的直接竞争关系。
3. `场景替代` 对应 `scenario_substitute`，用于非同类但解决同一使用场景问题的替代关系。
4. `信任压制` 对应 `trust_suppression`，当竞品证据或产品信息出现安全、认证、防夹、口碑、评价、售后、信任、质保等信任信号时优先命中。
5. `内容种草竞争` 对应 `content_seeding_competition`，用于内容共现或种草竞争关系。
6. 每个标签均由后端返回一句中文 `relationship_label_explanation`，前端不需要自行解释枚举。

### 威胁等级规则

1. `high_threat`：竞争分不低于 0.80，且证据可信状态不是证据不足。
2. `medium_threat`：竞争分不低于 0.60，且未因证据不足被降级。
3. `low_threat`：竞争分低于 0.60。
4. `high_score_needs_review`：竞争分不低于 0.60，但证据不足、关键证据缺失或存在相关未解决 QA 风险。
5. 高分但证据不足的关系不会直接标为高威胁。

### 架构边界

1. 本阶段只细化规则，不改变 `BattlefieldData` 的主要结构。
2. 本阶段未进一步重写四段式解释；解释结构强化留给后续步骤。
3. 本阶段未修改前端页面、导航、报告导出或 OpenAPI TypeScript 同步。
4. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 11 竞争边四段式解释

当前项目已将关键竞争关系的四段式解释升级为可追溯结构。

### Schema 契约

1. `BattlefieldExplanationSegment` 表示单段解释，字段包括正文、Claim 引用、Evidence 引用、Trace 引用、风险标记和 `is_analysis_suggestion`。
2. `BattlefieldFourPartExplanation` 包含四段：`why_competitor`、`strength`、`decision_stage_impact` 和 `response_suggestion`。
3. 缺少 Claim 与 Evidence 引用的解释段会自动标记 `missing_evidence` 风险。
4. `response_suggestion` 必须标记为分析建议，否则 Schema 校验失败。

### 生成契约

1. `why_competitor` 解释为什么它进入同一决策比较集合。
2. `strength` 解释它强在哪里，依据当前评分拆解与证据可信状态。
3. `decision_stage_impact` 解释它可能在哪些决策阶段抢走用户。
4. `response_suggestion` 以“分析建议”形式给出应对方向，不新增无证据事实。
5. 四段解释均绑定当前竞争边相关 Claim、Evidence 和 Analysis Trace 引用。

### 架构边界

1. 本阶段未修改关键关系筛选数量、PM 标签枚举、前端页面或报告导出。
2. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 12 产品画像横向对比

当前项目已在产品画像后端数据中加入第一屏横向对比对象。

### Schema 契约

1. `ProductProfileData.horizontal_comparison` 承载目标产品与关键竞品的横向对比。
2. `ProductProfileComparison.compared_products` 包含目标产品、最高威胁直接竞品和最高威胁替代/渠道替代竞品；不存在的竞品类型不硬补。
3. `ProfileComparisonDimension` 表示第一屏维度行，当前覆盖价格带、核心卖点、主要人群、使用场景和证据可信状态。
4. 每个维度行必须输出目标产品状态：优势、持平、短板或证据不足。
5. 每个维度行携带 Evidence 引用与 Trace 引用，便于下钻。

### 服务契约

1. `profile_service` 继续返回原有目标产品、功能树、价格模型、人群画像、证据摘要等下钻数据。
2. 横向对比只放第一屏高层维度，功能树明细、评论痛点和截图证据不进入默认第一层。
3. 最高威胁直接/替代竞品基于当前 Workflow 竞争边按分数选择。
4. 价格状态根据目标与已选竞品到手价相对关系判断。
5. 证据可信状态根据证据来源、访问时间和内容摘要是否完整判断。

### 架构边界

1. 本阶段未扩大 Human Feedback 范围，仍不允许自由编辑整份报告。
2. 本阶段未修改前端页面、导航、报告导出或 OpenAPI TypeScript 同步。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-29：v2 步骤 13 网页报告 2.0 结构

当前项目已将 Writer Agent 输出的网页报告数据结构升级为 2.0 八章节。

### ReportData 契约

1. 2.0 主章节顺序固定为：结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。
2. `section_order` 不再包含 1.0 的 `qa_summary` 和 `evidence_index`，二者进入“证据与质检附录”。
3. 旧 1.0 字段在 Schema 中暂时保留为可选字段，用于兼容旧缓存读取；新 Writer 产物按 2.0 字段生成。
4. 核心竞品拆解中的关键判断包含 `judgment_strength`。
5. 产品策略建议包含 `priority` 和 `responsibility_type`。

### Writer 契约

1. Writer Agent 继续只基于已通过 QA 的 Workflow 产物生成报告。
2. Evidence 索引、QA 打回、Collection 修复、Analysis 重算进入证据与质检附录。
3. 用户研究信号和 Agent 运行概况进入分析流程与系统能力附录。
4. 报告主章节标题使用自然中文，不再把 Evidence 索引或 QA 摘要作为主章节标题。

### 架构边界

1. 本阶段未删除 Markdown 导出 API；删除和 DOCX 替换留给后续步骤。
2. 本阶段未实现 Word 报告、关系图 PNG、前端报告页或导航。
3. 本阶段未引入新依赖、外部采集、模型必需链路、队列、缓存服务、数据库或新前端框架。

## 2026-05-30：v2 步骤 14 简化关系图 PNG 服务

当前项目已新增用于 Word 报告的简化竞争关系图生成服务。该能力独立于网页报告读取链路，后续 DOCX 导出可以直接复用生成后的 PNG 文件。

### 服务契约

1. `RelationshipGraphService` 位于 `backend/app/services/relationship_graph_service.py`，使用 `TaskRepository`、`ArtifactRepository` 和 LangGraph Workflow 生成默认切片下的 `BattlefieldData`。
2. `RELATIONSHIP_GRAPH_ARTIFACT_TYPE` 固定为 `relationship_graph_image`，导出产物使用 `RelationshipGraphImage` Schema 记录文件路径、文件名、大小、生成时间和安全扫描元信息。
3. `render_relationship_graph_png` 使用 Pillow 生成静态 PNG，不依赖 Graphviz、浏览器渲染、Office、PDF 或微服务。
4. 图片仅表达目标产品、默认 3 到 5 条关键竞争关系、威胁等级、PM 关系标签和证据可信状态，不追求与前端交互图完全一致。
5. 竞品或关键关系缺失时生成占位内容，保证后续导出链路可以给出可读说明。

### 失败与安全边界

1. PNG 渲染失败不会影响 `ReportService.get_report_data` 的网页报告读取能力。
2. 渲染失败会写入 Trace metadata 的 `relationship_graph_failures` 和 `last_failure`，只记录错误码、报告 ID、异常类型和记录时间，不记录异常消息正文。
3. 写入图片的文本和输出文件名会先进行敏感信息脱敏；导出元信息不保存产品名、API Key、Token 或未脱敏隐私。
4. 关系图服务只新增 Pillow 静态图片生成能力，不新增外部采集、模型必需链路、队列、缓存、数据库类型或后端 PDF 服务。

### 架构边界

1. 本阶段尚未实现 DOCX 导出接口或 Word 模板，相关能力留给步骤 15。
2. 本阶段尚未删除 Markdown 导出 API，删除留给步骤 16。
3. 本阶段尚未修改前端页面、导航或 OpenAPI TypeScript 同步产物。

## 2026-05-30：v2 步骤 15 Word 报告导出服务

当前项目已具备真实 `.docx` Word 报告生成服务。该能力仍位于后端服务层，尚未暴露 HTTP 下载接口。

### Schema 与产物

1. `WordReport` 位于 `backend/app/schemas/report.py`，记录 `word_report_id`、`task_id`、`report_id`、`generated_at`、`file_path`、`file_name`、`byte_size` 和 `metadata`。
2. `WORD_REPORT_ARTIFACT_TYPE` 固定为 `word_report`，Word 导出成功后会保存到统一 Artifact JSON 表。
3. Word 文件默认保存到 `<project-root>/data/reports/`；测试和后续 API 可以通过服务参数传入输出目录。

### 服务结构

1. `WordReportService` 位于 `backend/app/services/word_report_service.py`，使用 `TaskRepository`、`ArtifactRepository` 和 LangGraph Workflow 获取报告、产品和竞争关系数据。
2. `render_word_report` 使用 `python-docx` 生成真实 `.docx` 文件，不依赖 Headless Office、浏览器渲染、PDF 服务或微服务。
3. 导出服务复用第 14 步 `render_relationship_graph_png` 生成简化关系图，并在成功时保存 `relationship_graph_image` Artifact。
4. Word 报告结构包含封面、静态目录、产品图片摘要、目标产品缩略图、核心竞品缩略图、简化竞争关系图、正文和附录。
5. 目录为静态章节列表，不生成需要 Office 刷新域的自动目录。

### 图片与安全边界

1. 产品缩略图只解析本地可访问素材路径或 `/assets/raw/` 对应的本地文件，不联网抓取远程图片。
2. 目标产品或核心竞品图片缺失、格式不支持或插入失败时，Word 正文写入“暂无可靠图片”，不导致整份导出失败。
3. Word 文本、文件名和导出元信息在写入前进行敏感信息脱敏；安全扫描阻止 API Key、Token、手机号、账号 ID 等模式进入 Word 文本。
4. 关系图生成失败时，Word 导出元信息记录失败类型并继续写入占位内容；网页报告读取链路不依赖 Word 导出成功。

### 架构边界

1. 本阶段尚未新增 `GET /tasks/{task_id}/report/docx`，HTTP 下载接口留给步骤 16。
2. 本阶段尚未删除 Markdown 导出 API，删除留给步骤 16。
3. 本阶段尚未修改前端页面、导航或 OpenAPI TypeScript 同步产物。
4. 本阶段未引入 Graphviz、Headless Office、浏览器渲染服务、后端 PDF 服务、队列、缓存服务、新数据库或新前端框架。

## 2026-05-30：v2 步骤 16 Word 报告 API 与 Markdown API 删除

当前项目已将用户可见报告导出入口从 Markdown 切换为 Word `.docx` 下载。

### 后端 API 契约

1. `GET /tasks/{task_id}/report/docx` 位于 `backend/app/api/routes_reports.py`，成功时返回 `FileResponse`，媒体类型为 `application/vnd.openxmlformats-officedocument.wordprocessingml.document`。
2. Word API 由 `WordReportService.export_word_report()` 生成文件，继续使用 `app.state.report_output_dir` 支持测试隔离输出目录。
3. 未完成任务返回标准错误 `WORD_REPORT_NOT_READY`；任务不存在仍由服务返回 `TASK_NOT_FOUND`。
4. Word 导出失败返回标准错误 `WORD_REPORT_EXPORT_FAILED`，并且不影响 `GET /tasks/{task_id}/report` 读取网页报告。
5. `GET /tasks/{task_id}/report/markdown` 已从路由层删除，OpenAPI 中不再暴露旧 Markdown 路径。

### 前端与类型同步

1. `frontend/src/api/client.ts` 新增 `download()` 文件下载方法。成功响应按 Blob 处理；失败响应仍按后端标准 JSON 错误信封解析。
2. `frontend/src/App.tsx` 报告页按钮改为“下载 Word 报告”，调用 `/tasks/{task_id}/report/docx`，成功后触发浏览器文件下载并显示 Word 下载成功状态。
3. `frontend/src/api/schema.ts` 已通过 `npm --prefix frontend run sync:types` 从 FastAPI OpenAPI 重新生成，包含 docx 路由并移除 Markdown 路由。
4. 前端测试、E2E 路径、mock/domain 命名已从 Markdown 导出改为 Word 导出。
5. `.playwright-browsers` 作为本地生成物已加入 ESLint 和 Prettier ignore，避免全量前端质量检查扫描第三方浏览器脚本。

### 架构边界

1. 本阶段只删除用户可见 Markdown HTTP API；历史 Markdown 渲染服务和旧服务级测试仍保留，避免无关清理扩大改动面。
2. 本阶段尚未将 Word 导出失败写入 Trace metadata，失败追踪留给步骤 17。
3. 本阶段未新增后端 PDF、Headless Office、浏览器渲染、队列、缓存、新数据库或新前端框架。

## 2026-05-30：v2 步骤 17 Word 导出失败追踪

当前项目已将 Word 导出失败纳入 Trace metadata，保证用户下载失败时仍能在过程追踪中看到可诊断记录。

### 失败记录契约

1. `WordReportService._record_word_export_failure()` 负责写入失败记录。
2. 失败列表保存在 `TraceData.metadata.word_export_failures`，最近一次失败同步写入 `TraceData.metadata.last_failure`。
3. 单条失败记录包含：
   - `status`: 固定为 `failed`。
   - `code`: 固定为 `WORD_REPORT_EXPORT_FAILED`。
   - `report_id`: 关联报告 ID。
   - `phase`: 当前为 `docx_render_or_write`。
   - `error_type`: 异常类型名称。
   - `readable_reason`: 面向用户的可读原因。
   - `details`: 仅包含脱敏后的任务、报告和阶段信息。
   - `recorded_at`: UTC ISO 时间。
4. 失败记录不保存异常消息正文、不保存本地输出目录原文、不保存本机绝对路径。

### Trace 写入流程

1. 如果任务已有 Trace artifact，服务会读取并追加失败记录。
2. 如果任务尚无 Trace artifact，服务会用任务记录构建最小 Trace，再写入失败 metadata。
3. Trace 写入不改变任务状态，不删除已有网页报告 Artifact。
4. `GET /tasks/{task_id}/trace` 能读取到导出失败记录；`GET /tasks/{task_id}/report` 在失败后仍返回网页报告。

### 架构边界

1. 本阶段尚未重构 Trace 为 2.0 证据与过程追踪视图，结构升级留给步骤 18。
2. 本阶段不改变 Word 导出 API 契约，也不新增 PDF、Headless Office、浏览器渲染、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 18 Trace 证据与过程追踪数据结构

当前项目已将 Trace 后端数据契约从单纯过程日志扩展为“证据与过程追踪”视图的数据源。原有 DAG、Agent Run、Tool Call、Token Usage、Prompt Preview、QA Review 和 Diff 字段继续保留，新增结构服务于 PM 默认阅读层和后续前端 Tab 重构。

### TraceData 契约

1. `TraceData.evidence_chains` 按 Claim 组织证据链，每条链包含 Claim 内容、状态、置信度、是否推断、报告章节引用、Evidence 摘要、风险标记和下钻 query。
2. `TraceData.quality_records` 从 QA Review 派生，展示检查项、问题等级、打回目标、处理结果、是否已解决和是否仍需关注。
3. `TraceData.process_view` 记录过程视图默认行为，当前 `technical_details_folded=True`，用于前端默认折叠技术细节。
4. `TraceData.drilldown_targets` 汇总证据链、质检记录、智能体过程和差异记录入口，统一以 `trace_tab` query 定位目标 Tab，并携带对象 ID 用于高亮。
5. `TraceDiff.business_impact` 使用业务语言解释 Collection 证据补齐、Analysis 竞争边重算或 Claim 证据绑定变化的影响，不只暴露 before/after JSON。

### 服务生成逻辑

1. `TraceService` 仍以任务状态和 LangGraph Workflow 产物为唯一数据来源，不新增外部采集或模型必需链路。
2. Evidence Chain 通过 Claim 的 `evidence_ids` 绑定 Evidence，并从最新报告章节中反查 Claim 所在章节。
3. Evidence Item 只暴露摘要、局限性、来源类型、可信等级、访问时间状态和来源 URL；不暴露本地截图绝对路径。
4. QA 质检记录保留原始 ReviewTask，同时提供面向用户可读的 `action_result`、`resolved` 和 `needs_attention` 字段。
5. Trace metadata 继续记录计数信息，并新增 evidence chain、quality record 和 diff 数量，便于前端或测试校验数据完整性。

### 安全与兼容边界

1. Trace 响应继续在返回前执行 `redact_sensitive_value(..., redact_key_names=True)`，避免 API Key、Token、手机号、账号 ID、地址等敏感信息外露。
2. 新结构不改变 LangGraph DAG、四 Agent、QA 打回、Collection 修复或 Analysis 重算的执行语义。
3. 前端 OpenAPI 类型已同步，但 Trace 页面重构仍留给后续步骤 30 和 31。
4. 本阶段未新增 PDF、Headless Office、浏览器渲染、队列、缓存、新数据库或新前端框架。

## 2026-05-30：v2 步骤 19 前端 API Client 2.0 契约

当前前端已同步后端 OpenAPI 2.0 类型，并在 API Client 层提供受控业务入口。页面组件后续可以调用封装方法，而不是手写路径和临时 query 字段。

### 类型同步范围

1. `frontend/src/api/schema.ts` 由 `scripts/sync-openapi-types.mjs` 从 FastAPI OpenAPI 生成。
2. 类型中包含 `GET /tasks/{task_id}/overview`、`GET /tasks/{task_id}/battlefield` 的 `include_all_relations` query、`GET /tasks/{task_id}/profile` 横向画像字段、`GET /tasks/{task_id}/trace` 证据与过程追踪字段，以及 `GET /tasks/{task_id}/report/docx` Word 下载响应。
3. 类型中不再包含旧 `GET /tasks/{task_id}/report/markdown` 操作和 `MarkdownReport` 前端可见 Schema。

### API Client 封装

1. `ApiClient.getOverview(taskId, query)` 获取竞争态势总览，query 仅允许价格带、人群和使用场景切片字段。
2. `ApiClient.getBattlefield(taskId, query)` 获取竞争图谱，query 允许切片字段和 `include_all_relations`。
3. `ApiClient.getProductProfile(taskId)` 获取产品与竞品画像，包含后端返回的横向对比字段。
4. `ApiClient.getReport(taskId)` 获取网页报告结构化数据。
5. `ApiClient.getTrace(taskId)` 获取证据与过程追踪数据。
6. `ApiClient.downloadWordReport(taskId)` 下载 Word `.docx` 文件。
7. 所有 task 路径都通过统一 helper 对 `task_id` 做 URL 编码，减少页面层临时拼接路径的风险。

### 架构边界

1. 本阶段不改变页面布局、导航顺序或任务创建后的默认落点；这些留给步骤 20 之后。
2. 本阶段不引入 Redux、Next.js、Tailwind、复杂状态管理、新后端依赖、外部采集或模型必需链路。

## 2026-05-30：v2 步骤 20 前端导航与默认落点

当前前端主导航已切换到 2.0 工作台信息架构，任务创建后的默认落点从过程追踪改为竞争态势总览。

### 导航契约

1. 主导航五项固定为：竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪。
2. `/` 任务输入页继续保留，用于创建任务，但不再作为主导航工作台项。
3. `/overview` 是任务创建后的默认落点，负责承接 `task_id` 并提供后续工作台入口；完整总览业务内容留给步骤 21。
4. `routePathForTask()` 继续统一保留跨页面 `task_id` query，主导航和任务结果入口都沿用该逻辑。

### 中文化边界

1. 证据与过程追踪页的默认可见标题已从 `Trace`、`Agent Run`、`Tool Call`、`Token Usage`、`Diff View` 调整为中文业务表达。
2. 智能体展示名改为采集智能体、分析智能体、质检智能体和报告智能体。
3. 更深层技术字段、Trace Tab 结构和全站中文化仍按步骤 30、31、32 继续推进。

### 架构边界

1. 本阶段不改变后端 API、LangGraph DAG、四 Agent、QA 打回、报告导出或 Human Review 语义。
2. 本阶段不新增 Redux、Next.js、Tailwind、复杂状态管理、外部采集、队列、缓存或新数据库。
3. E2E Demo 路径仍按步骤 34 统一更新，避免在导航落点步骤中过度扩大验证范围。

## 2026-05-30：v2 步骤 21 竞争态势总览首屏

当前 `/overview` 已成为 PM 默认阅读入口的首屏工作台，直接消费后端 Overview 2.0 数据契约。

### 页面数据流

1. `OverviewPage` 通过 `ApiClient.getOverview(taskId)` 读取 `GET /tasks/{task_id}/overview`；测试或轻量客户端未实现封装方法时回退到同一路径的 `get()` 调用。
2. 页面不在前端推断竞争结论，只渲染后端返回的 `one_sentence_judgment`、`decision_usability`、`judgment_strength`、`analysis_scope`、`key_competitors`、`action_recommendations` 和 `risk_points`。
3. `routePathForTask()` 扩展为可携带受控额外 query，当前用于从关键竞品下钻到 `/battlefield?task_id=<task_id>&edge_id=<edge_id>`。

### 首屏信息结构

1. 主区域优先展示一句话判断和分析范围声明，范围声明明确说明报告基于用户提供的脱敏 SKU 快照，不代表实时全网数据。
2. 状态条展示判断强度、决策可用性和分析范围统计，服务 PM 快速判断当前结果是否可用于决策。
3. 侧栏展示首要行动建议和证据风险提醒，避免用户只看到结论而忽略证据限制。
4. 关键竞品列表以重复卡片展示缩略图、名称、关系标签、威胁等级、证据可信度、纳入原因和竞争关系下钻入口；缺图或加载失败统一显示“暂无可靠图片”。

### 架构边界

1. 本阶段不改变 OverviewService 的数据生成规则，也不新增外部采集或模型必需链路。
2. 本阶段不重构竞争图谱、画像、报告或证据与过程追踪页面，后续步骤继续按计划推进。
3. 新增 Playwright 视觉用例只验证桌面首屏核心判断可见性，不引入截图基线、PDF、浏览器渲染导出或新测试框架。
4. 本阶段不新增 Redux、Next.js、Tailwind、复杂状态管理、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 22 总览切片联动

当前竞争态势总览页支持以价格带、人群和使用场景为维度刷新总览判断。

### 切片数据流

1. `OverviewPage` 维护本页 `BattlefieldSliceSelection` 状态，默认从当前 URL 的 `price_band`、`persona`、`scenario` query 初始化。
2. 切片控件选项通过 `getBattlefieldData(taskId, { include_all_relations: true })` 读取 Battlefield `available_slices`，前端只做去重展示。
3. `getOverviewData(taskId, selection)` 会压缩空切片字段，只把非空 `price_band`、`persona`、`scenario` 传给 Overview API。
4. React Query Key 包含三个切片字段，因此任意切片变化都会重新请求 Overview 数据。

### 展示联动

1. 一句话判断、关键竞品、首要行动建议、机会点和风险点全部来自当前 Overview 响应，不在前端根据切片自行推断。
2. 机会点和风险点在总览页增加独立可见区域，配合首屏风险提醒展示切片变化后的业务影响。
3. 关键竞品“查看竞争关系”仍通过 Overview 下钻引用携带 `edge_id`，并保留当前 `task_id`。

### 架构边界

1. 本阶段没有新增后端 Schema 字段；总览切片选项复用现有 Battlefield `available_slices`。
2. 本阶段没有改变 OverviewService、BattlefieldService、LangGraph DAG、四 Agent、QA 打回或报告导出语义。
3. 本阶段不引入 Redux、Next.js、Tailwind、复杂状态管理、外部采集、队列、缓存或新数据库。
4. 术语解释、竞争图谱默认阅读层、画像页和追踪页改造继续按后续步骤推进。

## 2026-05-30：v2 步骤 23 统一术语解释组件

当前前端拥有统一的轻量术语解释能力，用于降低 PM 阅读评分、切片、证据和质检状态时的理解成本。

### 组件结构

1. `frontend/src/termExplanations.ts` 作为术语字典，集中维护术语标签和解释文案。
2. `frontend/src/TermHint.tsx` 只负责渲染解释触发按钮和 tooltip，避免与 Fast Refresh 规则冲突。
3. `TermHint` 使用原生按钮作为触发控件，支持鼠标悬停和键盘聚焦；tooltip 使用 `role="tooltip"`，并通过 `aria-describedby` 与触发按钮关联。

### 术语覆盖

1. 评分维度：需求替代性、上下文匹配度、决策阶段影响力、证据置信度、市场信号强度。
2. 状态与阅读层：质检、证据可信状态、动态切片、威胁等级、判断强度。
3. 解释文案保持短句中文，不把术语说明做成长说明书，也不暴露裸英文技术词。

### 接入位置

1. 总览页：动态切片、判断强度、威胁等级、证据可信度。
2. 竞争图谱页：评分拆解五个维度、证据卡片置信度、QA 打回记录。
3. 触发按钮作为标签旁边的独立控件，不改变原有核心标签文本，避免影响既有页面断言和业务阅读层。

### 架构边界

1. 本阶段不改变后端 API、Schema、LangGraph DAG、四 Agent、QA 打回或报告导出语义。
2. 本阶段不引入新 UI 框架、Tooltip 依赖、Redux、Next.js、Tailwind、队列、缓存或新数据库。
3. 竞争图谱默认阅读层重构继续按步骤 24 推进。

## 2026-05-30：v2 步骤 24 竞争图谱默认阅读层

当前竞争图谱页默认面向 PM 展示后端筛选的关键竞争关系，并把全部关系折叠为显式开关，避免首屏被低优先级竞争边稀释。

### 数据流

1. `BattlefieldPage` 默认通过 `getBattlefieldData(taskId, sliceQuery)` 读取 `GET /tasks/{task_id}/battlefield`，不携带 `include_all_relations`。
2. “展开全部关系”开关开启后，同一查询会携带 `include_all_relations=true`，由后端决定返回关系数量和 `key_relations` 范围。
3. React Query Key 包含切片字段和展开状态，因此切片变化或展开切换都会重新请求 Battlefield 数据。
4. 切片变化会重置当前选中的竞争边和展开状态，保证不同业务切片下的默认阅读层始终来自后端当前筛选结果。

### 默认展示结构

1. `getVisibleBattlefieldEdges()` 优先根据 `data.key_relations[*].edge_id` 过滤图谱边；如果后端没有关键关系，则回退展示全部 `graph_edges`。
2. `getVisibleBattlefieldNodes()` 根据当前可见边保留相关源/目标节点，并始终保留 `target_product_id` 对应节点。
3. 关键关系面板展示竞品名称、PM 关系标签、威胁等级、证据可信度、纳入原因和关系说明，作为图谱上方的默认阅读层。
4. 图谱连线不直接显示原始竞争分，原始分数和五个评分维度继续保留在竞争边详情的评分拆解区域。

### 展开与响应式边界

1. `relation_filter` 提供当前可见关系数量、总关系数量和是否可展开信息，前端只负责渲染开关与状态，不自行推断业务筛选规则。
2. 展开全部关系后，关键关系面板可同时展示后端返回的扩展关系，并用“扩展关系”状态区分默认关键关系。
3. 视觉测试覆盖桌面和窄屏视口，确保图谱区域、关键关系面板和详情面板不会发生重叠。

### 架构边界

1. 本阶段不改变 BattlefieldService 的关系筛选与评分生成规则，也不新增后端 Schema 字段。
2. 本阶段不改变 Overview、画像、报告、Trace、任务创建跳转、LangGraph DAG、四 Agent、QA 打回或导出语义。
3. 本阶段不引入 Redux、Next.js、Tailwind、新图谱库、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 25 竞争边详情

当前竞争边详情页侧栏以业务解释为主线，保留评分和证据细节作为可下钻依据。

### 详情数据来源

1. 四段式解释来自 `BattlefieldData.key_relations[*].four_part_explanation`，按照当前选中的 `edge_id` 匹配对应关键关系。
2. 解释段落包含 `claim_ids`、`evidence_ids`、`trace_refs`、`risk_flags` 和 `is_analysis_suggestion`，前端只做展示和下钻组织。
3. 如果当前边没有匹配到关键关系，详情区显示空状态，不在前端补写解释。

### 默认阅读层

1. 竞争边详情的主标题为“竞争边解释”，默认展示四段：为什么是竞品、强在哪、影响哪个决策阶段、应对建议。
2. `response_suggestion.is_analysis_suggestion=true` 的段落显示“分析建议”标记，避免把系统建议包装成确定事实。
3. 每个段落都有“查看依据”按钮，展开后显示相关结论 ID、证据 ID 和筛选后的证据卡片。
4. 结论与证据、证据卡片、质检打回记录保留在同一侧栏，服务逐层追溯。

### 评分拆解

1. 五维评分继续使用后端 `score_breakdown` 字段，原始竞争分只在详情侧栏出现。
2. 维度名称使用需求替代性、上下文匹配度、决策阶段影响力、证据置信度、市场信号强度。
3. 每个维度增加一句前端固定解释，用于说明维度含义，不改变后端评分计算。

### 架构边界

1. 本阶段不改变 BattlefieldService、OpenAPI Schema、评分规则或关键关系筛选逻辑。
2. 本阶段不改变产品画像、报告、Trace、任务创建跳转、LangGraph DAG、四 Agent、QA 打回或导出语义。
3. 本阶段不引入 Redux、Next.js、Tailwind、新可视化库、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 26 产品与竞品画像页

当前产品与竞品画像页以横向对比作为默认阅读层，面向 PM 展示目标产品与核心竞品的第一屏差异判断。

### 数据来源

1. `ProductProfilePage` 继续读取 `GET /tasks/{task_id}/profile`，不从 Overview、Battlefield 或 Report 拼接画像首屏。
2. 新增的前端阅读层直接消费 `ProductProfileData.horizontal_comparison`，该对象由后端步骤 12 生成。
3. 若后端暂未返回横向对比对象，前端只用目标产品构造保守兜底视图，并将状态标记为“证据不足”，不补造竞品。

### 默认阅读层

1. `ProfileComparisonWorkbench` 是画像页第一块内容，默认展示三列：目标产品、最高威胁直接竞品、最高威胁替代竞品。
2. 每列展示产品名称、品牌、主图状态和缺失图片兜底；缺少竞品时显示“暂无可用于对比的直接竞品”或“暂无可用于对比的替代竞品”。
3. 对比维度按后端返回顺序展示，覆盖价格带、核心卖点、主要人群、使用场景和证据可信状态。
4. 每个维度展示目标产品状态标签：优势、持平、短板或证据不足，并展示后端状态原因。
5. “查看依据”入口跳转到 `/trace?task_id=<task_id>&tab=evidence&evidence_id=<evidence_id>`，保留证据下钻路径。

### 下钻与修正

1. 原有基础信息、功能树、价格模型、用户人群和 Evidence 摘要保留在横向对比之后，作为详细画像下钻。
2. 有限人工修正面板仍在右侧栏，允许范围继续由 `buildHumanReviewOptions()` 控制，不允许自由编辑报告或改写 Claim 正文。
3. 窄屏下横向对比列和维度值改为单列堆叠，避免严重水平溢出。

### 架构边界

1. 本阶段不改变 `ProfileService`、OpenAPI Schema、后端横向对比生成规则或 Human Review 后端语义。
2. 本阶段不改变 Overview、Battlefield、Report、Trace、任务创建跳转、LangGraph DAG、四 Agent、QA 打回或导出语义。
3. 本阶段不引入 Redux、Next.js、Tailwind、新 UI 框架、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 27 受控人工复核

当前人工复核入口面向用户使用业务中文表达，并继续保持后端受控结构化反馈边界。

### 前端入口

1. 画像页右侧复核面板命名为“修正画像”，副标题为“受控复核”。
2. 可见动作标签为“修正画像、标记不采纳、补充证据备注”，对应后端已有的画像字段更新、Claim 状态标记和 Evidence 备注能力。
3. 画像修正表单只展示 `buildHumanReviewOptions()` 中的 allowlist 字段，不出现“整份报告”或“Claim 正文”等自由编辑入口。
4. 提交后仍调用 `POST /tasks/{task_id}/feedback`，并通过前端重新拉取画像数据刷新页面。

### 后端边界

1. `FeedbackService` 仍以 `_PROFILE_FIELD_ALLOWLIST` 控制画像字段，画像类反馈只允许 `update_field`。
2. Claim 类反馈只允许 `mark_accepted`、`mark_rejected`、`mark_needs_review`，不能通过 `update_field` 改写正文。
3. Evidence 类反馈只允许 `add_note`，用于补充证据备注。
4. Competition Edge 和 Slice 的受控能力保持既有约束，没有开放自由编辑报告。

### Trace 差异

1. 反馈服务在 `human_feedback_local_updates` 中保存 feedback_id、target_type、target_id、action、before、after、reason 和受影响对象。
2. `TraceService` 将这些记录转为 `source=human_feedback` 的 `TraceDiff`，在差异记录中展示。
3. 人工修正差异的 `business_impact` 使用业务语言解释：画像字段修正会刷新页面画像和缓存，标记不采纳会影响报告采纳程度，补充证据备注会辅助后续复核。

### 架构边界

1. 本阶段不改变 LangGraph DAG、四 Agent、QA 打回、Overview、Battlefield、Report 或 Word 导出语义。
2. 本阶段不引入新数据存储、新队列、外部采集、模型必需链路、Redux、Next.js 或 Tailwind。

## 2026-05-30：v2 步骤 28 分析报告页工作台视图

当前分析报告页已经从旧版报告展示升级为 2.0 工作台视图，并以 Word `.docx` 作为正式导出入口。

### 报告页结构

1. `ReportPage` 继续读取 `GET /tasks/{task_id}/report`，不从 Overview、Battlefield 或 Trace 临时拼接报告章节。
2. 报告页按固定八章节顺序渲染 `ReportData`：结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。
3. 若某个章节缺失，前端只展示保守兜底章节和“暂无可靠数据”，不补写事实结论。
4. 每个章节保留 Claim、Evidence、风险标记，并提供“查看依据”“查看过程”入口下钻到证据与过程追踪页。

### 导出与打印

1. 报告工具栏提供 Word 下载、浏览器打印和打印视图切换。
2. Word 下载调用 `GET /tasks/{task_id}/report/docx`，由后端负责真实 `.docx` 文件生成。
3. Word 下载失败只在当前页面展示错误，不隐藏网页报告内容。
4. 打印视图隐藏工具栏并保留报告章节和静态图谱摘要，不新增后端 PDF 服务。
5. 前端不再展示 Markdown 导出入口或 Markdown 导出成功提示。

### 架构边界

1. 本阶段不改变后端 `ReportData` 生成语义、Word 服务、LangGraph DAG、四 Agent、QA 打回或 Human Review 规则。
2. 本阶段不引入 PDF 服务、Headless Office、Redux、Next.js、Tailwind、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 29 报告打印视图

当前报告页具备独立打印视图，用于浏览器打印或另存 PDF。该能力完全在前端完成，不新增后端 PDF 服务。

### 打印视图契约

1. 打印视图由报告页本地状态控制，切换后在 `body` 上标记 `data-report-view="print"`。
2. `data-report-view="print"` 隐藏工作台左侧导航和页面头部，使屏幕预览更接近正式报告。
3. `report-print-mode` 隐藏报告工具栏和章节下钻按钮，只保留正式报告内容。
4. `@media print` 进一步隐藏导航、按钮和交互控件，保证浏览器打印输出不包含工作台操作层。
5. 打印视图仍保留静态图谱摘要和八个报告章节，避免离线报告依赖交互图谱。

### 架构边界

1. 打印或另存 PDF 只调用浏览器 `window.print()`，不经过后端 PDF、Headless Office 或图渲染服务。
2. 打印视图不改变网页报告、Word 下载、后端 ReportData 或 Trace 数据契约。
3. 本阶段不引入新前端框架、复杂状态管理、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 30 证据与过程追踪 Tab

当前证据与过程追踪页已经从旧版过程日志陈列改为四 Tab 阅读层，默认按结论组织证据链。

### Trace 页面结构

1. 页面保留追踪概览，展示 Trace ID、流程状态、任务状态、生成时间、运行记录数和模型用量。
2. 默认阅读层为四个 Tab：证据链、质检记录、智能体过程、差异记录。
3. 默认 Tab 从 `TraceData.process_view.default_tab` 读取，缺失时兜底到证据链。
4. 证据链 Tab 消费 `TraceData.evidence_chains`，按 Claim 展示证据，而不是平铺 Evidence。
5. 质检记录 Tab 优先消费 `TraceData.quality_records`，后端旧 `qa_reviews` 仍作为兼容兜底。
6. 智能体过程 Tab 保留 LangGraph DAG、Agent Run、Tool Call、模型用量和 Prompt 摘要。
7. Tool Call、模型用量和 Prompt 摘要被包进“技术详情”折叠区，默认不展开。
8. 差异记录 Tab 消费 `TraceData.diffs`，展示 before/after 和业务影响说明。

### 安全边界

1. Prompt 摘要、错误、Diff 文本和 Trace 字段仍通过前端脱敏函数展示。
2. 技术详情只是折叠展示已有 Trace 数据，不新增 Prompt 原文来源。
3. 本阶段不改变 LangGraph DAG、四 Agent、QA 打回、Trace API 或存储语义。

### 架构边界

1. 本阶段不改变后端 TraceService 生成规则，只消费步骤 18 已新增的数据结构。
2. 本阶段不引入新图谱库、复杂状态管理、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 31 质检记录与差异记录阅读层

当前证据与过程追踪页进一步强化质检记录和差异记录的业务默认层，帮助 PM 区分“已经闭环的问题”和“仍需关注的问题”，并把前后差异解释为业务影响。

### 质检记录展示契约

1. 质检记录 Tab 继续优先消费 `TraceData.quality_records`，不在前端拼接新的 QA 结论。
2. 页面顶部展示仍需关注、已解决、待处理或豁免三类数量汇总。
3. 每条质检记录展示 QA 检查项、问题等级、质检打回对象、打回目标、处理要求、处理结论和是否仍需关注。
4. `needs_attention` 与 `resolved` 是前端区分状态的主要信号；旧 `qa_reviews` 仍只作为兼容兜底。

### 差异记录展示契约

1. 差异记录 Tab 继续消费 `TraceData.diffs`，不改变后端 Diff 生成语义。
2. Diff 默认按来源翻译为 QA 打回修复、QA 打回后的分析重算、人工修正差异或流程差异。
3. 默认阅读层展示变化来源、影响对象、关联打回和 `business_impact`，避免只展示 before/after JSON。
4. before/after 结构化值保留在折叠区，供需要复核细节时下钻查看。

### 架构边界

1. 本阶段不改变 TraceService、QA 规则、Human Feedback 服务、LangGraph DAG 或存储结构。
2. 本阶段不引入新状态管理、图谱库、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 32 全站中文化阅读层

当前前端主界面进一步收敛为中文业务表达，技术字段和英文原始名称只保留在受控下钻或代码类型层，不作为默认阅读层标题。

### 中文化边界

1. 主导航继续固定为竞争态势总览、竞争图谱、产品与竞品画像、分析报告、证据与过程追踪。
2. 产品画像默认模块标题使用“功能能力树”“价格与证据”“用户人群画像”“证据摘要”，不再暴露 `FeatureTree`、`PricingModel`、`UserPersona` 等 Schema 名称。
3. 证据与过程追踪页默认使用证据链、质检记录、智能体过程、差异记录和协作流程图等中文标题。
4. Prompt 预览标题在前端渲染层翻译为“采集智能体提示摘要”等中文表达，仍保留脱敏标记。
5. 流程图节点和边在渲染层把 Collection、Analysis、QA、Writer 映射为采集、分析、质检和报告相关中文表达；后端原始枚举和 Agent 名称不变。

### 测试约束

1. 前端组件测试增加默认用户可见文案扫描，防止 `Agent Run`、`Tool Call`、`Payload`、`Diff View`、`FeatureTree`、`PricingModel` 等旧主界面词回流。
2. Trace 与 Report 视觉用例继续覆盖主要页面标题和按钮中文化。
3. 后端 Writer、Report API 和 Word 导出测试继续验证报告章节为自然中文。

### 架构边界

1. 本阶段不改变 OpenAPI Schema、后端存储、TraceService、Writer Agent、Word 导出服务或 Agent 数据协议。
2. 本阶段不引入新 UI 框架、状态管理、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 33 Mock 与 Fixture 合约

当前开发 Mock 和测试 fixture 已按 2.0 API 契约重新收敛，并明确与最终演示数据分离。

### 前端开发 Mock

1. `frontend/src/types/domain.ts` 不再维护独立旧响应类型，只在 OpenAPI 生成类型外增加 `mock_meta`，用于标记开发 fixture。
2. `ALL_DEVELOPMENT_MOCKS` 包含总览、产品画像、竞争图谱、证据与过程追踪和分析报告五类 fixture。
3. 总览 Mock 使用 `OverviewData`，覆盖一句话判断、决策可用状态、关键竞品、机会风险、行动建议和范围摘要。
4. 竞争图谱 Mock 使用 `BattlefieldData`，覆盖 `graph_nodes`、`graph_edges`、`key_relations`、四段式解释、证据可信状态、QA 摘要、证据卡和切片选项。
5. Trace Mock 使用 `TraceData`，覆盖证据链、质检记录、差异记录、Prompt 摘要、技术详情折叠和 QA 打回差异。
6. 报告 Mock 使用 `ReportData` 的 2.0 八章节，不再保留旧 `sections` 数组或 Markdown 导出形态。

### 后端 Fixture 合约

1. `backend/tests/test_v2_fixture_contracts.py` 以冻结 Demo 稳定输入运行真实 LangGraph workflow，再构造 Overview、Battlefield、Trace 和 Word 报告 fixture 合约断言。
2. 合约测试覆盖总览范围摘要、关键关系入选理由、威胁标签、四段式解释、证据可信状态和证据链按 Claim 组织。
3. DOCX 缺图测试通过清空产品主图字段验证“暂无可靠图片”兜底，不改变冻结 Demo 快照。
4. fixture 安全扫描覆盖冻结快照、稳定输入和 workflow 结果摘要，防止密钥、手机号、账号 ID、地址等敏感模式进入测试数据。

### 架构边界

1. 前端开发 Mock 是组件开发和测试数据，不作为最终演示数据来源。
2. 冻结 Demo 快照、哈希和稳定输入保持不变；如果后续确需改动，必须同步更新冻结文档和回归测试。
3. 本阶段不改变 OpenAPI Schema、后端服务生成规则、LangGraph DAG、四 Agent、QA 打回、Human Review 或 Word 导出实现。
4. 本阶段不引入 Redux、Next.js、Tailwind、外部采集、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 34 端到端 Demo 路径

当前真实后端 E2E Demo 路径已经对齐 2.0 信息架构。

### Demo 路由顺序

1. 用户从任务输入页创建任务后，前端默认跳转到 `/overview?task_id=<task_id>`。
2. 端到端路径首屏验证竞争态势总览，展示核心判断、决策可用状态、首要行动建议和关键竞品入口。
3. 后续路径依次覆盖竞争图谱、产品与竞品画像、分析报告和证据与过程追踪。
4. 证据与过程追踪仍保留 QA 打回、采集补证、Analysis 重算、差异记录和智能体运行记录的可追溯路径。

### 导出与人工修正

1. Demo 路径通过报告页触发 `GET /tasks/{task_id}/report/docx`，并验证返回 `.docx` 文件字节，不再覆盖 Markdown 导出。
2. 报告页不展示 Markdown 导出按钮。
3. QA 回归路径覆盖画像页受控人工修正入口，提交结构化画像字段修正后通过 Trace 的 `human_feedback` 差异记录验证可追溯。

### E2E 测试边界

1. `task-flow.e2e.spec.ts` 是基础真实后端路径验证。
2. `qa-revision.e2e.spec.ts` 聚焦 QA 打回、补证、重算和人工修正。
3. `demo-path.e2e.spec.ts` 覆盖完整演示路径、截图、Word 导出和窄屏布局基础检查。

### 架构边界

1. 本阶段没有改变后端 API、OpenAPI Schema、LangGraph DAG、四 Agent、QA 打回或 Word 导出实现。
2. E2E 使用后台任务同步执行入口和临时 SQLite 数据库，不引入真实外部采集、队列、缓存或新基础设施。
3. 本阶段不引入 Redux、Next.js、Tailwind、PDF 服务、Headless Office、微服务或新数据库。

## 2026-05-30：v2 步骤 35 响应式视觉回归

当前前端响应式质量通过 Playwright 视觉回归保护，覆盖 2.0 五个主要工作台页面。

### 覆盖页面

1. 竞争态势总览：验证核心判断、决策状态、关键竞品缩略图和“暂无可靠图片”占位在桌面/窄屏下可见。
2. 竞争图谱：验证 React Flow 节点和边非空，图谱容器具备稳定高度，关键关系信息不遮挡。
3. 产品与竞品画像：验证三列横向对比在窄屏下堆叠，图片占位与标题文本不重叠。
4. 分析报告：验证 Word 下载、浏览器打印、打印视图入口和报告章节在桌面/窄屏下可读，且不出现 Markdown 导出按钮。
5. 证据与过程追踪：验证证据链和智能体过程可读，流程图容器稳定，技术详情仍默认折叠。

### 测试方式

1. `responsive.visual.spec.ts` 使用前端开发 fixture mock API，避免真实后端启动时序影响布局断言。
2. 该用例统一检查主导航与内容区关系、水平溢出、关键局部盒子重叠和截图非空。
3. 已有 `overview.visual`、`battlefield.visual`、`profile.visual`、`report.visual`、`trace.visual` 继续作为页面专项视觉回归。

### 架构边界

1. 响应式验证只增加测试，不改变业务数据契约、后端 API、Agent DAG 或存储结构。
2. 不引入新的视觉测试服务、截图托管、UI 框架、状态管理库、外部采集或基础设施。

## 2026-05-30：v2 步骤 36 安全与合规回归

当前安全边界覆盖网页报告、Word 报告、Trace、导出失败元信息、错误响应、前端报告渲染和 QA 规则。

### 报告安全边界

1. `ReportService.get_report_data` 在返回和缓存 `ReportData` 前调用 `redact_report_data`，统一处理 API Key、Token、Secret、手机号、账号 ID、地址等敏感模式。
2. `redact_report_data` 基于 `app.security.redact_sensitive_value(..., redact_key_names=True)` 对报告整体递归脱敏，再重新校验为 `ReportData`。
3. `WordReportService` 在从 workflow 取报告和读取缓存报告时复用同一份 `redact_report_data`，保证 DOCX 文本、报告缓存和网页报告的安全口径一致。
4. Word 渲染层继续在段落写入前调用 `_safe_text`，并在保存前用 `_assert_document_is_safe` 扫描整份文档文本。
5. Word 导出失败只在 Trace 元信息中记录失败阶段、错误类型、报告 ID 和脱敏后的结构化 details，不记录本地输出目录、异常原文或敏感输入。

### Trace 与前端渲染边界

1. `TraceService` 继续通过 `_redacted_trace` 对完整 `TraceData` 做递归脱敏。
2. 前端报告页对章节 ID、标题、摘要、字段值、数组值、嵌套字段和值标题执行脱敏展示，敏感字段名显示为“敏感字段”。
3. 证据与过程追踪页继续对 Prompt 摘要、错误、Diff、QA 文案和结构化嵌套值使用前端脱敏函数。
4. 前端脱敏是展示层兜底；后端 API 和导出服务仍是主安全边界。

### 合规规则边界

1. QA 规则会标记宠物安全、电器认证、医疗/治疗和零风险类绝对化表达，issue code 为 `SENSITIVE_CLAIM_NEEDS_CONSERVATIVE_LANGUAGE`。
2. Writer Agent 不调用模型润色新增事实；报告由结构化 Product、Evidence、Claim、CompetitionEdge、ReviewTask 和 workflow metadata 拼装。
3. 报告建议项必须标记 `is_inference`，并绑定来源 edge、Claim 和 Evidence；与结构化证据或 QA 结果冲突时以后者为准。

### 架构边界

1. 本阶段不改变 OpenAPI Schema、存储表结构、LangGraph DAG、四 Agent、QA 打回或 Human Review 协议。
2. 本阶段不引入新安全服务、外部采集、模型必需链路、队列、缓存、微服务或新数据库。

## 2026-05-30：v2 步骤 37 文档与 API 契约记录

当前项目文档已同步到 2.0 产品定位和正式交付方式。

### 设计文档口径

1. `memory-bank/design-document.md` 当前版本为 v2.0，记录创建任务后默认进入竞争态势总览。
2. 信息架构固定为输入页、竞争态势总览、产品与竞品画像、竞争图谱、分析报告、证据与过程追踪。
3. 分析报告正式交付为网页报告、Word `.docx` 下载和浏览器打印/另存 PDF；Markdown 不再作为用户可见正式交付入口。
4. 2.0 报告章节固定为结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。

### 技术栈口径

1. `memory-bank/tech-stack.md` 当前记录 `python-docx` 负责 Word `.docx` 导出，`Pillow` 负责简化竞争关系图生成。
2. 后端仍使用 Python 3.12、FastAPI、LangGraph、Pydantic v2、SQLite、SQLAlchemy。
3. 前端仍使用 React、TypeScript、Vite、TanStack Query、React Flow 和项目现有组件样式。
4. MVP 阶段继续禁止 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind、外部实时采集平台、微服务和后端 PDF 服务。
5. 文档中的启动路径使用相对项目根目录的 `backend/` 与 `frontend/`。

### API 契约文档

1. 新增 `docs/api-contract.md`，记录前后端 2.0 协作入口。
2. 核心接口包括 `POST /tasks`、`GET /tasks/{task_id}`、`GET /tasks/{task_id}/overview`、`GET /tasks/{task_id}/profile`、`GET /tasks/{task_id}/battlefield`、`GET /tasks/{task_id}/report`、`GET /tasks/{task_id}/report/docx`、`GET /tasks/{task_id}/trace` 和 `POST /tasks/{task_id}/feedback`。
3. 文档明确 `GET /tasks/{task_id}/report/markdown` 不是 2.0 用户可见正式入口，前端不得展示 Markdown 导出按钮。
4. API 契约文档记录 Trace 四个阅读层：证据链、质检记录、智能体过程和差异记录。
5. API 契约文档记录报告、Trace、导出元信息、错误响应和前端渲染的敏感信息脱敏要求。

### 架构边界

1. 本阶段仅更新文档，不改变代码路径、Schema、数据表、Agent DAG、API 路由或测试 fixture。
2. 历史架构记录中的 Markdown 阶段保留为演进记录；当前 2.0 口径以 Word `.docx` 和后续 v2 记录为准。

## 2026-05-30：v2 步骤 38 后端完整回归

当前后端全量 Pytest 与 Ruff 已通过。

### 回归修复

1. 全量测试暴露 `backend/tests/test_markdown_renderer.py` 仍按 1.0 九章节和旧字段名断言。
2. `backend/app/services/markdown_renderer.py` 作为历史服务仍保留，但现在兼容 2.0 报告结构：
   - `core_competitor_analysis` 复用竞品拆解渲染。
   - `product_strategy_recommendations` 复用建议渲染。
   - `evidence_quality_appendix` 识别 `appendix_type=evidence_index` 并渲染 Evidence 索引。
3. `backend/tests/test_markdown_renderer.py` 更新为 2.0 八章节断言，并继续验证 Claim/Evidence、访问时间、“暂无可靠数据”和敏感信息脱敏。

### 当前边界

1. Markdown 渲染器只是保留的历史服务级能力，不重新暴露用户可见 Markdown HTTP 导出入口。
2. 2.0 正式报告交付仍为网页报告、Word `.docx` 下载和浏览器打印/另存 PDF。
3. 本阶段没有改变 ReportData、WordReport、Overview、Battlefield、Trace、Human Review 或 LangGraph DAG 契约。

### 验证

1. `backend\.conda312\python.exe -m pytest backend\tests`：通过，237 个测试通过。
2. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。

## 2026-05-30：v2 步骤 39 前端完整回归

当前前端全量组件测试、静态检查、类型检查和生产构建均已通过。

### 验证

1. `$env:VITE_CACHE_DIR='.vite-cache-codex'; npm run test`：首次命中 Codex 沙箱 `/@fs/D:/...` 路径映射问题，单独重跑同一命令后通过，7 个测试文件、81 个测试通过。
2. `npm run lint`：通过。
3. `npm run format:check`：通过。
4. `npx tsc --noEmit`：通过。
5. `npm run build -- --outDir ..\.codex-run\frontend-dist-step39-verify --emptyOutDir false`：通过；仅有 Vite chunk 大于 500 kB 的既有警告。

### 架构边界

1. 本阶段没有改变前端路由、页面结构、API Client、OpenAPI 类型、Word 下载入口或响应式布局实现。
2. 本阶段不引入 Redux、Next.js、Tailwind、新 UI 框架、外部采集、队列、缓存或新数据库。

## 2026-05-30：v2 步骤 40 E2E 与冻结回归

当前 v2 实施计划 40 个步骤已全部完成，2.0 冻结 Demo、全路径 E2E、前后端质量门禁和安全边界均已复核通过。

### 冻结 Demo 基线

1. 冻结文档为 `demo/DEMO_FREEZE.md`，当前记录 2.0 演示路径和验收口径。
2. 冻结快照仍为 `data/snapshots/demo_sku_snapshot.json`，SHA256 为 `8E8303BEB9E157ACF90929352493DD00330952F09438E94443A4D98E8C01111F`。
3. 稳定输入仍为 `demo/stable-demo-input.json`，默认目标 SKU 仍为 `sku_02`，QA revision SKU 仍为 `sku_01`。
4. 2.0 演示路径固定为输入页创建任务后进入竞争态势总览，再进入竞争图谱、产品与竞品画像、分析报告、证据与过程追踪。
5. 报告正式交付为网页报告、Word `.docx` 下载和浏览器打印/另存 PDF；前端不展示 Markdown 导出按钮，旧 `/tasks/{task_id}/report/markdown` 路由保持不可用回归覆盖。

### E2E 稳定性调整

1. `demo-path.e2e.spec.ts` 使用动态后端端口，并把前端 preview 端口限制在 4100-4199 范围内，匹配后端 CORS 白名单，避免组合 E2E 中的端口占用和跨域失败。
2. `responsive.visual.spec.ts` 的画像、报告和追踪页 mock 路由覆盖查询参数，确保带 `task_id` 的页面请求稳定命中 2.0 fixture。
3. 任务输入侧栏文案与 2.0 默认跳转页同步为“竞争态势总览”。
4. 这些调整只影响 E2E 稳定性和用户可见文案，不改变后端业务语义、OpenAPI Schema、LangGraph DAG、Agent 协议或存储结构。

### 最终验证

1. `npm run test:e2e -- task-flow.e2e.spec.ts qa-revision.e2e.spec.ts demo-path.e2e.spec.ts responsive.visual.spec.ts overview.visual.spec.ts battlefield.visual.spec.ts profile.visual.spec.ts report.visual.spec.ts trace.visual.spec.ts`：通过，9 个 Playwright 用例通过；仅有 Vite chunk 大于 500 kB 的既有警告。
2. `backend\.conda312\python.exe -m pytest backend\tests`：通过，237 个测试通过。
3. `backend\.conda312\python.exe -m ruff check --no-cache backend`：通过。
4. `$env:VITE_CACHE_DIR='.vite-cache-codex'; npm run test`：通过，7 个测试文件、81 个测试通过。
5. `npx tsc --noEmit`、`npm run lint`、`npm run format:check` 和 `npm run build -- --outDir ..\.codex-run\frontend-dist-step40-verify --emptyOutDir false`：通过；构建仅有既有 Vite chunk 警告。
6. 冻结快照哈希校验通过，未发生冻结数据漂移。
7. 前端源码与 E2E 中没有用户可见 Markdown 导出入口；旧 Markdown 路径只出现在不可用回归测试和文档说明中。
8. 应用代码和前端依赖未新增真实外部采集、Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准基础设施；仅保留 `snapshot_plus_live` 未执行真实外部采集的占位说明。

### 架构边界

1. 2.0 完成态仍遵守 Python 3.12、FastAPI、LangGraph、Pydantic v2、SQLite、SQLAlchemy、React、TypeScript、Vite、TanStack Query、React Flow、Pytest、Vitest 和 Playwright 的技术栈约束。
2. Word `.docx` 由 `python-docx` 生成，简化竞争关系图由 `Pillow` 生成；二者是 2.0 已批准的本地交付依赖。
3. 未配置模型 API Key 时，系统仍通过本地脱敏快照和规则流程完成 Collection、Analysis、QA、Writer、Overview、Battlefield、Profile、Report、Trace 和 DOCX 导出。
4. QA 打回、Collection 补证、Analysis 局部重算、Human Review 差异、证据链、质检记录和 Diff 仍可通过 Trace 查询。
5. 报告、Trace、导出元信息、错误响应和前端渲染继续执行敏感信息脱敏；测试中的假密钥样式只用于脱敏断言，不代表真实凭据。

## 2026-06-03：报告页叙事可读性修复

本次调整不改变后端 Writer Agent、ReportData Schema、Word/PDF 交付、Claim/Evidence 绑定或竞争评分逻辑，只优化 `frontend/src/App.tsx` 的网页报告叙事层。问题表现为 `conclusion_summary`、`competitive_landscape_judgment`、`core_competitor_analysis`、`user_decision_chain_analysis` 等章节容易把结构化字段、机器 Claim 或枚举标签拼成名词堆积式段落，用户难以读出“结论是什么、为什么、该怎么继续看”。

### 前端呈现边界

1. `frontend/src/App.tsx`：总体判断改为按“竞争压力来源、关系性质、阅读顺序、证据口径”组织段落，不再把原始机器摘要当正文堆叠。
2. `frontend/src/App.tsx`：竞争格局判断从“切片 + 关系数量 + 分数”改为说明该切片下用户最可能比较谁，以及压力来自同一使用任务的替代。
3. `frontend/src/App.tsx`：核心竞品拆解不再直接展示 `claim.content` 中的规则评分模板句，改为用竞品名、关系类型、切片、评分、决策阶段和证据数量生成可读段落。
4. `frontend/src/App.tsx`：用户决策链分析新增阶段解释，把 `capability_understanding`、`trust_building`、`decision_completion` 等阶段转换为用户正在判断的问题和目标产品需要补强的表达。
5. `frontend/src/App.css`：新增报告正文段落卡片样式，不新增嵌套 `<article>`，保持 2.0 报告章节数量语义稳定。
6. `frontend/src/App.test.tsx`：报告工作台测试覆盖机器 Claim、`direct`、`clear_judgment` 等原始字段，断言页面展示自然语言段落且不暴露机器模板句。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\typescript\bin\tsc --noEmit`：通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx`：通过。

### 边界

1. 本次没有修改后端报告接口、Writer Agent、Word 导出或持久化数据。
2. 本次没有改变竞争关系排序、评分公式、QA 打回或证据可追溯结构。
3. 本次没有引入新依赖、新前端框架或外部采集能力。

## 2026-06-03：画像、战场与报告中文可读性修复

本次调整继续限定在前端展示层，不改变后端 API、OpenAPI Schema、Agent DAG、评分公式、Claim/Evidence 绑定、Word 导出或存储结构。修复目标是把产品画像、竞争图谱和网页报告中的机器字段、英文枚举和内部 ID 转换成用户可读的中文表达，避免页面出现 `douyin_sku_snapshot`、`medium`、`edge_*`、`claim_*`、`ev_*` 之类的正文噪音。

### 前端呈现边界

1. `frontend/src/App.tsx`：产品画像页的功能能力树改为每个能力块都有业务解释、证据不足提示和中文化条目；清洁、除臭、安全、智能、维护成本不再只是短词列表。
2. `frontend/src/App.tsx`：画像页和战场页的证据摘要统一使用 `buildEvidenceParagraphs` 分段展示，把商品快照、核心卖点、评论摘要和证据边界拆开阅读；来源通过 `SOURCE_TYPE_LABELS` 显示为“抖音商品快照”，置信度通过 `CONFIDENCE_DETAIL_LABELS` 显示为“中等可信度”等中文。
3. `frontend/src/App.tsx`：竞争图谱详情页不再在正文展示竞争边 ID、结论 ID 和证据 ID；改为“当前关系”“结论 1”“证据 1”和结论/证据数量，仍保留下钻时需要的真实 ID 参数。
4. `frontend/src/App.tsx`：竞争评分说明新增 `ScoreExplanationList`，用综合分、主要得分维度和证据边界解释评分含义；五个评分维度改为更口语化的中文标签和说明。
5. `frontend/src/App.tsx`：报告页把“报告编号”改为“报告名称”，引用条只展示分析判断和证据材料数量；报告字段渲染会过滤内部 ID，并把来源、置信度、状态、竞争类型等枚举转换成中文。
6. `frontend/src/App.css`：新增画像能力说明、证据分段、关系名称、评分说明和结论分条样式，保持现有卡片半径和页面结构，不引入新 UI 框架。
7. `frontend/src/App.test.tsx`：组件测试覆盖画像能力说明、来源中文化、置信度中文化、战场证据中文展示、评分维度中文化和报告名称展示。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\typescript\bin\tsc --noEmit`：通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx`：通过，54 个测试通过。

### 边界

1. 本次没有修改后端数据生成、Writer Agent prompt、ReportData Schema 或数据库内容。
2. 本次没有移除 Trace 中真实可追溯 ID；只是避免在用户正文中直接展示内部索引。
3. 本次没有新增依赖、外部采集、队列、缓存、微服务或未批准的前端框架。

## 2026-06-03：报告与过程追踪用户视图收口

本次调整继续限定在前端展示层，目标是把网页报告和过程追踪从“工程调试视图”收敛为“用户可读的分析解释视图”。后端 TraceData、ReportData、QA 打回、Diff、Agent Run、Tool Call 和 Evidence 结构均保持不变，真实内部 ID 仍存在于 API 与下钻参数中，但不再作为用户正文展示。

### 前端呈现边界

1. `frontend/src/App.tsx`：过程追踪页顶部“当前任务”不再展示 `task_id`，改为展示目标产品名和中文状态说明；更新时间统一显示到分钟。
2. `frontend/src/App.tsx`：Trace 概览、证据链、质检记录、工具调用、模型用量和差异记录继续保留，但将 `completed`、`snapshot_loader`、`local_rule_flow`、`TIMELY_EVIDENCE_MISSING_ACCESS_TIME`、`missing_access_time` 等状态、工具名、质检码和风险标记转换为中文。
3. `frontend/src/App.tsx`：Trace 证据链中的 Evidence、Claim、内部对象 ID 改为“证据 1”“1 条分析判断”“已记录”等用户可读表达；Prompt 预览不再渲染到用户页面。
4. `frontend/src/App.tsx`：报告结论摘要、竞争格局、核心竞品和用户决策链段落重写为“竞争压力来自谁、用户为什么会比较、目标产品需要回应什么、证据支撑到哪里”的叙事结构。
5. `frontend/src/App.tsx`：空任务提示、报告等待提示、战场决策链统计和 QA 风险关系说明去掉 `task_id`、`completed`、`Claim`、`Evidence` 等中英文混杂表达。
6. `frontend/src/App.test.tsx`：组件测试新增或更新断言，保护报告与 Trace 页面不展示原始任务 ID、证据 ID、工具英文名、Prompt 预览和英文 QA 问题码。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx`：通过，54 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\typescript\bin\tsc --noEmit`：通过。

### 边界

1. 本次没有修改后端 API、OpenAPI Schema、LangGraph DAG、四 Agent、QA 规则、ReportData Schema 或数据库存储。
2. 本次没有删除可追溯能力；只是把用户页面默认视图从内部调试信息改为中文解释，技术记录仍由后端结构化保存。
3. 本次没有新增依赖、外部采集、队列、缓存、微服务或未批准的前端框架。

## 2026-06-03：统一 LLM Client 服务层

本次新增后端统一 LLM Client，作为后续 Writer Agent 和 Analysis Agent 接入 Doubao-Seed-2.0-lite 的唯一服务边界。当前只提供独立服务能力和单元测试，不改变 LangGraph DAG、Writer Agent、ReportData 生成规则、API 路由或前端页面。

### 服务结构

1. `backend/app/services/llm_client.py`：新增 `LLMSettings`、`LLMClient`、`LLMCallResult`、`LLMTokenUsage` 和 `load_llm_settings`。
2. `LLMSettings` 从环境变量读取 `LLM_ENABLED`、`LLM_PROVIDER`、`DOUBAO_API_KEY`、`DOUBAO_BASE_URL`、`DOUBAO_MODEL`、`LLM_TIMEOUT_SECONDS` 和 `LLM_MAX_RETRIES`；默认尝试加载 `backend/.env`，并保持 `override=False`，避免覆盖已显式设置的运行环境变量。
3. `LLMClient.complete_json(...)` 使用 `httpx` 调用 OpenAI-compatible `/chat/completions` 接口，默认请求 `response_format={"type":"json_object"}`，不新增 OpenAI SDK 依赖。
4. 模型输出通过既有 `coerce_structured_model_output` 校验为 JSON object；非 JSON、请求失败、超时或响应缺字段时按 `LLM_MAX_RETRIES` 重试，最终返回调用方提供的 fallback。
5. 未启用模型、Provider 不支持、缺少 API Key、缺少 Base URL 或缺少模型名时不会请求外部接口，直接返回 fallback，并在 `fallback_reason` 中记录原因。
6. `LLMTokenUsage` 只记录模型名、prompt/completion/total token，可转换为既有 `TokenUsageLog`，供后续 Trace 接入。

### 安全边界

1. API Key 只用于请求头 `Authorization: Bearer ...`，不会进入 `LLMCallResult`、`safe_metadata`、错误信息、测试输出、文档或 Trace。
2. 错误记录只保留错误类型、尝试次数和脱敏后的短消息，不记录完整请求头、完整 endpoint、API Key 或原始密钥片段。
3. `backend/.env` 由 `.gitignore` 的 `**/.env` 忽略，不应提交真实密钥。
4. 当前 LLM Client 只提供基础调用能力，不允许模型绕过 Evidence/Claim 约束直接生成事实；后续接入 Writer Agent 时仍必须保持“只能基于结构化证据组织语言”的边界。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_llm_client.py`：通过，7 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\services\llm_client.py backend\tests\test_llm_client.py`：通过。

### 边界

1. 本次没有把 LLM 接入 Writer、Analysis、Collection 或 QA Agent。
2. 本次没有改变报告内容生成、Word 导出、Trace API、存储表结构或 OpenAPI Schema。
3. 本次没有引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind、外部实时采集或新微服务。

## 2026-06-03：Writer Agent 接入 LLM 报告语言组织

本次将统一 LLM Client 接入 Writer Agent，但只用于“章节摘要语言组织”，不让模型改动结构化事实、证据引用、评分、QA 状态、报告章节数量或下游 API Schema。后端仍先用本地规则完整生成 `ReportData`，再把压缩后的报告上下文交给 LLM，请模型返回已有章节的中文摘要；模型不可用或输出无效时保留本地规则摘要。

### 接入边界

1. `backend/app/agents/writer.py`：`writer_agent_node` 新增可选 `llm_client` 参数，默认使用 `LLMClient()`；LangGraph 仍可按原 `writer_agent_node(state)` 方式调用。
2. `backend/app/agents/writer.py`：新增 `_rewrite_report_summaries_with_llm`，在 `_build_report_data` 完成本地结构化报告后执行，只应用 `{"sections":[{"section_id","summary"}]}` 中合法、非空、且属于现有 `section_order` 的摘要。
3. `backend/app/agents/writer.py`：LLM 输入上下文只包含任务类别、目标产品名、章节摘要、章节计数、风险标记和前三条压缩 items；不发送 API Key、不发送 Prompt 预览、不发送完整 Trace、不发送本地截图路径。
4. `backend/app/agents/writer.py`：LLM metadata 写入 `state["metadata"]["writer_agent"]["llm_rewrite"]`，只记录 `status`、`attempts`、`fallback_reason`、`error_count` 和 token 计数，不记录 raw response 或密钥。
5. `backend/app/agents/writer.py`：当 LLM 返回 token usage 且总量大于 0 时，写入既有 `token_usage_logs`，供 Trace 服务沿用现有 token 展示链路。
6. `backend/tests/test_writer_agent.py`：使用 fake LLM Client 注入测试，覆盖“只改 summary、不改证据链”和“fallback 时保留本地报告”。

### 安全与事实约束

1. LLM system prompt 明确要求只能使用输入材料，不得编造价格、销量、认证、尺寸、排名；证据不足必须写“暂无可靠数据”或“建议复核”。
2. LLM 输出只影响 `ReportSection.summary`，不会新增 Claim、Evidence、CompetitionEdge、ReviewTask 或策略建议事实。
3. LLM 输出不会覆盖 `items`、`claim_ids`、`evidence_ids`、`risk_flags`、`section_order`、`report_id`、`task_id` 或 `generated_at`。
4. 无 Key、未启用、缺 Base URL、请求失败、非 JSON 或章节格式不合规时自动降级，不阻断完整 Demo。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_llm_client.py backend\tests\test_workflow.py backend\tests\test_task_execution.py`：通过，23 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\agents\writer.py backend\tests\test_writer_agent.py`：通过。

### 边界

1. 本次没有让 LLM 参与 Analysis、Collection、QA、评分公式、竞品召回或证据抽取。
2. 本次没有改变 OpenAPI Schema、数据库表结构、ReportData Schema、Word 导出格式或前端 API 调用。
3. 本次没有新增依赖、外部采集、队列、缓存、微服务或未批准的前端/后端基础设施。
## 2026-06-04：Doubao JSON 输出兼容修复

本次修复保持统一 `LLMClient` 与 Writer Agent 接入边界不变，只补齐 Doubao Ark OpenAI-compatible endpoint 的兼容行为：部分 Doubao endpoint 会对 `response_format={"type":"json_object"}` 返回 400，错误信息为该模型不支持 `json_object`。为避免模型可用但报告语言组织被整体降级，`backend/app/services/llm_client.py` 现在会先按 JSON mode 请求；如果仅因 `response_format` 不兼容失败，则自动移除 `response_format` 再请求一次，同时继续通过 system prompt 要求 JSON 输出，并用本地 `coerce_structured_model_output` 做结构化校验与 fallback。

### 文件作用更新

1. `backend/app/services/llm_client.py`：统一 LLM Client。负责读取本地 `.env`、调用 Doubao OpenAI-compatible `/chat/completions`、记录 token、脱敏错误、超时重试、无 Key 降级，以及本次新增的 `response_format` 不兼容自动重试。
2. `backend/tests/test_llm_client.py`：覆盖 LLM Client 的配置加载、缺 Key 降级、OpenAI-compatible 请求结构、Base URL 自动补协议、非 JSON 重试、请求失败脱敏、token 日志转换，以及 Doubao 不支持 `response_format` 时移除该参数后继续成功解析 JSON 的兼容场景。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_llm_client.py`：通过，9 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\services\llm_client.py backend\tests\test_llm_client.py`：通过。
3. 本地最小 Doubao 调用已返回结构化 JSON，`used_fallback=false`，`total_tokens=158`。
4. 重跑完整任务 `task_ec3695ed4bc44057947079f7764a5768` 后，Trace `token_usage_count=1`，说明 Writer Agent 已实际记录模型用量。
## 2026-06-04：报告页等待态与正文收敛

本次调整同时处理报告生成体验和网页报告可读性。问题来源不是单纯“数据少”，而是三层因素叠加：第一，接入 Doubao 后 Writer Agent 需要等待 LLM 改写章节摘要，报告在生成阶段会比纯本地规则慢；第二，原报告页只显示普通加载态，未把 `REPORT_NOT_READY` 解释为“报告正在生成”并自动轮询；第三，网页报告渲染层把每个结构化 item 都展开为多段模板解释，LLM 章节摘要又可能逐项罗列，导致正文看起来很长但重点分散。当前修复不改变 ReportData Schema、Claim/Evidence 绑定、Word 导出、Agent DAG 或评分规则，只收敛等待体验、LLM 摘要约束和网页正文展示层。

### 文件作用更新

1. `frontend/src/App.tsx`：报告页识别 `REPORT_NOT_READY` 后显示“报告正在生成”等待态，并每 2 秒自动重新请求报告；报告章节正文对竞争格局、核心竞品、决策链、动态切片等高重复章节只展开前三个重点 item，其余关系计入统计但不逐条铺开，避免网页报告被重复模板句淹没。
2. `frontend/src/App.test.tsx`：新增报告未就绪自动轮询回归测试，并更新等待态文案断言；继续覆盖报告页正文、下载和敏感信息脱敏等既有行为。
3. `backend/app/agents/writer.py`：Writer Agent 的 LLM system prompt 和 user rules 改为要求章节摘要保持短结论，1 到 2 句、尽量 120 字以内，不逐项罗列切片、关系或证据编号，不重复证据口径和空泛背景，只提炼本章最重要的结论、原因和下一步动作。

### 设计判断

1. 报告冗余的主要原因是结构和呈现：章节摘要与 item 展开同时承担“解释全部关系”的职责，导致重复；数据量不足只是放大了模板化表达，因为缺少更丰富的评论洞察、用户研究和真实对比维度时，系统会反复围绕价格带、场景、证据数量说话。
2. 当前 MVP 仍保持“先本地规则生成完整 ReportData，再由 LLM 只改写摘要”的安全边界；LLM 不新增事实、不改证据链、不改评分和章节结构。
3. 网页报告优先呈现重点判断，完整可追溯信息仍保留在 ReportData、Trace、证据链和 Word 导出链路中。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx`：通过，56 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\typescript\bin\tsc --noEmit`：通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_llm_client.py`：通过，15 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\agents\writer.py backend\app\services\llm_client.py backend\tests\test_writer_agent.py backend\tests\test_llm_client.py`：通过。

### 2026-06-04 补充：报告页只读缓存与短卡片展示

1. `frontend/src/App.tsx`：报告页查询新增 10 分钟 `staleTime` 和 `gcTime`。页面切换回来时优先复用已读取的报告数据，避免用户误以为每次点击“分析报告”都会重新调用大模型。后端仍以任务保存的 report artifact 为准，不在报告查看阶段重新生成报告。
2. `frontend/src/App.tsx`：章节 summary 不再原样展示 Writer 保存的长段落，而是按章节类型给出固定短说明；总体判断进一步压缩为“主要压力 + 依据”两句以内；竞争格局和动态切片的 item 标题从“分析项 N”改为“重点切片：价格带/人群/场景”，正文压缩为切片、对象、压力和依据，避免重复解释同一类购买理由。
3. `frontend/src/App.test.tsx`：同步更新报告页断言，覆盖新的短判断、重点切片标题和核心竞品短卡片文案。

### 验证记录

1. `.\node_modules\.bin\vitest.cmd run --configLoader runner --root . src\App.test.tsx`：通过，56 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit`：通过。

## 2026-06-04：用户报告与证据页隐藏内部审计口径

本次调整继续收敛用户可见页面的语言边界：报告页不再展示“依据：几条判断、几条证据；证据不足处保守处理”这类内部审计口径；证据与过程追踪页不再把 `[REDACTED]`、`source.access_time`、`QA 打回后补齐字段` 或“评论洞察尚待后续结构化抽取”作为用户证据正文展示。后端仍保存证据数量、Claim/Evidence 绑定、QA 记录和风险标记，只是用户页默认呈现业务含义，不暴露实现字段。

### 文件作用更新

1. `backend/app/schemas/trace.py`：`TraceEvidenceItem` 新增可选 `access_time` 字段，保留既有 `access_time_status`，用于前端在证据链中展示具体访问时间。
2. `backend/app/services/trace_service.py`：Trace 证据项构造时传出 `Evidence.access_time`；无访问时间时仍保留 `missing_access_time` 风险标记。
3. `frontend/src/api/schema.ts`：同步前端 OpenAPI 类型，允许 Trace 证据项读取 `access_time`。
4. `frontend/src/App.tsx`：报告页移除依据计数句；证据链访问时间优先显示具体时间；证据段落会过滤 `[REDACTED]`、内部补字段话术和评论抽取占位句；质检记录把内部字段名转换为“证据访问时间”等用户可理解表达。
5. `frontend/src/App.test.tsx`：覆盖报告页不显示依据计数、证据链显示具体访问时间、内部字段与占位符不出现在用户页面。
6. `backend/tests/test_trace_api.py`：覆盖 Trace API 在访问时间可用时返回具体 `access_time`。

### 验证记录

1. `.\node_modules\.bin\vitest.cmd run --configLoader runner --root . src\App.test.tsx`：通过，56 个测试通过。
2. `.\node_modules\.bin\tsc.cmd --noEmit`：通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_trace_api.py`：通过，9 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\schemas\trace.py backend\app\services\trace_service.py backend\tests\test_trace_api.py`：通过。

## 2026-06-04：Writer 报告规划器与 LLM 段落 JSON

本次将 Writer Agent 从“完整生成所有结构化报告后只让 LLM 润色章节摘要”升级为两段式报告生成：先由本地报告规划器选择 3 到 5 条最值得展示的重点竞争关系，再让 LLM 基于已选关系、相关 Claim、Evidence 和商品信息生成短段落 JSON。LLM 仍不能新增竞品、评分、证据、Claim 或事实，只能回填已有 section/item 的中文表达。

### 文件作用更新

1. `backend/app/agents/writer.py`：新增 `ReportPlan` 和 `_build_report_plan`。规划器按竞争分排序，并尽量覆盖不同竞品与不同价格带/人群/场景切片；报告正文的核心竞品、竞争格局、决策链和策略建议只围绕计划内重点关系展开，避免把所有结构化 item 都塞进用户报告。
2. `backend/app/agents/writer.py`：Writer metadata 新增 `report_plan`，记录 `total_edge_count` 和 `planned_edge_ids`，用于后续追踪“报告为什么只展开这些关系”。
3. `backend/app/agents/writer.py`：LLM 调用 schema 从 `writer_report_summary_rewrite` 升级为 `writer_report_paragraph_generation`。Prompt 输入包括任务信息、目标产品、规划后的重点关系、相关证据摘要、章节和 item_key；输出为 `sections[].summary` 与 `sections[].items[].{item_key, conclusion, reason, action}`。
4. `backend/app/agents/writer.py`：新增 `_apply_llm_report_sections`。只允许 LLM 更新已存在 section 的 summary，以及已存在 item_key 的 `llm_paragraphs`；未知 section、未知 item_key、空字段会被忽略。
5. `frontend/src/App.tsx`：报告 item 渲染时优先读取 `llm_paragraphs.conclusion/reason/action`，没有该字段时继续使用本地规则短文案，确保无 Key 或 LLM fallback 时 Demo 仍完整。
6. `backend/tests/test_writer_agent.py`：新增报告规划器测试，覆盖正文重点 item 数量限制和 metadata；更新 LLM 测试，验证模型输出段落 JSON 能写入已有 item，且 Prompt 包含 competition_edges/evidence 上下文。
7. `frontend/src/App.test.tsx`：新增 LLM 段落优先展示测试，确保前端使用模型生成的短结论、原因和行动建议。

### 设计边界

1. 报告规划器是本地规则，不依赖外部模型；无 Key 时仍能先筛重点关系并生成可读报告。
2. LLM 不改变 `edge_score`、`claim_ids`、`evidence_ids`、`risk_flags`、`section_order` 或证据链，只写展示层段落。
3. LLM Prompt 明确禁止输出内部 ID、字段名、Trace、Token、QA 字段名，以及“几条判断/几条证据”的审计口径。
4. 当前仍未让 LLM 做评分、召回、证据抽取或数据扩增；信息量不足的问题仍需要后续评论/卖点洞察抽取和数据扩增解决。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py`：通过，7 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_llm_client.py backend\tests\test_writer_agent.py`：通过，16 个测试通过。
3. `.\node_modules\.bin\vitest.cmd run --configLoader runner --root . src\App.test.tsx`：通过，57 个测试通过。
4. `.\node_modules\.bin\tsc.cmd --noEmit`：通过。
5. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\agents\writer.py backend\tests\test_writer_agent.py`：通过。

## 2026-06-04：模型报告生成稳定性修复

本次针对 Writer Agent 接入 Doubao 后出现的 `429 Too Many Requests`、长 prompt 超时和模型输出非纯 JSON 三类问题做稳定性修复。目标是优先保证模型报告段落能真实落入 `ReportData.items[].llm_paragraphs`，同时保留本地规则 fallback，不让外部模型故障阻断完整 Demo。

### 文件作用更新

1. `backend/app/services/llm_client.py`：新增 `LLM_RETRY_BACKOFF_SECONDS` 配置，默认 8 秒；请求失败后若仍有重试次数，会等待后再重试。遇到 429 且响应头包含 `Retry-After` 时优先按平台建议等待，避免连续快速重试放大限流。
2. `backend/app/services/llm_client.py`：`LLMSettings.safe_metadata()` 新增 `retry_backoff_seconds`，仍不记录或输出 API Key。
3. `backend/app/services/structured_output.py`：结构化输出解析器支持从 Markdown fenced code block 或普通说明文本中抽取第一个 JSON object。Doubao 即使输出“以下是 JSON”加代码块和解释，也能被解析成结构化对象。
4. `backend/app/agents/writer.py`：Writer LLM prompt 进一步压缩，只发送用户报告正文需要的章节、重点 item、相关产品、重点竞争关系和相关证据；证据附录、流程附录不再送入模型。
5. `backend/app/agents/writer.py`：Writer LLM prompt 明确顶层输出必须是 `{"sections":[...]}`，并提供每个 section 允许的 `item_key`，降低模型返回不可应用结构的概率。
6. `backend/tests/test_llm_client.py`：新增 429 后按 `Retry-After` 退避再成功的测试。
7. `backend/tests/test_structured_output.py`：新增从 Markdown 说明中提取 JSON object 的测试。

### 运行注意

1. Doubao-Seed-2.0-lite 对 15KB 以上 prompt 的响应可能超过 30 秒。本地跑模型版报告时建议用 `LLM_TIMEOUT_SECONDS=90` 启动后端；本次没有写入 `.env`，而是用进程环境变量临时启动验证。
2. `LLM_MAX_RETRIES` 不宜太高。限流时重点是等待退避，不是快速重打。
3. 新任务 `task_7bc99958a8cf4b5792a4bed1244484b3` 已验证模型段落真实写入：核心竞品章节 `CORE_LLM_COUNT=5`，首条段落为“霍曼智能猫砂盆超大号自动补砂款为高价位核心直接竞品 / 二者竞争匹配评分最高，覆盖全用户决策链路 / 完成两款产品的核心功能逐项对标”。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_structured_output.py backend\tests\test_llm_client.py backend\tests\test_writer_agent.py`：通过，20 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\services\structured_output.py backend\app\services\llm_client.py backend\app\agents\writer.py backend\tests\test_structured_output.py backend\tests\test_llm_client.py backend\tests\test_writer_agent.py`：通过。
## 2026-06-04：Writer 评论洞察抽取与报告质检 LLM

本次在不改变 LangGraph DAG、ReportData Schema、评分公式和证据链边界的前提下，继续增强 Writer Agent 的模型能力。Writer 现在不再只让 LLM 写报告段落，而是在报告生成阶段拆成三段模型子流程：先从已有 SKU 快照、评论摘要和用户研究文本中抽取“痛点、购买理由、异议点”，再把这些洞察连同重点竞品关系交给段落生成，最后由独立的质检 LLM 检查报告是否冗余、是否像人话、是否出现内部字段或 ID、是否在证据不足时写得过满。三个子流程都通过统一 `LLMClient` 调用 Doubao OpenAI-compatible API，均支持无 Key 时本地降级，且只记录 token 用量，不记录 API Key。

### 文件作用更新

1. `backend/app/agents/writer.py`：Writer Agent 现在负责本地报告规划、LLM 评论/卖点洞察抽取、LLM 报告段落 JSON 生成和 LLM 报告质检。新增 `_extract_report_insights_with_llm`、`_insight_extraction_user_prompt`、`_apply_llm_extracted_insights`，用于从已有 ReviewInsight、Evidence 和 `research_text` 中抽取用户痛点、购买理由和异议点，并把清洗后的中文洞察写入 `target_opportunities_and_risks.items[0].llm_extracted_insights`。新增 `_review_report_quality_with_llm`、`_report_quality_user_prompt`、`_apply_llm_report_quality`，用于在段落生成后保存中文质检结果到 `evidence_quality_appendix.items[0].llm_report_quality`。
2. `backend/app/services/llm_client.py`：继续作为唯一 LLM 调用入口，新增的洞察抽取、段落生成、报告质检都复用该 Client 的 `.env` 配置、超时重试、JSON 解析、429 退避、token 记录和无 Key fallback 能力。
3. `backend/tests/test_writer_agent.py`：Writer 测试新增队列式 Fake LLM Client，普通 Writer 单测显式传入禁用 LLM 的假客户端，避免测试误打真实模型；专项测试按顺序模拟洞察抽取、段落生成和报告质检三次调用，并验证洞察进入报告数据、段落进入 `llm_paragraphs`、质检进入中文质检字段、三次 token usage 均记录到 Writer run。

### 设计边界

1. 洞察抽取只从已有 SKU 快照、评论摘要和用户研究文本中提炼表达，不创建新的 Product、Evidence、Claim 或 CompetitionEdge。
2. 质检 LLM 只记录问题，不直接改写报告事实、评分、证据绑定或章节结构。
3. LLM Prompt 明确禁止输出 `task_id`、`edge_id`、`claim_id`、`evidence_id`、Trace、Token、API Key 和“几条证据/几条判断”这类内部审计口径。
4. 无 Key、限流、超时或模型非 JSON 输出时，Writer 仍使用本地规则报告完成 Demo；模型增强只提升表达和洞察质量，不成为主链路单点依赖。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_llm_client.py backend\tests\test_structured_output.py`：通过，20 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\agents\writer.py backend\app\services\llm_client.py backend\app\services\structured_output.py backend\tests\test_writer_agent.py backend\tests\test_llm_client.py backend\tests\test_structured_output.py`：通过。
## 2026-06-05：Word 报告导出阅读版与缓存复用

本次修复分析报告页下载 Word 时长时间停留在“下载中”、以及 Word 正文大量出现内部字段和原始截图的问题。根因有两层：第一，`WordReportService.export_word_report` 每次下载都会重新跑完整 Agent workflow、重新构造报告并生成关系图图片，导致导出链路明显偏慢；第二，`render_word_report` 旧实现会递归展开 `ReportData.items` 的所有结构化字段，因此 `edge_id`、`competitor_product_id`、`claim_ids`、`evidence_ids`、`screenshot_path` 等内部字段会以英文/字段名形式进入 Word 正文。现在 Word 导出改为“用户阅读版”：复用已有报告产物，优先返回已生成的新版本 Word 文件，正文只保留结论、原因和行动建议，不展示商品原始截图、缩略图、截图路径、任务编号、报告编号、Claim/Evidence/Edge 内部索引。

### 文件作用更新

1. `backend/app/services/word_report_service.py`：新增 `WORD_REPORT_RENDER_VERSION = "readable_v2"`。导出时先检查同一任务是否已有该版本 Word artifact 且文件仍存在，命中时直接返回，避免重复渲染；没有 Word 缓存时优先读取已保存的 `report` artifact，只有报告 artifact 不存在才兜底执行 workflow。
2. `backend/app/services/word_report_service.py`：`render_word_report` 不再调用产品图片摘要和关系图图片写入。Word metadata 中 `target_image_status` 固定为 `omitted`，`core_competitor_image_count` 为 `0`，`relationship_graph_included` 为 `false`，避免把用户不需要的原始素材放进正式报告。
3. `backend/app/services/word_report_service.py`：封面不再展示 `task_id` 或 `report_id`，只展示报告名称、生成时间和导出时间。
4. `backend/app/services/word_report_service.py`：正文渲染从递归字段 dump 改为按章节生成自然语言段落。优先使用 `items[].llm_paragraphs`；没有模型段落时按章节类型生成“核心竞品、重点切片、决策阶段、行动建议、机会风险、证据质检”等可读分析段落。内部字段黑名单覆盖 `edge_id`、`claim_id`、`evidence_id`、`product_id`、`task_id`、`report_id`、`screenshot_path`、`source_url` 等字段。
5. `backend/tests/test_word_report_service.py`：更新 Word 导出测试，验证 docx 可打开、导出 metadata 使用 `readable_v2`、不生成关系图、不展示产品图片摘要、不出现 `Edge Id`、`Claim Ids`、`Competitor Product Id`、`edge_prod`、`claim_edge` 等不可读内容，并新增“第二次导出复用缓存文件”的回归测试。
6. `backend/tests/test_v2_security_compliance.py`：更新 Word 安全断言，允许敏感内容被完全移除而不是必须以 `[REDACTED]` 形式出现；继续验证真实敏感片段不会进入导出文本。

### 设计边界

1. Word 报告是正式阅读交付物，不再承担原始证据截图和内部结构化字段审计职责；这些内容仍保留在数据库 artifact、网页证据链和 Trace 页面。
2. Word 正文不修改评分、证据绑定、Claim、CompetitionEdge 或 ReportData Schema，只改变导出呈现方式。
3. 缓存只复用 `readable_v2` 版本 Word 文件，避免旧版字段转储文档继续被返回。
4. 如果缓存文件被删除，服务会重新渲染；如果任务没有 report artifact，仍保留兜底 workflow 执行能力。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_word_report_service.py backend\tests\test_reports_api.py backend\tests\test_v2_security_compliance.py`：通过，15 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\services\word_report_service.py backend\tests\test_word_report_service.py backend\tests\test_v2_security_compliance.py`：通过。

## 2026-06-05：Writer LLM 分析扩增与类目知识框架

本次在已有报告规划器、洞察抽取、段落 JSON 生成和质检 LLM 的基础上，新增“分析结果扩增”层。它以现有 SKU 快照、Evidence、Claim、CompetitionEdge、已抽取洞察和本地类目知识框架为地基，让 LLM 把重点报告 item 扩写成更像正式分析报告的中文段落。扩增只增强解释深度、用户决策推理和行动建议，不创建新的商品、证据、评分、销量、认证、价格或外部事实。

### 文件作用更新

1. `backend/app/agents/writer.py`：新增 `_expand_report_analysis_with_llm`、`_analysis_expansion_user_prompt`、`_section_expansion_context`、`_category_knowledge_context` 和 `_apply_llm_expanded_analysis`。Writer 在本地报告、洞察抽取和短段落生成之后调用扩增 LLM，输出 schema 为 `writer_report_analysis_expansion`，只允许写入已有 section/item 的 `llm_expanded_analysis` 段落。
2. `backend/app/agents/writer.py`：`_category_knowledge_context` 提供自动猫砂盆类目的通用分析框架，包括清理负担、除臭与封闭性、容量与多猫适配、安全可靠性、维护成本和信息表达。该框架只能帮助组织分析，不作为具体 SKU 事实来源；涉及具体产品表现时仍必须回到 Evidence/Claim/Edge。
3. `backend/app/agents/writer.py`：Writer metadata 新增 `llm_analysis_expansion`，记录扩增调用是否应用、fallback 原因和 token 使用情况；token usage logs 继续只记录模型、prompt/completion/total token，不记录 API Key 或原始输出。
4. `frontend/src/App.tsx`：报告正文渲染优先读取 `items[].llm_expanded_analysis`，其后才读取 `llm_paragraphs` 或本地规则文案。这样网页报告可以呈现更完整的分析推理，而不是只展示短结论、原因、行动建议三段。
5. `backend/app/services/word_report_service.py`：Word 阅读版正文同样优先使用 `llm_expanded_analysis`，保证网页报告和下载报告在分析深度上保持一致，同时继续隐藏内部 ID、截图路径、Claim/Evidence/Edge 字段和原始素材。
6. `backend/tests/test_writer_agent.py`、`frontend/src/App.test.tsx`、`backend/tests/test_word_report_service.py`：补充扩增链路测试，验证 LLM 扩增段落能进入 ReportData、网页报告和 Word 报告，并且不会绕过既有结构化证据边界。

### 设计边界

1. 当前没有接入实时外部检索，也没有改变 `snapshot_plus_live` 的 MVP 占位性质；“相关知识”先以本地类目知识框架注入，避免把未经采集和审计的外部信息写进报告。
2. LLM 扩增不得输出内部 ID、字段名、Trace、Token、API Key、证据计数口径，也不得把“暂无可靠数据”的领域写成确定事实。
3. 扩增内容只落在展示层字段 `llm_expanded_analysis`，不修改 `edge_score`、`claim_ids`、`evidence_ids`、`risk_flags`、`section_order`、评分公式或 QA 结果。
4. 无 Key、429、超时、非 JSON 或输出不可应用时，Writer 仍保留已有短段落和本地规则报告，确保 Demo 主链路可完成。
5. 后续如果要真正检索外部知识，应先新增独立的可审计 Retrieval/Knowledge 服务，保存来源、访问时间和证据等级，再由 Writer 只引用通过审计的知识 Artifact。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_writer_agent.py backend/tests/test_word_report_service.py`：通过，12 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend/app/agents/writer.py backend/app/services/word_report_service.py backend/tests/test_writer_agent.py backend/tests/test_word_report_service.py`：通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx`：通过，59 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\typescript\bin\tsc --noEmit`：通过。

## 2026-06-05：Knowledge/Retrieval Service 与可审计知识 Artifact

本次将上一阶段 Writer 内部的“类目知识框架”提升为独立的 Knowledge/Retrieval 层。系统现在会在 Writer 生成报告语言之前，基于任务、重点竞品关系和报告焦点生成一份 `KnowledgeArtifact`，再把压缩后的知识上下文送入 LLM。这样报告扩增可以使用自动猫砂盆类目的通用决策维度，但这些知识不会直接混进报告正文，也不会被误认为某个 SKU 的事实证据。

### 文件作用更新

1. `backend/app/schemas/knowledge.py`：新增 `KnowledgeSource`、`KnowledgeItem` 和 `KnowledgeArtifact`。每份知识 Artifact 都包含来源、访问时间、可信度、使用边界、检索模式、是否执行外部检索、检索上下文和局限性。
2. `backend/app/services/knowledge_retrieval.py`：新增 `KnowledgeRetrievalService` 和 `compact_knowledge_for_llm`。当前实现使用本地静态自动猫砂盆类目知识库，覆盖清理负担、除臭与封闭性、容量与多猫适配、安全可靠性、维护成本、信息表达和竞品分析框架。
3. `backend/app/graph/state.py` 与 `backend/app/graph/__init__.py`：`TaskGraphState` 新增 `knowledge_artifacts` 列表和 `append_knowledge_artifact`，Trace 序列化计数也会包含知识 Artifact。
4. `backend/app/agents/writer.py`：Writer 在 `_build_report_data` 后调用 `KnowledgeRetrievalService().retrieve_for_writer(...)`，将结果追加到 Graph State，并把 `compact_knowledge_for_llm(...)` 输出传给段落生成和分析扩增 LLM。Writer metadata 新增 `knowledge_retrieval`，记录 `knowledge_id`、检索模式、是否外部检索、知识项数量和来源数量。
5. `backend/app/services/task_execution.py`：任务完成后将 `knowledge_artifacts` 按 `knowledge_artifact` 类型缓存到 SQLite Artifact 表，保证报告、Trace、后续导出和复核可以追溯同一份知识地基。
6. `backend/app/schemas/__init__.py` 与 `backend/app/services/__init__.py`：统一导出新增 schema、服务和 `KNOWLEDGE_ARTIFACT_TYPE`，保持项目现有模块访问方式。

### 设计边界

1. 当前没有执行实时外部检索，`KnowledgeArtifact.external_search_performed` 固定为 `false`，`retrieval_mode` 为 `local_static_category_framework`。
2. 知识项只作为分析框架，不作为具体 SKU 的价格、销量、认证、排名、尺寸或真实评论依据；具体产品判断仍必须回到 Evidence、Claim 和 CompetitionEdge。
3. Writer Prompt 中现在引用的是可审计 `knowledge_artifact`，而不是隐式散落的知识字符串。后续接外网检索时，应继续先保存为 `KnowledgeArtifact`，再允许 Writer 使用。
4. 外部知识未来必须记录 `source_url`、`access_time`、`confidence_level` 和 `limitations`，否则不能进入正式报告生成上下文。
5. 该层不改变 LangGraph 节点数量、ReportData Schema、评分公式、QA 规则或 Evidence/Claim 绑定，只新增可追溯的知识上下文。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_knowledge_retrieval.py backend/tests/test_graph_state.py backend/tests/test_writer_agent.py backend/tests/test_task_execution.py`：通过，18 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend/app/schemas/knowledge.py backend/app/services/knowledge_retrieval.py backend/app/graph/state.py backend/app/graph/__init__.py backend/app/agents/writer.py backend/app/services/task_execution.py backend/app/services/__init__.py backend/app/schemas/__init__.py backend/tests/test_knowledge_retrieval.py backend/tests/test_graph_state.py backend/tests/test_writer_agent.py backend/tests/test_task_execution.py`：通过。

## 2026-06-05：报告缓存锁定与显式重新生成

本次把报告读取链路从“页面请求时可能重新跑 Writer/LLM”收敛为“默认读取已锁定报告，只有用户显式点击重新生成才重新调用模型”。修复的核心问题是 `ReportService._latest_report()` 曾经因为不可达返回语句导致已缓存报告永远读不到，从而让 `GET /tasks/{task_id}/report` 在完成任务后仍可能反复执行 workflow。现在网页报告、页面刷新、页面切换和 Word 下载都会优先复用同一份已保存 `report_data` Artifact，减少 429、等待时间和同任务报告漂移。

### 文件作用更新

1. `backend/app/services/report_service.py`：修复 `_latest_report()` 缓存读取逻辑；`get_report_data()` 现在优先返回最新已保存 `report_data`，只有历史任务缺少报告 Artifact 时才兜底生成一次。新增 `regenerate_report_data(task_id)`，作为唯一显式重跑 workflow/LLM 的服务入口。
2. `backend/app/services/report_service.py`：显式重新生成时会先把已有报告版本预装入 `TaskGraphState["reports"]`，因此 Writer 生成的新 `report_id` 会递增，例如 `_001` 到 `_002`，不会覆盖旧报告版本。
3. `backend/app/api/routes_reports.py`：新增 `POST /tasks/{task_id}/report/regenerate`，返回新的 `ReportData`。普通 `GET /tasks/{task_id}/report` 不再承担重新生成职责。
4. `backend/app/services/word_report_service.py`：Word 下载前先确定当前最新锁定 `report_id`，只复用同一 `report_id` 的 Word 缓存。如果报告重新生成后尚未导出 Word，会为新报告版本重新渲染 Word，避免返回旧报告文件。
5. `frontend/src/App.tsx`：报告页新增“重新生成报告”按钮。默认进入报告页仍使用 TanStack Query 无限 stale 缓存和 `completedReportCache`；只有点击该按钮才调用 `POST /report/regenerate`，成功后同步更新页面缓存。
6. `frontend/src/App.test.tsx`、`backend/tests/test_reports_api.py`：新增回归测试，覆盖二次 GET 不重跑、显式重新生成创建新报告版本、Word 导出跟随最新版本，以及前端按钮点击前不调用重新生成接口。

### 设计边界

1. 默认用户行为是只读查看报告：刷新页面、切换页面、下载 Word 都不会重新调用 LLM。
2. 显式重新生成会创建新报告版本，而不是覆盖旧版本；旧版本仍保留在 Artifact 表，便于后续版本对比能力扩展。
3. 历史任务如果已经是 `completed` 但没有 `report_data` Artifact，`GET /report` 仍允许兜底生成一次，生成后随即锁定。
4. Word 缓存以 `report_id + render_version` 为有效复用条件，只要当前最新报告版本变化，就不会复用旧 Word。
5. 本次没有改变 ReportData Schema、Writer 事实边界、QA 规则、评分公式或 Knowledge Artifact；只调整报告生成时机、版本号和缓存读取策略。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_reports_api.py backend/tests/test_word_report_service.py backend/tests/test_task_execution.py`：通过，18 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend/app/services/report_service.py backend/app/api/routes_reports.py backend/app/services/word_report_service.py backend/tests/test_reports_api.py backend/tests/test_word_report_service.py backend/tests/test_task_execution.py`：通过。
3. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_knowledge_retrieval.py backend/tests/test_writer_agent.py`：通过，9 个测试通过。
4. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx`：通过，60 个测试通过。
5. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\typescript\bin\tsc --noEmit`：通过。

## 2026-06-05：竞争态势总览缓存前置与快速补缓存

本次修复竞争态势总览页加载过慢的问题。根因是 `OverviewService.get_overview()` 在找不到 `overview_data` Artifact 时会直接重跑完整 LangGraph workflow；而任务执行完成时之前没有主动缓存 `overview_data`，导致用户第一次打开 `/overview` 时可能触发 Collection、Analysis、QA、Writer 以及 LLM 报告链路。现在总览页读取路径改为“优先读 overview 缓存，其次用已保存的 battlefield 缓存快速补 overview，最后才兜底重跑 workflow”，新任务在完成时也会直接保存默认总览缓存。

### 文件作用更新

1. `backend/app/services/task_execution.py`：任务成功完成后，除了缓存 Trace、产品画像、竞争图谱、报告和知识 Artifact，也会用同一份 LangGraph 结果生成并保存默认 `overview_data`。任务元数据的 `artifact_counts` 新增 `overview_data` 计数，便于后续排查任务完成后是否已具备总览缓存。
2. `backend/app/services/overview_service.py`：`get_overview()` 缓存未命中时不再立即重跑完整 workflow，而是先读取默认或当前切片的 `battlefield_data` Artifact，并从图谱节点、竞争边、证据卡片和 QA 状态中快速构造 `OverviewData`。该快速补缓存结果会以 `metadata.source = cached_battlefield_artifact` 标记并保存为正式 `overview_data`，之后刷新页面直接命中缓存。
3. `backend/tests/test_overview_api.py`：新增回归测试，验证在已有 `battlefield_data` 但缺少 `overview_data` 的历史任务上，总览接口不会重新执行 workflow，而是快速生成并缓存总览。
4. `backend/tests/test_task_execution.py`：端到端任务执行测试新增断言，确保任务完成后已经保存 1 份 `overview_data`，并且前端请求总览时拿到的是 `langgraph_workflow` 来源的锁定产物。

### 设计边界

1. 总览页默认是读取型页面，不应成为隐式重新分析入口。
2. 从 `battlefield_data` 快速补出的总览只用于历史任务兼容和缓存缺口修复，不改变 CompetitionEdge、Claim、Evidence、ReportData 或评分公式。
3. 只有 `overview_data` 和 `battlefield_data` 都缺失的已完成历史任务，才保留最后的 workflow 兜底路径。
4. 该改动不新增技术栈，不改变前端 API 契约，前端仍只请求 `GET /tasks/{task_id}/overview`。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_overview_api.py backend\tests\test_task_execution.py`：通过，8 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\services\overview_service.py backend\app\services\task_execution.py backend\tests\test_overview_api.py backend\tests\test_task_execution.py`：通过。

## 2026-06-05：Writer 质检 LLM 一次性定向修复闭环

本次把 Writer 的报告质检 LLM 从“只记录问题”升级为“发现问题后最多自动修一次”。Writer 仍先按既有顺序完成洞察抽取、短段落生成、分析扩增和质检；如果质检返回 `needs_revision` 且不是 fallback，系统会只把质检定位到的章节或分析项送入 `writer_report_quality_repair`，让 LLM 删除内部字段、压缩冗余表达、修正证据不足却写得过满的问题。修复结果只覆盖目标 item 的 `llm_expanded_analysis` 和 `llm_paragraphs`，不会修改评分、证据绑定、Claim、CompetitionEdge 或 ReportData 结构。

### 文件作用更新

1. `backend/app/agents/writer.py`：新增 `_repair_report_quality_issues_with_llm`，在 `_review_report_quality_with_llm` 后执行。该函数仅在质检结果为 `needs_revision`、未走 fallback、且能定位到可修复段落时调用统一 `LLMClient.complete_json`，schema 名为 `writer_report_quality_repair`。
2. `backend/app/agents/writer.py`：新增 `_quality_repair_targets`、`_quality_issue_location`、`_quality_repair_user_prompt` 和 `_apply_llm_quality_repair`。这些函数负责从质检 issue 中解析 `section_id` / `item_key`，构造只包含问题段落、相关证据、竞争关系和知识 Artifact 的修复输入，并把模型返回定向写回原 item。
3. `backend/app/agents/writer.py`：质检 prompt 现在要求每条 issue 尽量返回 `section_id` 和 `item_key`，便于后续修复精确落点；无法定位 item 时允许只修章节 summary。
4. `backend/app/agents/writer.py`：Writer metadata 新增 `llm_quality_repair`，记录修复调用是否应用、fallback 原因和 token 使用；token 日志新增可选 usage id `usage_<run_id>_llm_quality_repair`。
5. `backend/app/agents/writer.py`：`evidence_quality_appendix.items[0].llm_report_quality` 新增 `自动修正` 字段。若修复成功，`质检状态` 会从“需要修改”更新为“已自动修正”，同时记录目标段落数和应用修改数。
6. `backend/tests/test_writer_agent.py`：新增回归测试，模拟质检发现 `Edge Id`、证据计数等内部口径后，Writer 只对对应 `conclusion_summary` item 触发一次修复，并验证修复后段落不再包含内部字段。

### 设计边界

1. 修复最多执行一次，不做质检-修复无限循环。
2. 修复只作用于质检定位的目标段落或章节摘要，不扩大到整份报告。
3. 修复 prompt 仍禁止编造价格、销量、认证、尺寸、排名、真实评论和平台趋势；证据不足处必须保守表达。
4. 如果质检 LLM fallback、质检通过、或无法定位问题段落，Writer 不会额外调用修复 LLM，保证无 Key 和限流场景仍可降级完成。
5. 该闭环不改变 LangGraph DAG、QA Agent 规则、评分公式或 Artifact Schema，只增强 Writer 生成报告后的表达质量控制。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_word_report_service.py backend\tests\test_reports_api.py`：通过，23 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\agents\writer.py backend\tests\test_writer_agent.py`：通过。

## 2026-06-05：Writer 章节级 LLM 生成

本次把 Writer 的报告短段落生成从一个统一 prompt 拆成章节级 LLM 调用。此前 Writer 会把多个报告章节一次性交给 `writer_report_paragraph_generation`，容易让模型输出泛泛而谈的通用话术。现在 Writer 按章节责任分别调用不同 schema：总体判断只输出核心结论，核心竞品只解释为什么是竞品，竞争切片只解释用户在哪些场景会比较，行动建议只输出可执行动作。

### 文件作用更新

1. `backend/app/agents/writer.py`：新增 `SectionLLMConfig` 和 `_section_llm_configs()`，集中定义章节组、schema 名、章节范围、写作目标、规则和最大 item 数。
2. `backend/app/agents/writer.py`：`_rewrite_report_summaries_with_llm()` 现在按章节组循环调用 LLM，schema 分别为 `writer_report_conclusion_generation`、`writer_report_core_competitor_generation`、`writer_report_competitive_slice_generation` 和 `writer_report_action_recommendation_generation`。
3. `backend/app/agents/writer.py`：`_writer_llm_system_prompt()` 和 `_writer_llm_user_prompt()` 改为接收章节配置，只把当前章节需要的 section、edge、evidence、产品、用户洞察和 knowledge artifact 放进 prompt，减少无关结构化 item 对模型输出的干扰。
4. `backend/app/agents/writer.py`：新增 `_sections_for_config()`、`_planned_edge_ids_from_sections()` 和 `_llm_rewrite_batch_metadata()`，用于章节筛选、上下文裁剪和多次 LLM 调用的 metadata 汇总。
5. `backend/tests/test_writer_agent.py`：更新 LLM Writer 测试，锁定新调用顺序为“洞察抽取 + 4 个章节生成 + 分析扩增 + 质检”，并验证质检失败后仍只额外触发一次定向修复。

### 设计边界

1. 章节级 LLM 只改变报告语言组织方式，不改变 ReportData Schema、评分公式、Claim/Evidence/Edge 绑定、QA 规则或 LangGraph DAG。
2. 每个章节 prompt 仍禁止编造价格、销量、认证、尺寸、排名、真实评论和平台趋势；证据不足时必须保守表达。
3. 无 Key、429、超时或非 JSON 输出时，每个章节都可以独立 fallback，Writer 仍保留本地规则报告和后续扩增、质检链路。
4. Token usage logs 现在会按章节记录 `llm_paragraph_<section_group>`，metadata 中的 `llm_rewrite` 会汇总总 token、章节数量、成功章节数、fallback 章节数和每个 schema 的调用状态。
5. 后续如果要继续提升质量，应优先改各章节 prompt/schema 和报告 planner，而不是重新扩大单次 Writer prompt。

### 验证记录

1. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend\tests\test_writer_agent.py backend\tests\test_word_report_service.py backend\tests\test_reports_api.py`：通过，23 个测试通过。
2. `C:\Users\liuchang_c\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m ruff check backend\app\agents\writer.py backend\tests\test_writer_agent.py`：通过。
