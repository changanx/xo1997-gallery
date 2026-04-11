"""
ChatMessageWidget 组件测试
"""
import pytest
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot

from app.components.chat_message_widget import ChatMessageWidget


class TestChatMessageWidgetCreation:
    """ChatMessageWidget 创建测试"""

    def test_creation_user_message(self, qtbot: QtBot):
        """测试创建用户消息"""
        widget = ChatMessageWidget("user", "你好")
        qtbot.addWidget(widget)

        assert widget._role == "user"
        assert widget._content == "你好"
        assert widget._thinking == ""
        assert widget._tool_calls == []

    def test_creation_ai_message(self, qtbot: QtBot):
        """测试创建 AI 消息"""
        widget = ChatMessageWidget("assistant", "你好！")
        qtbot.addWidget(widget)

        assert widget._role == "assistant"
        assert widget._content == "你好！"

    def test_creation_empty_message(self, qtbot: QtBot):
        """测试创建空消息"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        assert widget._content == ""

    def test_user_message_no_thinking_widget(self, qtbot: QtBot):
        """测试用户消息没有思考过程组件"""
        widget = ChatMessageWidget("user", "测试")
        qtbot.addWidget(widget)

        # 用户消息不应该有 thinkingLabel
        assert not hasattr(widget, 'thinkingLabel') or widget.thinkingLabel is None

    def test_ai_message_has_thinking_widget(self, qtbot: QtBot):
        """测试 AI 消息有思考过程组件"""
        widget = ChatMessageWidget("assistant", "测试")
        qtbot.addWidget(widget)

        # AI 消息应该有 thinkingLabel（初始隐藏）
        assert hasattr(widget, 'thinkingLabel')
        assert widget.thinkingLabel.isVisible() is False


class TestChatMessageWidgetThinking:
    """ChatMessageWidget 思考过程测试"""

    def test_append_thinking(self, qtbot: QtBot):
        """测试追加思考过程"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        widget.appendThinking("思考中...")
        widget.appendThinking(" 继续思考")

        assert widget._thinking == "思考中... 继续思考"
        # thinkingLabel 在追加内容后会显示
        assert widget.thinkingLabel is not None

    def test_user_message_append_thinking_ignored(self, qtbot: QtBot):
        """测试用户消息忽略思考过程"""
        widget = ChatMessageWidget("user", "测试")
        qtbot.addWidget(widget)

        widget.appendThinking("应该被忽略")

        assert widget._thinking == ""


class TestChatMessageWidgetContent:
    """ChatMessageWidget 内容测试"""

    def test_append_content(self, qtbot: QtBot):
        """测试追加内容"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        widget.appendContent("Hello")
        widget.appendContent(" World")

        assert widget._content == "Hello World"

    def test_set_content(self, qtbot: QtBot):
        """测试设置内容"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        widget.setContent("完整内容")

        assert widget._content == "完整内容"

    def test_append_content_multiple_times(self, qtbot: QtBot):
        """测试多次追加内容（模拟流式输出）"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        chunks = ["你", "好", "，", "世", "界", "！"]
        for chunk in chunks:
            widget.appendContent(chunk)

        assert widget._content == "你好，世界！"


class TestChatMessageWidgetToolCalls:
    """ChatMessageWidget 工具调用测试"""

    def test_add_tool_call(self, qtbot: QtBot):
        """测试添加工具调用"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        widget.addToolCall("read_file", {"file_path": "test.txt"}, "call_1")

        assert len(widget._tool_calls) == 1
        assert widget._tool_calls[0]["name"] == "read_file"
        assert widget._tool_calls[0]["args"] == {"file_path": "test.txt"}
        # toolCallsWidget 应该已创建
        assert widget.toolCallsWidget is not None

    def test_add_multiple_tool_calls(self, qtbot: QtBot):
        """测试添加多个工具调用"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        widget.addToolCall("read_file", {"file_path": "a.txt"}, "call_1")
        widget.addToolCall("write_file", {"file_path": "b.txt", "content": "test"}, "call_2")

        assert len(widget._tool_calls) == 2

    def test_add_tool_result(self, qtbot: QtBot):
        """测试添加工具结果"""
        widget = ChatMessageWidget("assistant", "")
        qtbot.addWidget(widget)

        widget.addToolCall("read_file", {"file_path": "test.txt"}, "call_1")
        widget.addToolResult("read_file", "文件内容")

        assert widget._tool_calls[0]["result"] == "文件内容"

    def test_user_message_tool_calls_ignored(self, qtbot: QtBot):
        """测试用户消息忽略工具调用"""
        widget = ChatMessageWidget("user", "测试")
        qtbot.addWidget(widget)

        widget.addToolCall("read_file", {"file_path": "test.txt"}, "call_1")

        assert len(widget._tool_calls) == 0


class TestChatMessageWidgetCopy:
    """ChatMessageWidget 复制功能测试"""

    def test_copy_content(self, qtbot: QtBot):
        """测试复制内容"""
        widget = ChatMessageWidget("assistant", "测试内容")
        qtbot.addWidget(widget)

        widget._copyContent()

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        assert "测试内容" in clipboard.text()

    def test_copy_content_with_tool_calls(self, qtbot: QtBot):
        """测试复制包含工具调用的内容"""
        widget = ChatMessageWidget("assistant", "回答内容")
        qtbot.addWidget(widget)

        widget.addToolCall("read_file", {"file_path": "test.txt"}, "call_1")
        widget.addToolResult("read_file", "文件内容")

        widget._copyContent()

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        assert "回答内容" in text
        assert "read_file" in text
        assert "工具调用记录" in text


class TestChatMessageWidgetLayout:
    """ChatMessageWidget 布局测试"""

    def test_user_message_layout(self, qtbot: QtBot):
        """测试用户消息布局"""
        widget = ChatMessageWidget("user", "测试")
        qtbot.addWidget(widget)

        # 用户消息应该有特定样式
        assert widget.contentLabel is not None

    def test_ai_message_layout(self, qtbot: QtBot):
        """测试 AI 消息布局"""
        widget = ChatMessageWidget("assistant", "测试")
        qtbot.addWidget(widget)

        # AI 消息应该有思考区域和工具调用区域
        assert hasattr(widget, 'thinkingLabel')
        assert hasattr(widget, 'toolCallsWidget')

    def test_widget_minimum_size(self, qtbot: QtBot):
        """测试组件最小尺寸"""
        widget = ChatMessageWidget("assistant", "测试")
        qtbot.addWidget(widget)

        # 组件应该有合理的最小尺寸
        assert widget.minimumSizeHint().width() > 0
        assert widget.minimumSizeHint().height() > 0
