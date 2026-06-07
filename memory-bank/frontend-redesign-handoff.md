# 前端设计交接文档

本文档用于交接当前前端设计与实现状态。内容基于当前 `frontend/src` 与 `frontend/e2e` 代码盘点，不作为逐次修改日志；接手时优先用它理解页面形态、代码组织、数据流、响应式护栏和不可破坏的业务契约。

## 1. 当前实现状态

前端已经覆盖比赛 MVP 的完整工作台链路：

1. 任务输入页：创建自动猫砂盆竞品分析任务，支持 `demo_snapshot` 默认模式和 `snapshot_plus_live` 占位模式，成功后进入竞争态势总览。
2. 竞争态势总览页：展示一句话判断、决策可用状态、分析范围、关键竞品、机会风险、首要行动和切片入口。
3. 产品与竞品画像页：展示目标产品、最高威胁直接竞品和最高威胁替代竞品的结构化矩阵对比，并提供受控 Human Review Drawer。
4. 竞争图谱页：展示 React Flow 竞争关系图、左侧关键关系大纲、图谱顶部动态切片工具条、关系数量开关、新手引导和右侧边关系深研 Drawer。
5. 分析报告页：以白皮书式页面展示 2.0 八章节报告，支持显式重新生成、Word `.docx` 下载、浏览器打印和打印视图。
6. 证据与过程追踪页：展示任务状态、证据链、智能体过程、质检记录、Diff、DAG、工具调用、Token 和 Prompt 摘要。

整体形态是工作台应用，不是营销页面。左侧 `AppShell` 负责主导航和任务上下文保留；各页面负责消费后端 Artifact，不在前端临时拼接事实结论。

## 2. 技术栈与边界

当前前端技术栈来自 `frontend/package.json`：

1. React + TypeScript + Vite。
2. Ant Design 作为主要 UI 组件库。
3. TanStack Query 负责服务端状态、缓存和轮询。
4. React Flow 负责竞争图谱和 Trace DAG。
5. `react-router-dom` 提供路由能力；当前源码从 `react-router` 导入运行时 API。
6. `lucide-react` 提供轻量图标。
7. Vitest + Testing Library 负责组件和状态测试。
8. Playwright 负责关键页面视觉、响应式和端到端 Demo 验证。

必须保持的边界：

1. 不引入 Next.js、Redux、Tailwind、Celery、Redis、PostgreSQL、微服务或复杂实时采集架构。
2. 不改后端 API 契约，除非同步更新后端 schema、OpenAPI 类型、服务实现和测试。
3. 不弱化 LangGraph DAG、Collection/Analysis/QA/Writer 四 Agent、Evidence/Claim 绑定、QA 打回、Trace 展示、Human Review 和 Word 导出能力。
4. `snapshot_plus_live` 在 MVP 中仍只是增强模式占位，不做真实外部采集。
5. 找不到可靠证据时继续显示“暂无可靠数据”或保守表达，不能补造价格、销量、认证、尺寸、排名。
6. 不在前端、文档、截图、Trace 或导出报告中暴露 API Key、Token、手机号、账号、地址等敏感信息。

## 3. 应用结构

当前入口和应用壳：

```text
frontend/src/main.tsx
frontend/src/App.tsx
frontend/src/app/AppProviders.tsx
frontend/src/app/AppShell.tsx
frontend/src/app/queryClient.ts
frontend/src/app/routes.tsx
frontend/src/App.css
```

页面：

```text
frontend/src/pages/TaskInputPage.tsx
frontend/src/pages/OverviewPage.tsx
frontend/src/pages/ProfilePage.tsx
frontend/src/pages/BattlefieldPage.tsx
frontend/src/pages/ReportPage.tsx
frontend/src/pages/TracePage.tsx
```

数据与状态：

```text
frontend/src/api/client.ts
frontend/src/api/state.ts
frontend/src/api/RequestStateMessage.tsx
frontend/src/api/schema.ts
frontend/src/hooks/useOverview.ts
frontend/src/hooks/useBattlefield.ts
frontend/src/hooks/useReport.ts
frontend/src/hooks/useTrace.ts
```

