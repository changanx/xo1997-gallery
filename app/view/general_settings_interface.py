"""
通用设置页面
"""
import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)

from app.ui import (
    ScrollArea, TitleLabel, SubtitleLabel, BodyLabel,
    PushButton, InfoBar, ComboBox, SpinBox,
    CardWidget, FluentIcon as FIF
)

from app.common.logger import set_level, set_backup_count, get_log_dir
from app.common.log_config import log_config_manager
from app.common.storage_config import storage_config_manager


class GeneralSettingsInterface(ScrollArea):
    """通用设置页面"""

    configChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initUI()

    def _initUI(self):
        """初始化 UI"""
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        # 标题
        self.titleLabel = TitleLabel("通用设置", self)
        self.subtitleLabel = SubtitleLabel("日志和数据存储配置", self)

        # 日志配置区域
        self._initLogConfigUI()

        # 存储配置区域
        self._initStorageConfigUI()

        # 布局
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addWidget(self.logConfigCard)
        self.vBoxLayout.addWidget(self.storageConfigCard)
        self.vBoxLayout.addStretch()

        # 滚动设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        self.setObjectName('generalSettingsInterface')
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

    def _initStorageConfigUI(self):
        """初始化存储配置 UI"""
        self.storageConfigCard = CardWidget(self)
        layout = QVBoxLayout(self.storageConfigCard)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(16)

        # 标题
        titleLabel = SubtitleLabel("数据存储", self)
        layout.addWidget(titleLabel)

        # 数据库路径显示
        pathLayout = QHBoxLayout()
        pathLayout.addWidget(BodyLabel("数据位置:"))

        self.dataPathLabel = BodyLabel(str(storage_config_manager.get_config().effective_data_dir), self)
        self.dataPathLabel.setStyleSheet("color: #666;")
        pathLayout.addWidget(self.dataPathLabel, 1)
        layout.addLayout(pathLayout)

        # 按钮行
        btnLayout = QHBoxLayout()

        # 打开数据目录
        openDataBtn = PushButton(FIF.FOLDER, "打开数据目录", self)
        openDataBtn.clicked.connect(self._onOpenDataDir)
        btnLayout.addWidget(openDataBtn)

        # 更改存储位置
        changePathBtn = PushButton(FIF.EDIT, "更改位置", self)
        changePathBtn.clicked.connect(self._onChangeDataPath)
        btnLayout.addWidget(changePathBtn)

        btnLayout.addStretch()
        layout.addLayout(btnLayout)

        # 提示
        tipLabel = BodyLabel("提示: 更改存储位置后需要重启应用", self)
        tipLabel.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(tipLabel)

    def _onOpenDataDir(self):
        """打开数据目录"""
        import os
        import subprocess

        data_dir = storage_config_manager.get_config().effective_data_dir
        if data_dir.exists():
            if os.name == 'nt':  # Windows
                os.startfile(str(data_dir))
            else:  # macOS / Linux
                subprocess.run(['xdg-open', str(data_dir)])
        else:
            # 创建目录
            data_dir.mkdir(parents=True, exist_ok=True)
            if os.name == 'nt':
                os.startfile(str(data_dir))
            else:
                subprocess.run(['xdg-open', str(data_dir)])

    def _onChangeDataPath(self):
        """更改数据存储位置"""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from pathlib import Path

        current_dir = storage_config_manager.get_config().effective_data_dir
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "选择数据存储位置",
            str(current_dir),
        )

        if not new_dir:
            return

        new_path = Path(new_dir)
        old_path = current_dir

        # 检查是否是相同路径
        if new_path.resolve() == old_path.resolve():
            InfoBar.warning(
                title="未更改",
                content="选择了相同的目录",
                parent=self,
                duration=3000
            )
            return

        # 检查旧位置是否有数据需要迁移
        if storage_config_manager.has_data_to_migrate(old_path):
            # 弹出迁移选项对话框
            msg = QMessageBox(self)
            msg.setWindowTitle("数据迁移")
            msg.setText("检测到当前数据目录中有数据，是否迁移到新位置？")
            msg.setInformativeText(
                f"旧位置: {old_path}\n"
                f"新位置: {new_path}\n\n"
                "选择「迁移」将复制数据到新位置\n"
                "选择「不迁移」将在新位置创建空数据库"
            )
            msg.setIcon(QMessageBox.Question)

            migrate_btn = msg.addButton("迁移数据", QMessageBox.AcceptRole)
            migrate_delete_btn = msg.addButton("迁移并删除旧数据", QMessageBox.ActionRole)
            no_migrate_btn = msg.addButton("不迁移", QMessageBox.RejectRole)
            cancel_btn = msg.addButton(QMessageBox.Cancel)

            msg.exec()

            clicked = msg.clickedButton()

            if clicked == cancel_btn:
                return

            if clicked == migrate_btn or clicked == migrate_delete_btn:
                delete_old = (clicked == migrate_delete_btn)
                success, message = storage_config_manager.migrate_data(
                    old_path, new_path, delete_old=delete_old
                )

                if success:
                    storage_config_manager.set_data_dir(new_dir)
                    self.dataPathLabel.setText(new_dir)
                    InfoBar.success(
                        title="迁移成功",
                        content=f"{message}\n请重启应用以生效",
                        parent=self,
                        duration=5000
                    )
                else:
                    InfoBar.error(
                        title="迁移失败",
                        content=message,
                        parent=self,
                        duration=5000
                    )
            else:
                # 不迁移
                storage_config_manager.set_data_dir(new_dir)
                self.dataPathLabel.setText(new_dir)
                InfoBar.success(
                    title="已更新",
                    content=f"数据存储位置已更改\n将在新位置创建空数据库\n请重启应用以生效",
                    parent=self,
                    duration=5000
                )
        else:
            # 没有数据需要迁移
            storage_config_manager.set_data_dir(new_dir)
            self.dataPathLabel.setText(new_dir)
            InfoBar.success(
                title="已更新",
                content=f"数据存储位置已更改为 {new_dir}\n请重启应用以生效",
                parent=self,
                duration=5000
            )
