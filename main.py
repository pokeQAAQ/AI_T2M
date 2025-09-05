#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI语音生图横屏版 - 主程序入口"""

import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QScreen
from main_window import MainWindow

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/ai_voice_image.log')
    ]
)

logger = logging.getLogger(__name__)


def setup_environment():
    """设置环境变量以优化性能"""
    # 优化Qt渲染
    os.environ['QT_QUICK_BACKEND'] = 'software'
    os.environ['QT_SCALE_FACTOR'] = '1'
    # 减少内存使用
    os.environ['QT_LOGGING_RULES'] = '*.debug=false'


def main():
    """主程序入口"""
    setup_environment()

    app = QApplication(sys.argv)
    app.setApplicationName("AI语音生图")
    app.setOrganizationName("OrangePi")

    # 设置应用风格
    app.setStyle('Fusion')

    # 创建主窗口
    window = MainWindow()

    # 设置窗口大小和位置（横屏1024x600）
    window.setFixedSize(1024, 600)

    # 居中显示
    screen = app.primaryScreen()
    if screen:
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - 1024) // 2
        y = (screen_geometry.height() - 600) // 2
        window.move(x, y)

    # 显示窗口
    window.show()

    logger.info("应用已启动 - 横屏模式 1024x600")

    sys.exit(app.exec())


if __name__ == '__main__':
    main()