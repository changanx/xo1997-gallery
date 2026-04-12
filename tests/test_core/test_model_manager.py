"""
ModelManager 测试
"""
import pytest
from unittest.mock import MagicMock, patch
import json

from core.model_manager import ModelManager, MODEL_PROVIDERS
from data.models.ai_config import AIModelConfig


@pytest.fixture
def manager():
    """创建 ModelManager 实例"""
    return ModelManager()


@pytest.fixture
def sample_config():
    """创建示例配置"""
    return AIModelConfig(
        id=1,
        name="测试配置",
        provider="openai",
        model_name="gpt-4o",
        api_key="test-key",
        base_url="https://api.openai.com/v1",
        temperature=0.7,
        max_tokens=2048,
        is_default=True,
        is_enabled=True
    )


class TestModelProviders:
    """模型提供商测试"""

    def test_get_provider(self, manager):
        """测试获取提供商"""
        provider = manager.get_provider("openai")
        assert provider is not None
        assert provider.name == "OpenAI"

    def test_get_provider_not_exist(self, manager):
        """测试获取不存在的提供商"""
        provider = manager.get_provider("nonexistent")
        assert provider is None

    def test_get_all_providers(self, manager):
        """测试获取所有提供商"""
        providers = manager.get_all_providers()
        assert len(providers) == 9  # 预定义的 9 个提供商

    def test_provider_attributes(self, manager):
        """测试提供商属性"""
        provider = manager.get_provider("openai")
        assert provider.id == "openai"
        assert provider.default_base_url == "https://api.openai.com/v1"
        assert "gpt-4o" in provider.default_models
        assert provider.requires_api_key is True

    def test_ollama_no_api_key(self, manager):
        """测试 Ollama 不需要 API Key"""
        provider = manager.get_provider("ollama")
        assert provider.requires_api_key is False


class TestWorkDirectory:
    """工作目录测试"""

    def test_set_work_directory(self, manager, temp_work_dir):
        """测试设置工作目录"""
        manager.set_work_directory(str(temp_work_dir))

        assert manager.get_work_directory() == str(temp_work_dir)
        assert manager.has_tools() is True

    def test_has_tools_false_initially(self, manager):
        """测试初始状态没有工具"""
        assert manager.has_tools() is False

    def test_get_work_directory_none_initially(self, manager):
        """测试初始状态工作目录为 None"""
        assert manager.get_work_directory() is None


class TestCreateChatModel:
    """创建聊天模型测试"""

    def test_create_openai_model(self, manager, sample_config):
        """测试创建 OpenAI 模型"""
        with patch('langchain_openai.ChatOpenAI') as MockChatOpenAI:
            mock_model = MagicMock()
            MockChatOpenAI.return_value = mock_model

            model = manager.create_chat_model(sample_config)

            MockChatOpenAI.assert_called_once()
            assert model == mock_model

    def test_create_anthropic_model(self, manager):
        """测试创建 Anthropic 模型"""
        config = AIModelConfig(
            provider="anthropic",
            model_name="claude-3-opus",
            api_key="test-key",
            temperature=0.7,
            max_tokens=2048
        )

        with patch('langchain_anthropic.ChatAnthropic') as MockChatAnthropic:
            mock_model = MagicMock()
            MockChatAnthropic.return_value = mock_model

            model = manager.create_chat_model(config)

            MockChatAnthropic.assert_called_once()
            assert model == mock_model

    def test_create_ollama_model(self, manager):
        """测试创建 Ollama 模型"""
        config = AIModelConfig(
            provider="ollama",
            model_name="llama3",
            base_url="http://localhost:11434",
            temperature=0.7,
            max_tokens=2048
        )

        with patch('langchain_ollama.ChatOllama') as MockChatOllama:
            mock_model = MagicMock()
            MockChatOllama.return_value = mock_model

            model = manager.create_chat_model(config)

            MockChatOllama.assert_called_once()
            assert model == mock_model

    def test_create_deepseek_model(self, manager):
        """测试创建 DeepSeek 模型"""
        config = AIModelConfig(
            provider="deepseek",
            model_name="deepseek-chat",
            api_key="test-key",
            temperature=0.7,
            max_tokens=2048
        )

        with patch('langchain_openai.ChatOpenAI') as MockChatOpenAI:
            mock_model = MagicMock()
            MockChatOpenAI.return_value = mock_model

            model = manager.create_chat_model(config)

            MockChatOpenAI.assert_called_once()
            # 验证使用了 DeepSeek 的 base_url
            call_kwargs = MockChatOpenAI.call_args[1]
            assert "deepseek" in call_kwargs['base_url']

    def test_create_invalid_provider(self, manager):
        """测试无效提供商"""
        config = AIModelConfig(
            provider="invalid_provider",
            model_name="test"
        )

        with pytest.raises(ValueError, match="不支持的模型提供商"):
            manager.create_chat_model(config)


