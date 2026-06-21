"""程序卡片组件 — 显示图标、名称、简介，支持悬浮/点击效果和右键菜单"""

import os

from PyQt6.QtCore import (
    Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint,
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFont, QPen, QBrush,
    QMouseEvent, QEnterEvent,
)
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QSizePolicy,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
    QMenu, QApplication,
)

from toolbox.config_manager import resolve_icon_path


class AppCard(QFrame):
    """程序卡片"""

    double_clicked = pyqtSignal(str)       # app_id
    context_menu_requested = pyqtSignal(str, QPoint)  # app_id, global_pos

    def __init__(
        self,
        app_id: str,
        name: str,
        icon_path: str = "",
        description: str = "",
        card_width: int = 200,
        card_height: int = 150,
        icon_size: int = 48,
        hidden: bool = False,
        accent_color: str = "#6c5ce7",
        theme_mode: str = "dark",
        parent=None,
    ):
        super().__init__(parent)
        self._app_id = app_id
        self._name = name
        self._icon_path = icon_path
        self._description = description
        self._card_width = card_width
        self._card_height = card_height
        self._icon_size = icon_size
        self._hidden = hidden
        self._accent_color = accent_color
        self._theme_mode = theme_mode
        self._hovered = False

        self.setObjectName("AppCard")
        self._init_ui()
        self._apply_style()

    def _init_ui(self):
        """初始化 UI"""
        self.setFixedSize(self._card_width, self._card_height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # 鼠标追踪（用于悬浮效果）
        self.setMouseTracking(True)

        # 透明度效果（隐藏程序）
        self._opacity_effect = None
        self._shadow_effect = None

        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(8)

        # 图标
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setFixedSize(self._icon_size + 16, self._icon_size + 16)
        self._update_icon()

        # 名称
        self.name_label = QLabel(self._name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        font = self.name_label.font()
        font.setPointSize(10)
        font.setBold(True)
        self.name_label.setFont(font)
        self.name_label.setMaximumHeight(36)
        if self._theme_mode == "dark":
            self.name_label.setStyleSheet("color: #e8e8f0;")
        else:
            self.name_label.setStyleSheet("color: #1a1a2e;")

        # 简介
        desc_text = self._description or "暂无简介"
        self.desc_label = QLabel(desc_text)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.desc_label.setWordWrap(True)
        if self._theme_mode == "dark":
            self.desc_label.setStyleSheet("color: #8888a0; font-size: 11px;")
        else:
            self.desc_label.setStyleSheet("color: #6e6e8a; font-size: 11px;")
        self.desc_label.setMaximumHeight(28)

        # 添加到布局
        layout.addStretch()
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.desc_label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        # 透明度效果/阴影效果
        self._opacity_effect = None
        self._shadow_effect = None
        self._update_graphics_effect()

    def _update_icon(self):
        """更新图标显示"""
        pixmap = self._load_icon_pixmap()
        if pixmap:
            scaled = pixmap.scaled(
                self._icon_size, self._icon_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.icon_label.setPixmap(scaled)
        else:
            # 字母头像 fallback
            self._draw_letter_avatar()

    def _load_icon_pixmap(self) -> QPixmap | None:
        """加载图标文件"""
        if self._icon_path and isinstance(self._icon_path, str):
            full_path = resolve_icon_path(self._icon_path)
            if os.path.exists(full_path):
                return QPixmap(full_path)
        return None

    def _draw_letter_avatar(self):
        """绘制字母头像（无图标时使用）"""
        letter = self._name[0] if self._name else "?"
        pixmap = QPixmap(self._icon_size, self._icon_size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 圆形背景
        bg_color = QColor(self._accent_color)
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self._icon_size, self._icon_size,
                                self._icon_size // 2, self._icon_size // 2)

        # 字母
        painter.setPen(QPen(QColor("#ffffff")))
        font = QFont("Microsoft YaHei", self._icon_size // 2)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, 0, self._icon_size, self._icon_size,
                         Qt.AlignmentFlag.AlignCenter, letter)
        painter.end()

        self.icon_label.setPixmap(pixmap)

    def _apply_style(self):
        """应用卡片样式"""
        if self._theme_mode == "dark":
            self.setStyleSheet(f"""
                AppCard {{
                    background-color: #1a1a24;
                    border: 1.5px solid #2a2a3a;
                    border-radius: 12px;
                }}
                AppCard:hover {{
                    background-color: #22223a;
                    border-color: {self._accent_color};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                AppCard {{
                    background-color: #ffffff;
                    border: 1.5px solid #e0e0e8;
                    border-radius: 12px;
                }}
                AppCard:hover {{
                    background-color: #f0f0ff;
                    border-color: {self._accent_color};
                }}
            """)

    # ==================== 事件处理 ====================

    def enterEvent(self, event: QEnterEvent):
        """鼠标进入"""
        self._hovered = True
        self._animate_scale(1.03)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self._animate_scale(1.0)
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self._app_id)
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if event.button() == Qt.MouseButton.RightButton:
            self.context_menu_requested.emit(self._app_id, event.globalPosition().toPoint())
        super().mousePressEvent(event)

    def _animate_scale(self, target: float):
        """缩放动画"""
        anim = QPropertyAnimation(self, b"geometry")
        anim.setDuration(150)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        # 简单缩放：通过固定尺寸变化模拟
        if target > 1.0:
            self.setFixedSize(
                int(self._card_width * target),
                int(self._card_height * target),
            )
        else:
            self.setFixedSize(self._card_width, self._card_height)

    # ==================== 公开方法 ====================

    def update_data(self, name: str, icon_path: str, description: str,
                    card_width: int, card_height: int, icon_size: int,
                    hidden: bool, accent_color: str, theme_mode: str):
        """更新卡片数据"""
        self._name = name
        self._icon_path = icon_path
        self._description = description
        self._card_width = card_width
        self._card_height = card_height
        self._icon_size = icon_size
        self._hidden = hidden
        self._accent_color = accent_color
        self._theme_mode = theme_mode

        self.setFixedSize(card_width, card_height)
        self.name_label.setText(name)
        self.desc_label.setText(description or "暂无简介")
        self._update_icon()
        self._apply_style()

        self._update_graphics_effect()

    def _update_graphics_effect(self):
        """根据隐藏状态设置图形效果（阴影或半透明）"""
        if self._hidden:
            if not self._opacity_effect:
                self._opacity_effect = QGraphicsOpacityEffect()
                self._opacity_effect.setOpacity(0.35)
            self.setGraphicsEffect(self._opacity_effect)
        else:
            if not self._shadow_effect:
                self._shadow_effect = QGraphicsDropShadowEffect()
                self._shadow_effect.setBlurRadius(20)
                self._shadow_effect.setOffset(0, 4)
                self._shadow_effect.setColor(QColor(0, 0, 0, 60))
            self.setGraphicsEffect(self._shadow_effect)
            # 清理透明度效果引用
            if self._opacity_effect:
                self._opacity_effect = None

    @property
    def app_id(self) -> str:
        return self._app_id
