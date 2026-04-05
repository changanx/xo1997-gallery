"""
HR 工具箱 - 应用入口
"""
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from qfluentwidgets import setTheme, Theme

from app.view.main_window import MainWindow


def main():
    """应用程序入口"""
    app = QApplication(sys.argv)

    # 设置主题
    setTheme(Theme.LIGHT)

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
