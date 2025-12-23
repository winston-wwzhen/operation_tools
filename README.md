# HotSpotAI

> 全网热点聚合与 AI 自动化文案生成工具（前后端分离版）

这是一个基于 Python + FastAPI + Vue.js 的前后端分离项目。它能够自动抓取主流平台（微博、百度、知乎、抖音、小红书、今日头条）的热搜数据，利用大模型（GLM-4）进行智能分析、评分和打标签，并能根据热点自动生成文章草稿。

## ✨ 主要功能

### 多平台热搜抓取
- 微博热搜 (Weibo)
- 百度热搜 (Baidu)
- 知乎热榜 (Zhihu) - 使用 Playwright
- 抖音热榜 (Douyin) - 使用 Playwright
- 小红书热榜 (Xiaohongshu)
- 今日头条热榜 (Toutiao)

### AI 智能分析
- 使用 GLM-4 模型对热点进行评分 (0-100)
- 自动分类打标签
- 支持生成微信公众号、小红书、知乎、今日头条等平台适配的文案

### 历史数据查询
- 所有数据自动保存到数据库
- 支持按日期范围筛选历史记录
- 支持按数据源筛选（微博/百度/知乎等）
- 分页浏览历史热点

### 定时任务
- 内置 APScheduler，支持 Cron 表达式配置自动运行
- 默认每 2 小时自动抓取一次
- 支持手动触发刷新

### 可视化界面
- Vue.js 3 + Element Plus 响应式界面
- 实时热点展示与状态监控
- 支持移动端访问
- SSE 实时事件推送

## 📂 项目结构

```
operation_tools/
├── HotSpotAI/              # 后端服务 (端口 3000)
│   ├── main.py             # FastAPI 入口
│   ├── api/                # API 路由模块
│   │   ├── __init__.py
│   │   ├── status.py       # 状态接口
│   │   ├── content.py      # 内容生成接口
│   │   └── history.py      # 历史数据接口
│   ├── core/               # 核心模块
│   │   ├── config.py       # 配置管理
│   │   ├── database.py     # 数据库管理
│   │   ├── llm.py          # AI 引擎
│   │   ├── scheduler.py    # 任务调度
│   │   └── logger.py       # 日志系统
│   ├── scrapers/           # 各平台爬虫
│   │   ├── weibo.py
│   │   ├── baidu.py
│   │   ├── zhihu.py
│   │   ├── douyin.py
│   │   ├── xiaohongshu.py
│   │   └── toutiao.py
│   ├── .env                # 环境配置
│   └── pyproject.toml      # Poetry 依赖配置
│
├── frontend/               # 前端项目 (端口 8080)
│   ├── src/
│   │   ├── main.js         # 入口文件
│   │   ├── App.vue         # 根组件
│   │   ├── router/         # 路由管理
│   │   ├── api/            # API 请求封装
│   │   ├── views/          # 页面视图
│   │   │   ├── Home.vue    # 主页（最新热点）
│   │   │   └── History.vue # 历史记录页
│   │   └── components/     # 公共组件
│   └── package.json
│
└── scripts/                # 启动脚本
    ├── start.bat           # Windows 统一启动
    ├── stop.bat            # Windows 停止服务
    └── start.sh            # Mac/Linux 统一启动
```

## 🚀 快速开始

### 一键启动（推荐）

**Windows:**
```bash
# 双击运行或命令行执行
scripts\start.bat
```

**Mac/Linux:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

启动脚本会自动：
1. 检查 Python 环境
2. 安装 Playwright 浏览器（如需要）
3. 启动后端服务（端口 3000）
4. 启动前端服务（端口 8080）
5. 自动打开浏览器

### 手动启动

**后端:**
```bash
cd HotSpotAI

# 安装依赖 (Poetry)
poetry install

# 或使用 pip
pip install fastapi uvicorn[standard] pydantic pydantic-settings httpx beautifulsoup4 playwright openai apscheduler aiosqlite tenacity

# 安装 Playwright 浏览器
playwright install chromium

# 启动服务
poetry run python main.py
```

后端 API 运行在 **http://localhost:3000**

API 文档: **http://localhost:3000/docs**

**前端:**
```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run serve
```

前端界面运行在 **http://localhost:8080**

### 停止服务

**Windows:**
```bash
scripts\stop.bat
```

**Mac/Linux:**
```bash
./scripts/stop.sh
```

## ⚙️ 配置说明

复制 `HotSpotAI/.env.example` 为 `HotSpotAI/.env` 并填写配置：

```bash
# ============ LLM 配置 ============
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4.7
LLM_TIMEOUT=120

# ============ 定时任务配置 ============
SCHEDULE_CRON=0 */2 * * *    # 每2小时执行一次
AUTO_RUN=true                # 是否自动运行定时任务

# ============ 爬虫配置 ============
TOPIC_LIMIT=10               # 每个平台抓取数量

# ============ 服务配置 ============
HOST=0.0.0.0
PORT=3000
DEBUG=false
```

## 🛠️ API 接口说明

### 状态接口
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/status` | 获取系统状态、配置和日志 |
| GET | `/api/events` | SSE 实时事件推送 |

### 内容接口
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/refresh-topics` | 手动触发热点聚合任务 |
| POST | `/api/generate-draft` | 根据热点生成文章草稿 |

### 历史数据接口
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/api/history/topics` | 获取历史热点（支持分页、筛选） |
| GET | `/api/history/dates` | 获取所有可用日期列表 |
| GET | `/api/history/stats` | 获取数据库统计信息 |

### 健康检查
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 根路径 |
| GET | `/health` | 健康检查 |

## 📦 依赖说明

### 后端依赖
- **FastAPI** - Web 框架
- **Uvicorn** - ASGI 服务器
- **Playwright** - 浏览器自动化
- **HTTPX** - 异步 HTTP 客户端
- **BeautifulSoup4** - HTML 解析
- **APScheduler** - 定时任务
- **OpenAI SDK** - GLM-4 API 客户端
- **aiosqlite** - 异步 SQLite
- **tenacity** - 重试机制
- **pydantic-settings** - 配置管理

### 前端依赖
- **Vue 3** - 前端框架
- **Vue Router** - 路由管理
- **Element Plus** - UI 组件库
- **Axios** - HTTP 客户端
- **TailwindCSS** - CSS 框架
- **Marked** - Markdown 解析

## ⚠️ 注意事项

1. **Poetry 虚拟环境**: 使用 `poetry run python` 确保依赖正确加载

2. **Playwright 浏览器**: 知乎、抖音、今日头条的抓取依赖无头浏览器，请务必执行 `playwright install chromium`

3. **API Key**: 请配置有效的智谱 AI (GLM-4) API Key

4. **Windows 用户**: 已包含 Windows 平台的 ProactorEventLoop 修复

5. **数据存储**: SQLite 数据库文件 `data.db` 会自动创建在 HotSpotAI 目录下

## 📝 更新日志

### v1.1.0
- 重命名为 HotSpotAI
- 添加历史数据查询功能
- 添加定时任务自动运行
- 优化前端界面，添加历史记录页面
- 完善日志系统

### v1.0.0
- 初始版本
- 支持 6 个平台的热搜抓取
- AI 智能分析与文案生成
- 前后端分离架构

## 📄 许可证

MIT License
