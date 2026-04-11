"""
LangChain Mock 对象
用于测试 ModelManager 的对话和工具调用功能
"""
from typing import List, Dict, Any, Optional, Generator
from unittest.mock import MagicMock


class MockAIMessageChunk:
    """Mock AIMessageChunk"""

    def __init__(self, content: str = "", additional_kwargs: Optional[Dict] = None):
        self.content = content
        self.additional_kwargs = additional_kwargs or {}
        self.tool_call_chunks = []
        self.tool_calls = []


class MockToolCallChunk:
    """Mock 工具调用片段"""

    def __init__(
        self,
        name: str = "",
        args: str = "",
        id: str = "",
        index: int = 0
    ):
        self.name = name
        self.args = args
        self.id = id
        self.index = index

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


class MockAIMessageWithToolCall:
    """Mock 带工具调用的 AI 消息"""

    def __init__(self, tool_calls: List[Dict[str, Any]]):
        self.content = ""
        self.tool_calls = tool_calls
        self.tool_call_chunks = []
        self.additional_kwargs = {}


class MockChatModel:
    """
    Mock LangChain 聊天模型

    用法:
        # 普通流式响应
        model = MockChatModel(responses=["你好", "世界"])

        # 带思考过程的响应
        model = MockChatModel(
            responses=["回答内容"],
            thinking=["思考过程1", "思考过程2"]
        )

        # 带工具调用的响应
        model = MockChatModel(
            responses=["我来帮你"],
            tool_calls=[{
                'id': 'call_1',
                'name': 'read_file',
                'args': {'file_path': 'test.txt'}
            }]
        )
    """

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        thinking: Optional[List[str]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        raise_error: Optional[Exception] = None
    ):
        """
        Args:
            responses: 流式响应内容列表
            thinking: 思考过程内容列表
            tool_calls: 工具调用列表
            raise_error: 是否抛出异常
        """
        self.responses = responses or ["测试响应"]
        self.thinking = thinking or []
        self.tool_calls = tool_calls or []
        self.raise_error = raise_error
        self._bound_tools = []
        self._invoke_count = 0
        self._stream_count = 0

    def stream(self, messages: List) -> Generator:
        """模拟流式响应"""
        if self.raise_error:
            raise self.raise_error

        self._stream_count += 1

        # 先返回思考过程
        for think in self.thinking:
            yield MockAIMessageChunk(
                content="",
                additional_kwargs={'reasoning_content': think}
            )

        # 返回内容
        for content in self.responses:
            yield MockAIMessageChunk(content=content)

        # 返回工具调用
        if self.tool_calls:
            tool_chunk = MockAIMessageChunk(content="")
            for tc in self.tool_calls:
                tool_chunk.tool_calls.append(tc)
            yield tool_chunk

    def invoke(self, messages: List) -> MockAIMessageChunk:
        """模拟非流式响应"""
        if self.raise_error:
            raise self.raise_error

        self._invoke_count += 1

        content = "".join(self.responses)
        additional_kwargs = {}
        if self.thinking:
            additional_kwargs['reasoning_content'] = "".join(self.thinking)

        if self.tool_calls:
            return MockAIMessageWithToolCall(self.tool_calls)

        return MockAIMessageChunk(content=content, additional_kwargs=additional_kwargs)

    def bind_tools(self, tools: List) -> 'MockChatModel':
        """模拟绑定工具"""
        self._bound_tools = tools
        return self

    @property
    def invoke_count(self) -> int:
        """invoke 被调用次数"""
        return self._invoke_count

    @property
    def stream_count(self) -> int:
        """stream 被调用次数"""
        return self._stream_count


class MockAnthropicMessageChunk:
    """Mock Anthropic 格式的消息片段"""

    def __init__(self, content: List[Dict[str, Any]]):
        self.content = content
        self.additional_kwargs = {}


class MockAnthropicThinkingBlock:
    """Mock Anthropic thinking block"""

    def __init__(self, thinking: str):
        self.type = "thinking"
        self.thinking = thinking


class MockAnthropicTextBlock:
    """Mock Anthropic text block"""

    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class MockAnthropicChatModel:
    """
    Mock Anthropic 格式的聊天模型

    支持 Extended Thinking 格式
    """

    def __init__(
        self,
        responses: Optional[List[str]] = None,
        thinking: Optional[List[str]] = None
    ):
        self.responses = responses or ["测试响应"]
        self.thinking = thinking or []
        self._bound_tools = []

    def stream(self, messages: List) -> Generator:
        """模拟 Anthropic 流式响应"""
        # 返回思考过程
        for think in self.thinking:
            yield MockAnthropicMessageChunk([
                {'type': 'thinking', 'thinking': think}
            ])

        # 返回内容
        for text in self.responses:
            yield MockAnthropicMessageChunk([
                {'type': 'text', 'text': text}
            ])

    def bind_tools(self, tools: List) -> 'MockAnthropicChatModel':
        self._bound_tools = tools
        return self


def create_mock_tool(name: str, func: callable) -> MagicMock:
    """
    创建 Mock 工具

    Args:
        name: 工具名称
        func: 工具执行函数

    Returns:
        Mock 工具对象
    """
    tool = MagicMock()
    tool.name = name
    tool.func = func
    return tool
