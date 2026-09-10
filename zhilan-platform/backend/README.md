# 智览后端启动指南

## 环境要求

| 依赖 | 版本要求 | 说明 |
|---|---|---|
| Python | 3.9+ | |
| MySQL | 8.0+ | 需提前创建 `zhilian` 数据库 |
| Redis | 7.x | 缓存，可选（未启动时自动降级为内存缓存） |
| Elasticsearch | 8.x | 全文检索，可选（未启动时自动降级） |

## 前置服务启动

按顺序启动依赖服务：

```bash
# 1. MySQL  D:\Tools\Es\bin\elasticsearch.bat
net start mysql          # Windows 服务方式
# 或
mysqld --console         # 手动启动

# 2. Redis
redis-server             # 默认 127.0.0.1:6379

# 3. Elasticsearch
D:\Tools\Es\bin\elasticsearch.bat    # 默认 http://localhost:9200
```

> Redis / ES 不可用时后端会自动降级，不影响基本功能。

## 快速启动

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量（首次使用，已有 .env 则跳过）
cp .env.example .env
# 然后按需编辑 .env（数据库密码、API Key 等）

# 4. 初始化种子数据（自动建表 + 插入演示数据）
python -m app.seed

# 5. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

启动后访问：
| 地址 | 说明 |
|---|---|
| http://localhost:8000/docs | Swagger API 文档 |
| http://localhost:8000/redoc | ReDoc API 文档 |
| http://localhost:8000/health | 健康检查 |
| ws://localhost:8000/ws | WebSocket 实时推送 |

## API 路由一览

| 路径 | 方法 | 说明 |
|---|---|---|
| `/api/v1/dashboard/stats` | GET | 仪表盘统计数据 |
| `/api/v1/dashboard/top-news` | GET | 今日热点 |
| `/api/v1/dashboard/trend` | GET | 采集趋势 |
| `/api/v1/dashboard/latest-reports` | GET | 最新研报卡片 |
| `/api/v1/dashboard/workflow-status` | GET | 工作流进度 |
| `/api/v1/briefs` | GET | 每日简报列表（支持 `?date=` 过滤） |
| `/api/v1/briefs/{id}` | GET | 简报详情 |
| `/api/v1/reports` | GET | 研报列表（支持 `?q=` 搜索） |
| `/api/v1/reports/{id}` | GET | 研报详情（含四段式内容） |
| `/api/v1/clusters` | GET | 新闻聚类列表 |
| `/api/v1/clusters/graph` | GET | 力导向图数据 |
| `/api/v1/clusters/{id}` | GET | 聚类详情 |
| `/api/v1/monitor/status` | GET | 流水线状态 + Agent + 指标 |
| `/api/v1/monitor/agents` | GET | Agent 状态列表 |
| `/api/v1/monitor/logs` | GET | 系统日志（分页） |
| `/api/v1/monitor/metrics` | GET | 系统指标 |
| `/api/v1/topics` | GET/POST | 主题管理 |
| `/api/v1/topics/{id}` | DELETE | 删除主题 |
| `/api/v1/topics/{id}/toggle` | PUT | 启用/禁用主题 |
| `/api/v1/sources` | GET | 数据源列表 |
| `/api/v1/sources/{id}` | PUT | 启用/禁用数据源 |
| `/api/v1/config/cron` | GET/PUT | 定时任务配置 |
| `/api/v1/config/push` | GET | 推送渠道 |
| `/api/v1/config/push/{id}` | PUT | 启用/禁用推送渠道 |
| `/api/v1/collect` | POST | 手动触发采集 |
| `/ws` | WebSocket | 实时推送（进度/日志/Agent状态） |

## 关键配置（.env）

### MySQL
| 变量 | 说明 | 默认值 |
|---|---|---|
| `DB_HOST` | MySQL 主机 | `localhost` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | MySQL 用户 | `root` |
| `DB_PASSWORD` | MySQL 密码 | - |
| `DB_NAME` | 数据库名 | `zhilian` |

### Redis
| 变量 | 说明 | 默认值 |
|---|---|---|
| `REDIS_HOST` | Redis 主机 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_PASSWORD` | Redis 密码 | 空 |

### Elasticsearch
| 变量 | 说明 | 默认值 |
|---|---|---|
| `ES_HOST` | ES 地址 | `http://localhost:9200` |
| `ES_USER` | ES 用户名 | `elastic` |
| `ES_PASSWORD` | ES 密码 | - |

### DeepSeek LLM
| 变量 | 说明 | 默认值 |
|---|---|---|
| `DEEPSEEK_API_KEY` | API Key | - |
| `DEEPSEEK_API_BASE` | API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名 | `deepseek-v4-pro` |

### QQ邮箱通知（可选）
| 变量 | 说明 |
|---|---|
| `QQ_EMAIL_SENDER` | 发送方 QQ 邮箱 |
| `QQ_EMAIL_AUTH_CODE` | SMTP 授权码 |
| `QQ_EMAIL_RECEIVER` | 接收方邮箱 |

### 后端服务
| 变量 | 说明 | 默认值 |
|---|---|---|
| `BACKEND_HOST` | 监听地址 | `0.0.0.0` |
| `BACKEND_PORT` | 监听端口 | `8000` |
| `ALLOWED_ORIGINS` | CORS 白名单（逗号分隔） | `http://localhost:3000` |

## 数据库初始化

首次启动前，在 MySQL 中创建数据库：

```sql
CREATE DATABASE IF NOT EXISTS zhilian CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

然后运行种子脚本（自动建表 + 插入演示数据）：

```bash
python -m app.seed
```

> 重复运行种子脚本会跳过已有数据，不会重复插入。

## Docker 一键启动

```bash
# 在项目根目录（zhilian-platform/）

# 仅启动基础服务
docker-compose up -d mysql redis

# 启动全部（backend + mysql + redis + es + frontend）
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止
docker-compose down
```

## 故障排查

### 数据库连接失败
```
sqlalchemy.exc.OperationalError: Can't connect to MySQL server
```
- 检查 MySQL 是否启动：`net start mysql` 或 `mysqld --console`
- 检查 `.env` 中 `DB_PASSWORD` 是否正确
- 确认 `zhilian` 数据库已创建

### Redis / ES 未启动
启动日志中看到连接错误是正常的，后端会自动降级。如需启用：
```bash
redis-server
d:\Tools\Es\bin\elasticsearch.bat
```

### 端口被占用
```
OSError: [Errno 10048] error while attempting to bind on address
```
- 修改 `.env` 中 `BACKEND_PORT` 为其他端口
- 或终止占用进程：`netstat -ano | findstr :8000` → `taskkill /PID xxx`

## 目录结构

```
backend/
├── app/
│   ├── main.py           # FastAPI 入口
│   ├── config.py         # 配置（读取 .env）
│   ├── database.py       # 数据库连接
│   ├── seed.py           # 种子数据
│   ├── api/              # API 路由
│   ├── models/           # 数据库模型
│   ├── schemas/          # Pydantic 类型
│   ├── cache/            # Redis 缓存
│   ├── search/            # Elasticsearch 全文检索
│   ├── scheduler/        # 定时任务
│   ├── collectors/       # 数据采集
│   ├── processors/       # 去重/聚类
│   ├── generators/       # 摘要/研报生成
│   ├── dispatchers/      # 推送分发
│   └── exporters/        # Markdown/PDF 导出
├── evaluation/            # 检索和结果评估脚本
├── runtime/               # 本地数据库和报告输出（不提交 git）
├── requirements.txt
├── Dockerfile
├── .env                  # 环境变量（不提交 git）
└── .env.example          # 环境变量模板
```
