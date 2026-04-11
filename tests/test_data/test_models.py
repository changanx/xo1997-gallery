"""
数据模型测试
测试所有数据模型的 from_row 方法
"""
import pytest
import json

from data.models.department import Department
from data.models.employee import Employee
from data.models.ai_config import AIModelConfig, ChatMessage, ChatSession
from tests.helpers import SQLiteHelper


class TestDepartment:
    """Department 模型测试"""

    def test_from_row_basic(self):
        """测试基本解析"""
        row = SQLiteHelper.create_department_row(
            id=1,
            parent_id=None,
            name="技术部",
            level=0
        )

        dept = Department.from_row(row)

        assert dept.id == 1
        assert dept.parent_id is None
        assert dept.name == "技术部"
        assert dept.level == 0

    def test_from_row_with_parent(self):
        """测试带父部门的解析"""
        row = SQLiteHelper.create_department_row(
            id=2,
            parent_id=1,
            name="前端组",
            level=1
        )

        dept = Department.from_row(row)

        assert dept.id == 2
        assert dept.parent_id == 1
        assert dept.level == 1

    def test_from_row_empty_name(self):
        """测试空名称处理"""
        row = SQLiteHelper.create_department_row(
            id=1,
            name=""
        )

        dept = Department.from_row(row)
        assert dept.name == ""


class TestEmployee:
    """Employee 模型测试"""

    def test_from_row_basic(self):
        """测试基本解析"""
        row = SQLiteHelper.create_employee_row(
            id=1,
            name="张三",
            employee_number="E001",
            department_level1="技术部"
        )

        emp = Employee.from_row(row)

        assert emp.id == 1
        assert emp.name == "张三"
        assert emp.employee_number == "E001"
        assert emp.department_level1 == "技术部"

    def test_from_row_full_departments(self):
        """测试完整部门层级"""
        row = SQLiteHelper.create_employee_row(
            id=1,
            name="员工",
            department_level1="总公司",
            department_level2="技术部",
            department_level3="开发组",
            department_level4="前端组",
            department_level5="React组"
        )

        emp = Employee.from_row(row)

        assert emp.department_level1 == "总公司"
        assert emp.department_level2 == "技术部"
        assert emp.department_level3 == "开发组"
        assert emp.department_level4 == "前端组"
        assert emp.department_level5 == "React组"

    def test_from_row_with_rank_and_category(self):
        """测试职级和类别"""
        row = SQLiteHelper.create_employee_row(
            id=1,
            name="员工",
            rank="P7",
            category="技术"
        )

        emp = Employee.from_row(row)
        assert emp.rank == "P7"
        assert emp.category == "技术"


class TestAIModelConfig:
    """AIModelConfig 模型测试"""

    def test_from_row_basic(self):
        """测试基本解析"""
        row = SQLiteHelper.create_ai_config_row(
            id=1,
            name="测试配置",
            provider="openai",
            model_name="gpt-4o"
        )

        config = AIModelConfig.from_row(row)

        assert config.id == 1
        assert config.name == "测试配置"
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o"

    def test_from_row_with_extra_params(self):
        """测试带额外参数"""
        row = SQLiteHelper.create_ai_config_row(
            id=1,
            extra_params={"top_p": 0.9, "frequency_penalty": 0.5}
        )

        config = AIModelConfig.from_row(row)

        assert config.extra_params["top_p"] == 0.9
        assert config.extra_params["frequency_penalty"] == 0.5

    def test_from_row_invalid_json_extra_params(self):
        """测试无效 JSON 额外参数"""
        row = SQLiteHelper.create_ai_config_row(id=1)
        # 直接设置无效 JSON
        row._data['extra_params'] = "not valid json"

        config = AIModelConfig.from_row(row)

        # 无效 JSON 应该返回空字典
        assert config.extra_params == {}

    def test_to_dict(self):
        """测试序列化"""
        config = AIModelConfig(
            id=1,
            name="测试",
            provider="openai",
            model_name="gpt-4o",
            api_key="key",
            base_url="url",
            temperature=0.7,
            max_tokens=2048,
            extra_params={"top_p": 0.9},
            is_default=True,
            is_enabled=True
        )

        d = config.to_dict()

        assert d['id'] == 1
        assert d['name'] == "测试"
        assert d['provider'] == "openai"
        assert d['extra_params'] == {"top_p": 0.9}

    def test_from_row_boolean_fields(self):
        """测试布尔字段"""
        row = SQLiteHelper.create_ai_config_row(
            id=1,
            is_default=1,
            is_enabled=0
        )

        config = AIModelConfig.from_row(row)

        assert config.is_default is True
        assert config.is_enabled is False


class TestChatSession:
    """ChatSession 模型测试"""

    def test_from_row_basic(self):
        """测试基本解析"""
        data = {
            'id': 1,
            'title': '测试会话',
            'model_config_id': 2,
            'created_at': '2024-01-01 00:00:00',
            'updated_at': '2024-01-01 01:00:00'
        }
        row = SQLiteHelper.create_row(data, ['id', 'title', 'model_config_id', 'created_at', 'updated_at'])

        session = ChatSession.from_row(row)

        assert session.id == 1
        assert session.title == '测试会话'
        assert session.model_config_id == 2

    def test_from_row_default_title(self):
        """测试默认标题"""
        data = {
            'id': 1,
            'title': None,
            'model_config_id': 0,
            'created_at': '',
            'updated_at': ''
        }
        row = SQLiteHelper.create_row(data, ['id', 'title', 'model_config_id', 'created_at', 'updated_at'])

        session = ChatSession.from_row(row)

        assert session.title == "新对话"


class TestChatMessage:
    """ChatMessage 模型测试"""

    def test_from_row_basic(self):
        """测试基本解析"""
        data = {
            'id': 1,
            'session_id': 2,
            'role': 'user',
            'content': '你好',
            'created_at': '2024-01-01 00:00:00'
        }
        row = SQLiteHelper.create_row(data, ['id', 'session_id', 'role', 'content', 'created_at'])

        msg = ChatMessage.from_row(row)

        assert msg.id == 1
        assert msg.session_id == 2
        assert msg.role == 'user'
        assert msg.content == '你好'

    def test_from_row_assistant_message(self):
        """测试助手消息"""
        data = {
            'id': 1,
            'session_id': 1,
            'role': 'assistant',
            'content': '你好！有什么可以帮助你的吗？',
            'created_at': '2024-01-01 00:00:01'
        }
        row = SQLiteHelper.create_row(data, ['id', 'session_id', 'role', 'content', 'created_at'])

        msg = ChatMessage.from_row(row)

        assert msg.role == 'assistant'

    def test_from_row_empty_content(self):
        """测试空内容"""
        data = {
            'id': 1,
            'session_id': 1,
            'role': 'user',
            'content': None,
            'created_at': ''
        }
        row = SQLiteHelper.create_row(data, ['id', 'session_id', 'role', 'content', 'created_at'])

        msg = ChatMessage.from_row(row)

        assert msg.content == ""
