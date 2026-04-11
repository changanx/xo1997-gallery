"""
SQLite 数据库连接管理
"""
import sqlite3
from typing import Optional
from contextlib import contextmanager

from app.common.logger import get_logger

logger = get_logger()


class Database:
    """SQLite 数据库连接管理器 - 单例模式"""

    _instance: Optional['Database'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.db_path = ":memory:"
        self._connection: Optional[sqlite3.Connection] = None
        self._initialized = True

    @property
    def connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        if self._connection is None:
            logger.debug("创建数据库连接", extra={"db_path": self.db_path})
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._enable_foreign_keys()
            self._init_schema()
            logger.info("数据库初始化完成")
        return self._connection

    def _enable_foreign_keys(self):
        """启用外键约束"""
        self.connection.execute("PRAGMA foreign_keys = ON")

    def _init_schema(self):
        """初始化数据库表结构"""
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS department (
                id INTEGER PRIMARY KEY,
                parent_id INTEGER,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS employee (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                employee_number TEXT,
                department_level1 TEXT,
                department_level2 TEXT,
                department_level3 TEXT,
                department_level4 TEXT,
                department_level5 TEXT,
                rank TEXT,
                category TEXT
            );

            CREATE TABLE IF NOT EXISTS ai_model_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                provider TEXT NOT NULL DEFAULT 'openai',
                model_name TEXT NOT NULL,
                api_key TEXT,
                base_url TEXT,
                temperature REAL DEFAULT 0.7,
                max_tokens INTEGER DEFAULT 2048,
                extra_params TEXT,
                is_default INTEGER DEFAULT 0,
                is_enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '新对话',
                model_config_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_session(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_department_parent ON department(parent_id);
            CREATE INDEX IF NOT EXISTS idx_employee_dept ON employee(department_level3);
            CREATE INDEX IF NOT EXISTS idx_chat_message_session ON chat_message(session_id);
        """)
        self.connection.commit()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception as e:
            logger.error("事务失败，执行回滚", extra={"error": str(e)})
            conn.rollback()
            raise

    def close(self):
        """关闭连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("数据库连接已关闭")

    def clear(self):
        """清空所有数据"""
        logger.info("清空数据库数据")
        self.connection.execute("DELETE FROM employee")
        self.connection.execute("DELETE FROM department")
        self.connection.execute("DELETE FROM chat_message")
        self.connection.execute("DELETE FROM chat_session")
        self.connection.execute("DELETE FROM ai_model_config")
        self.connection.commit()


# 全局实例
db = Database()