共享展示能力：

```text
frontend/src/components/EvidenceCard.tsx
frontend/src/components/MetricHint.tsx
frontend/src/components/PageLoadingState.tsx
frontend/src/components/RiskFlagList.tsx
frontend/src/components/StatusBadge.tsx
frontend/src/components/TermHint.tsx
frontend/src/domain/labels.ts
frontend/src/domain/metricExplanations.ts
frontend/src/domain/termExplanations.ts
frontend/src/utils/format.ts
frontend/src/utils/sanitize.ts
```

开发 fixture：

```text
frontend/src/mocks/
frontend/src/types/
```

`frontend/src/mocks/development.ts` 明确标记这些数据仅用于前端开发和测试，`final_demo_data: false`，不得当作最终演示数据。

## 4. 页面交接

### 4.1 任务输入页

路径：`/`

主要实现：

1. `TaskInputPage` 使用 Ant Design Form 创建任务。
2. 默认表单值为智能宠物硬件、自动猫砂盆、`demo_snapshot`。
3. `target_product_name`、`category`、`subcategory` 有必填校验。
4. `snapshot_plus_live` 只显示稳定性提示，说明 MVP 会降级使用本地快照。
5. 成功调用 `POST /tasks` 后通过 `navigateTo` 跳转 `/overview?task_id=<task_id>`。
6. 创建失败时复用 `RequestStateMessage` 展示错误码、错误信息和 trace id。

设计状态：

1. 页面是工作台式任务启动表单，左侧输入，右侧展示数据范围、默认目标和运行提示。
2. 不应改成 landing page，也不应在前端引入真实外部采集流程。

### 4.2 竞争态势总览页

路径：`/overview?task_id=<task_id>`

主要实现：

1. `useOverview` 请求 `GET /tasks/{task_id}/overview`，并把价格带、人群、使用场景作为 query key。
2. `useOverviewSliceOptions` 请求 `GET /tasks/{task_id}/battlefield?include_all_relations=true`，用于切片选项。
3. 页面展示核心判断、决策可用状态、分析范围、关键竞品、机会点、风险点和首要行动建议。
4. 切片控件支持价格带、人群、使用场景切换，切换后重新请求 overview。
5. 关键竞品通过 `routePathForTask("/battlefield", taskId, { edge_id })` 下钻到指定竞争边。
6. 后端返回 `OVERVIEW_NOT_READY` 时，页面抑制通用请求提示，只展示稳定等待卡片和“重新检查”按钮，并每 2 秒 refetch。
7. 代码中当前等待文案来自 `OverviewWaitingState` 的“正在生成竞争态势总览...”；`App.test.tsx` 仍锁定过“竞争态势还在生成”这个用户可见语义，后续改文案时要同步测试。

设计状态：

1. 总览是业务判断首屏，目标是让 PM 或评委先看懂“能不能用、先看谁、下一步做什么”。
2. 页面不应成为隐式重新分析入口，只消费后端 overview artifact 或后端明确返回的等待状态。

### 4.3 产品与竞品画像页

路径：`/profile?task_id=<task_id>`

主要实现：

1. 页面直接请求 `GET /tasks/{task_id}/profile`。
2. `ProfileComparisonWorkbench` 消费 `horizontal_comparison`，没有该对象时用目标产品构造保守兜底视图。
3. 横向对比当前是矩阵结构：表头展示目标产品、最高威胁直接竞品、最高威胁替代竞品；每个维度行只展示一次维度名、状态、风险标签和“查看依据”入口。
4. 每个商品单元格只展示当前维度下该商品的差异值；空槽位显示“暂无可靠数据”和缺省竞品文案。
5. “查看依据”通过 `/trace?task_id=...&tab=evidence&evidence_id=...` 形成证据下钻链接。
6. 详细画像区保留基础信息、功能能力树、价格模型、人群画像和证据摘要，证据摘要复用 `EvidenceCard`。
7. Human Review 通过右下角 `FloatButton` 打开 Drawer，只允许 `buildHumanReviewOptions()` 中的结构化画像字段，提交 `POST /tasks/{task_id}/feedback` 后 refetch profile。

