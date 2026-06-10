# 豆包 AI 助手竞品分析演示脚本

## 冻结输入

- 稳定输入文件：`demo/internet-ai-assistant-stable-input.json`
- 目标产品入口：`https://www.doubao.com/chat/`
- 领域：`互联网产品 / AI 助手`
- 数据模式：`builtin_candidates`
- 候选池：`data/snapshots/internet_ai_assistant_snapshot.json`
- 目标产品：豆包
- 核心竞品：Kimi、DeepSeek、千问、腾讯元宝
- QA 打回样例：Kimi 官方首页证据 `ev_ip_kimi_homepage` 缺失截图路径，由本地 `qa_revision_fixture` 补齐。

## 演示路径

1. 在输入页选择“互联网产品”，子类保持“AI 助手”。
2. 保持目标产品链接为 `https://www.doubao.com/chat/`，数据模式为“内置候选池”。
3. 点击“启动分析任务”，进入 `/overview?task_id=<task_id>`。
4. 在总览页展示豆包与 Kimi、DeepSeek、千问、腾讯元宝的竞争判断，以及证据边界。
5. 进入竞争图谱页，切换或展示“商业模式/付费层、人群、使用场景”三类切片。
6. 打开产品画像页，展示“产品名称、产品入口、商业模式与证据、核心任务能力、创作与多模态能力、隐私安全与企业能力”等 AI 助手语境标签。
7. 打开报告页，展示互联网产品竞品分析章节，确认报告中保留“暂无可靠数据/建议复核”的证据边界，并提供 Word 下载入口。
8. 打开 Trace 页，展示候选池加载 metadata、LangGraph DAG、QA 打回、Kimi 截图修复 Diff、Analysis 重算 Diff。

## 答辩讲法

这条演示强调系统不是搜索引擎，也不是只列竞品清单。用户只输入豆包入口后，系统从受控本地候选池带出 Kimi、DeepSeek、千问和腾讯元宝，再由 Collection、Analysis、QA、Writer 四个 Agent 形成可追溯的竞争关系判断。

需要主动说明的边界：

1. `builtin_candidates` 不调用搜索引擎，不发现候选池之外的新产品。
2. 候选池不等于结论，报告只展示经过 Evidence、Analysis 和 QA 支撑的竞争关系。
3. 定价、下载量、用户规模、模型能力排名、市场份额和隐私安全结论没有可靠证据时，统一写“暂无可靠数据”或“建议复核”。
4. QA 打回不是摆设，Kimi 截图缺失会真实打回 Collection，补齐后 Analysis 重新计算，Trace 展示前后差异。

## 验收口径

1. 同一输入稳定匹配豆包为目标产品。
2. 同一输入稳定带出 Kimi、DeepSeek、千问、腾讯元宝 4 个核心竞品。
3. 同一输入稳定触发 `CRITICAL_EVIDENCE_MISSING_SCREENSHOT`，并最终将该 QA 任务标记为 resolved。
4. 报告稳定使用 AI 助手语境和“商业模式/付费层”切片。
5. Word 导出可用，前端不展示 Markdown 导出按钮。
