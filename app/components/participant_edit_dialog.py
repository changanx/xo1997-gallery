"""
参与者编辑对话框
"""
from typing import Optional, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy

from app.ui import (
    MessageBoxBase, SubtitleLabel, BodyLabel, LineEdit,
    ComboBox, PushButton, TextEdit, FluentIcon as FIF, AvatarWidget
)

from data.models.ai_config import AIModelConfig
from data.repositories.ai_config_repository import AIModelConfigRepository
from core.group_chat_manager import ROLE_TEMPLATES


# 可选头像列表（FluentIcon 名称）
AVATAR_OPTIONS = [
    ("🤖 机器人", "ROBOT"),
    ("🧠 大脑", "BRAIN"),
    ("💡 灯泡", "IDEA"),
    ("🎯 目标", "TARGET"),
    ("⚡ 闪电", "FLASH"),
    ("🔥 火焰", "FIRE"),
    ("⭐ 星星", "STAR"),
    ("🌙 月亮", "MOON"),
    ("☀️ 太阳", "SUN"),
    ("🍀 幸运草", "LEAF"),
    ("🎨 调色板", "PALETTE"),
    ("🎵 音乐", "MUSIC"),
    ("📖 书本", "BOOK"),
    ("💎 钻石", "GEM"),
    ("🚀 火箭", "ROCKET"),
]


class ParticipantEditDialog(MessageBoxBase):
    """参与者编辑对话框"""

    def __init__(self, parent=None, participant=None):
        """
        Args:
            parent: 父窗口
            participant: 现有参与者（编辑模式）
        """
        super().__init__(parent)
        self._participant = participant
        self._model_config_repo = AIModelConfigRepository()

        self._initUI()
        self._loadModels()

        # 编辑模式：填充现有数据
        if participant:
            self._fillExistingData()

    def _initUI(self):
        """初始化 UI"""
        self.titleLabel = SubtitleLabel("添加参与者" if not self._participant else "编辑参与者", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 模型选择
        self.modelLabel = BodyLabel("选择模型:", self)
        self.modelCombo = ComboBox(self)
        self.modelCombo.setMinimumWidth(200)
        self.modelCombo.currentIndexChanged.connect(self._onModelChanged)
        self.viewLayout.addWidget(self.modelLabel)
        self.viewLayout.addWidget(self.modelCombo)

        # 昵称
        self.nicknameLabel = BodyLabel("昵称:", self)
        self.nicknameEdit = LineEdit(self)
        self.nicknameEdit.setPlaceholderText("例如: @gpt-4")
        self.viewLayout.addWidget(self.nicknameLabel)
        self.viewLayout.addWidget(self.nicknameEdit)

        # 头像选择
        self.avatarLabel = BodyLabel("头像:", self)
        self.avatarCombo = ComboBox(self)
        self.avatarCombo.setMinimumWidth(200)
        for display_name, icon_name in AVATAR_OPTIONS:
            self.avatarCombo.addItem(display_name, userData=icon_name)
        self.viewLayout.addWidget(self.avatarLabel)
        self.viewLayout.addWidget(self.avatarCombo)

        # 角色模板
        self.templateLabel = BodyLabel("角色模板:", self)
        self.templateCombo = ComboBox(self)
        self.templateCombo.addItem("自定义")
        self.templateCombo.addItems([k for k in ROLE_TEMPLATES.keys() if k != "自定义"])
        self.templateCombo.setCurrentIndex(0)
        self.templateCombo.currentIndexChanged.connect(self._onTemplateChanged)
        self.viewLayout.addWidget(self.templateLabel)
        self.viewLayout.addWidget(self.templateCombo)

        # 角色描述
        self.roleLabel = BodyLabel("角色描述:", self)
        self.roleEdit = TextEdit(self)
        self.roleEdit.setPlaceholderText("描述这个模型在群聊中的角色和职责...")
        self.roleEdit.setFixedHeight(150)
        self.viewLayout.addWidget(self.roleLabel)
        self.viewLayout.addWidget(self.roleEdit)

        # 设置按钮文本
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")

        # 最小宽度
        self.widget.setMinimumWidth(400)

    def _loadModels(self):
        """加载可用模型"""
        models = self._model_config_repo.find_enabled()
        self._models = models

        for model in models:
            self.modelCombo.addItem(f"{model.name} ({model.model_name})")

    def _fillExistingData(self):
        """填充现有数据（编辑模式）"""
        if not self._participant:
            return

        # 选择模型
        for i, model in enumerate(self._models):
            if model.id == self._participant.model_config_id:
                self.modelCombo.setCurrentIndex(i)
                break

        # 昵称
        self.nicknameEdit.setText(self._participant.nickname)

        # 头像
        avatar = self._participant.avatar or "ROBOT"
        for i in range(self.avatarCombo.count()):
            if self.avatarCombo.itemData(i) == avatar:
                self.avatarCombo.setCurrentIndex(i)
                break

        # 角色描述
        self.roleEdit.setPlainText(self._participant.role_description)

    def _onModelChanged(self, index: int):
        """模型选择变化"""
        if index < 0 or index >= len(self._models):
            return

        model = self._models[index]

        # 自动生成昵称
        if not self.nicknameEdit.text():
            nickname = f"@{model.name.lower().replace(' ', '_').replace('-', '_')}"
            self.nicknameEdit.setText(nickname)

    def _onTemplateChanged(self, index: int):
        """角色模板选择变化"""
        template_name = self.templateCombo.currentText()
        if template_name in ROLE_TEMPLATES:
            self.roleEdit.setPlainText(ROLE_TEMPLATES[template_name])

    def validate(self) -> bool:
        """验证输入"""
        if self.modelCombo.currentIndex() < 0:
            return False
        if not self.nicknameEdit.text().strip():
            return False
        return True

    def get_data(self) -> dict:
        """获取对话框数据"""
        model_index = self.modelCombo.currentIndex()
        model_id = self._models[model_index].id if model_index >= 0 and model_index < len(self._models) else None

        avatar_index = self.avatarCombo.currentIndex()
        avatar = self.avatarCombo.itemData(avatar_index) if avatar_index >= 0 else "ROBOT"

        return {
            "model_config_id": model_id,
            "nickname": self.nicknameEdit.text().strip(),
            "role_description": self.roleEdit.toPlainText().strip(),
            "avatar": avatar,
        }
