"""
群聊数据仓库
"""
import json
from typing import List, Optional

from ..database import persistent_db
from ..models.group_chat import GroupChatSession, GroupChatParticipant, GroupChatMessage


class GroupChatSessionRepository:
    """群聊会话仓库"""

    def find_all(self, limit: int = 50) -> List[GroupChatSession]:
        """获取所有群聊会话"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_session ORDER BY updated_at DESC LIMIT ?", (limit,)
        )
        return [GroupChatSession.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[GroupChatSession]:
        """根据 ID 查找"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_session WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return GroupChatSession.from_row(row) if row else None

    def save(self, session: GroupChatSession) -> GroupChatSession:
        """保存群聊会话"""
        if session.id is None:
            cursor = persistent_db.connection.execute(
                """
                INSERT INTO group_chat_session (title, max_discussion_rounds)
                VALUES (?, ?)
                """,
                (session.title, session.max_discussion_rounds)
            )
            session.id = cursor.lastrowid
        else:
            persistent_db.connection.execute(
                """
                UPDATE group_chat_session SET title=?, max_discussion_rounds=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (session.title, session.max_discussion_rounds, session.id)
            )
        persistent_db.connection.commit()
        return session

    def delete(self, id: int) -> bool:
        """删除群聊会话"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM group_chat_session WHERE id = ?", (id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def update_title(self, id: int, title: str) -> bool:
        """更新会话标题"""
        cursor = persistent_db.connection.execute(
            "UPDATE group_chat_session SET title=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (title, id)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        """统计会话数量"""
        cursor = persistent_db.connection.execute("SELECT COUNT(*) FROM group_chat_session")
        return cursor.fetchone()[0]


class GroupChatParticipantRepository:
    """群聊参与者仓库"""

    def find_by_session(self, session_id: int) -> List[GroupChatParticipant]:
        """获取会话的所有参与者"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_participant WHERE session_id = ? ORDER BY joined_at ASC",
            (session_id,)
        )
        return [GroupChatParticipant.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[GroupChatParticipant]:
        """根据 ID 查找"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_participant WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return GroupChatParticipant.from_row(row) if row else None

    def find_by_session_and_model(self, session_id: int, model_config_id: int) -> Optional[GroupChatParticipant]:
        """根据会话和模型查找参与者"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_participant WHERE session_id = ? AND model_config_id = ?",
            (session_id, model_config_id)
        )
        row = cursor.fetchone()
        return GroupChatParticipant.from_row(row) if row else None

    def save(self, participant: GroupChatParticipant) -> GroupChatParticipant:
        """保存参与者"""
        if participant.id is None:
            cursor = persistent_db.connection.execute(
                """
                INSERT INTO group_chat_participant (session_id, model_config_id, nickname, role_description)
                VALUES (?, ?, ?, ?)
                """,
                (participant.session_id, participant.model_config_id,
                 participant.nickname, participant.role_description)
            )
            participant.id = cursor.lastrowid
            # 更新会话时间
            persistent_db.connection.execute(
                "UPDATE group_chat_session SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
                (participant.session_id,)
            )
        else:
            persistent_db.connection.execute(
                """
                UPDATE group_chat_participant SET nickname=?, role_description=?
                WHERE id=?
                """,
                (participant.nickname, participant.role_description, participant.id)
            )
        persistent_db.connection.commit()
        return participant

    def delete(self, id: int) -> bool:
        """删除参与者"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM group_chat_participant WHERE id = ?", (id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def delete_by_session(self, session_id: int) -> int:
        """删除会话的所有参与者"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM group_chat_participant WHERE session_id = ?", (session_id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount

    def count_by_session(self, session_id: int) -> int:
        """统计会话参与者数量"""
        cursor = persistent_db.connection.execute(
            "SELECT COUNT(*) FROM group_chat_participant WHERE session_id = ?", (session_id,)
        )
        return cursor.fetchone()[0]


class GroupChatMessageRepository:
    """群聊消息仓库"""

    def find_by_session(self, session_id: int) -> List[GroupChatMessage]:
        """获取会话的所有消息"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_message WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,)
        )
        return [GroupChatMessage.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[GroupChatMessage]:
        """根据 ID 查找"""
        cursor = persistent_db.connection.execute(
            "SELECT * FROM group_chat_message WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return GroupChatMessage.from_row(row) if row else None

    def find_latest_round(self, session_id: int) -> int:
        """获取会话最新的讨论轮次"""
        cursor = persistent_db.connection.execute(
            "SELECT MAX(discussion_round) FROM group_chat_message WHERE session_id = ?",
            (session_id,)
        )
        result = cursor.fetchone()[0]
        return result if result else 0

    def save(self, message: GroupChatMessage) -> GroupChatMessage:
        """
        保存消息

        注意：此方法仅支持插入新消息。如需更新现有消息，请使用 update() 方法。

        Raises:
            ValueError: 当尝试保存已有 id 的消息时
        """
        if message.id is not None:
            raise ValueError(
                f"GroupChatMessage.save() 仅支持插入新消息。"
                f"消息已有 id={message.id}，如需更新请使用 update() 方法。"
            )

        mentioned_models_json = json.dumps(message.mentioned_models) if message.mentioned_models else None

        cursor = persistent_db.connection.execute(
            """
            INSERT INTO group_chat_message (session_id, role, model_config_id, content,
                mentioned_models, discussion_round)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (message.session_id, message.role, message.model_config_id,
             message.content, mentioned_models_json, message.discussion_round)
        )
        message.id = cursor.lastrowid
        # 更新会话时间
        persistent_db.connection.execute(
            "UPDATE group_chat_session SET updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (message.session_id,)
        )
        persistent_db.connection.commit()
        return message

    def update_content(self, id: int, content: str) -> bool:
        """更新消息内容"""
        cursor = persistent_db.connection.execute(
            "UPDATE group_chat_message SET content=? WHERE id=?",
            (content, id)
        )
        persistent_db.connection.commit()
        return cursor.rowcount > 0

    def delete_by_session(self, session_id: int) -> int:
        """删除会话的所有消息"""
        cursor = persistent_db.connection.execute(
            "DELETE FROM group_chat_message WHERE session_id = ?", (session_id,)
        )
        persistent_db.connection.commit()
        return cursor.rowcount

    def count_by_session(self, session_id: int) -> int:
        """统计会话消息数量"""
        cursor = persistent_db.connection.execute(
            "SELECT COUNT(*) FROM group_chat_message WHERE session_id = ?", (session_id,)
        )
        return cursor.fetchone()[0]
