# 竞品分析与竞争关系重建多 Agent 协作系统技术栈推荐

## 1. 结论

推荐使用一套简单但健壮的 MVP 技术栈：

```text
Backend:  Python 3.12 + FastAPI + LangGraph + Pydantic v2 + SQLite + SQLAlchemy
Frontend: React + TypeScript + Vite + Ant Design + TanStack Query + React Flow
Model:    Doubao-Seed-2.0-lite via OpenAI-compatible client, optional enhancement
Dev:      uv + Ruff + Pytest + npm + ESLint + Prettier + Vitest
```

这套组合的原则是：少依赖、少服务、强类型、结构化、可演示、可追踪。MVP 阶段不引入 Celery、Redis、PostgreSQL、Next.js、微服务或复杂实时采集平台，避免 20 天开发周期被基础设施消耗。

路径约定：本文档位于 `memory-bank/`；文中 `backend/`、`frontend/`、`data/`、`docs/`、`demo/` 等路径均相对于项目根目录。

## 2. 推荐技术栈总表

| 层级 | 推荐选择 | 用途 | 选择理由 |
|---|---|---|---|
| Python 运行时 | Python 3.12 | 后端与 Agent 运行环境 | 兼容性稳，AI/数据依赖支持广，适合比赛环境 |
| JS 运行时 | Node.js 24 LTS | 前端开发与构建 | 当前 LTS，适配新版 Vite |
| 后端框架 | FastAPI | REST API、任务接口、报告导出 | 类型友好、自动 OpenAPI、适合 Pydantic Schema |
| Agent 编排 | LangGraph | Collection/Analysis/QA/Writer DAG | 支持状态图、条件边、human-in-the-loop、持久化思路 |
| Schema 校验 | Pydantic v2 | AgentMessage、Artifact、Claim、Evidence | 统一 Python 类型、JSON 校验、OpenAPI Schema |
| 数据库 | SQLite | 任务、Artifact、Trace、反馈记录 | 零部署，适合本地 Demo 和单任务 MVP |
| ORM | SQLAlchemy 2.0 | 数据访问层 | 成熟稳定，后续可迁移 PostgreSQL |
| 快照存储 | 本地 JSON + 文件目录 | SKU 快照、评论快照、截图、Markdown | 简单透明，便于演示和答辩排查 |
| 前端框架 | React + TypeScript | 5 个产品页面 | 生态成熟，适合数据密集型应用 |
| 构建工具 | Vite | 前端开发、构建、代理 | 启动快、配置轻、支持 React TS 模板 |
| UI 组件 | Ant Design | 表单、表格、Tabs、Drawer、Timeline、Tag | 适合运营/分析类后台工具，少造轮子 |
| 图可视化 | React Flow (`@xyflow/react`) | 竞争关系图、Agent DAG | 节点边模型贴合本项目 |
| 服务端状态 | TanStack Query | API 请求、轮询任务状态和 Trace | 缓存、错误态、轮询能力成熟 |
| 图标 | lucide-react | 按钮和工具类图标 | 轻量、语义清楚 |
| Markdown 生成 | Jinja2 模板 | 后端 Markdown 报告导出 | 模板稳定，可控性强 |
| 后端测试 | Pytest + httpx | API、Agent 节点、QA 规则测试 | 简单可靠 |
| 前端测试 | Vitest + Testing Library | 组件和数据映射测试 | 与 Vite 配套 |
| E2E 验证 | Playwright | 关键页面截图和演示链路检查 | 保证答辩前页面可用 |
| 代码质量 | Ruff + ESLint + Prettier | 格式化、lint、基础质量门禁 | 维护成本低 |

## 3. 后端技术栈

### 3.1 FastAPI

FastAPI 负责所有后端 HTTP 接口：

1. `POST /tasks`
2. `GET /tasks/{task_id}`
3. `GET /tasks/{task_id}/profile`
4. `GET /tasks/{task_id}/battlefield`
5. `GET /tasks/{task_id}/trace`
6. `GET /tasks/{task_id}/report`
7. `GET /tasks/{task_id}/report/markdown`
8. `POST /tasks/{task_id}/feedback`

推荐原因：

1. 与 Pydantic 天然契合，适合大量结构化 Schema。
2. 自动生成 OpenAPI，前端可以据此生成 TypeScript 类型。
3. 对异步模型调用、文件下载、后台任务都足够友好。
4. 团队学习成本低，适合 20 天比赛开发。

### 3.2 LangGraph

LangGraph 用来实现真实 Agent DAG，而不是伪装的顺序函数调用。

推荐节点：

