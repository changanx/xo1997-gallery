"""
StatusCardWidget 测试
"""
import pytest
from pytestqt.qtbot import QtBot

from app.components.status_card_widget import StatusCardWidget


class TestStatusCardWidget:

    def test_creation(self, qtbot: QtBot):
        """测试组件创建"""
        card = StatusCardWidget("部门数量", "10")
        qtbot.addWidget(card)

        assert card is not None
        assert card.value() == "10"

    def test_set_value(self, qtbot: QtBot):
        """测试设置值"""
        card = StatusCardWidget("员工数量", "0")
        qtbot.addWidget(card)

        card.setValue("100")

        assert card.value() == "100"

    def test_set_int_value(self, qtbot: QtBot):
        """测试设置整数值"""
        card = StatusCardWidget("计数", "0")
        qtbot.addWidget(card)

        card.setValue(42)

        assert card.value() == "42"
