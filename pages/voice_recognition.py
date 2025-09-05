# -*- coding: utf-8 -*-
"""语音识别页面"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, Signal, Slot, QTimer, QObject, QEvent
from PySide6.QtGui import QPixmap, QFont, QPainter, QBrush
from styles.app_styles import AppStyles
from widgets.animated_label import AnimatedLabel
from widgets.borderless_button import BorderlessButton
from threads.record_thread import RecordThread
from threads.asr_thread import ASRThread
import os
import logging

logger = logging.getLogger(__name__)


class GlobalFocusFilter(QObject):
    """全局事件过滤器，彻底隐藏所有QFocusFrame焦点框"""
    def eventFilter(self, obj, event):
        # 如果是焦点框相关事件，直接忽略
        if obj.__class__.__name__ == 'QFocusFrame':
            return True
        return False


class VoiceRecognitionPage(QWidget):
    """语音识别页面"""

    back_clicked = Signal()
    next_clicked = Signal(str)

    def __init__(self):
        super().__init__()
        self.current_style = ""
        self.current_style_name = ""
        self.current_background = None  # 当前背景图片
        self.background_pixmap = None   # 背景图片对象
        self.recognized_text = ""
        self.record_thread = None
        self.asr_thread = None
        self.is_recording = False
        
        # 安装全局事件过滤器来彻底隐藏焦点框
        self.global_focus_filter = GlobalFocusFilter()
        QApplication.instance().installEventFilter(self.global_focus_filter)
        
        self.setup_ui()

    def setup_ui(self):
        """设置UI - 重新设计布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 15, 30, 15)
        main_layout.setSpacing(10)

        # ========== 1. 顶部：风格显示（固定高度） ==========
        self.style_label = QLabel("当前风格：未选择")
        self.style_label.setAlignment(Qt.AlignCenter)
        self.style_label.setStyleSheet(AppStyles.STYLE_HEADER_LABEL)
        self.style_label.setFixedHeight(60)
        main_layout.addWidget(self.style_label)

        # ========== 2. 中间：识别结果框（弹性空间） ==========
        # 识别结果容器 - 初始完全隐藏，不设置任何固定尺寸
        self.result_container = QFrame()
        # 设置完全透明的背景样式
        self.result_container.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
                margin: 0px;
                padding: 0px;
            }
        """)
        # 不设置最小高度，让它完全动态
        self.result_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        # 初始完全隐藏识别结果框
        self.result_container.setVisible(False)

        result_layout = QVBoxLayout(self.result_container)
        result_layout.setContentsMargins(20, 20, 20, 20)

        # 识别结果标签 - 居中显示
        self.animated_label = AnimatedLabel()
        self.animated_label.setWordWrap(True)
        self.animated_label.setAlignment(Qt.AlignCenter)  # 文字居中
        self.animated_label.setStyleSheet(AppStyles.RESULT_TEXT_CENTER)
        result_layout.addWidget(self.animated_label, 0, Qt.AlignCenter)

        main_layout.addWidget(self.result_container, 1)  # 占据剩余空间
        
        # 添加弹性占位空间，防止底部元素向上移动
        spacer = QWidget()
        spacer.setStyleSheet("background-color: transparent;")
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(spacer, 1)

        # ========== 3. 底部控制区（固定高度，确保按钮完全显示） ==========
        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(250)  # 进一步增加底部高度，使按钮更向下
        bottom_widget.setStyleSheet("background-color: transparent;")
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 20, 0, 10)  # 增加顶部间距
        bottom_layout.setSpacing(12)  # 增加元素间距

        # 提示文字
        self.hint_label = QLabel("请说出你想要生成的图片")
        self.hint_label.setAlignment(Qt.AlignCenter)
        self.hint_label.setStyleSheet(AppStyles.BOTTOM_HINT_LABEL)
        self.hint_label.setFixedHeight(15)  # 增加高度使文字更突出
        bottom_layout.addWidget(self.hint_label)
        
        # 减少提示文字和按钮之间的间距
        bottom_layout.addSpacing(0)  # 从15px减少到5px

        # 录音按钮行
        button_row = QWidget()
        button_row.setFixedHeight(260)  # 进一步增加高度以适应更大的按钮并向下移动
        button_row_layout = QHBoxLayout(button_row)
        button_row_layout.setContentsMargins(0, 5, 0, 0)  # 减少顶部间距，从40px减少到20px

        button_row_layout.addStretch()

        # 录音按钮 - 使用多重方法确保无焦点框
        self.mic_button = BorderlessButton()
        self.mic_button.setCursor(Qt.PointingHandCursor)
        
        # 安装事件过滤器
        self.mic_button.installEventFilter(self)

        # 设置按钮
        icon_path = "Icon/button.png"
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                # 设置更大的按钮尺寸（再放大一倍）
                self.mic_button.setFixedSize(280, 200)  # 从 140x100 再放大一倍到 280x200
                # 缩放图标
                scaled_pixmap = pixmap.scaled(
                    220, 140,  # 相应增加图标尺寸
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.mic_button.setIcon(scaled_pixmap)
                self.mic_button.setIconSize(scaled_pixmap.size())
            else:
                self.setup_text_button()
        else:
            self.setup_text_button()

        # 使用强化的样式表完全覆盖焦点框
        self.mic_button.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none !important;
                outline: none !important;
                border-radius: 12px;
                padding: 10px;
            }
            QPushButton:hover {
                background: rgba(116, 185, 255, 0.1);
                border: none !important;
                outline: none !important;
            }
            QPushButton:focus {
                border: none !important;
                outline: none !important;
                background: transparent !important;
            }
            QPushButton:pressed {
                background: rgba(116, 185, 255, 0.2);
                border: none !important;
                outline: none !important;
            }
            QPushButton[focus="true"] {
                border: none !important;
                outline: none !important;
            }
        """)
        
        # 连接信号，但阻止焦点
        self.mic_button.pressed.connect(lambda: (
            self.mic_button.clearFocus(),
            self.start_recording()
        ))
        self.mic_button.released.connect(lambda: (
            self.mic_button.clearFocus(),
            self.stop_recording()
        ))
        
        button_row_layout.addWidget(self.mic_button)
        button_row_layout.addStretch()

        bottom_layout.addWidget(button_row)

        # 增加按钮和状态提示之间的间距
        bottom_layout.addSpacing(10)

        # 录音状态提示
        self.recording_hint = QLabel("长按按钮开始录音")
        self.recording_hint.setAlignment(Qt.AlignCenter)
        self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT)
        self.recording_hint.setFixedHeight(30)  # 增加高度使状态提示更突出
        bottom_layout.addWidget(self.recording_hint)

        # 增加状态提示和导航按钮之间的间距
        bottom_layout.addSpacing(15)

        # 导航按钮行
        nav_widget = QWidget()
        nav_widget.setFixedHeight(40)
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)

        # 上一步按钮
        self.back_btn = QPushButton("上一步")
        self.back_btn.setFixedSize(100, 36)
        self.back_btn.setStyleSheet(AppStyles.NAV_BACK_BUTTON)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.back_clicked)
        nav_layout.addWidget(self.back_btn)

        nav_layout.addStretch()

        # 下一步按钮
        self.next_btn = QPushButton("下一步")
        self.next_btn.setFixedSize(100, 36)
        self.next_btn.setStyleSheet(AppStyles.NAV_NEXT_DISABLED)
        self.next_btn.setCursor(Qt.ForbiddenCursor)
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.on_next_clicked)
        nav_layout.addWidget(self.next_btn)

        bottom_layout.addWidget(nav_widget)

        main_layout.addWidget(bottom_widget)

        # 录音动画定时器
        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_recording_animation)
        self.recording_dots = 0

    def setup_text_button(self):
        """设置文字按钮（无图标时）"""
        self.mic_button.setFixedSize(280, 200)  # 与图标按钮保持一致的尺寸
        self.mic_button.setText("按住\n录音")
        font = QFont()
        font.setPointSize(24)  # 相应增加字体大小
        font.setBold(True)
        self.mic_button.setFont(font)

    def set_style(self, style, style_name=None, background_image=None):
        """设置当前风格和背景图片"""
        self.current_style = style
        if style_name:
            self.current_style_name = style_name
        else:
            from utils.config import Config
            config = Config.get_instance()
            for s in config.STYLES:
                if s.get("prompt") == style:
                    self.current_style_name = s.get("name", "未知风格")
                    break
            else:
                self.current_style_name = "自定义风格"

        self.style_label.setText(f"当前风格：{self.current_style_name}")
        
        # 设置背景图片
        if background_image:
            self.set_background_image(background_image)
        else:
            self.clear_background()
            
    def set_background_image(self, background_filename):
        """设置背景图片"""
        try:
            # 构建背景图片路径
            background_path = os.path.join("image", "backgrounds", background_filename)
            absolute_path = os.path.abspath(background_path)
            
            if os.path.exists(absolute_path):
                # 加载图片
                self.background_pixmap = QPixmap(absolute_path)
                if not self.background_pixmap.isNull():
                    # 缩放图片以适应窗口尺寸
                    self.background_pixmap = self.background_pixmap.scaled(
                        self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                    )
                    self.current_background = background_filename
                    logger.info(f"设置背景图片: {background_filename}")
                else:
                    logger.warning(f"无法加载背景图片: {background_filename}")
                    self.clear_background()
            else:
                logger.warning(f"背景图片不存在: {absolute_path}")
                self.clear_background()
        except Exception as e:
            logger.error(f"设置背景图片失败: {e}")
            self.clear_background()
        
        # 刷新界面
        self.update()
        
    def clear_background(self):
        """清除背景图片"""
        self.background_pixmap = None
        self.current_background = None
        self.update()
        
    def paintEvent(self, event):
        """自定义绘制事件 - 绘制背景图片"""
        painter = QPainter(self)
        
        # 绘制背景图片
        if self.background_pixmap and not self.background_pixmap.isNull():
            # 计算居中位置
            widget_rect = self.rect()
            pixmap_rect = self.background_pixmap.rect()
            
            # 居中显示
            x = (widget_rect.width() - pixmap_rect.width()) // 2
            y = (widget_rect.height() - pixmap_rect.height()) // 2
            
            # 绘制背景图片
            painter.drawPixmap(x, y, self.background_pixmap)
            
            # 添加半透明蒙版以提高可读性
            overlay_color = Qt.black
            painter.fillRect(widget_rect, QBrush(overlay_color, Qt.Dense6Pattern))
        
        # 调用父类的paintEvent继续正常绘制
        super().paintEvent(event)
        
    def resizeEvent(self, event):
        """窗口尺寸改变时重新调整背景图片"""
        super().resizeEvent(event)
        if self.current_background:
            # 重新设置背景图片以适应新尺寸
            self.set_background_image(self.current_background)

    @Slot()
    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return

        logger.info("开始录音")
        self.is_recording = True
        self.recognized_text = ""
        self.animated_label.clear()
        # 隐藏识别结果框
        self.result_container.setVisible(False)

        # 更新UI
        self.mic_button.setStyleSheet(AppStyles.MIC_BUTTON_RECORDING_CLEAN)
        self.recording_hint.setText("正在录音...")
        self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT_ACTIVE)
        self.recording_timer.start(500)

        # 启动录音线程
        self.record_thread = RecordThread()
        self.record_thread.finished.connect(self.on_recording_finished)
        self.record_thread.error.connect(self.on_recording_error)
        self.record_thread.start()

    @Slot()
    def stop_recording(self):
        """停止录音"""
        if not self.is_recording:
            return

        logger.info("停止录音")
        self.is_recording = False
        self.recording_timer.stop()

        # 更新UI
        self.mic_button.setStyleSheet(AppStyles.MIC_BUTTON_CLEAN)
        self.recording_hint.setText("正在识别...")
        self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT_PROCESSING)

        # 停止录音线程
        if self.record_thread:
            self.record_thread.stop()

    @Slot(str)
    def on_recording_finished(self, audio_path):
        """录音完成"""
        if not audio_path:
            self.recording_hint.setText("录音失败，请重试")
            self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT_ERROR)
            return

        logger.info(f"录音完成: {audio_path}")

        # 启动识别线程
        self.asr_thread = ASRThread(audio_path)
        self.asr_thread.result.connect(self.on_recognition_result)
        self.asr_thread.error.connect(self.on_recognition_error)
        self.asr_thread.start()

    @Slot(str)
    def on_recording_error(self, error):
        """录音错误"""
        logger.error(f"录音错误: {error}")
        self.recording_hint.setText(f"录音失败: {error}")
        self.mic_button.setStyleSheet(AppStyles.MIC_BUTTON_CLEAN)

    @Slot(str)
    def on_recognition_result(self, text):
        """识别结果"""
        logger.info(f"识别结果: {text}")
        self.recognized_text = text
        self.recording_hint.setText("识别成功！")
        self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT_SUCCESS)

        # 显示识别结果框和动画文字
        if text.strip():  # 只有当有实际内容时才显示
            self.result_container.setVisible(True)
            self.animated_label.set_text(text)
        else:
            self.result_container.setVisible(False)

        # 启用下一步按钮
        self.next_btn.setEnabled(True)
        self.next_btn.setCursor(Qt.PointingHandCursor)
        self.next_btn.setStyleSheet(AppStyles.NAV_NEXT_ENABLED)

    @Slot(str)
    def on_recognition_error(self, error):
        """识别错误"""
        logger.error(f"识别错误: {error}")
        self.recording_hint.setText(f"识别失败: {error}")
        self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT_ERROR)

    def update_recording_animation(self):
        """更新录音动画"""
        self.recording_dots = (self.recording_dots + 1) % 4
        dots = "." * self.recording_dots
        self.recording_hint.setText(f"正在录音{dots}")

    @Slot()
    def on_next_clicked(self):
        """下一步按钮点击"""
        if self.recognized_text:
            self.next_clicked.emit(self.recognized_text)

    def reset(self):
        """重置页面"""
        # 停止录音和识别线程
        self.is_recording = False
        if hasattr(self, 'record_thread') and self.record_thread and self.record_thread.isRunning():
            self.record_thread.stop()
            self.record_thread.wait(1000)  # 等待最多1秒
            self.record_thread = None
            
        if hasattr(self, 'asr_thread') and self.asr_thread and self.asr_thread.isRunning():
            self.asr_thread.terminate()
            self.asr_thread.wait(1000)  # 等待最多1秒
            self.asr_thread = None
            
        # 停止定时器
        if hasattr(self, 'recording_timer'):
            self.recording_timer.stop()
        
        # 重置 UI 状态
        self.recognized_text = ""
        self.animated_label.clear()
        # 隐藏识别结果框
        self.result_container.setVisible(False)
        self.recording_hint.setText("长按按钮开始录音")
        self.recording_hint.setStyleSheet(AppStyles.STATUS_HINT)
        self.mic_button.setStyleSheet(AppStyles.MIC_BUTTON_CLEAN)
        self.next_btn.setEnabled(False)
        self.next_btn.setCursor(Qt.ForbiddenCursor)
        self.next_btn.setStyleSheet(AppStyles.NAV_NEXT_DISABLED)
        
    def eventFilter(self, obj, event):
        """事件过滤器 - 拦截焦点事件"""
        if obj == self.mic_button:
            if event.type() == QEvent.Type.Paint:
                # 清除焦点状态后再绘制
                obj.clearFocus()
            elif event.type() in [QEvent.Type.FocusIn, 
                                 QEvent.Type.FocusOut,
                                 QEvent.Type.FocusAboutToChange]:
                return True  # 拦截焦点事件
        return super().eventFilter(obj, event)