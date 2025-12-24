#!/bin/bash
# HotSpotAI 统一启动脚本 (Linux/macOS)
# 用途: 同时启动前后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "================================"
echo "  HotSpotAI 启动脚本"
echo "================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

# ================================
# 依赖检查函数
# ================================

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}[√]${NC} $1 已安装"
        return 0
    else
        echo -e "${RED}[✗]${NC} $1 未安装"
        return 1
    fi
}

check_poetry() {
    if ! command -v poetry &> /dev/null; then
        echo -e "${RED}[错误]${NC} Poetry 未安装"
        echo "        访问: https://python-poetry.org/docs/#installation"
        exit 1
    fi
    echo -e "${GREEN}[√]${NC} Poetry 已安装"
}

check_python_deps() {
    cd HotSpotAI
    if ! poetry show fastapi &> /dev/null; then
        echo -e "${YELLOW}[警告]${NC} Python 依赖未安装，正在安装..."
        poetry install
        if [ $? -ne 0 ]; then
            echo -e "${RED}[错误]${NC} Poetry 安装失败"
            exit 1
        fi
    else
        echo -e "${GREEN}[√]${NC} Python 依赖已安装"
    fi

    # 检查关键认证依赖包
    if ! poetry show python-jose &> /dev/null; then
        echo -e "${YELLOW}[警告]${NC} python-jose 未安装，正在更新依赖..."
        poetry install
    fi
    cd ..
}

check_npm() {
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}[错误]${NC} npm 未安装"
        echo "        访问: https://nodejs.org/"
        exit 1
    fi
    echo -e "${GREEN}[√]${NC} npm 已安装"
}

check_frontend_deps() {
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}[警告]${NC} 前端依赖未安装，正在安装..."
        npm install
        if [ $? -ne 0 ]; then
            echo -e "${RED}[错误]${NC} npm install 失败"
            exit 1
        fi
    else
        echo -e "${GREEN}[√]${NC} 前端依赖已安装"
    fi

    # 检查关键前端依赖
    if [ ! -d "node_modules/element-plus" ]; then
        echo -e "${YELLOW}[警告]${NC} element-plus 未安装，正在重新安装..."
        npm install
    fi
    cd ..
}

check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$1 "; then
        echo -e "${RED}[错误]${NC} 端口 $1 已被占用"
        echo "        请运行 ./scripts/stop.sh 停止服务"
        exit 1
    fi
}

# ================================
# 执行检查
# ================================

echo -e "${BLUE}[0/4] 检查依赖...${NC}"
check_poetry
check_python_deps
check_npm
check_frontend_deps

echo ""
echo "================================"
echo "  依赖检查完成"
echo "================================"
echo ""

echo -e "${BLUE}[1/4] 检查端口占用...${NC}"
check_port 3000
check_port 8080
echo -e "${GREEN}[√]${NC} 端口检查通过"
echo ""

# ================================
# 启动服务
# ================================

# 设置镜像源
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 创建日志目录
mkdir -p logs

echo -e "${BLUE}[2/4] 启动后端服务...${NC}"
cd HotSpotAI
nohup poetry run python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

# 等待后端启动
sleep 5

# 检查后端健康
if curl -s http://localhost:3000/api/health > /dev/null 2>&1 || \
   curl -s http://localhost:3000/docs > /dev/null 2>&1 || \
   kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}[√]${NC} 后端服务已启动 (PID: $BACKEND_PID)"
else
    echo -e "${YELLOW}[警告]${NC} 后端可能启动较慢，请稍后检查..."
    echo "        查看日志: tail -f logs/backend.log"
fi

echo -e "${BLUE}[3/4] 启动前端服务...${NC}"
cd frontend
nohup npm run serve > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

sleep 8

# 检查前端进程
if kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${GREEN}[√]${NC} 前端服务已启动 (PID: $FRONTEND_PID)"
else
    echo -e "${YELLOW}[警告]${NC} 前端启动可能有问题"
    echo "        查看日志: tail -f logs/frontend.log"
fi

echo ""
echo "================================"
echo -e "${GREEN}  服务启动完成！${NC}"
echo "================================"
echo ""
echo "  后端 API:     http://localhost:3000"
echo "  API 文档:     http://localhost:3000/docs"
echo "  前端界面:     http://localhost:8080"
echo ""
echo "  后端 PID:     $BACKEND_PID"
echo "  前端 PID:     $FRONTEND_PID"
echo ""
echo "  查看后端日志: tail -f logs/backend.log"
echo "  查看前端日志: tail -f logs/frontend.log"
echo "  停止服务:     ./scripts/stop.sh"
echo ""

# 尝试打开浏览器
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080 &>/dev/null &
elif command -v open &> /dev/null; then
    open http://localhost:8080 &>/dev/null &
fi
