# 手动采集「卡在摘要」问题排查与解决记录

## 一、问题现象

用户在实时监控页面点击「手动采集」按钮后，流水线一直停在「摘要」阶段（进度 80%），长时间无法完成，看起来像卡死。

## 二、根因分析

排查过程中共发现 3 个叠加的问题：

### 根因 1：研报生成串行调用 LLM，耗时过长

`backend/app/generators/report_generator.py` 的 `run_generation()` 原来对每个新闻簇**串行**调用 **2 次** DeepSeek LLM：



1. `generate_summary()` —— 生成摘要（1 次调用）
2. `_generate_report()` —— 生成四段式研报（1 次调用）

当一次采集产生 28~30 个簇时，需要 **56~60 次串行 HTTP 请求**，每次 5~15 秒，总计 **5~10 分钟**。期间「摘要」步骤一直停留在 80%，用户误以为卡死。

### 根因 2：两个后端实例并发运行

发现有两个 uvicorn 进程同时监听 8000 端口（PID 45856 与 102296）。它们各自拥有独立的事件循环和全局锁，各自的定时任务会**并发触发多条流水线**，互相竞争 LLM 资源，进一步拖慢甚至中断生成。

### 根因 3：Python 版本误判 + FastAPI 版本不兼容

- 项目实际使用 **Python 3.12**（`D:\develop\python\python.exe`），此前误用 Python 3.9（`D:\Python39\python.exe`）。
- 切换到 Python 3.12 并安装最新依赖后，新版 FastAPI（0.141.x）移除了 `app.add_websocket_route()` 方法，导致后端启动报错 `AttributeError: 'FastAPI' object has no attribute 'add_websocket_route'`。

## 三、解决过程

### 1. 优化研报生成：合并 LLM 调用 + 并发化

改造 `report_generator.py`：

- 新增 `_generate_full()`：**一次** LLM 调用同时返回摘要字段（title/summary/sentiment/heat/volatility/trends/category）与研报四段式字段（background/status_content/trend_short/trend_long/risk1/risk2/key_data/sources）。
- 重写 `run_generation()`：改为「串行读库 → 5 路并发 LLM（`asyncio.Semaphore(5)` + `asyncio.gather`）→ 串行写库」三段式。
- 新增 `_fallback_full()`：LLM 不可用时基于真实标题降级生成（非硬编码 mock）。

效果：每簇从 2 次串行调用降为 1 次并发调用，30 簇从 5~10 分钟缩短到约 30 秒。

### 2. 清理重复后端实例

杀掉重复的 uvicorn 进程（PID 102296 及其 worker），只保留一个实例，消除并发抢资源的流水线。

### 3. 切换到 Python 3.12

- 用 `D:\develop\python\python.exe -m pip install -r requirements.txt` 安装全部依赖（使用清华镜像源）。
- `jieba` 是源码包，需先安装 `setuptools`/`wheel` 才能构建。
- 修复 `main.py` 中的 WebSocket 路由注册方式（兼容新版 FastAPI）：

```python
# 旧写法（新版 FastAPI 已移除）
app.add_websocket_route("/ws", websocket_endpoint)
# 新写法（各版本通用）
app.websocket("/ws")(websocket_endpoint)
```

- 杀掉 Python 3.9 后端进程，用 Python 3.12 重启后端。

### 4. 清理僵尸记录

清理被中断遗留的 9 条 `status='running'` 的流水线记录（标记为 failed）。

## 四、验证结果

- 后端健康检查返回 200：`{"status":"ok","app":"智览 API","version":"1.0.0"}`。
- 流水线 33 秒完成：**采集 2 篇 → 去重后 2 篇 → 2 簇 → 生成 2 篇研报**。
- 新研报四段式字段完整、简报评分齐全，示例：
  - 「新干剪纸：非遗传承与创新之路」—— 情绪 80 / 热度 65 / 波动 30（文化产业）
  - 「中吉联合考古首年成果显著，丝路合作深化」—— 情绪 75 / 热度 60 / 波动 20（考古/文化合作）

## 五、涉及文件变更

| 文件 | 变更 |
|------|------|
| `backend/app/generators/report_generator.py` | 合并 LLM 调用、并发化 `run_generation`、新增降级逻辑 |
| `backend/app/main.py` | WebSocket 路由注册方式改为 `app.websocket("/ws")(...)` |
| `backend/requirements.txt` | 未改动（依赖清单保持不变） |

## 六、经验总结

