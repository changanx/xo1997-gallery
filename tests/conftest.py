"""
测试配置
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from PySide6.QtWidgets import QApplication
import sys


@pytest.fixture(scope="session")
def qapp():
    """创建 QApplication 实例"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def qtbot(qapp, qtbot):
    """确保 qtbot 有 qapp 上下文"""
    return qtbot


@pytest.fixture
def temp_work_dir(tmp_path):
    """
    临时工作目录，用于测试文件/目录工具
    自动清理
    """
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    return work_dir


@pytest.fixture
def sample_excel_file(tmp_path):
    """
    创建示例 Excel 文件，包含 department 和 employee 两张表
    用于测试 ExcelProcessor
    """
    import pandas as pd

    excel_path = tmp_path / "sample.xlsx"

    # 创建部门数据
    dept_data = {
        'id': [1, 2, 3, 4, 5],
        'parent_id': [None, 1, 1, 2, 2],
        'name': ['总公司', '技术部', '市场部', '前端组', '后端组'],
        'level': [0, 1, 1, 2, 2]
    }

    # 创建员工数据
    emp_data = {
        'id': [1, 2, 3, 4, 5],
        'name': ['张三', '李四', '王五', '赵六', '钱七'],
        'employee_number': ['E001', 'E002', 'E003', 'E004', 'E005'],
        'department_level1': ['技术部', '技术部', '技术部', '市场部', '市场部'],
        'department_level2': ['前端组', '后端组', '后端组', None, None],
        'department_level3': [None, None, None, None, None],
        'department_level4': [None, None, None, None, None],
        'department_level5': [None, None, None, None, None],
        'rank': ['P5', 'P6', 'P7', 'P5', 'P6'],
        'category': ['技术', '技术', '技术', '市场', '市场']
    }

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        pd.DataFrame(dept_data).to_excel(writer, sheet_name='department', index=False)
        pd.DataFrame(emp_data).to_excel(writer, sheet_name='employee', index=False)

    return excel_path


@pytest.fixture
def sample_department_tree():
    """
    示例部门树结构数据
    返回字典列表，每个字典包含 id, parent_id, name, level
    """
    return [
        {'id': 1, 'parent_id': None, 'name': '总公司', 'level': 0},
        {'id': 2, 'parent_id': 1, 'name': '技术部', 'level': 1},
        {'id': 3, 'parent_id': 1, 'name': '市场部', 'level': 1},
        {'id': 4, 'parent_id': 2, 'name': '前端组', 'level': 2},
        {'id': 5, 'parent_id': 2, 'name': '后端组', 'level': 2},
    ]


@pytest.fixture
def sample_employees():
    """
    示例员工数据
    返回字典列表
    """
    return [
        {'id': 1, 'name': '张三', 'employee_number': 'E001',
         'department_level1': '技术部', 'department_level2': '前端组',
         'rank': 'P5', 'category': '技术'},
        {'id': 2, 'name': '李四', 'employee_number': 'E002',
         'department_level1': '技术部', 'department_level2': '后端组',
         'rank': 'P6', 'category': '技术'},
        {'id': 3, 'name': '王五', 'employee_number': 'E003',
         'department_level1': '市场部', 'department_level2': None,
         'rank': 'P5', 'category': '市场'},
    ]


@pytest.fixture
def sample_ai_config():
    """
    示例 AI 模型配置
    """
    from data.models.ai_config import AIModelConfig
    return AIModelConfig(
        id=1,
        name="测试模型",
        provider="openai",
        model_name="gpt-4o",
        api_key="test-api-key",
        base_url="https://api.openai.com/v1",
        temperature=0.7,
        max_tokens=2048,
        is_default=True,
        is_enabled=True
    )


@pytest.fixture
def mock_chat_model():
    """
    Mock LangChain 聊天模型
    用于测试 ModelManager 的对话功能
    """
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessageChunk

    model = MagicMock()

    # 默认流式响应
    def mock_stream(messages):
        chunks = ["你好", "！这", "是测试", "响应。"]
        for chunk in chunks:
            yield AIMessageChunk(content=chunk)

    model.stream = mock_stream
    model.bind_tools = MagicMock(return_value=model)

    return model


@pytest.fixture
def mock_chat_model_with_tools():
    """
    Mock LangChain 聊天模型，支持工具调用
    """
    from unittest.mock import MagicMock
    from langchain_core.messages import AIMessageChunk

    model = MagicMock()

    # 模拟工具调用响应
    def mock_stream(messages):
        # 先返回内容
        yield AIMessageChunk(content="我来帮你读取文件。")
        # 然后返回工具调用
        tool_call_chunk = MagicMock()
        tool_call_chunk.tool_call_chunks = [{
            'id': 'call_123',
            'name': 'read_file',
            'args': '{"file_path": "test.txt"}',
            'index': 0
        }]
        yield tool_call_chunk

    model.stream = mock_stream
    model.bind_tools = MagicMock(return_value=model)

    return model
