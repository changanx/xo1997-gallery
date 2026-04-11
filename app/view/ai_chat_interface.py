"""
AI 对话页面
"""
import json
from typing import List, Dict, Optional
from datetime import datetime

from PySide6.QtCore import Qt, Signal, QThread, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy,
    QScrollArea, QFileDialog
)

from qfluentwidgets import (
    ScrollArea, TitleLabel, SubtitleLabel, BodyLabel,
    PrimaryPushButton, PushButton, TransparentToolButton, ToolButton,
    InfoBar, InfoBarPosition, LineEdit, TextEdit, ComboBox,
    FluentIcon as FIF, CardWidget, SimpleCardWidget, MessageBox
)

from ..components.chat_message_widget import ChatMessageWidget
from ..common.logger import logger
from core.model_manager import model_manager
from data.models.ai_config import AIModelConfig, ChatMessage, ChatSession
from data.repositories.ai_config_repository import (
    AIModelConfigRepository, ChatSessionRepository, ChatMessageRepository
)


class ChatWorker(QThread):
    """聊天工作线程"""

    messageReceived = Signal(str, str)  # 收到消息片段 (type, json_data)
    finished = Signal()                 # 完成
    error = Signal(str)                 # 错误

    def __init__(self, messages: List[Dict[str, str]], use_tools: bool = False, parent=None):
        super().__init__(parent)
        self._messages = messages
        self._is_stopped = False
        self._use_tools = use_tools

    def run(self):
        """执行聊天"""
        try:
            if self._use_tools and model_manager.has_tools():
                # 使用支持工具调用的对话
                for chunk in model_manager.chat_with_tools(self._messages, stream=True):
                    if self._is_stopped:
                        break
                    chunk_type = chunk.get("type", "content")
                    self.messageReceived.emit(chunk_type, json.dumps(chunk, ensure_ascii=False))
            else:
                # 普通对话
                for chunk in model_manager.chat(self._messages, stream=True):
                    if self._is_stopped:
                        break
                    chunk_type = chunk.get("type", "content")
                    chunk_text = chunk.get("text", "")
                    self.messageReceived.emit(chunk_type, json.dumps({"text": chunk_text}, ensure_ascii=False))
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        """停止"""
        self._is_stopped = True


