# -*- coding: utf-8 -*-
"""应用样式定义 - 横屏优化版"""


class AppStyles:
    """应用样式类"""

    # ==================== 主窗口样式 ====================
    MAIN_WINDOW = """
        QWidget {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 #1E1E1E, stop:1 #2A2A2A);
            color: #F5F5F7;
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', sans-serif;
        }
    """

    # ==================== 通用样式 ====================
    # 页面标题
    TITLE_STYLE_PAGE = """
        QLabel {
            color: #F5F5F7;
            font-size: 32px;
            font-weight: bold;
            padding: 10px;
        }
    """

    # 提示标签
    HINT_LABEL = """
        QLabel {
            color: #B2BEC3;
            font-size: 16px;
            padding: 5px;
        }
    """

    # ==================== 风格选择页面样式 ====================
    # 风格容器
    STYLE_CONTAINER = """
        QWidget {
            background-color: rgba(30, 30, 30, 0.9);
            border: none;
            border-radius: 20px;
            padding: 20px;
        }
    """

    # 风格按钮
    STYLE_BUTTON = """
        QPushButton {
            color: #F5F5F7;
            border: 2px solid rgba(123, 87, 230, 0.3);
            border-radius: 15px;
            font-size: 17px;
            font-weight: 500;
            padding: 15px;
            text-align: center;
        }
        QPushButton:hover {
            border: 2px solid #7B57E6;
        }
    """

    # 带背景图片的风格按钮
    @staticmethod
    def get_style_button_with_image(image_path):
        """获取带背景图片的风格按钮样式 - 文字在底部带毛玻璃效果"""
        return f"""
            QPushButton {{
                background-image: url({image_path});
                background-repeat: no-repeat;
                background-position: center;
                color: #FFFFFF;
                border: 2px solid rgba(123, 87, 230, 0.3);
                border-radius: 15px;
                font-size: 13px;
                font-weight: bold;
                padding: 0px 8px 8px 8px;
                text-align: center;
            }}
            QPushButton:hover {{
                border: 2px solid #7B57E6;
            }}
        """

    STYLE_BUTTON_HOVER = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(155, 123, 247, 0.8), stop:1 rgba(123, 87, 230, 0.8));
            color: white;
            border: 2px solid #7B57E6;
            border-radius: 15px;
            font-size: 17px;
            font-weight: 500;
            padding: 15px;
            text-align: center;
        }
    """

    STYLE_BUTTON_SELECTED = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(155, 123, 247, 0.9), stop:1 rgba(123, 87, 230, 0.9));
            color: white;
            border: 2px solid #9B7BF7;
            border-radius: 15px;
            font-size: 17px;
            font-weight: bold;
            padding: 15px;
            text-align: center;
        }
    """

    # 刷新按钮
    REFRESH_BUTTON = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #7B57E6, stop:1 #6A4BC5);
            color: white;
            border: none;
            border-radius: 22px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #9B7BF7, stop:1 #7B57E6);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #6A4BC5, stop:1 #5A3FB5);
        }
    """

    # ==================== 语音识别页面样式 ====================
    # 顶部风格显示
    STYLE_HEADER_LABEL = """
        QLabel {
            color: #2c3e50;
            font-size: 22px;
            font-weight: bold;
            padding: 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(116, 185, 255, 0.05),
                stop:0.5 rgba(116, 185, 255, 0.1),
                stop:1 rgba(116, 185, 255, 0.05));
            border-bottom: 2px solid #74b9ff;
        }
    """

    # 风格提示标签
    STYLE_HINT_LABEL = """
        QLabel {
            color: #0984e3;
            font-size: 14px;
            padding: 5px;
            background-color: rgba(116, 185, 255, 0.1);
            border-radius: 10px;
        }
    """

    # 风格显示标签
    STYLE_DISPLAY_LABEL = """
        QLabel {
            color: #2c3e50;
            font-size: 20px;
            font-weight: bold;
            padding: 12px;
            background-color: rgba(116, 185, 255, 0.08);
            border-radius: 10px;
            border: 1px solid rgba(116, 185, 255, 0.2);
        }
    """

    # 识别结果相关
    RESULT_TITLE_LABEL = """
        QLabel {
            color: #7f8c8d;
            font-size: 14px;
            font-weight: 600;
            padding-left: 5px;
        }
    """

    # 大识别结果容器
    RESULT_CONTAINER_LARGE = """
        QFrame {
            background-color: #ffffff;
            border: 2px solid #dfe6e9;
            border-radius: 15px;
        }
    """

    # 旧版识别结果容器（保留兼容）
    RESULT_CONTAINER = """
        QWidget {
            background-color: rgba(255, 255, 255, 0.9);
            border: 1px solid #dfe6e9;
            border-radius: 15px;
            padding: 15px;
        }
    """

    # 识别结果文字
    RESULT_TEXT = """
        QLabel {
            color: #2c3e50;
            font-size: 18px;
            line-height: 1.6;
            padding: 10px;
            background-color: transparent;
        }
    """

    # 动画标签
    ANIMATED_LABEL = """
        QLabel {
            color: #2c3e50;
            font-size: 20px;
            font-weight: 500;
            padding: 10px;
            background-color: rgba(116, 185, 255, 0.1);
            border-radius: 10px;
        }
    """

    # 语音提示标签
    VOICE_HINT_LABEL = """
        QLabel {
            color: #2c3e50;
            font-size: 24px;
            font-weight: 500;
            padding: 20px;
        }
    """

    # 底部提示文字
    BOTTOM_HINT_LABEL = """
        QLabel {
            color: #34495e;
            font-size: 18px;
            font-weight: 500;
        }
    """

    # 区块标签
    SECTION_LABEL = """
        QLabel {
            color: #7f8c8d;
            font-size: 14px;
            font-weight: 500;
            padding: 5px 10px;
        }
    """

    # 录音提示
    RECORDING_HINT = """
        QLabel {
            color: #7f8c8d;
            font-size: 16px;
            padding: 10px;
        }
    """

    # 状态提示样式
    STATUS_HINT = """
        QLabel {
            color: #7f8c8d;
            font-size: 14px;
            font-weight: 500;
        }
    """

    STATUS_HINT_ACTIVE = """
        QLabel {
            color: #ff6b6b;
            font-size: 14px;
            font-weight: bold;
        }
    """

    STATUS_HINT_PROCESSING = """
        QLabel {
            color: #74b9ff;
            font-size: 14px;
            font-weight: bold;
        }
    """

    STATUS_HINT_SUCCESS = """
        QLabel {
            color: #00b894;
            font-size: 14px;
            font-weight: bold;
        }
    """

    STATUS_HINT_ERROR = """
        QLabel {
            color: #d63031;
            font-size: 14px;
            font-weight: bold;
        }
    """

    # ==================== 麦克风按钮样式 ====================

    # ==================== 导航按钮样式 ====================
    # 返回按钮
    BACK_BUTTON = """
        QPushButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background-color: #7f8c8d;
        }
    """

    NAV_BACK_BUTTON = """
        QPushButton {
            background-color: #95a5a6;
            color: white;
            border: none;
            border-radius: 18px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #7f8c8d;
        }
    """

    # 下一步按钮 - 启用状态
    NEXT_BUTTON_NORMAL = """
        QPushButton {
            background-color: #00b894;
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background-color: #00cec9;
        }
    """

    NAV_NEXT_ENABLED = """
        QPushButton {
            background-color: #00b894;
            color: white;
            border: none;
            border-radius: 18px;
            font-size: 14px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #00cec9;
        }
    """

    # 下一步按钮 - 禁用状态
    NEXT_BUTTON_DISABLED = """
        QPushButton {
            background-color: #b2bec3;
            color: #dfe6e9;
            border: none;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }
    """

    NAV_NEXT_DISABLED = """
        QPushButton {
            background-color: #dfe6e9;
            color: #b2bec3;
            border: none;
            border-radius: 18px;
            font-size: 14px;
            font-weight: bold;
        }
    """

    # ==================== 图片显示页面样式 ====================
    # 加载提示
    LOADING_HINT = """
        QLabel {
            color: #7f8c8d;
            font-size: 18px;
            padding: 10px;
        }
    """

    # 缩略图
    THUMBNAIL = """
        QLabel {
            background-color: white;
            border: 2px solid #dfe6e9;
            border-radius: 15px;
            padding: 10px;
        }
        QLabel:hover {
            border: 2px solid #74b9ff;
        }
    """

    # 重新生成按钮
    REGENERATE_BUTTON = """
        QPushButton {
            background-color: #6c5ce7;
            color: white;
            border: none;
            border-radius: 20px;
            font-size: 16px;
            font-weight: bold;
            padding: 10px 20px;
        }
        QPushButton:hover {
            background-color: #a29bfe;
        }
    """

    # 居中的识别结果容器 - 透明版本
    RESULT_CONTAINER_CENTER = """
        QFrame {
            background-color: transparent;
            border: none;
            margin: 10px;
        }
    """

    # 居中的识别结果文字 - 非常轻微透明版本
    RESULT_TEXT_CENTER = """
        QLabel {
            color: #FFFFFF;
            font-size: 28px;
            font-weight: bold;
            line-height: 1.8;
            padding: 20px;
            background-color: rgba(0, 0, 0, 0.35);
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }
    """

    # 简洁的麦克风按钮 - 完全透明无边框，彻底隐藏焦点框
    MIC_BUTTON_CLEAN = """
        QPushButton {
            background: transparent;
            border: 0px solid transparent;
            border-radius: 12px;
            padding: 10px;
            outline: 0px;
        }
        QPushButton:hover {
            background: rgba(116, 185, 255, 0.1);
            border: 0px solid transparent;
            outline: 0px;
        }
        QPushButton:focus {
            border: 0px solid transparent !important;
            outline: 0px !important;
            background: transparent !important;
        }
        QPushButton:pressed {
            background: rgba(116, 185, 255, 0.2);
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
        QPushButton:active {
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
        QPushButton:!focus {
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
        QPushButton::focus {
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
    """

    MIC_BUTTON_RECORDING_CLEAN = """
        QPushButton {
            background: rgba(255, 107, 107, 0.2);
            border: 0px solid transparent;
            border-radius: 12px;
            padding: 10px;
            outline: 0px;
        }
        QPushButton:focus {
            border: 0px solid transparent !important;
            outline: 0px !important;
            background: rgba(255, 107, 107, 0.2) !important;
        }
        QPushButton:pressed {
            border: 0px solid transparent !important;
            outline: 0px !important;
            background: rgba(255, 107, 107, 0.3) !important;
        }
        QPushButton:active {
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
        QPushButton:!focus {
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
        QPushButton::focus {
            border: 0px solid transparent !important;
            outline: 0px !important;
        }
    """
