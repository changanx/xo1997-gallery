"""
AI 模型配置数据模型
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import sqlite3
import json


@dataclass
class AIModelConfig:
    """AI 模型配置"""
    id: Optional[int] = None
    name: str = ""                          # 配置名称
    provider: str = "openai"                # 提供商: openai, azure, anthropic, ollama, custom
    model_name: str = ""                    # 模型名称
    api_key: str = ""                       # API Key
    base_url: str = ""                      # 自定义 API 地址
    temperature: float = 0.7                # 温度参数
    max_tokens: int = 2048                  # 最大 token 数
    extra_params: Dict[str, Any] = field(default_factory=dict)  # 额外参数
    is_default: bool = False                # 是否默认模型
    is_enabled: bool = True                 # 是否启用

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'AIModelConfig':
        """从数据库行创建实例"""
        extra_params = {}
        if row['extra_params']:
            try:
                extra_params = json.loads(row['extra_params'])
            except json.JSONDecodeError:
                pass

        return cls(
            id=row['id'],
            name=row['name'] or "",
            provider=row['provider'] or "openai",
            model_name=row['model_name'] or "",
            api_key=row['api_key'] or "",
            base_url=row['base_url'] or "",
            temperature=row['temperature'] or 0.7,
            max_tokens=row['max_tokens'] or 2048,
            extra_params=extra_params,
            is_default=bool(row['is_default']),
            is_enabled=bool(row['is_enabled']),
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'provider': self.provider,
            'model_name': self.model_name,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'extra_params': self.extra_params,
            'is_default': self.is_default,
            'is_enabled': self.is_enabled,
        }


@dataclass
class ChatMessage:
    """聊天消息"""
    id: Optional[int] = None
    session_id: int = 0                     # 会话 ID
    role: str = "user"                      # 角色: user, assistant, system
    content: str = ""                       # 消息内容
    created_at: str = ""                    # 创建时间

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'ChatMessage':
        """从数据库行创建实例"""
        return cls(
            id=row['id'],
            session_id=row['session_id'] or 0,
            role=row['role'] or "user",
            content=row['content'] or "",
            created_at=row['created_at'] or "",
        )


@dataclass
class ChatSession:
    """聊天会话"""
    id: Optional[int] = None
    title: str = "新对话"                   # 会话标题
    model_config_id: int = 0                # 使用的模型配置 ID
    created_at: str = ""                    # 创建时间
    updated_at: str = ""                    # 更新时间

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'ChatSession':
        """从数据库行创建实例"""
        return cls(
            id=row['id'],
            title=row['title'] or "新对话",
            model_config_id=row['model_config_id'] or 0,
            created_at=row['created_at'] or "",
            updated_at=row['updated_at'] or "",
        )
