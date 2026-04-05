"""
部门数据仓库
"""
from typing import List, Optional

from ..database import db
from ..models.department import Department


class DepartmentRepository:
    """部门数据仓库"""

    def find_all(self) -> List[Department]:
        """获取所有部门"""
        cursor = db.connection.execute(
            "SELECT * FROM department ORDER BY level, id"
        )
        return [Department.from_row(row) for row in cursor.fetchall()]

    def find_by_id(self, id: int) -> Optional[Department]:
        """根据 ID 查找"""
        cursor = db.connection.execute(
            "SELECT * FROM department WHERE id = ?", (id,)
        )
        row = cursor.fetchone()
        return Department.from_row(row) if row else None

    def find_by_parent(self, parent_id: Optional[int]) -> List[Department]:
        """根据父 ID 查找子部门"""
        if parent_id is None:
            cursor = db.connection.execute(
                "SELECT * FROM department WHERE parent_id IS NULL ORDER BY id"
            )
        else:
            cursor = db.connection.execute(
                "SELECT * FROM department WHERE parent_id = ? ORDER BY id", (parent_id,)
            )
        return [Department.from_row(row) for row in cursor.fetchall()]

    def save(self, dept: Department) -> Department:
        """保存部门"""
        if dept.id is None:
            cursor = db.connection.execute(
                "INSERT INTO department (parent_id, name, level) VALUES (?, ?, ?)",
                (dept.parent_id, dept.name, dept.level)
            )
            dept.id = cursor.lastrowid
        else:
            db.connection.execute(
                "UPDATE department SET parent_id = ?, name = ?, level = ? WHERE id = ?",
                (dept.parent_id, dept.name, dept.level, dept.id)
            )
        db.connection.commit()
        return dept

    def save_all(self, departments: List[Department]) -> List[Department]:
        """批量保存部门"""
        for dept in departments:
            self.save(dept)
        return departments

    def delete(self, id: int) -> bool:
        """删除部门"""
        cursor = db.connection.execute("DELETE FROM department WHERE id = ?", (id,))
        db.connection.commit()
        return cursor.rowcount > 0

    def count(self) -> int:
        """统计部门数量"""
        cursor = db.connection.execute("SELECT COUNT(*) FROM department")
        return cursor.fetchone()[0]

    def get_tree(self) -> List[dict]:
        """获取部门树结构"""
        departments = self.find_all()
        nodes = {d.id: {'id': d.id, 'parent_id': d.parent_id, 'name': d.name, 'level': d.level, 'children': []}
                 for d in departments}
        roots = []
        for d in departments:
            node = nodes[d.id]
            if d.parent_id is None:
                roots.append(node)
            else:
                parent = nodes.get(d.parent_id)
                if parent:
                    parent['children'].append(node)
        return roots
