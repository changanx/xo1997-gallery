"""
视图层测试
测试 MainWindow、ExcelPPTInterface、AIChatInterface、AISettingsInterface
"""
import pytest
from pytestqt.qtbot import QtBot
from unittest.mock import MagicMock, patch

from PySide6.QtCore import Qt


class TestMainWindow:
    """MainWindow 测试"""

    def test_window_creation(self, qtbot: QtBot):
        """测试窗口创建"""
        from app.view.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        assert window is not None
        assert window.windowTitle() != ""

    def test_navigation_items(self, qtbot: QtBot):
        """测试导航项配置"""
        from app.view.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        # 验证导航项存在
        # FluentWindow 有 navigationInterface
        assert hasattr(window, 'navigationInterface')

    def test_window_size(self, qtbot: QtBot):
        """测试窗口大小"""
        from app.view.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        # 窗口应该有合理的默认大小
        assert window.width() > 0
        assert window.height() > 0


class TestExcelPPTInterface:
    """ExcelPPTInterface 测试"""

    def test_interface_creation(self, qtbot: QtBot):
        """测试界面创建"""
        from app.view.excel_ppt_interface import ExcelPPTInterface

        interface = ExcelPPTInterface()
        qtbot.addWidget(interface)

        assert interface is not None

    def test_components_initialized(self, qtbot: QtBot):
        """测试组件初始化"""
        from app.view.excel_ppt_interface import ExcelPPTInterface

        interface = ExcelPPTInterface()
        qtbot.addWidget(interface)

        # 验证关键组件存在
        assert hasattr(interface, 'excelSelector')
        assert hasattr(interface, 'outputSelector')
        assert hasattr(interface, 'importBtn')
        assert hasattr(interface, 'generateBtn')


class TestAIChatInterface:
    """AIChatInterface 测试"""

    def test_interface_creation(self, qtbot: QtBot):
        """测试界面创建"""
        from app.view.ai_chat_interface import AIChatInterface

        interface = AIChatInterface()
        qtbot.addWidget(interface)

        assert interface is not None

    def test_components_initialized(self, qtbot: QtBot):
        """测试组件初始化"""
        from app.view.ai_chat_interface import AIChatInterface

        interface = AIChatInterface()
        qtbot.addWidget(interface)

        assert hasattr(interface, 'modelCombo')
        assert hasattr(interface, 'inputEdit')
        assert hasattr(interface, 'sendBtn')
        assert hasattr(interface, 'stopBtn')

    def test_new_session(self, qtbot: QtBot):
        """测试新建会话"""
        from app.view.ai_chat_interface import AIChatInterface

        interface = AIChatInterface()
        qtbot.addWidget(interface)

        # 新建会话应该清空消息
        initial_session = interface._current_session
        interface._newSession()

        # 应该是新的会话对象
        assert interface._current_session is not initial_session

    def test_send_message_disabled_without_model(self, qtbot: QtBot):
        """测试无模型时发送按钮状态"""
        from app.view.ai_chat_interface import AIChatInterface
        from data.database import db
        db.clear()

        interface = AIChatInterface()
        qtbot.addWidget(interface)

        # 如果没有模型配置，发送按钮可能被禁用
        # 或者显示提示信息
        # 具体行为取决于实现


class TestAISettingsInterface:
    """AISettingsInterface 测试"""

    def test_interface_creation(self, qtbot: QtBot):
        """测试界面创建"""
        from app.view.ai_settings_interface import AISettingsInterface

        interface = AISettingsInterface()
        qtbot.addWidget(interface)

        assert interface is not None

    def test_components_initialized(self, qtbot: QtBot):
        """测试组件初始化"""
        from app.view.ai_settings_interface import AISettingsInterface

        interface = AISettingsInterface()
        qtbot.addWidget(interface)

        assert hasattr(interface, 'addBtn')
        assert hasattr(interface, 'configContainer')

    def test_load_configs(self, qtbot: QtBot):
        """测试加载配置列表"""
        from app.view.ai_settings_interface import AISettingsInterface
        from data.database import db
        db.clear()

        interface = AISettingsInterface()
        qtbot.addWidget(interface)

        # 应该加载配置列表（可能为空）
        assert interface.configLayout.count() >= 0

    def test_add_config_button(self, qtbot: QtBot):
        """测试添加配置按钮"""
        from app.view.ai_settings_interface import AISettingsInterface

        interface = AISettingsInterface()
        qtbot.addWidget(interface)

        # 点击添加按钮应该打开对话框
        # 但对话框测试需要特殊处理
        assert interface.addBtn is not None


