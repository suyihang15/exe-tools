"""工具箱入口"""

import sys
import os

# 解决 PyInstaller 打包后的路径问题
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 确保能找到 toolbox 模块
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def main():
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication

    # 高 DPI 适配
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("工具箱")
    app.setOrganizationName("Toolbox")

    from toolbox.toolbox_app import ToolboxApp

    window = ToolboxApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
