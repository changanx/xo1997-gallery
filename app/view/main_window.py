"""
主窗口
"""
from qfluentwidgets import FluentWindow, FluentIcon as FIF, setTheme, Theme, NavigationItemPosition
from PySide6.QtCore import Qt

from .excel_ppt_interface import ExcelPPTInterface
from .ai_chat_interface import AIChatInterface
from .ai_settings_interface import AISettingsInterface
from .group_chat_interface import GroupChatInterface
from app.components.log_viewer_window import LogViewerWindow


class MainWindow(FluentWindow):
    """应用程序主窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建页面
        self.excelPptInterface = ExcelPPTInterface(self)
        self.aiChatInterface = AIChatInterface(self)
        self.groupChatInterface = GroupChatInterface(self)
        self.aiSettingsInterface = AISettingsInterface(self)

        # 创建日志窗口
        self.logViewerWindow = LogViewerWindow(self)

        self.initNavigation()
        self.initWindow()

        # 连接信号
        self.aiSettingsInterface.configChanged.connect(self._onConfigChanged)

    def initNavigation(self):
        """初始化导航"""
        self.addSubInterface(
            self.aiChatInterface,
            FIF.ROBOT,
            'AI 助手'
        )
        self.addSubInterface(
            self.groupChatInterface,
            FIF.PEOPLE,
            '群聊模式'
        )
        self.addSubInterface(
            self.excelPptInterface,
            FIF.DOCUMENT,
            'Excel→PPT'
        )
        self.navigationInterface.addSeparator()
        self.addSubInterface(
            self.aiSettingsInterface,
            FIF.SETTING,
            'AI 设置',
            position=NavigationItemPosition.BOTTOM
        )

        # 添加日志按钮到导航栏底部
        self.navigationInterface.addItem(
            routeKey='logViewer',
            icon=FIF.TAG,
            text='日志',
            onClick=self._showLogViewer,
            position=NavigationItemPosition.BOTTOM
        )

    def initWindow(self):
        """初始化窗口"""
        self.setWindowTitle('HR 工具箱')
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        # 设置主题
        setTheme(Theme.LIGHT)

    def _onConfigChanged(self):
        """配置变更时刷新 AI 对话页面"""
        self.aiChatInterface.refreshModels()

    def _showLogViewer(self):
        """显示日志查看窗口"""
        self.logViewerWindow.show()
        self.logViewerWindow.raise_()
        self.logViewerWindow.activateWindow()
