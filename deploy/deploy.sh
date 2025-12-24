#!/bin/bash
# HotSpotAI Ubuntu Server 自动部署脚本
# 适用于 Ubuntu 20.04 / 22.04

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
DEPLOY_DIR="/opt/hotspotai"
SERVICE_NAME="hotspotai"
NGINX_CONF="/etc/nginx/sites-available/hotspotai"
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "此脚本需要 root 权限运行"
        log_info "请使用: sudo bash deploy/deploy.sh"
        exit 1
    fi
}

# 检测 Ubuntu 版本
check_ubuntu() {
    if [[ ! -f /etc/os-release ]]; then
        log_error "无法检测操作系统版本"
        exit 1
    fi

    . /etc/os-release
    if [[ "$ID" != "ubuntu" ]]; then
        log_error "此脚本仅支持 Ubuntu 系统"
        exit 1
    fi

    VERSION_ID=$(echo $VERSION_ID | cut -d. -f1)
    if [[ $VERSION_ID -lt 20 ]]; then
        log_error "需要 Ubuntu 20.04 或更高版本"
        exit 1
    fi

    log_info "检测到 Ubuntu $VERSION_ID"
}

# 检查网络连接
check_network() {
    log_info "检查网络连接..."

    # 使用国内可访问的地址测试网络
    # 优先测试 DNS（阿里云公共 DNS）
    if ping -c 1 -W 2 223.5.5.5 &> /dev/null; then
        log_info "网络连接正常 ✓"
        return 0
    fi

    # 备用测试：腾讯公共 DNS
    if ping -c 1 -W 2 119.29.29.29 &> /dev/null; then
        log_info "网络连接正常 ✓"
        return 0
    fi

    # 备用测试：百度
    if ping -c 1 -W 2 www.baidu.com &> /dev/null; then
        log_info "网络连接正常 ✓"
        return 0
    fi

    # 所有测试都失败
    log_warn "无法连接到外网，部署可能失败"
    log_warn "请检查网络设置或配置代理"
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
}

# 更新系统包
update_system() {
    log_info "更新系统包..."
    apt-get update -qq
    apt-get upgrade -y -qq
}

# 安装 Python 和 Poetry
install_python() {
    log_info "检查 Python 版本..."

    if ! command -v python3 &> /dev/null; then
        log_info "安装 Python 3..."
        apt-get install -y python3 python3-pip python3-venv
    fi

    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
        log_error "需要 Python 3.8 或更高版本，当前版本: $PYTHON_VERSION"
        exit 1
    fi

    log_info "Python 版本: $PYTHON_VERSION ✓"

    # 安装 Poetry
    if ! command -v poetry &> /dev/null; then
        log_info "安装 Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        export PATH="$HOME/.local/bin:$PATH"
    else
        log_info "Poetry 已安装 ✓"
    fi
}

# 安装 Node.js 18
install_nodejs() {
    log_info "检查 Node.js 版本..."

    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d. -f1)
        if [[ $NODE_VERSION -ge 18 ]]; then
            log_info "Node.js 版本: $(node --version) ✓"
            return
        fi
    fi

    log_info "安装 Node.js 18 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
    log_info "Node.js 版本: $(node --version) ✓"
}

# 安装 Nginx
install_nginx() {
    log_info "安装 Nginx..."
    if ! command -v nginx &> /dev/null; then
        apt-get install -y nginx
    else
        log_info "Nginx 已安装 ✓"
    fi
}

# 安装系统依赖
install_dependencies() {
    log_info "安装系统依赖..."
    apt-get install -y \
        curl \
        git \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev \
        ca-certificates \
        gnupg \
        lsb-release
}

# 部署应用代码
deploy_app() {
    log_info "部署应用代码..."

    # 创建部署目录
    mkdir -p $DEPLOY_DIR

    # 复制代码
    log_info "复制应用文件到 $DEPLOY_DIR ..."
    rsync -av --progress \
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

    cd $DEPLOY_DIR
}

# 安装 Python 依赖
install_python_deps() {
    log_info "安装 Python 依赖..."
    cd $DEPLOY_DIR/HotSpotAI

    # 创建虚拟环境（如果不存在）
    if [[ ! -d .venv ]]; then
        poetry config virtualenvs.in-project true
        poetry install --no-interaction
    else
        log_info "虚拟环境已存在，跳过安装"
    fi

    # 安装 Playwright 浏览器
    log_info "安装 Playwright 浏览器..."
    poetry run playwright install chromium --with-deps
}

