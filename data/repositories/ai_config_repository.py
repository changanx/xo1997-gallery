"""
AI 配置数据仓库
"""
import json
from typing import List, Optional

from ..database import persistent_db
from ..models.ai_config import AIModelConfig, ChatMessage, ChatSession


class AIModelConfigRepository:
    """AI 模型配置仓库"""

    def find_all(self) -> List[AIModelConfig]:
        """获取所有模型配置"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM ai_model_config ORDER BY is_default DESC, name"
        )
        return [AIModelConfig.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[AIModelConfig]:
        """根据 ID 查找"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM ai_model_config WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return AIModelConfig.from_row(row) if row else None

    def find_enabled(self) -> List[AIModelConfig]:
        """获取所有启用的模型配置"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM ai_model_config WHERE is_enabled = 1 ORDER BY is_default DESC, name"
        )
        return [AIModelConfig.from_row(row) for row in cursor.fetchall()]

    def find_default(self) -> Optional[AIModelConfig]:
        """获取默认模型配置"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM ai_model_config WHERE is_default = 1 AND is_enabled = 1 LIMIT 1"
        )
        row = cursor.fetchone()
        return AIModelConfig.from_row(row) if row else None

    def save(self, config: AIModelConfig) -> AIModelConfig:
        """保存模型配置"""
        extra_params_json = json.dumps(config.extra_params) if config.extra_params else None

        if config.id is None:
            cursor = persistent_db.connection.execute(
                """
                INSERT INTO ai_model_config (name, provider, model_name, api_key, base_url,
                    temperature, max_tokens, extra_params, is_default, is_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (config.name, config.provider, config.model_name, config.api_key,
                 config.base_url, config.temperature, config.max_tokens,
                 extra_params_json, int(config.is_default), int(config.is_enabled))
            )
            config.id = cursor.lastrowid
        else:
            persistent_db.connection.execute(
                """
                UPDATE ai_model_config SET name=?, provider=?, model_name=?, api_key=?,
                    base_url=?, temperature=?, max_tokens=?, extra_params=?,
                    is_default=?, is_enabled=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (config.name, config.provider, config.model_name, config.api_key,
                 config.base_url, config.temperature, config.max_tokens,
                 extra_params_json, int(config.is_default), int(config.is_enabled), config.id)
            )
        persistent_db.connection.commit()
        return config

    def delete(self, id: int) -> bool:
        """删除模型配置"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM ai_model_config WHERE id = ?", (id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def set_default(self, id: int) -> bool:
        """
        设置默认模型

        使用单条 SQL 语句确保原子性，避免并发问题
        """
        # 使用 CASE 表达式在单条语句中完成更新
        cursor = persistent_db.connection.execute(
            """
            UPDATE ai_model_config
            SET is_default = CASE WHEN id = ? THEN 1 ELSE 0 END
            """,
            (id,)
        )
        # 检查是否设置了指定的模型
        check_cursor = persistent_db.connection.execute(
            "SELECT is_default FROM ai_model_config WHERE id = ?", (id,)
        )
        result = check_cursor.fetchone()
        persistent_db.connection.commit()
        return result is not None and result['is_default'] == 1

    def count(self) -> int:
        """统计配置数量"""
        cursor = persistent_db.connection.execute("SELECT COUNT(*) FROM ai_model_config")
        return cursor.fetchone()[0]


class ChatSessionRepository:
    """聊天会话仓库"""

    def find_all(self, limit: int = 50) -> List[ChatSession]:
        """获取所有会话"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM chat_session ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        return [ChatSession.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[ChatSession]:
        """根据 ID 查找"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM chat_session WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return ChatSession.from_row(row) if row else None

    def save(self, session: ChatSession) -> ChatSession:
        """保存会话"""
        if session.id is None:
            cursor = persistent_db.connection.execute(
                """
                INSERT INTO chat_session (title, model_config_id)
                VALUES (?, ?)
                """,
                (session.title, session.model_config_id)
            )
            session.id = cursor.lastrowid
        else:
            persistent_db.connection.execute(
                """
                UPDATE chat_session SET title=?, model_config_id=?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (session.title, session.model_config_id, session.id)
            )
        persistent_db.connection.commit()
        return session

    def delete(self, id: int) -> bool:
        """删除会话"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM chat_session WHERE id = ?", (id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def update_title(self, id: int, title: str) -> bool:
        """更新会话标题"""
        cursor = persistent_db.connection.execute(
            "UPDATE chat_session SET title=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, id)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0


class ChatMessageRepository:
    """聊天消息仓库"""

    def find_by_session(self, session_id: int) -> List[ChatMessage]:
        """获取会话的所有消息"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM chat_message WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        )
        return [ChatMessage.from_row(row) for row in cursor.fetchall()]

    def save(self, message: ChatMessage) -> ChatMessage:
        """
        保存消息

        注意：此方法仅支持插入新消息。如需更新现有消息，请使用 update() 方法。

        Raises:
            ValueError: 当尝试保存已有 id 的消息时
        """
        if message.id is not None:
            raise ValueError(
                f"ChatMessage.save() 仅支持插入新消息。"
                f"消息已有 id={message.id}，如需更新请使用 update() 方法。"
            )

        cursor = persistent_db.connection.execute(
            """
            INSERT INTO chat_message (session_id, role, content)
            VALUES (?, ?, ?)
            """,
            (message.session_id, message.role, message.content)
        )
        message.id = cursor.lastrowid
        # 更新会话时间
        persistent_db.connection.execute(
            "UPDATE chat_session SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (message.session_id,)
        )
        persistent_db.connection.commit()
        return message

    def update_content(self, id: int, content: str) -> bool:
        """更新消息内容"""
        cursor = persistent_db.connection.execute(
            "UPDATE chat_message SET content=? WHERE id=?",
            (content, id)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def delete_by_session(self, session_id: int) -> int:
        """删除会话的所有消息"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM chat_message WHERE session_id = ?", (session_id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount

    def count_by_session(self, session_id: int) -> int:
        """统计会话消息数量"""
        cursor = persistent_db.connection.execute(
            "SELECT COUNT(*) FROM chat_message WHERE session_id = ?", (session_id,)
        )
        return cursor.fetchone()[0]
