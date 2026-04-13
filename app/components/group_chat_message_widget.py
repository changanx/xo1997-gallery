"""
群聊消息组件
"""
import json
from typing import Optional, Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from app.ui import (
    SimpleCardWidget, BodyLabel, CaptionLabel, TextEdit,
    FluentIcon as FIF, TransparentToolButton, AvatarWidget
)


class GroupChatMessageWidget(QWidget):
    """群聊消息组件"""

    def __init__(self, role: str, content: str, model_info: Dict = None, parent=None):
        """
        Args:
            role: "user" 或 "assistant"
            content: 消息内容
            model_info: {"id": int, "name": str, "nickname": str, "avatar": str}
        """
        super().__init__(parent)
        self._role = role
        self._content = content
        self._model_info = model_info or {}
        self._thinking = ""
        self._tool_calls = []

        self._initUI()

    def _initUI(self):
        """初始化 UI"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(12)

        is_user = self._role == "user"

        if is_user:
            mainLayout.addStretch()

        # 消息区域
        messageLayout = QVBoxLayout()
        messageLayout.setSpacing(4)

        # 顶部：昵称 + 时间
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(8)

        if not is_user and self._model_info:
            # AI 模型头像
            nickname = self._model_info.get("nickname", "AI")
            avatar = self._model_info.get("avatar", "ROBOT")
            avatar_emoji = self._get_avatar_emoji(avatar)
            icon_label = BodyLabel(avatar_emoji, self)
            headerLayout.addWidget(icon_label)

            # 昵称
            nickname_label = CaptionLabel(nickname, self)
            nickname_label.setStyleSheet("color: #1976d2; font-weight: bold;")
            headerLayout.addWidget(nickname_label)
        else:
            # 用户图标
            user_icon = BodyLabel("👤", self)
            headerLayout.addWidget(user_icon)

            user_label = CaptionLabel("你", self)
            user_label.setStyleSheet("color: #888; font-weight: bold;")
            headerLayout.addWidget(user_label)

        headerLayout.addStretch()

        # 卡片容器
        cardLayout = QVBoxLayout()
        cardLayout.setSpacing(4)

        # 思考过程（仅 AI 消息）
        if not is_user:
            self.thinkingLabel = TextEdit(self)
            self.thinkingLabel.setPlaceholderText("思考中...")
            self.thinkingLabel.setReadOnly(True)
            self.thinkingLabel.setVisible(False)
            self.thinkingLabel.document().documentLayout().documentSizeChanged.connect(
                self._updateThinkingHeight
            )
            self.thinkingLabel.setStyleSheet("""
                TextEdit {
                    background-color: #fff8e1;
                    border: 1px solid #ffecb3;
                    border-radius: 8px;
                    padding: 8px;
                    color: #666;
                    font-style: italic;
                }
            """)
            cardLayout.addWidget(self.thinkingLabel)

            # 工具调用区域
            self.toolCallsWidget = QWidget(self)
            self.toolCallsLayout = QVBoxLayout(self.toolCallsWidget)
            self.toolCallsLayout.setContentsMargins(0, 0, 0, 0)
            self.toolCallsLayout.setSpacing(4)
            self.toolCallsWidget.setVisible(False)
            cardLayout.addWidget(self.toolCallsWidget)

        # 消息内容
        self.contentLabel = TextEdit(self)
        self.contentLabel.setPlainText(self._content)
        self.contentLabel.setReadOnly(True)
        self.contentLabel.document().documentLayout().documentSizeChanged.connect(
            self._updateHeight
        )
        self._updateHeight()

        # 根据角色设置样式
        if is_user:
            self.contentLabel.setStyleSheet("""
                TextEdit {
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
        else:
            self.contentLabel.setStyleSheet("""
                TextEdit {
                    background-color: #f5f5f5;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)

        cardLayout.addWidget(self.contentLabel)

        # 底部：复制按钮
        footerLayout = QHBoxLayout()
        footerLayout.addStretch()

        copyBtn = TransparentToolButton(FIF.COPY, self)
        copyBtn.setFixedSize(24, 24)
        copyBtn.clicked.connect(self._copyContent)
        footerLayout.addWidget(copyBtn)

        cardLayout.addLayout(footerLayout)

        # 组装
        messageLayout.addLayout(headerLayout)
        messageLayout.addLayout(cardLayout)

        mainLayout.addLayout(messageLayout)

        if not is_user:
            mainLayout.addStretch()

    def _copyContent(self):
        """复制内容"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self._content)

    def _updateHeight(self):
        """更新内容高度"""
        doc_height = self.contentLabel.document().size().height()
        new_height = max(40, min(400, int(doc_height) + 20))
        self.contentLabel.setFixedHeight(new_height)

    def _updateThinkingHeight(self):
        """更新思考过程高度"""
        if hasattr(self, 'thinkingLabel') and self.thinkingLabel.isVisible():
            doc_height = self.thinkingLabel.document().size().height()
            new_height = max(30, min(200, int(doc_height) + 16))
            self.thinkingLabel.setFixedHeight(new_height)

    def appendThinking(self, text: str):
        """追加思考过程"""
        if self._role == "user":
            return
        self._thinking += text
        if hasattr(self, 'thinkingLabel'):
            self.thinkingLabel.setVisible(True)
            self.thinkingLabel.setPlainText(self._thinking)

    def appendContent(self, text: str):
        """追加内容"""
        self._content += text
        self.contentLabel.setPlainText(self._content)

    def setContent(self, text: str):
        """设置内容"""
        self._content = text
        self.contentLabel.setPlainText(self._content)

    def addToolCall(self, name: str, args: dict, tool_id: str = ""):
        """添加工具调用显示"""
        if self._role == "user":
            return

        self.toolCallsWidget.setVisible(True)

        callCard = QWidget(self.toolCallsWidget)
        callLayout = QVBoxLayout(callCard)
        callLayout.setContentsMargins(8, 8, 8, 8)
        callLayout.setSpacing(4)

        nameLabel = CaptionLabel(f"🔧 调用工具: {name}", callCard)
        nameLabel.setStyleSheet("color: #1976d2; font-weight: bold;")
        callLayout.addWidget(nameLabel)

        if args:
            argsLabel = CaptionLabel(f"参数: {json.dumps(args, ensure_ascii=False)}", callCard)
            argsLabel.setStyleSheet("color: #666;")
            argsLabel.setWordWrap(True)
            callLayout.addWidget(argsLabel)

        callCard.setStyleSheet("""
            QWidget {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
                border-radius: 6px;
            }
        """)

        self.toolCallsLayout.addWidget(callCard)

        self._tool_calls.append({
            "name": name,
            "args": args,
            "id": tool_id,
            "result": ""
        })

        callCard._tool_name = name
        callCard._result_label = None
        callCard._call_layout = callLayout

    def addToolResult(self, name: str, result: str):
        """添加工具执行结果"""
        if self._role == "user":
            return

        for tc in self._tool_calls:
            if tc["name"] == name and not tc["result"]:
                tc["result"] = result
                break

        for i in range(self.toolCallsLayout.count()):
            card = self.toolCallsLayout.itemAt(i).widget()
            if hasattr(card, '_tool_name') and card._tool_name == name:
                resultLabel = CaptionLabel(f"✅ 结果: {result[:200]}{'...' if len(result) > 200 else ''}", card)
                resultLabel.setStyleSheet("color: #2e7d32;")
                resultLabel.setWordWrap(True)
                card._call_layout.addWidget(resultLabel)

                card.setStyleSheet("""
                    QWidget {
                        background-color: #e8f5e9;
                        border: 1px solid #a5d6a7;
                        border-radius: 6px;
                    }
                """)
                break

    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return self._model_info

    def _get_avatar_emoji(self, avatar_name: str) -> str:
        """根据头像名称返回 emoji"""
        avatar_map = {
            "ROBOT": "🤖",
            "BRAIN": "🧠",
            "IDEA": "💡",
            "TARGET": "🎯",
            "FLASH": "⚡",
            "FIRE": "🔥",
            "STAR": "⭐",
            "MOON": "🌙",
            "SUN": "☀️",
            "LEAF": "🍀",
            "PALETTE": "🎨",
            "MUSIC": "🎵",
            "BOOK": "📖",
            "GEM": "💎",
            "ROCKET": "🚀",
        }
        return avatar_map.get(avatar_name, "🤖")
