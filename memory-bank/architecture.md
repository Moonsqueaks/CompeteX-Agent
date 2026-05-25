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
