# -*- coding: utf-8 -*-
"""风格选择页面"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PySide6.QtGui import QFont, QPainter, QPixmap, QBrush, QColor, QPen, QPainterPath
from styles.app_styles import AppStyles
from utils.config import Config
import random
import os


class StyleButton(QPushButton):
    """风格按钮"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        # 调整按钮尺寸为三行四列，增加高度让按钮更美观
        self.setFixedSize(200, 150)  # 从 200x120 增加到 200x150
        # 不再设置默认样式，由自定义绘制处理
        self.setCursor(Qt.PointingHandCursor)

        # 鼠标悬停效果
        self.setMouseTracking(True)
        self._animation = None
        self._image_path = None
        self._has_background_image = False
        self._background_pixmap = None
        self._is_hovered = False
        self._is_selected = False
        
        # 设置透明背景以便自定义绘制
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def set_background_image(self, image_path):
        """设置背景图片"""
        if os.path.exists(image_path):
            self._image_path = image_path.replace("\\", "/")  # 确保路径格式正确
            self._has_background_image = True
            
            # 加载背景图片
            self._background_pixmap = QPixmap(image_path)
            if not self._background_pixmap.isNull():
                # 缩放图片以适应按钮尺寸
                self._background_pixmap = self._background_pixmap.scaled(
                    self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            
            # 强制更新显示
            self.update()
        else:
            self._has_background_image = False
            self._background_pixmap = None
            self.update()

    def paintEvent(self, event):
        """自定义绘制事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取按钮区域
        rect = self.rect()
        
        # 绘制圆角矩形背景
        border_color = QColor(123, 87, 230, 77) if not self._is_hovered else QColor(123, 87, 230, 255)
        if self._is_selected:
            border_color = QColor(155, 123, 247, 255)
        
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))  # 透明背景
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 15, 15)
        
        # 绘制背景图片
        if self._has_background_image and self._background_pixmap and not self._background_pixmap.isNull():
            # 计算图片居中位置
            img_rect = self._background_pixmap.rect()
            target_rect = rect.adjusted(2, 2, -2, -2)  # 略微内缩以适应边框
            
            # 保持图片居中
            x = target_rect.x() + (target_rect.width() - img_rect.width()) // 2
            y = target_rect.y() + (target_rect.height() - img_rect.height()) // 2
            
            # 使用QPainterPath实现圆角裁剪
            clip_path = QPainterPath()
            clip_path.addRoundedRect(target_rect, 13, 13)
            painter.setClipPath(clip_path)
            painter.drawPixmap(x, y, self._background_pixmap)
            painter.setClipping(False)
        
        # 绘制底部毛玻璃效果区域
        text_height = 35  # 文字区域高度，适应增加到150的按钮高度
        text_rect = QRect(rect.x() + 2, rect.bottom() - text_height - 2, rect.width() - 4, text_height)
        
        # 毛玻璃背景 - 半透明黑色
        glass_color = QColor(0, 0, 0, 120)  # 黑色半透明
        if self._is_hovered:
            glass_color = QColor(123, 87, 230, 100)  # 悬停时显示紫色
        if self._is_selected:
            glass_color = QColor(155, 123, 247, 120)  # 选中时显示亮紫色
            
        painter.setBrush(QBrush(glass_color))
        painter.setPen(Qt.NoPen)
        # 绘制底部直角矩形（取消圆角）
        painter.drawRect(text_rect)
        
        # 绘制文字
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        font = QFont()
        font.setPointSize(10)  # 字体大小调整为10，适应增加后的按钮高度
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(text_rect, Qt.AlignCenter, self.text())

    def enterEvent(self, event):
        """鼠标进入"""
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._is_hovered = False
        self.update()
        super().leaveEvent(event)
        
    def set_selected(self, selected):
        """设置选中状态"""
        self._is_selected = selected
        self.update()


class StyleSelectorPage(QWidget):
    """风格选择页面"""

    style_selected = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.config = Config.get_instance()
        self.all_styles = self.config.STYLES.copy()
        self.current_batch = 0
        self.batch_size = 12  # 改为12个按钮（3行4列）
        self.selected_style = None
        self.setup_ui()

    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        # 调整整体边距，删除标题后进一步缩小上边距
        layout.setContentsMargins(50, 40, 50, 40)  # 增加上下边距以居中
        layout.setSpacing(0)  # 去掉间距

        # 删除标题

        # 风格按钮容器 - 使用全部空间
        self.button_container = QWidget()
        self.button_container.setStyleSheet(AppStyles.STYLE_CONTAINER)
        # 设置容器的最大高度，适应三行布局（按钮高度增加到150后调整）
        self.button_container.setMaximumHeight(520)
        layout.addWidget(self.button_container)

        # 风格按钮网格 - 三行四列
        self.grid_layout = QGridLayout(self.button_container)
        # 调整间距以适应更多按钮
        self.grid_layout.setHorizontalSpacing(20)  # 水平间距，减小以适应4列
        self.grid_layout.setVerticalSpacing(25)  # 垂直间距
        # 调整容器内边距以居中
        self.grid_layout.setContentsMargins(30, 30, 30, 30)

        # 设置行列的拉伸因子，让布局更均匀
        for row in range(3):  # 三行
            self.grid_layout.setRowStretch(row, 1)
        for col in range(4):  # 四列
            self.grid_layout.setColumnStretch(col, 1)

        # 初始化按钮 - 3行4列，共12个按钮
        self.style_buttons = []
        for i in range(3):  # 3行
            for j in range(4):  # 4列
                btn = StyleButton("")
                btn.clicked.connect(self.on_style_clicked)
                self.grid_layout.addWidget(btn, i, j, Qt.AlignCenter)
                self.style_buttons.append(btn)

        # 加载所有风格
        self.load_all_styles()

    def load_all_styles(self):
        """加载所有风格"""
        # 获取所有风格
        all_styles = self.all_styles.copy()
        
        # 如果风格数量不足12个，用随机风格补充
        while len(all_styles) < self.batch_size:
            all_styles.append(random.choice(self.all_styles))
        
        # 更新按钮
        for i, btn in enumerate(self.style_buttons):
            if i < len(all_styles):
                style_data = all_styles[i]
                btn.setText(style_data["name"])
                btn.setProperty("style_prompt", style_data["prompt"])
                
                # 设置背景图片
                if "image" in style_data:
                    import os
                    image_path = os.path.join("image", "styles", style_data["image"])
                    absolute_path = os.path.abspath(image_path)
                    btn.set_background_image(absolute_path)
                else:
                    # 如果没有图片，使用默认样式
                    btn.setStyleSheet(AppStyles.STYLE_BUTTON)
                    btn._has_background_image = False
                
                btn.setVisible(True)
            else:
                btn.setVisible(False)
        
        # 添加延迟刷新，确保背景图片正确显示
        QTimer.singleShot(100, self.force_refresh_styles)


    def animate_button_fade_in(self, button, delay):
        """按钮淡入动画"""
        # 不再重置样式，保持已设置的背景图片
        # 简单的延时显示，减少动画开销
        QTimer.singleShot(delay, lambda: button.show())
    
    def force_refresh_styles(self):
        """强制刷新所有按钮的显示"""
        for btn in self.style_buttons:
            btn.update()  # 强制更新显示

    @Slot()
    def on_style_clicked(self):
        """风格按钮点击"""
        sender = self.sender()
        if sender:
            style_name = sender.text()
            style_prompt = sender.property("style_prompt")

            # 先清除所有按钮的选中状态
            for btn in self.style_buttons:
                btn.set_selected(False)
            
            # 设置当前按钮为选中状态
            sender.set_selected(True)
            self.selected_style = sender

            # 延迟发送信号，让用户看到选中效果
            QTimer.singleShot(500, lambda: self.style_selected.emit(style_prompt, style_name))

    def reset(self):
        """重置页面"""
        self.load_all_styles()
        # 不再重置所有按钮样式，保持背景图片
        # for btn in self.style_buttons:
        #     btn.setStyleSheet(AppStyles.STYLE_BUTTON)