"""程序扫描器 — 自动发现系统中的已安装程序

支持三种扫描方式：
1. 注册表扫描 (最全面，通过 Uninstall 注册表项)
2. 开始菜单扫描 (解析 .lnk 快捷方式)
3. 常用目录扫描 (Program Files 等常见安装目录)

返回统一的 ProgramInfo 结构，自动去重。
"""

import os
import sys
import subprocess
from typing import Optional

if sys.platform == "win32":
    import winreg


# ==================== 数据结构 ====================

def make_program(
    name: str = "",
    exe_path: str = "",
    version: str = "",
    publisher: str = "",
    install_dir: str = "",
    source: str = "",
) -> dict:
    """创建统一的程序信息字典"""
    return {
        "name": name,
        "exe_path": exe_path,
        "version": version,
        "publisher": publisher,
        "install_dir": install_dir or os.path.dirname(exe_path),
        "source": source,
    }


def _norm(path: str) -> str:
    """规范化路径用于去重比较"""
    return os.path.normpath(path).lower() if path else ""


# ==================== 注册表扫描 ====================

def _read_reg_str(hkey, subkey_path: str, value_name: str) -> str:
    """安全读取注册表字符串值"""
    try:
        subkey = winreg.OpenKey(hkey, subkey_path)
        value, _ = winreg.QueryValueEx(subkey, value_name)
        subkey.Close()
        if isinstance(value, str):
            return value.strip()
    except (OSError, PermissionError, FileNotFoundError):
        pass
    return ""


def _resolve_exe_from_registry(uninstall_key) -> str:
    """从注册表卸载项中推测主程序 exe 路径

    尝试多种方式：
    1. DisplayIcon (通常指向 exe，但需过滤卸载器)
    2. InstallLocation + 搜索 exe
    3. UninstallString 中提取

    自动过滤安装器、卸载器、更新器等非主程序。
    """
    # 排除关键词（卸载器/安装器/更新器）
    bad_keywords = [
        "unins", "uninst", "unwise", "uninstall",
        "installer", "updater", "packer", "cleanup",
    ]

    def _is_bad_exe(path: str) -> bool:
        name_lower = os.path.basename(path).lower()
        for kw in bad_keywords:
            if kw in name_lower:
                return True
        return False

    try:
        # 方法1: DisplayIcon 通常指向主 exe
        icon, _ = _safe_query(uninstall_key, "DisplayIcon")
        if icon and isinstance(icon, str):
            icon = icon.strip().strip('"')
            # 去除图标索引参数 (如 ",0")
            if "," in icon and icon.rsplit(",", 1)[-1].strip().isdigit():
                icon = icon.rsplit(",", 1)[0]
            if icon.lower().endswith(".exe") and os.path.exists(icon):
                if not _is_bad_exe(icon):
                    return icon

        # 方法2: InstallLocation + 搜索 exe
        install_dir, _ = _safe_query(uninstall_key, "InstallLocation")
        if install_dir and isinstance(install_dir, str):
            install_dir = install_dir.strip().strip('"')
            if os.path.isdir(install_dir):
                display_name, _ = _safe_query(uninstall_key, "DisplayName")
                exe = _find_main_exe(install_dir, display_name or "")
                if exe:
                    return exe

        # 方法3: 从 UninstallString 推测
        uninst, _ = _safe_query(uninstall_key, "UninstallString")
        if uninst and isinstance(uninst, str):
            uninst = uninst.strip().strip('"')
            if uninst.lower().endswith(".exe") and not _is_bad_exe(uninst):
                parent = os.path.dirname(uninst)
                if os.path.isdir(parent):
                    display_name, _ = _safe_query(uninstall_key, "DisplayName")
                    exe = _find_main_exe(parent, display_name or "")
                    if exe:
                        return exe
                    if os.path.exists(uninst):
                        return uninst
    except Exception:
        pass
    return ""


def _safe_query(key, value_name: str) -> tuple:
    """安全查询注册表值"""
    try:
        return winreg.QueryValueEx(key, value_name)
    except (OSError, PermissionError):
        return (None, None)


