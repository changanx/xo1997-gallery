"""
Database 测试
"""
import pytest

from data.database import Database, db


class TestDatabase:

    def test_singleton(self):
        """测试单例模式"""
        db1 = Database()
        db2 = Database()

        assert db1 is db2

    def test_connection(self):
        """测试连接获取"""
        conn = db.connection

        assert conn is not None

    def test_schema_initialized(self):
        """测试 Schema 初始化"""
        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = [row[0] for row in cursor.fetchall()]

        assert 'department' in tables
        assert 'employee' in tables

    def test_clear(self):
        """测试清空数据"""
        # 插入测试数据
        db.connection.execute("INSERT INTO department (name, level) VALUES ('测试', 0)")
        db.connection.commit()

        # 清空
        db.clear()

        # 验证
        cursor = db.connection.execute("SELECT COUNT(*) FROM department")
        assert cursor.fetchone()[0] == 0
