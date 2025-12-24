@echo off
REM HotSpotAI 统一启动脚本 (Windows)
REM 用途: 同时启动前后端服务
chcp 65001 >nul

echo ================================
echo  HotSpotAI 启动脚本
echo ================================
echo.

REM ================================
REM 依赖检查
REM ================================
echo [0/4] 检查依赖...

REM 检查 Poetry
where poetry >nul 2>&1
if errorlevel 1 (
    echo [错误] Poetry 未安装，请先安装 Poetry
    echo        访问: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)
echo [√] Poetry 已安装

REM 检查 Python 依赖
cd /d "%~dp0..\HotSpotAI"
poetry show fastapi >nul 2>&1
if errorlevel 1 (
    echo [警告] Python 依赖未安装，正在安装...
    poetry install
    if errorlevel 1 (
        echo [错误] Poetry 安装失败
        pause
        exit /b 1
    )
) else (
    echo [√] Python 依赖已安装
)

REM 检查关键认证依赖包
poetry show python-jose >nul 2>&1
if errorlevel 1 (
    echo [警告] python-jose 未安装，正在更新依赖...
    poetry install
)

REM 检查 npm
where npm >nul 2>&1
if errorlevel 1 (
    echo [错误] npm 未安装，请先安装 Node.js
    echo        访问: https://nodejs.org/
    pause
    exit /b 1
)
echo [√] npm 已安装

REM 检查前端依赖
cd /d "%~dp0..\frontend"
if not exist "node_modules\" (
    echo [警告] 前端依赖未安装，正在安装...
    call npm install
    if errorlevel 1 (
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
) else (
    echo [√] 前端依赖已安装
)

REM 检查关键前端依赖
if not exist "node_modules\element-plus\" (
    echo [警告] element-plus 未安装，正在重新安装...
    call npm install
)

echo.
echo ================================
echo  依赖检查完成
echo ================================
echo.

REM ================================
REM 端口检查
REM ================================
echo [1/4] 检查端口占用...

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

echo [√] 端口检查通过
echo.

REM ================================
REM 启动服务
REM ================================

REM 设置镜像源
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

echo [2/4] 启动后端服务...
start "HotSpotAI-Backend" cmd /c "cd /d "%~dp0..\HotSpotAI" && poetry run python main.py 2>&1"

REM 等待后端启动
echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

REM 简单检查后端是否启动成功
timeout /t 1 /nobreak >nul
curl -s http://localhost:3000/api/health >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端可能启动较慢，请稍后检查...
) else (
    echo [√] 后端服务已启动
)

echo [3/4] 启动前端服务...
start "HotSpotAI-Frontend" /min cmd /c "cd /d "%~dp0..\frontend" && npm run serve"

REM 等待前端启动
timeout /t 8 /nobreak >nul

echo [√] 前端服务已启动
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
