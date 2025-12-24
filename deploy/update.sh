#!/bin/bash
# HotSpotAI 更新脚本
# 支持从任意目录运行：sudo bash update.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 配置
DEPLOY_DIR="/opt/hotspotai"
BACKUP_DIR="/opt/hotspotai_backup_$(date +%Y%m%d_%H%M%S)"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 检查 root 权限
if [[ $EUID -ne 0 ]]; then
    log_error "此脚本需要 root 权限运行"
    log_info "请使用: sudo bash deploy/update.sh"
    exit 1
fi

echo ""
echo "=========================================="
echo "  HotSpotAI 更新脚本"
echo "=========================================="
echo ""

log_info "当前目录: $CURRENT_DIR"
log_info "部署目录: $DEPLOY_DIR"
echo ""

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

# 备份环境配置
if [[ -f $DEPLOY_DIR/HotSpotAI/.env ]]; then
    cp $DEPLOY_DIR/HotSpotAI/.env $BACKUP_DIR/
fi

# 备份 Nginx 配置
if [[ -f /etc/nginx/sites-available/hotspotai ]]; then
    cp /etc/nginx/sites-available/hotspotai $BACKUP_DIR/
fi

log_info "配置已备份到: $BACKUP_DIR"

# 2. 更新代码
log_info "更新代码..."

# 如果部署目录是 git 仓库，尝试拉取
if [[ -d $DEPLOY_DIR/.git ]]; then
    log_info "从 git 拉取最新代码..."
    cd $DEPLOY_DIR
    git fetch origin
    git reset --hard origin/main
else
    # 从当前目录同步代码
    log_info "从当前目录同步代码..."
    rsync -av \
        --exclude 'node_modules' \
        --exclude '.git' \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.venv' \
        --exclude 'frontend/dist' \
        --exclude 'frontend/node_modules' \
        --exclude 'data.db' \
        --exclude 'logs' \
        $CURRENT_DIR/ $DEPLOY_DIR/
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

# 5. 恢复配置
log_info "恢复配置..."
if [[ -f $BACKUP_DIR/.env ]]; then
    cp $BACKUP_DIR/.env $DEPLOY_DIR/HotSpotAI/.env
    log_info "环境配置已恢复"
else
    log_warn "未找到备份的 .env 文件，请手动配置"
fi

# 6. 更新 Nginx 配置
log_info "更新 Nginx 配置..."
if [[ -f $DEPLOY_DIR/deploy/nginx.conf ]]; then
    cp $DEPLOY_DIR/deploy/nginx.conf /etc/nginx/sites-available/hotspotai

    # 确保符号链接存在
    if [[ ! -L /etc/nginx/sites-enabled/hotspotai ]]; then
        ln -sf /etc/nginx/sites-available/hotspotai /etc/nginx/sites-enabled/hotspotai
    fi

    # 删除冲突的默认配置
    rm -f /etc/nginx/sites-enabled/default
    rm -f /etc/nginx/conf.d/default.conf
    rm -f /etc/nginx/conf.d/*.conf 2>/dev/null || true

    # 测试配置
    if nginx -t; then
        systemctl reload nginx
        log_info "Nginx 配置已更新"
    else
        log_error "Nginx 配置测试失败，恢复备份..."
        if [[ -f $BACKUP_DIR/hotspotai ]]; then
            cp $BACKUP_DIR/hotspotai /etc/nginx/sites-available/hotspotai
            systemctl reload nginx
        fi
    fi
fi

# 7. 重启服务
log_info "重启服务..."
systemctl restart hotspotai-backend.service

# 等待服务启动
sleep 3

# 8. 验证服务
log_info "验证服务..."

# 检查后端服务状态
if systemctl is-active --quiet hotspotai-backend.service; then
    log_info "后端服务运行正常 ✓"
else
    log_error "后端服务启动失败"
    log_info "查看日志: sudo journalctl -u hotspotai-backend -n 50"

    # 尝试恢复
    read -p "是否回滚更新？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "正在回滚..."
        # 这里可以添加回滚逻辑
    fi
    exit 1
fi

# 检查 API 端点
if curl -s http://localhost:3000/api/health > /dev/null; then
    log_info "API 端点响应正常 ✓"
else
    log_warn "API 端点无响应，请检查后端日志"
fi

# 9. 清理旧备份（保留最近 3 个）
log_info "清理旧备份..."
ls -dt /opt/hotspotai_backup_* 2>/dev/null | tail -n +4 | xargs rm -rf 2>/dev/null || true

echo ""
echo "=========================================="
log_info "更新完成！"
echo "=========================================="
echo ""
echo "部署目录: $DEPLOY_DIR"
echo "备份目录: $BACKUP_DIR"
echo ""
echo "服务管理:"
echo "  查看状态: sudo systemctl status hotspotai-backend"
echo "  查看日志: sudo journalctl -u hotspotai-backend -f"
echo "  重启服务: sudo systemctl restart hotspotai-backend"
echo ""
