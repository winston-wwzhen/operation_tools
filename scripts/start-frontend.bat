@echo off
REM AutoMediaBot 前端启动脚本 (Windows)
REM 用途: 启动 Vue.js 前端开发服务器
chcp 65001 >nul

echo ================================
echo AutoMediaBot 前端启动
echo ================================

cd /d "%~dp0frontend"

echo.
echo 检查 Node.js 环境...
node --version
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    pause
    exit /b 1
)

echo.
echo 检查依赖...
if not exist "node_modules" (
    echo [提示] 依赖未安装，正在安装...
    call npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo.
echo 启动前端开发服务器...
echo 前端地址: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务
echo.

call npm run serve
