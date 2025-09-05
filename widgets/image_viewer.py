# -*- coding: utf-8 -*-
"""自定义图片查看器"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QWidget, QFrame)
from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtGui import QPixmap
import os
import logging

logger = logging.getLogger(__name__)


class ImageViewer(QDialog):
    """自定义图片查看器"""
    
    save_requested = Signal(str)
    
    def __init__(self, image_paths, current_index=0, parent=None):
        super().__init__(parent)
        self.image_paths = image_paths
        self.current_index = current_index
        self.setup_ui()
        self.load_current_image()
        
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("图片查看器")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.setFixedSize(1024, 600)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 图片显示区域
        self.image_container = QWidget()
        self.image_container.setStyleSheet("background-color: rgba(0, 0, 0, 0.9);")
        image_layout = QVBoxLayout(self.image_container)
        image_layout.setAlignment(Qt.AlignCenter)
        
        # 图片标签
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 450)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: transparent;
                border: 2px solid #74b9ff;
                border-radius: 10px;
            }
        """)
        image_layout.addWidget(self.image_label)
        
        main_layout.addWidget(self.image_container, 1)
        
        # 底部控制栏
        bottom_container = QFrame()
        bottom_container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 0.8);
                border-top: 2px solid #74b9ff;
            }
        """)
        bottom_container.setFixedHeight(80)
        
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        bottom_layout.setSpacing(20)
        
        # 上一张按钮
        self.prev_btn = QPushButton("上一张")
        self.prev_btn.setFixedSize(100, 40)
        self.prev_btn.setStyleSheet("""
            QPushButton {
                background-color: #74b9ff;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0984e3;
            }
            QPushButton:disabled {
                background-color: #636e72;
                color: #b2bec3;
            }
        """)
        self.prev_btn.clicked.connect(self.show_previous)
        bottom_layout.addWidget(self.prev_btn)
        
        bottom_layout.addStretch()
        
        # 退出按钮
        self.exit_btn = QPushButton("退出")
        self.exit_btn.setFixedSize(100, 40)
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff6b6b;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d63031;
            }
        """)
        self.exit_btn.clicked.connect(self.close)
        bottom_layout.addWidget(self.exit_btn)
        
        bottom_layout.addStretch()
        
        # 保存到U盘按钮（仅发出请求信号，实际保存与提示交给上层处理）
        self.save_btn = QPushButton("保存到U盘")
        self.save_btn.setFixedSize(100, 40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 12px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #00cec9;
            }
        """)
        self.save_btn.clicked.connect(self.save_image)
        bottom_layout.addWidget(self.save_btn)
        
        bottom_layout.addStretch()
        
        # 下一张按钮
        self.next_btn = QPushButton("下一张")
        self.next_btn.setFixedSize(100, 40)
        self.next_btn.setStyleSheet(self.prev_btn.styleSheet())
        self.next_btn.clicked.connect(self.show_next)
        bottom_layout.addWidget(self.next_btn)
        
        main_layout.addWidget(bottom_container)
        
        # 更新按钮状态
        self.update_navigation_buttons()
    
    def load_current_image(self):
        """加载当前图片"""
        if 0 <= self.current_index < len(self.image_paths):
            path = self.image_paths[self.current_index]
            if os.path.exists(path):
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(QSize(780, 430), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled)
                    return
        self.image_label.setText("图片加载失败")
    
    def show_previous(self):
        """显示上一张图片"""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            self.update_navigation_buttons()
    
    def show_next(self):
        """显示下一张图片"""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_current_image()
            self.update_navigation_buttons()
    
    def update_navigation_buttons(self):
        """更新导航按钮状态"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_paths) - 1)
    
    def save_image(self):
        """请求保存当前图片到U盘（仅发信号，不在本对话框内做保存或弹提示）"""
        if 0 <= self.current_index < len(self.image_paths):
            path = self.image_paths[self.current_index]
            logger.info(f"请求保存到U盘: {path}")
            self.save_requested.emit(path)
    
    def keyPressEvent(self, event):
        """键盘事件处理"""
        if event.key() == Qt.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)