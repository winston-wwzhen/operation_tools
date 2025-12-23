#!/bin/bash
# AutoMediaBot 停止服务脚本 (Linux)

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================"
echo "  AutoMediaBot 停止服务"
echo "================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 停止后端
echo -e "${YELLOW}停止后端服务...${NC}"
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null && echo -e "${GREEN}后端已停止${NC}" || echo "后端未运行"
    rm -f backend.pid
else
    pkill -f "python.*main.py" && echo -e "${GREEN}后端已停止${NC}" || echo "后端未运行"
fi

# 停止前端
echo -e "${YELLOW}停止前端服务...${NC}"
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null && echo -e "${GREEN}前端已停止${NC}" || echo "前端未运行"
    rm -f frontend.pid
else
    pkill -f "npm run serve" && echo -e "${GREEN}前端已停止${NC}" || echo "前端未运行"
fi

echo ""
echo "================================"
echo -e "${GREEN}  服务已停止${NC}"
echo "================================"
