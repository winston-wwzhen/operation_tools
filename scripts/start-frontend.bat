@echo off
REM HotSpotAI 前端启动脚本 (Windows)
REM 用途: 启动 Vue.js 前端开发服务器
chcp 65001 >nul

echo ================================
echo  HotSpotAI 前端启动
echo ================================
echo.

cd /d "%~dp0..\frontend"

REM ================================
REM 依赖检查
REM ================================
echo [1/3] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js
    echo        访问: https://nodejs.org/
    pause
    exit /b 1
)
echo [√] Node.js 已安装

echo.
echo [2/3] 检查 npm...
npm --version >nul 2>&1
if errorlevel 1 (
    echo [错误] npm 未找到
    pause
    exit /b 1
)
echo [√] npm 已安装

echo.
echo [3/3] 检查前端依赖...

REM 检查 package.json
if not exist "package.json" (
    echo [错误] 未找到 package.json
    pause
    exit /b 1
)

REM 检查 node_modules
if not exist "node_modules\" (
    echo [警告] 前端依赖未安装，正在安装...
    call npm install
    if errorlevel 1 (
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
    echo [√] 依赖安装完成
) else (
    echo [√] 前端依赖已安装
)

REM 检查关键依赖
if not exist "node_modules\vue\" (
    echo [警告] Vue 未安装，正在重新安装...
    call npm install
)

if not exist "node_modules\element-plus\" (
    echo [警告] element-plus 未安装，正在重新安装...
    call npm install
)

if not exist "node_modules\vue-router\" (
    echo [警告] vue-router 未安装，正在重新安装...
    call npm install
)

if not exist "node_modules\axios\" (
    echo [警告] axios 未安装，正在重新安装...
    call npm install
)

REM 检查端口占用
echo.
echo 检查端口占用...
netstat -ano | findstr "LISTENING" | findstr ":8080" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 8080 已被占用
    echo        请先关闭占用该端口的进程
    pause
    exit /b 1
)

echo.
echo ================================
echo  依赖检查完成，正在启动服务...
echo ================================
echo.
echo 前端地址:     http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务
echo.

call npm run serve
