# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是 **HotSpotAI**，一个全栈 Web 应用，用于聚合中文社交媒体平台的热点话题并生成 AI 驱动的文案草稿。

**技术栈：**
- 后端：Python FastAPI + SQLite
- 前端：Vue.js 3 + TypeScript + Element Plus
- AI：GLM-4（智谱 AI）通过 OpenAI SDK
- 爬虫：Playwright + BeautifulSoup4

**项目结构：**
```
operation_tools/
├── HotSpotAI/              # 后端 (端口 3000)
│   ├── main.py             # FastAPI 入口
│   ├── api/                # API 路由
│   ├── core/               # 核心模块
│   ├── scrapers/           # 各平台爬虫 (继承基类)
│   ├── tests/              # 单元测试
│   ├── scripts/            # 工具脚本
│   └── .env.example        # 环境配置模板
├── frontend/               # 前端 (端口 8080)
│   ├── src/
│   │   ├── views/          # 页面视图
│   │   ├── api/            # API 封装
│   │   ├── composables/    # 组合式函数
│   │   └── utils/          # 工具函数 (TypeScript)
│   └── package.json
├── deploy/                 # Ubuntu 部署脚本
└── scripts/                # 本地开发启动脚本
```

## 常用开发命令

### 本地开发

**一键启动（推荐）：**
```bash
# Windows
scripts\start.bat

# Mac/Linux
./scripts/start.sh
```

**手动启动：**
```bash
# 后端 (HotSpotAI/)
poetry install
playwright install chromium
poetry run python main.py

# 前端 (frontend/)
npm install
npm run serve
```

### 测试

```bash
# 运行所有测试
cd HotSpotAI
poetry run pytest

# 运行测试并查看覆盖率
poetry run pytest --cov=. --cov-report=html

# 运行特定测试文件
poetry run pytest tests/unit/test_database.py
```

### 代码质量检查

```bash
# 格式化代码
poetry run black .
poetry run isort .

# 代码检查
poetry run flake8 .
poetry run mypy core/

# 安全检查
poetry run bandit -r core/
```

### 停止服务

**Windows：** `scripts\stop.bat`
**Mac/Linux：** `./scripts/stop.sh`

### 创建管理员账户

```bash
cd HotSpotAI
poetry run python scripts/create_admin.py
```

默认账户：`admin` / `aaaaaa`（请立即修改密码）

### Ubuntu 服务器部署

```bash
# 一键部署
sudo bash deploy/deploy.sh

# 更新
cd /opt/hotspotai && sudo bash deploy/update.sh

# 服务管理
sudo systemctl status hotspotai-backend
sudo journalctl -u hotspotai-backend -f
```

## 架构设计

### 后端架构

**入口文件：** `HotSpotAI/main.py`

启动顺序：
1. Windows ProactorEventLoop 修复 (第 6-7 行)
2. 初始化日志系统（带文件轮转）
3. 初始化数据库连接池
4. 从数据库恢复最新热点数据
5. 启动 APScheduler 定时任务
6. 检查/安装 Playwright 浏览器

**配置 (`core/config.py`)：**
- 使用 `pydantic-settings` 加载环境变量
- 单例模式通过 `get_settings()` 获取
- 运行时状态存储在 `runtime_state` 字典中
- 日志缓冲区使用 `core/log_utils.py` 共享

**日志系统 (`core/log_utils.py`)：**
- 独立日志缓冲区，避免循环导入
- 线程安全的日志管理
- 被 `config.py` 和 `logger.py` 共享使用

**数据库连接池 (`core/db_pool.py`)：**
- WAL 模式提升并发性能
- 单例连接管理
- 通过 `get_db()` 上下文管理器使用

**LLM 集成 (`core/llm.py`)：**
- Prompt 配置化在 `core/prompts.py`
- 两个核心函数：
  - `analyze_hot_topics()` - 去重、评分 (0-100)、打标签
  - `generate_article_for_topic()` - 按平台风格生成文案
