# 🧰 Windows 桌面工具箱

一个基于 **PyQt6** 做的现代化 Windows 程序启动器/工具箱。通过卡片式网格界面统一管理和快速启动各类程序，支持自动扫描、便携分发、主题可切换，适合个人日常使用或作为工具合集分享给他人。

---

##  功能特性

###  核心能力

| 功能 | 说明 |
|------|------|
| **程序卡片管理** | 以卡片网格展示所有程序，支持图标、名称、简介，三种尺寸（small / medium / large） |
| **智能扫描导入** | 自动从系统注册表、开始菜单、常用安装目录发现已安装程序，批量勾选一键导入 |
| **便携化分发** | 导入的程序自动复制到 `apps/` 目录，配置文件存相对路径，整个文件夹复制即可迁移 |
| **分类组织** | 内置分类（全部/开发工具/设计/游戏/办公/其他），支持自定义新建、重命名、删除 |
| **搜索过滤** | `Ctrl+F` 聚焦搜索框，输入关键词即时过滤显示 |
| **右键菜单** | 编辑信息、隐藏/显示、移动分类、删除程序 |
| **双主题** | 内置暗色主题和亮色主题，可自由切换 |
| **路径修复** | 迁移后自动在 `apps/` 目录搜索匹配程序，修复失效路径 |

###  界面亮点

- 流式卡片网格布局（自动换行，随窗口大小自适应）
- 6 种预设主题色（紫色/蓝色/绿色/橙色/红色/粉色），支持自定义取色
- 卡片圆角可调（0-24px）
- 字体与字号可自定义
- 隐藏程序半透明显示，右击可恢复
- 悬浮缩放动画 + 阴影效果
- 状态栏实时统计程序数量

---

##  项目结构

```
/
├── toolbox/                  # 源码目录
│   ├── __init__.py           # 包标识
│   ├── main.py               # 程序入口
│   ├── toolbox_app.py        # 主窗口（搜索、分类、卡片网格、右键菜单）
│   ├── config_manager.py     # 配置读写、程序 CRUD、图标/apps管理
│   ├── card_widget.py        # 程序卡片组件（图标、悬浮动画、阴影）
│   ├── dialogs.py            # 对话框（导入、扫描、编辑、设置、分类管理）
│   ├── program_scanner.py    # 系统程序扫描器（注册表/开始菜单/常用目录）
│   ├── flow_layout.py        # 流式布局引擎（自动换行网格）
│   └── styles.py             # QSS 样式表（暗色/亮色双主题）
├── app_icons/                # 程序图标存储目录
├── apps/                     # 导入的程序文件存储目录（便携分发关键）
├── config.json               # 配置文件（主题、分类、程序列表、窗口状态）
├── requirements.txt          # Python 依赖
├── 打包说明.txt              # 打包与分发详细说明
└── README.md                 # 本文件
```

---

##  快速开始

### 环境要求

- **Windows 10/11**
- **Python 3.10+**（推荐 3.11）
- PyQt6 >= 6.5.0

### 安装运行

```bash
# 1. 克隆或进入工具箱目录
cd 工具箱

# 2. 安装依赖
pip install -r requirements.txt

# 如果下载慢，使用清华镜像：
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 运行
python -m toolbox.main
```

首次启动后，程序会提示"是否扫描电脑中已安装的程序"——选"是"即可自动发现并批量导入。

---

##  打包为 EXE

> 详细的常见问题排查请查看 [打包说明.txt](./打包说明.txt)

### 前置准备

```bash
# 1. 创建干净虚拟环境（强烈推荐，可减小一半体积）
python -m venv venv
venv\Scripts\activate

# 2. 安装依赖
pip install pyqt6 pyinstaller

# 3. 先运行一次源码，确保 config.json 和 app_icons/ 已生成
python -m toolbox.main
```

### 方案一：文件夹分发（推荐）

打包为独立文件夹，而且相较于单文件多文件打开更快，配置也可修改，方便迁移分享。**推荐此方案。**

**PowerShell：**
```powershell
pyinstaller --onedir --windowed --name=工具箱 `
    --add-data "config.json;." `
    --add-data "app_icons;app_icons" `
    --add-data "apps;apps" `
    --hidden-import=PyQt6.QtCore `
    --hidden-import=PyQt6.QtGui `
    --hidden-import=PyQt6.QtWidgets `
    --exclude-module=tkinter `
    --clean `
    toolbox/main.py
```

打包完成后 `dist\工具箱\` 目录结构：

```
dist\工具箱\
├── 工具箱.exe          ← 双击启动
├── config.json         ← 可随时编辑
├── app_icons\          ← 图标目录
├── apps\               ← 导入的程序文件
└── _internal\          ← Python + PyQt6 运行库
```

将整个 `dist\工具箱\` 文件夹打包为 zip 发给对方，解压双击即可。

### 方案二：单文件 EXE（本人已经打包了这个，方便小白使用）

打包为单个 exe，简洁干净，但首次启动较慢（需自解压）。

**CMD：**
```batch
pyinstaller --onefile --windowed --name=工具箱 ^
    --add-data "config.json;." ^
    --add-data "app_icons;app_icons" ^
    --add-data "apps;apps" ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --exclude-module=tkinter ^
    --clean ^
    toolbox/main.py
