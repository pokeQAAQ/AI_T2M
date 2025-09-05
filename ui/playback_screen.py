#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐播放界面
第三个界面：音乐播放控制、历史记录、进度管理
"""

import logging
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSlider, QFrame, QListWidget, QListWidgetItem, QStackedWidget,
    QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtMultimedia import QMediaPlayer

from config import get_app_config
from music.player import MusicPlayer, format_time

logger = logging.getLogger(__name__)


class PlaybackScreen(QWidget):
    """音乐播放界面"""
    
    # 信号定义
    new_generation_requested = Signal()  # 请求新的生成
    
    def __init__(self):
        super().__init__()
        self.app_config = get_app_config()
        
        # 音乐播放器
        self.music_player = MusicPlayer()
        
        # 界面状态
        self.current_song: Optional[Dict] = None
        self.is_history_visible = False
        
        # 更新定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_progress)
        self.update_timer.start(1000)  # 每秒更新一次
        
        self.setup_ui()
        self.setup_player_connections()
        self.apply_theme()
        
    def setup_ui(self):
        """设置界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # 上方区域
        self.create_top_section(main_layout)
        
        # 中间内容区域（可切换）
        self.create_content_section(main_layout)
        
        # 下方控制栏
        self.create_control_section(main_layout)
    
    def create_top_section(self, parent_layout):
        """创建上方区域"""
        top_layout = QHBoxLayout()
        top_layout.setSpacing(20)
        
        # 左侧：GIF区域占位符
        gif_frame = QFrame()
        gif_frame.setObjectName("gif_frame")
        gif_frame.setFixedSize(200, 150)
        
        gif_layout = QVBoxLayout(gif_frame)
        gif_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.gif_label = QLabel("🎵")
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gif_label.setObjectName("gif_label")
        
        gif_font = QFont()
        gif_font.setPointSize(48)
        self.gif_label.setFont(gif_font)
        
        gif_layout.addWidget(self.gif_label)
        
        # 右侧：歌曲信息区域
        info_frame = QFrame()
        info_frame.setObjectName("info_frame")
        info_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        info_layout = QVBoxLayout(info_frame)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_layout.setSpacing(10)
        
        # 歌曲名称
        self.song_name_label = QLabel("AI音乐创作")
        self.song_name_label.setObjectName("song_name_label")
        self.song_name_label.setWordWrap(True)
        
        song_font = QFont()
        song_font.setPointSize(18)
        song_font.setBold(True)
        self.song_name_label.setFont(song_font)
        
        # 歌曲信息
        self.song_info_label = QLabel("选择一首歌曲开始播放")
        self.song_info_label.setObjectName("song_info_label")
        self.song_info_label.setWordWrap(True)
        
        info_font = QFont()
        info_font.setPointSize(12)
        self.song_info_label.setFont(info_font)
        
        # 新建按钮
        self.new_button = QPushButton("创建新音乐")
        self.new_button.setObjectName("new_button")
        self.new_button.setFixedSize(120, 35)
        self.new_button.clicked.connect(self.on_new_generation_clicked)
        
        info_layout.addWidget(self.song_name_label)
        info_layout.addWidget(self.song_info_label)
        info_layout.addWidget(self.new_button)
        info_layout.addStretch()
        
        top_layout.addWidget(gif_frame)
        top_layout.addWidget(info_frame)
        
        parent_layout.addLayout(top_layout)
    
    def create_content_section(self, parent_layout):
        """创建中间内容区域"""
        # 堆叠窗口部件，用于切换显示内容
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_stack")
        
        # 默认页面（空白）
        default_page = QWidget()
        default_layout = QVBoxLayout(default_page)
        default_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        welcome_label = QLabel("🎼")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_font = QFont()
        welcome_font.setPointSize(72)
        welcome_label.setFont(welcome_font)
        welcome_label.setObjectName("welcome_label")
        
        welcome_text = QLabel("点击"历史音乐"查看已生成的作品")
        welcome_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_text.setObjectName("welcome_text")
        
        default_layout.addWidget(welcome_label)
        default_layout.addWidget(welcome_text)
        
        # 历史列表页面
        history_page = QWidget()
        history_layout = QVBoxLayout(history_page)
        
        # 历史列表标题
        history_title = QLabel("历史音乐")
        history_title.setObjectName("history_title")
        history_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        history_title.setFont(title_font)
        
        # 历史列表
        self.history_list = QListWidget()
        self.history_list.setObjectName("history_list")
        self.history_list.itemClicked.connect(self.on_history_item_clicked)
        
        history_layout.addWidget(history_title)
        history_layout.addWidget(self.history_list)
        
        # 添加页面到堆叠窗口
        self.content_stack.addWidget(default_page)  # 索引 0
        self.content_stack.addWidget(history_page)   # 索引 1
        
        parent_layout.addWidget(self.content_stack)
    
    def create_control_section(self, parent_layout):
        """创建控制栏"""
        control_frame = QFrame()
        control_frame.setObjectName("control_frame")
        control_frame.setFixedHeight(100)
        
        control_layout = QVBoxLayout(control_frame)
        control_layout.setSpacing(10)
        
        # 控制按钮行
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(20)
        
        # 历史音乐按钮
        self.history_button = QPushButton("≡")
        self.history_button.setObjectName("history_button")
        self.history_button.setFixedSize(50, 50)
        self.history_button.setToolTip("历史音乐")
        self.history_button.clicked.connect(self.toggle_history)
        
        # 上一首按钮
        self.prev_button = QPushButton("◀")
        self.prev_button.setObjectName("control_button")
        self.prev_button.setFixedSize(45, 45)
        self.prev_button.clicked.connect(self.music_player.play_previous)
        
        # 播放/暂停按钮
        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("play_button")
        self.play_button.setFixedSize(60, 60)
        self.play_button.clicked.connect(self.toggle_playback)
        
        # 下一首按钮
        self.next_button = QPushButton("▶▶")
        self.next_button.setObjectName("control_button")
        self.next_button.setFixedSize(45, 45)
        self.next_button.clicked.connect(self.music_player.play_next)
        
        buttons_layout.addWidget(self.history_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.prev_button)
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.next_button)
        buttons_layout.addStretch()
        
        # 进度条行
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(10)
        
        # 当前时间
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setObjectName("time_label")
        self.current_time_label.setFixedWidth(40)
        
        # 进度滑块
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setObjectName("progress_slider")
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(100)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderPressed.connect(self.on_progress_pressed)
        self.progress_slider.sliderReleased.connect(self.on_progress_released)
        
        # 总时长
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setObjectName("time_label")
        self.total_time_label.setFixedWidth(40)
        
        progress_layout.addWidget(self.current_time_label)
        progress_layout.addWidget(self.progress_slider)
        progress_layout.addWidget(self.total_time_label)
        
        control_layout.addLayout(buttons_layout)
        control_layout.addLayout(progress_layout)
        
        parent_layout.addWidget(control_frame)
    
    def setup_player_connections(self):
        """设置播放器信号连接"""
        self.music_player.position_changed.connect(self.on_position_changed)
        self.music_player.duration_changed.connect(self.on_duration_changed)
        self.music_player.state_changed.connect(self.on_state_changed)
        self.music_player.error_occurred.connect(self.on_player_error)
        self.music_player.media_loaded.connect(self.on_media_loaded)
    
    def apply_theme(self):
        """应用深色主题"""
        theme = self.app_config.DARK_THEME
        
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['background']};
                color: {theme['text_primary']};
            }}
            
            #gif_frame {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 10px;
            }}
            
            #gif_label {{
                background: transparent;
                color: {theme['text_secondary']};
            }}
            
            #info_frame {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 10px;
                padding: 15px;
            }}
            
            #song_name_label {{
                background: transparent;
                color: {theme['text_primary']};
            }}
            
            #song_info_label {{
                background: transparent;
                color: {theme['text_secondary']};
            }}
            
            #new_button {{
                background-color: {theme['primary']};
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }}
            
            #new_button:hover {{
                background-color: {theme['primary_variant']};
            }}
            
            #new_button:pressed {{
                background-color: {theme['primary_variant']};
                transform: scale(0.98);
            }}
            
            #content_stack {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 10px;
                padding: 10px;
            }}
            
            #welcome_label {{
                background: transparent;
                color: {theme['text_secondary']};
            }}
            
            #welcome_text {{
                background: transparent;
                color: {theme['text_hint']};
            }}
            
            #history_title {{
                background: transparent;
                color: {theme['text_primary']};
                margin-bottom: 10px;
            }}
            
            #history_list {{
                background-color: {theme['background']};
                border: 1px solid {theme['border']};
                border-radius: 6px;
                padding: 5px;
                color: {theme['text_primary']};
            }}
            
            #history_list::item {{
                background-color: {theme['surface']};
                border: 1px solid {theme['border']};
                border-radius: 4px;
                padding: 8px;
                margin: 2px;
            }}
            
            #history_list::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}
            
            #history_list::item:hover {{
                background-color: {theme['primary_variant']};
                color: white;
            }}
            
            #control_frame {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 10px;
                padding: 10px;
            }}
            
            #history_button {{
                background-color: {theme['secondary']};
                border: none;
                border-radius: 25px;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }}
            
            #history_button:hover {{
                background-color: {theme['primary']};
            }}
            
            #control_button {{
                background-color: {theme['surface']};
                border: 2px solid {theme['border']};
                border-radius: 22px;
                color: {theme['text_primary']};
                font-size: 16px;
                font-weight: bold;
            }}
            
            #control_button:hover {{
                background-color: {theme['primary']};
                border-color: {theme['primary']};
                color: white;
            }}
            
            #play_button {{
                background-color: {theme['primary']};
                border: none;
                border-radius: 30px;
                color: white;
                font-size: 20px;
                font-weight: bold;
            }}
            
            #play_button:hover {{
                background-color: {theme['primary_variant']};
            }}
            
            #play_button:pressed {{
                background-color: {theme['primary_variant']};
                transform: scale(0.95);
            }}
            
            #progress_slider {{
                background: transparent;
            }}
            
            #progress_slider::groove:horizontal {{
                background-color: {theme['border']};
                height: 6px;
                border-radius: 3px;
            }}
            
            #progress_slider::handle:horizontal {{
                background-color: {theme['primary']};
                border: 2px solid {theme['primary']};
                width: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }}
            
            #progress_slider::sub-page:horizontal {{
                background-color: {theme['primary']};
                border-radius: 3px;
            }}
            
            #time_label {{
                background: transparent;
                color: {theme['text_secondary']};
                font-weight: bold;
            }}
        """)
    
    def load_song(self, song_info: Dict):
        """加载歌曲"""
        try:
            self.current_song = song_info
            self.music_player.load_song(song_info)
            
            # 更新界面显示
            song_name = song_info.get('song_name', '未命名歌曲')
            self.song_name_label.setText(song_name)
            
            # 构建歌曲信息
            info_parts = []
            if song_info.get('genre'):
                info_parts.append(f"风格: {song_info['genre']}")
            if song_info.get('mood'):
                info_parts.append(f"情绪: {song_info['mood']}")
            if song_info.get('gender'):
                info_parts.append(f"声音: {song_info['gender']}")
            
            info_text = " | ".join(info_parts) if info_parts else "AI生成的音乐作品"
            self.song_info_label.setText(info_text)
            
            # 添加到播放列表
            self.music_player.add_to_playlist(song_info)
            
            logger.info(f"✅ 歌曲已加载: {song_name}")
            
        except Exception as e:
            logger.error(f"❌ 加载歌曲失败: {e}")
    
    def toggle_playback(self):
        """切换播放/暂停"""
        try:
            if self.music_player.is_playing():
                self.music_player.pause()
            elif self.music_player.is_paused():
                self.music_player.play()
            else:
                # 停止状态，开始播放
                if self.current_song:
                    self.music_player.play()
                    
        except Exception as e:
            logger.error(f"❌ 切换播放状态失败: {e}")
    
    def toggle_history(self):
        """切换历史列表显示"""
        try:
            if self.is_history_visible:
                # 隐藏历史列表
                self.content_stack.setCurrentIndex(0)
                self.history_button.setText("≡")
                self.is_history_visible = False
            else:
                # 显示历史列表
                self.load_history()
                self.content_stack.setCurrentIndex(1)
                self.history_button.setText("×")
                self.is_history_visible = True
                
        except Exception as e:
            logger.error(f"❌ 切换历史列表失败: {e}")
    
    def load_history(self):
        """加载历史记录"""
        try:
            self.history_list.clear()
            
            history = self.music_player.get_history()
            
            if not history:
                item = QListWidgetItem("暂无历史记录")
                item.setData(Qt.ItemDataRole.UserRole, None)
                self.history_list.addItem(item)
                return
            
            for song in history:
                name = song.get('name', '未命名歌曲')
                genre = song.get('genre', '')
                mood = song.get('mood', '')
                play_count = song.get('play_count', 0)
                
                # 构建显示文本
                display_text = name
                if genre or mood:
                    details = []
                    if genre:
                        details.append(genre)
                    if mood:
                        details.append(mood)
                    display_text += f" ({' | '.join(details)})"
                
                if play_count > 0:
                    display_text += f" - 播放{play_count}次"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, song)
                self.history_list.addItem(item)
            
            logger.info(f"✅ 已加载{len(history)}条历史记录")
            
        except Exception as e:
            logger.error(f"❌ 加载历史记录失败: {e}")
    
    def on_history_item_clicked(self, item: QListWidgetItem):
        """历史项目点击"""
        try:
            song_data = item.data(Qt.ItemDataRole.UserRole)
            if song_data and song_data.get('url'):
                # 构建歌曲信息
                song_info = {
                    'song_name': song_data.get('name', '未命名歌曲'),
                    'audio_url': song_data.get('url', ''),
                    'duration': song_data.get('duration', 0),
                    'genre': song_data.get('genre', ''),
                    'mood': song_data.get('mood', ''),
                    'gender': song_data.get('gender', ''),
                    'prompt': song_data.get('prompt', '')
                }
                
                self.load_song(song_info)
                
                # 隐藏历史列表
                self.toggle_history()
                
        except Exception as e:
            logger.error(f"❌ 播放历史歌曲失败: {e}")
    
    def on_position_changed(self, position: int):
        """播放位置变化"""
        if not self.progress_slider.isSliderDown():
            duration = self.music_player.get_duration()
            if duration > 0:
                progress = int((position / duration) * 100)
                self.progress_slider.setValue(progress)
    
    def on_duration_changed(self, duration: int):
        """时长变化"""
        self.total_time_label.setText(format_time(duration))
    
    def on_state_changed(self, state: int):
        """播放状态变化"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("⏸")
        else:
            self.play_button.setText("▶")
    
    def on_player_error(self, error_msg: str):
        """播放器错误"""
        logger.error(f"❌ 播放器错误: {error_msg}")
        self.song_info_label.setText(f"播放错误: {error_msg}")
    
    def on_media_loaded(self):
        """媒体加载完成"""
        logger.info("✅ 音频加载完成")
    
    def on_progress_pressed(self):
        """进度条按下"""
        pass
    
    def on_progress_released(self):
        """进度条释放，设置播放位置"""
        try:
            duration = self.music_player.get_duration()
            if duration > 0:
                position = int((self.progress_slider.value() / 100) * duration)
                self.music_player.set_position(position)
        except Exception as e:
            logger.error(f"❌ 设置播放位置失败: {e}")
    
    def update_progress(self):
        """更新进度显示"""
        try:
            position = self.music_player.get_position()
            self.current_time_label.setText(format_time(position))
        except Exception as e:
            logger.error(f"❌ 更新进度失败: {e}")
    
    def on_new_generation_clicked(self):
        """新建音乐按钮点击"""
        self.new_generation_requested.emit()
    
    def cleanup(self):
        """清理资源"""
        try:
            self.update_timer.stop()
            self.music_player.cleanup()
            logger.info("🧹 播放界面资源已清理")
        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}")