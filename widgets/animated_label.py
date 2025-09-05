# -*- coding: utf-8 -*-
"""动画标签组件"""

from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtGui import QFont
from styles.app_styles import AppStyles


class AnimatedLabel(QLabel):
    """带动画效果的标签"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setStyleSheet(AppStyles.ANIMATED_LABEL)
        self.setAlignment(Qt.AlignCenter)  # 确保居中对齐

        self.full_text = ""
        self.current_index = 0

        # 打字机效果定时器
        self.type_timer = QTimer()
        self.type_timer.timeout.connect(self.type_next_char)

    def set_text(self, text):
        """设置文本并开始动画"""
        self.full_text = text
        self.current_index = 0
        self.setText("")

        # 淡入效果
        effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(effect)
        self.opacity_animation = QPropertyAnimation(effect, b"opacity")
        self.opacity_animation.setDuration(500)
        self.opacity_animation.setStartValue(0)
        self.opacity_animation.setEndValue(1)
        self.opacity_animation.start()

        # 开始打字机效果
        self.type_timer.start(50)

    def type_next_char(self):
        """显示下一个字符"""
        if self.current_index < len(self.full_text):
            self.setText(self.full_text[:self.current_index + 1])
            self.current_index += 1
        else:
            self.type_timer.stop()

    def clear(self):
        """清空文本"""
        self.type_timer.stop()
        self.setText("")
        self.full_text = ""
        self.current_index = 0