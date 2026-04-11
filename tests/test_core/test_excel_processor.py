"""
Excel 处理器测试
"""
import pytest
from pathlib import Path
import pandas as pd

from core.excel_processor import ExcelProcessor
from data.database import db


@pytest.fixture
def processor():
    """创建 Excel 处理器实例"""
    db.clear()  # 清空数据库
    return ExcelProcessor()


class TestExcelProcessor:
    """ExcelProcessor 测试"""

    def test_init(self, processor):
        """测试初始化"""
        assert processor.dept_repo is not None
        assert processor.emp_repo is not None

    def test_import_excel_success(self, processor, sample_excel_file):
        """测试成功导入 Excel"""
        success, message = processor.import_excel(str(sample_excel_file))

        assert success is True
        assert "导入成功" in message
        assert "5 个部门" in message
        assert "5 名员工" in message

    def test_import_excel_counts(self, processor, sample_excel_file):
        """测试导入后的计数"""
        processor.import_excel(str(sample_excel_file))

        assert processor.department_count == 5
        assert processor.employee_count == 5

    def test_import_excel_department_tree(self, processor, sample_excel_file):
        """测试导入后获取部门树"""
        processor.import_excel(str(sample_excel_file))

        tree = processor.get_department_tree()

        assert len(tree) == 1  # 一个根节点
        assert tree[0]['name'] == '总公司'
        assert len(tree[0]['children']) == 2  # 技术部和市场部

    def test_import_excel_employee_stats(self, processor, sample_excel_file):
        """测试导入后获取员工统计"""
        processor.import_excel(str(sample_excel_file))

        stats = processor.get_employee_stats()

        assert len(stats) > 0
        # stats 格式: (department, category, rank, count)
        for stat in stats:
            assert len(stat) == 4

    def test_import_excel_file_not_exist(self, processor):
        """测试文件不存在"""
        success, message = processor.import_excel("nonexistent.xlsx")

        assert success is False
        assert "不存在" in message

    def test_import_excel_invalid_file(self, processor, tmp_path):
        """测试无效文件格式"""
        invalid_file = tmp_path / "invalid.xlsx"
        invalid_file.write_text("not an excel file", encoding='utf-8')

        success, message = processor.import_excel(str(invalid_file))

        assert success is False
        assert "失败" in message

    def test_import_excel_missing_sheets(self, processor, tmp_path):
        """测试缺少必要工作表"""
        empty_excel = tmp_path / "empty.xlsx"
        with pd.ExcelWriter(empty_excel, engine='openpyxl') as writer:
            pd.DataFrame().to_excel(writer, sheet_name='other', index=False)

        success, message = processor.import_excel(str(empty_excel))

        # 应该成功但没有数据
        assert success is True
        assert "0 个部门" in message
        assert "0 名员工" in message

    def test_import_excel_clears_existing_data(self, processor, sample_excel_file, tmp_path):
        """测试导入会清空现有数据"""
        # 第一次导入
        processor.import_excel(str(sample_excel_file))
        assert processor.employee_count == 5

        # 创建一个新的 Excel 只有 1 个员工
        new_excel = tmp_path / "new.xlsx"
        emp_data = {
            'id': [1],
            'name': ['张三'],
            'employee_number': ['E001'],
            'department_level1': ['技术部'],
            'department_level2': [None],
            'department_level3': [None],
            'department_level4': [None],
            'department_level5': [None],
            'rank': ['P5'],
            'category': ['技术']
        }
        dept_data = {
            'id': [1],
            'parent_id': [None],
            'name': ['技术部'],
            'level': [0]
        }
        with pd.ExcelWriter(new_excel, engine='openpyxl') as writer:
            pd.DataFrame(dept_data).to_excel(writer, sheet_name='department', index=False)
            pd.DataFrame(emp_data).to_excel(writer, sheet_name='employee', index=False)

        # 第二次导入
        processor.import_excel(str(new_excel))

        # 数据应该被替换
        assert processor.employee_count == 1
        assert processor.department_count == 1


class TestExcelProcessorProperties:
    """ExcelProcessor 属性测试"""

    def test_department_count_empty(self, processor):
        """测试空数据库的部门计数"""
        assert processor.department_count == 0

    def test_employee_count_empty(self, processor):
        """测试空数据库的员工计数"""
        assert processor.employee_count == 0

    def test_department_count_after_import(self, processor, sample_excel_file):
        """测试导入后的部门计数"""
        processor.import_excel(str(sample_excel_file))
        assert processor.department_count == 5

    def test_employee_count_after_import(self, processor, sample_excel_file):
        """测试导入后的员工计数"""
        processor.import_excel(str(sample_excel_file))
        assert processor.employee_count == 5


class TestDepartmentTree:
    """部门树结构测试"""

    def test_get_department_tree_empty(self, processor):
        """测试空数据库的部门树"""
        tree = processor.get_department_tree()
        assert tree == []

    def test_get_department_tree_structure(self, processor, sample_excel_file):
        """测试部门树结构"""
        processor.import_excel(str(sample_excel_file))
        tree = processor.get_department_tree()

        # 验证树结构
        root = tree[0]
        assert root['name'] == '总公司'
        assert root['level'] == 0

        # 验证子节点
        children = root['children']
        assert len(children) == 2

        tech_dept = next((c for c in children if c['name'] == '技术部'), None)
        assert tech_dept is not None
        assert len(tech_dept['children']) == 2  # 前端组和后端组

    def test_get_department_tree_deep(self, processor, tmp_path):
        """测试深层部门树"""
        # 创建深层部门数据
        dept_data = {
            'id': [1, 2, 3, 4, 5],
            'parent_id': [None, 1, 2, 3, 4],
            'name': ['L1', 'L2', 'L3', 'L4', 'L5'],
            'level': [0, 1, 2, 3, 4]
        }
        emp_data = {
            'id': [1],
            'name': ['员工'],
            'employee_number': ['E001'],
            'department_level1': ['L1'],
            'department_level2': ['L2'],
            'department_level3': ['L3'],
            'department_level4': ['L4'],
            'department_level5': ['L5'],
            'rank': ['P5'],
            'category': ['技术']
        }

        deep_excel = tmp_path / "deep.xlsx"
        with pd.ExcelWriter(deep_excel, engine='openpyxl') as writer:
            pd.DataFrame(dept_data).to_excel(writer, sheet_name='department', index=False)
            pd.DataFrame(emp_data).to_excel(writer, sheet_name='employee', index=False)

        processor.import_excel(str(deep_excel))
        tree = processor.get_department_tree()

        # 验证 5 层嵌套
        def count_depth(node):
            if not node['children']:
                return 1
            return 1 + max(count_depth(c) for c in node['children'])

        assert count_depth(tree[0]) == 5


class TestEmployeeStats:
    """员工统计测试"""

    def test_get_employee_stats_empty(self, processor):
        """测试空数据库的员工统计"""
        stats = processor.get_employee_stats()
        assert stats == []

    def test_get_employee_stats_format(self, processor, sample_excel_file):
        """测试员工统计格式"""
        processor.import_excel(str(sample_excel_file))
        stats = processor.get_employee_stats()

        # 验证统计格式
        for stat in stats:
            assert len(stat) == 4
            department, category, rank, count = stat
            assert isinstance(department, str)
            assert isinstance(category, str)
            assert isinstance(rank, str)
            assert isinstance(count, int)