- 支持平台特定的 temperature 参数

**Prompt 配置 (`core/prompts.py`)：**
- 集中管理所有 LLM Prompt
- 支持的平台：wechat, xiaohongshu, zhihu, toutiao
- 每个平台有独立的 temperature 配置

**爬虫 (`scrapers/`)：**
- 所有爬虫继承自 `BaseScraper` 基类
- HTTP 爬虫继承 `HTTPScraper`：weibo, baidu
- Playwright 爬虫继承 `PlaywrightScraper`：zhihu, douyin, xiaohongshu, toutiao
- 使用工厂模式和装饰器注册

### 前端架构

**Vue 3 + TypeScript：**
- `composables/useAuth.js` - JWT token 认证状态管理
- `api/modules/` - 集中的 API 封装
- `router/index.js` - 客户端路由

**工具函数 (`src/utils/`)：**
- `formatters.ts` - 日期格式化函数
- `platform.ts` - 平台相关工具和配置

## 配置说明

复制 `HotSpotAI/.env.example` 为 `HotSpotAI/.env`：

**必需配置：**
- `LLM_API_KEY` - 智谱 AI (GLM-4) API 密钥

**可选配置：**
- `LLM_MODEL` - 默认：`glm-4.7`
- `SCHEDULE_CRON` - 默认：`0 */2 * * *`
- `AUTO_RUN` - 是否自动运行定时任务
- `TOPIC_LIMIT` - 每个平台抓取数量（默认：10）
- `CORS_ORIGINS` - 逗号分隔的允许来源
- `JWT_SECRET_KEY` - 认证密钥
- `DEBUG` - 启用 FastAPI 热重载

## 平台爬虫

| 平台 | 方式 | 基类 |
|------|------|------|
| 微博 | HTTP + BeautifulSoup | HTTPScraper |
| 百度 | HTTP + BeautifulSoup | HTTPScraper |
| 知乎 | Playwright (聚合平台) | PlaywrightScraper |
| 抖音 | Playwright (API拦截) | PlaywrightScraper |
| 小红书 | Playwright (聚合平台) | PlaywrightScraper |
| 头条 | Playwright (API拦截) | PlaywrightScraper |

## 用户认证

- JWT token + bcrypt 密码哈希
- 管理员用户可手动刷新热点
- Token 存储在 localStorage (`useAuth.js`)

## AI 文案生成平台

| 平台 | Temperature | 风格 |
|------|-------------|------|
| `wechat` | 0.8 | HTML 格式，深度分析 |
| `xiaohongshu` | 0.9 | Emoji 丰富，口语化 |
| `zhihu` | 0.5 | Markdown，理性客观 |
| `toutiao` | 0.7 | 标题党风格 |

## 测试

```bash
# 运行所有测试
poetry run pytest

# 带覆盖率报告
poetry run pytest --cov=. --cov-report=html

# 运行特定测试
poetry run pytest tests/unit/test_database.py -v
```

## Pre-commit Hooks

项目配置了 pre-commit hooks，会在提交时自动运行：
- Black (代码格式化)
- isort (导入排序)
- flake8 (代码检查)
- mypy (类型检查)
- bandit (安全检查)

安装：
```bash
cd HotSpotAI
poetry run pre-commit install
```

## CI/CD

GitHub Actions 自动化：
- CI: 每次 push 和 PR 自动运行测试和代码检查
- Deploy: main 分支推送后自动部署到服务器

## 数据流向

1. 爬虫从 6 个平台抓取原始热点
2. `analyze_hot_topics()` 通过 LLM 去重、评分、打标签
3. 结果存储在连接池并持久化到 SQLite
4. 前端通过 `/api/status` 或 SSE 事件获取
5. 用户点击"生成" → `generate_article_for_topic()` 创建平台特定内容
6. 文章保存到用户个人库（可选公开分享）
