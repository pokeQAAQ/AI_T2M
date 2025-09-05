#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI音乐生成应用主程序
整合录音转文字、音乐生成、播放控制等功能
"""

import sys
import os
import logging
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QScreen

from config import get_app_config
from ui.recording_screen import RecordingScreen
from ui.generation_screen import GenerationScreen
from ui.playback_screen import PlaybackScreen

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/ai_music.log')
    ]
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.app_config = get_app_config()
        
        # 设置窗口属性
        self.setWindowTitle(self.app_config.WINDOW_TITLE)
        self.setFixedSize(self.app_config.WINDOW_WIDTH, self.app_config.WINDOW_HEIGHT)
        
        # 创建界面栈
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # 创建各个界面
        self.setup_screens()
        
        # 连接信号
        self.setup_connections()
        
        # 设置窗口样式
        self.apply_window_style()
        
        logger.info("🎵 主窗口初始化完成")
    
    def setup_screens(self):
        """设置界面"""
        # 创建三个主要界面
        self.recording_screen = RecordingScreen()
        self.generation_screen = GenerationScreen()
        self.playback_screen = PlaybackScreen()
        
        # 添加到栈中
        self.stacked_widget.addWidget(self.recording_screen)  # 索引 0
        self.stacked_widget.addWidget(self.generation_screen)  # 索引 1
        self.stacked_widget.addWidget(self.playback_screen)   # 索引 2
        
        # 显示第一个界面
        self.stacked_widget.setCurrentIndex(0)
        
        logger.info("✅ 界面栈设置完成")
    
    def setup_connections(self):
        """设置信号连接"""
        # 录音界面 -> 生成界面
        self.recording_screen.generation_requested.connect(self.on_generation_requested)
        
        # 生成界面 -> 播放界面
        self.generation_screen.generation_completed.connect(self.on_generation_completed)
        self.generation_screen.generation_failed.connect(self.on_generation_failed)
        
        # 播放界面 -> 录音界面
        self.playback_screen.new_generation_requested.connect(self.on_new_generation_requested)
        
        logger.info("✅ 信号连接设置完成")
    
    def apply_window_style(self):
        """应用窗口样式"""
        theme = self.app_config.DARK_THEME
        
        # 设置窗口样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {theme['background']};
            }}
            
            QStackedWidget {{
                background-color: {theme['background']};
                border: none;
            }}
        """)
        
        # 设置窗口标志
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
    
    def on_generation_requested(self, params: dict):
        """处理生成请求"""
        try:
            logger.info(f"🎵 收到生成请求: {params}")
            
            # 切换到生成界面
            self.stacked_widget.setCurrentIndex(1)
            
            # 开始生成
            self.generation_screen.start_generation(params)
            
        except Exception as e:
            logger.error(f"❌ 处理生成请求失败: {e}")
    
    def on_generation_completed(self, song_info: dict):
        """处理生成完成"""
        try:
            logger.info(f"✅ 音乐生成完成: {song_info.get('song_name', '未知歌曲')}")
            
            # 切换到播放界面
            self.stacked_widget.setCurrentIndex(2)
            
            # 加载歌曲
            self.playback_screen.load_song(song_info)
            
        except Exception as e:
            logger.error(f"❌ 处理生成完成失败: {e}")
    
    def on_generation_failed(self, error_msg: str):
        """处理生成失败"""
        try:
            logger.error(f"❌ 音乐生成失败: {error_msg}")
            
            # 返回录音界面
            self.stacked_widget.setCurrentIndex(0)
            
            # 可以在这里显示错误提示
            # 这里简单地重置录音界面
            self.recording_screen.reset_form()
            
        except Exception as e:
            logger.error(f"❌ 处理生成失败失败: {e}")
    
    def on_new_generation_requested(self):
        """处理新建请求"""
        try:
            logger.info("🔄 请求创建新音乐")
            
            # 切换到录音界面
            self.stacked_widget.setCurrentIndex(0)
            
            # 重置录音界面
            self.recording_screen.reset_form()
            
        except Exception as e:
            logger.error(f"❌ 处理新建请求失败: {e}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        try:
            logger.info("🛑 应用程序正在关闭...")
            
            # 清理各个界面的资源
            self.recording_screen.cleanup()
            self.generation_screen.cleanup()
            self.playback_screen.cleanup()
            
            logger.info("✅ 资源清理完成")
            event.accept()
            
        except Exception as e:
            logger.error(f"❌ 关闭应用程序失败: {e}")
            event.accept()  # 强制关闭


def setup_environment():
    """设置环境变量"""
    # 优化Qt渲染（适合Orange Pi Zero 3）
    os.environ['QT_QUICK_BACKEND'] = 'software'
    os.environ['QT_SCALE_FACTOR'] = '1'
    os.environ['QT_LOGGING_RULES'] = '*.debug=false'
    
    # 音频相关
    os.environ['PULSE_RUNTIME_PATH'] = '/run/user/1000/pulse'
    
    # 确保临时目录存在
    temp_dirs = ['/tmp', get_app_config().MUSIC_CACHE_DIR]
    for temp_dir in temp_dirs:
        os.makedirs(temp_dir, exist_ok=True)


def main():
    """主程序入口"""
    try:
        # 设置环境
        setup_environment()
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("AI音乐创作")
        app.setOrganizationName("OrangePi")
        
        # 设置应用风格
        app.setStyle('Fusion')
        
        # 创建主窗口
        window = MainWindow()
        
        # 居中显示（适配Orange Pi Zero 3的1024x600分辨率）
        screen = app.primaryScreen()
        if screen:
            screen_geometry = screen.geometry()
            x = (screen_geometry.width() - window.width()) // 2
            y = (screen_geometry.height() - window.height()) // 2
            window.move(max(0, x), max(0, y))
        
        # 显示窗口
        window.show()
        
        logger.info("🚀 AI音乐创作应用已启动 - 横屏模式 1024x600")
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"❌ 应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()