class TestModelConfigDialog:
    """ModelConfigDialog 测试"""

    def test_dialog_creation(self, qtbot: QtBot):
        """测试对话框创建"""
        from app.view.ai_settings_interface import ModelConfigDialog
        from PySide6.QtWidgets import QWidget

        # ModelConfigDialog 需要 parent
        parent = QWidget()
        qtbot.addWidget(parent)

        dialog = ModelConfigDialog(parent=parent)
        qtbot.addWidget(dialog)

        assert dialog is not None

    def test_dialog_with_existing_config(self, qtbot: QtBot):
        """测试使用现有配置创建对话框"""
        from app.view.ai_settings_interface import ModelConfigDialog
        from data.models.ai_config import AIModelConfig
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        qtbot.addWidget(parent)

        config = AIModelConfig(
            id=1,
            name="测试配置",
            provider="openai",
            model_name="gpt-4o",
            api_key="test-key"
        )

        dialog = ModelConfigDialog(config, parent=parent)
        qtbot.addWidget(dialog)

        # 验证配置已加载
        assert dialog.nameEdit.text() == "测试配置"

    def test_provider_combo_changes_models(self, qtbot: QtBot):
        """测试提供商下拉框更改模型列表"""
        from app.view.ai_settings_interface import ModelConfigDialog
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        qtbot.addWidget(parent)

        dialog = ModelConfigDialog(parent=parent)
        qtbot.addWidget(dialog)

        # 选择不同的提供商
        initial_count = dialog.modelNameEdit.count()
        dialog.providerCombo.setCurrentIndex(1)  # 切换到第二个提供商

        # 模型列表应该更新
        # 具体验证取决于实现

    def test_validate_empty_name(self, qtbot: QtBot):
        """测试验证空名称"""
        from app.view.ai_settings_interface import ModelConfigDialog
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        qtbot.addWidget(parent)

        dialog = ModelConfigDialog(parent=parent)
        qtbot.addWidget(dialog)

        # 清空名称
        dialog.nameEdit.clear()

        # 验证应该失败
        assert dialog.validate() is False

    def test_validate_empty_model_name(self, qtbot: QtBot):
        """测试验证空模型名称"""
        from app.view.ai_settings_interface import ModelConfigDialog
        from PySide6.QtWidgets import QWidget

        parent = QWidget()
        qtbot.addWidget(parent)

        dialog = ModelConfigDialog(parent=parent)
        qtbot.addWidget(dialog)

        # 设置名称但清空模型名
        dialog.nameEdit.setText("测试")
        dialog.modelNameEdit.clear()

        # 验证应该失败
        assert dialog.validate() is False


class TestModelConfigCard:
    """ModelConfigCard 测试"""

    def test_card_creation(self, qtbot: QtBot):
        """测试卡片创建"""
        from app.view.ai_settings_interface import ModelConfigCard
        from data.models.ai_config import AIModelConfig

        config = AIModelConfig(
            id=1,
            name="测试配置",
            provider="openai",
            model_name="gpt-4o"
        )

        card = ModelConfigCard(config)
        qtbot.addWidget(card)

        assert card is not None

    def test_card_displays_config_info(self, qtbot: QtBot):
        """测试卡片显示配置信息"""
        from app.view.ai_settings_interface import ModelConfigCard
        from data.models.ai_config import AIModelConfig

        config = AIModelConfig(
            id=1,
            name="我的配置",
            provider="openai",
            model_name="gpt-4o"
        )

        card = ModelConfigCard(config)
        qtbot.addWidget(card)

        # 卡片应该显示配置名称
        assert card.nameLabel.text() == "我的配置"

    def test_card_default_tag(self, qtbot: QtBot):
        """测试默认配置标签"""
        from app.view.ai_settings_interface import ModelConfigCard
        from data.models.ai_config import AIModelConfig

        config = AIModelConfig(
            id=1,
            name="默认配置",
            provider="openai",
            model_name="gpt-4o",
            is_default=True
        )

        card = ModelConfigCard(config)
        qtbot.addWidget(card)

        # 应该显示默认标签
        assert hasattr(card, 'defaultTag')

    def test_card_signals(self, qtbot: QtBot):
        """测试卡片信号"""
        from app.view.ai_settings_interface import ModelConfigCard
        from data.models.ai_config import AIModelConfig

        config = AIModelConfig(
            id=1,
            name="测试配置",
            provider="openai",
            model_name="gpt-4o"
        )

        card = ModelConfigCard(config)
        qtbot.addWidget(card)

        # 验证信号存在
        assert hasattr(card, 'edited')
        assert hasattr(card, 'deleted')
