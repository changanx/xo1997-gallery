"""
Excel 处理器
"""
from typing import Tuple, List
from pathlib import Path

import pandas as pd

from data.database import db
from data.repositories.department_repository import DepartmentRepository
from data.repositories.employee_repository import EmployeeRepository
from data.models.department import Department
from data.models.employee import Employee


class ExcelProcessor:
    """Excel 数据处理"""

    def __init__(self):
        self.dept_repo = DepartmentRepository()
        self.emp_repo = EmployeeRepository()

    def import_excel(self, excel_path: str) -> Tuple[bool, str]:
        """
        导入 Excel 数据

        Args:
            excel_path: Excel 文件路径

        Returns:
            (成功与否, 消息)
        """
        try:
            path = Path(excel_path)
            if not path.exists():
                return False, f"文件不存在: {excel_path}"

            xls = pd.ExcelFile(excel_path)

            # 清空现有数据
            db.clear()

            dept_count = 0
            emp_count = 0

            # 导入部门数据
            if 'department' in xls.sheet_names:
                dept_df = pd.read_excel(xls, sheet_name='department')
                departments = []
                for _, row in dept_df.iterrows():
                    dept = Department(
                        id=int(row['id']) if pd.notna(row.get('id')) else None,
                        parent_id=int(row['parent_id']) if pd.notna(row.get('parent_id')) else None,
                        name=str(row['name']) if pd.notna(row.get('name')) else "",
                        level=int(row['level']) if pd.notna(row.get('level')) else 0,
                    )
                    departments.append(dept)
                self.dept_repo.save_all(departments)
                dept_count = len(departments)

            # 导入员工数据
            if 'employee' in xls.sheet_names:
                emp_df = pd.read_excel(xls, sheet_name='employee')
                employees = []
                for _, row in emp_df.iterrows():
                    emp = Employee(
                        id=int(row['id']) if pd.notna(row.get('id')) else None,
                        name=str(row['name']) if pd.notna(row.get('name')) else "",
                        employee_number=str(row.get('employee_number', '')) if pd.notna(row.get('employee_number')) else "",
                        department_level1=str(row.get('department_level1', '')) if pd.notna(row.get('department_level1')) else "",
                        department_level2=str(row.get('department_level2', '')) if pd.notna(row.get('department_level2')) else "",
                        department_level3=str(row.get('department_level3', '')) if pd.notna(row.get('department_level3')) else "",
                        department_level4=str(row.get('department_level4', '')) if pd.notna(row.get('department_level4')) else "",
                        department_level5=str(row.get('department_level5', '')) if pd.notna(row.get('department_level5')) else "",
                        rank=str(row.get('rank', '')) if pd.notna(row.get('rank')) else "",
                        category=str(row.get('category', '')) if pd.notna(row.get('category')) else "",
                    )
                    employees.append(emp)
                self.emp_repo.save_all(employees)
                emp_count = len(employees)

            return True, f"导入成功：{dept_count} 个部门，{emp_count} 名员工"

        except Exception as e:
            return False, f"导入失败: {str(e)}"

    def get_department_tree(self) -> List[dict]:
        """获取部门树结构"""
        return self.dept_repo.get_tree()

    def get_employee_stats(self) -> List[Tuple]:
        """获取员工统计"""
        return self.emp_repo.get_stats_by_department()

    @property
    def department_count(self) -> int:
        """部门数量"""
        return self.dept_repo.count()

    @property
    def employee_count(self) -> int:
        """员工数量"""
        return self.emp_repo.count()
