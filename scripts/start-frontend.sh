#!/bin/bash
# AutoMediaBot 前端启动脚本 (Linux)
# 用途: 启动 Vue.js 前端开发服务器

set -e

echo "================================"
echo "AutoMediaBot 前端启动"
echo "================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/frontend"

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "[错误] 未找到 Node.js，请先安装 Node.js"
    exit 1
fi

echo "Node 版本: $(node --version)"

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "[提示] 依赖未安装，正在安装..."
    npm install
fi

echo ""
echo "启动前端开发服务器..."
echo "前端地址: http://localhost:8080"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 启动开发服务器
npm run serve
