# HotSpotAI Ubuntu Server 部署指南

## 目录

- [系统要求](#系统要求)
- [快速部署](#快速部署)
- [手动部署](#手动部署)
- [配置说明](#配置说明)
- [服务管理](#服务管理)
- [故障排查](#故障排查)
- [更新升级](#更新升级)

## 系统要求

- **操作系统**: Ubuntu 20.04 / 22.04 LTS
- **内存**: 最低 2GB，推荐 4GB+
- **磁盘**: 最低 10GB 可用空间
- **网络**: 需要访问外网（安装依赖、API 调用）

## 快速部署

### 方式一：从 Git 仓库部署

```bash
# 1. 克隆代码
git clone https://github.com/your-repo/operation_tools.git
cd operation_tools

# 2. 运行部署脚本
sudo bash deploy/deploy.sh
```

### 方式二：使用 curl 一键部署

```bash
curl -fsSL https://raw.githubusercontent.com/your-repo/operation_tools/main/deploy/deploy.sh | sudo bash
```

部署脚本会自动：
1. 检测系统环境
2. 安装所有依赖（Python、Node.js、Nginx、Poetry）
3. 部署应用代码到 `/opt/hotspotai`
4. 构建前端静态文件
5. 配置 systemd 服务
6. 配置 Nginx 反向代理
7. 启动所有服务

## 手动部署

如果自动部署脚本无法使用，可以按照以下步骤手动部署：

### 1. 安装系统依赖

```bash
sudo apt-get update
sudo apt-get install -y curl git build-essential python3 python3-pip python3-venv nginx
```

### 2. 安装 Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

### 3. 安装 Node.js 18

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 4. 部署代码

```bash
# 创建部署目录
sudo mkdir -p /opt/hotspotai
sudo chown $USER:$USER /opt/hotspotai

# 复制代码
cp -r . /opt/hotspotai/
cd /opt/hotspotai
```

### 5. 安装 Python 依赖

```bash
cd HotSpotAI
poetry config virtualenvs.in-project true
poetry install

# 安装 Playwright 浏览器
poetry run playwright install chromium --with-deps
```

### 6. 构建前端

```bash
cd ../frontend
npm install
npm run build
```

### 7. 配置环境变量

```bash
cd ../HotSpotAI
cp .env.example .env
nano .env  # 编辑配置文件，设置 LLM_API_KEY
```

### 8. 创建 systemd 服务

```bash
# 后端服务
sudo cp deploy/hotspotai-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable hotspotai-backend.service

# 创建用户
sudo useradd -r -s /bin/false -d /opt/hotspotai hotspotai
sudo chown -R hotspotai:hotspotai /opt/hotspotai
```

### 9. 配置 Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/hotspotai
sudo ln -s /etc/nginx/sites-available/hotspotai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 10. 启动服务

```bash
sudo systemctl start hotspotai-backend
```

## 配置说明

### 环境变量

编辑 `/opt/hotspotai/HotSpotAI/.env` 文件：

```bash
# ============ 必需配置 ============
LLM_API_KEY=your_zhipu_ai_api_key_here

# ============ 可选配置 ============
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
LLM_MODEL=glm-4
LLM_TIMEOUT=600

# JWT 认证
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# 数据库（默认 SQLite）
DATABASE_URL=sqlite:///./data.db

# 定时任务
SCHEDULE_CRON=0 */2 * * *
AUTO_RUN=true

# 爬虫配置
TOPIC_LIMIT=10
REQUEST_TIMEOUT=30

# 服务配置
HOST=0.0.0.0
PORT=3000
DEBUG=false
LOG_LEVEL=INFO
```

### LLM API Key

智谱 AI API Key 获取地址：https://open.bigmodel.cn/

## 服务管理

### 查看服务状态

```bash
# 后端服务
sudo systemctl status hotspotai-backend

# 查看所有相关服务
sudo systemctl status hotspotai-*
```

### 启动/停止/重启

```bash
# 启动
sudo systemctl start hotspotai-backend

# 停止
sudo systemctl stop hotspotai-backend

# 重启
sudo systemctl restart hotspotai-backend
```

### 查看日志

```bash
# 实时查看日志
sudo journalctl -u hotspotai-backend -f

# 查看最近 100 行日志
sudo journalctl -u hotspotai-backend -n 100

# 查看今天的服务日志
sudo journalctl -u hotspotai-backend --since today
```

### Nginx 管理

```bash
# 查看状态
sudo systemctl status nginx

# 重启
sudo systemctl restart nginx

# 重新加载配置
sudo systemctl reload nginx

# 测试配置
sudo nginx -t
```

## 故障排查

### 服务无法启动

1. 查看服务状态
```bash
sudo systemctl status hotspotai-backend
```

2. 查看详细日志
```bash
sudo journalctl -u hotspotai-backend -n 50 --no-pager
```

3. 检查端口占用
```bash
sudo netstat -tlnp | grep 3000
```

### 502 Bad Gateway

1. 检查后端服务是否运行
```bash
sudo systemctl status hotspotai-backend
curl http://127.0.0.1:3000/health
```

2. 检查 Nginx 配置
```bash
sudo nginx -t
```

### 前端页面无法访问

1. 检查前端文件是否存在
```bash
ls -la /opt/hotspotai/frontend/dist
```

2. 检查 Nginx 配置中的路径是否正确

3. 查看 Nginx 错误日志
```bash
sudo tail -f /var/log/nginx/hotspotai_error.log
```

### API 调用失败

1. 检查 LLM_API_KEY 是否正确配置
```bash
cat /opt/hotspotai/HotSpotAI/.env | grep LLM_API_KEY
```

2. 测试 API 连接
```bash
curl http://127.0.0.1:3000/api/status
```

3. 查看后端日志
```bash
sudo journalctl -u hotspotai-backend -f
```

## 更新升级

### 使用更新脚本

```bash
cd /opt/hotspotai
sudo bash deploy/update.sh
```

### 手动更新

```bash
cd /opt/hotspotai

# 1. 备份配置
sudo cp HotSpotAI/.env /tmp/.env.backup

# 2. 拉取最新代码
sudo git pull origin main

# 3. 更新依赖
cd HotSpotAI
poetry install

# 4. 重新构建前端
cd ../frontend
npm install
npm run build

# 5. 恢复配置
sudo cp /tmp/.env.backup HotSpotAI/.env

# 6. 重启服务
sudo systemctl restart hotspotai-backend
```

## 目录结构

部署后的目录结构：

```
/opt/hotspotai/
├── HotSpotAI/                # 后端代码
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── scrapers/
│   ├── .env                  # 环境配置
│   ├── .venv/                # Python 虚拟环境
│   └── data.db               # SQLite 数据库
│
├── frontend/
│   └── dist/                 # 前端构建产物
│       ├── index.html
│       └── static/
│
├── deploy/                   # 部署脚本
│   ├── deploy.sh
│   ├── update.sh
│   ├── setup-env.sh
│   └── ...
│
└── logs/                     # 日志目录（如果配置）
```

## 常用命令速查

```bash
# 部署
sudo bash deploy/deploy.sh

# 更新
cd /opt/hotspotai && sudo bash deploy/update.sh

# 服务状态
sudo systemctl status hotspotai-backend

# 查看日志
sudo journalctl -u hotspotai-backend -f

# 重启服务
sudo systemctl restart hotspotai-backend

# 编辑配置
sudo nano /opt/hotspotai/HotSpotAI/.env

# 重启 Nginx
sudo systemctl restart nginx

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/hotspotai_error.log
```

## 安全建议

1. **配置防火墙**
```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **使用 HTTPS**（生产环境推荐）
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

3. **定期更新系统**
```bash
sudo apt-get update && sudo apt-get upgrade -y
```

4. **配置日志轮转**
systemd journald 自动管理日志，无需额外配置。

## 卸载

```bash
# 停止并禁用服务
sudo systemctl stop hotspotai-backend
sudo systemctl disable hotspotai-backend

# 删除服务文件
sudo rm /etc/systemd/system/hotspotai-*.service
sudo systemctl daemon-reload

# 删除 Nginx 配置
sudo rm /etc/nginx/sites-enabled/hotspotai
sudo rm /etc/nginx/sites-available/hotspotai
sudo systemctl restart nginx

# 删除应用目录
sudo rm -rf /opt/hotspotai

# 删除用户
sudo userdel hotspotai
```
