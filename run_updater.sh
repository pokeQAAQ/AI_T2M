#!/bin/bash
# AI语音生图项目便捷启动脚本

set -e

# 项目路径
PROJECT_DIR="/home/orangepi/T2I/pycharm_project_287"
VENV_PATH="/home/orangepi/test1"

# 切换到项目目录
cd "$PROJECT_DIR"

# 设置显示环境变量
export DISPLAY=:0

# 检查虚拟环境
if [ ! -f "$VENV_PATH/bin/python" ]; then
    echo "错误：虚拟环境不存在 $VENV_PATH"
    exit 1
fi

# 检查是否安装了requests
if ! "$VENV_PATH/bin/python" -c "import requests" 2>/dev/null; then
    echo "正在安装依赖 requests..."
    "$VENV_PATH/bin/pip" install requests
fi

# 运行自动更新程序
echo "启动AI语音生图自动更新程序..."
exec "$VENV_PATH/bin/python" "$PROJECT_DIR/auto_updater.py" "$@"