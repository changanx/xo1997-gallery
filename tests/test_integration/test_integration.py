"""
集成测试
测试完整的工作流程
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from data.database import db
from core.excel_processor import ExcelProcessor
from core.ppt_generator import PPTGenerator


class TestExcelToPPTWorkflow:
    """Excel 导入到 PPT 生成的完整工作流测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_full_workflow(self, sample_excel_file, tmp_path):
        """测试完整的导入和生成流程"""
        # 1. 导入 Excel
        processor = ExcelProcessor()
        success, message = processor.import_excel(str(sample_excel_file))

        assert success is True
        assert processor.department_count == 5
        assert processor.employee_count == 5

        # 2. 获取部门树
        tree = processor.get_department_tree()
        assert len(tree) == 1
        assert tree[0]['name'] == '总公司'

        # 3. 获取员工统计
        stats = processor.get_employee_stats()
        assert len(stats) > 0

        # 4. 生成 PPT
        generator = PPTGenerator()
        output_path = tmp_path / "output.pptx"
        success, message = generator.generate(
            tree=tree,
            stats=stats,
            output_path=str(output_path)
        )

        assert success is True
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_workflow_with_empty_data(self, tmp_path):
        """测试空数据的工作流"""
        # 创建空 Excel
        import pandas as pd

        empty_excel = tmp_path / "empty.xlsx"
        with pd.ExcelWriter(empty_excel, engine='openpyxl') as writer:
            pd.DataFrame().to_excel(writer, sheet_name='department', index=False)
            pd.DataFrame().to_excel(writer, sheet_name='employee', index=False)

        # 导入
        processor = ExcelProcessor()
        success, message = processor.import_excel(str(empty_excel))

        assert success is True
        assert processor.department_count == 0
        assert processor.employee_count == 0

        # 生成 PPT
        tree = processor.get_department_tree()
        stats = processor.get_employee_stats()

        generator = PPTGenerator()
        output_path = tmp_path / "empty_output.pptx"
        success, message = generator.generate(
            tree=tree,
            stats=stats,
            output_path=str(output_path)
        )

        # 空数据也应该能生成 PPT
        assert success is True


class TestAIChatWorkflow:
    """AI 对话工作流测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_model_selection_and_chat(self):
        """测试模型选择和对话流程"""
        from core.model_manager import model_manager
        from data.models.ai_config import AIModelConfig
        from data.repositories.ai_config_repository import AIModelConfigRepository

        # 1. 创建模型配置
        repo = AIModelConfigRepository()
        config = AIModelConfig(
            name="测试模型",
            provider="openai",
            model_name="gpt-4o",
            api_key="test-key",
            is_default=True,
            is_enabled=True
        )
        saved = repo.save(config)

        # 2. 设置当前模型
        with patch('langchain_openai.ChatOpenAI') as MockChatOpenAI:
            mock_model = MagicMock()
            MockChatOpenAI.return_value = mock_model

            model_manager.set_current_model(saved)

            assert model_manager.get_current_model() == mock_model
            assert model_manager.get_current_config() == saved

    def test_chat_session_persistence(self):
        """测试会话持久化"""
        from data.models.ai_config import ChatSession, ChatMessage
        from data.repositories.ai_config_repository import (
            ChatSessionRepository, ChatMessageRepository
        )

        session_repo = ChatSessionRepository()
        message_repo = ChatMessageRepository()

        # 1. 创建会话
        session = ChatSession(title="测试会话")
        saved_session = session_repo.save(session)

        # 2. 添加消息
        user_msg = ChatMessage(
            session_id=saved_session.id,
            role="user",
            content="你好"
        )
        ai_msg = ChatMessage(
            session_id=saved_session.id,
            role="assistant",
            content="你好！有什么可以帮助你的吗？"
        )

        message_repo.save(user_msg)
        message_repo.save(ai_msg)

        # 3. 验证消息已保存
        messages = message_repo.find_by_session(saved_session.id)
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_tool_workflow(self, temp_work_dir):
        """测试工具调用工作流"""
        from core.model_manager import model_manager
        from core.tools.base import SecurityContext
        from core.tools import create_all_tools

        # 1. 创建测试文件
        test_file = temp_work_dir / "test.txt"
        test_file.write_text("Hello, World!", encoding='utf-8')

        # 2. 设置工作目录
        model_manager.set_work_directory(str(temp_work_dir))

        # 3. 验证工具已创建
        assert model_manager.has_tools() is True

        # 4. 测试工具执行
        result = model_manager._execute_tool("read_file", {"file_path": "test.txt"})
        assert result == "Hello, World!"


class TestEndToEndWorkflow:
    """端到端工作流测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_complete_hr_workflow(self, sample_excel_file, tmp_path):
        """测试完整的 HR 工具工作流"""
        # 场景：导入员工数据 -> 查看统计 -> 生成报告

        # 1. 导入数据
        processor = ExcelProcessor()
        success, message = processor.import_excel(str(sample_excel_file))
        assert success is True

        # 2. 获取部门统计
        tree = processor.get_department_tree()
        stats = processor.get_employee_stats()

        # 3. 验证数据完整性
        assert processor.department_count > 0
        assert processor.employee_count > 0

        # 4. 生成报告
        generator = PPTGenerator()
        report_path = tmp_path / "report.pptx"

        success, message = generator.generate(
            tree=tree,
            stats=stats,
            output_path=str(report_path)
        )

        assert success is True
        assert report_path.exists()

        # 5. 验证报告文件有效
        from pptx import Presentation
        prs = Presentation(str(report_path))
        assert len(prs.slides) > 0


class TestErrorHandling:
    """错误处理测试"""

    def setup_method(self):
        """每个测试前清空数据"""
        db.clear()

    def test_invalid_excel_handling(self, tmp_path):
        """测试无效 Excel 文件处理"""
        # 创建无效文件
        invalid_file = tmp_path / "invalid.xlsx"
        invalid_file.write_text("not an excel file", encoding='utf-8')

        processor = ExcelProcessor()
        success, message = processor.import_excel(str(invalid_file))

        assert success is False
        assert "失败" in message

    def test_missing_excel_file(self):
        """测试缺失 Excel 文件处理"""
        processor = ExcelProcessor()
        success, message = processor.import_excel("nonexistent.xlsx")

        assert success is False
        assert "不存在" in message

    def test_invalid_ppt_output_path(self):
        """测试无效 PPT 输出路径"""
        import platform

        # 使用真正无法写入的路径
        if platform.system() == "Windows":
            invalid_path = "Z:\\nonexistent_drive\\output.pptx"
        else:
            invalid_path = "/nonexistent_drive/output.pptx"

        generator = PPTGenerator()
        success, message = generator.generate(
            tree=[{'id': 1, 'name': 'Test', 'children': []}],
            stats=[],
            output_path=invalid_path
        )

        assert success is False
        assert "失败" in message or "不存在" in message

    def test_tool_execution_with_invalid_path(self, temp_work_dir):
        """测试工具执行无效路径"""
        from core.model_manager import model_manager

        model_manager.set_work_directory(str(temp_work_dir))

        # 尝试读取不存在的文件
        result = model_manager._execute_tool("read_file", {"file_path": "nonexistent.txt"})
        assert "错误" in result

        # 尝试访问工作目录外的文件
        result = model_manager._execute_tool("read_file", {"file_path": "../outside.txt"})
        assert "错误" in result
