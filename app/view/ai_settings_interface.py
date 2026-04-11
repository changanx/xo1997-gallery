"""
AI 模型配置页面
"""
from typing import Optional
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QSpacerItem, QSizePolicy
)

from qfluentwidgets import (
    ScrollArea, TitleLabel, SubtitleLabel, BodyLabel,
    PrimaryPushButton, PushButton, TransparentToolButton, ToolButton,
    InfoBar, InfoBarPosition, LineEdit, ComboBox, SpinBox, DoubleSpinBox,
    SwitchButton, CardWidget, SimpleCardWidget, FluentIcon as FIF,
    MessageBoxBase, SubtitleLabel as MBoxSubtitleLabel, LineEdit as MBoxLineEdit,
    ComboBox as MBoxComboBox, TextEdit, ExpandLayout
)
from PySide6.QtWidgets import QComboBox

from core.model_manager import MODEL_PROVIDERS, ModelProvider
from data.models.ai_config import AIModelConfig
from data.repositories.ai_config_repository import AIModelConfigRepository
from app.common.logger import set_level, set_backup_count, get_log_dir
from app.common.log_config import log_config_manager


class ModelConfigDialog(MessageBoxBase):
    """模型配置对话框"""

    def __init__(self, config: Optional[AIModelConfig] = None, parent=None):
        super().__init__(parent)
        self._config = config or AIModelConfig()
        self._repo = AIModelConfigRepository()

        self._initUI()
        self._loadConfig()

    def _initUI(self):
        """初始化 UI"""
        # 标题
        self.titleLabel = SubtitleLabel("模型配置", self)
        self.viewLayout.addWidget(self.titleLabel)

        # 表单布局
        formLayout = QGridLayout()
        formLayout.setSpacing(12)
        row = 0

        # 配置名称
        formLayout.addWidget(BodyLabel("配置名称:"), row, 0)
        self.nameEdit = LineEdit(self)
        self.nameEdit.setPlaceholderText("如: GPT-4o 个人")
        formLayout.addWidget(self.nameEdit, row, 1)
        row += 1

        # 提供商
        formLayout.addWidget(BodyLabel("提供商:"), row, 0)
        self.providerCombo = ComboBox(self)
        self.providerCombo.addItems([p.name for p in MODEL_PROVIDERS.values()])
        self.providerCombo.currentIndexChanged.connect(self._onProviderChanged)
        formLayout.addWidget(self.providerCombo, row, 1)
        row += 1

        # 模型名称
        formLayout.addWidget(BodyLabel("模型名称:"), row, 0)
        self.modelNameEdit = QComboBox(self)
        self.modelNameEdit.setEditable(True)
        formLayout.addWidget(self.modelNameEdit, row, 1)
        row += 1

        # API Key
        formLayout.addWidget(BodyLabel("API Key:"), row, 0)
        self.apiKeyEdit = LineEdit(self)
        self.apiKeyEdit.setEchoMode(LineEdit.Password)
        self.apiKeyEdit.setPlaceholderText("sk-...")
        formLayout.addWidget(self.apiKeyEdit, row, 1)
        row += 1

        # Base URL
        formLayout.addWidget(BodyLabel("API 地址:"), row, 0)
        self.baseUrlEdit = LineEdit(self)
        self.baseUrlEdit.setPlaceholderText("可选，自定义 API 端点")
        formLayout.addWidget(self.baseUrlEdit, row, 1)
        row += 1

        # Temperature
        formLayout.addWidget(BodyLabel("Temperature:"), row, 0)
        self.tempSpin = DoubleSpinBox(self)
        self.tempSpin.setRange(0.0, 2.0)
        self.tempSpin.setSingleStep(0.1)
        self.tempSpin.setValue(0.7)
        formLayout.addWidget(self.tempSpin, row, 1)
        row += 1

        # Max Tokens
        formLayout.addWidget(BodyLabel("Max Tokens:"), row, 0)
        self.maxTokensSpin = SpinBox(self)
        self.maxTokensSpin.setRange(100, 128000)
        self.maxTokensSpin.setValue(2048)
        self.maxTokensSpin.setSingleStep(100)
        formLayout.addWidget(self.maxTokensSpin, row, 1)
        row += 1

        # 设为默认
        defaultLayout = QHBoxLayout()
        formLayout.addWidget(BodyLabel("设为默认:"), row, 0)
        self.defaultSwitch = SwitchButton(self)
        defaultLayout.addWidget(self.defaultSwitch)
        defaultLayout.addStretch()
        formLayout.addLayout(defaultLayout, row, 1)
        row += 1

        self.viewLayout.addLayout(formLayout)

        # 按钮
        self.yesButton.setText("保存")
        self.cancelButton.setText("取消")

        # 初始化提供商
        self._onProviderChanged(0)

    def _onProviderChanged(self, index: int):
        """提供商改变"""
        provider_id = list(MODEL_PROVIDERS.keys())[index]
        provider = MODEL_PROVIDERS[provider_id]

        # 更新模型列表
        self.modelNameEdit.clear()
        self.modelNameEdit.addItems(provider.default_models)

        # 更新默认 base URL
        self.baseUrlEdit.setPlaceholderText(provider.default_base_url)

        # Ollama 不需要 API Key
        if not provider.requires_api_key:
            self.apiKeyEdit.setPlaceholderText("无需 API Key")
        else:
            self.apiKeyEdit.setPlaceholderText("sk-...")

    def _loadConfig(self):
        """加载配置"""
        if self._config.id is not None:
            self.nameEdit.setText(self._config.name)

            # 设置提供商
            provider_ids = list(MODEL_PROVIDERS.keys())
            if self._config.provider in provider_ids:
                self.providerCombo.setCurrentIndex(provider_ids.index(self._config.provider))

            self.modelNameEdit.setCurrentText(self._config.model_name)
            self.apiKeyEdit.setText(self._config.api_key)
            self.baseUrlEdit.setText(self._config.base_url)
            self.tempSpin.setValue(self._config.temperature)
            self.maxTokensSpin.setValue(self._config.max_tokens)
            self.defaultSwitch.setChecked(self._config.is_default)

    def _saveConfig(self) -> AIModelConfig:
        """保存配置"""
        provider_ids = list(MODEL_PROVIDERS.keys())
        provider_idx = self.providerCombo.currentIndex()

        self._config.name = self.nameEdit.text().strip()
        self._config.provider = provider_ids[provider_idx]
        self._config.model_name = self.modelNameEdit.currentText().strip()
        self._config.api_key = self.apiKeyEdit.text().strip()
        self._config.base_url = self.baseUrlEdit.text().strip()
        self._config.temperature = self.tempSpin.value()
        self._config.max_tokens = self.maxTokensSpin.value()
        self._config.is_default = self.defaultSwitch.isChecked()

        return self._repo.save(self._config)

    def validate(self) -> bool:
        """验证输入"""
        if not self.nameEdit.text().strip():
            InfoBar.warning(
                title="警告",
                content="请输入配置名称",
                parent=self
            )
            return False

        if not self.modelNameEdit.currentText().strip():
            InfoBar.warning(
                title="警告",
                content="请输入模型名称",
                parent=self
            )
            return False

        provider = list(MODEL_PROVIDERS.values())[self.providerCombo.currentIndex()]
        if provider.requires_api_key and not self.apiKeyEdit.text().strip():
            InfoBar.warning(
                title="警告",
                content="请输入 API Key",
                parent=self
            )
            return False

        return True


