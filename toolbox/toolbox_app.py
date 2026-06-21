"""工具箱主窗口 — 搜索栏、分类标签、卡片网格、右键菜单"""

import os
import sys
import subprocess
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QMenu, QMessageBox,
    QApplication, QStatusBar, QSizePolicy, QFrame,
)

from toolbox.config_manager import ConfigManager, BASE_DIR
from toolbox.flow_layout import FlowLayout
from toolbox.card_widget import AppCard
from toolbox.dialogs import (
    ImportAppDialog, EditAppDialog, SettingsDialog, CategoryManageDialog,
    ScanProgramsDialog,
)
from toolbox.styles import get_stylesheet


class ToolboxApp(QMainWindow):
    """桌面工具箱主窗口"""

    def __init__(self):
        super().__init__()
        self._config = ConfigManager()
        self._cards: dict[str, AppCard] = {}  # app_id -> card
        self._current_category = "全部"
        self._search_text = ""
        self._category_buttons: list[QPushButton] = []

        self._init_ui()
        self._load_cards()
        self._apply_theme()
        self._restore_window_state()

    # ==================== UI 初始化 ====================

    def _init_ui(self):
        """初始化主界面"""
        self.setWindowTitle("工具箱")
        self.setMinimumSize(800, 500)

        # 中央控件
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 顶部栏 ===
        top_bar = QWidget()
        top_bar.setFixedHeight(72)
        top_bar.setStyleSheet("background-color: #0d0d15; border-bottom: 1px solid #1a1a24;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 12, 20, 12)
        top_layout.setSpacing(12)

        # Logo/标题
        logo = QLabel("🧰 工具箱")
        logo.setStyleSheet("font-size: 20px; font-weight: 800; color: #ffffff;")
        top_layout.addWidget(logo)

        top_layout.addSpacing(8)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText="🔍  搜索程序..."
        self.search_input.setFixedWidth(280)
        self.search_input.setFixedHeight(40)
        self.search_input.textChanged.connect(self._on_search)
        top_layout.addWidget(self.search_input)

        top_layout.addStretch()

        # 扫描按钮
        scan_btn = QPushButton("🔍 扫描程序")
        scan_btn.setProperty("accent", True)
        scan_btn.setFixedHeight(38)
        scan_btn.clicked.connect(self._scan_programs)
        top_layout.addWidget(scan_btn)

        # 导入按钮
        import_btn = QPushButton("📦 导入程序")
        import_btn.setFixedHeight(38)
        import_btn.clicked.connect(self._import_app)
        top_layout.addWidget(import_btn)

        # 设置按钮
        settings_btn = QPushButton("⚙️ 设置")
        settings_btn.setFixedHeight(38)
        settings_btn.clicked.connect(self._open_settings)
        top_layout.addWidget(settings_btn)

        # 管理分类按钮
        cat_btn = QPushButton("📂 分类")
        cat_btn.setFixedHeight(38)
        cat_btn.clicked.connect(self._manage_categories)
        top_layout.addWidget(cat_btn)

        main_layout.addWidget(top_bar)

        # === 分类标签栏 ===
        self.category_bar = QWidget()
        self.category_bar.setFixedHeight(50)
        self.category_bar.setStyleSheet("background-color: #0a0a0f;")
        self.category_layout = QHBoxLayout(self.category_bar)
        self.category_layout.setContentsMargins(20, 8, 20, 8)
        self.category_layout.setSpacing(8)
        self.category_layout.addStretch()
        main_layout.addWidget(self.category_bar)

        # === 卡片网格区域 ===
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.card_container = QWidget()
        self.card_container.setStyleSheet("background-color: transparent;")
        self.flow_layout = FlowLayout(self.card_container, margin=20, spacing_h=14, spacing_v=14)
        self.card_container.setLayout(self.flow_layout)

        self.scroll_area.setWidget(self.card_container)
        main_layout.addWidget(self.scroll_area, 1)

        # === 状态栏 ===
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(
            "background-color: #0a0a0f; border-top: 1px solid #1a1a24; "
            "color: #8888a0; font-size: 12px; padding: 4px 16px;"
        )
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 快捷键
        QShortcut(QKeySequence("Ctrl+F"), self, activated=lambda: self.search_input.setFocus())

    # ==================== 卡片加载与刷新 ====================

    def _load_cards(self):
        """加载所有程序卡片"""
        # 清空现有卡片
        self._cards.clear()
        # 清空布局
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        apps = self._config.get_apps(include_hidden=True)
        theme = self._config.get_theme()
        accent = theme.get("accent_color", "#6c5ce7")
        mode = theme.get("mode", "dark")
        default_size = theme.get("card_size", "medium")

        for app in apps:
            size_name = app.get("card_size", default_size)
            preset = self._config.get_card_size_preset(size_name)

            card = AppCard(
                app_id=app["id"],
                name=app.get("name", ""),
                icon_path=app.get("icon_path", ""),
                description=app.get("description", ""),
                card_width=preset["w"],
                card_height=preset["h"],
                icon_size=preset["icon_size"],
                hidden=app.get("hidden", False),
                accent_color=accent,
                theme_mode=mode,
                parent=self.card_container,
            )
            card.double_clicked.connect(self._launch_app)
            card.context_menu_requested.connect(self._show_context_menu)

            self._cards[app["id"]] = card
            self.flow_layout.addWidget(card)

        self._rebuild_category_buttons()
        self._update_status()

        # 首次使用：如果没有程序，提示扫描
        if len(apps) == 0:
            QTimer.singleShot(500, self._prompt_first_scan)

    def _refresh_cards(self):
        """刷新卡片显示（保留卡片实例）"""
        theme = self._config.get_theme()
        accent = theme.get("accent_color", "#6c5ce7")
        mode = theme.get("mode", "dark")

        for app_id, card in self._cards.items():
            app = self._config.get_app(app_id)
            if app:
                size_name = app.get("card_size", theme.get("card_size", "medium"))
                preset = self._config.get_card_size_preset(size_name)
                card.update_data(
                    name=app.get("name", ""),
                    icon_path=app.get("icon_path", ""),
                    description=app.get("description", ""),
                    card_width=preset["w"],
                    card_height=preset["h"],
                    icon_size=preset["icon_size"],
                    hidden=app.get("hidden", False),
                    accent_color=accent,
                    theme_mode=mode,
                )
                card.setVisible(self._is_card_visible(app))

        self._update_status()

    def _rebuild_card_grid(self):
        """完全重建卡片网格（用于分类/搜索变化后）"""
        self._load_cards()
        self._apply_filter()

    def _apply_filter(self):
        """应用分类和搜索过滤"""
        for app_id, card in self._cards.items():
            app = self._config.get_app(app_id)
            if app:
                card.setVisible(self._is_card_visible(app))
        self._update_status()

    def _is_card_visible(self, app: dict) -> bool:
        """判断卡片是否应该可见（隐藏的程序也在网格中显示，半透明）"""
        # 分类筛选
        if self._current_category != "全部":
            if app.get("category", "") != self._current_category:
                return False

        # 搜索筛选
        if self._search_text:
            search_lower = self._search_text.lower()
            name = app.get("name", "").lower()
            desc = app.get("description", "").lower()
            if search_lower not in name and search_lower not in desc:
                return False

        return True

    # ==================== 分类标签 ====================

    def _rebuild_category_buttons(self):
        """重建分类标签按钮"""
        # 清除旧按钮
        for btn in self._category_buttons:
            self.category_layout.removeWidget(btn)
            btn.deleteLater()
        self._category_buttons.clear()

        categories = self._config.get_categories()
        for cat in categories:
            btn = QPushButton(cat)
            btn.setProperty("category", True)
            if cat == self._current_category:
                btn.setProperty("active", True)
            btn.clicked.connect(lambda checked, c=cat: self._on_category_changed(c))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.category_layout.insertWidget(self.category_layout.count() - 1, btn)
            self._category_buttons.append(btn)

        # 刷新样式
        self._apply_theme()

    def _on_category_changed(self, category: str):
        """分类切换"""
        self._current_category = category
        # 更新按钮状态
        for btn in self._category_buttons:
            btn.setProperty("active", btn.text() == category)
            self._restyle_widget(btn)
        self._apply_filter()

    # ==================== 搜索 ====================

    def _on_search(self, text: str):
        """搜索文本变化"""
        self._search_text = text.strip()
        self._apply_filter()

    # ==================== 程序启动 ====================

    def _launch_app(self, app_id: str):
        """启动程序"""
        app = self._config.get_app(app_id)
        if not app:
            return

        if app.get("hidden", False):
            QMessageBox.information(
                self, "程序已隐藏",
                f"「{app.get('name', '')}」当前已隐藏。\n请右键点击卡片选择「显示」后启动。"
            )
            return

        exe_path = self._config.resolve_exe_path(app.get("exe_path", ""))
        if not exe_path or not os.path.exists(exe_path):
            QMessageBox.warning(
                self, "启动失败",
                f"程序文件不存在：\n{exe_path}\n\n请检查路径是否正确。"
            )
            return

        try:
            exe_dir = os.path.dirname(exe_path)
            subprocess.Popen(
                exe_path,
                cwd=exe_dir,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.status_bar.showMessage(f"已启动：{app.get('name', '')}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "启动失败", f"无法启动程序：\n{str(e)}")

    # ==================== 右键菜单 ====================

    def _show_context_menu(self, app_id: str, pos: QPoint):
        """显示右键菜单"""
        app = self._config.get_app(app_id)
        if not app:
            return

        menu = QMenu(self)
        menu.setStyleSheet(self.styleSheet())

        # 编辑
        edit_action = menu.addAction("✏️  编辑")
        edit_action.triggered.connect(lambda: self._edit_app(app_id))

        # 隐藏/显示
        hidden = app.get("hidden", False)
        toggle_action = menu.addAction("👁  显示" if hidden else "🙈  隐藏")
        toggle_action.triggered.connect(lambda: self._toggle_hidden(app_id))

        menu.addSeparator()

        # 移动到分类
        move_menu = menu.addMenu("📂 移动到...")
        for cat in self._config.get_visible_categories():
            if cat != app.get("category", ""):
                cat_action = move_menu.addAction(cat)
                cat_action.triggered.connect(lambda checked, c=cat: self._move_to_category(app_id, c))

        menu.addSeparator()

        # 删除
        delete_action = menu.addAction("🗑  删除")
        delete_action.setEnabled(True)
        delete_action.triggered.connect(lambda: self._delete_app(app_id))

        menu.exec(pos)

    def _edit_app(self, app_id: str):
        """编辑程序"""
        app = self._config.get_app(app_id)
        if not app:
            return
        dlg = EditAppDialog(app, self._config, self)
        if dlg.exec() == EditAppDialog.DialogCode.Accepted:
            result = dlg.get_result()
            if result:
                self._config.update_app(app_id, result)
                theme = self._config.get_theme()
                if "card_size" in result or "name" in result or "icon_path" in result:
                    self._refresh_cards()
                self._apply_theme()
                self.status_bar.showMessage("程序已更新", 3000)

    def _toggle_hidden(self, app_id: str):
        """切换隐藏状态"""
        new_state = self._config.toggle_hidden(app_id)
        self._rebuild_card_grid()
        state_text = "已隐藏" if new_state else "已显示"
        self.status_bar.showMessage(f"程序{state_text}", 3000)

    def _move_to_category(self, app_id: str, category: str):
        """移动到指定分类"""
        self._config.move_app_to_category(app_id, category)
        self._rebuild_card_grid()
        self.status_bar.showMessage(f"已移动到「{category}」", 3000)

    def _delete_app(self, app_id: str):
        """删除程序"""
        app = self._config.get_app(app_id)
        if not app:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除「{app.get('name', '')}」吗？\n此操作不可撤销。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._config.delete_app(app_id)
            self._rebuild_card_grid()
            self.status_bar.showMessage("程序已删除", 3000)

    # ==================== 对话框操作 ====================

    def _import_app(self):
        """导入程序"""
        dlg = ImportAppDialog(self._config, self)
        if dlg.exec() == ImportAppDialog.DialogCode.Accepted:
            result = dlg.get_result()
            if result:
                self._config.add_app(result)
                self._rebuild_card_grid()
                self.status_bar.showMessage(f"已导入：{result.get('name', '')}", 3000)

    def _scan_programs(self):
        """扫描系统中的已安装程序并批量导入"""
        dlg = ScanProgramsDialog(self._config, self)
        if dlg.exec() == ScanProgramsDialog.DialogCode.Accepted:
            count = dlg.get_imported_count()
            if count > 0:
                self._rebuild_card_grid()
                self.status_bar.showMessage(f"成功导入 {count} 个程序！", 5000)

    def _prompt_first_scan(self):
        """首次使用提示：询问是否自动扫描已安装程序"""
        reply = QMessageBox.question(
            self, "欢迎使用工具箱",
            "🎉 欢迎使用桌面工具箱！\n\n"
            "工具箱还没有导入任何程序。\n"
            "是否自动扫描电脑中已安装的程序？\n\n"
            "工具箱会找到您系统中的程序，\n"
            "您可以选择需要的批量导入。\n\n"
            "导入后程序文件会存放在工具箱的 apps/ 目录下，\n"
            "整个文件夹复制到其他电脑也能直接使用。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scan_programs()

    def _open_settings(self):
        """打开设置"""
        dlg = SettingsDialog(self._config, self)
        if dlg.exec() == SettingsDialog.DialogCode.Accepted:
            result = dlg.get_result()
            if result:
                self._config.update_theme(result)
                self._apply_theme()
                self._refresh_cards()
                self.status_bar.showMessage("设置已保存", 3000)

    def _manage_categories(self):
        """管理分类"""
        dlg = CategoryManageDialog(self._config, self)
        dlg.exec()
        self._rebuild_card_grid()
        self.status_bar.showMessage("分类已更新", 3000)

    # ==================== 主题应用 ====================

    def _apply_theme(self):
        """应用主题样式"""
        theme = self._config.get_theme()
        qss = get_stylesheet(theme)
        self.setStyleSheet(qss)

        # 重新设置状态栏样式（因为全局样式会覆盖）
        mode = theme.get("mode", "dark")
        if mode == "light":
            self.statusBar().setStyleSheet(
                "background-color: #f5f5f9; border-top: 1px solid #e0e0e8; "
                "color: #6e6e8a; font-size: 12px; padding: 4px 16px;"
            )
            self.search_input.setStyleSheet("""
                QLineEdit {
                    background-color: #ffffff;
                    color: #1a1a2e;
                    border: 1px solid #d8d8e0;
                    border-radius: 10px;
                    padding: 10px 16px;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #6c5ce7;
                    background-color: #fafaff;
                }
            """)
        else:
            self.statusBar().setStyleSheet(
                "background-color: #0a0a0f; border-top: 1px solid #1a1a24; "
                "color: #8888a0; font-size: 12px; padding: 4px 16px;"
            )
            self.search_input.setStyleSheet("""
                QLineEdit {
                    background-color: #13131a;
                    color: #e8e8f0;
                    border: 1px solid #2a2a3a;
                    border-radius: 10px;
                    padding: 10px 16px;
                    font-size: 13px;
                }
                QLineEdit:focus {
                    border-color: #6c5ce7;
                    background-color: #1a1a24;
                }
            """)

        # 刷新样式属性
        for btn in self._category_buttons:
            self._restyle_widget(btn)

    def _restyle_widget(self, widget):
        """强制刷新控件样式"""
        style = widget.style()
        if style:
            style.unpolish(widget)
            style.polish(widget)
            widget.update()

    # ==================== 窗口状态 ====================

    def _restore_window_state(self):
        """恢复窗口大小和位置"""
        state = self._config.get_window_state()
        w = state.get("width", 1200)
        h = state.get("height", 800)
        self.resize(w, h)

    def resizeEvent(self, event):
        """窗口大小变化时更新布局"""
        super().resizeEvent(event)
        if hasattr(self, 'flow_layout'):
            self.flow_layout.invalidate()

    def closeEvent(self, event):
        """关闭时保存状态"""
        self._config.save_window_state(
            self.width(), self.height(),
            self.x(), self.y()
        )
        super().closeEvent(event)

    # ==================== 状态栏 ====================

    def _update_status(self):
        """更新状态栏信息"""
        visible_count = sum(
            1 for card in self._cards.values() if not card.isHidden()
        )
        total = len(self._cards)
        hidden_count = sum(
            1 for app_id, card in self._cards.items()
            if self._config.get_app(app_id) and self._config.get_app(app_id).get("hidden", False)
        )
        theme = self._config.get_theme()
        mode_text = "🌙 暗色" if theme.get("mode") == "dark" else "☀️ 亮色"
        status = f"共 {total} 个程序 | 显示 {visible_count} 个"
        if hidden_count > 0:
            status += f" | 隐藏 {hidden_count} 个"
        status += f" | {mode_text}"
        self.status_bar.showMessage(status)
