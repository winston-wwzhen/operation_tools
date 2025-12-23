@echo off
REM HotSpotAI 后端启动脚本 (Windows)
REM 用途: 启动 FastAPI 后端服务
chcp 65001 >nul

echo ================================
echo HotSpotAI 后端启动
echo ================================

cd /d "%~dp0..\HotSpotAI"

echo.
echo 检查 Python 环境...
python --version
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo.
echo 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [提示] 依赖未安装，正在安装...
    pip install fastapi uvicorn[standard] pydantic httpx beautifulsoup4 playwright openai apscheduler
)

echo.
echo 安装 Playwright 浏览器...
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
python -m playwright install chromium

echo.
echo 启动后端服务...
echo 后端 API: http://localhost:3000
echo API 文档: http://localhost:3000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

poetry run python main.py
