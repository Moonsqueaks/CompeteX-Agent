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
