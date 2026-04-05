"""
员工数据模型
"""
from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Employee:
    """员工数据模型"""
    id: Optional[int] = None
    name: str = ""
    employee_number: str = ""
    department_level1: str = ""
    department_level2: str = ""
    department_level3: str = ""
    department_level4: str = ""
    department_level5: str = ""
    rank: str = ""
    category: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'Employee':
        """从数据库行创建实例"""
        return cls(
            id=row['id'],
            name=row['name'] or "",
            employee_number=row['employee_number'] or "",
            department_level1=row['department_level1'] or "",
            department_level2=row['department_level2'] or "",
            department_level3=row['department_level3'] or "",
            department_level4=row['department_level4'] or "",
            department_level5=row['department_level5'] or "",
            rank=row['rank'] or "",
            category=row['category'] or "",
        )
