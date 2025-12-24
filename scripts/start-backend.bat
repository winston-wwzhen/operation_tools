@echo off
REM HotSpotAI 后端启动脚本 (Windows)
REM 用途: 启动 FastAPI 后端服务
chcp 65001 >nul

echo ================================
echo  HotSpotAI 后端启动
echo ================================
echo.

cd /d "%~dp0..\HotSpotAI"

REM ================================
REM 依赖检查
REM ================================
echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)
echo [√] Python 已安装

echo.
echo [2/3] 检查 Poetry...
where poetry >nul 2>&1
if errorlevel 1 (
    echo [错误] Poetry 未安装
    echo        访问: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)
echo [√] Poetry 已安装

echo.
echo [3/3] 检查 Python 依赖...

REM 检查 FastAPI
poetry show fastapi >nul 2>&1
if errorlevel 1 (
    echo [警告] FastAPI 未安装，正在安装依赖...
    poetry install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [√] FastAPI 已安装
)

REM 检查关键认证依赖包
poetry show python-jose >nul 2>&1
if errorlevel 1 (
    echo [警告] python-jose 未安装，正在更新依赖...
    poetry install
)

REM 检查 passlib
poetry show passlib >nul 2>&1
if errorlevel 1 (
    echo [警告] passlib 未安装，正在更新依赖...
    poetry install
)

REM 检查 Playwright 浏览器
echo.
echo 检查 Playwright 浏览器...
poetry run python -c "from playwright.sync_api import sync_playwright" >nul 2>&1
if errorlevel 1 (
    echo [警告] Playwright 未完全安装，正在安装浏览器...
    set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
    poetry run playwright install chromium
) else (
    echo [√] Playwright 已安装
)

echo.
echo ================================
echo  依赖检查完成，正在启动服务...
echo ================================
echo.
echo 后端 API:     http://localhost:3000
echo API 文档:     http://localhost:3000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

poetry run python main.py
