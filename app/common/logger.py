"""
日志配置模块
"""
import logging
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import TimedRotatingFileHandler

from PySide6.QtCore import QObject, Signal


class JsonFormatter(logging.Formatter):
    """JSON 格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化为 JSON"""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # 添加额外字段
        if hasattr(record, "extra_data") and record.extra_data:
            log_data["extra"] = record.extra_data

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加位置信息
        if record.levelno >= logging.WARNING:
            log_data["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """文本格式日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化为文本"""
        base = super().format(record)

        # 添加额外字段
        if hasattr(record, "extra_data") and record.extra_data:
            extra_str = " | " + " ".join(f"{k}={v}" for k, v in record.extra_data.items())
            base += extra_str

        return base


class LogSignalEmitter(QObject):
    """日志信号发射器"""
    log_received = Signal(str, str)  # (level, formatted_message)


class QtSignalHandler(logging.Handler):
    """将日志转发到 Qt 信号的 Handler"""

    def __init__(self):
        super().__init__()
        self._emitter = LogSignalEmitter()
        self._formatter = TextFormatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%H:%M:%S",
        )

    def emit(self, record: logging.LogRecord) -> None:
        """发射日志信号"""
        try:
            msg = self.format(record)
            self._emitter.log_received.emit(record.levelname, msg)
        except Exception:
            pass

    @property
    def emitter(self) -> LogSignalEmitter:
        """获取信号发射器"""
        return self._emitter


class LoggerManager:
    """日志管理器"""

    _instance: Optional["LoggerManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._logger: Optional[logging.Logger] = None
        self._console_handler: Optional[logging.StreamHandler] = None
        self._file_handler: Optional[TimedRotatingFileHandler] = None
        self._json_handler: Optional[TimedRotatingFileHandler] = None
        self._signal_handler: Optional[QtSignalHandler] = None
        self._current_level: int = logging.DEBUG
        self._log_dir: Path = Path.home() / ".xo1997-gallery" / "logs"
        self._backup_count: int = 7
        self._initialized = True

    def setup(
        self,
        name: str = "xo1997-gallery",
        level: int = logging.DEBUG,
        backup_count: int = 7,
        json_format: bool = True,
    ) -> logging.Logger:
        """
        设置日志器

        Args:
            name: 日志器名称
            level: 日志级别
            backup_count: 日志保留天数
            json_format: 是否生成 JSON 格式日志文件
        """
        self._current_level = level
        self._backup_count = backup_count

        # 创建日志目录
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # 创建日志器
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)

        # 清除已有处理器
        self._logger.handlers.clear()

        # 控制台输出（文本格式）
        self._console_handler = logging.StreamHandler(sys.stdout)
        self._console_handler.setLevel(logging.DEBUG)
        console_format = TextFormatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%H:%M:%S",
        )
        self._console_handler.setFormatter(console_format)
        self._logger.addHandler(self._console_handler)

        # 文件输出（文本格式）
        log_file = self._log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        self._file_handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=backup_count,
            encoding="utf-8",
        )
        self._file_handler.setLevel(logging.DEBUG)
        file_format = TextFormatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._file_handler.setFormatter(file_format)
        self._logger.addHandler(self._file_handler)

        # JSON 格式文件输出
        if json_format:
            json_file = self._log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.json"
            self._json_handler = TimedRotatingFileHandler(
                json_file,
                when="midnight",
                interval=1,
                backupCount=backup_count,
                encoding="utf-8",
            )
            self._json_handler.setLevel(logging.DEBUG)
            self._json_handler.setFormatter(JsonFormatter())
            self._logger.addHandler(self._json_handler)

        # Qt 信号输出（用于 UI 日志窗口）
        self._signal_handler = QtSignalHandler()
        self._signal_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(self._signal_handler)

        return self._logger

    def get_logger(self) -> logging.Logger:
        """获取日志器"""
        if self._logger is None:
            return self.setup()
        return self._logger

    def set_level(self, level: int) -> None:
        """
        动态设置日志级别

        Args:
            level: logging.DEBUG, INFO, WARNING, ERROR, CRITICAL
        """
        self._current_level = level
        if self._logger:
            self._logger.setLevel(level)
        if self._file_handler:
            self._file_handler.setLevel(level)
        if self._json_handler:
            self._json_handler.setLevel(level)
        # 控制台保持 DEBUG，便于开发调试

    def get_level(self) -> int:
        """获取当前日志级别"""
        return self._current_level

    def get_log_dir(self) -> Path:
        """获取日志目录"""
        return self._log_dir

    def set_backup_count(self, count: int) -> None:
        """
        设置日志保留天数

        Args:
            count: 保留天数
        """
        self._backup_count = count
        if self._file_handler:
            self._file_handler.backupCount = count
        if self._json_handler:
            self._json_handler.backupCount = count

    def get_backup_count(self) -> int:
        """获取日志保留天数"""
        return self._backup_count

    def get_signal_handler(self) -> Optional[QtSignalHandler]:
        """获取 Qt 信号 Handler"""
        return self._signal_handler


class StructuredLogger:
    """结构化日志包装器"""

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _log(self, level: int, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录带额外字段的日志"""
        record = self._logger.makeRecord(
            self._logger.name,
            level,
            "",
            0,
            msg,
            (),
            None,
        )
        record.extra_data = extra or {}
        self._logger.handle(record)

    def debug(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.DEBUG, msg, extra)

    def info(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.INFO, msg, extra)

    def warning(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.WARNING, msg, extra)

    def error(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.ERROR, msg, extra)

    def critical(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        self._log(logging.CRITICAL, msg, extra)

    def exception(self, msg: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """记录异常日志"""
        record = self._logger.makeRecord(
            self._logger.name,
            logging.ERROR,
            "",
            0,
            msg,
            (),
            None,
        )
        record.extra_data = extra or {}
        record.exc_info = sys.exc_info()
        self._logger.handle(record)


# 全局日志管理器
_manager = LoggerManager()


def setup_logger(
    name: str = "xo1997-gallery",
    level: int = logging.DEBUG,
    backup_count: int = 7,
    json_format: bool = True,
) -> logging.Logger:
    """设置日志器"""
    return _manager.setup(name, level, backup_count, json_format)


def get_logger() -> StructuredLogger:
    """获取结构化日志器"""
    return StructuredLogger(_manager.get_logger())


def set_level(level: int) -> None:
    """设置日志级别"""
    _manager.set_level(level)


def get_level() -> int:
    """获取当前日志级别"""
    return _manager.get_level()


def get_log_dir() -> Path:
    """获取日志目录"""
    return _manager.get_log_dir()


def set_backup_count(count: int) -> None:
    """设置日志保留天数"""
    _manager.set_backup_count(count)


def get_backup_count() -> int:
    """获取日志保留天数"""
    return _manager.get_backup_count()


def get_signal_handler() -> Optional[QtSignalHandler]:
    """获取 Qt 信号 Handler（用于 UI 连接）"""
    return _manager.get_signal_handler()


# 全局日志器（兼容旧代码）
logger = _manager.setup()
