# AGENTS.md

## 项目说明

本项目是“竞品分析与竞争关系重建多 Agent 协作系统”的比赛 MVP。系统围绕自动猫砂盆类目，使用用户提供的真实脱敏 SKU 快照，构建 Collection、Analysis、QA、Writer 多 Agent 协作流程，输出可追溯、可打回、可人工修正的竞品分析报告。


## 路径约定

本文档位于项目根目录。`memory-bank/` 内文档提到的路径均相对于项目根目录，例如：

1. `backend/`
2. `frontend/`
3. `data/`
4. `docs/`
5. `demo/`
6. `memory-bank/`

## 技术栈约定

必须优先使用 `memory-bank/tech-stack.md` 推荐的简单稳健技术栈：

1. 后端：Python 3.12、FastAPI、LangGraph、Pydantic v2、SQLite、SQLAlchemy。
2. 前端：React、TypeScript、Vite、Ant Design、TanStack Query、React Flow。
3. 模型：Doubao-Seed-2.0-lite via OpenAI-compatible client，作为可选增强。
4. 测试：Pytest、httpx、Vitest、Testing Library、Playwright。
5. 质量工具：Ruff、ESLint、Prettier。

禁止在 MVP 阶段擅自引入 Celery、Redis、PostgreSQL、Next.js、Redux、Tailwind、复杂实时采集平台或微服务架构。

## 当前确认决策

1. Demo 数据由用户提供真实脱敏 SKU 快照。
2. 开发者可以创建测试 fixture，但不得把模拟数据当作最终演示数据。
3. MVP 目标产品固定；如用户未指定，从用户提供的脱敏 SKU 中选择证据最完整、最适合作为演示主线的产品。
4. 未配置模型 API Key 时，系统也必须依靠本地快照和规则流程跑通完整 Demo。
5. QA 打回案例优先演示“补齐一条缺失证据”，并在 Trace 中展示补齐前后差异。
6. SQLite 使用“任务表 + Artifact JSON + 日志表”的轻量存储方案。
7. 产品运行时使用后台任务和前端轮询；测试中提供同步执行入口。
8. 创建任务后前端默认跳转到 Agent Trace 页。
9. Human Review 提交后立即触发 Analysis 局部重算。
10. `snapshot_plus_live` 在 MVP 中只是增强模式占位，不做真实外部采集。
11. Markdown 报告接口返回 Markdown 内容，并保存到 `<project-root>/data/reports/`。

## 实施规则

开发必须严格按照 `memory-bank/implementation-plan.md` 的步骤推进。

每一步都必须做到：

1. 小步实现，不跨多个责任边界。
2. 明确对应测试。
3. 运行对应测试。
4. 记录测试是否通过。
5. 不跳过 QA 打回、证据链、Trace、Markdown 导出这些 MVP 核心能力。

## 核心功能不可弱化

必须保住以下能力：

1. LangGraph 真实 DAG。
2. Collection、Analysis、QA、Writer 四个主 Agent。
3. 结构化 AgentMessage 和 Artifact。
4. Claim 与 Evidence 绑定。
5. QA Agent 真实打回。
6. 打回后 Collection 或 Analysis 真实重跑。
7. Agent Trace 展示 DAG、Agent Run、Tool Call、Token、QA 打回和 Diff。
8. 竞品战场页支持价格带、人群、使用场景切片切换。
9. 网页报告展示。
10. 后端 Markdown 导出。
11. 有限 Human Review。

## 安全与合规

1. 不得把 API Key 写入代码、文档、日志、Trace、截图或导出报告。
2. `.env` 只用于本地环境变量，不提交真实密钥。
3. 用户提供的问卷、访谈、SKU 数据必须按脱敏数据处理。
4. 报告中对宠物安全、电器认证、医疗美容等敏感表达必须保守。
5. 找不到可靠证据时写“暂无可靠数据”，不得凭记忆补价格、认证、尺寸、销量、排名。
6. 推断内容必须显式标记为推断。

## Git 与文件操作

1. 不要删除或覆盖用户已有文件，除非用户明确要求。
2. 不要回滚用户改动。
3. 手工编辑文件时优先使用补丁方式。
4. 生成的新文档默认使用 Markdown。
5. 项目文档优先放入 `memory-bank/`，除非用户指定其他位置。

## 完成任务前检查

每次完成开发任务前至少检查：

1. 相关测试是否通过。
2. 是否破坏 `memory-bank` 中已有决策。
3. 是否引入了未批准的新技术。
4. 是否泄露敏感信息。
5. 是否保持路径相对于项目根目录。
6. 是否需要同步更新文档。

## 重要提示
1. 写任何代码前必须完整阅读 memory-bank/@architecture.md
2. 写任何代码前必须完整阅读 memory-bank/@design-document.md
3. 每完成一个重大功能或里程碑后，必须更新 memory-bank/@architecture.md
