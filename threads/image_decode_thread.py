import os
import time
from PySide6.QtCore import QThread, Signal
from PIL import Image as PILImage, ImageFile, UnidentifiedImageError

# 允许加载截断的图片，避免网络/移动过程中出现的半截图导致解码失败
ImageFile.LOAD_TRUNCATED_IMAGES = True


class ImageDecodeThread(QThread):
    """后台解码并按目标高度缩放图片，返回 RGB 原始字节"""
    result = Signal(int, int, bytes)
    error = Signal(str)

    def __init__(self, image_path: str, target_h: int = 250, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.target_h = target_h
        self._stop = False

    def run(self):
        try:
            if not os.path.exists(self.image_path):
                self.error.emit("图片不存在")
                return

            # 短重试：文件可能刚移动/写入，稍等片刻
            im = None
            last_err = None
            for _ in range(3):
                if self._stop:
                    return
                try:
                    im = PILImage.open(self.image_path)
                    break
                except (UnidentifiedImageError, OSError) as e:
                    last_err = e
                    time.sleep(0.05)

            if im is None:
                self.error.emit(f"图片打开失败: {last_err}")
                return

            with im:
                if self._stop:
                    return

                # 转换并确保真正解码完成（load）
                im = im.convert('RGB')
                im.load()

                w, h = im.size
                if w <= 0 or h <= 0:
                    self.error.emit("图片尺寸异常")
                    return

                new_w = max(1, int(w * self.target_h / h))
                if self._stop:
                    return

                # 高质量缩放
                im = im.resize((new_w, self.target_h), PILImage.Resampling.LANCZOS)
                if self._stop:
                    return

                data = im.tobytes("raw", "RGB")
                self.result.emit(new_w, self.target_h, data)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._stop = True