class TestSetCurrentModel:
    """设置当前模型测试"""

    def test_set_current_model(self, manager, sample_config):
        """测试设置当前模型"""
        with patch('langchain_openai.ChatOpenAI') as MockChatOpenAI:
            mock_model = MagicMock()
            MockChatOpenAI.return_value = mock_model

            manager.set_current_model(sample_config)

            assert manager.get_current_model() == mock_model
            assert manager.get_current_config() == sample_config

    def test_set_current_model_binds_tools(self, manager, sample_config, temp_work_dir):
        """测试设置模型时绑定工具"""
        manager.set_work_directory(str(temp_work_dir))

        with patch('langchain_openai.ChatOpenAI') as MockChatOpenAI:
            mock_model = MagicMock()
            mock_model.bind_tools = MagicMock(return_value=mock_model)
            MockChatOpenAI.return_value = mock_model

            manager.set_current_model(sample_config)

            # 验证工具已绑定
            mock_model.bind_tools.assert_called_once()


class TestChat:
    """对话测试"""

    def test_chat_no_model_raises(self, manager):
        """测试没有模型时聊天抛出异常"""
        with pytest.raises(RuntimeError, match="请先设置模型"):
            list(manager.chat([{"role": "user", "content": "test"}]))

    def test_chat_stream(self, manager, sample_config):
        """测试流式对话"""
        from tests.mocks.langchain_mock import MockChatModel

        mock_model = MockChatModel(responses=["Hello", " World"])
        manager._current_model = mock_model

        chunks = list(manager.chat([{"role": "user", "content": "Hi"}]))

        assert len(chunks) == 2
        assert chunks[0]["type"] == "content"
        assert chunks[0]["text"] == "Hello"
        assert chunks[1]["text"] == " World"

    def test_chat_with_thinking(self, manager, sample_config):
        """测试带思考过程的对话"""
        from tests.mocks.langchain_mock import MockChatModel

        mock_model = MockChatModel(
            responses=["回答"],
            thinking=["思考中..."]
        )
        manager._current_model = mock_model

        chunks = list(manager.chat([{"role": "user", "content": "test"}]))

        # 应该有思考过程和内容
        thinking_chunks = [c for c in chunks if c["type"] == "thinking"]
        content_chunks = [c for c in chunks if c["type"] == "content"]

        assert len(thinking_chunks) == 1
        assert len(content_chunks) == 1


class TestChatWithTools:
    """工具调用对话测试"""

    def test_chat_with_tools_no_model_raises(self, manager):
        """测试没有模型时工具调用抛出异常"""
        with pytest.raises(RuntimeError, match="请先设置模型"):
            list(manager.chat_with_tools([{"role": "user", "content": "test"}]))

    def test_chat_with_tools_no_tools(self, manager, sample_config):
        """测试没有工具时的对话"""
        from tests.mocks.langchain_mock import MockChatModel

        mock_model = MockChatModel(responses=["Hello"])
        manager._current_model = mock_model

        chunks = list(manager.chat_with_tools([{"role": "user", "content": "Hi"}]))

        content_chunks = [c for c in chunks if c["type"] == "content"]
        assert len(content_chunks) == 1


