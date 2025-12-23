#!/bin/bash

# === 配置区 ===
BASE_DIR=$(cd "$(dirname "$0")"; pwd)
VENV_DIR="$BASE_DIR/venv"
LOG_FILE="$BASE_DIR/run.log"
PID_FILE="$BASE_DIR/service.pid"
# ============

# 1. 环境准备函数
prepare_env() {
    # 检查并创建虚拟环境
    if [ ! -d "$VENV_DIR" ]; then
        echo "[INFO] 未检测到虚拟环境，正在创建..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # 激活虚拟环境 (使用 . 兼容 sh)
    . "$VENV_DIR/bin/activate"

    # 检查依赖 (仅当requirements存在时)
    if [ -f "requirements.txt" ]; then
        # 使用清华源加速
        pip install -r requirements.txt -i > /dev/null 2>&1
    fi

    # 检查 Playwright 浏览器
    if [ ! -d "$HOME/.cache/ms-playwright" ] && [ ! -d "/root/.cache/ms-playwright" ]; then
        echo "[INFO] 正在安装 Playwright 浏览器..."
        playwright install chromium
    fi
}

# 2. 启动服务函数
start_service() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null; then
            echo "[WARN] 服务已在运行 (PID: $OLD_PID)。请勿重复启动。"
            return
        else
            rm "$PID_FILE"
        fi
    fi

    echo "[INFO] 正在检查环境并启动..."
    prepare_env

    # 环境变量会由 python-dotenv 自动读取 .env 文件
    nohup python main.py > "$LOG_FILE" 2>&1 &
    
    NEW_PID=$!
    echo "$NEW_PID" > "$PID_FILE"
    echo "[SUCCESS] 服务已启动！PID: $NEW_PID"
    echo "[INFO] 日志文件: $LOG_FILE"
}

# 3. 停止服务函数
stop_service() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null; then
            echo "[INFO] 正在停止服务 (PID: $PID)..."
            kill "$PID"
            # 等待进程退出
            while ps -p "$PID" > /dev/null; do sleep 1; done
            echo "[SUCCESS] 服务已停止。"
        else
            echo "[INFO] 进程不存在，清理残留 PID 文件。"
        fi
        rm "$PID_FILE"
    else
        echo "[WARN] 未找到运行中的服务 (PID文件不存在)。"
    fi
}

# 4. 安装系统依赖函数 (修复缺库问题)
install_system_deps() {
    echo "[INFO] 正在准备环境..."
    prepare_env
    echo "[INFO] 正在安装系统级依赖 (需要 root 权限，可能耗时较长)..."
    playwright install-deps chromium
    echo "[SUCCESS] 系统依赖安装完成！"
}

# === 主逻辑 ===
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        stop_service
        sleep 1
        start_service
        ;;
    install)
        install_system_deps
        ;;
    *)
        echo "用法: bash $0 {start|stop|restart|install}"
        echo "首次部署或报错缺库时，请运行: bash $0 install"
        start_service
        ;;
esac
