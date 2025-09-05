# -*- coding: utf-8 -*-
"""无边框按钮 - 完全隐藏焦点框"""

from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPainter, QPainterPath, QRegion


class BorderlessButton(QPushButton):
    """无边框按钮 - 完全隐藏焦点框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.NoFocus)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.setDefault(False)
        self.setAutoDefault(False)
        
    def focusInEvent(self, event):
        """重写焦点进入事件 - 忽略"""
        event.ignore()
        
    def focusOutEvent(self, event):
        """重写焦点离开事件 - 忽略"""
        event.ignore()
        
    def paintEvent(self, event):
        """重写绘制事件 - 避免绘制焦点矩形"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 只绘制按钮内容，不绘制焦点框
        if self.icon() and not self.icon().isNull():
            # 绘制图标
            icon_rect = self.rect()
            icon_rect.adjust(10, 10, -10, -10)  # 添加内边距
            self.icon().paint(painter, icon_rect)
        elif self.text():
            # 绘制文本
            painter.setPen(self.palette().color(self.palette().ButtonText))
            painter.drawText(self.rect(), Qt.AlignCenter, self.text())
            
    def event(self, e):
        """重写事件处理 - 过滤焦点相关事件"""
        if e.type() == QEvent.Type.FocusIn or e.type() == QEvent.Type.FocusOut:
            e.ignore()
            return True
        return super().event(e)