class TestConvertMessages:
    """消息转换测试"""

    def test_convert_user_message(self, manager):
        """测试转换用户消息"""
        from langchain_core.messages import HumanMessage

        messages = [{"role": "user", "content": "Hello"}]
        lc_messages = manager._convert_messages(messages)

        assert len(lc_messages) == 1
        assert isinstance(lc_messages[0], HumanMessage)
        assert lc_messages[0].content == "Hello"

    def test_convert_assistant_message(self, manager):
        """测试转换助手消息"""
        from langchain_core.messages import AIMessage

        messages = [{"role": "assistant", "content": "Hi"}]
        lc_messages = manager._convert_messages(messages)

        assert len(lc_messages) == 1
        assert isinstance(lc_messages[0], AIMessage)

    def test_convert_system_message(self, manager):
        """测试转换系统消息"""
        from langchain_core.messages import SystemMessage

        messages = [{"role": "system", "content": "You are helpful"}]
        lc_messages = manager._convert_messages(messages)

        assert len(lc_messages) == 1
        assert isinstance(lc_messages[0], SystemMessage)

    def test_convert_mixed_messages(self, manager):
        """测试转换混合消息"""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"}
        ]
        lc_messages = manager._convert_messages(messages)

        assert len(lc_messages) == 4


class TestAggregateToolCalls:
    """工具调用聚合测试"""

    def test_aggregate_single_tool_call(self, manager):
        """测试聚合单个工具调用"""
        chunks = [
            {"index": 0, "name": "read_file", "args": '{"file_path":', "id": "call_1"},
            {"index": 0, "name": "", "args": ' "test.txt"}', "id": ""}
        ]

        result = manager._aggregate_tool_calls(chunks)

        assert len(result) == 1
        assert result[0]["name"] == "read_file"
        assert result[0]["args"] == {"file_path": "test.txt"}
        assert result[0]["id"] == "call_1"

    def test_aggregate_multiple_tool_calls(self, manager):
        """测试聚合多个工具调用"""
        chunks = [
            {"index": 0, "name": "read_file", "args": '{"file_path": "a.txt"}', "id": "call_1"},
            {"index": 1, "name": "write_file", "args": '{"file_path": "b.txt"}', "id": "call_2"}
        ]

        result = manager._aggregate_tool_calls(chunks)

        assert len(result) == 2
        assert result[0]["name"] == "read_file"
        assert result[1]["name"] == "write_file"

    def test_aggregate_invalid_json(self, manager):
        """测试无效 JSON 参数"""
        chunks = [
            {"index": 0, "name": "test_tool", "args": "not valid json", "id": "call_1"}
        ]

        result = manager._aggregate_tool_calls(chunks)

        # 无效 JSON 应该返回包含错误信息的结构
        assert len(result) == 1
        assert "_parse_error" in result[0]["args"]
        assert "_raw_args" in result[0]["args"]
        assert result[0]["args"]["_raw_args"] == "not valid json"


class TestExecuteTool:
    """工具执行测试"""

    def test_execute_tool_unknown(self, manager):
        """测试执行未知工具"""
        result = manager._execute_tool("unknown_tool", {})
        assert "错误" in result
        assert "未知" in result

    def test_execute_tool_with_work_directory(self, manager, temp_work_dir):
        """测试在工作目录中执行工具"""
        manager.set_work_directory(str(temp_work_dir))

        # 创建测试文件
        test_file = temp_work_dir / "test.txt"
        test_file.write_text("content", encoding='utf-8')

        # 执行 read_file 工具
        result = manager._execute_tool("read_file", {"file_path": "test.txt"})
        assert result == "content"
