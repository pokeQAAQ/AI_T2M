# threads/image_gen_thread.py
# -*- coding: utf-8 -*-
"""图片生成线程 - 支持本地保存并转换为 PNG 缩略图 - 增强安全性"""

import os
import tempfile
import requests
import logging
from PySide6.QtCore import QThread, Signal
from volcenginesdkarkruntime import Ark
from utils.config import Config
from utils.image_utils import ImageUtils
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class ImageGenThread(QThread):
    result = Signal(str)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
        self.config = Config.get_instance()
        self._stop_requested = False

    def stop(self):
        """停止生成"""
        self._stop_requested = True

    def download_image(self, url):
        """下载图片，增加安全检查"""
        try:
            if self._stop_requested:
                return None

            self.progress.emit("正在下载图片...")

            # 验证URL
            if not url or not url.startswith(('http://', 'https://')):
                logger.error(f"无效的图片URL: {url}")
                return None

            # 下载文件
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (compatible; AI-Image-Generator/1.0)'
            })

            response = session.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()

            # 检查内容类型
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                logger.error(f"无效的内容类型: {content_type}")
                return None

            # 检查文件大小
            content_length = response.headers.get('content-length')
            if content_length:
                size = int(content_length)
                if size > self.config.MAX_FILE_SIZE:
                    logger.error(f"文件过大: {size} bytes")
                    return None

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.jpg',
                delete=False,
                prefix='generated_image_'
            )

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(temp_file.name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_requested:
                        try:
                            os.unlink(temp_file.name)
                        except:
                            pass
                        return None

                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # 检查大小限制
                        if downloaded > self.config.MAX_FILE_SIZE:
                            logger.error("下载文件超过大小限制")
                            try:
                                os.unlink(temp_file.name)
                            except:
                                pass
                            return None

                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress.emit(f"下载中... {progress}%")

            # 验证下载的文件
            if not os.path.exists(temp_file.name) or os.path.getsize(temp_file.name) == 0:
                logger.error("下载的文件为空")
                return None

            logger.info(f"✅ 图片已下载到: {temp_file.name} ({downloaded} bytes)")
            return temp_file.name

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            return None

    def run(self):
        try:
            if self._stop_requested:
                return

            # 验证输入
            if not self.prompt or not self.prompt.strip():
                self.error.emit("提示词不能为空")
                return

            # 过滤提示词中的敏感内容（简单示例）
            filtered_prompt = self.filter_prompt(self.prompt.strip())
            if not filtered_prompt:
                self.error.emit("提示词包含不当内容")
                return

            self.progress.emit("正在生成图片...")
            logger.info(f"开始生成图片，提示词: {filtered_prompt}")

            try:
                client = Ark(
                    base_url=self.config.BASE_URL,
                    api_key=self.config.API_KEY,
                    timeout=self.config.REQUEST_TIMEOUT
                )

                if self._stop_requested:
                    return

                response = client.images.generate(
                    model=self.config.MODEL_NAME,
                    prompt=filtered_prompt,
                    watermark=False
                )

                if self._stop_requested:
                    return

                if response and response.data and len(response.data) > 0:
                    image_url = response.data[0].url
                    logger.info(f"🔗 获取到图片URL: {image_url}")

                    local_jpg = self.download_image(image_url)
                    if local_jpg and not self._stop_requested:
                        # 转换为安全的PNG格式
                        safe_path = ImageUtils.to_png_thumbnail(local_jpg, max_side=1280)

                        # 保存信息文件用于调试
                        try:
                            os.makedirs(self.config.SAVE_DIR, exist_ok=True)
                            ts_name = datetime.now().strftime("%Y%m%d_%H%M%S_%f") + ".png"
                            final_path = os.path.join(self.config.SAVE_DIR, ts_name)
                            shutil.move(safe_path, final_path)
                            safe_path = final_path
                            logger.info(f"✅ 图片已移动并重命名: {safe_path}")
                        except Exception as e:
                            logger.warning(f"重命名/移动图片失败: {e}")


                        # 保存信息文件用于调试
                        try:
                            with open("/tmp/last_image_info.txt", "w", encoding='utf-8') as f:
                                f.write(f"URL: {image_url}\n")
                                f.write(f"Local(JPG): {local_jpg}\n")
                                f.write(f"Local(PNG): {safe_path}\n")
                                f.write(f"Prompt: {filtered_prompt}\n")
                        except Exception as e:
                            logger.warning(f"保存调试信息失败: {e}")

                        # 清理原始JPG文件
                        try:
                            if local_jpg != safe_path and os.path.exists(local_jpg):
                                os.remove(local_jpg)
                        except Exception as e:
                            logger.warning(f"清理JPG文件失败: {e}")

                        if not self._stop_requested:
                            self.result.emit(safe_path)
                    else:
                        if not self._stop_requested:
                            self.error.emit("图片下载失败")
                            self.result.emit("")
                else:
                    if not self._stop_requested:
                        self.error.emit("生成失败：未返回图片")
                        self.result.emit("")

            except Exception as e:
                if not self._stop_requested:
                    logger.error(f"API调用失败: {e}")
                    self.error.emit(f"API调用失败：{str(e)}")
                    self.result.emit("")

        except Exception as e:
            if not self._stop_requested:
                logger.error(f"生成错误: {e}")
                self.error.emit(f"生成错误：{str(e)}")
                self.result.emit("")

    def filter_prompt(self, prompt):
        """简单的提示词过滤"""
        # 移除可能的有害内容（这里只是示例，实际应用中需要更完善的过滤）
        sensitive_words = ['violence', 'nsfw', 'explicit', 'harmful']
        prompt_lower = prompt.lower()

        for word in sensitive_words:
            if word in prompt_lower:
                logger.warning(f"检测到敏感词: {word}")
                return None

        # 限制长度
        if len(prompt) > self.config.MAX_PROMPT_LENGTH:
            prompt = prompt[:self.config.MAX_PROMPT_LENGTH]
            logger.info(f"提示词已截断至{self.config.MAX_PROMPT_LENGTH}字符")

        return prompt