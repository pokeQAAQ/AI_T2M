# -*- coding: utf-8 -*-
"""主窗口管理器"""

from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut

from pages.style_selector import StyleSelectorPage
from pages.voice_recognition import VoiceRecognitionPage
from pages.image_display import ImageDisplayPage
from styles.app_styles import AppStyles

import logging

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_shortcuts()
        self.current_style = None
        self.current_prompt = None

    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("AI语音生图 · 横屏版")
        self.setWindowFlags(Qt.FramelessWindowHint)  # 无边框全屏

        # 设置样式
        self.setStyleSheet(AppStyles.MAIN_WINDOW)

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 创建页面栈
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        # 创建各个页面
        self.style_page = StyleSelectorPage()
        self.voice_page = VoiceRecognitionPage()
        self.image_page = ImageDisplayPage()

        # 添加页面到栈
        self.stack.addWidget(self.style_page)
        self.stack.addWidget(self.voice_page)
        self.stack.addWidget(self.image_page)

        # 连接信号
        self.style_page.style_selected.connect(self.on_style_selected)
        self.voice_page.back_clicked.connect(self.show_style_page)
        self.voice_page.next_clicked.connect(self.on_voice_completed)
        self.image_page.back_clicked.connect(self.show_voice_page)
        self.image_page.back_to_style_clicked.connect(self.show_style_page)
        self.image_page.regenerate_clicked.connect(self.on_regenerate)

        # 显示第一个页面
        self.show_style_page()

    def setup_shortcuts(self):
        """设置快捷键"""
        # ESC键退出
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)
        # F11全屏切换
        QShortcut(QKeySequence(Qt.Key_F11), self, self.toggle_fullscreen)

    def toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    @Slot()
    def show_style_page(self):
        """显示风格选择页面"""
        logger.info("切换到风格选择页面")
        self.stack.setCurrentWidget(self.style_page)
        self.style_page.reset()

    @Slot()
    def show_voice_page(self):
        """显示语音识别页面"""
        logger.info("切换到语音识别页面")
        self.stack.setCurrentWidget(self.voice_page)
        self.voice_page.reset()

    @Slot()
    def show_image_page(self):
        """显示图片展示页面"""
        logger.info("切换到图片展示页面")
        self.stack.setCurrentWidget(self.image_page)

    @Slot(str, str)  # 修改信号接收两个参数
    def on_style_selected(self, style_prompt, style_name):
        """风格选择完成"""
        logger.info(f"选择风格: {style_name} - {style_prompt}")
        self.current_style = style_prompt
        self.current_style_name = style_name
        
        # 获取风格背景图片
        from utils.config import Config
        config = Config.get_instance()
        background_image = None
        
        for style_data in config.STYLES:
            if style_data.get("name") == style_name:
                background_image = style_data.get("background")
                break
        
        self.show_voice_page()
        self.voice_page.set_style(style_prompt, style_name, background_image)  # 传递背景图片
    @Slot(str)
    def on_voice_completed(self, prompt):
        """语音识别完成"""
        logger.info(f"识别文字: {prompt}")
        self.current_prompt = prompt

        # 生成完整提示词
        full_prompt = f"{prompt}, {self.current_style}"
        logger.info(f"完整提示词: {full_prompt}")

        # 显示图片页面并开始生成
        self.show_image_page()
        self.image_page.generate_images(full_prompt)

    @Slot()
    def on_regenerate(self):
        """重新生成"""
        if self.current_prompt and self.current_style:
            full_prompt = f"{self.current_prompt}, {self.current_style}"
            self.image_page.generate_images(full_prompt)