class AIChatInterface(ScrollArea):
    """AI 对话页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.info("初始化 AI 对话页面...")
        self._config_repo = AIModelConfigRepository()
        self._session_repo = ChatSessionRepository()
        self._message_repo = ChatMessageRepository()
        self._current_session: Optional[ChatSession] = None
        self._messages: List[Dict[str, str]] = []
        self._worker: Optional[ChatWorker] = None
        self._current_message_widget: Optional[ChatMessageWidget] = None

        self._initUI()
        self._loadModelConfigs()
        self._newSession()
        logger.info("AI 对话页面初始化完成")

    def _initUI(self):
        """初始化 UI"""
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        # 顶部工具栏
        toolbarLayout = QHBoxLayout()

        self.titleLabel = TitleLabel("AI 助手", self)

        # 模型选择
        self.modelCombo = ComboBox(self)
        self.modelCombo.setFixedWidth(200)
        self.modelCombo.currentIndexChanged.connect(self._onModelChanged)

        # 工作目录选择
        self.workDirBtn = PushButton(FIF.FOLDER, "选择工作目录", self)
        self.workDirBtn.setFixedWidth(140)
        self.workDirBtn.clicked.connect(self._selectWorkDirectory)

        # 工作目录显示
        self.workDirLabel = BodyLabel("未设置工作目录", self)
        self.workDirLabel.setStyleSheet("color: #888;")

        # 新建对话按钮
        self.newChatBtn = TransparentToolButton(FIF.ADD, self)
        self.newChatBtn.setToolTip("新建对话")
        self.newChatBtn.clicked.connect(self._newSession)

        # 设置按钮
        self.settingsBtn = TransparentToolButton(FIF.SETTING, self)
        self.settingsBtn.setToolTip("模型设置")
        self.settingsBtn.clicked.connect(self._onSettings)

        toolbarLayout.addWidget(self.titleLabel)
        toolbarLayout.addStretch()
        toolbarLayout.addWidget(BodyLabel("当前模型:", self))
        toolbarLayout.addWidget(self.modelCombo)
        toolbarLayout.addWidget(self.workDirBtn)
        toolbarLayout.addWidget(self.workDirLabel)
        toolbarLayout.addWidget(self.newChatBtn)
        toolbarLayout.addWidget(self.settingsBtn)

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

        # 消息容器（用于存放消息）
        self._message_widgets = []
        self._empty_shown = True

        # 空状态提示
        self.emptyLabel = BodyLabel(
            "开始与 AI 助手对话吧！\n\n您可以：\n- 询问 HR 相关问题\n- 让 AI 帮您分析数据\n- 生成报告和建议\n- 设置工作目录后可操作本地文件",
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
        self.inputEdit.setPlaceholderText("输入消息... (Enter 发送, Shift+Enter 换行)")
        self.inputEdit.setFixedHeight(80)
        self.inputEdit.installEventFilter(self)

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
        self.vBoxLayout.addWidget(self.scrollArea, 1)
        self.vBoxLayout.addWidget(inputCard)

        # 滚动设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.setObjectName('aiChatInterface')
        self.view.setObjectName('view')

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理 Enter 键"""
        from PySide6.QtCore import QEvent, Qt
        if hasattr(self, 'inputEdit') and obj == self.inputEdit and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self._sendMessage()
                return True
        return super().eventFilter(obj, event)

    def _selectWorkDirectory(self):
        """选择工作目录"""
        from pathlib import Path
        current_dir = model_manager.get_work_directory() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择工作目录",
            current_dir
        )
        if directory:
            model_manager.set_work_directory(directory)
            # 显示简短路径
            display_path = directory
            if len(directory) > 40:
                display_path = "..." + directory[-37:]
            self.workDirLabel.setText(display_path)
            self.workDirLabel.setStyleSheet("color: #1976d2;")

            InfoBar.success(
                title="工作目录已设置",
                content=directory,
                parent=self
            )

    def _loadModelConfigs(self):
        """加载模型配置列表"""
        configs = self._config_repo.find_enabled()
        self.modelCombo.clear()

        if not configs:
            # 自动创建默认配置（腾讯云 Claude）
            self._createDefaultConfig()
            configs = self._config_repo.find_enabled()

        if not configs:
            self.modelCombo.addItem("请先配置模型")
            self.sendBtn.setEnabled(False)
            return

        self.sendBtn.setEnabled(True)
        default_idx = 0
        for i, config in enumerate(configs):
            self.modelCombo.addItem(config.name, userData=config)
            if config.is_default:
                default_idx = i

        self.modelCombo.setCurrentIndex(default_idx)
        self._onModelChanged(default_idx)

    def _createDefaultConfig(self):
        """创建默认配置"""
        import os
        # 从环境变量读取配置
        api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "https://api.lkeap.cloud.tencent.com/coding/anthropic")
        model_name = os.environ.get("ANTHROPIC_MODEL", "glm-5")

        if not api_key:
            return  # 没有配置则不自动创建

        config = AIModelConfig(
            name="默认模型",
            provider="tencent_claude",
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.7,
            max_tokens=4096,
            is_default=True,
            is_enabled=True,
        )
        self._config_repo.save(config)

    def _onModelChanged(self, index: int):
        """模型选择改变"""
        config = self.modelCombo.itemData(index)
        if config and isinstance(config, AIModelConfig):
            try:
                model_manager.set_current_model(config)
                if self._current_session:
                    self._current_session.model_config_id = config.id
            except Exception as e:
                InfoBar.error(
                    title="错误",
                    content=f"模型加载失败: {str(e)}",
                    parent=self
                )

    def _onSettings(self):
        """打开设置"""
        from .ai_settings_interface import AISettingsInterface
        # 发送信号通知主窗口切换到设置页面
        pass  # 由主窗口处理

    def _newSession(self):
        """新建会话"""
        self._current_session = ChatSession()
        config = self.modelCombo.currentData()
        if config:
            self._current_session.model_config_id = config.id
        self._current_session = self._session_repo.save(self._current_session)
        self._messages = []
        self._clearMessages()

    def _clearMessages(self):
        """清空消息区域"""
        # 删除所有消息 widget
        for widget in self._message_widgets:
            widget.deleteLater()
        self._message_widgets.clear()
        # 显示空状态提示
        self.emptyLabel.show()
        self._empty_shown = True

    def _scrollToBottom(self):
        """滚动到底部"""
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, lambda: self.scrollArea.verticalScrollBar().setValue(
            self.scrollArea.verticalScrollBar().maximum()
        ))

    def _addMessage(self, role: str, content: str):
        """添加消息到界面"""
        # 隐藏空状态提示
        if self._empty_shown:
            self.emptyLabel.hide()
            self._empty_shown = False
        widget = ChatMessageWidget(role, content, self.scrollWidget)
        self._message_widgets.append(widget)
        self.scrollLayout.insertWidget(self.scrollLayout.count() - 1, widget)
        self._scrollToBottom()
        return widget

    def _sendMessage(self):
        """发送消息"""
        content = self.inputEdit.toPlainText().strip()
        if not content:
            return

        config = self.modelCombo.currentData()
        if not config or not isinstance(config, AIModelConfig):
            InfoBar.warning(
                title="提示",
                content="请先配置 AI 模型",
                parent=self
            )
            return

        # 添加用户消息
        self._addMessage("user", content)
        self._messages.append({"role": "user", "content": content})
        logger.debug(f"用户消息: {content[:50]}...")

        # 保存用户消息
        user_msg = ChatMessage(
            session_id=self._current_session.id,
            role="user",
            content=content
        )
        self._message_repo.save(user_msg)

        # 清空输入
        self.inputEdit.clear()

        # 更新标题
        if len(self._messages) == 1:
            title = content[:20] + "..." if len(content) > 20 else content
            self._session_repo.update_title(self._current_session.id, title)

        # 启动工作线程
        use_tools = model_manager.has_tools()
        logger.info(f"启动 AI 生成，模型: {config.model_name}, 工具模式: {use_tools}")
        self._worker = ChatWorker(self._messages, use_tools=use_tools, parent=self)
        self._worker.messageReceived.connect(self._onMessageReceived)
        self._worker.finished.connect(self._onFinished)
        self._worker.error.connect(self._onError)

        # UI 状态
        self.sendBtn.setVisible(False)
        self.stopBtn.setVisible(True)
        self.inputEdit.setEnabled(False)

        # 添加 AI 消息占位
        self._current_message_widget = self._addMessage("assistant", "")

        self._worker.start()

    @Slot(str, str)
    def _onMessageReceived(self, msg_type: str, data: str):
        """收到消息片段"""
        if not self._current_message_widget:
            return

        try:
            chunk = json.loads(data)
        except json.JSONDecodeError:
            chunk = {"text": data}

        if msg_type == "thinking":
            text = chunk.get("text", "")
            self._current_message_widget.appendThinking(text)
        elif msg_type == "content":
            text = chunk.get("text", "")
            self._current_message_widget.appendContent(text)
        elif msg_type == "tool_call":
            name = chunk.get("name", "")
            args = chunk.get("args", {})
            tool_id = chunk.get("id", "")
            self._current_message_widget.addToolCall(name, args, tool_id)
        elif msg_type == "tool_result":
            name = chunk.get("name", "")
            result = chunk.get("result", "")
            self._current_message_widget.addToolResult(name, result)
        else:
            # 默认作为内容处理
            text = chunk.get("text", "")
            if text:
                self._current_message_widget.appendContent(text)

        self._scrollToBottom()

    @Slot()
    def _onFinished(self):
        """生成完成"""
        # 保存 AI 消息
        if self._current_message_widget:
            ai_content = self._current_message_widget._content
            self._messages.append({"role": "assistant", "content": ai_content})
            logger.info(f"AI 响应完成: {len(ai_content)} 字符")

            ai_msg = ChatMessage(
                session_id=self._current_session.id,
                role="assistant",
                content=ai_content
            )
            self._message_repo.save(ai_msg)

        self._resetUI()

    @Slot(str)
    def _onError(self, error: str):
        """发生错误"""
        logger.error(f"AI 生成错误: {error}")
        if self._current_message_widget:
            self._current_message_widget.setContent(f"发生错误: {error}")
        self._resetUI()

        InfoBar.error(
            title="错误",
            content=error,
            duration=5000,
            parent=self
        )

    def _stopGeneration(self):
        """停止生成"""
        if self._worker:
            self._worker.stop()
        self._resetUI()

    def _resetUI(self):
        """重置 UI 状态"""
        self.sendBtn.setVisible(True)
        self.stopBtn.setVisible(False)
        self.inputEdit.setEnabled(True)
        self._worker = None
        self._current_message_widget = None

    def refreshModels(self):
        """刷新模型列表"""
        self._loadModelConfigs()
