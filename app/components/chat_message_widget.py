"""
聊天消息组件
"""
import json
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy

from qfluentwidgets import (
    SimpleCardWidget, BodyLabel, CaptionLabel, TextEdit,
    FluentIcon as FIF, AvatarWidget, TransparentToolButton
)


class ChatMessageWidget(QWidget):
    """聊天消息组件"""

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self._role = role
        self._content = content
        self._thinking = ""  # 思考过程
        self._tool_calls = []  # 工具调用记录

        self._initUI()

    def _initUI(self):
        """初始化 UI"""
        mainLayout = QHBoxLayout(self)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(12)

        # 用户消息靠右，AI 消息靠左
        is_user = self._role == "user"

        if is_user:
            mainLayout.addStretch()

        # 消息卡片
        cardLayout = QVBoxLayout()
        cardLayout.setSpacing(4)

        # 角色标签
        roleLabel = CaptionLabel("你" if is_user else "AI", self)
        roleLabel.setStyleSheet("color: #888;")
        cardLayout.addWidget(roleLabel)

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

            # 工具调用区域（仅 AI 消息）
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
        # 计算高度，确保最小高度
        self.contentLabel.document().documentLayout().documentSizeChanged.connect(
            self._updateHeight
        )
        self._updateHeight()
        self.contentLabel.setStyleSheet("""
            TextEdit {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        if is_user:
            self.contentLabel.setStyleSheet("""
                TextEdit {
                    background-color: #e3f2fd;
                    border: 1px solid #bbdefb;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)

        cardLayout.addWidget(self.contentLabel)

        # 复制按钮
        copyBtn = TransparentToolButton(FIF.COPY, self)
        copyBtn.setFixedSize(24, 24)
        copyBtn.clicked.connect(self._copyContent)

        btnLayout = QHBoxLayout()
        btnLayout.addStretch()
        btnLayout.addWidget(copyBtn)
        cardLayout.addLayout(btnLayout)

        mainLayout.addLayout(cardLayout)

        if not is_user:
            mainLayout.addStretch()

    def _copyContent(self):
        """复制内容"""
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        # 复制内容包括工具调用
        full_content = self._content
        if self._tool_calls:
            full_content += "\n\n[工具调用记录]\n"
            for tc in self._tool_calls:
                full_content += f"- {tc['name']}({json.dumps(tc['args'], ensure_ascii=False)})\n"
                full_content += f"  结果: {tc['result'][:100]}...\n" if len(tc['result']) > 100 else f"  结果: {tc['result']}\n"
        clipboard.setText(full_content)

    def _updateHeight(self):
        """更新高度"""
        doc_height = self.contentLabel.document().size().height()
        # 最小高度 40，最大高度 300
        new_height = max(40, min(300, int(doc_height) + 20))
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
        """追加内容（用于流式输出）"""
        self._content += text
        self.contentLabel.setPlainText(self._content)
        # 自动调整高度
        doc_height = self.contentLabel.document().size().height() + 30
        self.contentLabel.setFixedHeight(min(300, doc_height))

    def setContent(self, text: str):
        """设置内容"""
        self._content = text
        self.contentLabel.setPlainText(self._content)
        doc_height = self.contentLabel.document().size().height() + 30
        self.contentLabel.setFixedHeight(min(300, doc_height))

    def setThinking(self, text: str):
        """设置思考过程"""
        if self._role == "user":
            return
        self._thinking = text
        if hasattr(self, 'thinkingLabel') and text:
            self.thinkingLabel.setVisible(True)
            self.thinkingLabel.setPlainText(text)

    def addToolCall(self, name: str, args: dict, tool_id: str = ""):
        """添加工具调用显示"""
        if self._role == "user":
            return

        self.toolCallsWidget.setVisible(True)

        # 创建工具调用卡片
        callCard = QWidget(self.toolCallsWidget)
        callLayout = QVBoxLayout(callCard)
        callLayout.setContentsMargins(8, 8, 8, 8)
        callLayout.setSpacing(4)

        # 工具名称
        nameLabel = CaptionLabel(f"🔧 调用工具: {name}", callCard)
        nameLabel.setStyleSheet("color: #1976d2; font-weight: bold;")
        callLayout.addWidget(nameLabel)

        # 参数显示
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

        # 记录工具调用
        self._tool_calls.append({
            "name": name,
            "args": args,
            "id": tool_id,
            "result": ""
        })

        # 保存引用以便更新结果
        callCard._tool_name = name
        callCard._result_label = None
        callCard._call_layout = callLayout

    def addToolResult(self, name: str, result: str):
        """添加工具执行结果"""
        if self._role == "user":
            return

        # 更新工具调用记录
        for tc in self._tool_calls:
            if tc["name"] == name and not tc["result"]:
                tc["result"] = result
                break

        # 找到对应的工具调用卡片并添加结果
        for i in range(self.toolCallsLayout.count()):
            card = self.toolCallsLayout.itemAt(i).widget()
            if hasattr(card, '_tool_name') and card._tool_name == name:
                # 创建结果标签
                resultLabel = CaptionLabel(f"✅ 结果: {result[:200]}{'...' if len(result) > 200 else ''}", card)
                resultLabel.setStyleSheet("color: #2e7d32;")
                resultLabel.setWordWrap(True)
                card._call_layout.addWidget(resultLabel)

                # 改变卡片样式
                card.setStyleSheet("""
                    QWidget {
                        background-color: #e8f5e9;
                        border: 1px solid #a5d6a7;
                        border-radius: 6px;
                    }
                """)
                break
