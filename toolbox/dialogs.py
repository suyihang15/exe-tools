"""对话框 — 导入程序、批量扫描、编辑条目、主题设置、分类管理"""

import os
import sys
import threading

from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QColor, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QComboBox, QTextEdit, QCheckBox,
    QSlider, QColorDialog, QFontDialog, QMessageBox, QFrame,
    QListWidget, QListWidgetItem, QGridLayout, QWidget, QScrollArea,
    QGroupBox, QSizePolicy, QProgressBar, QApplication,
)

from toolbox.config_manager import resolve_icon_path


# ==================== 工具函数 ====================

def make_title(text: str) -> QLabel:
    """创建对话框标题标签"""
    label = QLabel(text)
    label.setProperty("heading", True)
    label.setStyleSheet("font-size: 18px; font-weight: 700; padding-bottom: 8px;")
    return label


def make_separator() -> QFrame:
    """创建分割线"""
    frame = QFrame()
    frame.setProperty("separator", True)
    frame.setFrameShape(QFrame.Shape.HLine)
    return frame


def make_field_label(text: str) -> QLabel:
    """创建字段标签"""
    label = QLabel(text)
    label.setStyleSheet("font-weight: 600; font-size: 12px; color: #8888a0; margin-top: 8px;")
    return label


def _format_size(mb: float) -> str:
    """格式化文件大小"""
    if mb < 1:
        return f"{int(mb * 1024)} KB"
    elif mb < 1024:
        return f"{mb:.1f} MB"
    else:
        return f"{mb / 1024:.1f} GB"


# ==================== 导入程序对话框 ====================

