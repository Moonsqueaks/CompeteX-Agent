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
7. Markdown 导出、报告 API、产品画像 API、战场 API、Trace API 和 Human Feedback API 仍未实现。

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
2. 尚未实现竞品战场 API、Trace API 或 Human Feedback API。
3. 尚未把完整 LangGraph workflow 接入 `POST /tasks` 后的后台任务执行链路。

## 2026-05-26：步骤 22 产品画像 API

当前项目已完成实施计划步骤 22，后端具备目标产品画像读取 HTTP API。该步骤只实现产品画像 API，不创建竞品战场 API，不推进步骤 23。

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

1. 产品画像 API 只面向产品画像页，不返回竞品关系图、切片列表、边评分解释或战场筛选数据。
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

## 2026-05-26：步骤 23 竞品战场 API

当前项目已完成实施计划步骤 23，后端具备面向竞品战场页的 HTTP API。该步骤只实现 `GET /tasks/{task_id}/battlefield`，不推进 Trace API，也不改变后台任务执行方式。

### 新增与调整文件职责

1. `backend/app/schemas/battlefield.py`：第 23 步新增的战场响应契约文件。它把前端战场页需要的数据拆成 `BattlefieldData`、`BattlefieldSliceSelection`、`BattlefieldSliceOption`、`BattlefieldGraphNode`、`BattlefieldGraphEdge`、`BattlefieldClaimReference`、`BattlefieldScoreExplanation`、`BattlefieldDecisionChainStage`、`BattlefieldEvidenceCard` 和 `BattlefieldQASummary`，确保图、切片、评分、证据和 QA 状态都有稳定结构。
2. `backend/app/schemas/__init__.py`：新增导出所有 battlefield schema，保证 FastAPI OpenAPI 与后续前端类型同步能发现第 23 步接口契约。
3. `backend/app/services/battlefield_service.py`：第 23 步新增的战场聚合服务。它负责校验任务状态、按切片读取或生成缓存、同步调用现有 LangGraph workflow、把 Product/Claim/Evidence/CompetitionEdge/ReviewTask/AgentMessage 组装成战场视图，并维护 `BATTLEFIELD_ARTIFACT_TYPE` 与 Evidence 卡片摘要长度常量。
4. `backend/app/services/__init__.py`：新增导出 `BattlefieldService`、`BattlefieldServiceError`、`BATTLEFIELD_ARTIFACT_TYPE` 和 `MAX_EVIDENCE_CARD_SUMMARY_CHARS`，与 report/profile service 保持一致的服务入口模式。
5. `backend/app/api/routes_battlefield.py`：第 23 步新增的 FastAPI 路由文件，提供 `GET /tasks/{task_id}/battlefield`，接收 `price_band`、`persona`、`scenario` 三个可选查询参数，负责把 service error 转换成统一 `ApiException`。
6. `backend/app/main.py`：注册 battlefield router，让战场 API 进入应用路由表。
7. `backend/tests/test_battlefield_api.py`：第 23 步新增 API 测试，覆盖默认战场数据、价格带过滤、Claim/Evidence 引用、风险边状态和未完成任务错误。

### BattlefieldService 核心职责

1. `get_battlefield(task_id, price_band, persona, scenario)`：战场 API 的服务入口。它先确认任务存在且状态为 `completed`，再按任务与切片参数生成稳定 `battlefield_id`，优先读取 SQLite `artifact_json` 中缓存的 `battlefield_data`；缓存缺失时同步生成。
2. `_generate_and_cache_battlefield`：同步生成兜底函数。它从已完成任务创建 `TaskGraphState`，运行 `build_analysis_workflow().invoke(...)`，确认 workflow 完成后组装 `BattlefieldData` 并写入 Artifact 缓存。
3. `_build_battlefield_data`：战场视图组装函数。它只消费现有 workflow 结构化产物，不新增无证据事实；默认返回所有竞争边并按 `edge_score` 降序排列，显式传入切片参数时按对应维度过滤。
4. `_graph_edge` 与 `_claim_ref`：把 `CompetitionEdge` 和关联 `Claim` 转成前端可渲染的图边结构，每条边保留 `claim_ids`、`evidence_ids`、`claim_refs`、`score_breakdown` 和 `score_explanations`。
5. `_edge_risk_flags`：聚合边本身风险、Claim 风险、非 accepted Claim 状态和开放 ReviewTask，把问题边标记为 `risk_status = "at_risk"`。
6. `_available_slices`：基于所有 `CompetitionEdge.slice` 生成可选切片列表，每个切片包含边数量和最高边得分。
7. `_decision_chain`：按 `DecisionStage` 汇总边、Claim、Evidence 和平均得分，供前端战场页展示决策链。
8. `_evidence_card`：从边引用的 Evidence 生成卡片，保留来源、截图、访问时间、置信度、摘要、局限和缺失字段风险。
9. `_qa_summary`：汇总 ReviewTask、revision message、风险边和风险 Claim，用于战场页展示 QA 总状态。

### 当前战场 API 数据流

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

1. 竞品战场 API 面向战场页，不返回 Agent Run、Tool Call、Token Usage 或 Diff View；这些留给步骤 24 的 Trace API。
2. 战场 API 复用同步 workflow 生成作为阶段性兜底，后续后台任务落地后可以优先读取已持久化的底层 Artifact 或已缓存 `BattlefieldData`。
3. 缓存粒度包含任务 ID 和切片参数，避免默认战场、价格带战场、人群战场、场景战场互相覆盖。
4. 没有引入新基础设施；仍使用 FastAPI、Pydantic、LangGraph、SQLite 和 SQLAlchemy。

### 当前验证契约

1. 新增 `backend/tests/test_battlefield_api.py`，验证默认战场返回直接竞品和替代/渠道类竞品，且边按分数降序。
2. 验证切换 `price_band` 会改变返回边集合或评分解释，并保证边切片与查询参数一致。
3. 验证每条边包含 `claim_ids`、`evidence_ids` 和 `claim_refs`，Evidence 卡片覆盖边引用的 Evidence。
4. 验证被 QA 或服务标记的问题边带 `at_risk` 状态，并进入 `qa_summary.risk_edge_ids`。
5. 验证未完成任务请求战场数据返回 `BATTLEFIELD_NOT_READY`。
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

1. Trace API 面向 Agent Trace 页，返回 DAG、Agent Run、Tool Call、Token Usage、QA Review 和 Diff View；不返回战场页切片聚合结构，也不承担 Human Feedback 提交。
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
