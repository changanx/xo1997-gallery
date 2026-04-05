"""
数据层模块
"""
from .database import Database, db
from .models.department import Department
from .models.employee import Employee
from .repositories.department_repository import DepartmentRepository
from .repositories.employee_repository import EmployeeRepository

__all__ = [
    "Database", "db",
    "Department",
    "Employee",
    "DepartmentRepository",
    "EmployeeRepository",
]