1. LLM 批量生成务必并发化 + 限流（信号量），避免串行调用导致的超长等待。
2. 排查「卡住」问题时，先检查是否有多实例并发（`netstat` 查端口监听进程）。
3. 写类型注解时确认目标 Python 版本；`dict | None` 联合类型需 Python 3.10+。
4. 升级/重装依赖后，注意框架的破坏性 API 变更（如 FastAPI 移除 `add_websocket_route`）。

---

# 监控页面「Agent 状态」与「系统指标」空白问题排查与解决记录

## 一、问题现象

打开实时监控页面，右侧「Agent 状态」卡片区和底部「系统指标」卡片区完全空白，没有任何数据；而左侧「工作流管道视图」和「实时日志」显示正常。

## 二、根因分析

监控页面「Agent 状态」和「系统指标」分别读数据库两张表：`agent_statuses` 和 `system_metrics`，这两张表一直是**空的**（0 行）。

排查发现两个叠加原因：

1. `backend/app/seed.py` 只初始化了主题、数据源、定时任务、推送渠道四类配置，**漏掉了 `agent_statuses` 和 `system_metrics` 两张表**的初始化。
2. `backend/app/pipeline.py` 流水线收尾时，只执行 `select(AgentStatus)` **更新已存在的记录**（`if a.name in agent_map`），从不创建新记录；对 `SystemMetric` 甚至完全没有更新逻辑。

于是无论流水线跑多少次，这两张表始终是空的，页面永远空白。

## 三、解决过程

### 1. 补齐 seed 初始化（幂等）

在 `seed.py` 中增加两张表的初始化（已存在则跳过，不重复插入）：

- 4 个 Agent（与 `pipeline.py` 的 `agent_map` 名称对齐）：
  - `CollectorAgent`（采集）、`DedupAgent`（去重）、`ClusterAgent`（聚类）、`ResearchAgent`（研报生成）
  - 初始状态：`status="idle"`、`status_text="就绪"`、`color="gray"`
- 4 个系统指标：
  - `今日采集`（blue）、`去重保留率`（green）、`聚类簇数`（amber）、`研报通过率`（orange）

### 2. 让流水线收尾动态更新指标

在 `pipeline.py` 收尾阶段，基于本次流水线真实结果更新 4 个指标：

- 今日采集：本次采集篇数（subValue 为「篇」）
- 去重保留率：`去重后 / 采集总数 × 100%`
- 聚类簇数：本次生成的簇数
- 研报通过率：`通过数 / 生成数 × 100%`

### 3. 运行 seed 并验证

执行 `python -m app.seed` 落库，随后请求接口验证。

## 四、验证结果

接口 `GET /api/v1/monitor/status` 返回完整的 4 个 Agent 和 4 个指标：

```json
"agents": [
  {"name":"CollectorAgent","status":"done","detail":"已处理: 0篇","statusText":"✅ 就绪","color":"green"},
  {"name":"DedupAgent","status":"done","detail":"已处理: 0篇","statusText":"✅ 就绪","color":"green"},
  {"name":"ClusterAgent","status":"done","detail":"已处理: 0簇","statusText":"✅ 就绪","color":"green"},
  {"name":"ResearchAgent","status":"done","detail":"已生成: 0篇研报","statusText":"✅ 就绪","color":"green"}
],
"metrics": [
  {"label":"今日采集","value":"0","subValue":"篇","percentage":0,"color":"blue"},
  {"label":"去重保留率","value":"0","subValue":"%","percentage":0,"color":"green"},
  {"label":"聚类簇数","value":"0","subValue":"簇","percentage":0,"color":"amber"},
  {"label":"研报通过率","value":"0","subValue":"%","percentage":0,"color":"orange"}
]
```

页面「Agent 状态」和「系统指标」卡片恢复正常显示。当前数值为 0 是因为最近几次采集没有抓到新内容（RSS 已去重采完），属正常状态；下次抓到新文章后指标会自动更新为真实值。

## 五、涉及文件变更

| 文件 | 变更 |
|------|------|
| `backend/app/seed.py` | 新增 `AgentStatus`、`SystemMetric` 两张表的幂等初始化 |
| `backend/app/pipeline.py` | 流水线收尾时基于真实结果动态更新 4 个系统指标 |

## 六、经验总结

1. 监控/统计类页面空白，先查后端对应数据表是否为空，再看是否有初始化（seed）逻辑。
2. 种子数据初始化要覆盖**所有**基础配置表，不能只初始化业务主数据。
3. 「只更新不创建」的代码模式（如 pipeline 收尾更新 Agent）必须有配套的初始化逻辑，否则表永远是空的。
4. 排查数据问题时，用 SQL `COUNT(*)` 快速定位哪些表有数据、哪些表是空的。