class ImportAppDialog(QDialog):
    """导入外部 exe 程序"""

    def __init__(self, config_manager, parent=None, exe_path: str = ""):
        super().__init__(parent)
        self._config = config_manager
        self._exe_path = exe_path
        self._icon_path = ""
        self._result_data: dict | None = None

        self.setWindowTitle("导入程序")
        self.setFixedSize(540, 580)
        self.setModal(True)
        self._init_ui()

        # 如果传入了 exe_path，自动填充
        if self._exe_path and os.path.exists(self._exe_path):
            self._on_exe_selected()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # 标题
        layout.addWidget(make_title("📦 导入外部程序"))

        # Exe 路径选择
        layout.addWidget(make_field_label("程序路径 (.exe)"))
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("选择要导入的 exe 文件...")
        self.path_input.setReadOnly(True)
        browse_btn = QPushButton("浏览...")
        browse_btn.setProperty("accent", True)
        browse_btn.clicked.connect(self._browse_exe)
        path_layout.addWidget(self.path_input, 1)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # 复制模式选择
        layout.addWidget(make_field_label("导入模式"))
        mode_layout = QVBoxLayout()
        self.copy_folder_check = QCheckBox("📁 复制整个程序文件夹 (推荐)")
        self.copy_folder_check.setToolTip(
            "将程序所在的整个文件夹复制到工具箱 apps/ 目录。\n"
            "这样可以保留程序依赖的 DLL、配置文件等，\n"
            "分发到其他电脑时也能正常运行。"
        )
        self.copy_folder_check.setChecked(True)
        self.copy_folder_check.setStyleSheet("""
            QCheckBox {
                color: #e8e8f0;
                font-weight: 500;
                spacing: 8px;
                padding: 4px 0;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3a3a50;
            }
            QCheckBox::indicator:checked {
                background-color: #6c5ce7;
                border-color: #6c5ce7;
            }
        """)
        mode_layout.addWidget(self.copy_folder_check)
        hint = QLabel("    仅复制 exe：适合单文件绿色程序 | 复制整文件夹：保留全部依赖")
        hint.setStyleSheet("color: #5a5a70; font-size: 11px;")
        mode_layout.addWidget(hint)
        layout.addLayout(mode_layout)

        # 文件夹大小提示
        self.folder_info_label = QLabel("")
        self.folder_info_label.setStyleSheet("color: #f59e0b; font-size: 11px; padding: 2px 8px;")
        self.folder_info_label.setVisible(False)
        layout.addWidget(self.folder_info_label)

        # 图标预览
        layout.addWidget(make_field_label("图标"))
        icon_layout = QHBoxLayout()
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(64, 64)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_preview.setStyleSheet(
            "border: 2px dashed #3a3a50; border-radius: 12px; background: transparent;"
        )
        icon_layout.addWidget(self.icon_preview)
        icon_btn_layout = QVBoxLayout()
        self.auto_extract_btn = QPushButton("自动提取图标")
        self.auto_extract_btn.clicked.connect(self._auto_extract_icon)
        self.custom_icon_btn = QPushButton("选择自定义图标...")
        self.custom_icon_btn.clicked.connect(self._choose_icon)
        icon_btn_layout.addWidget(self.auto_extract_btn)
        icon_btn_layout.addWidget(self.custom_icon_btn)
        icon_btn_layout.addStretch()
        icon_layout.addLayout(icon_btn_layout)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)

        # 名称
        layout.addWidget(make_field_label("显示名称"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("程序显示名称（自动从文件名提取）")
        layout.addWidget(self.name_input)

        # 简介
        layout.addWidget(make_field_label("简介"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText="简短描述..."
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background-color: #13131a;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
                padding: 8px;
                color: #e8e8f0;
            }
            QTextEdit:focus {
                border-color: #6c5ce7;
            }
        """)
        layout.addWidget(self.desc_input)

        # 分类
        layout.addWidget(make_field_label("分类"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self._config.get_visible_categories())
        if self.category_combo.count() == 0:
            self.category_combo.addItem("其他")
        layout.addWidget(self.category_combo)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        self.ok_btn = QPushButton("导入")
        self.ok_btn.setProperty("accent", True)
        self.ok_btn.clicked.connect(self._on_import)
        self.ok_btn.setEnabled(self._exe_path != "")
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择可执行文件", "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if path:
            self._exe_path = path
            self._on_exe_selected()

    def _on_exe_selected(self):
        """exe 路径选择后的处理"""
        self.path_input.setText(self._exe_path)
        base = os.path.splitext(os.path.basename(self._exe_path))[0]
        if not self.name_input.text():
            self.name_input.setText(base)
        self.ok_btn.setEnabled(True)

        # 自动提取图标
        self._auto_extract_icon()

        # 检查文件夹大小
        install_dir = os.path.dirname(self._exe_path)
        self._check_folder_size(install_dir)

        # 尝试获取程序描述
        try:
            from toolbox.program_scanner import get_program_description
            desc = get_program_description(self._exe_path)
            if desc and not self.desc_input.toPlainText():
                self.desc_input.setPlainText(desc)
        except ImportError:
            pass

    def _check_folder_size(self, directory: str):
        """检查文件夹大小并更新提示"""
        try:
            from toolbox.program_scanner import check_program_portable
            info = check_program_portable(self._exe_path)
            if info["total_size_mb"] > 0:
                size_text = _format_size(info["total_size_mb"])
                if info["warnings"]:
                    self.folder_info_label.setText(
                        f"⚠️ 程序目录大小: {size_text} | {'; '.join(info['warnings'])}"
                    )
                    self.folder_info_label.setVisible(True)
                    if not info["is_portable"]:
                        self.copy_folder_check.setChecked(False)
                        self.folder_info_label.setStyleSheet(
                            "color: #e74c3c; font-size: 11px; padding: 2px 8px;"
                        )
                else:
                    self.folder_info_label.setText(f"📁 程序目录大小: {size_text}")
                    self.folder_info_label.setVisible(True)
        except (ImportError, Exception):
            pass

    def _auto_extract_icon(self):
        if not self._exe_path:
            return
        icon_path = self._config.extract_icon_from_exe(self._exe_path)
        if icon_path:
            self._icon_path = icon_path
            pixmap = QPixmap(resolve_icon_path(icon_path))
            self.icon_preview.setPixmap(pixmap.scaled(
                64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.icon_preview.setStyleSheet(
                "border: 2px solid #6c5ce7; border-radius: 12px; background: transparent;"
            )

    def _choose_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件", "",
            "图片文件 (*.png *.ico *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        if path:
            imported = self._config.import_icon(path)
            if imported:
                self._icon_path = imported
                pixmap = QPixmap(resolve_icon_path(imported))
                self.icon_preview.setPixmap(pixmap.scaled(
                    64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.icon_preview.setStyleSheet(
                    "border: 2px solid #6c5ce7; border-radius: 12px; background: transparent;"
                )

    def _on_import(self):
        if not self._exe_path:
            return
        copy_folder = self.copy_folder_check.isChecked()
        copied_path = self._config.import_exe(self._exe_path, copy_folder=copy_folder)
        if not copied_path:
            QMessageBox.warning(self, "导入失败", "无法复制程序文件，请检查磁盘空间")
            return
        self._result_data = {
            "name": self.name_input.text() or os.path.splitext(os.path.basename(self._exe_path))[0],
            "exe_path": copied_path,
            "icon_path": self._icon_path,
            "description": self.desc_input.toPlainText().strip(),
            "category": self.category_combo.currentText(),
        }
        self.accept()

    def get_result(self) -> dict | None:
        return self._result_data


# ==================== 批量扫描导入对话框 ====================

class ScanWorker(QThread):
    """后台扫描线程"""
    progress = pyqtSignal(str, int)   # message, percent
    finished = pyqtSignal(list)       # results

    def __init__(self, use_registry=True, use_start_menu=True, use_common_dirs=True):
        super().__init__()
        self._use_registry = use_registry
        self._use_start_menu = use_start_menu
        self._use_common_dirs = use_common_dirs

    def run(self):
        try:
            from toolbox.program_scanner import scan_all
            results = scan_all(
                use_registry=self._use_registry,
                use_start_menu=self._use_start_menu,
                use_common_dirs=self._use_common_dirs,
                progress_callback=lambda msg, pct: self.progress.emit(msg, pct),
            )
            self.finished.emit(results)
        except Exception as e:
            self.progress.emit(f"扫描出错: {e}", -1)
            self.finished.emit([])


class ImportWorker(QThread):
    """后台导入线程"""
    progress = pyqtSignal(int, int, str)  # current, total, name
    finished = pyqtSignal(list)           # imported apps
    error = pyqtSignal(str)

    def __init__(self, config_manager, programs, copy_folder=True):
        super().__init__()
        self._config = config_manager
        self._programs = programs
        self._copy_folder = copy_folder

    def run(self):
        try:
            imported = self._config.batch_import_apps(
                self._programs,
                copy_folder=self._copy_folder,
                progress_callback=lambda cur, total, name: self.progress.emit(cur, total, name),
            )
            self.finished.emit(imported)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit([])


class ScanProgramsDialog(QDialog):
    """自动扫描系统中的已安装程序，批量选择导入"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._scan_results: list[dict] = []
        self._checkboxes: dict[str, QCheckBox] = {}
        self._imported_count = 0

        self.setWindowTitle("扫描与导入程序")
        self.setMinimumSize(680, 620)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        # 标题
        title_layout = QHBoxLayout()
        title_layout.addWidget(make_title("🔍 扫描系统中的已安装程序"))
        title_layout.addStretch()
        layout.addLayout(title_layout)

        desc = QLabel(
            "自动发现您电脑中已安装的程序，\n"
            "选择需要的程序批量导入到工具箱中。"
        )
        desc.setStyleSheet("color: #8888a0; font-size: 12px; padding-bottom: 4px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addWidget(make_separator())

        # 扫描来源选择
        layout.addWidget(make_field_label("扫描来源"))
        sources_widget = QWidget()
        sources_layout = QVBoxLayout(sources_widget)
        sources_layout.setContentsMargins(0, 0, 0, 0)
        sources_layout.setSpacing(2)

        self.reg_check = QCheckBox("📋 系统注册表 (最全面，推荐)")
        self.reg_check.setChecked(True)
        self.sm_check = QCheckBox("📂 开始菜单快捷方式")
        self.sm_check.setChecked(True)
        self.cd_check = QCheckBox("💾 常用安装目录 (Program Files 等)")
        self.cd_check.setChecked(True)

        for cb in [self.reg_check, self.sm_check, self.cd_check]:
            cb.setStyleSheet("""
                QCheckBox {
                    color: #c0c0d0;
                    spacing: 8px;
                    padding: 3px 0;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    border: 2px solid #3a3a50;
                }
                QCheckBox::indicator:checked {
                    background-color: #6c5ce7;
                    border-color: #6c5ce7;
                }
            """)
            sources_layout.addWidget(cb)

        layout.addWidget(sources_widget)

        # 扫描按钮
        scan_layout = QHBoxLayout()
        self.scan_btn = QPushButton("🔍 开始扫描")
        self.scan_btn.setProperty("accent", True)
        self.scan_btn.setFixedHeight(42)
        self.scan_btn.clicked.connect(self._start_scan)
        scan_layout.addWidget(self.scan_btn)

        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        self.scan_progress.setFixedHeight(8)
        self.scan_progress.setTextVisible(False)
        self.scan_progress.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a24;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #6c5ce7;
                border-radius: 4px;
            }
        """)
        scan_layout.addWidget(self.scan_progress, 1)

        layout.addLayout(scan_layout)

        # 扫描状态
        self.scan_status = QLabel("")
        self.scan_status.setStyleSheet("color: #5a5a70; font-size: 11px;")
        self.scan_status.setVisible(False)
        layout.addWidget(self.scan_status)

        # 结果列表
        layout.addWidget(make_field_label("发现的程序 (勾选要导入的程序)"))
        list_header = QHBoxLayout()
        self.select_all_check = QCheckBox("全选")
        self.select_all_check.setStyleSheet("color: #6c5ce7; font-weight: 500;")
        self.select_all_check.stateChanged.connect(self._on_select_all)
        list_header.addWidget(self.select_all_check)
        list_header.addStretch()
        self.result_count_label = QLabel("")
        self.result_count_label.setStyleSheet("color: #8888a0; font-size: 11px;")
        list_header.addWidget(self.result_count_label)
        layout.addLayout(list_header)

        # 可滚动的程序列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: #13131a;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
            }
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background-color: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(2)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_container)
        layout.addWidget(scroll, 1)

        # 导入模式
        layout.addWidget(make_field_label("导入模式"))
        mode_widget = QWidget()
        mode_layout = QVBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(4)

        self.import_folder_check = QCheckBox("📁 复制整个程序文件夹 (推荐，保留依赖文件)")
        self.import_folder_check.setChecked(True)
        self.import_folder_check.setStyleSheet("""
            QCheckBox {
                color: #e8e8f0;
                font-weight: 500;
                spacing: 8px;
                padding: 2px 0;
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
        """)
        mode_layout.addWidget(self.import_folder_check)
        hint2 = QLabel("    仅复制 exe：适合单文件工具 | 复制整文件夹：适合有依赖的完整程序")
        hint2.setStyleSheet("color: #5a5a70; font-size: 11px;")
        mode_layout.addWidget(hint2)

        layout.addWidget(mode_widget)

        # 导入进度
        self.import_progress = QProgressBar()
        self.import_progress.setVisible(False)
        self.import_progress.setFixedHeight(8)
        self.import_progress.setTextVisible(False)
        self.import_progress.setStyleSheet("""
            QProgressBar {
                background-color: #1a1a24;
                border-radius: 4px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.import_progress)

        self.import_status = QLabel("")
        self.import_status.setStyleSheet("color: #5a5a70; font-size: 11px;")
        self.import_status.setVisible(False)
        layout.addWidget(self.import_status)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        self.import_btn = QPushButton("📦 导入选中程序")
        self.import_btn.setProperty("accent", True)
        self.import_btn.setEnabled(False)
        self.import_btn.clicked.connect(self._start_import)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.import_btn)
        layout.addLayout(btn_layout)

    def _start_scan(self):
        """开始扫描"""
        self.scan_btn.setEnabled(False)
        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)
        self.scan_status.setVisible(True)
        self.scan_status.setText("正在初始化扫描...")
        self.import_btn.setEnabled(False)

        # 清空旧结果
        self._scan_results = []
        self._clear_list()

        self._worker = ScanWorker(
            use_registry=self.reg_check.isChecked(),
            use_start_menu=self.sm_check.isChecked(),
            use_common_dirs=self.cd_check.isChecked(),
        )
        self._worker.progress.connect(self._on_scan_progress)
        self._worker.finished.connect(self._on_scan_finished)
        self._worker.start()

    def _on_scan_progress(self, message: str, percent: int):
        self.scan_status.setText(message)
        if percent >= 0:
            self.scan_progress.setValue(percent)

    def _on_scan_finished(self, results: list):
        self._scan_results = results
        self.scan_btn.setEnabled(True)
        self.scan_progress.setVisible(False)
        self.scan_status.setVisible(False)

        self._populate_list(results)
        self._update_count()

        if results:
            self.import_btn.setEnabled(True)
        else:
            self.scan_status.setText("未发现任何程序，请尝试勾选更多扫描来源")
            self.scan_status.setVisible(True)

    def _clear_list(self):
        """清空列表"""
        self._checkboxes.clear()
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _populate_list(self, results: list):
        """填充程序列表"""
        self._clear_list()
        for prog in results:
            row = self._create_program_row(prog)
            self.list_layout.addWidget(row)
        self.list_layout.addStretch()
        self.select_all_check.setChecked(True)

    def _create_program_row(self, prog: dict) -> QWidget:
        """创建单个程序行"""
        row = QWidget()
        row.setStyleSheet("""
            QWidget#programRow {
                background-color: transparent;
                border-radius: 6px;
            }
            QWidget#programRow:hover {
                background-color: #1a1a24;
            }
        """)
        row.setObjectName("programRow")

        h_layout = QHBoxLayout(row)
        h_layout.setContentsMargins(4, 4, 8, 4)
        h_layout.setSpacing(8)

        # 复选框
        cb = QCheckBox()
        cb.setChecked(True)
        cb.setStyleSheet("""
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #3a3a50;
            }
            QCheckBox::indicator:checked {
                background-color: #6c5ce7;
                border-color: #6c5ce7;
            }
        """)
        prog_id = prog.get("exe_path", str(id(prog)))
        self._checkboxes[prog_id] = cb
        h_layout.addWidget(cb)

        # 程序信息
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 2, 0, 2)
        info_layout.setSpacing(1)

        name_label = QLabel(prog.get("name", "未知程序"))
        name_label.setStyleSheet("color: #e8e8f0; font-weight: 600; font-size: 12px;")
        info_layout.addWidget(name_label)

        exe_path = prog.get("exe_path", "")
        # 截断过长路径
        if len(exe_path) > 80:
            exe_path = "..." + exe_path[-77:]
        detail = exe_path
        if prog.get("version"):
            detail += f"  |  v{prog['version']}"
        if prog.get("publisher"):
            detail += f"  |  {prog['publisher']}"

        detail_label = QLabel(detail)
        detail_label.setStyleSheet("color: #5a5a70; font-size: 10px;")
        detail_label.setWordWrap(False)
        info_layout.addWidget(detail_label)

        h_layout.addWidget(info_widget, 1)
        return row

    def _on_select_all(self, state):
        checked = state == Qt.CheckState.Checked.value
        for cb in self._checkboxes.values():
            cb.setChecked(checked)
        self._update_count()

    def _update_count(self):
        """更新选中计数"""
        total = len(self._scan_results)
        selected = sum(1 for cb in self._checkboxes.values() if cb.isChecked())
        self.result_count_label.setText(f"已选 {selected} / 共 {total} 个")
        self.import_btn.setEnabled(selected > 0)

    def _get_selected_programs(self) -> list[dict]:
        """获取被选中的程序列表"""
        selected = []
        for prog in self._scan_results:
            prog_id = prog.get("exe_path", "")
            cb = self._checkboxes.get(prog_id)
            if cb and cb.isChecked():
                selected.append(prog)
        return selected

    def _start_import(self):
        """开始导入选中的程序"""
        selected = self._get_selected_programs()
        if not selected:
            return

        self.import_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.import_progress.setVisible(True)
        self.import_progress.setValue(0)
        self.import_status.setVisible(True)
        self.import_status.setText(f"准备导入 {len(selected)} 个程序...")

        self._import_worker = ImportWorker(
            self._config,
            selected,
            copy_folder=self.import_folder_check.isChecked(),
        )
        self._import_worker.progress.connect(self._on_import_progress)
        self._import_worker.finished.connect(self._on_import_finished)
        self._import_worker.error.connect(self._on_import_error)
        self._import_worker.start()

    def _on_import_progress(self, current: int, total: int, name: str):
        self.import_progress.setValue(int((current / total) * 100))
        self.import_status.setText(f"[{current}/{total}] {name}")

    def _on_import_finished(self, imported: list):
        self._imported_count = len(imported)
        self.import_progress.setVisible(False)
        self.import_status.setVisible(False)
        self.scan_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

        if self._imported_count > 0:
            QMessageBox.information(
                self, "导入完成",
                f"成功导入 {self._imported_count} 个程序！\n\n"
                f"程序文件已复制到工具箱的 apps/ 目录，\n"
                f"整个工具箱文件夹复制到其他电脑也能使用。"
            )
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "没有成功导入任何程序")

    def _on_import_error(self, error: str):
        QMessageBox.critical(self, "导入错误", f"导入过程出错：\n{error}")
        self.import_btn.setEnabled(True)
        self.scan_btn.setEnabled(True)

    def get_imported_count(self) -> int:
        return self._imported_count