def _find_main_exe(directory: str, hint_name: str = "", max_depth: int = 2) -> str:
    """在目录中寻找主 exe 文件

    优先策略：
    1. 目录下直接有 .exe 文件（匹配 hint 名称优先）
    2. 子目录中搜索（深度受限）
    排除卸载程序、更新程序、安装器等辅助工具。
    """
    if not os.path.isdir(directory):
        return ""

    # 排除关键词（这些不是主程序）
    exclude_keywords = [
        "unins", "uninst", "unwise", "update", "setup", "install",
        "crash", "error", "report", "tray", "helper", "service",
        "launcher_patcher", "cleanup", "repair", "uninstall",
        "installer", "updater", "packer", " activator", "crack",
        "patcher", "keygen",
    ]

    hint_lower = os.path.splitext(hint_name)[0].lower() if hint_name else ""
    hint_keywords = []
    if hint_lower:
        # 提取可能的关键词
        hint_keywords = [w for w in hint_lower.split() if len(w) > 2]

    def _is_main_candidate(filepath: str) -> bool:
        name_lower = os.path.basename(filepath).lower()
        for kw in exclude_keywords:
            if kw in name_lower:
                return False
        return True

    def _score(filepath: str) -> int:
        """计算匹配得分，越高越可能是主程序"""
        score = 0
        name_lower = os.path.basename(filepath).lower()
        # 排除卸载程序等
        if not _is_main_candidate(filepath):
            return -1000
        # 名称匹配加分
        for kw in hint_keywords:
            if kw in name_lower:
                score += 10
        # exe 文件名和目录名一致，加分
        dir_name = os.path.basename(directory).lower()
        if os.path.splitext(name_lower)[0] in dir_name or dir_name in os.path.splitext(name_lower)[0]:
            score += 5
        # 文件越大，越可能是主程序（>1MB 加分）
        try:
            size = os.path.getsize(filepath)
            if size > 1024 * 1024:
                score += 3
            if size > 10 * 1024 * 1024:
                score += 2
        except OSError:
            pass
        return score

    candidates = []

    # 深度1: 直接在目录下找
    try:
        for f in os.listdir(directory):
            if f.lower().endswith(".exe"):
                full = os.path.join(directory, f)
                if os.path.isfile(full):
                    s = _score(full)
                    if s >= 0:
                        candidates.append((s, full))
    except (OSError, PermissionError):
        pass

    # 深度2: 子目录中找
    if max_depth >= 2 and not candidates:
        try:
            for sub in os.listdir(directory):
                sub_path = os.path.join(directory, sub)
                if os.path.isdir(sub_path):
                    for f in os.listdir(sub_path):
                        if f.lower().endswith(".exe"):
                            full = os.path.join(sub_path, f)
                            if os.path.isfile(full):
                                s = _score(full)
                                if s >= 0:
                                    candidates.append((s, full))
        except (OSError, PermissionError):
            pass

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return ""


def scan_registry() -> list[dict]:
    """扫描 Windows 注册表中的已安装程序

    读取 HKLM 和 HKCU 下的 Uninstall 注册表项，
    提取程序名、版本、安装路径、主程序 exe。
    """
    results = []

    registry_roots = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for hkey_root, reg_path in registry_roots:
        try:
            key = winreg.OpenKey(hkey_root, reg_path)
            subkey_count = winreg.QueryInfoKey(key)[0]
            for i in range(subkey_count):
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)

                    # 读取 DisplayName
                    name, _ = _safe_query(subkey, "DisplayName")
                    if not name or not isinstance(name, str) or not name.strip():
                        subkey.Close()
                        continue
                    name = name.strip()

                    # 跳过系统组件（通常不含 DisplayIcon 且名字很长）
                    if len(name) > 128:
                        subkey.Close()
                        continue

                    # 尝试解析主程序路径
                    exe_path = _resolve_exe_from_registry(subkey)
                    if not exe_path or not os.path.exists(exe_path):
                        subkey.Close()
                        continue

                    # 读取其他元数据
                    version, _ = _safe_query(subkey, "DisplayVersion")
                    publisher, _ = _safe_query(subkey, "Publisher")
                    install_loc, _ = _safe_query(subkey, "InstallLocation")

                    results.append(make_program(
                        name=name,
                        exe_path=exe_path,
                        version=str(version).strip() if version else "",
                        publisher=str(publisher).strip() if publisher else "",
                        install_dir=str(install_loc).strip().strip('"') if install_loc else "",
                        source="registry",
                    ))
                    subkey.Close()
                except (OSError, PermissionError):
                    continue
            key.Close()
        except (OSError, PermissionError):
            continue

    return _deduplicate(results)


