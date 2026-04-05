"""
主窗口
"""
from qfluentwidgets import FluentWindow, FluentIcon as FIF, setTheme, Theme
from PySide6.QtCore import Qt

from .excel_ppt_interface import ExcelPPTInterface


class MainWindow(FluentWindow):
    """应用程序主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建页面
        self.excelPptInterface = ExcelPPTInterface(self)

        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        """初始化导航"""
        self.addSubInterface(
            self.excelPptInterface,
            FIF.DOCUMENT,
            'Excel→PPT'
        )

    def initWindow(self):
        """初始化窗口"""
        self.setWindowTitle('HR 工具箱')
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # 设置主题
        setTheme(Theme.LIGHT)
