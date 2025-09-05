# -*- coding: utf-8 -*-
"""图片显示页面"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QGridLayout, QDialog)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QSize
from PySide6.QtGui import QPixmap, QMovie
from styles.app_styles import AppStyles
from threads.image_gen_thread import ImageGenThread
from widgets.image_viewer import ImageViewer
from widgets.toast import Toast, show_toast_anywhere

from utils.config import Config
from utils.usb_utils import first_usb_mount  # 如果你的工具方法在别处，按实际导入
import shutil
from datetime import datetime
from PySide6.QtWidgets import QApplication

import os
import logging

logger = logging.getLogger(__name__)


class ImageThumbnail(QLabel):
    """图片缩略图"""

    clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = ""
        self.setFixedSize(220, 220)
        self.setScaledContents(True)
        self.setStyleSheet(AppStyles.THUMBNAIL)
        self.setCursor(Qt.PointingHandCursor)
        self.setAlignment(Qt.AlignCenter)

    def set_image(self, path):
        """设置图片"""
        self.image_path = path
        if os.path.exists(path):
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio,
                                       Qt.SmoothTransformation)
                self.setPixmap(scaled)
            else:
                self.setText("加载失败")
        else:
            self.setText("加载中...")

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton and self.image_path:
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class ImageDisplayPage(QWidget):
    """图片显示页面"""

    back_clicked = Signal()
    back_to_style_clicked = Signal()
    regenerate_clicked = Signal()

    def __init__(self):
        super().__init__()
        self.generated_images = []
        self.generation_threads = []
        self.idle_timer = None
        self.setup_ui()
        self.setup_idle_timer()

    def setup_ui(self):
        """设置UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(50, 30, 50, 30)
        main_layout.setSpacing(20)

        # 主容器
        main_container = QWidget()
        main_container_layout = QVBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(20)
        main_layout.addWidget(main_container, 1)

        # 标题
        title_label = QLabel("生成结果")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(AppStyles.TITLE_STYLE_PAGE)
        main_container_layout.addWidget(title_label)

        # 加载动画容器
        self.loading_container = QWidget()
        self.loading_container.setMinimumHeight(400)
        loading_layout = QVBoxLayout(self.loading_container)
        loading_layout.setAlignment(Qt.AlignCenter)
        main_container_layout.addWidget(self.loading_container)

        # 加载动画
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignCenter)
        loading_layout.addWidget(self.loading_label)

        loading_gif_path = "Icon/loading.gif"
        if os.path.exists(loading_gif_path):
            self.loading_movie = QMovie(loading_gif_path)
            self.loading_movie.setScaledSize(QSize(120, 120))
            self.loading_label.setMovie(self.loading_movie)
        else:
            self.loading_label.setText("⏳ 生成中...")
            self.loading_label.setStyleSheet("font-size: 48px;")

        self.loading_hint = QLabel("AI正在创作，请稍候...")
        self.loading_hint.setAlignment(Qt.AlignCenter)
        self.loading_hint.setStyleSheet(AppStyles.LOADING_HINT)
        loading_layout.addWidget(self.loading_hint)

        # 图片网格容器
        self.grid_container = QWidget()
        self.grid_container.setVisible(False)
        main_container_layout.addWidget(self.grid_container, 1)

        grid_layout = QGridLayout(self.grid_container)
        grid_layout.setSpacing(15)  # 减小图片之间的间距
        grid_layout.setContentsMargins(250, 15, 250, 15)  # 增加左右边距，让四宫格居中

        # 创建4个缩略图
        self.thumbnails = []
        for i in range(2):
            for j in range(2):
                thumbnail = ImageThumbnail()
                thumbnail.clicked.connect(self.show_full_image)
                grid_layout.addWidget(thumbnail, i, j)
                self.thumbnails.append(thumbnail)

        # 底部按钮
        bottom_layout = QHBoxLayout()
        main_container_layout.addLayout(bottom_layout)

        # 左下角返回按钮（返回到风格选择）
        self.back_to_style_btn = QPushButton("返回风格选择")
        self.back_to_style_btn.setFixedSize(120, 40)
        self.back_to_style_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.back_to_style_btn.setCursor(Qt.PointingHandCursor)
        self.back_to_style_btn.clicked.connect(self.back_to_style)
        self.back_to_style_btn.setVisible(False)
        bottom_layout.addWidget(self.back_to_style_btn)

        bottom_layout.addStretch()

        # 重新生成按钮
        self.regenerate_btn = QPushButton("重新生成")
        self.regenerate_btn.setFixedSize(120, 40)
        self.regenerate_btn.setStyleSheet(AppStyles.REGENERATE_BUTTON)
        self.regenerate_btn.setCursor(Qt.PointingHandCursor)
        self.regenerate_btn.clicked.connect(self.on_regenerate)
        self.regenerate_btn.setVisible(False)
        bottom_layout.addWidget(self.regenerate_btn)

        # 底部返回按钮（返回到语音识别）
        self.back_btn = QPushButton("返回")
        self.back_btn.setFixedSize(100, 40)
        self.back_btn.setStyleSheet(AppStyles.BACK_BUTTON)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_clicked)
        self.back_btn.setVisible(False)
        bottom_layout.addWidget(self.back_btn)

    def generate_images(self, prompt):
        """生成图片"""
        logger.info(f"开始生成图片: {prompt}")

        # 清理之前的线程
        self.stop_all_threads()

        # 显示加载动画
        self.loading_container.setVisible(True)
        self.grid_container.setVisible(False)
        self.regenerate_btn.setVisible(False)

        if hasattr(self, 'loading_movie'):
            self.loading_movie.start()

        # 清空之前的图片
        self.generated_images = []
        for thumbnail in self.thumbnails:
            thumbnail.set_image("")
            thumbnail.setText("生成中...")

        # 启动4个生成线程
        for i in range(4):
            thread = ImageGenThread(prompt)
            thread.result.connect(lambda path, idx=i: self.on_image_generated(path, idx))
            thread.error.connect(lambda err, idx=i: self.on_generation_error(err, idx))
            self.generation_threads.append(thread)
            thread.start()

            # 错开启动时间，减少服务器压力
            QTimer.singleShot(i * 1000, thread.start)

    @Slot(str, int)
    def on_image_generated(self, path, index):
        """图片生成完成"""
        logger.info(f"图片 {index} 生成完成: {path}")

        if path and os.path.exists(path):
            self.generated_images.append(path)
            self.thumbnails[index].set_image(path)
        else:
            self.thumbnails[index].setText("生成失败")

        # 检查是否全部完成
        self.check_all_completed()

    @Slot(str, int)
    def on_generation_error(self, error, index):
        """生成错误"""
        logger.error(f"图片 {index} 生成失败: {error}")
        self.thumbnails[index].setText("生成失败")
        self.check_all_completed()

    def check_all_completed(self):
        """检查是否全部完成"""
        # 检查所有线程是否完成
        all_finished = all(not thread.isRunning() for thread in self.generation_threads)

        if all_finished:
            logger.info("所有图片生成完成")

            # 停止加载动画
            if hasattr(self, 'loading_movie'):
                self.loading_movie.stop()

            # 显示图片网格和按钮
            self.loading_container.setVisible(False)
            self.grid_container.setVisible(True)
            self.regenerate_btn.setVisible(True)
            self.back_btn.setVisible(True)
            self.back_to_style_btn.setVisible(True)

            # 启动空闲定时器
            self.reset_idle_timer()

    @Slot(str)
    def show_full_image(self, path):
        """显示大图 - 使用自定义图片查看器"""
        if not self.generated_images:
            return
        
        # 找到当前图片的索引
        try:
            current_index = self.generated_images.index(path)
        except ValueError:
            current_index = 0
        
        # 创建自定义图片查看器
        viewer = ImageViewer(self.generated_images, current_index, self)
        viewer.save_requested.connect(self.on_image_save_requested)
        viewer.exec()
    
    @Slot(str)
    def on_image_save_requested(self, path):
        logger.info(f"用户请求保存图片: {path}")

        # 首先检查文件是否存在
        if not os.path.exists(path):
            logger.error(f"文件不存在: {path}")
            parent = QApplication.activeWindow() or self.window()
            Toast.show_toast(parent, "图片文件不存在，无法保存", duration=2000, bg="rgba(231, 76, 60, 220)")
            return

        # 示例：保存到 U 盘
        usb_root = first_usb_mount(Config.get_instance().USB_MOUNT_DIRS)
        if not usb_root:
            # 在当前活动窗口上显示 Toast，确保覆盖在 ImageViewer 对话框上
            parent = QApplication.activeWindow() or self.window()
            Toast.show_toast(parent, "未检测到U盘，请插入后重试", duration=2000, bg="rgba(231, 76, 60, 220)")
            return

        try:
            target_dir = os.path.join(usb_root, "AI语音生图")
            os.makedirs(target_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = os.path.splitext(path)[1].lower() or ".png"
            dst = os.path.join(target_dir, f"image_{ts}{ext}")
            shutil.copy2(path, dst)

            parent = QApplication.activeWindow() or self.window()
            Toast.show_toast(parent, "保存成功，已复制到U盘", duration=2000, bg="rgba(255, 140, 0, 210)")
        except Exception as e:
            logger.error(f"保存到U盘失败: {e}")
            parent = QApplication.activeWindow() or self.window()
            Toast.show_toast(parent, f"保存失败：{e}", duration=2200, bg="rgba(231, 76, 60, 220)")

    @Slot()
    def back_to_style(self):
        """返回到风格选择页面"""
        self.back_to_style_clicked.emit()

    def setup_idle_timer(self):
        """设置空闲定时器"""
        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self.on_idle_timeout)
        self.reset_idle_timer()

    def reset_idle_timer(self):
        """重置空闲定时器"""
        if self.idle_timer:
            self.idle_timer.stop()
            self.idle_timer.start(60000)  # 1分钟 = 60000毫秒

    def on_idle_timeout(self):
        """空闲超时处理"""
        logger.info("空闲超时，返回风格选择并删除生成图片")
        self.delete_generated_images()
        self.back_to_style_clicked.emit()

    def delete_generated_images(self):
        """删除生成的图片"""
        for image_path in self.generated_images:
            try:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    logger.info(f"已删除图片: {image_path}")
            except Exception as e:
                logger.error(f"删除图片失败 {image_path}: {e}")
        self.generated_images = []

    def mousePressEvent(self, event):
        """鼠标点击事件 - 重置空闲定时器"""
        self.reset_idle_timer()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        """键盘事件 - 重置空闲定时器"""
        self.reset_idle_timer()
        super().keyPressEvent(event)

    @Slot()
    def on_regenerate(self):
        """重新生成"""
        self.reset_idle_timer()
        self.regenerate_clicked.emit()

    def stop_all_threads(self):
        """停止所有线程"""
        for thread in self.generation_threads:
            if thread.isRunning():
                thread.stop()
                thread.quit()
                thread.wait()
        self.generation_threads.clear()