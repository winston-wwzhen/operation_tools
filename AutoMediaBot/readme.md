AutoMediaBot (Python Server)

这是一个基于 Python + FastAPI 的全网热点聚合与 AI 自动化文案生成工具。

它能够自动抓取主流平台（微博、百度、知乎、抖音）的热搜数据，利用大模型（GLM-4）进行智能分析、评分和打标签，并能根据热点自动生成公众号文章草稿。

✨ 主要功能

多平台热搜抓取:

微博热搜 (Weibo)

百度热搜 (Baidu)

知乎热榜 (Zhihu) - 使用 Playwright 模拟浏览器

抖音热榜 (Douyin) - 使用 Playwright 模拟浏览器

AI 智能分析:

使用 GLM-4 模型对热点进行评分 (0-100) 和自动分类打标签。

支持联网搜索，生成深度文章草稿。

可视化后台: 提供 Web 界面展示热点数据、控制任务状态。

定时任务: 内置 APScheduler，支持 Cron 表达式配置自动运行。

📂 目录结构 (重构版)

项目已进行模块化拆分，结构如下：

py_server/
├── main.py              # [入口] 程序启动入口，FastAPI 路由配置
├── config_manager.py    # [配置] 全局配置管理、日志系统、状态管理
├── scraper_engine.py    # [爬虫] 各平台抓取逻辑 (HTTPX + Playwright)
├── llm_engine.py        # [AI] 大模型交互逻辑 (GLM-4)
├── task_scheduler.py    # [调度] 定时任务编排与执行
├── config.json          # 配置文件 (自动生成)
├── requirements.txt     # 项目依赖
└── public/              # 前端静态资源 (可选)


🚀 快速开始

1. 环境准备

确保已安装 Python 3.10 或以上版本。

2. 安装依赖

# 1. 安装 Python 库
pip install -r requirements.txt

# 2. 安装 Playwright 浏览器内核 (用于抓取知乎/抖音)
playwright install chromium


3. 配置文件

项目启动后会自动生成 config.json，或者你可以手动创建。关键配置项说明：

{
  "llmApiKey": "your_glm4_api_key",
  "llmBaseUrl": "[https://open.bigmodel.cn/api/paas/v4/](https://open.bigmodel.cn/api/paas/v4/)",
  "llmModel": "glm-4",
  "scheduleCron": "0 */2 * * *",   // Cron 表达式 (默认每2小时)
  "autoRun": false,                // 是否自动启动定时任务
  "topicLimit": 10                 // 每个平台抓取数量限制
}


4. 启动服务

运行新的入口文件：

python main.py


启动成功后，访问控制台：

地址: http://localhost:3000

🛠️ API 接口说明

方法

路径

描述

GET

/api/status

获取当前服务运行状态、配置和最近日志

POST

/api/config

更新系统配置

POST

/api/refresh-topics

立即触发一次全网热点聚合任务 (后台异步)

POST

/api/generate-draft

针对指定热点生成文章草稿

⚠️ 注意事项

Playwright 依赖: 知乎和抖音的抓取依赖无头浏览器，请务必执行 playwright install chromium。

API Key: 请确保在 config.json 或前端设置页面中配置了有效的智谱 AI (GLM-4) API Key，否则无法进行智能分析和文案生成。

Windows 用户: main.py 中已包含针对 Windows 平台的 ProactorEventLoop 修复代码，可直接运行。