"""
群聊数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, List
import sqlite3
import json

from app.common.logger import get_logger

logger = get_logger()


@dataclass
class GroupChatSession:
    """群聊会话"""
    id: Optional[int] = None
    title: str = "新群聊"                   # 会话标题
    max_discussion_rounds: int = 3          # 最大讨论轮次
    created_at: str = ""                    # 创建时间
    updated_at: str = ""                    # 更新时间

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'GroupChatSession':
        """从数据库行创建实例"""
        return cls(
            id=row['id'],
            title=row['title'] or "新群聊",
            max_discussion_rounds=row['max_discussion_rounds'] or 3,
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or "",
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'max_discussion_rounds': self.max_discussion_rounds,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class GroupChatParticipant:
    """群聊参与者（全局配置）"""
    id: Optional[int] = None
    model_config_id: int = 0                # 模型配置 ID
    nickname: str = ""                      # 群聊中的昵称（如 @gpt4）
    role_description: str = ""              # 角色描述
    avatar: str = "ROBOT"                   # 头像图标名称（FluentIcon）
    fish_audio_voice_id: str = ""           # Fish Audio 音色 ID
    created_at: str = ""                    # 创建时间

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'GroupChatParticipant':
        """从数据库行创建实例"""
        return cls(
            id=row['id'],
            model_config_id=row['model_config_id'] or 0,
            nickname=row['nickname'] or "",
            role_description=row['role_description'] or "",
            avatar=row['avatar'] or "ROBOT",
            fish_audio_voice_id=row['fish_audio_voice_id'] or "",
            created_at=row['created_at'] or "",
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'model_config_id': self.model_config_id,
            'nickname': self.nickname,
            'role_description': self.role_description,
            'avatar': self.avatar,
            'fish_audio_voice_id': self.fish_audio_voice_id,
            'created_at': self.created_at,
        }


@dataclass
class GroupChatMessage:
    """群聊消息"""
    id: Optional[int] = None
    session_id: int = 0                     # 会话 ID
    role: str = "user"                      # 角色: user, assistant
    participant_id: Optional[int] = None    # 参与者 ID（assistant 时）
    content: str = ""                       # 消息内容
    mentioned_models: List[int] = field(default_factory=list)  # 被 @ 的参与者 ID 列表
    discussion_round: int = 0               # 第几轮讨论
    created_at: str = ""                    # 创建时间

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'GroupChatMessage':
        """从数据库行创建实例"""
        mentioned_models = []
        if row['mentioned_models']:
            try:
                mentioned_models = json.loads(row['mentioned_models'])
                if not isinstance(mentioned_models, list):
                    logger.warning("mentioned_models 不是有效的列表", extra={"value": str(mentioned_models)[:100]})
                    mentioned_models = []
            except json.JSONDecodeError as e:
                logger.warning("mentioned_models JSON 解析失败", extra={"error": str(e), "raw": str(row['mentioned_models'])[:100]})
                mentioned_models = []

        return cls(
            id=row['id'],
            session_id=row['session_id'] or 0,
            role=row['role'] or "user",
            participant_id=row['participant_id'],
            content=row['content'] or "",
            mentioned_models=mentioned_models,
            discussion_round=row['discussion_round'] or 0,
            created_at=row['created_at'] or "",
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'participant_id': self.participant_id,
            'content': self.content,
            'mentioned_models': self.mentioned_models,
            'discussion_round': self.discussion_round,
            'created_at': self.created_at,
        }
