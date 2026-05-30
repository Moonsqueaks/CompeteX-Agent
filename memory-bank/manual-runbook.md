# 手动启动与测试流程

## 1. 启动后端

打开第一个 PowerShell：

```powershell
cd /d D:\pythonproject\zijieagent\backend
.\.conda312\python.exe -m fastapi dev app\main.py --host 127.0.0.1 --port 8000
```

后端健康检查地址：

```text
http://127.0.0.1:8000/health
```

如果 `fastapi dev` 在本机不可用，可以改用：

```powershell
cd /d D:\pythonproject\zijieagent\backend
.\.conda312\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## 2. 启动前端

打开第二个 PowerShell：

```powershell
cd /d D:\pythonproject\zijieagent\frontend
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

如果 5173 被占用，以终端里 Vite 打印出来的实际地址为准。前端默认会请求：

```text
http://127.0.0.1:8000
```

## 3. 手动测试主流程

1. 打开前端首页 `http://127.0.0.1:5173`。
2. 保持默认 Demo 输入，数据模式选择 `demo_snapshot`。
3. 点击创建/启动任务按钮。
4. 创建成功后，页面应跳转到 `/overview?task_id=<task_id>`。
5. 在“竞争态势总览”页检查：
   - 一句话判断是否出现。
   - 关键竞品、首要行动、机会与风险是否出现。
   - 页面没有后端连接失败提示。
6. 切到“竞争图谱”页检查：
   - 关系图节点和边可见。
   - 价格带、人群、场景切片可以切换。
   - 证据卡片和 QA 摘要可见。
7. 切到“产品与竞品画像”页检查：
   - 目标产品与核心竞品对比可见。
   - Human Review 修改入口可用。
   - 提交一次结构化修改后，页面无报错。
8. 切到“分析报告”页检查：
   - 8 个报告章节可见。
   - Word `.docx` 下载按钮可点击。
   - 浏览器打印/打印视图入口可用。
   - 页面不应出现 Markdown 导出按钮。
9. 切到“证据与过程追踪”页检查：
   - Evidence 链路可见。
   - QA 打回记录可见。
   - Collection 补证、Analysis 重算和 Diff 记录可见。

## 4. 可选接口冒烟测试

后端启动后，可以用 PowerShell 快速检查接口：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

创建一个稳定 Demo 任务：

```powershell
$body = Get-Content ..\demo\stable-demo-input.json -Raw
$resp = Invoke-RestMethod -Uri http://127.0.0.1:8000/tasks -Method Post -ContentType 'application/json' -Body $body
$taskId = $resp.data.task_id
$taskId
```

查询任务与核心页面数据：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId"
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId/overview"
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId/battlefield"
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId/profile"
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId/report"
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId/trace"
```

下载 Word 报告：

```powershell
Invoke-WebRequest "http://127.0.0.1:8000/tasks/$taskId/report/docx" -OutFile ..\data\reports\manual-demo-report.docx
```

## 5. 停止服务

两个终端分别按：

```text
Ctrl + C
```

