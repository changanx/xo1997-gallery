"""
群聊数据层测试
"""
import pytest
import json

from data.models.group_chat import GroupChatSession, GroupChatParticipant, GroupChatMessage
from data.repositories.group_chat_repository import (
    GroupChatSessionRepository,
    GroupChatParticipantRepository,
    GroupChatMessageRepository,
)
from data.repositories.ai_config_repository import AIModelConfigRepository
from data.models.ai_config import AIModelConfig


class TestGroupChatSessionModel:
    """群聊会话模型测试"""

    def test_create_session(self):
        """测试创建会话"""
        session = GroupChatSession(
            title="测试群聊",
            max_discussion_rounds=3
        )
        assert session.title == "测试群聊"
        assert session.max_discussion_rounds == 3
        assert session.id is None

    def test_session_to_dict(self):
        """测试会话转字典"""
        session = GroupChatSession(
            id=1,
            title="测试",
            max_discussion_rounds=5
        )
        d = session.to_dict()
        assert d['id'] == 1
        assert d['title'] == "测试"
        assert d['max_discussion_rounds'] == 5


class TestGroupChatParticipantModel:
    """群聊参与者模型测试"""

    def test_create_participant(self):
        """测试创建参与者"""
        participant = GroupChatParticipant(
            session_id=1,
            model_config_id=1,
            nickname="@gpt-4",
            role_description="代码审查专家"
        )
        assert participant.session_id == 1
        assert participant.model_config_id == 1
        assert participant.nickname == "@gpt-4"
        assert participant.role_description == "代码审查专家"

    def test_participant_to_dict(self):
        """测试参与者转字典"""
        participant = GroupChatParticipant(
            id=1,
            session_id=1,
            model_config_id=2,
            nickname="@claude",
            role_description="架构分析师"
        )
        d = participant.to_dict()
        assert d['id'] == 1
        assert d['nickname'] == "@claude"


class TestGroupChatMessageModel:
    """群聊消息模型测试"""

    def test_create_message(self):
        """测试创建消息"""
        message = GroupChatMessage(
            session_id=1,
            role="user",
            content="你好",
            mentioned_models=[1, 2],
            discussion_round=1
        )
        assert message.session_id == 1
        assert message.role == "user"
        assert message.content == "你好"
        assert message.mentioned_models == [1, 2]
        assert message.discussion_round == 1

    def test_message_to_dict(self):
        """测试消息转字典"""
        message = GroupChatMessage(
            id=1,
            session_id=1,
            role="assistant",
            model_config_id=1,
            content="回复内容",
            mentioned_models=[],
            discussion_round=1
        )
        d = message.to_dict()
        assert d['id'] == 1
        assert d['role'] == "assistant"
        assert d['model_config_id'] == 1


class TestGroupChatSessionRepository:
    """群聊会话仓库测试"""

    def setup_method(self):
        """每个测试前初始化仓库"""
        # 数据清理由 conftest.py 的 clean_persistent_db fixture 自动处理
        pass

    def test_save_and_find_session(self):
        """测试保存和查找会话"""
        repo = GroupChatSessionRepository()

        session = GroupChatSession(title="测试群聊", max_discussion_rounds=3)
        saved = repo.save(session)

        assert saved.id is not None

        found = repo.find_by_id(saved.id)
        assert found is not None
        assert found.title == "测试群聊"
        assert found.max_discussion_rounds == 3

    def test_find_all_sessions(self):
        """测试获取所有会话"""
        repo = GroupChatSessionRepository()

        repo.save(GroupChatSession(title="群聊1"))
        repo.save(GroupChatSession(title="群聊2"))

        sessions = repo.find_all()
        assert len(sessions) == 2

    def test_delete_session(self):
        """测试删除会话"""
        repo = GroupChatSessionRepository()

        session = repo.save(GroupChatSession(title="要删除的群聊"))
        assert repo.delete(session.id)

        assert repo.find_by_id(session.id) is None

    def test_update_session(self):
        """测试更新会话"""
        repo = GroupChatSessionRepository()

        session = repo.save(GroupChatSession(title="原标题"))
        session.title = "新标题"
        session.max_discussion_rounds = 5
        repo.save(session)

        found = repo.find_by_id(session.id)
        assert found.title == "新标题"
        assert found.max_discussion_rounds == 5


