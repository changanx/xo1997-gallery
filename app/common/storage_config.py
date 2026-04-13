"""
存储配置管理模块
"""
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass, asdict

from PySide6.QtCore import QObject, Signal


@dataclass
class StorageConfig:
    """存储配置"""

    data_dir: str = ""
    """数据存储目录路径，为空则使用默认位置"""

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StorageConfig":
        """从字典创建"""
        return cls(
            data_dir=data.get("data_dir", ""),
        )

    @property
    def effective_data_dir(self) -> Path:
        """获取有效的数据目录"""
        if self.data_dir:
            return Path(self.data_dir)
        return Path("C:/ProgramData/xo1997-pyside-gallery/db")


class StorageConfigManager(QObject):
    """存储配置管理器"""

    # 配置变更信号
    config_changed = Signal(StorageConfig)

    # 需要重启应用信号
    restart_required = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._config_dir: Path = Path.home() / ".xo1997-gallery" / "config"
        self._config_file: Path = self._config_dir / "storage.json"
        self._config: StorageConfig = StorageConfig()

        # 加载配置
        self._load_config()

    def _load_config(self) -> None:
        """从文件加载配置"""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = StorageConfig.from_dict(data)
            except Exception:
                # 加载失败，使用默认配置
                self._config = StorageConfig()

    def _save_config(self) -> None:
        """保存配置到文件"""
        self._config_dir.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

    def get_config(self) -> StorageConfig:
        """获取当前配置"""
        return self._config

    def set_data_dir(self, path: str) -> None:
        """
        设置数据存储目录

        Args:
            path: 目录路径，为空则使用默认位置
        """
        old_dir = self._config.effective_data_dir
        self._config.data_dir = path
        self._save_config()
        self.config_changed.emit(self._config)

        # 如果路径改变，需要重启应用
        new_dir = self._config.effective_data_dir
        if old_dir != new_dir:
            self.restart_required.emit()

    def get_database_path(self) -> Path:
        """获取数据库文件路径"""
        return self._config.effective_data_dir / "xo1997-gallery.db"

    def ensure_data_dir(self) -> Path:
        """确保数据目录存在"""
        data_dir = self._config.effective_data_dir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def has_data_to_migrate(self, path: Path) -> bool:
        """
        检查指定路径是否有可迁移的数据

        Args:
            path: 数据目录路径

        Returns:
            是否存在数据库文件
        """
        db_file = path / "xo1997-gallery.db"
        return db_file.exists() and db_file.stat().st_size > 0

    def migrate_data(
        self,
        old_path: Path,
        new_path: Path,
        delete_old: bool = False
    ) -> Tuple[bool, str]:
        """
        迁移数据到新位置

        Args:
            old_path: 旧数据目录
            new_path: 新数据目录
            delete_old: 是否删除旧数据

        Returns:
            (成功与否, 消息)
        """
        old_db = old_path / "xo1997-gallery.db"
        new_db = new_path / "xo1997-gallery.db"

        # 检查旧数据库是否存在
        if not old_db.exists():
            return False, "旧数据目录中没有数据库文件"

        try:
            # 确保新目录存在
            new_path.mkdir(parents=True, exist_ok=True)

            # 检查新位置是否已有数据库
            if new_db.exists():
                # 备份现有数据库
                backup_path = new_db.with_suffix(".db.bak")
                if backup_path.exists():
                    backup_path.unlink()
                shutil.copy2(new_db, backup_path)

            # 复制数据库文件
            shutil.copy2(old_db, new_db)

            # 如果需要删除旧数据
            if delete_old:
                old_db.unlink()

            return True, "数据迁移成功"

        except Exception as e:
            return False, f"迁移失败: {str(e)}"


# 全局存储配置管理器实例
storage_config_manager = StorageConfigManager()