---

# 研报「导出 PDF」无 PDF 文件问题排查与解决记录

## 一、问题现象

在研报详情页点击「导出 PDF」按钮没有反应，`backend/exports/` 目录里只有 `.md` 文件，从未生成过 `.pdf` 文件。

## 二、根因分析

整条 PDF 导出链路都是空的，共 3 处缺失：

1. **后端生成是降级实现**：`backend/app/exporters/file_exporter.py` 的 `export_to_pdf()` 注释明确写着「无 PDF 渲染库时的降级」，它只是把 Markdown 文本 UTF-8 编码成字节返回，从不生成真正的 PDF。
2. **后端没有下载接口**：`reports.py` 没有 PDF 导出路由；`dispatchers/pusher.py` 推送分发也只调用 `export_to_markdown()`，从不导出 PDF；`requirements.txt` 里也没有 PDF 生成库。
3. **前端按钮没绑定事件**：`pages/reports/[id].vue` 的「导出 PDF」按钮是纯装饰，没有 `@click` 处理。

## 三、解决过程

### 1. 安装 PDF 生成库 reportlab

```
pip install reportlab -i https://pypi.tuna.tsinghua.edu.cn/simple
```

> 提示：首次用官方源下载 reportlab 时速度仅 31.8 kB/s 且超时，改用清华镜像源后秒下。

### 2. 重写 `export_to_pdf()` 生成真实 PDF

用 reportlab 的 `SimpleDocTemplate` + `Paragraph` 排版，中文使用内置 CID 字体 `STSong-Light`（无需外部字体文件，开箱即用）：

- 标题/摘要/四段式（背景、现状、趋势、风险）/关键数据/来源分段渲染
- `Paragraph` 自动换行，避免长文本溢出
- 对内容做 HTML 转义（`&` `<` `>`），防止 `Paragraph` 解析报错
- 输出写入 `EXPORT_DIR/report_{id}.pdf`

### 3. 新增 PDF 下载接口

在 `reports.py` 新增 `GET /reports/{report_id}/export`，用 `FileResponse` 返回 `application/pdf` 文件流（需放在 `/{report_id}` 之前，避免路由歧义）。

### 4. 前端绑定下载事件

- `utils/api.ts` 新增 `BACKEND_ORIGIN` 后端直连地址常量。
- `[id].vue` 给「导出 PDF」按钮绑定 `@click="exportPdf"`，用 `window.open` 打开导出地址。

> 关键点：PDF 下载走**后端直连**而非 Nuxt 代理，因为 `server/api/v1/[...].ts` 的 `$fetch` 会把二进制流当文本解析而损坏文件。

### 5. 更新依赖清单

`requirements.txt` 新增 `reportlab>=4.0.0`。

## 四、验证结果

- `export_to_pdf(14)` 生成 `exports/report_14.pdf`：4433 字节，文件头 `%PDF-1.4` ✅
- 接口 `GET /api/v1/reports/14/export` 返回 **HTTP 200**，`content-type: application/pdf` ✅
- 前端点击「导出 PDF」后浏览器直接打开/下载真实 PDF ✅

## 五、涉及文件变更

| 文件 | 变更 |
|------|------|
| `backend/app/exporters/file_exporter.py` | 用 reportlab 重写 `export_to_pdf()`，生成真实 PDF |
| `backend/app/api/reports.py` | 新增 `GET /reports/{id}/export` 下载接口 |
| `backend/requirements.txt` | 新增 `reportlab>=4.0.0` |
| `utils/api.ts` | 新增 `BACKEND_ORIGIN` 后端直连地址常量 |
| `pages/reports/[id].vue` | 「导出 PDF」按钮绑定下载事件 |

## 六、经验总结

1. 「降级实现」的占位函数要留意，注释里写「无 XXX 库时的降级」往往意味着功能从未真正落地。
2. 二进制文件（PDF/图片）下载不能走会做 JSON 解析的代理，应直连后端或用 `responseType: 'arraybuffer'`。
3. reportlab 生成中文 PDF 用内置 CID 字体 `STSong-Light`，无需依赖系统字体文件，跨环境最省事。
4. 长文本内容写入 PDF 前先做 HTML 特殊字符转义，避免 `Paragraph` 把 `<` `>` 当成标签解析。
