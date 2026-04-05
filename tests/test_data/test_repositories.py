"""
Repository 测试
"""
import pytest

from data.database import db
from data.models.department import Department
from data.models.employee import Employee
from data.repositories.department_repository import DepartmentRepository
from data.repositories.employee_repository import EmployeeRepository


class TestDepartmentRepository:

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_save(self):
        """测试保存部门"""
        repo = DepartmentRepository()
        dept = Department(name="技术部", level=0)

        saved = repo.save(dept)

        assert saved.id is not None
        assert saved.name == "技术部"

    def test_find_all(self):
        """测试查找所有"""
        repo = DepartmentRepository()
        repo.save(Department(name="技术部", level=0))
        repo.save(Department(name="产品部", level=0))

        all_depts = repo.find_all()

        assert len(all_depts) == 2

    def test_count(self):
        """测试计数"""
        repo = DepartmentRepository()
        repo.save(Department(name="技术部", level=0))
        repo.save(Department(name="产品部", level=0))

        assert repo.count() == 2


class TestEmployeeRepository:

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_save(self):
        """测试保存员工"""
        repo = EmployeeRepository()
        emp = Employee(name="张三", rank="21", category="技术")

        saved = repo.save(emp)

        assert saved.id is not None
        assert saved.name == "张三"

    def test_count(self):
        """测试计数"""
        repo = EmployeeRepository()
        repo.save(Employee(name="张三"))
        repo.save(Employee(name="李四"))

        assert repo.count() == 2