# 安装前端依赖并构建
build_frontend() {
    log_info "安装前端依赖..."
    cd $DEPLOY_DIR/frontend

    # 安装依赖
    npm install --production=false

    log_info "构建前端..."
    npm run build

    # 安装生产依赖
    npm ci --production
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."

    if [[ ! -f $DEPLOY_DIR/HotSpotAI/.env ]]; then
        # 非交互模式：直接复制并提示用户配置
        cp $DEPLOY_DIR/HotSpotAI/.env.example $DEPLOY_DIR/HotSpotAI/.env

        echo ""
        log_warn "环境配置文件已创建: $DEPLOY_DIR/HotSpotAI/.env"
        echo ""
        echo "=========================================="
        echo "  ⚠️  重要：请配置以下必需项"
        echo "=========================================="
        echo ""
        echo "请编辑配置文件设置 LLM_API_KEY："
        echo "  sudo nano $DEPLOY_DIR/HotSpotAI/.env"
        echo ""
        echo "必需配置项："
        echo "  - LLM_API_KEY     : 智谱 AI API Key（必需）"
        echo "  - JWT_SECRET_KEY : JWT 密钥（必需）"
        echo ""

        # 等待用户配置
        read -p "配置完成后按回车继续..." -r
        echo ""

        # 验证配置
        if grep -q "LLM_API_KEY=your_api_key_here" $DEPLOY_DIR/HotSpotAI/.env; then
            log_warn "LLM_API_KEY 未设置，服务可能无法正常工作"
            read -p "是否继续？(y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_error "部署已取消"
                exit 1
            fi
        fi
    else
        log_info ".env 文件已存在，跳过配置"
    fi
}

# 安装 systemd 服务
install_services() {
    log_info "安装 systemd 服务..."

    # 后端服务
    cp $DEPLOY_DIR/deploy/hotspotai-backend.service /etc/systemd/system/
    systemctl daemon-reload

    # 创建 hotspotai 用户（如果不存在）
    if ! id "$SERVICE_NAME" &>/dev/null; then
        useradd -r -s /bin/false -d $DEPLOY_DIR $SERVICE_NAME
        log_info "创建用户: $SERVICE_NAME"
    fi

    # 设置目录权限
    chown -R $SERVICE_NAME:$SERVICE_NAME $DEPLOY_DIR

    # 启用服务
    systemctl enable hotspotai-backend.service
    log_info "后端服务已启用"
}

# 配置 Nginx
setup_nginx() {
    log_info "配置 Nginx..."

    # 复制配置文件
    cp $DEPLOY_DIR/deploy/nginx.conf $NGINX_CONF

    # 创建符号链接
    if [[ ! -L /etc/nginx/sites-enabled/hotspotai ]]; then
        ln -sf $NGINX_CONF /etc/nginx/sites-enabled/hotspotai
    fi

    # 删除所有默认配置（包括 sites-enabled 和 conf.d）
    rm -f /etc/nginx/sites-enabled/default
    rm -f /etc/nginx/conf.d/default.conf
    rm -f /etc/nginx/conf.d/*.conf 2>/dev/null || true

    # 测试配置
    if ! nginx -t; then
        log_error "Nginx 配置测试失败"
        exit 1
    fi

    # 重启 Nginx
    systemctl restart nginx
    log_info "Nginx 已配置并重启"
}

# 启动服务
start_services() {
    log_info "启动服务..."

    # 启动后端服务
    systemctl restart hotspotai-backend.service

    # 等待服务启动
    sleep 3

    # 检查服务状态
    if systemctl is-active --quiet hotspotai-backend.service; then
        log_info "后端服务启动成功 ✓"
    else
        log_error "后端服务启动失败"
        journalctl -u hotspotai-backend.service -n 20 --no-pager
        exit 1
    fi
}

# 显示部署信息
show_info() {
    echo ""
    echo "=========================================="
    log_info "部署完成！"
    echo "=========================================="
    echo ""
    echo "部署目录: $DEPLOY_DIR"
    echo "访问地址: http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "服务管理命令:"
    echo "  查看状态: sudo systemctl status hotspotai-backend"
    echo "  重启服务: sudo systemctl restart hotspotai-backend"
    echo "  查看日志: sudo journalctl -u hotspotai-backend -f"
    echo "  重启 Nginx: sudo systemctl restart nginx"
    echo ""
    echo "配置文件:"
    echo "  环境变量: $DEPLOY_DIR/HotSpotAI/.env"
    echo "  Nginx 配置: $NGINX_CONF"
    echo ""
    echo "如需更新代码，请运行:"
    echo "  sudo bash $DEPLOY_DIR/deploy/update.sh"
    echo ""
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "  HotSpotAI Ubuntu Server 部署脚本"
    echo "=========================================="
    echo ""

    check_root
    check_ubuntu
    check_network

    log_info "开始部署..."
    echo ""

    update_system
    install_dependencies
    install_python
    install_nodejs
    install_nginx
    deploy_app
    install_python_deps
    build_frontend
    setup_environment
    install_services
    setup_nginx
    start_services
    show_info
}

# 运行主函数
main "$@"
