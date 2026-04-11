"""
AI 配置仓库测试
"""
import pytest

from data.database import db
from data.models.ai_config import AIModelConfig, ChatSession, ChatMessage
from data.repositories.ai_config_repository import (
    AIModelConfigRepository,
    ChatSessionRepository,
    ChatMessageRepository
)


class TestAIModelConfigRepository:
    """AI 模型配置仓库测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()
        self.repo = AIModelConfigRepository()

    def test_save_and_find(self):
        """测试保存和查找"""
        config = AIModelConfig(
            name="腾讯云 Claude",
            provider="tencent_claude",
            model_name="glm-5",
            api_key="test-key",
            base_url="https://api.lkeap.cloud.tencent.com/coding/anthropic",
            temperature=0.7,
            max_tokens=4096
        )

        saved = self.repo.save(config)
        assert saved.id is not None

        found = self.repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == "腾讯云 Claude"
        assert found.provider == "tencent_claude"
        assert found.model_name == "glm-5"

    def test_find_all(self):
        """测试获取所有配置"""
        self.repo.save(AIModelConfig(name="配置1", provider="openai", model_name="gpt-4o"))
        self.repo.save(AIModelConfig(name="配置2", provider="anthropic", model_name="claude-3"))

        configs = self.repo.find_all()
        assert len(configs) == 2

    def test_find_enabled(self):
        """测试获取启用的配置"""
        self.repo.save(AIModelConfig(name="启用", provider="openai", model_name="gpt-4o", is_enabled=True))
        self.repo.save(AIModelConfig(name="禁用", provider="openai", model_name="gpt-3.5", is_enabled=False))

        configs = self.repo.find_enabled()
        assert len(configs) == 1
        assert configs[0].name == "启用"

    def test_set_default(self):
        """测试设置默认"""
        c1 = self.repo.save(AIModelConfig(name="配置1", provider="openai", model_name="gpt-4o", is_default=True))
        c2 = self.repo.save(AIModelConfig(name="配置2", provider="anthropic", model_name="claude-3"))

        self.repo.set_default(c2.id)

        default = self.repo.find_default()
        assert default.id == c2.id

    def test_delete(self):
        """测试删除"""
        config = self.repo.save(AIModelConfig(name="待删除", provider="openai", model_name="gpt-4o"))

        assert self.repo.delete(config.id) is True
        assert self.repo.find_by_id(config.id) is None

    def test_extra_params(self):
        """测试额外参数"""
        config = AIModelConfig(
            name="带额外参数",
            provider="openai",
            model_name="gpt-4o",
            extra_params={"top_p": 0.9, "frequency_penalty": 0.5}
        )

        saved = self.repo.save(config)
        found = self.repo.find_by_id(saved.id)

        assert found.extra_params["top_p"] == 0.9
        assert found.extra_params["frequency_penalty"] == 0.5


class TestChatSessionRepository:
    """聊天会话仓库测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()
        self.repo = ChatSessionRepository()
        self.config_repo = AIModelConfigRepository()

    def test_save_and_find(self):
        """测试保存和查找"""
        config = self.config_repo.save(
            AIModelConfig(name="测试", provider="openai", model_name="gpt-4o")
        )

        session = ChatSession(title="测试会话", model_config_id=config.id)
        saved = self.repo.save(session)

        assert saved.id is not None
        assert saved.title == "测试会话"

    def test_find_all(self):
        """测试获取所有会话"""
        self.repo.save(ChatSession(title="会话1"))
        self.repo.save(ChatSession(title="会话2"))

        sessions = self.repo.find_all()
        assert len(sessions) == 2

    def test_update_title(self):
        """测试更新标题"""
        session = self.repo.save(ChatSession(title="旧标题"))

        self.repo.update_title(session.id, "新标题")

        found = self.repo.find_by_id(session.id)
        assert found.title == "新标题"


class TestChatMessageRepository:
    """聊天消息仓库测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()
        self.session_repo = ChatSessionRepository()
        self.message_repo = ChatMessageRepository()

    def test_save_and_find(self):
        """测试保存和查找"""
        session = self.session_repo.save(ChatSession(title="测试"))

        msg = ChatMessage(session_id=session.id, role="user", content="你好")
        saved = self.message_repo.save(msg)

        assert saved.id is not None

        messages = self.message_repo.find_by_session(session.id)
        assert len(messages) == 1
        assert messages[0].content == "你好"

    def test_conversation(self):
        """测试对话"""
        session = self.session_repo.save(ChatSession(title="对话"))

        self.message_repo.save(ChatMessage(session_id=session.id, role="user", content="你好"))
        self.message_repo.save(ChatMessage(session_id=session.id, role="assistant", content="你好！有什么可以帮助你的吗？"))

        messages = self.message_repo.find_by_session(session.id)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_count_by_session(self):
        """测试消息计数"""
        session = self.session_repo.save(ChatSession(title="测试"))

        self.message_repo.save(ChatMessage(session_id=session.id, role="user", content="消息1"))
        self.message_repo.save(ChatMessage(session_id=session.id, role="assistant", content="消息2"))

        count = self.message_repo.count_by_session(session.id)
        assert count == 2

    def test_delete_by_session(self):
        """测试删除会话消息"""
        session = self.session_repo.save(ChatSession(title="测试"))

        self.message_repo.save(ChatMessage(session_id=session.id, role="user", content="消息"))
        self.message_repo.save(ChatMessage(session_id=session.id, role="assistant", content="回复"))

        deleted_count = self.message_repo.delete_by_session(session.id)
        assert deleted_count == 2

        count = self.message_repo.count_by_session(session.id)
        assert count == 0
