# -*- coding: utf-8 -*-
"""配置管理模块"""

import os
from dataclasses import dataclass
from typing import List
import getpass


@dataclass
class Config:
    """应用配置"""

    # API配置 - 使用环境变量，提高安全性
    API_KEY: str = os.getenv("API_KEY", "da092e1c-5988-43d2-ae0b-e1c2dd70f41e")
    BASE_URL: str = os.getenv("BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "doubao-seedream-3-0-t2i-250415")

    # 语音识别配置 - 使用环境变量
    ASR_APP_ID: str = os.getenv("ASR_APP_ID", "6505759856")
    ASR_TOKEN: str = os.getenv("ASR_TOKEN", "eLnTRrJoZpztOD_hP4AO4m4mJaD0eQH2")
    ASR_SECRET: str = os.getenv("ASR_SECRET", "ClwFYkQ-WwP7y04_sYw-0Fo9ZMWQtGHD")
    ASR_CLUSTER: str = os.getenv("ASR_CLUSTER", "volcengine_streaming_common")
    ASR_WS_URL: str = os.getenv("ASR_WS_URL", "wss://openspeech.bytedance.com/api/v2/asr")

    # 音频配置
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1
    BIT_DEPTH: int = 16
    CHUNK_SIZE: int = 512
    MAX_RECORD_TIME: int = 30  # 最大录音时长（秒）
    MIN_RECORD_TIME: float = 0.5  # 最小录音时长（秒）

    # UI配置
    WINDOW_TITLE: str = "AI语音画聊 · 用说话生成专属图片"
    DEFAULT_MIC_NAME: str = "MIC"
    MAX_PROMPT_LENGTH: int = 200  # 最大提示词长度

    # 文件配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_IMAGE_FORMATS: List[str] = None

    # 安全配置
    MAX_RETRIES: int = 3
    REQUEST_TIMEOUT: int = 30
    WS_TIMEOUT: int = 30

    # 风格列表
    STYLES: List[dict] = None


    # 本地保存地址
    SAVE_DIR: str = os.getenv("SAVE_DIR", os.path.expanduser("~/Pictures/AI语音生图"))

    # u盘扫描目录列表
    USB_MOUNT_DIRS: List[str] = None

    # 是否在启动时尝试关闭U盘自动打开
    DISABLE_USB_AUTO_OPEN: bool = os.getenv("DISABLE_USB_AUTO_OPEN", False) == False
    def __post_init__(self):
        """初始化风格列表和其他配置"""
        self.ALLOWED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

        self.STYLES = [
            {"name": "动漫表情包", "prompt": "anime style, cute expression, emoticon, high quality", "image": "anime_style.jpg", "background": "anime_style_bg.jpg"},
            {"name": "黑白写实风格", "prompt": "black and white, realistic, photography, professional", "image": "realistic_bw.jpg", "background": "realistic_bw_bg.jpg"},
            {"name": "像素风格", "prompt": "pixel art, 8-bit style, retro game, detailed", "image": "pixel_art.jpg", "background": "pixel_art_bg.jpg"},
            {"name": "水彩手绘风格", "prompt": "watercolor painting, hand-drawn, artistic, soft colors", "image": "watercolor.jpg", "background": "watercolor_bg.jpg"},
            {"name": "赛博朋克风格", "prompt": "cyberpunk, neon lights, futuristic, high tech", "image": "cyberpunk.jpg", "background": "cyberpunk_bg.jpg"},
            {"name": "极简扁平风格", "prompt": "minimalist, flat design, simple shapes, clean", "image": "minimalist.jpg", "background": "minimalist_bg.jpg"},
            {"name": "油画质感风格", "prompt": "oil painting, textured, classical art, masterpiece", "image": "oil_painting.jpg", "background": "oil_painting_bg.jpg"},
            {"name": "3D卡通风格", "prompt": "3D cartoon, pixar style, cute character, rendered", "image": "3d_cartoon.jpg", "background": "3d_cartoon_bg.jpg"},
            {"name": "国风水墨风格", "prompt": "chinese ink painting, traditional art, elegant", "image": "chinese_ink.jpg", "background": "chinese_ink_bg.jpg"},
            {"name": "蒸汽波风格", "prompt": "vaporwave, aesthetic, retro 80s, synthwave", "image": "vaporwave.jpg", "background": "vaporwave_bg.jpg"},
            {"name": "写实摄影风格", "prompt": "photorealistic, professional photography, detailed", "image": "photography.jpg", "background": "photography_bg.jpg"},
            {"name": "故障艺术风格", "prompt": "glitch art, digital distortion, experimental, modern", "image": "glitch_art.jpg", "background": "glitch_art_bg.jpg"}
        ]

        # 保存目录就绪
        try:
            os.makedirs(self.SAVE_DIR, exist_ok=True)

        except Exception:
            pass
        # U盘扫描目录
        user = getpass.getuser()
        self.USB_MOUNT_DIRS = [
            f"/media/{user}", f"/run/media/{user}", "/mnt/usb", "/media/usb", "/media"
        ]

    @classmethod
    def get_instance(cls):
        """获取配置实例"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance

    def validate_api_config(self):
        """验证API配置"""
        if not self.API_KEY or len(self.API_KEY) < 10:
            raise ValueError("API_KEY 配置无效")
        if not self.BASE_URL.startswith(('http://', 'https://')):
            raise ValueError("BASE_URL 格式无效")
        if not self.ASR_APP_ID or not self.ASR_TOKEN:
            raise ValueError("语音识别配置无效")