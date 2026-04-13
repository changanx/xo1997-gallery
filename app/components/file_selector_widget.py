"""
文件选择器组件
"""
from pathlib import Path
from typing import Optional

from app.ui import CardWidget, LineEdit, PushButton, FluentIcon
from PySide6.QtWidgets import QHBoxLayout, QFileDialog
from PySide6.QtCore import Signal


class FileSelectorWidget(CardWidget):
    """文件选择器组件"""

    pathChanged = Signal(str)

    def __init__(self, label: str, mode: str = "open", filter: str = "", parent=None):
        """
        Args:
            label: 标签文本
            mode: 模式 ("open", "save", "folder")
            filter: 文件过滤器 (如 "Excel Files (*.xlsx)")
        """
        super().__init__(parent)
        self._label = label
        self._mode = mode
        self._filter = filter
        self._path: Optional[str] = None

        self._initUI()

    def _initUI(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        self.pathEdit = LineEdit(self)
        self.pathEdit.setPlaceholderText(self._label)
        self.pathEdit.setReadOnly(True)

        self.browseBtn = PushButton("浏览", self)
        self.browseBtn.setFixedWidth(80)
        self.browseBtn.clicked.connect(self._onBrowse)

        layout.addWidget(self.pathEdit, 1)
        layout.addWidget(self.browseBtn)

    def _onBrowse(self):
        """浏览按钮点击"""
        path = None

        if self._mode == "open":
            path, _ = QFileDialog.getOpenFileName(self, self._label, "", self._filter)
        elif self._mode == "save":
            path, _ = QFileDialog.getSaveFileName(self, self._label, "", self._filter)
        elif self._mode == "folder":
            path = QFileDialog.getExistingDirectory(self, self._label)

        if path:
            self.setPath(path)
            self.pathChanged.emit(path)

    def setPath(self, path: str):
        """设置路径"""
        self._path = path
        self.pathEdit.setText(path)

    def path(self) -> Optional[str]:
        """获取路径"""
        return self._path

    def clear(self):
        """清空"""
        self._path = None
        self.pathEdit.clear()
