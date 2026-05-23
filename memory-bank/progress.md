# 项目进度记录

## 当前总览

截至 2026-05-23，实施计划已按顺序完成步骤 01 到步骤 06；步骤 07 尚未开始。

当前边界：

1. 已完成项目骨架、质量工具、统一 API 响应、核心 Schema、SQLite 存储层和最终 Demo 快照规范。
2. `data/raw/` 中的真实脱敏 SKU 原始素材已作为步骤 06 的素材来源保留。
3. `data/snapshots/demo_sku_snapshot.json` 是后续步骤 07 的正式快照输入契约。
4. 尚未实现 Snapshot Loader、Collection Agent、任务 API、Agent DAG、QA 规则服务或报告导出。
5. 未引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
6. 未写入真实 API Key，未在 Trace、日志或文档中记录密钥。

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

## 下一步边界：步骤 07 尚未开始

下一步应进入实施计划步骤 07：实现快照加载服务。

开始步骤 07 前的边界提醒：

1. 只能读取并转换 `data/snapshots/demo_sku_snapshot.json`，不能把 `sku_catalog_draft.json` 当作最终输入。
2. Snapshot Loader 需要输出标准 `Product`、`Evidence` 和后续可扩展的 `ReviewInsight`。
3. 缺失字段必须保留缺失状态或“暂无可靠数据”，不得自动编造。
4. 需要新增非法快照文件的可诊断错误测试。
5. 继续禁止引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind 或其他未批准复杂基础设施。