设计状态：

1. 当前重点是“维度 x 商品”的横向比较，不在三列里重复同一条状态说明。
2. 响应式规则在 1180px 以下把矩阵转为按维度分组的纵向阅读结构，降低长中文和长 SKU 名挤压风险。
3. Human Review 不提供整份报告自由编辑；扩大范围前必须先有后端版本、审计和局部重算支持。

### 4.4 竞争图谱页

路径：`/battlefield?task_id=<task_id>`

主要实现：

1. `useBattlefield` 请求 `GET /tasks/{task_id}/battlefield`，query key 包含价格带、人群、使用场景和 `includeAllRelations`。
2. `placeholderData` 保留上一帧 battlefield 数据，减少切片切换时的视觉跳动。
3. 左侧 `KeyRelationsCard` 展示后端 `key_relations`，关系卡可点击打开右侧 Drawer。
4. `SliceHud` 位于图谱区域顶部，支持价格带、人群、使用场景切换，以及“展开全部关系”开关。
5. 图谱画布使用 React Flow 展示当前可见节点和边；默认优先展示 `key_relations` 对应边，没有关键关系时回退展示全部 `graph_edges`。
6. 支持 `edge_id` 深链，从总览或报告进入后可自动打开指定竞争边。
7. 新手引导使用 Ant Design `Tour`，右下角 `FloatButton` 触发。
8. “动态切片”标题使用 `.battlefield-modern-hud-title-text` 和 `white-space: nowrap` 保持单行。
9. 右侧 `InsightDrawer` 结构为关系详情卡片 + Tabs + QA 摘要卡片。Tabs 包含“多维评分”“分析结论”“底层证据”“四段解释”。
10. 深研面板已经只保留 Tab 版内容；四段解释、分析结论和证据不再在 Tabs 上方重复展示。

设计状态：

1. 图谱页是分析工作台，不是静态可视化海报。
2. 左侧关系列表负责选择，中央 React Flow 负责关系空间，右侧 Drawer 负责深研。
3. 后续优化应保持三者职责分离，避免把所有解释堆在画布上。

### 4.5 分析报告页

路径：`/report?task_id=<task_id>`

主要实现：

1. `useReport` 请求 `GET /tasks/{task_id}/report`，并使用 `completedReportCache` 与 TanStack Query 无限 stale 缓存，避免刷新或切页隐式重新生成。
2. 后端返回 `REPORT_NOT_READY` 时页面进入报告等待态，每 2 秒 refetch。
3. “重新生成报告”显式调用 `POST /tasks/{task_id}/report/regenerate`，成功后同步更新 `completedReportCache` 和 query cache。
4. “下载 Word 报告”调用 `GET /tasks/{task_id}/report/docx` 并触发浏览器文件下载。
5. “打印或另存 PDF”调用 `window.print()`；“切换打印视图”通过 `body[data-report-view="print"]` 和 `report-print-mode` 隐藏工作台操作层。
6. 报告正文按固定八章节优先展示：结论摘要、竞争格局判断、核心竞品拆解、用户决策链分析、目标产品机会与风险、产品策略建议、证据与质检附录、分析流程与系统能力附录。
7. 报告展示层会用 `sanitizeTraceText` 和字段标签表过滤敏感内容、内部字段和英文技术枚举。
8. 前端不展示 Markdown 导出入口。

设计状态：

1. 报告页是白皮书阅读版式，右侧目录用于长报告定位。
2. 打印视图只适配浏览器打印或另存 PDF，不新增服务端 PDF 能力。
3. 默认查看报告不应触发 Writer/LLM 重跑，只有显式点击重新生成才允许调用 regenerate。

### 4.6 证据与过程追踪页

路径：`/trace?task_id=<task_id>`

主要实现：

