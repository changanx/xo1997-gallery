"""
员工数据仓库
"""
from typing import List, Optional, Tuple

from ..database import db
from ..models.employee import Employee


class EmployeeRepository:
    """员工数据仓库"""

    def find_all(self) -> List[Employee]:
        """获取所有员工"""
        cursor = db.connection.execute("SELECT * FROM employee ORDER BY id")
        return [Employee.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[Employee]:
        """根据 ID 查找"""
        cursor = db.connection.execute(
            "SELECT * FROM employee WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return Employee.from_row(row) if row else None

    def save(self, emp: Employee) -> Employee:
        """保存员工"""
        if emp.id is None:
            cursor = db.connection.execute(
                """
                INSERT INTO employee (name, employee_number, department_level1,
                    department_level2, department_level3, department_level4,
                    department_level5, rank, category)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (emp.name, emp.employee_number, emp.department_level1,
                 emp.department_level2, emp.department_level3, emp.department_level4,
                 emp.department_level5, emp.rank, emp.category)
            )
            emp.id = cursor.lastrowid
        else:
            db.connection.execute(
                """
                UPDATE employee SET name = ?, employee_number = ?,
                    department_level1 = ?, department_level2 = ?,
                    department_level3 = ?, department_level4 = ?,
                    department_level5 = ?, rank = ?, category = ?
                WHERE id = ?
                """,
                (emp.name, emp.employee_number, emp.department_level1,
                 emp.department_level2, emp.department_level3, emp.department_level4,
                 emp.department_level5, emp.rank, emp.category, emp.id)
            )
        db.connection.commit()
        return emp

    def save_all(self, employees: List[Employee]) -> List[Employee]:
        """批量保存员工"""
        for emp in employees:
            self.save(emp)
        return employees

    def delete(self, id: int) -> bool:
        """删除员工"""
        cursor = db.connection.execute("DELETE FROM employee WHERE id = ?", (id,))
        db.connection.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        """统计员工数量"""
        cursor = db.connection.execute("SELECT COUNT(*) FROM employee")
        return cursor.fetchone()[0]

    def get_stats_by_department(self) -> List[Tuple]:
        """获取按部门、类别、职级分组的人数统计"""
        cursor = db.connection.execute("""
            SELECT department_level3, category, rank, COUNT(*) as count
            FROM employee
            WHERE department_level3 IS NOT NULL
              AND category IS NOT NULL
              AND rank IS NOT NULL
            GROUP BY department_level3, category, rank
            ORDER BY department_level3, category, rank
        """)
        return cursor.fetchall()
