"""
测试配置
"""
import pytest
from PySide6.QtWidgets import QApplication
import sys


@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def qtbot(qapp, qtbot):
    """确保 qtbot 有 qapp 上下文"""
    return qtbot
