#!/bin/bash
# HotSpotAI 环境变量配置脚本
# 用法: bash setup-env.sh [目标目录] [--non-interactive]

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

# 解析参数
TARGET_DIR="."
INTERACTIVE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --non-interactive)
            INTERACTIVE=false
            shift
            ;;
        *)
            TARGET_DIR="$1"
            shift
            ;;
    esac
done

# 检查 .env.example 是否存在
ENV_EXAMPLE="$TARGET_DIR/.env.example"
ENV_OUTPUT="$TARGET_DIR/.env"

if [[ ! -f "$ENV_EXAMPLE" ]]; then
    log_error "未找到 .env.example 文件: $ENV_EXAMPLE"
    exit 1
fi

# 非交互模式直接复制
if [[ $INTERACTIVE == false ]]; then
    cp "$ENV_EXAMPLE" "$ENV_OUTPUT"
    log_info "配置文件已创建: $ENV_OUTPUT"
    log_warn "请手动编辑配置文件，设置 LLM_API_KEY 和 JWT_SECRET_KEY"
    exit 0
fi

echo ""
echo "=========================================="
echo "  HotSpotAI 环境变量配置"
echo "=========================================="
echo ""
log_info "配置文件将保存到: $ENV_OUTPUT"
echo ""

# 询问是否使用交互式配置
read -p "是否使用交互式配置？(Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    # 交互式配置
    INTERACTIVE=true
else
    # 使用 .env.example 的默认值
    INTERACTIVE=false
fi

# 读取 .env.example 并生成 .env
log_info "生成环境配置文件..."

# 创建临时文件
TEMP_FILE=$(mktemp)

# 处理 .env.example
while IFS='=' read -r key value; do
    # 跳过注释和空行
    if [[ $key =~ ^#.*$ ]] || [[ -z $key ]]; then
        echo "$key$value" >> $TEMP_FILE
        continue
    fi

    # 去掉注释
    key=${key%%#*}
    key=$(echo $key | xargs)  # 去掉空格

    if [[ -z $key ]]; then
        echo "$key$value" >> $TEMP_FILE
        continue
    fi

    if [[ $INTERACTIVE == true ]]; then
        # 交互式输入
        DEFAULT_VALUE=$(echo $value | xargs)

        # 根据变量类型设置提示
        case $key in
            *SECRET*|*PASSWORD*|*KEY*)
                PROMPT_TYPE="password"
                ;;
            *TOKEN*)
                PROMPT_TYPE="password"
                ;;
            true|false)
                PROMPT_TYPE="boolean"
                ;;
            *)
                PROMPT_TYPE="text"
                ;;
        esac

        # 显示提示
        echo ""
        echo -e "${BLUE}配置: $key${NC}"

        # 获取输入
        if [[ $PROMPT_TYPE == "password" ]]; then
            read -s -p "请输入值 [默认: $DEFAULT_VALUE]: " INPUT_VALUE
            echo
        elif [[ $PROMPT_TYPE == "boolean" ]]; then
            read -p "请输入值 (true/false) [默认: $DEFAULT_VALUE]: " INPUT_VALUE
        else
            read -p "请输入值 [默认: $DEFAULT_VALUE]: " INPUT_VALUE
        fi

        # 使用输入值或默认值
        if [[ -z $INPUT_VALUE ]]; then
            FINAL_VALUE="$DEFAULT_VALUE"
        else
            FINAL_VALUE="$INPUT_VALUE"
        fi

        echo "$key=$FINAL_VALUE" >> $TEMP_FILE
    else
        # 使用默认值
        echo "$key$value" >> $TEMP_FILE
    fi
done < "$ENV_EXAMPLE"

# 移动到目标位置
mv $TEMP_FILE "$ENV_OUTPUT"

echo ""
log_info "配置文件已生成: $ENV_OUTPUT"
echo ""

# 检查必需的配置
log_info "验证配置..."

REQUIRED_VARS=("LLM_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if ! grep -q "^${var}=" "$ENV_OUTPUT" || grep -q "^${var}=.*your_.*here" "$ENV_OUTPUT"; then
        MISSING_VARS+=("$var")
    fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
    log_warn "以下必需配置项未设置或使用了默认占位符:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    log_warn "请手动编辑 $ENV_OUTPUT 设置这些值"
fi

echo ""
log_info "配置完成！"
echo ""
echo "您可以通过以下命令编辑配置文件:"
echo "  nano $ENV_OUTPUT"
echo "  vim $ENV_OUTPUT"
echo ""