```

> ⚠️ `--onefile` 注意：
> - exe 首次启动需要 3-8 秒自解压
> - `config.json` 内置在 exe 中，运行时会在同目录创建可编辑的副本
> - 分发时需要将 `apps\` 和 `app_icons\` 一起复制到 exe 同目录
> - 杀毒软件更容易误报，需添加信任

### 自定义图标

如果准备了 `.ico` 图标文件，在命令中添加：
```batch
--icon=app_icons/favicon.ico
```

### 减小体积

| 方法 | 效果 |
|------|------|
| 使用干净虚拟环境（只装 pyqt6 + pyinstaller） | ~80-120 MB → ~60-80 MB |
| 添加 `--exclude-module=tkinter` 等排除项 | 减少约 5-10 MB |
| 使用 UPX 压缩（需额外下载 upx.exe） | 再减少 20-30% |

预期打包后大小：`--onedir` 约 60-100 MB，`--onefile` 约 35-50 MB（PyQt6 的 Qt DLL 占大头）。

---

##  使用指南

### 导入程序

点击 ** 导入程序** → 选择 `.exe` 文件 → 支持两种模式：

| 模式 | 说明 |
|------|------|
|  复制整个程序文件夹（推荐） | 保留 DLL、配置文件等依赖，确保迁移后正常运行 |
| 仅复制 exe 文件 | 适合单文件绿色工具 |

### 扫描程序

点击 **🔍 扫描程序** → 自动从以下来源发现已安装程序：

| 来源 | 说明 |
|------|------|
| 系统注册表 | 最全面，读取 Uninstall 注册表项 |
| 开始菜单 | 解析 .lnk 快捷方式 |
| 常用安装目录 | 遍历 Program Files 等常见目录 |

扫描结果支持全选/反选/逐个勾选，确认后一键批量导入。

### 启动程序

- **双击卡片** → 启动程序
- 隐藏的程序会半透明显示，双击时提示确认

### 右键菜单

右键点击任意卡片可执行：

- **编辑** — 修改名称、路径、图标、简介、分类、卡片大小
- **隐藏/显示** — 控制卡片可见性
- **移动到分类** — 快速切换分类
- **删除** — 移除程序（同时清理图标和 `apps/` 下的文件）

### 主题设置

点击 ** 设置** 可自定义：

- 主题模式（暗色 / 亮色）
- 主题色（6 种预设 + 自定义取色）
- 字体与字号
- 卡片圆角 (0-24px)
- 默认卡片大小

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+F` | 聚焦搜索框 |

---

##  架构

```
┌─────────────────────────────────────────────┐
│                  main.py                     │
│            入口 · 高DPI · 启动窗口            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              toolbox_app.py                  │
│   主窗口 · 搜索栏 · 分类标签 · 流式网格 · 右键菜单  │
└──┬──────────┬──────────┬──────────┬─────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────────┐ ┌──────────┐
│card_ │ │config│ │program_  │ │styles.py │
│widget│ │_mana-│ │scanner.py│ │          │
│.py   │ │ger.py│ │          │ │QSS 样式表 │
│      │ │      │ │注册表    │ │暗色/亮色  │
│卡片  │ │配置  │ │开始菜单  │ │双主题    │
│组件  │ │CRUD  │ │常用目录  │ │          │
└──────┘ └──────┘ └──────────┘ └──────────┘
   │
   ▼
┌──────────┐    ┌──────────┐
│flow_     │    │dialogs.py│
│layout.py │    │          │
│          │    │导入/扫描 │
│流式布局  │    │编辑/设置 │
│自动换行  │    │分类管理  │
└──────────┘    └──────────┘
```

- **GUI 框架：** PyQt6
- **配置存储：** JSON（`config.json`）
- **程序扫描：** Windows 注册表 API (`winreg`) + PowerShell COM + 文件系统遍历
- **打包工具：** PyInstaller
- **运行环境：** Windows 10/11 + Python 3.10+

---

##  原理

工具箱实现便携化的核心机制：

1. **程序导入时自动复制到 `apps/` 目录**（支持整个文件夹或单文件复制）
2. **config.json 中存储相对路径**（如 `apps/MyApp/MyApp.exe`）
3. **运行时通过 `BASE_DIR` 动态解析路径**，兼容源码和打包两种模式
4. **路径修复机制：** 若程序路径失效（如迁移到其他电脑），自动在 `apps/` 目录中搜索同名 exe
5. **图标同理：** 图标自动提取到 `app_icons/` 目录，存相对路径

结论：将整个工具箱文件夹复制到任何 Windows 电脑即可使用，无需安装 Python 或任何依赖。

---

## ❓ 常见问题

<details>
<summary><b>Q: 打包后运行报错 "No module named 'toolbox'"</b></summary>

确保在工具箱**根目录**（包含 `toolbox/` 子目录的那个目录）执行打包命令，不要进入 `toolbox/` 目录内执行。
</details>

<details>
<summary><b>Q: 打包后界面没有图标</b></summary>

检查 `app_icons` 目录是否随 exe 一起分发。使用 `--add-data "app_icons;app_icons"` 参数确保图标目录被包含。
</details>

<details>
<summary><b>Q: 杀毒软件报毒</b></summary>

PyInstaller 打包的 exe 可能被部分杀毒软件误报，将工具箱添加至白名单即可，毕竟这是自己写的软件的通病。
</details>

<details>
<summary><b>Q: 迁移到其他电脑后程序启动失败</b></summary>

工具箱内置了路径修复功能。打开工具箱后，程序会自动检测失效路径并在 `apps/` 目录中搜索匹配程序。你也可以手动编辑程序、重新指定路径。
</details>

<details>
<summary><b>Q: 想使用自定义图标</b></summary>

1. 准备一个 `.ico` 文件放入 `app_icons/` 目录
2. 打包时添加 `--icon=app_icons/your_icon.ico`
3. 如果没有 `.ico` 文件，可省略 `--icon` 参数
</details>

---

## 📄 许可证

MIT License

---
## 效果展示   
<img width="894" height="613" alt="屏幕截图 2026-06-21 092420" src="https://github.com/user-attachments/assets/d0c839b0-1e54-45df-b7bb-c32b18792193" />