1. `useTaskStatus` 请求 `GET /tasks/{task_id}`，当状态为 `created`、`collecting`、`analyzing`、`reviewing`、`writing` 时每 1 秒轮询。
2. `useTrace` 请求 `GET /tasks/{task_id}/trace`，任务运行中跟随轮询，完成后停止。
3. 左侧 `TraceControlPanel` 展示任务状态、轮询状态、流程步骤、结果入口、DAG 节点数、运行记录数、QA 记录数和 Tokens。
4. 右侧 `TraceWorkspace` 使用四个 Tabs：证据链、智能体过程、质检记录、差异记录。默认 Tab 来自 `TraceData.process_view.default_tab`，缺失时兜底到证据链。
5. 证据链按 Claim 组织 Evidence，展示来源类型、访问时间、来源链接、可信度和风险标记。
6. 智能体过程保留 React Flow DAG、Agent Run；工具调用、Token Usage 和 Prompt 摘要放入“技术详情”折叠区。
7. Prompt、错误、Diff 和技术字段通过 `sanitizeTraceText` 与敏感字段判断脱敏展示。
8. Diff before/after 默认不挂载，点击“查看结构化前后值”后再显示。

设计状态：

1. Trace 页服务答辩叙事：证明系统不是黑盒报告生成器。
2. 技术信息默认折叠，首屏优先展示证据链和流程状态。
3. 可以继续降低技术噪音，但不能删掉 DAG、Agent Run、Tool Call、Token、QA 打回和 Diff 能力。

## 5. 共享状态与交互约定

1. `ApiClient` 统一解析 `{ data, error, trace_id }` envelope；错误统一抛出 `ApiClientError`。
2. `FetchApiTransport` 默认连接 `http://127.0.0.1:8000`，本地 Vite 页面会自动用当前 localhost hostname 拼 8000 端口。
3. `MockApiTransport` 与 `frontend/src/mocks` 只用于开发和测试。
4. `createTaskQueryClient()` 默认关闭窗口聚焦 refetch，并设置 `gcTime: 0`；报告页另有自己的长缓存策略。
5. 页面级 loading 优先用 `PageLoadingState`；错误、空态和重试入口优先用 `RequestStateMessage`。
6. 导航统一用 `routePathForTask` 和 `navigateTo`，确保 `task_id` 在工作台页面之间延续。
7. 术语解释用 `TermHint` 和 `domain/termExplanations.ts`，数值口径解释用 `MetricHint` 和 `domain/metricExplanations.ts`。
8. 敏感文本展示前优先经过 `utils/sanitize.ts`。

## 6. 样式状态

当前样式仍主要集中在：

```text
frontend/src/App.css
```

当前已实现的样式护栏：

1. `:root` 维护基础颜色、边框、阴影和背景变量。
2. `AppShell` 左侧导航固定宽度 280px，760px 以下转为顶部/单列布局。
3. 品牌区 `.brand-mark` 已固定尺寸、行高和 flex 行为，用于保持“竞析”logo 不挤压变形。
4. 页面外壳、Ant Design 布局、卡片、Space、Typography 等多处补了 `min-width: 0`。
5. 画像矩阵、图谱大纲、Trace 证据链、长 URL 和报告段落都有断行规则；正文区域优先使用 `overflow-wrap: break-word`，只在少数极长标识或名称处使用 `anywhere`。
6. 图谱页的动态切片工具条是图谱区域顶部网格，不再是覆盖 React Flow 的绝对定位浮层。
7. `.battlefield-modern-hud-title-text` 保证“动态切片”单行显示。
8. 1180px、1100px、860px、760px 等断点覆盖画像矩阵、图谱、Trace、报告和导航的主要响应式形态。
9. `@media print` 与 `report-print-mode` 覆盖报告打印视图。

后续建议：

1. 优先按页面拆分 `App.css`，例如 overview、profile、battlefield、report、trace 分文件。
2. 抽出共用布局 token，例如状态色、卡片层级、间距、边框和表格样式。
3. Ant Design 全局覆盖应继续收窄到页面 class 下，避免跨页副作用。
4. 不建议在 MVP 收尾期大规模引入 CSS-in-JS 或替换组件体系。

