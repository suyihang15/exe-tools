"""QSS 样式表 — 暗色/亮色双主题，现代简约风格"""

DARK_THEME = """
/* ========== 全局 ========== */
QWidget {
    background-color: #0a0a0f;
    color: #e8e8f0;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ========== 主窗口 ========== */
QMainWindow {
    background-color: #0a0a0f;
}

/* ========== 滚动区域 ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: #13131a;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #3a3a50;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #5a5a70;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: #13131a;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #3a3a50;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #5a5a70;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #1a1a24;
    color: #e8e8f0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #22223a;
    border-color: #6c5ce7;
}

QPushButton:pressed {
    background-color: #1a1a30;
}

QPushButton[accent="true"] {
    background-color: #6c5ce7;
    border-color: #6c5ce7;
    color: #ffffff;
    font-weight: 600;
}

QPushButton[accent="true"]:hover {
    background-color: #7c6ef7;
    border-color: #7c6ef7;
}

QPushButton[accent="true"]:pressed {
    background-color: #5c4ed7;
}

QPushButton[danger="true"] {
    background-color: transparent;
    border-color: #e74c3c;
    color: #e74c3c;
}

QPushButton[danger="true"]:hover {
    background-color: #e74c3c;
    color: #ffffff;
}

QPushButton[flat="true"] {
    background-color: transparent;
    border: none;
    padding: 6px 10px;
}

QPushButton[flat="true"]:hover {
    background-color: #1a1a24;
}

/* ========== 分类标签按钮 ========== */
QPushButton[category="true"] {
    background-color: transparent;
    border: 1px solid #2a2a3a;
    border-radius: 20px;
    padding: 6px 18px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton[category="true"]:hover {
    background-color: #1a1a24;
    border-color: #6c5ce7;
}

QPushButton[category="true"][active="true"] {
    background-color: #6c5ce7;
    border-color: #6c5ce7;
    color: #ffffff;
}

/* ========== 输入框 ========== */
QLineEdit {
    background-color: #13131a;
    color: #e8e8f0;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 13px;
    selection-background-color: #6c5ce7;
}

QLineEdit:focus {
    border-color: #6c5ce7;
    background-color: #1a1a24;
}

QLineEdit::placeholder {
    color: #5a5a70;
}

/* ========== 标签 ========== */
QLabel {
    background-color: transparent;
    border: none;
    color: #e8e8f0;
}

QLabel[heading="true"] {
    font-size: 18px;
    font-weight: 700;
    color: #ffffff;
}

QLabel[subtext="true"] {
    font-size: 12px;
    color: #8888a0;
}

/* ========== 菜单 ========== */
QMenu {
    background-color: #1a1a24;
    border: 1px solid #2a2a3a;
    border-radius: 10px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 6px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #22223a;
}

QMenu::item:disabled {
    color: #4a4a5a;
}

QMenu::separator {
    height: 1px;
    background: #2a2a3a;
    margin: 4px 12px;
}

/* ========== 对话框 ========== */
QDialog {
    background-color: #13131a;
    border: 1px solid #2a2a3a;
    border-radius: 14px;
}

/* ========== 下拉框 ========== */
QComboBox {
    background-color: #13131a;
    color: #e8e8f0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 8px 14px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #6c5ce7;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8888a0;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #1a1a24;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #22223a;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 14px;
    border-radius: 6px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #22223a;
}

/* ========== 提示框 ========== */
QToolTip {
    background-color: #1a1a24;
    color: #e8e8f0;
    border: 1px solid #2a2a3a;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
}

/* ========== 滑块 ========== */
QSlider::groove:horizontal {
    background: #2a2a3a;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #6c5ce7;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background: #7c6ef7;
}

QSlider::sub-page:horizontal {
    background: #6c5ce7;
    border-radius: 2px;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 10px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #3a3a50;
}

QCheckBox::indicator:checked {
    background-color: #6c5ce7;
    border-color: #6c5ce7;
}

/* ========== 分割线 ========== */
QFrame[separator="true"] {
    background-color: #2a2a3a;
    max-height: 1px;
    min-height: 1px;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #0a0a0f;
    border-top: 1px solid #1a1a24;
    color: #8888a0;
    font-size: 12px;
    padding: 4px 12px;
}
"""