# ==================== 开始菜单扫描 ====================

def _resolve_shortcut_target(lnk_path: str) -> str:
    """解析 .lnk 快捷方式的目标路径

    通过 PowerShell COM 对象解析，兼容所有 Windows 版本。
    """
    try:
        # PowerShell 脚本解析 .lnk
        ps_script = (
            f'$WshShell = New-Object -ComObject WScript.Shell; '
            f'$Shortcut = $WshShell.CreateShortcut("{lnk_path}"); '
            f'Write-Output $Shortcut.TargetPath'
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        target = result.stdout.strip()
        if target and os.path.exists(target):
            return target
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def scan_start_menu() -> list[dict]:
    """扫描开始菜单中的程序快捷方式

    遍历 All Users 和当前用户的开始菜单目录，
    解析所有 .lnk 快捷方式获取程序路径。
    """
    results = []
    start_menu_dirs = [
        os.path.join(os.environ.get("ALLUSERSPROFILE", "C:\\ProgramData"),
                     "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ.get("APPDATA", ""),
                     "Microsoft", "Windows", "Start Menu", "Programs"),
    ]

    for base_dir in start_menu_dirs:
        if not os.path.isdir(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            # 跳过大文件夹
            if len(results) > 500:
                break
            for f in files:
                if f.lower().endswith(".lnk"):
                    lnk_path = os.path.join(root, f)
                    target = _resolve_shortcut_target(lnk_path)
                    if target and target.lower().endswith(".exe"):
                        name = os.path.splitext(f)[0]
                        # 去掉常见后缀
                        for suffix in [" - 快捷方式", " (x64)", " (x86)",
                                       " (64-bit)", " (32-bit)"]:
                            if name.endswith(suffix):
                                name = name[:-len(suffix)]
                        results.append(make_program(
                            name=name,
                            exe_path=target,
                            install_dir=os.path.dirname(target),
                            source="start_menu",
                        ))

    return _deduplicate(results)


# ==================== 常用目录扫描 ====================

# 常见程序安装目录配置
COMMON_INSTALL_DIRS = [
    os.environ.get("ProgramFiles", "C:\\Program Files"),
    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs"),
    os.path.join(os.environ.get("APPDATA", ""), "..", "Local", "Programs"),
]


def scan_common_dirs(max_per_dir: int = 50) -> list[dict]:
    """扫描常见安装目录中的程序"""
    results = []

    for base_dir in COMMON_INSTALL_DIRS:
        if not os.path.isdir(base_dir):
            continue
        try:
            entries = os.listdir(base_dir)
        except (OSError, PermissionError):
            continue

        for entry in entries:
            if len(results) >= max_per_dir:
                break

            entry_path = os.path.join(base_dir, entry)
            if not os.path.isdir(entry_path):
                continue

            # 跳过显然不是程序的目录
            skip_names = {"windows", "windowsapps", "common files", "internet explorer",
                          "windows defender", "windows security", "windows mail",
                          "windows media player", "windows nt", "windows photo viewer",
                          "windows portable devices"}
            if entry.lower() in skip_names:
                continue

            exe = _find_main_exe(entry_path, entry)
            if exe:
                results.append(make_program(
                    name=entry,
                    exe_path=exe,
                    install_dir=entry_path,
                    source="common_dirs",
                ))

    return _deduplicate(results)


# ==================== 综合扫描 ====================

def scan_all(
    use_registry: bool = True,
    use_start_menu: bool = True,
    use_common_dirs: bool = True,
    progress_callback=None,
) -> list[dict]:
    """综合扫描所有来源，返回去重后的程序列表

    Args:
        use_registry: 是否扫描注册表
        use_start_menu: 是否扫描开始菜单
        use_common_dirs: 是否扫描常用目录
        progress_callback: 进度回调 (message: str, percent: int)

    Returns:
        去重后的程序信息列表
    """
    all_results = []
    sources_to_scan = []

    if use_registry:
        sources_to_scan.append(("registry", scan_registry))
    if use_start_menu:
        sources_to_scan.append(("start_menu", scan_start_menu))
    if use_common_dirs:
        sources_to_scan.append(("common_dirs", scan_common_dirs))

    total_sources = len(sources_to_scan)
    for idx, (source_name, scan_func) in enumerate(sources_to_scan):
        if progress_callback:
            progress_callback(
                f"正在扫描 {_source_label(source_name)}...",
                int((idx / total_sources) * 80)
            )
        try:
            source_results = scan_func()
            all_results.extend(source_results)
        except Exception as e:
            # 单个来源失败不影响其他
            if progress_callback:
                progress_callback(f"扫描 {source_name} 时出错: {e}", -1)

    if progress_callback:
        progress_callback("正在去重与排序...", 90)

    all_results = _deduplicate(all_results)

    # 排序: 按名称字母序
    all_results.sort(key=lambda p: p.get("name", "").lower())

    if progress_callback:
        progress_callback(f"扫描完成，发现 {len(all_results)} 个程序", 100)

    return all_results


def _source_label(source: str) -> str:
    labels = {
        "registry": "系统注册表",
        "start_menu": "开始菜单",
        "common_dirs": "常用安装目录",
    }
    return labels.get(source, source)


# ==================== 工具函数 ====================

def _deduplicate(results: list[dict]) -> list[dict]:
    """按 exe_path 去重，保留信息最完整的条目"""
    grouped: dict[str, dict] = {}

    for prog in results:
        key = _norm(prog.get("exe_path", ""))
        if not key:
            continue
        if key not in grouped:
            grouped[key] = prog
        else:
            # 合并：保留更完整的信息
            existing = grouped[key]
            # 保留更长的名称
            if len(prog.get("name", "")) > len(existing.get("name", "")):
                existing["name"] = prog["name"]
            # 保留非空版本
            if prog.get("version") and not existing.get("version"):
                existing["version"] = prog["version"]
            # 保留非空发布者
            if prog.get("publisher") and not existing.get("publisher"):
                existing["publisher"] = prog["publisher"]
            # 合并来源信息
            sources = set(existing.get("source", "").split(","))
            sources.add(prog.get("source", ""))
            existing["source"] = ",".join(sorted(s for s in sources if s))

    return list(grouped.values())


def check_program_portable(exe_path: str) -> dict:
    """检查程序是否适合直接复制（便携化）

    分析 exe 所在目录，判断：
    - total_size_mb: 目录总大小
    - is_portable: 是否可能适合直接复制
    - file_count: 目录下文件数
    - warnings: 需要注意的问题
    """
    result = {
        "total_size_mb": 0,
        "is_portable": True,
        "file_count": 0,
        "warnings": [],
    }

    install_dir = os.path.dirname(exe_path)
    if not os.path.isdir(install_dir):
        result["is_portable"] = False
        result["warnings"].append("安装目录不存在")
        return result

    total_size = 0
    file_count = 0
    try:
        for root, dirs, files in os.walk(install_dir):
            for f in files:
                try:
                    total_size += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
                file_count += 1
                if file_count > 100000:  # 防止超量
                    break
            if file_count > 100000:
                break
    except (OSError, PermissionError):
        pass

    total_mb = total_size / (1024 * 1024)
    result["total_size_mb"] = round(total_mb, 1)
    result["file_count"] = file_count

    if total_mb > 2000:
        result["is_portable"] = False
        result["warnings"].append(f"程序目录过大 ({total_mb:.0f} MB)，不建议复制")
    elif total_mb > 500:
        result["warnings"].append(f"程序目录较大 ({total_mb:.0f} MB)，复制可能需要一些时间")

    return result


def get_program_description(exe_path: str) -> str:
    """从 exe 文件获取程序描述（通过 PowerShell）"""
    try:
        ps_script = (
            f'(Get-Item "{exe_path}").VersionInfo | '
            f'Select-Object FileDescription, ProductName | '
            f'ConvertTo-Json -Compress'
        )
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        if result.returncode == 0:
            import json
            info = json.loads(result.stdout.strip())
            desc = info.get("FileDescription", "") or info.get("ProductName", "") or ""
            return desc.strip()
    except Exception:
        pass
    return ""