## 7. 响应式与可访问性护栏

当前已有的护栏：

1. 主导航使用 `aria-label="主导航"`，当前页面按钮带 `aria-current="page"`。
2. 图谱页关键关系按钮有 `aria-label="查看深研：..."`。
3. 图谱、Trace、报告和总览的关键区域有 `aria-label` 或 role，便于测试和读屏定位。
4. 图谱页、画像页、Trace 页和报告页均有 Playwright 视觉/响应式测试覆盖。
5. E2E 中有横向溢出检查、动态切片单行检查、深研面板去重检查、Prompt 脱敏检查和长 URL 可读性检查。

后续修改时要避免：

1. 把中文标题塞进过窄 fixed/flex 子项，导致逐字竖排。
2. 在大段正文上滥用 `overflow-wrap: anywhere`。
3. 用绝对定位工具条覆盖 React Flow 画布。
4. 把卡片嵌套进另一张卡片里造成视觉层级混乱。
5. 用营销 hero 替代实际工作台入口。

## 8. 当前测试入口

单元和组件测试：

```powershell
cd frontend
node .\node_modules\typescript\bin\tsc --noEmit --pretty false
node .\node_modules\eslint\bin\eslint.js src e2e vite.config.ts eslint.config.js
node .\node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx --testTimeout=30000 --reporter=verbose
node .\node_modules\vitest\vitest.mjs run --configLoader runner --root . src\api src\MetricHint.test.tsx src\TermHint.test.tsx --testTimeout=30000 --reporter=verbose
```

关键 Playwright 入口：

```powershell
cd frontend
npm run test:e2e -- e2e/overview.visual.spec.ts --reporter=line
npm run test:e2e -- e2e/profile.visual.spec.ts --reporter=line
npm run test:e2e -- e2e/battlefield.visual.spec.ts --reporter=line
npm run test:e2e -- e2e/report.visual.spec.ts --reporter=line
npm run test:e2e -- e2e/trace.visual.spec.ts --reporter=line
npm run test:e2e -- e2e/responsive.visual.spec.ts --reporter=line
npm run test:e2e -- e2e/demo-path.e2e.spec.ts --reporter=line
npm run test:e2e -- e2e/task-flow.e2e.spec.ts --reporter=line
npm run test:e2e -- e2e/qa-revision.e2e.spec.ts --reporter=line
```

环境备注：

1. 当前 Windows 环境下 Vite、Vitest、Playwright 和生产构建可能启动较慢，长测试建议单独运行。
2. Playwright 生产构建可能提示 chunk 过大，这是既有状态，不是页面功能阻塞。
3. Ant Design v6 相关弃用提示仍可能出现，后续可集中迁移。
4. in-app browser 对 localhost 偶发 `net::ERR_BLOCKED_BY_CLIENT` 时，以 Playwright 结果作为更可靠的视觉验证依据。

## 9. 最新修改记录 / 2026-06-07 Profile 对比矩阵去重优化

本次修改只涉及前端展示层和前端交接文档，不改变后端 API、OpenAPI 类型、Agent DAG、Evidence/Claim 绑定、QA 打回逻辑或数据快照。

修改内容：

1. `frontend/src/pages/ProfilePage.tsx`：将“目标产品与核心竞品对比”从三列重复卡片改为矩阵结构。商品信息集中在表头展示，维度名称、状态、风险标签和“查看依据”入口每行只展示一次；右侧单元格只保留各商品在该维度下的差异值。
2. `frontend/src/App.css`：新增 `.profile-comparison-matrix`、`.profile-comparison-product-header`、`.profile-comparison-dimension-cell`、`.profile-comparison-value-cell` 等样式，并在 1180px 以下切换为按维度分组的纵向阅读布局。
3. `frontend/src/App.test.tsx`：为画像页增加去重断言，锁定同一状态说明“价格低于核心竞品，形成进入门槛优势。”只渲染一次。
4. 已移除前序实现中的临时预览脚本 `frontend/.profile-matrix-preview.cjs`。

