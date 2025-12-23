#!/bin/bash
# AutoMediaBot 部署脚本 (Linux)
# 用途: 自动部署前后端服务

set -e

echo "================================"
echo "AutoMediaBot 部署脚本"
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python
check_python() {
    echo -e "${YELLOW}检查 Python 环境...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}错误: 未找到 Python3${NC}"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}Python 版本: $PYTHON_VERSION${NC}"
}

# 检查 Node.js
check_nodejs() {
    echo -e "${YELLOW}检查 Node.js 环境...${NC}"
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: 未找到 Node.js${NC}"
        exit 1
    fi
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}Node 版本: $NODE_VERSION${NC}"
}

# 安装后端依赖
install_backend_deps() {
    echo -e "${YELLOW}安装后端依赖...${NC}"
    cd AutoMediaBot

    # 检查是否使用 Poetry
    if command -v poetry &> /dev/null; then
        echo "使用 Poetry 安装依赖..."
        poetry install
    else
        echo "使用 pip 安装依赖..."
        pip3 install -r requirements.txt 2>/dev/null || pip3 install \
            fastapi uvicorn[standard] pydantic httpx beautifulsoup4 \
            playwright openai apscheduler
    fi

    # 安装 Playwright 浏览器
    echo -e "${YELLOW}安装 Playwright 浏览器...${NC}"
    export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
    python3 -m playwright install chromium

    cd ..
    echo -e "${GREEN}后端依赖安装完成${NC}"
}

# 安装前端依赖
install_frontend_deps() {
    echo -e "${YELLOW}安装前端依赖...${NC}"
    cd frontend

    if [ ! -d "node_modules" ]; then
        npm install
    fi

    cd ..
    echo -e "${GREEN}前端依赖安装完成${NC}"
}

# 构建前端
build_frontend() {
    echo -e "${YELLOW}构建前端...${NC}"
    cd frontend
    npm run build
    cd ..
    echo -e "${GREEN}前端构建完成${NC}"
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"

    # 杀掉可能存在的旧进程
    pkill -f "python.*main.py" || true
    pkill -f "uvicorn" || true

    # 启动后端
    echo "启动后端服务..."
    cd AutoMediaBot
    nohup python3 main.py > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../backend.pid
    cd ..

    sleep 3

    # 检查后端是否启动成功
    if curl -s http://localhost:3000/health > /dev/null; then
        echo -e "${GREEN}后端服务启动成功 (PID: $BACKEND_PID)${NC}"
    else
        echo -e "${RED}后端服务启动失败，请检查日志${NC}"
        cat logs/backend.log
        exit 1
    fi

    echo ""
    echo "================================"
    echo -e "${GREEN}部署完成！${NC}"
    echo "================================"
    echo "后端 API: http://localhost:3000"
    echo "API 文档: http://localhost:3000/docs"
    echo "后端 PID: $BACKEND_PID"
    echo ""
    echo "查看日志: tail -f logs/backend.log"
    echo "停止服务: kill $BACKEND_PID"
}

# 创建日志目录
mkdir -p logs

# 主流程
main() {
    case "${1:-deploy}" in
        deps)
            check_python
            check_nodejs
            install_backend_deps
            install_frontend_deps
            ;;
        build)
            build_frontend
            ;;
        deploy)
            check_python
            check_nodejs
            install_backend_deps
            install_frontend_deps
            start_services
            ;;
        start)
            start_services
            ;;
        stop)
            echo "停止服务..."
            if [ -f backend.pid ]; then
                kill $(cat backend.pid) 2>/dev/null || true
                rm backend.pid
                echo -e "${GREEN}服务已停止${NC}"
            else
                pkill -f "python.*main.py" || true
                echo -e "${GREEN}服务已停止${NC}"
            fi
            ;;
        restart)
            $0 stop
            sleep 2
            $0 start
            ;;
        *)
            echo "用法: $0 {deps|build|deploy|start|stop|restart}"
            echo ""
            echo "  deps    - 仅安装依赖"
            echo "  build   - 仅构建前端"
            echo "  deploy  - 完整部署（默认）"
            echo "  start   - 启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            exit 1
            ;;
    esac
}

main "$@"
