@echo off
REM HotSpotAI 统一启动脚本 (Windows)
REM 用途: 同时启动前后端服务
chcp 65001 >nul

echo ================================
echo  HotSpotAI 启动脚本
echo ================================
echo.

REM 检查端口占用 (先筛选 LISTENING 状态，再匹配端口)
netstat -ano | findstr "LISTENING" | findstr ":3000" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 3000 已被占用，请先运行 stop.bat 停止服务
    echo.
    pause
    exit /b 1
)

netstat -ano | findstr "LISTENING" | findstr ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 8080 已被占用，请先运行 stop.bat 停止服务
    echo.
    pause
    exit /b 1
)

REM 设置镜像源
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

echo [1/2] 启动后端服务...
start "HotSpotAI-Backend" cmd /c "cd /d "%~dp0..\HotSpotAI" && poetry run python main.py 2>&1"

REM 等待后端启动
echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo [2/2] 启动前端服务...
start "HotSpotAI-Frontend" /min cmd /c "cd /d "%~dp0..\frontend" && npm run serve"

REM 等待前端启动
timeout /t 8 /nobreak >nul

echo.
echo ================================
echo  服务启动完成！
echo ================================
echo.
echo 后端 API:     http://localhost:3000
echo API 文档:     http://localhost:3000/docs
echo 前端界面:     http://localhost:8080
echo.
echo 按任意键打开浏览器...
pause >nul

REM 打开浏览器
start http://localhost:8080

echo.
echo 服务已在后台运行，关闭此窗口不会停止服务。
echo 要停止服务请运行 stop.bat
