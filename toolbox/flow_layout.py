"""流式布局 — 自动换行的卡片网格布局"""

from PyQt6.QtCore import Qt, QSize, QRect, QPoint
from PyQt6.QtWidgets import QLayout, QLayoutItem, QWidgetItem, QSizePolicy


class FlowLayout(QLayout):
    """自动换行的流式布局，适用于卡片网格"""

    def __init__(self, parent=None, margin=12, spacing_h=12, spacing_v=12):
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._margin = margin
        self._spacing_h = spacing_h
        self._spacing_v = spacing_v
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        self.clear()

    def addItem(self, item: QLayoutItem):
        self._items.append(item)

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def clear(self):
        """清空所有布局项"""
        while self._items:
            item = self.takeAt(0)
            if item:
                widget = item.widget()
                if widget:
                    widget.deleteLater()

    def removeWidget(self, widget):
        """移除指定控件"""
        for i, item in enumerate(self._items):
            if item.widget() is widget:
                self.takeAt(i)
                break

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._doLayout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._doLayout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        margin = self.contentsMargins()
        size += QSize(
            margin.left() + margin.right(),
            margin.top() + margin.bottom()
        )
        return size

    def _doLayout(self, rect: QRect, test_only: bool = False) -> int:
        """执行布局，返回总高度"""
        margin = self.contentsMargins()
        available_width = rect.width() - margin.left() - margin.right()

        x = margin.left()
        y = margin.top()
        line_height = 0

        for item in self._items:
            widget = item.widget()
            if widget and widget.isHidden():
                continue

            item_size = item.sizeHint()

            # 当前行放不下则换行
            if x + item_size.width() > available_width and line_height > 0:
                x = margin.left()
                y += line_height + self._spacing_v
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item_size))

            x += item_size.width() + self._spacing_h
            line_height = max(line_height, item_size.height())

        total_height = y + line_height + margin.bottom()
        return total_height

    def setSpacing(self, h: int, v: int):
        """设置间距"""
        self._spacing_h = h
        self._spacing_v = v
        self.invalidate()