class TestGroupChatParticipantRepository:
    """群聊参与者仓库测试"""

    def setup_method(self):
        """每个测试前创建测试会话和模型配置"""
        # 数据清理由 conftest.py 的 clean_persistent_db fixture 自动处理

        # 创建会话
        self.session_repo = GroupChatSessionRepository()
        self.session = self.session_repo.save(GroupChatSession(title="测试群聊"))

        # 创建模型配置
        self.config_repo = AIModelConfigRepository()
        self.config = self.config_repo.save(AIModelConfig(
            name="GPT-4",
            provider="openai",
            model_name="gpt-4o",
            api_key="test-key",
            is_default=True,
            is_enabled=True
        ))

    def test_add_participant(self):
        """测试添加参与者"""
        repo = GroupChatParticipantRepository()

        participant = repo.save(GroupChatParticipant(
            session_id=self.session.id,
            model_config_id=self.config.id,
            nickname="@gpt-4",
            role_description="代码审查专家"
        ))

        assert participant.id is not None

    def test_find_by_session(self):
        """测试查找会话的参与者"""
        repo = GroupChatParticipantRepository()

        repo.save(GroupChatParticipant(
            session_id=self.session.id,
            model_config_id=self.config.id,
            nickname="@gpt-4"
        ))

        participants = repo.find_by_session(self.session.id)
        assert len(participants) == 1
        assert participants[0].nickname == "@gpt-4"

    def test_delete_participant(self):
        """测试删除参与者"""
        repo = GroupChatParticipantRepository()

        participant = repo.save(GroupChatParticipant(
            session_id=self.session.id,
            model_config_id=self.config.id,
            nickname="@gpt-4"
        ))

        assert repo.delete(participant.id)
        assert len(repo.find_by_session(self.session.id)) == 0


class TestGroupChatMessageRepository:
    """群聊消息仓库测试"""

    def setup_method(self):
        """每个测试前创建测试会话和模型配置"""
        # 数据清理由 conftest.py 的 clean_persistent_db fixture 自动处理

        self.session_repo = GroupChatSessionRepository()
        self.session = self.session_repo.save(GroupChatSession(title="测试群聊"))

        # 创建模型配置（用于 assistant 消息）
        self.config_repo = AIModelConfigRepository()
        self.config = self.config_repo.save(AIModelConfig(
            name="GPT-4",
            provider="openai",
            model_name="gpt-4o",
            api_key="test-key",
            is_default=True,
            is_enabled=True
        ))

    def test_save_message(self):
        """测试保存消息"""
        repo = GroupChatMessageRepository()

        message = repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="user",
            content="你好"
        ))

        assert message.id is not None

    def test_find_by_session(self):
        """测试查找会话消息"""
        repo = GroupChatMessageRepository()

        repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="user",
            content="用户消息"
        ))
        repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="assistant",
            model_config_id=self.config.id,
            content="AI 回复"
        ))

        messages = repo.find_by_session(self.session.id)
        assert len(messages) == 2

    def test_find_latest_round(self):
        """测试查找最新轮次"""
        repo = GroupChatMessageRepository()

        repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="user",
            content="消息1",
            discussion_round=1
        ))
        repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="assistant",
            model_config_id=self.config.id,
            content="消息2",
            discussion_round=1
        ))
        repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="user",
            content="消息3",
            discussion_round=2
        ))

        latest = repo.find_latest_round(self.session.id)
        assert latest == 2

    def test_delete_by_session(self):
        """测试删除会话消息"""
        repo = GroupChatMessageRepository()

        repo.save(GroupChatMessage(
            session_id=self.session.id,
            role="user",
            content="消息"
        ))

        count = repo.delete_by_session(self.session.id)
        assert count == 1
        assert len(repo.find_by_session(self.session.id)) == 0
