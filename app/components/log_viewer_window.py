"""
日志查看器窗口
"""
from typing import Optional
from datetime import datetime

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QPushButton
)
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat

from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, PushButton as FluentPushButton,
    FluentIcon as FIF
)

from app.common.logger import get_signal_handler


# 日志级别颜色映射
LEVEL_COLORS = {
    "DEBUG": "#808080",    # 灰色
    "INFO": "#000000",     # 黑色
    "WARNING": "#FF8C00",  # 橙色
    "ERROR": "#FF0000",    # 红色
    "CRITICAL": "#8B0000", # 深红色
}


class LogViewerWindow(QWidget):
    """日志查看窗口"""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("日志查看器")
        self.setMinimumSize(800, 500)
        self.resize(1000, 600)

        self._initUI()
        self._connectSignals()

    def _initUI(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 标题栏
        headerLayout = QHBoxLayout()

        titleLabel = SubtitleLabel("实时日志", self)
        headerLayout.addWidget(titleLabel)

        headerLayout.addStretch()

        # 状态标签
        self.statusLabel = QLabel("监控中", self)
        self.statusLabel.setStyleSheet("color: #4CAF50; font-weight: bold;")
        headerLayout.addWidget(self.statusLabel)

        # 清空按钮
        self.clearBtn = FluentPushButton(FIF.DELETE, "清空", self)
        self.clearBtn.setFixedWidth(80)
        self.clearBtn.clicked.connect(self._clearLog)
        headerLayout.addWidget(self.clearBtn)

        layout.addLayout(headerLayout)

        # 日志文本框
        self.logTextEdit = QTextEdit(self)
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.logTextEdit)

        # 底部信息栏
        footerLayout = QHBoxLayout()

        self.lineCountLabel = QLabel("0 行", self)
        self.lineCountLabel.setStyleSheet("color: #666;")
        footerLayout.addWidget(self.lineCountLabel)

        footerLayout.addStretch()

        tipLabel = QLabel("提示: 日志自动滚动到最新", self)
        tipLabel.setStyleSheet("color: #999; font-size: 11px;")
        footerLayout.addWidget(tipLabel)

        layout.addLayout(footerLayout)

    def _connectSignals(self):
        """连接日志信号"""
        handler = get_signal_handler()
        if handler and handler.emitter:
            handler.emitter.log_received.connect(self._onLogReceived)

    @Slot(str, str)
    def _onLogReceived(self, level: str, message: str):
        """接收日志"""
        # 获取颜色
        color = LEVEL_COLORS.get(level, "#d4d4d4")

        # 创建文本格式
        cursor = self.logTextEdit.textCursor()
        cursor.movePosition(QTextCursor.End)

        format = QTextCharFormat()
        format.setForeground(QColor(color))

        # 添加时间戳
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor.insertText(f"[{timestamp}] ", self._getTimestampFormat())

        # 添加日志级别
        level_format = QTextCharFormat()
        level_format.setForeground(QColor(color))
        level_format.setFontWeight(700)
        cursor.insertText(f"[{level}] ", level_format)

        # 添加消息
        cursor.insertText(message + "\n", format)

        # 滚动到底部
        scrollbar = self.logTextEdit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

        # 更新行数
        self._updateLineCount()

    def _getTimestampFormat(self) -> QTextCharFormat:
        """获取时间戳格式"""
        format = QTextCharFormat()
        format.setForeground(QColor("#569CD6"))  # 蓝色
        return format

    def _clearLog(self):
        """清空日志"""
        self.logTextEdit.clear()
        self._updateLineCount()

    def _updateLineCount(self):
        """更新行数显示"""
        text = self.logTextEdit.toPlainText()
        lines = text.count("\n") + 1 if text else 0
        self.lineCountLabel.setText(f"{lines} 行")

    def closeEvent(self, event):
        """关闭事件 - 隐藏而不是关闭"""
        event.ignore()
        self.hide()
