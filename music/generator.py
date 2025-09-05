#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音乐生成API客户端
提供歌词生成、完整歌曲生成、任务查询等功能
"""

import json
import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from PySide6.QtCore import QThread, Signal

from config import ACCESS_KEY, SECRET_KEY, get_music_config, get_app_config
from music.sign import create_request_headers, prepare_request_data, get_url

logger = logging.getLogger(__name__)


class MusicGenerationError(Exception):
    """音乐生成异常"""
    pass


class MusicAPIClient:
    """火山引擎音乐生成API客户端"""
    
    def __init__(self):
        self.music_config = get_music_config()
        self.app_config = get_app_config()
        self.access_key = ACCESS_KEY
        self.secret_key = SECRET_KEY
        
    def _make_request(self, action: str, data: Dict[str, Any], method: str = "POST") -> Tuple[bool, Any]:
        """
        发送API请求
        
        Args:
            action: API操作名
            data: 请求数据
            method: HTTP方法
            
        Returns:
            (成功标志, 响应数据或错误信息)
        """
        try:
            # 准备请求数据
            body_str = prepare_request_data(data) if data else ""
            
            # 创建请求头
            headers = create_request_headers(
                self.access_key, self.secret_key, method,
                self.music_config.HOST, body_str, action,
                self.music_config.VERSION, self.music_config.REGION
            )
            
            # 构建URL
            url = get_url(
                self.music_config.HOST, action, 
                self.music_config.VERSION, self.music_config.REGION
            )
            
            logger.info(f"🎵 发送{action}请求: {url}")
            
            # 发送请求
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=self.app_config.REQUEST_TIMEOUT)
            else:
                response = requests.post(url, data=body_str, headers=headers, timeout=self.app_config.REQUEST_TIMEOUT)
            
            # 检查响应状态
            if response.status_code != 200:
                logger.error(f"❌ HTTP错误: {response.status_code}")
                return False, f"HTTP错误: {response.status_code}"
            
            # 解析响应
            result = response.json()
            
            # 检查业务错误
            if 'ResponseMetadata' in result and 'Error' in result['ResponseMetadata']:
                error = result['ResponseMetadata']['Error']
                error_msg = f"{error.get('Code', 'Unknown')}: {error.get('Message', '未知错误')}"
                logger.error(f"❌ API错误: {error_msg}")
                return False, error_msg
            
            return True, result.get('Result', result)
            
        except requests.exceptions.Timeout:
            logger.error("❌ 请求超时")
            return False, "请求超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            logger.error("❌ 网络连接错误")
            return False, "网络连接失败，请检查网络"
        except Exception as e:
            logger.error(f"❌ 请求异常: {e}")
            return False, f"请求失败: {str(e)}"
    
    def generate_lyrics(self, prompt: str, gender: str, genre: str, mood: str, 
                       length: str = "Medium") -> Tuple[bool, Any]:
        """
        生成歌词
        
        Args:
            prompt: 歌词主题描述
            gender: 歌声性别 (Male/Female/Neutral)
            genre: 音乐风格 
            mood: 音乐情绪
            length: 歌词长度 (Short/Medium/Long)
            
        Returns:
            (成功标志, 歌词内容或错误信息)
        """
        data = {
            "prompt": prompt,
            "gender": gender,
            "genre": genre,
            "mood": mood,
            "length": length
        }
        
        success, result = self._make_request(self.music_config.GEN_LYRICS_ACTION, data)
        
        if success:
            lyrics = result.get('Lyrics', '')
            lyricist = result.get('Lyricist', '')
            logger.info(f"✅ 歌词生成成功，作者: {lyricist}")
            return True, {'lyrics': lyrics, 'lyricist': lyricist}
        else:
            return False, result
    
    def generate_song(self, prompt: str, gender: str, genre: str, mood: str, 
                     tempo: Optional[str] = None) -> Tuple[bool, Any]:
        """
        开始生成完整歌曲（异步任务）
        
        Args:
            prompt: 歌曲主题描述
            gender: 歌声性别
            genre: 音乐风格
            mood: 音乐情绪
            tempo: 节奏（可选，80-120）
            
        Returns:
            (成功标志, 任务信息或错误信息)
        """
        data = {
            "prompt": prompt,
            "gender": gender,
            "genre": genre,
            "mood": mood
        }
        
        if tempo:
            data["tempo"] = tempo
        
        success, result = self._make_request(self.music_config.GEN_SONG_ACTION, data)
        
        if success:
            task_id = result.get('TaskID', '')
            predicted_wait_time = result.get('PredictedWaitTime', 30)
            logger.info(f"✅ 歌曲生成任务已创建: {task_id}, 预计等待: {predicted_wait_time}秒")
            return True, {
                'task_id': task_id,
                'predicted_wait_time': predicted_wait_time
            }
        else:
            return False, result
    
    def query_song(self, task_id: str) -> Tuple[bool, Any]:
        """
        查询歌曲生成状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            (成功标志, 任务状态信息或错误信息)
        """
        data = {"TaskID": task_id}
        
        success, result = self._make_request(self.music_config.QUERY_SONG_ACTION, data)
        
        if success:
            status = result.get('Status', 0)
            progress = result.get('Progress', 0)
            
            if status == self.music_config.QUERY_STATUS_SUCCESS:
                song_detail = result.get('SongDetail', {})
                audio_url = song_detail.get('AudioUrl', '')
                song_name = song_detail.get('SongName', '')
                duration = song_detail.get('Duration', 0)
                
                logger.info(f"✅ 歌曲生成完成: {song_name}")
                return True, {
                    'status': status,
                    'progress': progress,
                    'audio_url': audio_url,
                    'song_name': song_name,
                    'duration': duration,
                    'song_detail': song_detail
                }
            elif status == self.music_config.QUERY_STATUS_FAILED:
                fail_reason = result.get('FailReason', '未知原因')
                logger.error(f"❌ 歌曲生成失败: {fail_reason}")
                return False, f"生成失败: {fail_reason}"
            else:
                # 仍在处理中
                logger.info(f"🔄 歌曲生成中... 进度: {progress}%")
                return True, {
                    'status': status,
                    'progress': progress
                }
        else:
            return False, result
    
    def query_usage(self) -> Tuple[bool, Any]:
        """
        查询服务使用量
        
        Returns:
            (成功标志, 使用量信息或错误信息)
        """
        success, result = self._make_request(self.music_config.QUERY_USAGE_ACTION, {}, method="GET")
        
        if success:
            logger.info("📊 使用量查询成功")
            return True, result
        else:
            return False, result


class MusicGenerationThread(QThread):
    """音乐生成线程"""
    
    # 信号定义
    lyrics_ready = Signal(dict)  # 歌词生成完成
    song_task_created = Signal(dict)  # 歌曲任务创建成功
    progress_updated = Signal(int)  # 进度更新
    song_ready = Signal(dict)  # 歌曲生成完成
    error_occurred = Signal(str)  # 错误发生
    
    def __init__(self, prompt: str, gender: str, genre: str, mood: str, 
                 generate_full_song: bool = True):
        super().__init__()
        self.prompt = prompt
        self.gender = gender
        self.genre = genre
        self.mood = mood
        self.generate_full_song = generate_full_song
        self.client = MusicAPIClient()
        self._stop_requested = False
        
    def stop(self):
        """停止生成"""
        self._stop_requested = True
        
    def run(self):
        """执行音乐生成"""
        try:
            if self._stop_requested:
                return
                
            # 1. 生成歌词（可选）
            if not self.generate_full_song:
                success, result = self.client.generate_lyrics(
                    self.prompt, self.gender, self.genre, self.mood
                )
                if success:
                    self.lyrics_ready.emit(result)
                else:
                    self.error_occurred.emit(result)
                return
            
            # 2. 开始生成完整歌曲
            success, result = self.client.generate_song(
                self.prompt, self.gender, self.genre, self.mood
            )
            
            if not success:
                self.error_occurred.emit(result)
                return
            
            task_id = result['task_id']
            predicted_wait_time = result['predicted_wait_time']
            
            self.song_task_created.emit(result)
            
            if self._stop_requested:
                return
            
            # 3. 等待预计时间
            time.sleep(min(predicted_wait_time, 5))  # 最多等待5秒
            
            # 4. 轮询任务状态
            max_attempts = 60  # 最多轮询5分钟
            attempt = 0
            
            while attempt < max_attempts and not self._stop_requested:
                success, result = self.client.query_song(task_id)
                
                if not success:
                    self.error_occurred.emit(result)
                    return
                
                status = result['status']
                progress = result.get('progress', 0)
                
                # 更新进度
                self.progress_updated.emit(progress)
                
                if status == self.client.music_config.QUERY_STATUS_SUCCESS:
                    # 生成成功
                    self.song_ready.emit(result)
                    return
                elif status == self.client.music_config.QUERY_STATUS_FAILED:
                    # 生成失败
                    self.error_occurred.emit("歌曲生成失败")
                    return
                
                # 继续等待
                time.sleep(5)
                attempt += 1
            
            if not self._stop_requested:
                self.error_occurred.emit("歌曲生成超时，请稍后重试")
                
        except Exception as e:
            logger.error(f"❌ 音乐生成线程异常: {e}")
            if not self._stop_requested:
                self.error_occurred.emit(f"生成异常: {str(e)}")