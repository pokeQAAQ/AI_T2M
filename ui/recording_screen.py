#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
录音转文字界面
第一个界面：录音转换文字，选择音乐风格，配置生成参数
"""

import os
import logging
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QComboBox, QPushButton, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap, QPalette, QColor

from config import get_music_config, get_app_config
from threads.record_thread import RecordThread
from threads.asr_thread import ASRThread

logger = logging.getLogger(__name__)


class RecordingScreen(QWidget):
    """录音转文字界面"""
    
    # 信号定义
    generation_requested = Signal(dict)  # 请求生成音乐，传递参数字典
    
    def __init__(self):
        super().__init__()
        self.music_config = get_music_config()
        self.app_config = get_app_config()
        
        # 录音相关
        self.record_thread: Optional[RecordThread] = None
        self.asr_thread: Optional[ASRThread] = None
        self.is_recording = False
        
        # 界面状态
        self.voice_text = ""
        self.selected_genre = ""
        self.selected_mood = ""
        self.selected_gender = ""
        
        self.setup_ui()
        self.apply_theme()
        
    def setup_ui(self):
        """设置界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(30)
        
        # 标题区域
        self.create_title_section(main_layout)
        
        # 文本输入区域
        self.create_text_section(main_layout)
        
        # 录音按钮区域
        self.create_recording_section(main_layout)
        
        # 下一步按钮区域
        self.create_navigation_section(main_layout)
        
    def create_title_section(self, parent_layout):
        """创建标题区域"""
        title_layout = QVBoxLayout()
        title_layout.setSpacing(5)
        
        # 主标题
        title_label = QLabel("Create your music")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setObjectName("title_label")
        
        # 副标题
        subtitle_label = QLabel("开启你的创作")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_font = QFont()
        subtitle_font.setPointSize(14)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setObjectName("subtitle_label")
        
        title_layout.addWidget(title_label)
        title_layout.addWidget(subtitle_label)
        
        parent_layout.addLayout(title_layout)
    
    def create_text_section(self, parent_layout):
        """创建文本输入区域"""
        # 创建文本框
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("我想创作一首歌曲（语音转文本内容）...")
        self.text_edit.setObjectName("text_edit")
        self.text_edit.setMinimumHeight(120)
        self.text_edit.setMaximumHeight(150)
        
        # 设置字体
        text_font = QFont()
        text_font.setPointSize(12)
        self.text_edit.setFont(text_font)
        
        parent_layout.addWidget(self.text_edit)
        
        # 选择区域
        self.create_selection_section(parent_layout)
    
    def create_selection_section(self, parent_layout):
        """创建选择区域"""
        selection_layout = QHBoxLayout()
        selection_layout.setSpacing(20)
        
        # 风格选择
        genre_layout = QVBoxLayout()
        genre_label = QLabel("音乐风格:")
        genre_label.setObjectName("selection_label")
        
        self.genre_combo = QComboBox()
        self.genre_combo.setObjectName("selection_combo")
        self.genre_combo.addItem("请选择风格", "")
        for genre_code, genre_name in self.music_config.GENRES:
            self.genre_combo.addItem(genre_name, genre_code)
        self.genre_combo.currentTextChanged.connect(self.on_selection_changed)
        
        genre_layout.addWidget(genre_label)
        genre_layout.addWidget(self.genre_combo)
        
        # 情绪选择
        mood_layout = QVBoxLayout()
        mood_label = QLabel("传达情绪:")
        mood_label.setObjectName("selection_label")
        
        self.mood_combo = QComboBox()
        self.mood_combo.setObjectName("selection_combo")
        self.mood_combo.addItem("请选择情绪", "")
        for mood_code, mood_name in self.music_config.MOODS:
            self.mood_combo.addItem(mood_name, mood_code)
        self.mood_combo.currentTextChanged.connect(self.on_selection_changed)
        
        mood_layout.addWidget(mood_label)
        mood_layout.addWidget(self.mood_combo)
        
        # 性别选择
        gender_layout = QVBoxLayout()
        gender_label = QLabel("声音性别:")
        gender_label.setObjectName("selection_label")
        
        self.gender_combo = QComboBox()
        self.gender_combo.setObjectName("selection_combo")
        self.gender_combo.addItem("请选择声音", "")
        for gender_code, gender_name in self.music_config.GENDERS:
            self.gender_combo.addItem(gender_name, gender_code)
        self.gender_combo.currentTextChanged.connect(self.on_selection_changed)
        
        gender_layout.addWidget(gender_label)
        gender_layout.addWidget(self.gender_combo)
        
        selection_layout.addLayout(genre_layout)
        selection_layout.addLayout(mood_layout)
        selection_layout.addLayout(gender_layout)
        
        parent_layout.addLayout(selection_layout)
    
    def create_recording_section(self, parent_layout):
        """创建录音按钮区域"""
        recording_layout = QHBoxLayout()
        recording_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 录音按钮
        self.record_button = QPushButton()
        self.record_button.setObjectName("record_button")
        self.record_button.setFixedSize(100, 100)
        self.record_button.clicked.connect(self.toggle_recording)
        
        # 设置按钮图标
        if os.path.exists(self.app_config.BUTTON_ICON_PATH):
            pixmap = QPixmap(self.app_config.BUTTON_ICON_PATH)
            self.record_button.setIcon(pixmap)
            self.record_button.setIconSize(pixmap.size())
        else:
            self.record_button.setText("🎤")
            font = QFont()
            font.setPointSize(24)
            self.record_button.setFont(font)
        
        # 录音状态标签
        self.record_status = QLabel("点击开始录音")
        self.record_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.record_status.setObjectName("record_status")
        
        record_container = QVBoxLayout()
        record_container.addWidget(self.record_button)
        record_container.addWidget(self.record_status)
        
        recording_layout.addLayout(record_container)
        parent_layout.addLayout(recording_layout)
    
    def create_navigation_section(self, parent_layout):
        """创建导航按钮区域"""
        nav_layout = QHBoxLayout()
        nav_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 下一步按钮
        self.next_button = QPushButton("下一步")
        self.next_button.setObjectName("next_button")
        self.next_button.setFixedSize(120, 40)
        self.next_button.setEnabled(False)  # 初始禁用
        self.next_button.clicked.connect(self.on_next_clicked)
        
        nav_layout.addWidget(self.next_button)
        parent_layout.addLayout(nav_layout)
        
        # 添加弹性空间
        parent_layout.addStretch()
    
    def apply_theme(self):
        """应用深色主题"""
        theme = self.app_config.DARK_THEME
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
            }}
            
            #title_label {{
                color: {theme['text_primary']};
                background: transparent;
            }}
            
            #subtitle_label {{
                color: {theme['text_secondary']};
                background: transparent;
            }}
            
            #text_edit {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 8px;
                padding: 12px;
                color: {theme['text_primary']};
                selection-background-color: {theme['primary']};
            }}
            
            #text_edit:focus {{
                border-color: {theme['primary']};
            }}
            
            #selection_label {{
                color: {theme['text_primary']};
                font-weight: bold;
                margin-bottom: 5px;
            }}
            
            #selection_combo {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 6px;
                padding: 8px;
                color: {theme['text_primary']};
                min-width: 150px;
                min-height: 30px;
            }}
            
            #selection_combo:focus {{
                border-color: {theme['primary']};
            }}
            
            #selection_combo::drop-down {{
                border: none;
                background: {theme['surface']};
            }}
            
            #selection_combo QAbstractItemView {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                selection-background-color: {theme['primary']};
                color: {theme['text_primary']};
            }}
            
            #record_button {{
                background-color: {theme['primary']};
                border: none;
                border-radius: 50px;
                color: white;
            }}
            
            #record_button:hover {{
                background-color: {theme['primary_variant']};
            }}
            
            #record_button:pressed {{
                background-color: {theme['primary_variant']};
                transform: scale(0.95);
            }}
            
            #record_button.recording {{
                background-color: {theme['error']};
                animation: pulse 1s infinite;
            }}
            
            #record_status {{
                color: {theme['text_secondary']};
                margin-top: 10px;
            }}
            
            #next_button {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 6px;
                color: {theme['text_hint']};
                font-weight: bold;
                padding: 8px 16px;
            }}
            
            #next_button:enabled {{
                background-color: {theme['primary']};
                border-color: {theme['primary']};
                color: white;
            }}
            
            #next_button:enabled:hover {{
                background-color: {theme['primary_variant']};
            }}
            
            #next_button:enabled:pressed {{
                background-color: {theme['primary_variant']};
                transform: scale(0.98);
            }}
        """)
    
    def toggle_recording(self):
        """切换录音状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录音"""
        try:
            logger.info("🎤 开始录音...")
            
            self.is_recording = True
            self.record_button.setProperty("class", "recording")
            self.record_button.style().unpolish(self.record_button)
            self.record_button.style().polish(self.record_button)
            self.record_status.setText("录音中... 点击停止")
            
            # 启动录音线程
            self.record_thread = RecordThread(self.app_config.TEMP_AUDIO_PATH)
            self.record_thread.finished.connect(self.on_recording_finished)
            self.record_thread.error.connect(self.on_recording_error)
            self.record_thread.start()
            
        except Exception as e:
            logger.error(f"❌ 开始录音失败: {e}")
            self.on_recording_error(f"录音失败: {str(e)}")
    
    def stop_recording(self):
        """停止录音"""
        try:
            logger.info("🛑 停止录音...")
            
            if self.record_thread and self.record_thread.isRunning():
                self.record_thread.stop()
                self.record_thread.wait(3000)  # 等待最多3秒
            
            self.is_recording = False
            self.record_button.setProperty("class", "")
            self.record_button.style().unpolish(self.record_button)
            self.record_button.style().polish(self.record_button)
            self.record_status.setText("处理中...")
            
        except Exception as e:
            logger.error(f"❌ 停止录音失败: {e}")
            self.on_recording_error(f"停止录音失败: {str(e)}")
    
    def on_recording_finished(self, audio_path: str):
        """录音完成回调"""
        if audio_path and os.path.exists(audio_path):
            logger.info(f"✅ 录音完成: {audio_path}")
            self.record_status.setText("正在识别...")
            
            # 启动语音识别
            self.asr_thread = ASRThread(audio_path)
            self.asr_thread.result.connect(self.on_asr_result)
            self.asr_thread.error.connect(self.on_asr_error)
            self.asr_thread.start()
        else:
            self.on_recording_error("录音文件无效")
    
    def on_recording_error(self, error_msg: str):
        """录音错误回调"""
        logger.error(f"❌ 录音错误: {error_msg}")
        self.is_recording = False
        self.record_button.setProperty("class", "")
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)
        self.record_status.setText(f"错误: {error_msg}")
        
        # 3秒后恢复
        QTimer.singleShot(3000, lambda: self.record_status.setText("点击开始录音"))
    
    def on_asr_result(self, text: str):
        """语音识别结果回调"""
        logger.info(f"✅ 语音识别成功: {text}")
        self.voice_text = text
        
        # 将识别结果放入文本框
        current_text = self.text_edit.toPlainText()
        if "语音转文本内容" in current_text or not current_text.strip():
            # 替换占位符文本
            new_text = f"我想创作一首歌曲，{text}。"
        else:
            # 追加到现有文本
            new_text = current_text + f" {text}"
        
        self.text_edit.setPlainText(new_text)
        self.record_status.setText("识别完成")
        
        # 检查是否可以启用下一步按钮
        self.check_next_button_state()
        
        # 3秒后恢复录音按钮状态
        QTimer.singleShot(3000, lambda: self.record_status.setText("点击开始录音"))
    
    def on_asr_error(self, error_msg: str):
        """语音识别错误回调"""
        logger.error(f"❌ 语音识别失败: {error_msg}")
        self.record_status.setText(f"识别失败: {error_msg}")
        
        # 3秒后恢复
        QTimer.singleShot(3000, lambda: self.record_status.setText("点击开始录音"))
    
    def on_selection_changed(self):
        """选择变化回调"""
        # 更新选择状态
        self.selected_genre = self.genre_combo.currentData() or ""
        self.selected_mood = self.mood_combo.currentData() or ""
        self.selected_gender = self.gender_combo.currentData() or ""
        
        # 检查下一步按钮状态
        self.check_next_button_state()
    
    def check_next_button_state(self):
        """检查下一步按钮是否应该启用"""
        text_filled = bool(self.text_edit.toPlainText().strip())
        genre_selected = bool(self.selected_genre)
        mood_selected = bool(self.selected_mood)
        gender_selected = bool(self.selected_gender)
        
        can_proceed = text_filled and genre_selected and mood_selected and gender_selected
        self.next_button.setEnabled(can_proceed)
        
        if can_proceed:
            logger.info("✅ 所有参数已配置完成，可以进入下一步")
    
    def on_next_clicked(self):
        """下一步按钮点击"""
        # 收集生成参数
        params = {
            'prompt': self.text_edit.toPlainText().strip(),
            'genre': self.selected_genre,
            'mood': self.selected_mood,
            'gender': self.selected_gender,
            'voice_text': self.voice_text  # 保存原始语音文本
        }
        
        logger.info(f"🎵 请求生成音乐: {params}")
        self.generation_requested.emit(params)
    
    def reset_form(self):
        """重置表单"""
        self.text_edit.clear()
        self.text_edit.setPlaceholderText("我想创作一首歌曲（语音转文本内容）...")
        self.genre_combo.setCurrentIndex(0)
        self.mood_combo.setCurrentIndex(0)
        self.gender_combo.setCurrentIndex(0)
        self.voice_text = ""
        self.selected_genre = ""
        self.selected_mood = ""
        self.selected_gender = ""
        self.next_button.setEnabled(False)
        self.record_status.setText("点击开始录音")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.record_thread and self.record_thread.isRunning():
                self.record_thread.stop()
                self.record_thread.wait()
            
            if self.asr_thread and self.asr_thread.isRunning():
                self.asr_thread.stop()
                self.asr_thread.wait()
                
            logger.info("🧹 录音界面资源已清理")
        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}")