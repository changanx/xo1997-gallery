"""
日志配置管理模块
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import logging

from PySide6.QtCore import QObject, Signal


@dataclass
class LogConfig:
    """日志配置"""

    level: int = logging.INFO
    """日志级别"""

    backup_count: int = 7
    """日志保留天数"""

    json_format: bool = True
    """是否启用 JSON 格式日志"""

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "LogConfig":
        """从字典创建"""
        return cls(
            level=data.get("level", logging.INFO),
            backup_count=data.get("backup_count", 7),
            json_format=data.get("json_format", True),
        )


class LogConfigManager(QObject):
    """日志配置管理器"""

    # 配置变更信号
    config_changed = Signal(LogConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config_dir: Path = Path.home() / ".xo1997-gallery" / "config"
        self._config_file: Path = self._config_dir / "log_config.json"
        self._config: LogConfig = LogConfig()

        # 加载配置
        self._load_config()

    def _load_config(self) -> None:
        """从文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = LogConfig.from_dict(data)
            except Exception:
                # 加载失败，使用默认配置
                self._config = LogConfig()

    def _save_config(self) -> None:
        """保存配置到文件"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

    def get_config(self) -> LogConfig:
        """获取当前配置"""
        return self._config

    def set_config(self, config: LogConfig) -> None:
        """
        设置配置

        Args:
            config: 新的日志配置
        """
        self._config = config
        self._save_config()
        self.config_changed.emit(config)

    def set_level(self, level: int) -> None:
        """
        设置日志级别

        Args:
            level: 日志级别 (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self._config.level = level
        self._save_config()
        self.config_changed.emit(self._config)

    def set_backup_count(self, count: int) -> None:
        """
        设置日志保留天数

        Args:
            count: 保留天数
        """
        self._config.backup_count = count
        self._save_config()
        self.config_changed.emit(self._config)

    def set_json_format(self, enabled: bool) -> None:
        """
        设置是否启用 JSON 格式日志

        Args:
            enabled: 是否启用
        """
        self._config.json_format = enabled
        self._save_config()
        self.config_changed.emit(self._config)

    @staticmethod
    def level_to_name(level: int) -> str:
        """将日志级别转换为名称"""
        return logging.getLevelName(level)

    @staticmethod
    def name_to_level(name: str) -> int:
        """将日志级别名称转换为数值"""
        return logging.getLevelName(name)


# 全局配置管理器实例
log_config_manager = LogConfigManager()
