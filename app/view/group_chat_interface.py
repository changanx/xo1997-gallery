"""
群聊界面
"""
import json
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QThread, Slot, QTimer, QEvent, QPoint
from PySide6.QtGui import QTextCursor, QAction, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,
    QScrollArea, QFileDialog, QListWidgetItem
)

from app.ui import (
    ScrollArea, TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel,
    PrimaryPushButton, PushButton, TransparentToolButton, ToolButton,
    InfoBar, InfoBarPosition, LineEdit, TextEdit, ComboBox,
    FluentIcon as FIF, CardWidget, SimpleCardWidget, MessageBox
)
from app.ui.components.widgets.menu import RoundMenu, MenuAnimationType
from app.ui.components.widgets.line_edit import IndicatorMenuItemDelegate

from ..components.group_chat_message_widget import GroupChatMessageWidget
from ..components.participant_edit_dialog import ParticipantEditDialog
from ..common.logger import logger
from core.group_chat_manager import group_chat_manager, ROLE_TEMPLATES
from core.tts_service import tts_service
from data.models.group_chat import GroupChatSession, GroupChatParticipant, GroupChatMessage
from data.repositories.ai_config_repository import AIModelConfigRepository


class GroupChatWorker(QThread):
    """群聊工作线程"""

    messageReceived = Signal(str, str)  # (type, json_data)
    finished = Signal()
    error = Signal(str)

    def __init__(self, user_message: str, mentioned_participant_ids: List[int] = None, parent=None):
        super().__init__(parent)
        self._user_message = user_message
        self._mentioned_participant_ids = mentioned_participant_ids
        self._is_stopped = False

    def run(self):
        """执行群聊"""
        try:
            for chunk in group_chat_manager.chat(self._user_message, self._mentioned_participant_ids):
                if self._is_stopped:
                    break
                chunk_type = chunk.get("type", "content")
                self.messageReceived.emit(chunk_type, json.dumps(chunk, ensure_ascii=False))
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """停止"""
        self._is_stopped = True


