#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐生成界面
第二个界面：显示生成进度，播放加载动画
"""

import os
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QMovie, QPixmap

from config import get_app_config
from music.generator import MusicGenerationThread

logger = logging.getLogger(__name__)


class GenerationScreen(QWidget):
    """音乐生成界面"""
    
    # 信号定义
    generation_completed = Signal(dict)  # 生成完成，传递歌曲信息
    generation_failed = Signal(str)  # 生成失败，传递错误信息
    back_requested = Signal()  # 请求返回上一页
    
    def __init__(self):
        super().__init__()
        self.app_config = get_app_config()
        
        # 生成线程
        self.generation_thread: Optional[MusicGenerationThread] = None
        
        # 当前生成参数
        self.current_params = {}
        
        # 加载动画
        self.loading_movie: Optional[QMovie] = None
        
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """设置界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建加载动画区域
        self.create_loading_section(main_layout)
        
    def create_loading_section(self, parent_layout):
        """创建加载动画区域"""
        # 容器
        loading_container = QFrame()
        loading_container.setObjectName("loading_container")
        loading_layout = QVBoxLayout(loading_container)
        loading_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.setSpacing(30)
        
        # 加载动画标签
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setObjectName("loading_label")
        
        # 设置加载GIF
        self.setup_loading_animation()
        
        # 状态文本
        self.status_label = QLabel("正在生成音乐...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("status_label")
        
        status_font = QFont()
        status_font.setPointSize(18)
        status_font.setBold(True)
        self.status_label.setFont(status_font)
        
        # 详细信息标签
        self.detail_label = QLabel("")
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setObjectName("detail_label")
        
        detail_font = QFont()
        detail_font.setPointSize(12)
        self.detail_label.setFont(detail_font)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("准备中...")
        
        # 进度条样式
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setFixedWidth(400)
        
        # 添加到布局
        loading_layout.addWidget(self.loading_label)
        loading_layout.addWidget(self.status_label)
        loading_layout.addWidget(self.detail_label)
        loading_layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(loading_container)
        
    def setup_loading_animation(self):
        """设置加载动画"""
        try:
            if os.path.exists(self.app_config.LOADING_GIF_PATH):
                # 使用提供的GIF文件
                self.loading_movie = QMovie(self.app_config.LOADING_GIF_PATH)
                self.loading_label.setMovie(self.loading_movie)
                
                # 设置合适的大小
                self.loading_movie.setScaledSize(self.loading_movie.currentPixmap().size().boundedTo(
                    self.loading_label.size().boundedTo(self.size() // 3)
                ))
                
                self.loading_movie.start()
                logger.info(f"✅ 加载动画已设置: {self.app_config.LOADING_GIF_PATH}")
            else:
                # 使用文本占位符
                self.loading_label.setText("🎵")
                font = QFont()
                font.setPointSize(72)
                self.loading_label.setFont(font)
                
                # 创建简单的动画效果
                self.create_text_animation()
                logger.warning(f"⚠️ 未找到GIF文件，使用文本动画: {self.app_config.LOADING_GIF_PATH}")
                
        except Exception as e:
            logger.error(f"❌ 设置加载动画失败: {e}")
            # 回退到简单文本
            self.loading_label.setText("♪")
            font = QFont()
            font.setPointSize(48)
            self.loading_label.setFont(font)
    
    def create_text_animation(self):
        """创建文本动画（当没有GIF时的备选方案）"""
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_text_animation)
        self.animation_timer.start(500)  # 每500ms更新一次
        
        self.animation_symbols = ["🎵", "🎶", "🎤", "🎧", "🎼"]
        self.animation_index = 0
    
    def update_text_animation(self):
        """更新文本动画"""
        try:
            if hasattr(self, 'animation_symbols'):
                symbol = self.animation_symbols[self.animation_index]
                self.loading_label.setText(symbol)
                self.animation_index = (self.animation_index + 1) % len(self.animation_symbols)
        except Exception as e:
            logger.error(f"❌ 更新文本动画失败: {e}")
    
    def apply_theme(self):
        """应用深色主题"""
        theme = self.app_config.DARK_THEME
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
            }}
            
            #loading_container {{
                background-color: {theme['background']};
                border: none;
            }}
            
            #loading_label {{
                background: transparent;
                color: {theme['text_primary']};
            }}
            
            #status_label {{
                background: transparent;
                color: {theme['text_primary']};
            }}
            
            #detail_label {{
                background: transparent;
                color: {theme['text_secondary']};
            }}
            
            #progress_bar {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 15px;
                text-align: center;
                color: {theme['text_primary']};
                font-weight: bold;
            }}
            
            #progress_bar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {theme['primary']}, 
                    stop:1 {theme['secondary']});
                border-radius: 13px;
                margin: 2px;
            }}
        """)
    
    def start_generation(self, params: dict):
        """开始生成音乐"""
        try:
            self.current_params = params.copy()
            
            logger.info(f"🎵 开始生成音乐: {params}")
            
            # 更新界面状态
            self.status_label.setText("正在生成音乐...")
            self.detail_label.setText(f"风格: {params.get('genre', '')} | 情绪: {params.get('mood', '')} | 声音: {params.get('gender', '')}")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("初始化...")
            
            # 启动生成线程
            self.generation_thread = MusicGenerationThread(
                prompt=params['prompt'],
                gender=params['gender'],
                genre=params['genre'],
                mood=params['mood'],
                generate_full_song=True
            )
            
            # 连接信号
            self.generation_thread.song_task_created.connect(self.on_task_created)
            self.generation_thread.progress_updated.connect(self.on_progress_updated)
            self.generation_thread.song_ready.connect(self.on_generation_completed)
            self.generation_thread.error_occurred.connect(self.on_generation_failed)
            
            # 开始生成
            self.generation_thread.start()
            
        except Exception as e:
            logger.error(f"❌ 开始生成失败: {e}")
            self.on_generation_failed(f"启动生成失败: {str(e)}")
    
    def on_task_created(self, task_info: dict):
        """任务创建成功回调"""
        try:
            task_id = task_info.get('task_id', '')
            predicted_wait_time = task_info.get('predicted_wait_time', 30)
            
            logger.info(f"✅ 音乐生成任务已创建: {task_id}")
            
            self.progress_bar.setValue(10)
            self.progress_bar.setFormat(f"任务已创建 | 预计等待: {predicted_wait_time}秒")
            self.detail_label.setText(f"任务ID: {task_id[:12]}...")
            
        except Exception as e:
            logger.error(f"❌ 处理任务创建信息失败: {e}")
    
    def on_progress_updated(self, progress: int):
        """进度更新回调"""
        try:
            # 进度映射：10-90 对应生成进度 0-100
            mapped_progress = 10 + int(progress * 0.8)
            self.progress_bar.setValue(mapped_progress)
            self.progress_bar.setFormat(f"生成中... {progress}%")
            
            if progress > 0:
                self.status_label.setText("AI正在创作您的音乐...")
            
            logger.info(f"📈 生成进度更新: {progress}%")
            
        except Exception as e:
            logger.error(f"❌ 更新进度失败: {e}")
    
    def on_generation_completed(self, song_info: dict):
        """生成完成回调"""
        try:
            logger.info("✅ 音乐生成完成")
            
            # 更新界面
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("生成完成!")
            self.status_label.setText("音乐生成完成！")
            
            song_name = song_info.get('song_name', '未命名歌曲')
            self.detail_label.setText(f"歌曲: {song_name}")
            
            # 停止动画
            self.stop_animation()
            
            # 合并参数和结果
            complete_info = {**self.current_params, **song_info}
            
            # 延迟一秒后切换到播放界面
            QTimer.singleShot(1000, lambda: self.generation_completed.emit(complete_info))
            
        except Exception as e:
            logger.error(f"❌ 处理生成完成失败: {e}")
            self.on_generation_failed(f"处理结果失败: {str(e)}")
    
    def on_generation_failed(self, error_msg: str):
        """生成失败回调"""
        try:
            logger.error(f"❌ 音乐生成失败: {error_msg}")
            
            # 更新界面
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("生成失败")
            self.status_label.setText("生成失败")
            self.detail_label.setText(f"错误: {error_msg}")
            
            # 停止动画
            self.stop_animation()
            
            # 3秒后发送失败信号
            QTimer.singleShot(3000, lambda: self.generation_failed.emit(error_msg))
            
        except Exception as e:
            logger.error(f"❌ 处理生成失败信息失败: {e}")
    
    def stop_animation(self):
        """停止动画"""
        try:
            if self.loading_movie:
                self.loading_movie.stop()
            
            if hasattr(self, 'animation_timer'):
                self.animation_timer.stop()
                
        except Exception as e:
            logger.error(f"❌ 停止动画失败: {e}")
    
    def start_animation(self):
        """开始动画"""
        try:
            if self.loading_movie:
                self.loading_movie.start()
            
            if hasattr(self, 'animation_timer'):
                self.animation_timer.start()
                
        except Exception as e:
            logger.error(f"❌ 开始动画失败: {e}")
    
    def cancel_generation(self):
        """取消生成"""
        try:
            logger.info("🛑 取消音乐生成")
            
            if self.generation_thread and self.generation_thread.isRunning():
                self.generation_thread.stop()
                self.generation_thread.wait(3000)
            
            self.stop_animation()
            
            # 更新界面
            self.status_label.setText("已取消生成")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("已取消")
            self.detail_label.setText("")
            
        except Exception as e:
            logger.error(f"❌ 取消生成失败: {e}")
    
    def reset_screen(self):
        """重置界面"""
        try:
            # 取消当前生成
            self.cancel_generation()
            
            # 重置界面状态
            self.status_label.setText("正在生成音乐...")
            self.detail_label.setText("")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("准备中...")
            self.current_params = {}
            
            # 重新开始动画
            self.start_animation()
            
        except Exception as e:
            logger.error(f"❌ 重置界面失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 停止生成线程
            if self.generation_thread and self.generation_thread.isRunning():
                self.generation_thread.stop()
                self.generation_thread.wait()
            
            # 停止动画
            self.stop_animation()
            
            # 清理动画资源
            if self.loading_movie:
                self.loading_movie.deleteLater()
                self.loading_movie = None
            
            if hasattr(self, 'animation_timer'):
                self.animation_timer.stop()
                self.animation_timer.deleteLater()
            
            logger.info("🧹 生成界面资源已清理")
            
        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}")
    
    def showEvent(self, event):
        """界面显示时启动动画"""
        super().showEvent(event)
        self.start_animation()
    
    def hideEvent(self, event):
        """界面隐藏时停止动画"""
        super().hideEvent(event)
        self.stop_animation()