"""
数据仓库补充测试
补充 DepartmentRepository 和 EmployeeRepository 的测试
"""
import pytest

from data.database import db
from data.models.department import Department
from data.models.employee import Employee
from data.repositories.department_repository import DepartmentRepository
from data.repositories.employee_repository import EmployeeRepository


class TestDepartmentRepositoryExtended:
    """DepartmentRepository 补充测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()
        self.repo = DepartmentRepository()

    def test_find_by_id(self):
        """测试按 ID 查找"""
        dept = Department(name="技术部", level=0)
        saved = self.repo.save(dept)

        found = self.repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == "技术部"

    def test_find_by_id_not_exist(self):
        """测试查找不存在的 ID"""
        found = self.repo.find_by_id(999)
        assert found is None

    def test_find_by_parent_none(self):
        """测试查找根部门（parent_id 为 None）"""
        # 创建根部门
        self.repo.save(Department(name="总公司", level=0, parent_id=None))
        self.repo.save(Department(name="技术部", level=1, parent_id=1))

        roots = self.repo.find_by_parent(None)
        assert len(roots) == 1
        assert roots[0].name == "总公司"

    def test_find_by_parent_with_id(self):
        """测试查找子部门"""
        # 创建部门层级
        root = self.repo.save(Department(name="总公司", level=0))
        tech = self.repo.save(Department(name="技术部", level=1, parent_id=root.id))
        self.repo.save(Department(name="前端组", level=2, parent_id=tech.id))
        self.repo.save(Department(name="后端组", level=2, parent_id=tech.id))

        children = self.repo.find_by_parent(tech.id)
        assert len(children) == 2

    def test_delete(self):
        """测试删除部门"""
        dept = self.repo.save(Department(name="待删除", level=0))

        assert self.repo.delete(dept.id) is True
        assert self.repo.find_by_id(dept.id) is None

    def test_delete_not_exist(self):
        """测试删除不存在的部门"""
        assert self.repo.delete(999) is False

    def test_get_tree_single_root(self):
        """测试单根部门树"""
        root = self.repo.save(Department(name="总公司", level=0))
        child = self.repo.save(Department(name="技术部", level=1, parent_id=root.id))

        tree = self.repo.get_tree()

        assert len(tree) == 1
        assert tree[0]['name'] == "总公司"
        assert len(tree[0]['children']) == 1
        assert tree[0]['children'][0]['name'] == "技术部"

    def test_get_tree_multiple_roots(self):
        """测试多根部门树"""
        self.repo.save(Department(name="公司A", level=0))
        self.repo.save(Department(name="公司B", level=0))

        tree = self.repo.get_tree()

        assert len(tree) == 2

    def test_get_tree_deep_nesting(self):
        """测试深层嵌套树"""
        d1 = self.repo.save(Department(name="L1", level=0))
        d2 = self.repo.save(Department(name="L2", level=1, parent_id=d1.id))
        d3 = self.repo.save(Department(name="L3", level=2, parent_id=d2.id))
        d4 = self.repo.save(Department(name="L4", level=3, parent_id=d3.id))

        tree = self.repo.get_tree()

        # 验证嵌套结构
        def find_deep(node, depth=0):
            if depth == 3:
                return node['name']
            if node['children']:
                return find_deep(node['children'][0], depth + 1)
            return None

        assert find_deep(tree[0]) == "L4"

    def test_save_all(self):
        """测试批量保存"""
        departments = [
            Department(name="部门1", level=0),
            Department(name="部门2", level=0),
            Department(name="部门3", level=0)
        ]

        saved = self.repo.save_all(departments)

        assert len(saved) == 3
        assert all(d.id is not None for d in saved)
        assert self.repo.count() == 3


class TestEmployeeRepositoryExtended:
    """EmployeeRepository 补充测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()
        self.repo = EmployeeRepository()

    def test_find_by_id(self):
        """测试按 ID 查找"""
        emp = Employee(name="张三", employee_number="E001")
        saved = self.repo.save(emp)

        found = self.repo.find_by_id(saved.id)
        assert found is not None
        assert found.name == "张三"

    def test_find_by_id_not_exist(self):
        """测试查找不存在的 ID"""
        found = self.repo.find_by_id(999)
        assert found is None

    def test_find_all(self):
        """测试获取所有员工"""
        self.repo.save(Employee(name="张三"))
        self.repo.save(Employee(name="李四"))

        all_emps = self.repo.find_all()
        assert len(all_emps) == 2

    def test_find_all_empty(self):
        """测试空数据库获取所有"""
        all_emps = self.repo.find_all()
        assert all_emps == []

    def test_delete(self):
        """测试删除员工"""
        emp = self.repo.save(Employee(name="待删除"))

        assert self.repo.delete(emp.id) is True
        assert self.repo.find_by_id(emp.id) is None

    def test_delete_not_exist(self):
        """测试删除不存在的员工"""
        assert self.repo.delete(999) is False

    def test_save_all(self):
        """测试批量保存"""
        employees = [
            Employee(name="员工1", employee_number="E001"),
            Employee(name="员工2", employee_number="E002"),
            Employee(name="员工3", employee_number="E003")
        ]

        saved = self.repo.save_all(employees)

        assert len(saved) == 3
        assert all(e.id is not None for e in saved)
        assert self.repo.count() == 3

    def test_get_stats_by_department(self):
        """测试按部门统计"""
        # 创建员工数据
        employees = [
            Employee(name="张三", department_level3="前端组", category="技术", rank="P5"),
            Employee(name="李四", department_level3="前端组", category="技术", rank="P5"),
            Employee(name="王五", department_level3="前端组", category="技术", rank="P6"),
            Employee(name="赵六", department_level3="后端组", category="技术", rank="P5"),
        ]
        self.repo.save_all(employees)

        stats = self.repo.get_stats_by_department()

        assert len(stats) == 3  # 前端P5, 前端P6, 后端P5

        # 查找前端组 P5 的统计
        frontend_p5 = next((s for s in stats if s[0] == "前端组" and s[2] == "P5"), None)
        assert frontend_p5 is not None
        assert frontend_p5[3] == 2  # 2 人

    def test_get_stats_by_department_empty(self):
        """测试空数据库统计"""
        stats = self.repo.get_stats_by_department()
        assert stats == []

    def test_get_stats_filters_null(self):
        """测试统计过滤空值"""
        # 创建不完整的员工数据
        employees = [
            Employee(name="完整", department_level3="组A", category="技术", rank="P5"),
            Employee(name="缺少部门", department_level3=None, category="技术", rank="P5"),
            Employee(name="缺少类别", department_level3="组A", category=None, rank="P5"),
            Employee(name="缺少职级", department_level3="组A", category="技术", rank=None),
        ]
        self.repo.save_all(employees)

        stats = self.repo.get_stats_by_department()

        # 只有完整数据的那条应该被统计
        assert len(stats) == 1