LIGHT_THEME = """
/* ========== 全局 ========== */
QWidget {
    background-color: #f5f5f9;
    color: #1a1a2e;
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ========== 主窗口 ========== */
QMainWindow {
    background-color: #f5f5f9;
}

/* ========== 滚动区域 ========== */
QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* ========== 滚动条 ========== */
QScrollBar:vertical {
    background: #e8e8ee;
    width: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #c0c0d0;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #a0a0b0;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}

QScrollBar:horizontal {
    background: #e8e8ee;
    height: 8px;
    border-radius: 4px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #c0c0d0;
    border-radius: 4px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #a0a0b0;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ========== 按钮 ========== */
QPushButton {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d8d8e0;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #f0f0f8;
    border-color: #6c5ce7;
}

QPushButton:pressed {
    background-color: #e8e8f0;
}

QPushButton[accent="true"] {
    background-color: #6c5ce7;
    border-color: #6c5ce7;
    color: #ffffff;
    font-weight: 600;
}

QPushButton[accent="true"]:hover {
    background-color: #7c6ef7;
    border-color: #7c6ef7;
}

QPushButton[accent="true"]:pressed {
    background-color: #5c4ed7;
}

QPushButton[danger="true"] {
    background-color: transparent;
    border-color: #e74c3c;
    color: #e74c3c;
}

QPushButton[danger="true"]:hover {
    background-color: #e74c3c;
    color: #ffffff;
}

QPushButton[flat="true"] {
    background-color: transparent;
    border: none;
    padding: 6px 10px;
}

QPushButton[flat="true"]:hover {
    background-color: #e8e8f0;
}

/* ========== 分类标签按钮 ========== */
QPushButton[category="true"] {
    background-color: #ffffff;
    border: 1px solid #d8d8e0;
    border-radius: 20px;
    padding: 6px 18px;
    font-size: 12px;
    font-weight: 500;
}

QPushButton[category="true"]:hover {
    background-color: #f0f0f8;
    border-color: #6c5ce7;
}

QPushButton[category="true"][active="true"] {
    background-color: #6c5ce7;
    border-color: #6c5ce7;
    color: #ffffff;
}

/* ========== 输入框 ========== */
QLineEdit {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d8d8e0;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 13px;
    selection-background-color: #6c5ce7;
}

QLineEdit:focus {
    border-color: #6c5ce7;
    background-color: #fafaff;
}

QLineEdit::placeholder {
    color: #a0a0b0;
}

/* ========== 标签 ========== */
QLabel {
    background-color: transparent;
    border: none;
    color: #1a1a2e;
}

QLabel[heading="true"] {
    font-size: 18px;
    font-weight: 700;
    color: #0a0a15;
}

QLabel[subtext="true"] {
    font-size: 12px;
    color: #6e6e8a;
}

/* ========== 菜单 ========== */
QMenu {
    background-color: #ffffff;
    border: 1px solid #d8d8e0;
    border-radius: 10px;
    padding: 6px;
}

QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 6px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #f0f0f8;
}

QMenu::item:disabled {
    color: #c0c0d0;
}

QMenu::separator {
    height: 1px;
    background: #e0e0e8;
    margin: 4px 12px;
}

/* ========== 对话框 ========== */
QDialog {
    background-color: #ffffff;
    border: 1px solid #d8d8e0;
    border-radius: 14px;
}

/* ========== 下拉框 ========== */
QComboBox {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d8d8e0;
    border-radius: 8px;
    padding: 8px 14px;
    min-width: 100px;
}

QComboBox:hover {
    border-color: #6c5ce7;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8888a0;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #d8d8e0;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: #f0f0f8;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 14px;
    border-radius: 6px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #f0f0f8;
}

/* ========== 提示框 ========== */
QToolTip {
    background-color: #ffffff;
    color: #1a1a2e;
    border: 1px solid #d8d8e0;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
}

/* ========== 滑块 ========== */
QSlider::groove:horizontal {
    background: #d8d8e0;
    height: 4px;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #6c5ce7;
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px 0;
}

QSlider::handle:horizontal:hover {
    background: #7c6ef7;
}

QSlider::sub-page:horizontal {
    background: #6c5ce7;
    border-radius: 2px;
}

/* ========== 复选框 ========== */
QCheckBox {
    spacing: 10px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #c0c0d0;
}

QCheckBox::indicator:checked {
    background-color: #6c5ce7;
    border-color: #6c5ce7;
}

/* ========== 分割线 ========== */
QFrame[separator="true"] {
    background-color: #d8d8e0;
    max-height: 1px;
    min-height: 1px;
}

/* ========== 状态栏 ========== */
QStatusBar {
    background-color: #f5f5f9;
    border-top: 1px solid #e0e0e8;
    color: #6e6e8a;
    font-size: 12px;
    padding: 4px 12px;
}
"""

# 卡片样式（动态参数用模板替换）
CARD_STYLE_DARK = """
AppCard {{
    background-color: {card_bg};
    border: 1.5px solid {card_border};
    border-radius: {radius}px;
}}

AppCard:hover {{
    background-color: {card_hover};
    border-color: {accent};
}}
"""

CARD_STYLE_LIGHT = """
AppCard {{
    background-color: {card_bg};
    border: 1.5px solid {card_border};
    border-radius: {radius}px;
}}

AppCard:hover {{
    background-color: {card_hover};
    border-color: {accent};
}}
"""


def get_stylesheet(theme_config: dict) -> str:
    """根据主题配置生成完整 QSS 样式表"""
    mode = theme_config.get("mode", "dark")

    if mode == "light":
        base = LIGHT_THEME
    else:
        base = DARK_THEME

    # 替换动态颜色
    accent = theme_config.get("accent_color", "#6c5ce7")
    font_family = theme_config.get("font_family", "Microsoft YaHei")
    font_size = theme_config.get("font_size", 10)

    # 应用字体设置
    qss = base.replace(
        'font-family: "Microsoft YaHei", "Segoe UI", sans-serif;',
        f'font-family: "{font_family}", "Segoe UI", sans-serif;'
    )
    qss = qss.replace(
        'font-size: 13px;',
        f'font-size: {font_size + 3}px;'
    )

    return qss


def get_card_style(theme_config: dict) -> str:
    """获取卡片专用样式"""
    mode = theme_config.get("mode", "dark")
    radius = theme_config.get("card_border_radius", 12)
    accent = theme_config.get("accent_color", "#6c5ce7")

    if mode == "light":
        template = CARD_STYLE_LIGHT
        card_bg = "#ffffff"
        card_border = "#e0e0e8"
        card_hover = "#f0f0ff"
    else:
        template = CARD_STYLE_DARK
        card_bg = "#1a1a24"
        card_border = "#2a2a3a"
        card_hover = "#22223a"

    return template.format(
        card_bg=card_bg,
        card_border=card_border,
        card_hover=card_hover,
        accent=accent,
        radius=radius,
    )
