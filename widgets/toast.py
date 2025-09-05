# widgets/toast.py
# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect, QWidget, QApplication
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve

class Toast(QLabel):
    def __init__(self, parent: QWidget, text: str, duration: int = 2000, bg: str = "rgba(255, 140, 0, 210)"):
        super().__init__(text, parent)
        self.duration = duration
        self._bg = bg

        # 不抢焦点、不拦截鼠标
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        # 样式：透明橙色、圆角、加粗白字
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self._bg};
                color: #ffffff;
                border-radius: 16px;
                padding: 12px 18px;
                font-size: 16px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)

        # 最大宽度，防止太长
        max_w = int(parent.width() * 0.8) if parent else 600
        self.setMaximumWidth(min(max_w, 600))
        self.adjustSize()

        # 居中显示（稍微偏下）
        self._recenter()

        # 透明度动画
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)

        self._anim_in = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim_in.setDuration(200)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.OutCubic)
        self._anim_in.finished.connect(self._hold_then_fadeout)

        self._anim_out = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim_out.setDuration(300)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.InCubic)
        self._anim_out.finished.connect(self.deleteLater)

    def _recenter(self):
        if not self.parent():
            return
        p = self.parent()
        self.adjustSize()
        x = (p.width() - self.width()) // 2
        y = int((p.height() - self.height()) * 0.45)  # 稍微靠上/中间
        self.move(max(0, x), max(0, y))
        self.raise_()

    def showEvent(self, e):
        super().showEvent(e)
        self._recenter()
        self._anim_in.start()

    def _hold_then_fadeout(self):
        # 总体显示时长约 = 200ms(淡入) + hold + 300ms(淡出)
        hold = max(0, self.duration - 500)
        QTimer.singleShot(hold, self._anim_out.start)

    @staticmethod
    def show_toast(parent: QWidget, text: str, duration: int = 2000, bg: str = "rgba(255, 140, 0, 210)"):
        # 若已有 Toast，先清掉，避免堆叠
        if parent:
            for w in parent.findChildren(Toast):
                w.deleteLater()
        toast = Toast(parent, text, duration, bg)
        toast.show()
        return toast

def show_toast_anywhere(text: str, duration: int = 2000, bg: str = "rgba(255, 140, 0, 210)"):
    parent = QApplication.activeWindow()
    if parent is None:
        return
    Toast.show_toast(parent, text, duration, bg)