class TestDatabaseExtended:
    """Database 补充测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_transaction_context(self):
        """测试事务上下文管理"""
        # 数据库应该支持事务
        with db.connection:
            cursor = db.connection.execute(
                "INSERT INTO department (name, level) VALUES (?, ?)",
                ("测试部门", 0)
            )

        # 事务应该已提交
        cursor = db.connection.execute("SELECT COUNT(*) FROM department")
        assert cursor.fetchone()[0] == 1

    def test_connection_is_valid(self):
        """测试连接有效性"""
        assert db.connection is not None

        # 简单查询应该成功
        cursor = db.connection.execute("SELECT 1")
        assert cursor.fetchone()[0] == 1

    def test_clear_resets_all_tables(self):
        """测试清空重置所有表"""
        # 插入数据到各个表
        db.connection.execute(
            "INSERT INTO department (name, level) VALUES (?, ?)",
            ("部门", 0)
        )
        db.connection.execute(
            "INSERT INTO employee (name) VALUES (?)",
            ("员工",)
        )
        db.connection.commit()

        # 清空
        db.clear()

        # 验证所有表都被清空
        assert db.connection.execute("SELECT COUNT(*) FROM department").fetchone()[0] == 0
        assert db.connection.execute("SELECT COUNT(*) FROM employee").fetchone()[0] == 0

    def test_singleton(self):
        """测试单例模式"""
        from data.database import db as db2
        assert db is db2