class GroupChatInterface(ScrollArea):
    """群聊界面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("初始化群聊界面...")
        self._model_config_repo = AIModelConfigRepository()
        self._current_session: Optional[GroupChatSession] = None
        self._worker: Optional[GroupChatWorker] = None
        self._current_participant_id: Optional[int] = None  # 当前正在响应的参与者
        self._participant_widgets: Dict[int, GroupChatMessageWidget] = {}  # participant_id -> widget
        self._sessions: List[GroupChatSession] = []
        self._mention_popup: Optional[RoundMenu] = None  # @ 提及弹出菜单
        self._mention_start_pos: int = -1  # @ 符号在文本中的位置

        self._initUI()
        self._loadSessions()
        self._refreshParticipantsUI()

        # 连接 TTS 信号
        tts_service.playback_finished.connect(self._onTTSFinished)
        tts_service.playback_error.connect(self._onTTSError)

        logger.info("群聊界面初始化完成")

    def _initUI(self):
        """初始化 UI"""
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        # 顶部工具栏
        toolbarLayout = QHBoxLayout()

        self.titleLabel = TitleLabel("群聊", self)

        # 会话历史选择
        self.sessionCombo = ComboBox(self)
        self.sessionCombo.setFixedWidth(150)
        self.sessionCombo.currentIndexChanged.connect(self._onSessionChanged)

        # 最大轮次
        self.roundsLabel = BodyLabel("最大轮次:", self)
        self.roundsSpin = ComboBox(self)
        self.roundsSpin.addItems(["1", "2", "3", "4", "5"])
        self.roundsSpin.setCurrentIndex(2)  # 默认 3
        self.roundsSpin.setFixedWidth(60)
        self.roundsSpin.currentIndexChanged.connect(self._onRoundsChanged)

        # 工作目录
        self.workDirBtn = PushButton(FIF.FOLDER, "工作目录", self)
        self.workDirBtn.setFixedWidth(100)
        self.workDirBtn.clicked.connect(self._selectWorkDirectory)

        self.workDirLabel = BodyLabel("未设置", self)
        self.workDirLabel.setStyleSheet("color: #888;")

        # 新建/清空
        self.newChatBtn = TransparentToolButton(FIF.ADD, self)
        self.newChatBtn.setToolTip("新建群聊")
        self.newChatBtn.clicked.connect(self._newSession)

        self.clearBtn = TransparentToolButton(FIF.DELETE, self)
        self.clearBtn.setToolTip("删除会话")
        self.clearBtn.clicked.connect(self._deleteSession)

        toolbarLayout.addWidget(self.titleLabel)
        toolbarLayout.addWidget(self.sessionCombo)
        toolbarLayout.addStretch()
        toolbarLayout.addWidget(self.roundsLabel)
        toolbarLayout.addWidget(self.roundsSpin)
        toolbarLayout.addWidget(self.workDirBtn)
        toolbarLayout.addWidget(self.workDirLabel)
        toolbarLayout.addWidget(self.newChatBtn)
        toolbarLayout.addWidget(self.clearBtn)

        # 参与者区域
        participantsCard = SimpleCardWidget(self)
        participantsLayout = QVBoxLayout(participantsCard)
        participantsLayout.setContentsMargins(12, 8, 12, 8)
        participantsLayout.setSpacing(8)

        # 参与者标题行
        participantHeader = QHBoxLayout()
        participantHeader.addWidget(BodyLabel("参与模型:", self))
        participantHeader.addStretch()

        self.addParticipantBtn = PushButton(FIF.ADD, "添加", self)
        self.addParticipantBtn.setFixedWidth(80)
        self.addParticipantBtn.clicked.connect(self._addParticipant)
        participantHeader.addWidget(self.addParticipantBtn)

        participantsLayout.addLayout(participantHeader)

        # 参与者标签区域
        self.participantsWidget = QWidget(self)
        self.participantsLayout = QHBoxLayout(self.participantsWidget)
        self.participantsLayout.setContentsMargins(0, 0, 0, 0)
        self.participantsLayout.setSpacing(8)
        self.participantsLayout.addStretch()

        participantsLayout.addWidget(self.participantsWidget)

        # 消息滚动区域
        self.scrollArea = ScrollArea(self)
        self.scrollWidget = QWidget(self)
        self.scrollLayout = QVBoxLayout(self.scrollWidget)
        self.scrollLayout.setAlignment(Qt.AlignTop)
        self.scrollLayout.setSpacing(16)
        self.scrollLayout.setContentsMargins(16, 16, 16, 16)

        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._message_widgets = []
        self._empty_shown = True

        # 空状态提示
        self.emptyLabel = BodyLabel(
            "欢迎使用群聊模式！\n\n"
            "1. 添加参与的 AI 模型\n"
            "2. 为每个模型设置角色描述\n"
            "3. 发送消息，@特定模型让其回复\n"
            "4. 模型会接力讨论，直到达成共识或达到最大轮次",
            self.scrollWidget
        )
        self.emptyLabel.setAlignment(Qt.AlignCenter)
        self.emptyLabel.setStyleSheet("color: #999; padding: 40px;")
        self.scrollLayout.addWidget(self.emptyLabel)
        self.scrollLayout.addStretch()

        # 输入区域
        inputCard = SimpleCardWidget(self)
        inputLayout = QHBoxLayout(inputCard)
        inputLayout.setContentsMargins(16, 12, 16, 12)
        inputLayout.setSpacing(12)

        self.inputEdit = TextEdit(self)
        self.inputEdit.setPlaceholderText("输入消息... (@昵称 提及特定模型，不提及则全部回复)")
        self.inputEdit.setFixedHeight(80)
        self.inputEdit.installEventFilter(self)
        self.inputEdit.textChanged.connect(self._onInputTextChanged)

        self.sendBtn = PrimaryPushButton(FIF.SEND, "发送", self)
        self.sendBtn.setFixedWidth(80)
        self.sendBtn.clicked.connect(self._sendMessage)

        self.stopBtn = PushButton("停止", self)
        self.stopBtn.setFixedWidth(80)
        self.stopBtn.setVisible(False)
        self.stopBtn.clicked.connect(self._stopGeneration)

        inputLayout.addWidget(self.inputEdit, 1)
        inputLayout.addWidget(self.sendBtn)
        inputLayout.addWidget(self.stopBtn)

        # 布局
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.addLayout(toolbarLayout)
        self.vBoxLayout.addWidget(participantsCard)
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addWidget(inputCard)

        # 滚动设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.setObjectName('groupChatInterface')
        self.view.setObjectName('view')

    def eventFilter(self, obj, event):
        """事件过滤器"""
        if not (hasattr(self, 'inputEdit') and obj == self.inputEdit):
            return super().eventFilter(obj, event)

        if event.type() == QEvent.KeyPress:
            # 弹出菜单可见时的键盘导航
            if self._mention_popup and self._mention_popup.isVisible():
                if event.key() == Qt.Key_Escape:
                    self._mention_popup.close()
                    return True
                if event.key() in (Qt.Key_Up, Qt.Key_Down):
                    # 让菜单处理上下键导航
                    return False
                if event.key() in (Qt.Key_Enter, Qt.Key_Return):
                    # 选择当前项
                    current_item = self._mention_popup.view.currentItem()
                    if current_item:
                        self._onMentionSelected(current_item.text())
                        self._mention_popup.close()
                    return True
                if event.key() == Qt.Key_Space:
                    # 空格关闭菜单
                    self._mention_popup.close()
                    return False

            # 原有的 Enter 发送逻辑（弹出菜单不可见时）
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                if not (self._mention_popup and self._mention_popup.isVisible()):
                    self._sendMessage()
                    return True

        return super().eventFilter(obj, event)

    def _selectWorkDirectory(self):
        """选择工作目录"""
        from pathlib import Path
        current_dir = group_chat_manager.has_tools() and group_chat_manager._security_context
        if current_dir:
            current_dir = str(group_chat_manager._security_context.work_directory)
        else:
            current_dir = str(Path.home())

        directory = QFileDialog.getExistingDirectory(
            self,
            "选择工作目录",
            current_dir
        )
        if directory:
            group_chat_manager.set_work_directory(directory)
            display_path = directory
            if len(directory) > 30:
                display_path = "..." + directory[-27:]
            self.workDirLabel.setText(display_path)
            self.workDirLabel.setStyleSheet("color: #1976d2;")

            InfoBar.success(
                title="工作目录已设置",
                content=directory,
                parent=self
            )

    def _onRoundsChanged(self, index: int):
        """最大轮次改变"""
        if self._current_session:
            self._current_session.max_discussion_rounds = index + 1
            from data.repositories.group_chat_repository import GroupChatSessionRepository
            repo = GroupChatSessionRepository()
            repo.save(self._current_session)

    def _loadSessions(self):
        """加载会话历史"""
        self._sessions = group_chat_manager.get_all_sessions()
        self.sessionCombo.blockSignals(True)
        self.sessionCombo.clear()

        if not self._sessions:
            # 没有会话，创建新的
            self._newSession()
            return

        for session in self._sessions:
            self.sessionCombo.addItem(session.title)

        # 选择最新的会话
        self.sessionCombo.setCurrentIndex(0)
        self.sessionCombo.blockSignals(False)
        self._switchToSession(self._sessions[0].id)

    def _onSessionChanged(self, index: int):
        """会话切换"""
        if index < 0 or index >= len(self._sessions):
            return
        self._switchToSession(self._sessions[index].id)

    def _switchToSession(self, session_id: int):
        """切换到指定会话"""
        group_chat_manager.set_current_session(session_id)
        self._current_session = group_chat_manager.get_session(session_id)

        # 更新轮次选择
        if self._current_session:
            self.roundsSpin.setCurrentIndex(self._current_session.max_discussion_rounds - 1)

        # 加载历史消息
        self._loadHistoryMessages()
        # 刷新参与者 UI（参与者是全局的，不需要切换）
        self._refreshParticipantsUI()

    def _loadHistoryMessages(self):
        """加载历史消息"""
        self._clearMessages(keep_db=True)

        if not self._current_session:
            return

        messages = group_chat_manager.get_messages(self._current_session.id)
        participants = {p.id: p for p in group_chat_manager.get_participants()}

        for msg in messages:
            if msg.role == "user":
                self._addMessage("user", msg.content)
            elif msg.role == "assistant":
                participant = participants.get(msg.participant_id)
                if participant:
                    self._addMessage("assistant", msg.content, {
                        "id": participant.id,
                        "nickname": participant.nickname,
                        "avatar": participant.avatar
                    })

    def _newSession(self):
        """新建群聊会话"""
        max_rounds = int(self.roundsSpin.currentText())
        self._current_session = group_chat_manager.create_session(
            title=f"群聊 {datetime.now().strftime('%H:%M')}",
            max_rounds=max_rounds
        )
        group_chat_manager.set_current_session(self._current_session.id)

        # 刷新会话列表
        self._sessions.insert(0, self._current_session)
        self.sessionCombo.blockSignals(True)
        self.sessionCombo.insertItem(0, self._current_session.title)
        self.sessionCombo.setCurrentIndex(0)
        self.sessionCombo.blockSignals(False)

        self._clearMessages()
        self._refreshParticipantsUI()

    def _deleteSession(self):
        """删除当前会话"""
        if not self._current_session:
            return

        # 确认弹窗
        msg = MessageBox(
            "确认删除",
            f"确定要删除会话「{self._current_session.title}」吗？\n此操作不可恢复。",
            self
        )
        msg.yesButton.setText("删除")
        msg.cancelButton.setText("取消")

        if msg.exec():
            session_id = self._current_session.id

            # 从数据库删除
            group_chat_manager.delete_session(session_id)

            # 从列表中移除
            self._sessions = [s for s in self._sessions if s.id != session_id]

            # 更新下拉框
            self.sessionCombo.blockSignals(True)
            current_index = self.sessionCombo.currentIndex()
            self.sessionCombo.removeItem(current_index)
            self.sessionCombo.blockSignals(False)

            # 切换到其他会话或创建新会话
            if self._sessions:
                self.sessionCombo.setCurrentIndex(0)
                self._switchToSession(self._sessions[0].id)
            else:
                self._newSession()

            InfoBar.success(
                title="删除成功",
                content="会话已删除",
                parent=self
            )

    def _clearMessages(self, keep_db: bool = False):
        """清空消息"""
        for widget in self._message_widgets:
            widget.deleteLater()
        self._message_widgets.clear()
        self._participant_widgets.clear()
        self.emptyLabel.show()
        self._empty_shown = True

        if self._current_session and not keep_db:
            group_chat_manager.clear_messages(self._current_session.id)

    def _refreshParticipantsUI(self):
        """刷新参与者 UI（全局参与者）"""
        # 清空现有
        while self.participantsLayout.count() > 1:
            item = self.participantsLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        participants = group_chat_manager.get_participants()

        for p in participants:
            # 参与者卡片
            card = self._createParticipantCard(p)
            self.participantsLayout.insertWidget(self.participantsLayout.count() - 1, card)

    def _createParticipantCard(self, participant: GroupChatParticipant) -> QWidget:
        """创建参与者卡片"""
        card = SimpleCardWidget(self)
        card.setFixedHeight(80)
        card.setFixedWidth(140)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        # 获取模型名称
        config = self._model_config_repo.find_by_id(participant.model_config_id)
        model_name = config.name if config else "未知"

        # 顶部：头像 + 昵称
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(4)

        # 头像（emoji）
        avatar_emoji = self._get_avatar_emoji(participant.avatar)
        avatar_label = BodyLabel(avatar_emoji, card)
        headerLayout.addWidget(avatar_label)

        # 昵称
        nickname_label = BodyLabel(participant.nickname, card)
        nickname_label.setStyleSheet("color: #1976d2; font-weight: bold;")
        headerLayout.addWidget(nickname_label, 1)

        layout.addLayout(headerLayout)

        # 模型名
        model_label = CaptionLabel(model_name, card)
        model_label.setStyleSheet("color: #666;")
        layout.addWidget(model_label)

        # 角色描述（截取）
        role = participant.role_description[:20] + "..." if len(participant.role_description) > 20 else participant.role_description
        role_label = CaptionLabel(role or "无角色描述", card)
        role_label.setStyleSheet("color: #888;")
        role_label.setWordWrap(True)
        layout.addWidget(role_label)

        # 编辑/删除按钮
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(4)

        editBtn = TransparentToolButton(FIF.EDIT, card)
        editBtn.setFixedSize(20, 20)
        editBtn.clicked.connect(lambda: self._editParticipant(participant.id))
        btnLayout.addWidget(editBtn)

        removeBtn = TransparentToolButton(FIF.DELETE, card)
        removeBtn.setFixedSize(20, 20)
        removeBtn.clicked.connect(lambda: self._removeParticipant(participant.id))
        btnLayout.addWidget(removeBtn)

        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        return card

    def _addParticipant(self):
        """添加参与者（全局）"""
        dialog = ParticipantEditDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            participant = group_chat_manager.add_participant(
                model_config_id=data["model_config_id"],
                nickname=data["nickname"],
                role_description=data["role_description"],
                avatar=data.get("avatar", "ROBOT")
            )
            if participant:
                self._refreshParticipantsUI()
                InfoBar.success(
                    title="添加成功",
                    content=f"已添加 {participant.nickname}",
                    parent=self
                )

    def _editParticipant(self, participant_id: int):
        """编辑参与者"""
        participant = group_chat_manager.get_participant(participant_id)

        if not participant:
            return

        dialog = ParticipantEditDialog(self, participant=participant)
        if dialog.exec():
            data = dialog.get_data()
            updated = group_chat_manager.update_participant(
                participant_id=participant_id,
                nickname=data["nickname"],
                role_description=data["role_description"],
                avatar=data.get("avatar"),
                fish_audio_voice_id=data.get("fish_audio_voice_id", "")
            )
            if updated:
                self._refreshParticipantsUI()

    def _removeParticipant(self, participant_id: int):
        """移除参与者"""
        if group_chat_manager.remove_participant(participant_id):
            self._refreshParticipantsUI()

    # ==================== @ 提及弹出菜单 ====================

    def _createMentionPopup(self) -> RoundMenu:
        """创建 @ 提及弹出菜单"""
        menu = RoundMenu("", self)
        menu.setItemHeight(33)
        menu.view.setItemDelegate(IndicatorMenuItemDelegate())
        menu.view.setViewportMargins(0, 2, 0, 6)
        menu.view.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # 减少阴影效果的模糊范围，避免透明边框
        menu.setShadowEffect(blurRadius=15, offset=(0, 4), color=QColor(0, 0, 0, 50))
        return menu

    def _showMentionPopup(self):
        """显示 @ 提及候选列表"""
        try:
            participants = group_chat_manager.get_participants()
            logger.debug(f"_showMentionPopup: participants count={len(participants)}")
            if not participants:
                return

            # 创建或重用弹出菜单
            if not self._mention_popup:
                self._mention_popup = self._createMentionPopup()
                logger.debug("创建了新的 _mention_popup")

            # 记录 @ 符号位置
            cursor = self.inputEdit.textCursor()
            self._mention_start_pos = cursor.position() - 1  # @ 符号的位置
            logger.debug(f"_mention_start_pos={self._mention_start_pos}")

            # 填充参与者列表
            self._mention_popup.clear()
            for p in participants:
                action = QAction(p.nickname, self)
                action.triggered.connect(lambda checked, nick=p.nickname: self._onMentionSelected(nick))
                self._mention_popup.addAction(action)
            logger.debug(f"添加了 {self._mention_popup.view.count()} 个菜单项")

            # 计算弹出位置
            cursor_rect = self.inputEdit.cursorRect(cursor)
            global_pos = self.inputEdit.mapToGlobal(cursor_rect.bottomLeft())
            global_pos.setY(global_pos.y() + 5)  # 稍微向下偏移
            logger.debug(f"弹出位置: {global_pos}")

            # 调整菜单大小
            self._mention_popup.adjustSize()
            if self._mention_popup.width() < 150:
                self._mention_popup.setMinimumWidth(150)

            # 显示菜单
            logger.debug("准备调用 exec 显示菜单")
            self._mention_popup.exec(global_pos, ani=True, aniType=MenuAnimationType.DROP_DOWN)
            logger.debug("exec 调用完成")

            # 设置初始选中项
            if self._mention_popup.view.count() > 0:
                self._mention_popup.view.setCurrentRow(0)
        except Exception as e:
            logger.error(f"_showMentionPopup 异常: {e}", exc_info=True)

    def _filterMentionPopup(self, text: str):
        """根据输入过滤候选列表"""
        if not self._mention_popup or not self._mention_popup.isVisible():
            return

        # 获取 @ 后的文本
        cursor = self.inputEdit.textCursor()
        current_pos = cursor.position()

        if self._mention_start_pos < 0 or current_pos <= self._mention_start_pos:
            # 光标移动到 @ 之前，关闭菜单
            self._mention_popup.close()
            return

        # 提取 @ 后的文本作为过滤条件
        filter_text = text[self._mention_start_pos + 1:current_pos].lower()

        participants = group_chat_manager.get_participants()

        # 重新填充过滤后的列表
        self._mention_popup.clear()
        for p in participants:
            nick = p.nickname.lstrip('@').lower()
            if filter_text in nick:
                action = QAction(p.nickname, self)
                action.triggered.connect(lambda checked, nick=p.nickname: self._onMentionSelected(nick))
                self._mention_popup.addAction(action)

        # 如果没有匹配项，关闭菜单
        if self._mention_popup.view.count() == 0:
            self._mention_popup.close()
        else:
            self._mention_popup.view.setCurrentRow(0)

    def _onMentionSelected(self, nickname: str):
        """选择提及后的处理"""
        cursor = self.inputEdit.textCursor()
        current_pos = cursor.position()

        # 选中从 @ 到当前位置的文本
        cursor.setPosition(self._mention_start_pos, QTextCursor.MoveAnchor)
        cursor.setPosition(current_pos, QTextCursor.KeepAnchor)

        # 替换为完整昵称（确保以 @ 开头）
        if not nickname.startswith('@'):
            nickname = '@' + nickname

        cursor.insertText(nickname + ' ')  # 添加空格分隔

        # 关闭菜单
        if self._mention_popup:
            self._mention_popup.close()

        # 重置状态
        self._mention_start_pos = -1

    def _onInputTextChanged(self):
        """输入文本变化时的处理"""
        text = self.inputEdit.toPlainText()
        cursor = self.inputEdit.textCursor()
        current_pos = cursor.position()

        logger.debug(f"_onInputTextChanged: text='{text}', pos={current_pos}")

        # 检查是否需要显示或过滤 @ 提及菜单
        if self._mention_popup and self._mention_popup.isVisible():
            # 检查光标是否还在 @ 提示范围内
            if self._mention_start_pos >= 0 and current_pos > self._mention_start_pos:
                self._filterMentionPopup(text)
            else:
                self._mention_popup.close()
                self._mention_start_pos = -1
        else:
            # 检测新输入的 @ 符号
            if current_pos > 0 and len(text) >= current_pos and text[current_pos - 1] == '@':
                # 检查 @ 是否在单词边界（前面是空格或行首）
                if current_pos == 1 or text[current_pos - 2] in (' ', '\n'):
                    logger.debug(f"检测到 @ 输入，准备显示弹出菜单")
                    QTimer.singleShot(0, self._showMentionPopup)

    def _scrollToBottom(self):
        """滚动到底部"""
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        ))

    def _addMessage(self, role: str, content: str, model_info: Dict = None):
        """添加消息"""
        if self._empty_shown:
            self.emptyLabel.hide()
            self._empty_shown = False

        widget = GroupChatMessageWidget(role, content, model_info, self.scrollWidget)
        self._message_widgets.append(widget)
        self.scrollLayout.insertWidget(self.scrollLayout.count() - 1, widget)
        self._scrollToBottom()
        return widget

    def _sendMessage(self):
        """发送消息"""
        content = self.inputEdit.toPlainText().strip()
        if not content:
            return

        participants = group_chat_manager.get_participants()
        if not participants:
            InfoBar.warning(
                title="提示",
                content="请先添加参与模型",
                parent=self
            )
            return

        # 解析 @ 提及（从文本中解析）
        mentioned_ids = group_chat_manager.parse_mentions(content, participants)

        # 添加用户消息
        self._addMessage("user", content)

        # 清空输入
        self.inputEdit.clear()

        # 启动工作线程
        self._worker = GroupChatWorker(content, mentioned_ids, parent=self)
        self._worker.messageReceived.connect(self._onMessageReceived)
        self._worker.finished.connect(self._onFinished)
        self._worker.error.connect(self._onError)

        # UI 状态
        self.sendBtn.setVisible(False)
        self.stopBtn.setVisible(True)
        self.inputEdit.setEnabled(False)
        self._participant_widgets.clear()

        self._worker.start()

    @Slot(str, str)
    def _onMessageReceived(self, msg_type: str, data: str):
        """收到消息"""
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            logger.warning(f"群聊消息解析失败: {data[:100]}")
            return

        logger.debug(f"群聊收到消息: type={msg_type}, chunk={chunk}")

        if msg_type == "model_response_start":
            participant_id = chunk.get("participant_id")
            nickname = chunk.get("nickname", "AI")
            avatar = chunk.get("avatar", "ROBOT")
            fish_audio_voice_id = chunk.get("fish_audio_voice_id", "")

            # 创建新的消息 widget
            widget = self._addMessage("assistant", "", {
                "id": participant_id,
                "nickname": nickname,
                "avatar": avatar,
                "fish_audio_voice_id": fish_audio_voice_id
            })
            self._participant_widgets[participant_id] = widget
            self._current_participant_id = participant_id

        elif msg_type == "content":
            participant_id = chunk.get("participant_id", self._current_participant_id)
            text = chunk.get("text", "")
            logger.debug(f"content消息: participant_id={participant_id}, text={text[:50] if text else 'empty'}")
            if participant_id in self._participant_widgets:
                self._participant_widgets[participant_id].appendContent(text)
            else:
                logger.warning(f"未找到 participant_id={participant_id} 的 widget")

        elif msg_type == "model_response_complete":
            # 模型响应完成，设置完整内容
            participant_id = chunk.get("participant_id")
            content = chunk.get("content", "")
            if participant_id in self._participant_widgets:
                widget = self._participant_widgets[participant_id]
                widget.setContent(content)

                # 尝试自动播放 TTS
                self._tryAutoPlayTTS(widget)

        elif msg_type == "thinking":
            participant_id = chunk.get("participant_id", self._current_participant_id)
            text = chunk.get("text", "")
            if participant_id in self._participant_widgets:
                self._participant_widgets[participant_id].appendThinking(text)

        elif msg_type == "round_start":
            round_num = chunk.get("round", 0)
            # 显示轮次提示
            self._addMessage("user", f"--- 第 {round_num} 轮讨论 ---", None)

        elif msg_type == "discussion_end":
            self._addMessage("user", "--- 讨论结束 ---", None)

        self._scrollToBottom()

    @Slot()
    def _onFinished(self):
        """完成"""
        self._resetUI()

    @Slot(str)
    def _onError(self, error: str):
        """错误"""
        logger.error(f"群聊错误: {error}")
        InfoBar.error(
            title="错误",
            content=error,
            duration=5000,
            parent=self
        )
        self._resetUI()

    def _stopGeneration(self):
        """停止生成"""
        if self._worker:
            self._worker.stop()
        self._resetUI()

    def _resetUI(self):
        """重置 UI"""
        self.sendBtn.setVisible(True)
        self.stopBtn.setVisible(False)
        self.inputEdit.setEnabled(True)
        self._worker = None
        self._current_participant_id = None

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

    def _tryAutoPlayTTS(self, widget: GroupChatMessageWidget):
        """尝试自动播放 TTS"""
        # 获取主窗口来访问通用设置
        from PySide6.QtWidgets import QApplication
        main_window = QApplication.instance().activeWindow()
        if not main_window:
            # 尝试从父窗口链获取
            parent = self.parent()
            while parent:
                if hasattr(parent, 'generalSettingsInterface'):
                    main_window = parent
                    break
                parent = parent.parent()

        if main_window and hasattr(main_window, 'generalSettingsInterface'):
            settings = main_window.generalSettingsInterface
            if settings.get_auto_play_tts():
                voice_id = widget.get_model_info().get("fish_audio_voice_id")
                if voice_id:
                    participant_id = widget.get_model_info().get("id")
                    tts_service.play(widget.get_content(), voice_id, participant_id)

    @Slot(int)
    def _onTTSFinished(self, participant_id: int):
        """TTS 播放完成"""
        if participant_id in self._participant_widgets:
            self._participant_widgets[participant_id].set_playing_state(False)

    @Slot(int, str)
    def _onTTSError(self, participant_id: int, error_msg: str):
        """TTS 播放错误"""
        if participant_id in self._participant_widgets:
            self._participant_widgets[participant_id].set_playing_state(False)

        InfoBar.warning(
            title="语音播放失败",
            content=error_msg,
            duration=3000,
            parent=self
        )
