#!/bin/bash
# AI语音生图项目开机自启动脚本

set -e

# 项目路径
PROJECT_DIR="/home/orangepi/T2I/pycharm_project_287"
VENV_PATH="/home/orangepi/test1"
LOG_FILE="$PROJECT_DIR/logs/startup_log.txt"

# 确保日志目录存在
mkdir -p "$PROJECT_DIR/logs"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========== 开机自启动脚本启动 =========="

# 等待显示服务器就绪
log "等待显示服务器启动..."
for i in {1..30}; do
    if [ -n "$DISPLAY" ] && xset q >/dev/null 2>&1; then
        log "显示服务器已就绪：$DISPLAY"
        break
    elif [ -n "$WAYLAND_DISPLAY" ]; then
        log "Wayland显示服务器已就绪：$WAYLAND_DISPLAY"
        break
    else
        log "等待显示服务器... ($i/30)"
        sleep 2
    fi
done

# 设置环境变量
export DISPLAY=${DISPLAY:-:0}
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-wayland-0}

log "设置显示环境：DISPLAY=$DISPLAY"

# 额外等待确保GUI环境完全就绪
log "等待GUI环境完全就绪..."
sleep 5

# 检测GUI是否可用
if python3 -c "
import os
os.environ['DISPLAY'] = '$DISPLAY'
try:
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()
    root.destroy()
    print('GUI_AVAILABLE')
except Exception as e:
    print(f'GUI_ERROR: {e}')
" 2>/dev/null | grep -q "GUI_AVAILABLE"; then
    log "GUI环境检测成功"
else
    log "GUI环境检测失败，将使用命令行模式"
fi

# 切换到项目目录
cd "$PROJECT_DIR"

# 检查虚拟环境
if [ ! -f "$VENV_PATH/bin/python" ]; then
    log "错误：虚拟环境不存在 $VENV_PATH"
    exit 1
fi

# 检查是否安装了requests
if ! "$VENV_PATH/bin/python" -c "import requests" 2>/dev/null; then
    log "正在安装依赖 requests..."
    "$VENV_PATH/bin/pip" install requests
fi

# 运行自动更新程序
log "启动AI语音生图自动更新程序..."
exec "$VENV_PATH/bin/python" "$PROJECT_DIR/auto_updater.py" "$@"