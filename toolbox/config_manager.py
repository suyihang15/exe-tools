"""配置管理 — JSON 配置文件读写、程序条目 CRUD、分类管理"""

import json
import os
import sys
import shutil
import uuid
from typing import Optional
from PyQt6.QtCore import QFileInfo
from PyQt6.QtWidgets import QFileIconProvider


def get_base_dir() -> str:
    """获取工具箱根目录（兼容源码运行和 PyInstaller 打包）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # 源码运行：toolbox/config_manager.py -> toolbox/ -> 根目录
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE_DIR = get_base_dir()
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
ICONS_DIR = os.path.join(BASE_DIR, "app_icons")
APPS_DIR = os.path.join(BASE_DIR, "apps")


def resolve_icon_path(icon_path: str) -> str:
    """解析图标路径：相对→绝对，支持大小写不敏感查找"""
    if not icon_path:
        return ""
    if os.path.isabs(icon_path):
        return icon_path if os.path.exists(icon_path) else ""
    full = os.path.join(BASE_DIR, icon_path)
    if os.path.exists(full):
        return full
    parent = os.path.dirname(full)
    name = os.path.basename(full)
    if os.path.isdir(parent):
        for f in os.listdir(parent):
            if f.lower() == name.lower():
                return os.path.join(parent, f)
    return full

# 卡片大小预设
CARD_SIZE_PRESETS = {
    "small":  {"w": 160, "h": 120, "icon_size": 36},
    "medium": {"w": 200, "h": 150, "icon_size": 48},
    "large":  {"w": 240, "h": 180, "icon_size": 64},
}

# 默认配置模板
DEFAULT_CONFIG = {
    "version": "1.0",
    "theme": {
        "mode": "dark",
        "accent_color": "#6c5ce7",
        "font_family": "Microsoft YaHei",
        "font_size": 10,
        "card_border_radius": 12,
        "card_size": "medium",
    },
    "categories": ["全部", "开发工具", "设计", "游戏", "办公", "其他"],
    "apps": [],
    "window": {"width": 1200, "height": 800},
}


class ConfigManager:
    """工具箱配置管理器"""

    def __init__(self):
        self._config: dict = {}
        self.load_config()

    # ==================== 配置读写 ====================

    def load_config(self):
        """加载配置文件，不存在则创建默认配置"""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                # 确保必要字段存在
                for key, value in DEFAULT_CONFIG.items():
                    if key not in self._config:
                        self._config[key] = value
                # 确保 "全部" 分类存在
                if "全部" not in self._config.get("categories", []):
                    self._config.setdefault("categories", []).insert(0, "全部")
            except (json.JSONDecodeError, IOError):
                self._config = DEFAULT_CONFIG.copy()
                self.save_config()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self.save_config()

        # 确保图标目录和应用目录存在
        os.makedirs(ICONS_DIR, exist_ok=True)
        os.makedirs(APPS_DIR, exist_ok=True)

    def save_config(self):
        """保存配置到文件"""
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def get_all(self) -> dict:
        return self._config

    # ==================== 主题 ====================

    def get_theme(self) -> dict:
        return self._config.get("theme", DEFAULT_CONFIG["theme"])

    def update_theme(self, theme_data: dict):
        self._config["theme"].update(theme_data)
        self.save_config()

    # ==================== 分类 ====================

    def get_categories(self) -> list[str]:
        return self._config.get("categories", ["全部"])

    def get_visible_categories(self) -> list[str]:
        """返回除'全部'外的分类"""
        return [c for c in self.get_categories() if c != "全部"]

    def add_category(self, name: str) -> bool:
        """添加分类，返回是否成功"""
        categories = self._config.setdefault("categories", ["全部"])
        if name in categories:
            return False
        if "全部" not in categories:
            categories.insert(0, "全部")
        categories.append(name)
        self.save_config()
        return True

    def rename_category(self, old_name: str, new_name: str) -> bool:
        """重命名分类，同时更新所有相关程序"""
        if old_name == "全部":
            return False
        categories = self._config.get("categories", [])
        if old_name not in categories or new_name in categories:
            return False
        idx = categories.index(old_name)
        categories[idx] = new_name
        # 更新所有使用该分类的程序
        for app in self._config.get("apps", []):
            if app.get("category") == old_name:
                app["category"] = new_name
        self.save_config()
        return True

    def delete_category(self, name: str) -> bool:
        """删除分类，该分类下的程序移到'其他'"""
        if name in ("全部",):
            return False
        categories = self._config.get("categories", [])
        if name not in categories:
            return False
        categories.remove(name)
        # 确保有"其他"分类
        if "其他" not in categories:
            categories.append("其他")
        # 将该分类下的程序移到"其他"
        for app in self._config.get("apps", []):
            if app.get("category") == name:
                app["category"] = "其他"
        self.save_config()
        return True

    # ==================== 程序条目 CRUD ====================

    def get_apps(self, include_hidden: bool = False) -> list[dict]:
        """获取所有程序条目，按 sort_order 排序"""
        apps = self._config.get("apps", [])
        if not include_hidden:
            apps = [a for a in apps if not a.get("hidden", False)]
        apps.sort(key=lambda a: a.get("sort_order", 0))
        return apps

    def get_app(self, app_id: str) -> Optional[dict]:
        """根据 ID 获取单个程序条目"""
        for app in self._config.get("apps", []):
            if app.get("id") == app_id:
                return app
        return None

    def add_app(self, app_data: dict) -> dict:
        """添加程序条目，返回创建后的完整条目"""
        apps = self._config.setdefault("apps", [])
        app_data.setdefault("id", str(uuid.uuid4())[:8])
        app_data.setdefault("name", "未命名程序")
        app_data.setdefault("exe_path", "")
        app_data.setdefault("icon_path", "")
        app_data.setdefault("description", "")
        app_data.setdefault("category", "其他")
        app_data.setdefault("card_size", "medium")
        app_data.setdefault("hidden", False)
        app_data.setdefault("sort_order", len(apps))
        apps.append(app_data)
        self.save_config()
        return app_data

    def update_app(self, app_id: str, data: dict):
        """更新程序条目"""
        app = self.get_app(app_id)
        if app:
            app.update(data)
            self.save_config()

    def delete_app(self, app_id: str):
        """删除程序条目（同时清理图标文件和apps下的exe文件）"""
        app = self.get_app(app_id)
        if app:
            # 清理图标文件
            icon_path = app.get("icon_path", "")
            resolved_icon = resolve_icon_path(icon_path)
            if resolved_icon and os.path.exists(resolved_icon):
                try:
                    os.remove(resolved_icon)
                except OSError:
                    pass
            # 清理 apps/ 下的 exe 文件
            self.delete_exe_file(app.get("exe_path", ""))
            apps = self._config.get("apps", [])
            self._config["apps"] = [a for a in apps if a.get("id") != app_id]
            self.save_config()

    def toggle_hidden(self, app_id: str) -> bool:
        """切换隐藏状态，返回新状态"""
        app = self.get_app(app_id)
        if app:
            app["hidden"] = not app.get("hidden", False)
            self.save_config()
            return app["hidden"]
        return False

    def move_app_to_category(self, app_id: str, category: str):
        """将程序移动到指定分类"""
        self.update_app(app_id, {"category": category})

    def reorder_apps(self, id_order: list[str]):
        """根据 ID 顺序重新设置 sort_order"""
        for i, app_id in enumerate(id_order):
            app = self.get_app(app_id)
            if app:
                app["sort_order"] = i
        self.save_config()

    # ==================== 图标管理 ====================

    def import_icon(self, source_path: str) -> str:
        """导入图标文件到 app_icons 目录，返回相对路径"""
        if not source_path or not os.path.exists(source_path):
            return ""
        ext = os.path.splitext(source_path)[1] or ".png"
        filename = f"icon_{uuid.uuid4().hex[:8]}{ext}"
        dest_path = os.path.join(ICONS_DIR, filename)
        shutil.copy2(source_path, dest_path)
        return os.path.relpath(dest_path, BASE_DIR)

    def extract_icon_from_exe(self, exe_path: str) -> str:
        """从 exe 文件提取图标，保存到 app_icons 目录，返回相对路径"""
        if not os.path.exists(exe_path):
            return ""
        try:
            provider = QFileIconProvider()
            icon = provider.icon(QFileInfo(exe_path))
            if icon.isNull():
                return ""
            pixmap = icon.pixmap(64, 64)
            if pixmap.isNull():
                return ""
            filename = f"icon_{uuid.uuid4().hex[:8]}.png"
            dest_path = os.path.join(ICONS_DIR, filename)
            pixmap.save(dest_path, "PNG")
            return os.path.relpath(dest_path, BASE_DIR)
        except Exception:
            return ""

    # ==================== 应用文件管理 ====================

    def import_exe(self, source_path: str, copy_folder: bool = False) -> str:
        """复制 exe 文件到 apps/ 目录，返回相对路径

        便携分发：导入的 exe 统一存入 apps/ 目录，
        config.json 中存储相对路径，分发时整体复制即可使用。

        Args:
            source_path: 源 exe 文件路径
            copy_folder: True=复制整个程序文件夹, False=仅复制 exe 文件
        """
        if not source_path or not os.path.exists(source_path):
            return ""

        if copy_folder:
            return self._import_program_folder(source_path)
        else:
            return self._import_single_exe(source_path)

    def _import_single_exe(self, source_path: str) -> str:
        """仅复制单个 exe 文件"""
        filename = os.path.basename(source_path)
        dest_path = os.path.join(APPS_DIR, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(APPS_DIR, f"{base}_{counter}{ext}")
            counter += 1
        shutil.copy2(source_path, dest_path)
        return os.path.relpath(dest_path, BASE_DIR)

    def _import_program_folder(self, source_path: str) -> str:
        """复制整个程序文件夹到 apps/ 目录

        保持原始目录结构，适用于依赖本地 DLL/数据文件的程序。
        返回复制后的 exe 相对路径。
        """
        source_dir = os.path.dirname(source_path)
        source_exe_name = os.path.basename(source_path)
        folder_name = os.path.basename(source_dir)

        # 目标文件夹: apps/<程序文件夹名>/
        dest_dir = os.path.join(APPS_DIR, folder_name)
        base_name = folder_name
        counter = 1
        while os.path.exists(dest_dir):
            dest_dir = os.path.join(APPS_DIR, f"{base_name}_{counter}")
            counter += 1

        try:
            shutil.copytree(source_dir, dest_dir, symlinks=False, dirs_exist_ok=False)
        except (OSError, shutil.Error) as e:
            # 复制失败时回退到只复制 exe
            print(f"[警告] 文件夹复制失败 ({e})，回退到仅复制 exe")
            return self._import_single_exe(source_path)

        # 返回复制后的 exe 相对路径
        dest_exe = os.path.join(dest_dir, source_exe_name)
        if os.path.exists(dest_exe):
            return os.path.relpath(dest_exe, BASE_DIR)
        else:
            # 如果 exe 不在目标目录（不应该），找一下
            for root, dirs, files in os.walk(dest_dir):
                for f in files:
                    if f.lower() == source_exe_name.lower():
                        return os.path.relpath(os.path.join(root, f), BASE_DIR)
            return self._import_single_exe(source_path)

    def batch_import_apps(self, programs: list[dict], copy_folder: bool = True,
                          progress_callback=None) -> list[dict]:
        """批量导入程序

        Args:
            programs: 程序信息列表，每项包含 name, exe_path 等
            copy_folder: 是否复制整个文件夹（推荐）
            progress_callback: 进度回调 (current: int, total: int, name: str)

        Returns:
            成功导入的程序列表
        """
        imported = []
        total = len(programs)
        for idx, prog in enumerate(programs):
            exe_path = prog.get("exe_path", "")
            if not exe_path or not os.path.exists(exe_path):
                if progress_callback:
                    progress_callback(idx + 1, total, f"跳过: {prog.get('name', '未知')} (文件不存在)")
                continue

            if progress_callback:
                progress_callback(idx + 1, total, f"正在导入: {prog.get('name', exe_path)}")

            # 复制程序文件
            copied_path = self.import_exe(exe_path, copy_folder=copy_folder)
            if not copied_path:
                continue

            # 提取图标
            icon_path = self.extract_icon_from_exe(exe_path)
            if not icon_path:
                # 尝试从复制后的路径提取
                resolved = self.resolve_exe_path(copied_path)
                if resolved and os.path.exists(resolved):
                    icon_path = self.extract_icon_from_exe(resolved)

            # 创建程序条目
            app_data = {
                "name": prog.get("name", os.path.splitext(os.path.basename(exe_path))[0]),
                "exe_path": copied_path,
                "icon_path": icon_path,
                "description": prog.get("description", ""),
                "category": prog.get("category", "其他"),
                "card_size": "medium",
            }
            self.add_app(app_data)
            imported.append(app_data)

        return imported

    def resolve_exe_path(self, exe_path: str) -> str:
        """解析 exe 路径：相对路径→绝对路径，绝对路径原样返回

        如果路径不存在且为相对路径，尝试在当前 BASE_DIR 下查找。
        """
        if not exe_path:
            return ""
        if os.path.isabs(exe_path):
            return exe_path if os.path.exists(exe_path) else ""

        # 相对路径 → 基于 BASE_DIR 解析
        full = os.path.join(BASE_DIR, exe_path)
        if os.path.exists(full):
            return full

        # 尝试查找同名文件（大小写不敏感）
        parent = os.path.dirname(full)
        name = os.path.basename(full)
        if os.path.isdir(parent):
            for f in os.listdir(parent):
                if f.lower() == name.lower():
                    return os.path.join(parent, f)

        return full  # 返回推测路径（可能不存在）

    def resolve_icon_path(self, icon_path: str) -> str:
        """解析图标路径（委托给模块级函数）"""
        return resolve_icon_path(icon_path)

    def repair_exe_path(self, app_id: str) -> bool:
        """尝试修复程序的 exe 路径（用于迁移到新电脑后自动修复）

        策略：
        1. 如果当前路径存在 → 无需修复
        2. 在 apps/ 目录中搜索同名 exe
        3. 返回是否修复成功
        """
        app = self.get_app(app_id)
        if not app:
            return False

        exe_path = app.get("exe_path", "")
        resolved = self.resolve_exe_path(exe_path)
        if resolved and os.path.exists(resolved):
            return True

        # 在 apps/ 中搜索
        exe_name = os.path.basename(exe_path)
        for root, dirs, files in os.walk(APPS_DIR):
            for f in files:
                if f.lower() == exe_name.lower():
                    new_path = os.path.relpath(os.path.join(root, f), BASE_DIR)
                    self.update_app(app_id, {"exe_path": new_path})
                    return True

        return False

    def get_missing_apps(self) -> list[dict]:
        """获取所有 exe 文件缺失的程序列表"""
        missing = []
        for app in self._config.get("apps", []):
            exe_path = self.resolve_exe_path(app.get("exe_path", ""))
            if not exe_path or not os.path.exists(exe_path):
                missing.append(app)
        return missing

    def repair_all_paths(self) -> int:
        """批量修复所有程序的 exe 路径

        Returns:
            成功修复的数量
        """
        fixed = 0
        for app in self._config.get("apps", []):
            if self.repair_exe_path(app.get("id", "")):
                fixed += 1
        return fixed

    def delete_exe_file(self, exe_path: str):
        """删除 apps/ 目录下的 exe 文件（仅清理相对路径指向的文件）"""
        if not exe_path:
            return
        if os.path.isabs(exe_path):
            # 绝对路径是外部文件，不删除
            return
        full_path = os.path.join(BASE_DIR, exe_path)
        if not os.path.exists(full_path):
            return

        # 安全检查：确保只删除 apps/ 目录下的文件
        try:
            common = os.path.commonpath([os.path.abspath(full_path), os.path.abspath(APPS_DIR)])
            if common == os.path.abspath(APPS_DIR):
                # 如果是文件夹（整程序导入），删除整个文件夹
                parent_dir = os.path.dirname(full_path)
                if parent_dir != os.path.abspath(APPS_DIR) and os.path.commonpath(
                    [parent_dir, os.path.abspath(APPS_DIR)]
                ) == os.path.abspath(APPS_DIR):
                    # exe 在子目录中，尝试删除整个子目录
                    try:
                        shutil.rmtree(parent_dir, ignore_errors=True)
                    except OSError:
                        os.remove(full_path)  # 回退到只删 exe
                else:
                    os.remove(full_path)
        except (OSError, ValueError):
            pass

    # ==================== 窗口状态 ====================

    def save_window_state(self, width: int, height: int, x: int = -1, y: int = -1):
        """保存窗口大小和位置"""
        self._config["window"] = {"width": width, "height": height}
        if x >= 0 and y >= 0:
            self._config["window"]["x"] = x
            self._config["window"]["y"] = y
        self.save_config()

    def get_window_state(self) -> dict:
        return self._config.get("window", {"width": 1200, "height": 800})

    # ==================== 卡片大小预设 ====================

    @staticmethod
    def get_card_size_preset(size_name: str) -> dict:
        """获取卡片大小预设"""
        return CARD_SIZE_PRESETS.get(size_name, CARD_SIZE_PRESETS["medium"])

    # ==================== 配置导入/导出 ====================

    def export_config(self, export_path: str):
        """导出配置到指定路径"""
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, ensure_ascii=False, indent=2)

    def import_config(self, import_path: str) -> bool:
        """从指定路径导入配置"""
        try:
            with open(import_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._config = data
            self.save_config()
            return True
        except (json.JSONDecodeError, IOError):
            return False
