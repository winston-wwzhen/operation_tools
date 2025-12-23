#!/bin/bash
# AutoMediaBot 统一启动脚本 (Linux)
# 用途: 同时启动前后端服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================"
echo "  AutoMediaBot 启动脚本"
echo "================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查端口
check_port() {
    if netstat -tuln 2>/dev/null | grep -q ":$1 "; then
        echo -e "${RED}错误: 端口 $1 已被占用${NC}"
        exit 1
    fi
}

check_port 3000
check_port 8080

# 设置镜像源
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/

# 创建日志目录
mkdir -p logs

# 启动后端
echo -e "${YELLOW}[1/2] 启动后端服务...${NC}"
cd AutoMediaBot
nohup python3 main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

# 等待后端启动
sleep 5

# 检查后端
if curl -s http://localhost:3000/health > /dev/null; then
    echo -e "${GREEN}后端启动成功 (PID: $BACKEND_PID)${NC}"
else
    echo -e "${RED}后端启动失败${NC}"
    cat logs/backend.log
    exit 1
fi

# 启动前端
echo -e "${YELLOW}[2/2] 启动前端服务...${NC}"
cd frontend
nohup npm run serve > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

sleep 8

# 显示结果
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
echo "  停止服务:     ./stop.sh"
echo ""

# 尝试打开浏览器 (Linux Desktop)
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8080 &>/dev/null &
fi
