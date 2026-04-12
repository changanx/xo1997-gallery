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
from app.common.logger import get_logger

logger = get_logger()

# 必需的列名定义
REQUIRED_DEPT_COLUMNS = ['id', 'parent_id', 'name', 'level']
REQUIRED_EMP_COLUMNS = ['id', 'name']


class ExcelProcessor:
    """Excel 数据处理"""

    def __init__(self):
        self.dept_repo = DepartmentRepository()
        self.emp_repo = EmployeeRepository()

    def _validate_columns(self, df: pd.DataFrame, required: List[str], sheet_name: str) -> Tuple[bool, str]:
        """
        验证 DataFrame 是否包含必需的列

        Args:
            df: DataFrame
            required: 必需列名列表
            sheet_name: 工作表名称（用于错误消息）

        Returns:
            (是否有效, 错误消息)
        """
        # 空数据（0 行）是允许的
        if df.empty:
            return True, ""

        # 检查缺失的列
        df_columns = set(df.columns.str.lower())
        missing = [col for col in required if col.lower() not in df_columns]

        if missing:
            available = list(df.columns)
            return False, f"工作表 '{sheet_name}' 缺少必需列: {', '.join(missing)}\n可用列: {', '.join(available)}"

        return True, ""

    def import_excel(self, excel_path: str) -> Tuple[bool, str]:
        """
        导入 Excel 数据

        Args:
            excel_path: Excel 文件路径

        Returns:
            (成功与否, 消息)
        """
        logger.info("开始导入 Excel", extra={"file": excel_path})

        try:
            path = Path(excel_path)
            if not path.exists():
                logger.warning("Excel 文件不存在", extra={"file": excel_path})
                return False, f"文件不存在: {excel_path}"

            xls = pd.ExcelFile(excel_path)
            logger.debug("Excel 文件打开成功", extra={"sheets": xls.sheet_names})

            dept_count = 0
            emp_count = 0

            # 使用事务保护整个导入过程
            with db.transaction():
                # 清空现有数据
                db.connection.execute("DELETE FROM employee")
                db.connection.execute("DELETE FROM department")
                logger.debug("已清空现有数据")

                # 导入部门数据
                if 'department' in xls.sheet_names:
                    dept_df = pd.read_excel(xls, sheet_name='department')

                    # 验证必需列
                    is_valid, error_msg = self._validate_columns(dept_df, REQUIRED_DEPT_COLUMNS, 'department')
                    if not is_valid:
                        logger.warning("部门数据列验证失败", extra={"error": error_msg})
                        return False, error_msg

                    # 标准化列名为小写（仅在列名是字符串时）
                    if not dept_df.empty and hasattr(dept_df.columns, 'str'):
                        dept_df.columns = dept_df.columns.str.lower()

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
                    logger.info("部门数据导入完成", extra={"count": dept_count})

                # 导入员工数据
                if 'employee' in xls.sheet_names:
                    emp_df = pd.read_excel(xls, sheet_name='employee')

                    # 验证必需列
                    is_valid, error_msg = self._validate_columns(emp_df, REQUIRED_EMP_COLUMNS, 'employee')
                    if not is_valid:
                        logger.warning("员工数据列验证失败", extra={"error": error_msg})
                        return False, error_msg

                    # 标准化列名为小写（仅在列名是字符串时）
                    if not emp_df.empty and hasattr(emp_df.columns, 'str'):
                        emp_df.columns = emp_df.columns.str.lower()

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
                    logger.info("员工数据导入完成", extra={"count": emp_count})

            logger.info("Excel 导入成功", extra={"departments": dept_count, "employees": emp_count})
            return True, f"导入成功：{dept_count} 个部门，{emp_count} 名员工"

        except Exception as e:
            logger.error("Excel 导入失败", extra={"error": str(e), "file": excel_path})
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