```text
orchestrator
  -> collection_agent
  -> analysis_agent
  -> qa_agent
  -> writer_agent
```

推荐条件边：

```text
qa_agent -> writer_agent      when qa_status == "passed"
qa_agent -> collection_agent  when revision_target == "collection"
qa_agent -> analysis_agent    when revision_target == "analysis"
```

推荐状态对象：

```text
TaskGraphState
  task
  products
  evidences
  claims
  competition_edges
  review_tasks
  human_feedback
  agent_messages
  run_logs
```

实现建议：

1. LangGraph State 用 `TypedDict` 或 dataclass，避免每一步都做重型 Pydantic 校验。
2. Agent 输入输出用 Pydantic 校验，保证 Artifact 可靠。
3. 每个节点函数只做一件事，方便 Trace 和测试。
4. QA 打回必须通过条件边回到 Collection 或 Analysis。

### 3.3 Pydantic v2

Pydantic 用于定义核心协议和数据结构：

1. `AnalysisTask`
2. `AgentMessage`
3. `Product`
4. `FeatureTree`
5. `PricingModel`
6. `UserPersona`
7. `Evidence`
8. `Claim`
9. `CompetitionEdge`
10. `ReviewTask`
11. `HumanFeedback`
12. `AgentRunLog`
13. `ToolCallLog`
14. `TokenUsageLog`

约定：

1. 所有 Agent 输出先进入 Pydantic 校验。
2. 校验失败时记录 `ReviewTask` 或 `AgentRunLog.error`。
3. Schema 字段命名统一使用 `snake_case`。
4. 对前端输出时保持 JSON 字段稳定，不随意改名。

### 3.4 SQLite + SQLAlchemy

MVP 使用 SQLite，不上 PostgreSQL。

SQLite 保存：

1. 任务状态
2. Product / Evidence / Claim / CompetitionEdge 等 Artifact JSON
3. ReviewTask / HumanFeedback
4. AgentRunLog / ToolCallLog / TokenUsageLog
5. Markdown 报告元信息

本地文件保存：

1. SKU 快照 JSON
2. 评论快照 JSON
3. 截图
4. 导出的 Markdown 文件

推荐原因：

1. 零部署，评审现场更稳。
2. 数据量只有 8 到 12 个 SKU，SQLite 足够。
3. SQLAlchemy 让后续迁移 PostgreSQL 的成本较低。

约束：

1. MVP 后端使用单进程单 worker。
2. 不做多任务大并发。
3. 长任务状态必须落库，避免页面刷新后 Trace 丢失。

### 3.5 任务执行方式

MVP 推荐使用 FastAPI 进程内后台任务，而不是 Celery/Redis。

推荐流程：

```text
POST /tasks
  -> 写入 task.created
  -> 启动 in-process background task
  -> 返回 task_id

Frontend
  -> 每 1-2 秒轮询 /tasks/{id} 和 /tasks/{id}/trace
```

不推荐 MVP 使用 WebSocket 或 SSE。轮询更简单，足够满足 Agent Trace 展示。

### 3.6 模型调用

推荐使用 OpenAI-compatible client 封装 Doubao-Seed-2.0-lite。模型调用是可选增强；未配置模型 API Key 时，系统必须仍能依靠本地快照和规则流程跑通完整 Demo。

建议封装：

```text
<project-root>/backend/app/services/llm_client.py
```

配置只来自环境变量：

```text
DOUBAO_API_KEY=
DOUBAO_BASE_URL=
DOUBAO_MODEL=Doubao-Seed-2.0-lite
```

约定：

1. API Key 不入库、不进日志、不进 Trace。
2. 所有模型调用记录 Token、耗时、Agent 名称、输出校验状态。
3. 模型返回非 JSON 时最多重试一次。
4. 重试失败后输出兜底结构，并让 QA 标记风险。

## 4. 前端技术栈

### 4.1 React + TypeScript + Vite

前端使用 Vite React TypeScript 项目。

推荐原因：

1. 页面都是客户端交互，没有 SSR 必要。
2. Vite 启动快，适合频繁调 Demo UI。
3. TypeScript 可以约束 API 数据结构。

不推荐 Next.js：

1. 本项目没有 SEO、SSR、复杂路由和服务端组件需求。
2. Next.js 会增加部署和调试复杂度。
3. 比赛 MVP 更需要快速稳定的单页应用。

### 4.2 Ant Design

Ant Design 用于主要 UI：

1. 表单：输入页、Human Review
2. 表格：竞品集合、Evidence 列表、Trace 列表
3. Tabs：报告页、Trace 页分区
4. Drawer/Modal：证据详情、Claim 详情、人工修正
5. Timeline/Steps：决策链和 QA 打回过程
6. Tag/Badge：风险、置信度、状态