验证记录：

1. `node .\node_modules\typescript\bin\tsc --noEmit --pretty false`：通过。
2. `node .\node_modules\eslint\bin\eslint.js src\pages\ProfilePage.tsx --no-warn-ignored` 与 `node .\node_modules\eslint\bin\eslint.js src\App.test.tsx --no-warn-ignored`：拆分执行通过；合并执行在当前 Windows 环境下曾因启动/扫描较慢触发 120 秒超时。
3. `node .\node_modules\vite\bin\vite.js build --configLoader runner --outDir .vite-build-check-profile-matrix --emptyOutDir false`：通过，产物位于 `frontend/.vite-build-check-profile-matrix/`。
4. `node .\node_modules\vitest\vitest.mjs run --configLoader runner --root . src\App.test.tsx --testTimeout=30000 --reporter=dot`：在当前 Windows 环境中启动后只输出 `RUN v4.1.7 D:/pythonproject/zijieagent/frontend` 并超时，和前序记录的 Vitest 启动卡住现象一致。
5. in-app Browser/本地预览核查未完成：前序尝试受 webview attach timeout 阻塞；本次再次尝试时，默认 Vite dev server 触发 `node_modules/.vite-temp` 写入权限问题，隔离端口预览服务未稳定保持可访问。因此本次以 TypeScript、ESLint、Vite build 和静态去重断言作为主要可运行性验证。

### 2026-06-07 顶部标题块填满修正

本次继续根据用户反馈修正页面顶部标题块：上一版为了连接侧栏使用了负向白色延伸，视觉上既没有填满顶部，又容易像遮到侧边栏。本次只改样式，不修改任何页面文字、接口、路由或业务结构。

改动内容：

1. `frontend/src/App.css`：`workspace-content` 恢复正常四边内边距，主内容不再向左做负向连接。
2. `frontend/src/App.css`：`page-surface` 取消最大宽限制，让页面标题块和内容区在主内容区域内横向填满。
3. `frontend/src/App.css`：`page-intro` 保持纯白背景和圆角边框，删除负向 `::before` 延伸，确保不会覆盖或侵入侧边栏。
4. `frontend/src/App.css`：移动端不再需要额外隐藏伪元素，只保留收敛后的标题块 padding。

验证结果：

1. `git diff --check -- frontend/src/App.css`：通过，仅有工作区 LF/CRLF 提示。
2. `node .\node_modules\typescript\bin\tsc --noEmit --pretty false`：通过。
3. `node .\node_modules\vite\bin\vite.js build --configLoader runner --outDir .vite-build-check-intro-fill --emptyOutDir false`：通过，保留既有大 chunk warning。

### 2026-06-07 页面级空态宽度对齐

本次根据用户反馈修复总览页顶部标题块与下方空状态卡宽度不一致的问题。根因是 Ant Design `Empty` 组件默认带横向 margin，导致 `overview-empty-state` 视觉上比 `page-intro` 缩进。

改动内容：

1. `frontend/src/App.css`：为 `empty-task-state`、`overview-empty-state`、`profile-loading-state`、`trace-modern-loading`、`battlefield-modern-loading` 统一设置 `margin: 0` 和 `width: 100%`。
2. `frontend/src/App.css`：为统一页面级加载态 `page-loading-state` 同步设置 `margin: 0` 和 `width: 100%`，避免 loading 态出现同类宽度偏差。

验证结果：

1. `git diff --check -- frontend/src/App.css`：通过，仅有工作区 LF/CRLF 提示。
2. `node .\node_modules\typescript\bin\tsc --noEmit --pretty false`：通过。
3. `node .\node_modules\vite\bin\vite.js build --configLoader runner --outDir .vite-build-check-empty-width --emptyOutDir false`：通过，保留既有大 chunk warning。

### 2026-06-07 页面级无任务空态统一

本次根据用户反馈将其它页面的“暂无可恢复/暂无可分析任务”卡片统一为总览页同款 Ant Design `Empty` 空态。处理范围只包含前端展示和本文档；不改接口、路由、任务状态或业务数据结构。

