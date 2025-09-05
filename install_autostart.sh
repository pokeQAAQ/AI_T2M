#!/bin/bash
# AI语音生图项目开机自启动安装脚本

set -e

PROJECT_DIR="/home/orangepi/T2I/pycharm_project_287"
SERVICE_FILE="$PROJECT_DIR/ai-voice-image.service"
SYSTEM_SERVICE_DIR="/etc/systemd/system"
USER_SERVICE_DIR="$HOME/.config/systemd/user"

echo "=== AI语音生图项目开机自启动安装脚本 ==="

# 检查是否以root权限运行（用于系统级服务）
if [ "$EUID" -eq 0 ]; then
    echo "检测到root权限，安装系统级服务..."
    SERVICE_DIR="$SYSTEM_SERVICE_DIR"
    SYSTEMCTL_CMD="systemctl"
    TARGET="multi-user.target"
else
    echo "使用用户级服务安装..."
    SERVICE_DIR="$USER_SERVICE_DIR"
    SYSTEMCTL_CMD="systemctl --user"
    TARGET="default.target"
    
    # 创建用户服务目录
    mkdir -p "$USER_SERVICE_DIR"
fi

# 检查服务文件是否存在
if [ ! -f "$SERVICE_FILE" ]; then
    echo "错误：服务文件不存在 $SERVICE_FILE"
    exit 1
fi

# 检查项目目录和虚拟环境
if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误：项目目录不存在 $PROJECT_DIR"
    exit 1
fi

if [ ! -f "/home/orangepi/test1/bin/python" ]; then
    echo "错误：虚拟环境不存在 /home/orangepi/test1/bin/python"
    exit 1
fi

# 复制服务文件
echo "复制服务文件到 $SERVICE_DIR/ai-voice-image.service"
if [ "$EUID" -eq 0 ]; then
    cp "$SERVICE_FILE" "$SERVICE_DIR/ai-voice-image.service"
else
    # 为用户级服务修改配置
    sed 's/After=graphical-session.target/After=graphical-session.target/' "$SERVICE_FILE" | \
    sed 's/Wants=graphical-session.target/Wants=graphical-session.target/' | \
    sed 's/WantedBy=graphical-session.target/WantedBy=default.target/' > "$SERVICE_DIR/ai-voice-image.service"
fi

# 设置文件权限
chmod 644 "$SERVICE_DIR/ai-voice-image.service"

# 重载systemd配置
echo "重载systemd配置..."
$SYSTEMCTL_CMD daemon-reload

# 启用服务
echo "启用开机自启动..."
$SYSTEMCTL_CMD enable ai-voice-image.service

# 显示服务状态
echo "服务状态："
$SYSTEMCTL_CMD status ai-voice-image.service --no-pager || true

echo ""
echo "=== 安装完成 ==="
echo "服务名称：ai-voice-image.service"
echo "管理命令："
echo "  启动服务：$SYSTEMCTL_CMD start ai-voice-image.service"
echo "  停止服务：$SYSTEMCTL_CMD stop ai-voice-image.service"
echo "  重启服务：$SYSTEMCTL_CMD restart ai-voice-image.service"
echo "  查看状态：$SYSTEMCTL_CMD status ai-voice-image.service"
echo "  查看日志：journalctl -u ai-voice-image.service -f"
echo "  禁用自启：$SYSTEMCTL_CMD disable ai-voice-image.service"

if [ "$EUID" -ne 0 ]; then
    echo ""
    echo "注意：使用用户级服务，需要启用用户服务自动启动："
    echo "  sudo loginctl enable-linger orangepi"
fi

echo ""
echo "重启系统后，AI语音生图程序将自动检查更新并启动。"