样式建议：

1. 使用 Ant Design Token 做主题，不额外引入 Tailwind。
2. 使用 CSS Modules 写少量页面布局样式。
3. 页面以数据密集型工作台为主，不做营销页。

### 4.3 React Flow

React Flow 用于两个核心图：

1. 竞争图谱页的竞争关系图。
2. Agent Trace 页的 LangGraph DAG 图。

推荐原因：

1. 节点、边、布局、交互模型与项目天然匹配。
2. 前端只需要渲染后端给出的 `nodes` 和 `edges`。
3. 可自定义节点卡片，展示产品名、分数、风险状态。

暂不引入 AntV G6：

1. G6 能力更强，但学习和调试成本更高。
2. MVP 图规模很小，React Flow 足够。

暂不引入 ECharts：

1. 评分解释可以用 Ant Design Progress、Descriptions 和自定义条形组件实现。
2. 如果后续要做趋势图、雷达图，再补 ECharts。

### 4.4 TanStack Query

TanStack Query 管理所有服务端状态：

1. 任务状态
2. 产品画像
3. 竞争图谱数据
4. Trace 数据
5. 报告数据
6. 人工修正 mutation

推荐用法：

```text
useQuery(["task", taskId], fetchTask, { refetchInterval: 2000 })
useQuery(["trace", taskId], fetchTrace, { refetchInterval: taskRunning ? 2000 : false })
useMutation(submitHumanFeedback)
```

不推荐 Redux/Zustand：

1. MVP 主要是服务端状态，不是复杂客户端状态。
2. React 本地 state + URL 参数 + TanStack Query 足够。

### 4.5 前端类型生成

推荐从 FastAPI OpenAPI 生成 TypeScript 类型：

```text
npx openapi-typescript http://localhost:8000/openapi.json -o frontend/src/api/schema.ts
```

收益：

1. 前后端字段一致。
2. 减少手写类型漂移。
3. 接口变更更容易发现。

## 5. 项目目录建议

```text
backend/
  app/
    main.py
    api/
      routes_tasks.py
      routes_reports.py
    agents/
      collection.py
      analysis.py
      qa.py
      writer.py
    graph/
      state.py
      workflow.py
    schemas/
      task.py
      agent_message.py
      product.py
      evidence.py
      claim.py
      competition.py
      trace.py
    services/
      llm_client.py
      snapshot_loader.py
      markdown_renderer.py
      scoring.py
      qa_rules.py
    storage/
      db.py
      repositories.py
    tests/
frontend/
  src/
    api/
      client.ts
      schema.ts
    components/
      battlefield/
      trace/
      report/
    pages/
      InputPage.tsx
      ProductProfilePage.tsx
      BattlefieldPage.tsx
      ReportPage.tsx
      TracePage.tsx
    types/
    App.tsx
data/
  snapshots/
  screenshots/
  mock_task.json
  mock_trace.json
docs/
demo/
memory-bank/
  design-document.md
  tech-stack.md
  implementation-plan.md
  progress.md
  architecture.md
```

## 6. 最小依赖清单

### 6.1 后端依赖

```text
fastapi[standard]
langgraph
pydantic
pydantic-settings
sqlalchemy
aiosqlite
openai
jinja2
python-dotenv
pytest
pytest-asyncio
httpx
ruff
```

说明：

1. `openai` 只作为 OpenAI-compatible client，不绑定 OpenAI 模型。
2. `aiosqlite` 用于异步 SQLite 访问。
3. `jinja2` 用于 Markdown 模板渲染。
4. 暂不引入 LangChain 全家桶，只在确实需要模型/工具封装时补。

### 6.2 前端依赖

```text
react
react-dom
typescript
vite
antd
@tanstack/react-query
@xyflow/react
react-router-dom
lucide-react
openapi-typescript
vitest
@testing-library/react
@testing-library/jest-dom
playwright
eslint
prettier
```

说明：

1. 暂不引入 Redux/Zustand。
2. 暂不引入 ECharts。
3. 暂不引入 Tailwind。
4. 暂不引入 Next.js。

## 7. 开发脚本建议

### 7.1 后端

```text
uv venv
uv pip install -r requirements-dev.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
ruff check .
ruff format .
pytest
```

### 7.2 前端

```text
npm create vite@latest frontend -- --template react-ts
npm install
npm run dev
npm run build
npm run test
npm run lint
```

### 7.3 类型同步

```text
npx openapi-typescript http://127.0.0.1:8000/openapi.json -o frontend/src/api/schema.ts
```

