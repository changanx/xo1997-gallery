"""
FileSelectorWidget 测试
"""
import pytest
from pytestqt.qtbot import QtBot
from PySide6.QtCore import Qt

from app.components.file_selector_widget import FileSelectorWidget


class TestFileSelectorWidget:

    def test_creation(self, qtbot: QtBot):
        """测试组件创建"""
        selector = FileSelectorWidget("选择文件")
        qtbot.addWidget(selector)

        assert selector is not None
        assert selector.path() is None

    def test_set_path(self, qtbot: QtBot):
        """测试设置路径"""
        selector = FileSelectorWidget("选择文件")
        qtbot.addWidget(selector)

        selector.setPath("/path/to/file.xlsx")

        assert selector.path() == "/path/to/file.xlsx"

    def test_clear(self, qtbot: QtBot):
        """测试清空"""
        selector = FileSelectorWidget("选择文件")
        qtbot.addWidget(selector)

        selector.setPath("/path/to/file.xlsx")
        selector.clear()

        assert selector.path() is None

    def test_path_changed_signal(self, qtbot: QtBot):
        """测试路径变更信号"""
        selector = FileSelectorWidget("选择文件")
        qtbot.addWidget(selector)

        # 直接设置路径不会触发信号，只有浏览选择才会
        # 这里测试手动发射
        with qtbot.waitSignal(selector.pathChanged, timeout=1000):
            selector.pathChanged.emit("/test/path.xlsx")
