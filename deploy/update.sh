#!/bin/bash
# HotSpotAI 更新脚本
# 用法: sudo bash update.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置
DEPLOY_DIR="/opt/hotspotai"
BACKUP_DIR="/opt/hotspotai_backup_$(date +%Y%m%d_%H%M%S)"

# 检查 root 权限
if [[ $EUID -ne 0 ]]; then
    log_error "此脚本需要 root 权限运行"
    log_info "请使用: sudo bash update.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo "  HotSpotAI 更新脚本"
echo "=========================================="
echo ""

# 检查部署目录是否存在
if [[ ! -d $DEPLOY_DIR ]]; then
    log_error "部署目录不存在: $DEPLOY_DIR"
    log_info "请先运行部署脚本: sudo bash deploy/deploy.sh"
    exit 1
fi

# 确认更新
read -p "是否确认更新 HotSpotAI？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "已取消更新"
    exit 0
fi

# 1. 备份当前配置
log_info "备份当前配置..."
mkdir -p $BACKUP_DIR
cp -r $DEPLOY_DIR/HotSpotAI/.env $BACKUP_DIR/ 2>/dev/null || true
log_info "配置已备份到: $BACKUP_DIR"

# 2. 拉取最新代码
log_info "更新代码..."
cd $DEPLOY_DIR

# 如果是 git 仓库，拉取最新代码
if [[ -d .git ]]; then
    git fetch origin
    git reset --hard origin/main
else
    log_warn "不是 git 仓库，跳过代码更新"
fi

# 3. 更新 Python 依赖
log_info "更新 Python 依赖..."
cd $DEPLOY_DIR/HotSpotAI
poetry install --no-interaction

# 4. 更新前端
log_info "更新前端..."
cd $DEPLOY_DIR/frontend
npm install --production=false
npm run build
npm ci --production

# 5. 恢复配置
log_info "恢复配置..."
cp $BACKUP_DIR/.env $DEPLOY_DIR/HotSpotAI/.env 2>/dev/null || true

# 6. 重启服务
log_info "重启服务..."
systemctl restart hotspotai-backend.service

# 等待服务启动
sleep 3

# 7. 检查服务状态
log_info "检查服务状态..."
if systemctl is-active --quiet hotspotai-backend.service; then
    log_info "后端服务运行正常 ✓"
else
    log_error "后端服务启动失败"
    log_info "查看日志: sudo journalctl -u hotspotai-backend -n 50"
    exit 1
fi

# 8. 清理旧备份（保留最近 3 个）
log_info "清理旧备份..."
ls -dt /opt/hotspotai_backup_* 2>/dev/null | tail -n +4 | xargs rm -rf 2>/dev/null || true

echo ""
echo "=========================================="
log_info "更新完成！"
echo "=========================================="
echo ""
echo "查看日志: sudo journalctl -u hotspotai-backend -f"
echo ""
