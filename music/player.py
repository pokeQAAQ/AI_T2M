#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐播放器模块
支持在线音频流播放、播放控制、进度管理等功能
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from PySide6.QtCore import QObject, Signal, QTimer, QThread
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

from config import get_app_config

logger = logging.getLogger(__name__)


class MusicHistory:
    """音乐历史记录管理"""
    
    def __init__(self, history_file: str = "/tmp/music_history.json"):
        self.history_file = history_file
        self.history: List[Dict] = []
        self.load_history()
    
    def load_history(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ 加载历史记录失败: {e}")
            self.history = []
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"❌ 保存历史记录失败: {e}")
    
    def add_song(self, song_info: Dict):
        """添加歌曲到历史记录"""
        song_record = {
            'name': song_info.get('song_name', '未命名歌曲'),
            'url': song_info.get('audio_url', ''),
            'duration': song_info.get('duration', 0),
            'prompt': song_info.get('prompt', ''),
            'genre': song_info.get('genre', ''),
            'mood': song_info.get('mood', ''),
            'gender': song_info.get('gender', ''),
            'created_time': datetime.now().isoformat(),
            'play_count': 0
        }
        
        # 避免重复
        existing = next((s for s in self.history if s['url'] == song_record['url']), None)
        if existing:
            existing.update(song_record)
        else:
            self.history.insert(0, song_record)
        
        # 限制历史记录数量
        if len(self.history) > 50:
            self.history = self.history[:50]
        
        self.save_history()
        logger.info(f"✅ 歌曲已添加到历史: {song_record['name']}")
    
    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        return self.history.copy()
    
    def increment_play_count(self, url: str):
        """增加播放次数"""
        song = next((s for s in self.history if s['url'] == url), None)
        if song:
            song['play_count'] = song.get('play_count', 0) + 1
            self.save_history()


class MusicDownloadThread(QThread):
    """音乐下载线程"""
    
    download_progress = Signal(int)  # 下载进度
    download_completed = Signal(str)  # 下载完成，返回本地文件路径
    download_failed = Signal(str)  # 下载失败
    
    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path
        self._stop_requested = False
    
    def stop(self):
        """停止下载"""
        self._stop_requested = True
    
    def run(self):
        """执行下载"""
        try:
            logger.info(f"🎵 开始下载音乐: {self.url}")
            
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_requested:
                        logger.info("🛑 下载已取消")
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.download_progress.emit(progress)
            
            logger.info(f"✅ 音乐下载完成: {self.save_path}")
            self.download_completed.emit(self.save_path)
            
        except Exception as e:
            logger.error(f"❌ 音乐下载失败: {e}")
            self.download_failed.emit(str(e))