## 8. 架构取舍

### 8.1 为什么不上 PostgreSQL

MVP 数据量小，现场演示更需要零部署和可控性。SQLite 足够保存任务、Trace、Artifact 和反馈记录。后续多任务并发、团队协作、云部署时再迁移 PostgreSQL。

### 8.2 为什么不上 Celery/Redis

当前只要求单任务演示和真实 QA 打回，不要求大规模并发。Celery/Redis 会增加部署、监控和故障排查成本。MVP 用进程内后台任务加轮询即可。

### 8.3 为什么不上 Next.js

本系统是内部分析工作台，不需要 SEO 和 SSR。Vite 单页应用更轻，和 FastAPI 后端分离也更清晰。

### 8.4 为什么选 React Flow 而不是 AntV G6

本项目核心图是小规模 DAG 和竞争关系网络，React Flow 的节点边交互模型刚好匹配。AntV G6 更适合复杂图分析，但 MVP 会增加学习和调试成本。

### 8.5 为什么先不用 ECharts

评分解释可以通过条形进度、表格和说明面板表达。先不引入 ECharts 可以减少视觉和数据适配成本。后续如果要展示趋势、雷达、漏斗，再补充 ECharts。

## 9. 关键工程约定

### 9.1 API 约定

1. 所有接口返回统一结构：

```json
{
  "data": {},
  "error": null,
  "trace_id": "trace_xxx"
}
```

2. 错误返回：

```json
{
  "data": null,
  "error": {
    "code": "QA_REVISION_REQUIRED",
    "message": "价格证据缺少访问时间",
    "details": {}
  },
  "trace_id": "trace_xxx"
}
```

### 9.2 Agent 输出约定

1. Agent 输出必须是结构化 JSON。
2. Agent 输出必须经过 Pydantic 校验。
3. 核心 Claim 必须绑定 `evidence_ids`。
4. 推断结论必须设置 `is_inference=true`。
5. 找不到可靠数据时写“暂无可靠数据”。

### 9.3 Trace 约定

Trace 至少记录：

1. Agent 名称
2. 节点状态
3. 输入摘要
4. 输出摘要
5. 工具调用
6. Token 消耗
7. 错误信息
8. QA 打回记录
9. 打回前后差异

Prompt 展示前必须脱敏。

### 9.4 前端轮询约定

1. 任务运行中每 2 秒刷新任务状态和 Trace。
2. 任务完成后停止轮询。
3. 失败节点保留在 Trace 中，不静默吞掉。
4. 报告页只在任务进入 `completed` 后展示正式结果。

## 10. 推荐版本策略

| 技术 | 推荐版本策略 |
|---|---|
| Python | 固定 `3.12.x` |
| Node.js | 固定 `24.x LTS` |
| FastAPI | 锁定到当前稳定小版本 |
| LangGraph | 锁定到当前稳定小版本，避免比赛期自动升级 |
| React | 使用 Vite 模板生成的稳定版本 |
| Ant Design | 锁定主版本，不在比赛期跨主版本升级 |
| React Flow | 锁定主版本 |
| TanStack Query | 锁定主版本 |

建议提交 lock 文件：

1. 后端提交 `requirements.lock` 或 `uv.lock`。
2. 前端提交 `package-lock.json`。

## 11. 后续扩展路径

| 当前 MVP | 后续可升级 |
|---|---|
| SQLite | PostgreSQL |
| 进程内后台任务 | Celery/RQ/Arq + Redis |
| 轮询 Trace | SSE 或 WebSocket |
| 本地快照 | 定时采集和对象存储 |
| React Flow 小图 | AntV G6 或专业图分析 |
| 手写 API client | OpenAPI 自动生成完整 SDK |
| 本地日志 | OpenTelemetry + LangSmith/自建观测 |

## 12. 官方资料参考

1. [FastAPI 官方文档](https://fastapi.tiangolo.com/)
2. [LangGraph 官方文档](https://docs.langchain.com/oss/python/langgraph/overview)
3. [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
4. [Pydantic JSON Schema 文档](https://docs.pydantic.dev/latest/api/json_schema/)
5. [Python 版本状态](https://devguide.python.org/versions/)
6. [Node.js Releases](https://nodejs.org/en/about/previous-releases)
7. [Vite 官方指南](https://vite.dev/guide/)
8. [Ant Design React 文档](https://ant.design/docs/react/introduce/)
9. [TanStack Query 文档](https://tanstack.com/query/latest/docs/framework/react/guides/queries)
10. [React Flow Quick Start](https://reactflow.dev/learn)
