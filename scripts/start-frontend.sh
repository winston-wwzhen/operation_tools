#!/bin/bash
# HotSpotAI 前端启动脚本 (Linux/macOS)
# 用途: 启动 Vue.js 前端开发服务器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "================================"
echo "  HotSpotAI 前端启动"
echo "================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../frontend"

# ================================
# 依赖检查
# ================================

echo -e "${YELLOW}[1/3]${NC} 检查 Node.js 环境..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未找到 Node.js"
    echo "        访问: https://nodejs.org/"
    exit 1
fi
echo -e "${GREEN}[√]${NC} Node.js 已安装 ($(node --version))"

echo ""
echo -e "${YELLOW}[2/3]${NC} 检查 npm..."
if ! command -v npm &> /dev/null; then
    echo -e "${RED}[错误]${NC} npm 未找到"
    exit 1
fi
echo -e "${GREEN}[√]${NC} npm 已安装 ($(npm --version))"

echo ""
echo -e "${YELLOW}[3/3]${NC} 检查前端依赖..."

# 检查 package.json
if [ ! -f "package.json" ]; then
    echo -e "${RED}[错误]${NC} 未找到 package.json"
    exit 1
fi

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}[警告]${NC} 前端依赖未安装，正在安装..."
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误]${NC} npm install 失败"
        exit 1
    fi
    echo -e "${GREEN}[√]${NC} 依赖安装完成"
else
    echo -e "${GREEN}[√]${NC} 前端依赖已安装"
fi

# 检查关键依赖
MISSING_DEPS=0
for dep in vue element-plus vue-router axios marked; do
    if [ ! -d "node_modules/$dep" ]; then
        echo -e "${YELLOW}[警告]${NC} $dep 未安装，正在重新安装..."
        npm install
        MISSING_DEPS=1
        break
    fi
done

if [ $MISSING_DEPS -eq 0 ]; then
    echo -e "${GREEN}[√]${NC} 所有关键依赖已安装"
fi

# 检查端口占用
echo ""
echo "检查端口占用..."
if netstat -tuln 2>/dev/null | grep -q ":8080 "; then
    echo -e "${RED}[错误]${NC} 端口 8080 已被占用"
    echo "        请先关闭占用该端口的进程"
    exit 1
fi

echo ""
echo "================================"
echo "  依赖检查完成，正在启动服务..."
echo "================================"
echo ""
echo "前端地址:     http://localhost:8080"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动开发服务器
npm run serve