改动内容：

1. `frontend/src/components/PageEmptyState.tsx`：新增统一页面级空态组件，默认文案为“暂无可恢复的分析任务。请先从任务输入页创建任务。”。
2. `frontend/src/pages/OverviewPage.tsx`：总览页无任务状态改用 `PageEmptyState`，作为统一样式来源。
3. `frontend/src/pages/ProfilePage.tsx`：画像页无任务状态改用 `PageEmptyState`，移除旧的纯文本空态，并去掉“查看产品画像”尾巴文案。
4. `frontend/src/pages/BattlefieldPage.tsx`、`frontend/src/pages/ReportPage.tsx`、`frontend/src/pages/TracePage.tsx`：无任务状态统一改用 `PageEmptyState`。
5. `frontend/src/App.css`：页面级空态样式只保留 `.page-empty-state`，清理旧 `.empty-task-state` / `.overview-empty-state` 依赖。

验证结果：

1. `node .\node_modules\typescript\bin\tsc --noEmit --pretty false`：通过。
2. `node .\node_modules\eslint\bin\eslint.js src\components\PageEmptyState.tsx src\pages\OverviewPage.tsx src\pages\ProfilePage.tsx src\pages\BattlefieldPage.tsx src\pages\ReportPage.tsx src\pages\TracePage.tsx`：通过。
3. `node .\node_modules\vite\bin\vite.js build --configLoader runner --outDir .vite-build-check-empty-state-unified --emptyOutDir false`：通过。

## 10. 已知技术债

1. `frontend/src/App.css` 仍然过大，需要按页面拆分。
2. 页面文件内局部组件偏多，尤其 `BattlefieldPage.tsx`、`ReportPage.tsx`、`TracePage.tsx`，后续可继续拆到 `components/` 或页面专属目录。
3. `App.test.tsx` 覆盖面很广，许多测试通过完整路由渲染，后续可逐步拆为页面级测试。
4. `TracePage` 当前没有实际读取 URL 中的 `tab` 和 `evidence_id` 参数；其它页面已经生成这些深链，后续可补齐定位/高亮能力。
5. `TermHint.tsx`、`termExplanations.ts` 等根路径文件目前是兼容导出，真正实现已迁移到 `components/` 和 `domain/`。
6. Ant Design 部分 API 弃用提示仍待迁移。
7. React Flow 与报告页相关 chunk 较大，后续可考虑路由级懒加载，但不要为了体积引入新框架。

## 11. 后续优先级建议

优先级从高到低：

1. 保持六个页面的业务能力、证据下钻和任务上下文稳定。
2. 继续压实响应式布局，尤其 1280-1440 桌面宽度、390px 移动宽度和浏览器缩放场景。
3. 补齐 Trace 对 `tab`、`evidence_id` 等深链参数的读取和定位。
4. 拆分 `App.css` 和页面大组件，降低后续改动风险。
5. 清理 Ant Design 弃用 API。
6. 增强视觉一致性：状态色、标题层级、卡片间距、按钮形态、Tabs 和 Drawer 体验。
7. 做路由级懒加载或代码分割，降低构建 chunk 警告。

## 12. 接手者注意事项

1. 每次改代码前仍需按项目规则阅读 `memory-bank/architecture.md` 和 `memory-bank/design-document.md`。
2. 前端可以继续美化，但不能弱化证据链、QA 打回、Trace 和报告导出。
3. 不要把模拟数据当最终演示数据；前端测试 fixture 可以存在，正式演示应使用用户提供的脱敏 SKU 快照。
4. 如果要改 API 字段，必须同步后端 schema、OpenAPI 类型、服务实现和测试。
5. 如果页面出现“一个字一行”，优先检查容器宽度、grid/flex 子项 `min-width`、Ant Design 外壳 class 和 `overflow-wrap:anywhere`。
6. 如果等待态闪烁，优先检查 TanStack Query 的 `isFetching`、`data`、`error` 中间态，以及是否仍挂载了通用 `RequestStateMessage`。