class ModelConfigCard(SimpleCardWidget):
    """模型配置卡片"""

    edited = Signal(int)       # 编辑信号
    deleted = Signal(int)      # 删除信号

    def __init__(self, config: AIModelConfig, parent=None):
        super().__init__(parent)
        self._config = config
        self._initUI()

    def _initUI(self):
        """初始化 UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 左侧信息
        infoLayout = QVBoxLayout()
        infoLayout.setSpacing(4)

        self.nameLabel = BodyLabel(self._config.name, self)
        self.nameLabel.setStyleSheet("font-weight: bold;")
        infoLayout.addWidget(self.nameLabel)

        provider = MODEL_PROVIDERS.get(self._config.provider)
        provider_name = provider.name if provider else self._config.provider
        self.detailLabel = BodyLabel(
            f"{provider_name} / {self._config.model_name}",
            self
        )
        self.detailLabel.setStyleSheet("color: #666;")
        infoLayout.addWidget(self.detailLabel)

        layout.addLayout(infoLayout, 1)

        # 状态标签
        if self._config.is_default:
            self.defaultTag = PushButton("默认", self)
            self.defaultTag.setDisabled(True)
            self.defaultTag.setFixedWidth(50)
            layout.addWidget(self.defaultTag)

        # 右侧按钮
        self.editBtn = TransparentToolButton(FIF.EDIT, self)
        self.editBtn.setFixedWidth(32)
        self.editBtn.clicked.connect(lambda: self.edited.emit(self._config.id))
        layout.addWidget(self.editBtn)

        self.deleteBtn = TransparentToolButton(FIF.DELETE, self)
        self.deleteBtn.setFixedWidth(32)
        self.deleteBtn.clicked.connect(lambda: self.deleted.emit(self._config.id))
        layout.addWidget(self.deleteBtn)


class AISettingsInterface(ScrollArea):
    """AI 设置页面"""

    configChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repo = AIModelConfigRepository()

        self._initUI()
        self._loadConfigs()

    def _initUI(self):
        """初始化 UI"""
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        # 标题
        self.titleLabel = TitleLabel("AI 模型配置", self)
        self.subtitleLabel = SubtitleLabel("管理 AI 模型的连接配置", self)

        # 添加按钮
        self.addBtn = PrimaryPushButton(FIF.ADD, "添加模型配置", self)
        self.addBtn.clicked.connect(self._onAddConfig)

        # 配置列表容器
        self.configContainer = QWidget(self)
        self.configLayout = QVBoxLayout(self.configContainer)
        self.configLayout.setSpacing(8)
        self.configLayout.setContentsMargins(0, 0, 0, 0)

        # 日志配置区域
        self._initLogConfigUI()

        # 布局
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addWidget(self.addBtn)
        self.vBoxLayout.addWidget(self.configContainer)
        self.vBoxLayout.addWidget(self.logConfigCard)
        self.vBoxLayout.addStretch()

        # 滚动设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.setObjectName('aiSettingsInterface')
        self.view.setObjectName('view')

    def _initLogConfigUI(self):
        """初始化日志配置 UI"""
        self.logConfigCard = CardWidget(self)
        layout = QVBoxLayout(self.logConfigCard)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 标题
        titleLabel = SubtitleLabel("日志配置", self)
        layout.addWidget(titleLabel)

        # 日志级别
        levelLayout = QHBoxLayout()
        levelLayout.addWidget(BodyLabel("日志级别:"))

        self.logLevelCombo = ComboBox(self)
        self.logLevelCombo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        # 设置当前级别
        current_level = log_config_manager.get_config().level
        self.logLevelCombo.setCurrentText(logging.getLevelName(current_level))
        self.logLevelCombo.currentTextChanged.connect(self._onLogLevelChanged)
        levelLayout.addWidget(self.logLevelCombo)
        levelLayout.addStretch()
        layout.addLayout(levelLayout)

        # 日志保留天数
        backupLayout = QHBoxLayout()
        backupLayout.addWidget(BodyLabel("保留天数:"))

        self.logBackupSpin = SpinBox(self)
        self.logBackupSpin.setRange(1, 90)
        self.logBackupSpin.setValue(log_config_manager.get_config().backup_count)
        self.logBackupSpin.valueChanged.connect(self._onBackupDaysChanged)
        backupLayout.addWidget(self.logBackupSpin)
        backupLayout.addStretch()
        layout.addLayout(backupLayout)

        # 打开日志目录按钮
        openDirBtn = PushButton(FIF.FOLDER, "打开日志目录", self)
        openDirBtn.clicked.connect(self._onOpenLogDir)
        layout.addWidget(openDirBtn)

    def _onLogLevelChanged(self, level_name: str):
        """日志级别改变"""
        level = getattr(logging, level_name, logging.INFO)
        set_level(level)
        log_config_manager.set_level(level)
        InfoBar.success(
            title="已更新",
            content=f"日志级别已设置为 {level_name}",
            parent=self
        )

    def _onBackupDaysChanged(self, days: int):
        """日志保留天数改变"""
        set_backup_count(days)
        log_config_manager.set_backup_count(days)

    def _onOpenLogDir(self):
        """打开日志目录"""
        import os
        import subprocess

        log_dir = get_log_dir()
        if log_dir.exists():
            if os.name == 'nt':  # Windows
                os.startfile(str(log_dir))
            else:  # macOS / Linux
                subprocess.run(['xdg-open', str(log_dir)])
        else:
            InfoBar.warning(
                title="提示",
                content="日志目录尚不存在",
                parent=self
            )

    def _loadConfigs(self):
        """加载配置列表"""
        # 清空现有卡片
        while self.configLayout.count():
            item = self.configLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 加载配置
        configs = self._repo.find_all()

        if not configs:
            emptyLabel = BodyLabel("暂无模型配置，点击上方按钮添加", self)
            emptyLabel.setStyleSheet("color: #999;")
            self.configLayout.addWidget(emptyLabel)
            return

        for config in configs:
            card = ModelConfigCard(config, self)
            card.edited.connect(self._onEditConfig)
            card.deleted.connect(self._onDeleteConfig)
            self.configLayout.addWidget(card)

    def _onAddConfig(self):
        """添加配置"""
        dialog = ModelConfigDialog(parent=self)
        if dialog.exec():
            if dialog.validate():
                dialog._saveConfig()
                self._loadConfigs()
                self.configChanged.emit()
                InfoBar.success(
                    title="成功",
                    content="模型配置已添加",
                    parent=self
                )

    def _onEditConfig(self, config_id: int):
        """编辑配置"""
        config = self._repo.find_by_id(config_id)
        if config:
            dialog = ModelConfigDialog(config, parent=self)
            if dialog.exec():
                if dialog.validate():
                    dialog._saveConfig()
                    self._loadConfigs()
                    self.configChanged.emit()
                    InfoBar.success(
                        title="成功",
                        content="模型配置已更新",
                        parent=self
                    )

    def _onDeleteConfig(self, config_id: int):
        """删除配置"""
        if self._repo.delete(config_id):
            self._loadConfigs()
            self.configChanged.emit()
            InfoBar.success(
                title="成功",
                content="模型配置已删除",
                parent=self
            )
