@echo off
REM HotSpotAI 停止服务脚本 (Windows)
chcp 65001 >nul

echo ================================
echo  HotSpotAI 停止服务
echo ================================
echo.

echo [1/3] 正在停止后端服务 (端口 3000)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":3000"') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo   - 已停止端口 3000 上的服务 (PID: %%a)
    )
)

echo.
echo [2/3] 正在停止前端服务 (端口 8080)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":8080"') do (
    taskkill /F /PID %%a >nul 2>&1
    if not errorlevel 1 (
        echo   - 已停止端口 8080 上的服务 (PID: %%a)
    )
)

echo.
echo [3/3] 额外清理：按窗口标题清理...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq HotSpotAI-Backend*" >nul 2>&1
taskkill /F /IM node.exe /FI "WINDOWTITLE eq HotSpotAI-Frontend*" >nul 2>&1

echo.
echo 清理 PID 文件...
del backend.pid 2>nul
del frontend.pid 2>nul

echo.
echo 等待进程完全退出...
timeout /t 2 /nobreak >nul

echo.
echo ================================
echo  服务已停止
echo ================================
pause
