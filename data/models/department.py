"""
部门数据模型
"""
from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Department:
    """部门数据模型"""
    id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str = ""
    level: int = 0

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Department':
        """从数据库行创建实例"""
        return cls(
            id=row['id'],
            parent_id=row['parent_id'],
            name=row['name'] or "",
            level=row['level'] or 0,
        )
