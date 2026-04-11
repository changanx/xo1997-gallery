"""
日志模块测试
"""
import json
import logging
import tempfile
from pathlib import Path

import pytest

from app.common.logger import (
    LoggerManager,
    JsonFormatter,
    TextFormatter,
    StructuredLogger,
    setup_logger,
    get_logger,
    set_level,
    get_level,
    set_backup_count,
    get_backup_count,
)
from app.common.log_config import LogConfig, LogConfigManager


class TestJsonFormatter:
    """JsonFormatter 测试"""

    def test_format_basic(self):
        """测试基本格式化"""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Hello",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Hello"
        assert "timestamp" in data

    def test_format_with_extra(self):
        """测试带额外字段的格式化"""
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"user": "admin", "action": "login"}
        result = formatter.format(record)
        data = json.loads(result)

        assert data["extra"]["user"] == "admin"
        assert data["extra"]["action"] == "login"

    def test_format_with_exception(self):
        """测试带异常信息的格式化"""
        formatter = JsonFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        result = formatter.format(record)
        data = json.loads(result)

        assert "exception" in data
        assert "ValueError: Test error" in data["exception"]


class TestTextFormatter:
    """TextFormatter 测试"""

    def test_format_basic(self):
        """测试基本格式化"""
        formatter = TextFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Hello",
            args=(),
            exc_info=None,
        )
        result = formatter.format(record)
        assert result == "Hello"

    def test_format_with_extra(self):
        """测试带额外字段的格式化"""
        formatter = TextFormatter("%(message)s")
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Action completed",
            args=(),
            exc_info=None,
        )
        record.extra_data = {"user": "admin", "count": 5}
        result = formatter.format(record)

        assert "user=admin" in result
        assert "count=5" in result


class TestStructuredLogger:
    """StructuredLogger 测试"""

    def test_info_with_extra(self, tmp_path):
        """测试带额外字段的 info 日志"""
        import logging

        # 创建临时日志文件
        log_file = tmp_path / "test.log"

        # 设置测试日志器
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(JsonFormatter())

        test_logger = logging.getLogger("test_structured")
        test_logger.setLevel(logging.DEBUG)
        test_logger.handlers.clear()
        test_logger.addHandler(handler)

        # 使用 StructuredLogger
        structured = StructuredLogger(test_logger)
        structured.info("User logged in", extra={"user_id": 123, "ip": "127.0.0.1"})

        # 验证日志文件
        handler.close()
        content = log_file.read_text(encoding="utf-8")
        data = json.loads(content.strip())

        assert data["message"] == "User logged in"
        assert data["extra"]["user_id"] == 123
        assert data["extra"]["ip"] == "127.0.0.1"


class TestLoggerManager:
    """LoggerManager 测试"""

    def test_singleton(self):
        """测试单例模式"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        assert manager1 is manager2

    def test_setup_creates_logger(self, tmp_path):
        """测试 setup 创建日志器"""
        manager = LoggerManager._instance
        if manager is None:
            manager = LoggerManager()

        # 重置状态
        manager._logger = None
        manager._log_dir = tmp_path

        logger = manager.setup(name="test_app", level=logging.DEBUG, backup_count=3)

        assert logger is not None
        assert logger.name == "test_app"
        assert manager._backup_count == 3

    def test_set_level(self):
        """测试设置日志级别"""
        manager = LoggerManager()
        manager.setup(name="test_level", level=logging.DEBUG)

        manager.set_level(logging.WARNING)
        assert manager.get_level() == logging.WARNING

        manager.set_level(logging.INFO)
        assert manager.get_level() == logging.INFO


class TestLogConfig:
    """LogConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = LogConfig()
        assert config.level == logging.INFO
        assert config.backup_count == 7
        assert config.json_format is True

    def test_to_dict(self):
        """测试转换为字典"""
        config = LogConfig(level=logging.DEBUG, backup_count=14, json_format=False)
        data = config.to_dict()

        assert data["level"] == logging.DEBUG
        assert data["backup_count"] == 14
        assert data["json_format"] is False

    def test_from_dict(self):
        """测试从字典创建"""
        data = {"level": logging.WARNING, "backup_count": 30, "json_format": False}
        config = LogConfig.from_dict(data)

        assert config.level == logging.WARNING
        assert config.backup_count == 30
        assert config.json_format is False


class TestLogConfigManager:
    """LogConfigManager 测试"""

    def test_default_config(self, tmp_path):
        """测试默认配置"""
        manager = LogConfigManager()
        config = manager.get_config()

        assert config.level == logging.INFO
        assert config.backup_count == 7

    def test_set_level(self, tmp_path):
        """测试设置日志级别"""
        manager = LogConfigManager()
        manager._config_dir = tmp_path
        manager._config_file = tmp_path / "log_config.json"

        manager.set_level(logging.DEBUG)
        assert manager.get_config().level == logging.DEBUG

    def test_set_backup_count(self, tmp_path):
        """测试设置保留天数"""
        manager = LogConfigManager()
        manager._config_dir = tmp_path
        manager._config_file = tmp_path / "log_config.json"

        manager.set_backup_count(14)
        assert manager.get_config().backup_count == 14

    def test_config_persistence(self, tmp_path):
        """测试配置持久化"""
        manager1 = LogConfigManager()
        manager1._config_dir = tmp_path
        manager1._config_file = tmp_path / "log_config.json"

        manager1.set_level(logging.WARNING)
        manager1.set_backup_count(30)

        # 创建新实例，应加载保存的配置
        manager2 = LogConfigManager()
        manager2._config_dir = tmp_path
        manager2._config_file = tmp_path / "log_config.json"
        manager2._load_config()

        config = manager2.get_config()
        assert config.level == logging.WARNING
        assert config.backup_count == 30