# ==================== 编辑程序对话框 ====================

class EditAppDialog(QDialog):
    """编辑程序条目"""

    def __init__(self, app_data: dict, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._app_data = app_data
        self._result_data: dict | None = None
        self._new_icon_path = ""
        self._exe_path_changed = False

        self.setWindowTitle("编辑程序")
        self.setFixedSize(540, 600)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(make_title("✏️ 编辑程序"))

        # 显示名称
        layout.addWidget(make_field_label("显示名称"))
        self.name_input = QLineEdit(self._app_data.get("name", ""))
        layout.addWidget(self.name_input)

        # 程序路径
        layout.addWidget(make_field_label("程序路径 (.exe)"))
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit(self._app_data.get("exe_path", ""))
        path_layout.addWidget(self.path_input, 1)
        browse_btn = QPushButton("更改...")
        browse_btn.clicked.connect(self._browse_exe)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # 图标
        layout.addWidget(make_field_label("图标"))
        icon_layout = QHBoxLayout()
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(64, 64)
        self.icon_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_path = self._app_data.get("icon_path", "")
        if icon_path:
            full = resolve_icon_path(icon_path)
            if os.path.exists(full):
                pixmap = QPixmap(full)
                self.icon_preview.setPixmap(pixmap.scaled(
                    64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.icon_preview.setStyleSheet(
                    "border: 2px solid #6c5ce7; border-radius: 12px; background: transparent;"
                )
            else:
                self.icon_preview.setStyleSheet(
                    "border: 2px dashed #3a3a50; border-radius: 12px; background: transparent;"
                )
        else:
            self.icon_preview.setStyleSheet(
                "border: 2px dashed #3a3a50; border-radius: 12px; background: transparent;"
            )

        icon_layout.addWidget(self.icon_preview)
        icon_btn_layout = QVBoxLayout()
        change_icon_btn = QPushButton("选择图标...")
        change_icon_btn.clicked.connect(self._choose_icon)
        auto_btn = QPushButton("从 exe 提取")
        auto_btn.clicked.connect(self._auto_extract)
        icon_btn_layout.addWidget(change_icon_btn)
        icon_btn_layout.addWidget(auto_btn)
        icon_btn_layout.addStretch()
        icon_layout.addLayout(icon_btn_layout)
        icon_layout.addStretch()
        layout.addLayout(icon_layout)

        # 简介
        layout.addWidget(make_field_label("简介"))
        self.desc_input = QTextEdit()
        self.desc_input.setPlainText(self._app_data.get("description", ""))
        self.desc_input.setMaximumHeight(60)
        self.desc_input.setStyleSheet("""
            QTextEdit {
                background-color: #13131a;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
                padding: 8px;
                color: #e8e8f0;
            }
            QTextEdit:focus {
                border-color: #6c5ce7;
            }
        """)
        layout.addWidget(self.desc_input)

        # 分类
        layout.addWidget(make_field_label("分类"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self._config.get_visible_categories())
        current_cat = self._app_data.get("category", "其他")
        idx = self.category_combo.findText(current_cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        layout.addWidget(self.category_combo)

        # 卡片大小
        layout.addWidget(make_field_label("卡片大小"))
        size_layout = QHBoxLayout()
        self.size_combo = QComboBox()
        self.size_combo.addItems(["small", "medium", "large"])
        current_size = self._app_data.get("card_size", "medium")
        idx = self.size_combo.findText(current_size)
        if idx >= 0:
            self.size_combo.setCurrentIndex(idx)
        size_layout.addWidget(self.size_combo)
        size_layout.addStretch()
        layout.addLayout(size_layout)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        self.ok_btn = QPushButton("保存")
        self.ok_btn.setProperty("accent", True)
        self.ok_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(self.ok_btn)
        layout.addLayout(btn_layout)

    def _browse_exe(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择可执行文件", "",
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if path:
            self.path_input.setText(path)
            self._exe_path_changed = True

    def _choose_icon(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件", "",
            "图片文件 (*.png *.ico *.jpg *.jpeg *.bmp);;所有文件 (*.*)"
        )
        if path:
            imported = self._config.import_icon(path)
            if imported:
                self._new_icon_path = imported
                pixmap = QPixmap(resolve_icon_path(imported))
                self.icon_preview.setPixmap(pixmap.scaled(
                    64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                self.icon_preview.setStyleSheet(
                    "border: 2px solid #6c5ce7; border-radius: 12px; background: transparent;"
                )

    def _auto_extract(self):
        exe_path = self._config.resolve_exe_path(self.path_input.text())
        if not exe_path or not os.path.exists(exe_path):
            QMessageBox.warning(self, "提示", "请先确保程序路径有效")
            return
        icon_path = self._config.extract_icon_from_exe(exe_path)
        if icon_path:
            self._new_icon_path = icon_path
            pixmap = QPixmap(resolve_icon_path(icon_path))
            self.icon_preview.setPixmap(pixmap.scaled(
                64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
            self.icon_preview.setStyleSheet(
                "border: 2px solid #6c5ce7; border-radius: 12px; background: transparent;"
            )

    def _on_save(self):
        exe_path = self.path_input.text().strip()
        if self._exe_path_changed and exe_path and os.path.exists(exe_path):
            # 询问是否复制整个文件夹
            reply = QMessageBox.question(
                self, "导入模式",
                "是否复制整个程序文件夹到工具箱？\n\n"
                "• 是 — 复制整个文件夹，保留依赖文件（推荐）\n"
                "• 否 — 仅复制 exe 文件",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            copied = self._config.import_exe(
                exe_path,
                copy_folder=(reply == QMessageBox.StandardButton.Yes),
            )
            if copied:
                exe_path = copied
            else:
                QMessageBox.warning(self, "保存失败", "无法复制程序文件")
                return
        self._result_data = {
            "name": self.name_input.text().strip(),
            "exe_path": exe_path,
            "icon_path": self._new_icon_path or self._app_data.get("icon_path", ""),
            "description": self.desc_input.toPlainText().strip(),
            "category": self.category_combo.currentText(),
            "card_size": self.size_combo.currentText(),
        }
        self.accept()

    def get_result(self) -> dict | None:
        return self._result_data


# ==================== 设置对话框 ====================

class SettingsDialog(QDialog):
    """工具箱设置 — 主题/颜色/字体"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._theme = dict(config_manager.get_theme())
        self._result_theme: dict | None = None

        self.setWindowTitle("工具箱设置")
        self.setFixedSize(500, 520)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(make_title("⚙️ 工具箱设置"))

        # 主题模式
        layout.addWidget(make_field_label("主题模式"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["dark", "light"])
        idx = self.mode_combo.findText(self._theme.get("mode", "dark"))
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        layout.addWidget(self.mode_combo)

        # 主题色
        layout.addWidget(make_field_label("主题色"))
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(36, 36)
        self._current_accent = self._theme.get("accent_color", "#6c5ce7")
        self._update_color_preview()
        color_layout.addWidget(self.color_preview)
        color_layout.addWidget(QLabel(self._current_accent))
        choose_color_btn = QPushButton("选择颜色...")
        choose_color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(choose_color_btn)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        # 预设主题色按钮
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(6)
        for color in ["#6c5ce7", "#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#ec4899"]:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid transparent;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border-color: #ffffff;
                }}
            """)
            btn.clicked.connect(lambda checked, c=color: self._set_accent(c))
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # 字体
        layout.addWidget(make_field_label("字体"))
        font_layout = QHBoxLayout()
        self.font_label = QLabel(
            f"{self._theme.get('font_family', 'Microsoft YaHei')} "
            f"{self._theme.get('font_size', 10) + 3}pt"
        )
        font_layout.addWidget(self.font_label, 1)
        choose_font_btn = QPushButton("选择字体...")
        choose_font_btn.clicked.connect(self._choose_font)
        font_layout.addWidget(choose_font_btn)
        layout.addLayout(font_layout)

        # 卡片圆角
        layout.addWidget(make_field_label("卡片圆角"))
        radius_layout = QHBoxLayout()
        self.radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.radius_slider.setRange(0, 24)
        self.radius_slider.setValue(self._theme.get("card_border_radius", 12))
        self.radius_label = QLabel(f"{self.radius_slider.value()}px")
        self.radius_slider.valueChanged.connect(
            lambda v: self.radius_label.setText(f"{v}px")
        )
        radius_layout.addWidget(self.radius_slider, 1)
        radius_layout.addWidget(self.radius_label)
        layout.addLayout(radius_layout)

        # 默认卡片大小
        layout.addWidget(make_field_label("默认卡片大小"))
        self.card_size_combo = QComboBox()
        self.card_size_combo.addItems(["small", "medium", "large"])
        idx = self.card_size_combo.findText(self._theme.get("card_size", "medium"))
        if idx >= 0:
            self.card_size_combo.setCurrentIndex(idx)
        layout.addWidget(self.card_size_combo)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        ok_btn = QPushButton("保存")
        ok_btn.setProperty("accent", True)
        ok_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    def _update_color_preview(self):
        self.color_preview.setStyleSheet(
            f"background-color: {self._current_accent}; "
            f"border-radius: 8px; border: 2px solid #2a2a3a;"
        )

    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self._current_accent), self, "选择主题色")
        if color.isValid():
            self._current_accent = color.name()
            self._update_color_preview()
            for child in self.findChildren(QLabel):
                if child.text().startswith("#"):
                    child.setText(self._current_accent)
                    break

    def _set_accent(self, color: str):
        self._current_accent = color
        self._update_color_preview()

    def _choose_font(self):
        current_font = QFont(
            self._theme.get("font_family", "Microsoft YaHei"),
            self._theme.get("font_size", 10) + 3,
        )
        font, ok = QFontDialog.getFont(current_font, self, "选择字体")
        if ok:
            self._theme["font_family"] = font.family()
            self._theme["font_size"] = font.pointSize() - 3
            self.font_label.setText(f"{font.family()} {font.pointSize()}pt")

    def _on_save(self):
        self._result_theme = {
            "mode": self.mode_combo.currentText(),
            "accent_color": self._current_accent,
            "font_family": self._theme.get("font_family", "Microsoft YaHei"),
            "font_size": self._theme.get("font_size", 10),
            "card_border_radius": self.radius_slider.value(),
            "card_size": self.card_size_combo.currentText(),
        }
        self.accept()

    def get_result(self) -> dict | None:
        return self._result_theme


# ==================== 分类管理对话框 ====================

class CategoryManageDialog(QDialog):
    """管理分类 — 新建、重命名、删除"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self._config = config_manager
        self._result: dict | None = None

        self.setWindowTitle("管理分类")
        self.setFixedSize(440, 420)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 20)

        layout.addWidget(make_title("📂 管理分类"))

        # 分类列表
        layout.addWidget(make_field_label("现有分类"))
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #13131a;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-radius: 6px;
                margin: 2px 4px;
            }
            QListWidget::item:hover {
                background-color: #1a1a24;
            }
            QListWidget::item:selected {
                background-color: #22223a;
            }
        """)
        for cat in self._config.get_visible_categories():
            item = QListWidgetItem(cat)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget, 1)

        # 按钮行
        btn_row = QHBoxLayout()
        add_btn = QPushButton("＋ 新建分类")
        add_btn.clicked.connect(self._add_category)
        rename_btn = QPushButton("重命名")
        rename_btn.clicked.connect(self._rename_category)
        delete_btn = QPushButton("删除")
        delete_btn.setProperty("danger", True)
        delete_btn.clicked.connect(self._delete_category)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(rename_btn)
        btn_row.addWidget(delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 说明
        hint = QLabel("💡 提示：删除分类后，该分类下的程序将移至「其他」")
        hint.setStyleSheet("color: #8888a0; font-size: 11px; padding-top: 4px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()

        # 关闭按钮
        close_btn = QPushButton("完成")
        close_btn.setProperty("accent", True)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_category(self):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "新建分类", "请输入新分类名称:")
        if ok and name.strip():
            if self._config.add_category(name.strip()):
                item = QListWidgetItem(name.strip())
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.list_widget.addItem(item)
            else:
                QMessageBox.warning(self, "提示", f"分类「{name}」已存在")

    def _rename_category(self):
        current = self.list_widget.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择要重命名的分类")
            return
        old_name = current.text()
        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(
            self, "重命名分类", "请输入新名称:", text=old_name
        )
        if ok and new_name.strip() and new_name.strip() != old_name:
            if self._config.rename_category(old_name, new_name.strip()):
                current.setText(new_name.strip())
            else:
                QMessageBox.warning(self, "提示", f"重命名失败，名称可能已存在")

    def _delete_category(self):
        current = self.list_widget.currentItem()
        if not current:
            QMessageBox.warning(self, "提示", "请先选择要删除的分类")
            return
        name = current.text()
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除分类「{name}」吗？\n该分类下的程序将移至「其他」。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self._config.delete_category(name):
                row = self.list_widget.row(current)
                self.list_widget.takeItem(row)

    def get_result(self) -> dict | None:
        return {"action": "updated"}