class MusicPlayer(QObject):
    """音乐播放器"""
    
    # 信号定义
    position_changed = Signal(int)  # 播放位置变化 (毫秒)
    duration_changed = Signal(int)  # 总时长变化 (毫秒)
    state_changed = Signal(int)  # 播放状态变化
    error_occurred = Signal(str)  # 播放错误
    media_loaded = Signal()  # 媒体加载完成
    
    def __init__(self):
        super().__init__()
        self.app_config = get_app_config()
        self.history = MusicHistory()
        
        # 初始化播放器
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # 连接信号
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.playbackStateChanged.connect(self.state_changed)
        self.media_player.errorOccurred.connect(self._handle_error)
        self.media_player.mediaStatusChanged.connect(self._handle_media_status)
        
        # 播放列表
        self.playlist: List[Dict] = []
        self.current_index = -1
        self.current_song: Optional[Dict] = None
        
        # 下载线程
        self.download_thread: Optional[MusicDownloadThread] = None
        
        logger.info("🎵 音乐播放器初始化完成")
    
    def _handle_error(self, error):
        """处理播放错误"""
        error_msg = f"播放错误: {error}"
        logger.error(f"❌ {error_msg}")
        self.error_occurred.emit(error_msg)
    
    def _handle_media_status(self, status):
        """处理媒体状态变化"""
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.media_loaded.emit()
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.error_occurred.emit("无效的音频文件")
    
    def load_song(self, song_info: Dict):
        """
        加载歌曲
        
        Args:
            song_info: 歌曲信息字典，包含audio_url等字段
        """
        try:
            self.current_song = song_info
            audio_url = song_info.get('audio_url', '')
            
            if not audio_url:
                self.error_occurred.emit("无效的音频URL")
                return
            
            logger.info(f"🎵 加载歌曲: {song_info.get('song_name', '未知歌曲')}")
            
            # 直接播放在线音频流
            self.media_player.setSource(QUrl(audio_url))
            
            # 添加到历史记录
            self.history.add_song(song_info)
            
        except Exception as e:
            logger.error(f"❌ 加载歌曲失败: {e}")
            self.error_occurred.emit(f"加载失败: {str(e)}")
    
    def play(self):
        """开始播放"""
        try:
            self.media_player.play()
            if self.current_song:
                self.history.increment_play_count(self.current_song.get('audio_url', ''))
        except Exception as e:
            logger.error(f"❌ 播放失败: {e}")
            self.error_occurred.emit(f"播放失败: {str(e)}")
    
    def pause(self):
        """暂停播放"""
        try:
            self.media_player.pause()
        except Exception as e:
            logger.error(f"❌ 暂停失败: {e}")
    
    def stop(self):
        """停止播放"""
        try:
            self.media_player.stop()
        except Exception as e:
            logger.error(f"❌ 停止失败: {e}")
    
    def set_position(self, position: int):
        """设置播放位置（毫秒）"""
        try:
            self.media_player.setPosition(position)
        except Exception as e:
            logger.error(f"❌ 设置播放位置失败: {e}")
    
    def set_volume(self, volume: float):
        """设置音量 (0.0-1.0)"""
        try:
            self.audio_output.setVolume(max(0.0, min(1.0, volume)))
        except Exception as e:
            logger.error(f"❌ 设置音量失败: {e}")
    
    def get_position(self) -> int:
        """获取当前播放位置（毫秒）"""
        return self.media_player.position()
    
    def get_duration(self) -> int:
        """获取总时长（毫秒）"""
        return self.media_player.duration()
    
    def get_state(self) -> int:
        """获取播放状态"""
        return self.media_player.playbackState()
    
    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.get_state() == QMediaPlayer.PlaybackState.PlayingState
    
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self.get_state() == QMediaPlayer.PlaybackState.PausedState
    
    def is_stopped(self) -> bool:
        """是否已停止"""
        return self.get_state() == QMediaPlayer.PlaybackState.StoppedState
    
    def add_to_playlist(self, song_info: Dict):
        """添加歌曲到播放列表"""
        self.playlist.append(song_info)
        logger.info(f"✅ 歌曲已添加到播放列表: {song_info.get('song_name', '未知歌曲')}")
    
    def clear_playlist(self):
        """清空播放列表"""
        self.playlist.clear()
        self.current_index = -1
    
    def play_next(self):
        """播放下一首"""
        if not self.playlist:
            return
        
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.load_song(self.playlist[self.current_index])
        self.play()
    
    def play_previous(self):
        """播放上一首"""
        if not self.playlist:
            return
        
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.load_song(self.playlist[self.current_index])
        self.play()
    
    def get_history(self) -> List[Dict]:
        """获取播放历史"""
        return self.history.get_history()
    
    def download_song(self, song_info: Dict):
        """
        下载歌曲到本地
        
        Args:
            song_info: 歌曲信息
        """
        try:
            audio_url = song_info.get('audio_url', '')
            song_name = song_info.get('song_name', 'unknown')
            
            if not audio_url:
                self.error_occurred.emit("无效的下载URL")
                return
            
            # 生成本地文件路径
            safe_name = "".join(c for c in song_name if c.isalnum() or c in (' ', '-', '_')).strip()
            local_path = os.path.join(self.app_config.MUSIC_CACHE_DIR, f"{safe_name}.mp3")
            
            # 停止之前的下载
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.stop()
                self.download_thread.wait()
            
            # 开始新的下载
            self.download_thread = MusicDownloadThread(audio_url, local_path)
            self.download_thread.download_completed.connect(
                lambda path: logger.info(f"✅ 歌曲下载完成: {path}")
            )
            self.download_thread.download_failed.connect(
                lambda error: self.error_occurred.emit(f"下载失败: {error}")
            )
            self.download_thread.start()
            
        except Exception as e:
            logger.error(f"❌ 开始下载失败: {e}")
            self.error_occurred.emit(f"下载失败: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        try:
            if self.download_thread and self.download_thread.isRunning():
                self.download_thread.stop()
                self.download_thread.wait()
            
            self.stop()
            logger.info("🧹 音乐播放器资源已清理")
        except Exception as e:
            logger.error(f"❌ 清理资源失败: {e}")


def format_time(milliseconds: int) -> str:
    """
    格式化时间显示
    
    Args:
        milliseconds: 毫秒数
        
    Returns:
        格式化的时间字符串 (mm:ss)
    """
    seconds = milliseconds // 1000
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"