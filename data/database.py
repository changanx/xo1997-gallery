"""
SQLite 数据库连接管理

双数据库架构：
- PersistentDB: 持久化数据库（文件），存储用户配置和聊天记录
- TempDB: 临时数据库（内存），存储员工组织数据
"""
import sqlite3
from typing import Optional
from contextlib import contextmanager
from pathlib import Path

from app.common.logger import get_logger, logger
from app.common.storage_config import storage_config_manager

logger = get_logger()


class Database:
    """SQLite 数据库连接管理器 - 单例模式"""

    _instance: Optional["Database"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connection: Optional[sqlite3.Connection] = None
        self._initialized = True

    @property
    def connection(self) -> sqlite3.Connection:
        """获取临时数据库连接（内存数据库）"""
        if self._connection is None:
            logger.debug("创建临时数据库连接", extra={"db_type": "memory"})
            self._connection = sqlite3.connect(":memory:", check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._enable_foreign_keys(self._connection)
            self._init_temp_schema(self._connection)
            logger.info("临时数据库初始化完成")
        return self._connection

    def _enable_foreign_keys(self, conn: sqlite3.Connection):
        """启用外键约束"""
        conn.execute("PRAGMA foreign_keys = ON")

    def _init_temp_schema(self, conn: sqlite3.Connection):
        """初始化临时数据库表结构（员工组织数据）"""
        conn.executescript("""
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

            CREATE INDEX IF NOT EXISTS idx_department_parent ON department(parent_id);
            CREATE INDEX IF NOT EXISTS idx_employee_dept ON employee(department_level3);
        """)
        conn.commit()

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
            logger.debug("临时数据库连接已关闭")

    def clear(self):
        """清空临时数据"""
        logger.info("清空临时数据库数据")
        self.connection.execute("DELETE FROM employee")
        self.connection.execute("DELETE FROM department")
        self.connection.commit()


class PersistentDatabase:
    """持久化数据库连接管理器 - 单例模式"""

    _instance: Optional["PersistentDatabase"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connection: Optional[sqlite3.Connection] = None
        self._db_path: Optional[Path] = None
        self._initialized = True

    @property
    def connection(self) -> sqlite3.Connection:
        """获取持久化数据库连接"""
        db_path = storage_config_manager.get_database_path()

        # 如果路径改变或连接不存在，重新创建连接
        if self._connection is None or self._db_path != db_path:
            if self._connection:
                self._connection.close()

            logger.debug("创建持久化数据库连接", extra={"db_path": str(db_path)})
            storage_config_manager.ensure_data_dir()
            self._connection = sqlite3.connect(str(db_path), check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._enable_optimizations(self._connection)
            self._init_persistent_schema(self._connection)
            self._db_path = db_path
            logger.info("持久化数据库初始化完成", extra={"db_path": str(db_path)})

        return self._connection

    def _enable_optimizations(self, conn: sqlite3.Connection):
        """
        启用数据库优化设置
        - 外键约束
        - WAL 模式（支持并发读写）
        - 忙等待超时
        """
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")  # 5 秒等待超时
            logger.debug("WAL 模式已启用")
        except Exception as e:
            # WAL 模式可能在某些情况下不可用（如网络驱动器）
            logger.warning("无法启用 WAL 模式，使用默认模式", extra={"error": str(e)})

    def _enable_foreign_keys(self, conn: sqlite3.Connection):
        """启用外键约束（兼容旧调用）"""
        conn.execute("PRAGMA foreign_keys = ON")

    def _init_persistent_schema(self, conn: sqlite3.Connection):
        """初始化持久化数据库表结构（用户配置和聊天记录）"""
        conn.executescript("""
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

            -- 群聊相关表
            CREATE TABLE IF NOT EXISTS group_chat_session (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL DEFAULT '新群聊',
                max_discussion_rounds INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS group_chat_participant (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                model_config_id INTEGER NOT NULL,
                nickname TEXT,
                role_description TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES group_chat_session(id) ON DELETE CASCADE,
                FOREIGN KEY (model_config_id) REFERENCES ai_model_config(id)
            );

            CREATE TABLE IF NOT EXISTS group_chat_message (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                model_config_id INTEGER,
                content TEXT NOT NULL,
                mentioned_models TEXT,
                discussion_round INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES group_chat_session(id) ON DELETE CASCADE,
                FOREIGN KEY (model_config_id) REFERENCES ai_model_config(id)
            );

            CREATE INDEX IF NOT EXISTS idx_chat_message_session ON chat_message(session_id);
            CREATE INDEX IF NOT EXISTS idx_group_chat_participant_session ON group_chat_participant(session_id);
            CREATE INDEX IF NOT EXISTS idx_group_chat_message_session ON group_chat_message(session_id);
        """)
        conn.commit()

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception as e:
            logger.error("持久化事务失败，执行回滚", extra={"error": str(e)})
            conn.rollback()
            raise

    def close(self):
        """关闭连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            self._db_path = None
            logger.debug("持久化数据库连接已关闭")

    def clear(self):
        """清空持久化数据（谨慎使用）"""
        logger.warning("清空持久化数据库数据")
        # 按外键依赖顺序删除（先删除依赖表）
        self.connection.execute("DELETE FROM group_chat_message")
        self.connection.execute("DELETE FROM group_chat_participant")
        self.connection.execute("DELETE FROM group_chat_session")
        self.connection.execute("DELETE FROM chat_message")
        self.connection.execute("DELETE FROM chat_session")
        self.connection.execute("DELETE FROM ai_model_config")
        self.connection.commit()

    def get_db_path(self) -> Path:
        """获取数据库文件路径"""
        return storage_config_manager.get_database_path()


# 全局实例
# db - 临时数据库（员工组织数据）
db = Database()

# persistent_db - 持久化数据库（用户配置和聊天记录）
persistent_db = PersistentDatabase()