# 智览平台

智览是一个面向新闻采集、信息聚类、AI 摘要和研报生成的全栈应用。项目包含 Nuxt 3 前端和 FastAPI 后端，使用 MySQL 保存业务数据，Redis 提供缓存，Elasticsearch 提供全文检索。

## 功能概览

- RSS 和网页内容采集
- 新闻去重、聚类和主题管理
- 基于 DeepSeek 的摘要与研报生成
- Dashboard、简报、研报和运行监控页面
- Markdown / PDF 报告导出
- REST API 和 WebSocket 实时状态推送

## 技术栈

- 前端：Vue 3、Nuxt 3、TypeScript、Pinia、Tailwind CSS、ECharts
- 后端：Python 3.11+、FastAPI、SQLAlchemy、Pydantic Settings
- 数据服务：MySQL 8、Redis 7、Elasticsearch 8
- AI 服务：DeepSeek LLM；可选使用 DashScope Embedding 和 TianAPI
- 部署：Docker Compose

## 项目结构

```text
.
├── README.md
├── zhilan-platform/
│   ├── app.vue
│   ├── pages/                 # 前端页面
│   ├── components/            # 前端组件
│   ├── stores/                # Pinia 状态
│   ├── server/api/            # Nuxt 服务端接口代理
│   ├── backend/
│   │   ├── app/              # FastAPI 应用
│   │   ├── .env.example      # 配置模板
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── docker-compose.yml
└── docs/                      # 项目设计文档
```

## 环境要求

本地开发需要：

- Python 3.11 或更高版本
- Node.js 18 或更高版本
- MySQL 8
- Redis 7（可选）
- Elasticsearch 8（可选）

也可以使用 Docker Desktop 启动全部依赖服务。

## 配置环境变量

进入后端目录，复制配置模板：

```powershell
cd zhilan-platform/backend
Copy-Item .env.example .env
```

然后编辑 `.env`，至少配置：

```dotenv
DB_PASSWORD=你的MySQL密码
DEEPSEEK_API_KEY=你的DeepSeek密钥
MYSQL_ROOT_PASSWORD=你的MySQL密码
ELASTIC_PASSWORD=你的Elasticsearch密码
```

如需使用向量检索、TianAPI 或邮件通知，再配置对应的 `DASHSCOPE_API_KEY`、`TIANAPI_KEY` 和 QQ 邮箱变量。`.env` 只保存在本地，不要提交到 GitHub；提交时使用 `.env.example`。

完整变量列表见 [backend/.env.example](zhilan-platform/backend/.env.example)，后端配置说明见 [backend/README.md](zhilan-platform/backend/README.md)。

## 本地启动

### 1. 启动后端依赖

先确保 MySQL 已启动，并创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS zhilian
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Redis 和 Elasticsearch 不可用时，后端部分功能会自动降级；需要完整检索能力时再启动它们。

### 2. 启动后端

```powershell
cd zhilan-platform/backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`app.seed` 会自动建表，并幂等地初始化主题、数据源、定时任务、推送渠道和监控指标。

后端地址：

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- WebSocket：ws://localhost:8000/ws

### 3. 启动前端

打开新的终端：

```powershell
cd zhilan-platform
npm install
npm run dev
```

前端默认地址：http://localhost:3000

## Docker 启动

Docker 构建后端镜像时会读取 `zhilan-platform/backend/.env`，因此首次启动前必须先创建它：

```powershell
cd zhilan-platform/backend
Copy-Item .env.example .env
# 编辑 .env，填入 DeepSeek 密钥等配置
cd ..
docker compose up -d --build
```

查看服务状态和日志：

```powershell
docker compose ps
docker compose logs -f backend
```

停止服务：

```powershell
docker compose down
```

Compose 会启动前端、后端、MySQL、Redis 和 Elasticsearch。后端容器启动时会自动执行 `python -m app.seed` 建表并初始化基础配置，MySQL 和 Elasticsearch 的数据保存在 Docker volumes 中。

当前 Compose 默认端口：

| 服务 | 地址 |
|---|---|
| 前端 | http://localhost:3000 |
| 后端 | http://localhost:8000 |
| MySQL | localhost:3306 |
| Redis | localhost:6379 |
| Elasticsearch | http://localhost:9200 |

## 数据库和 Elasticsearch 初始化

### MySQL

- 本地启动：手动创建 `zhilian` 数据库后运行 `python -m app.seed`。
- Docker 启动：Compose 会通过 `MYSQL_DATABASE=zhilian` 自动创建数据库，后端启动时运行种子脚本并建表。
- 重复执行种子脚本是安全的，已有基础数据会被跳过。

### Elasticsearch

- 本地启动时，将 `ES_HOST`、`ES_USER` 和 `ES_PASSWORD` 配置为实际值。
- Docker 启动时，Compose 会启动单节点 Elasticsearch，并使用健康检查等待服务可用。
- Elasticsearch 不可用时，后端会自动降级；需要全文检索和索引功能时再检查 ES 连接及索引状态。

## 常见问题

### `DEEPSEEK_API_KEY` 未配置

摘要或研报生成会失败。确认 `zhilan-platform/backend/.env` 中存在真实的 `DEEPSEEK_API_KEY`，并重启后端。

### Docker 构建找不到 `.env`

后端 Dockerfile 会复制 `.env`。在 `zhilan-platform/backend` 下执行 `Copy-Item .env.example .env` 后，再重新运行 `docker compose up -d --build`。

### MySQL 连接失败

检查 MySQL 是否启动、端口是否为 `3306`，以及 `.env` 中的 `DB_HOST`、`DB_USER`、`DB_PASSWORD` 和 `DB_NAME` 是否正确。Docker 环境中的数据库主机应为 `mysql`，不是 `localhost`。

### Redis 或 Elasticsearch 连接失败

确认服务已经启动，检查 `.env` 中的地址、端口、用户名和密码。Redis / Elasticsearch 不是基础页面运行的唯一依赖，暂时不可用时后端会尝试降级。

### 端口被占用

Windows 下可以查看占用进程：

```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

然后结束对应进程，或修改前后端端口配置。

### PowerShell 无法激活虚拟环境

可以临时允许当前终端执行脚本：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

## 安全提示

不要将真实的 API Key、数据库密码、邮箱授权码、`.env` 文件、数据库文件、日志、报告导出物或依赖目录提交到 GitHub。项目根目录的 `.gitignore` 已配置相应忽略规则。
