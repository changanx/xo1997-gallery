"""
测试辅助工具
提供快速创建测试数据的辅助方法
"""
from typing import Optional, List, Dict, Any
from pathlib import Path


class DataHelper:
    """数据模型测试辅助类"""

    @staticmethod
    def create_department(
        id: Optional[int] = None,
        parent_id: Optional[int] = None,
        name: str = "测试部门",
        level: int = 0
    ) -> Dict[str, Any]:
        """创建部门数据字典"""
        return {
            'id': id,
            'parent_id': parent_id,
            'name': name,
            'level': level
        }

    @staticmethod
    def create_employee(
        id: Optional[int] = None,
        name: str = "测试员工",
        employee_number: str = "E001",
        department_level1: str = "技术部",
        department_level2: Optional[str] = None,
        department_level3: Optional[str] = None,
        department_level4: Optional[str] = None,
        department_level5: Optional[str] = None,
        rank: str = "P5",
        category: str = "技术"
    ) -> Dict[str, Any]:
        """创建员工数据字典"""
        return {
            'id': id,
            'name': name,
            'employee_number': employee_number,
            'department_level1': department_level1,
            'department_level2': department_level2,
            'department_level3': department_level3,
            'department_level4': department_level4,
            'department_level5': department_level5,
            'rank': rank,
            'category': category
        }

    @staticmethod
    def create_ai_config(
        id: Optional[int] = None,
        name: str = "测试配置",
        provider: str = "openai",
        model_name: str = "gpt-4o",
        api_key: str = "test-key",
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        is_default: bool = False,
        is_enabled: bool = True,
        extra_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建 AI 配置数据字典"""
        return {
            'id': id,
            'name': name,
            'provider': provider,
            'model_name': model_name,
            'api_key': api_key,
            'base_url': base_url,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'is_default': is_default,
            'is_enabled': is_enabled,
            'extra_params': extra_params or {}
        }

    @staticmethod
    def create_chat_session(
        id: Optional[int] = None,
        title: str = "测试会话",
        model_config_id: int = 1,
        created_at: str = "",
        updated_at: str = ""
    ) -> Dict[str, Any]:
        """创建聊天会话数据字典"""
        return {
            'id': id,
            'title': title,
            'model_config_id': model_config_id,
            'created_at': created_at,
            'updated_at': updated_at
        }

    @staticmethod
    def create_chat_message(
        id: Optional[int] = None,
        session_id: int = 1,
        role: str = "user",
        content: str = "测试消息",
        created_at: str = ""
    ) -> Dict[str, Any]:
        """创建聊天消息数据字典"""
        return {
            'id': id,
            'session_id': session_id,
            'role': role,
            'content': content,
            'created_at': created_at
        }


class FileHelper:
    """文件测试辅助类"""

    @staticmethod
    def create_file(directory: Path, filename: str, content: str = "test content") -> Path:
        """在指定目录创建文件"""
        file_path = directory / filename
        file_path.write_text(content, encoding='utf-8')
        return file_path

    @staticmethod
    def create_directory(directory: Path, dirname: str) -> Path:
        """在指定目录创建子目录"""
        dir_path = directory / dirname
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def create_nested_structure(base_dir: Path) -> Dict[str, Path]:
        """创建嵌套目录结构，返回所有创建的路径"""
        paths = {}
        paths['dir1'] = FileHelper.create_directory(base_dir, "dir1")
        paths['dir2'] = FileHelper.create_directory(base_dir, "dir2")
        paths['nested_dir'] = FileHelper.create_directory(paths['dir1'], "nested")
        paths['file1'] = FileHelper.create_file(base_dir, "file1.txt", "content 1")
        paths['file2'] = FileHelper.create_file(paths['dir1'], "file2.txt", "content 2")
        paths['file3'] = FileHelper.create_file(paths['nested_dir'], "file3.txt", "content 3")
        return paths


class SQLiteHelper:
    """SQLite 测试辅助类"""

    @staticmethod
    def create_row(data: Dict[str, Any], columns: List[str]) -> object:
        """
        创建模拟的 sqlite3.Row 对象

        Args:
            data: 数据字典
            columns: 列名列表（用于确定顺序）

        Returns:
            模拟的 Row 对象，支持通过列名索引
        """
        class MockRow:
            def __init__(self, data, columns):
                self._data = data
                self._columns = columns

            def __getitem__(self, key):
                if isinstance(key, str):
                    return self._data.get(key)
                elif isinstance(key, int):
                    return self._data.get(self._columns[key])
                return None

            def keys(self):
                return self._columns

            def __repr__(self):
                return f"MockRow({self._data})"

        return MockRow(data, columns)

    @staticmethod
    def create_department_row(
        id: int = 1,
        parent_id: Optional[int] = None,
        name: str = "测试部门",
        level: int = 0
    ) -> object:
        """创建部门 Row"""
        data = {'id': id, 'parent_id': parent_id, 'name': name, 'level': level}
        return SQLiteHelper.create_row(data, ['id', 'parent_id', 'name', 'level'])

    @staticmethod
    def create_employee_row(
        id: int = 1,
        name: str = "测试员工",
        employee_number: str = "E001",
        department_level1: str = "技术部",
        **kwargs
    ) -> object:
        """创建员工 Row"""
        data = {
            'id': id,
            'name': name,
            'employee_number': employee_number,
            'department_level1': department_level1,
            'department_level2': kwargs.get('department_level2'),
            'department_level3': kwargs.get('department_level3'),
            'department_level4': kwargs.get('department_level4'),
            'department_level5': kwargs.get('department_level5'),
            'rank': kwargs.get('rank', 'P5'),
            'category': kwargs.get('category', '技术')
        }
        columns = ['id', 'name', 'employee_number',
                   'department_level1', 'department_level2', 'department_level3',
                   'department_level4', 'department_level5', 'rank', 'category']
        return SQLiteHelper.create_row(data, columns)

    @staticmethod
    def create_ai_config_row(
        id: int = 1,
        name: str = "测试配置",
        provider: str = "openai",
        model_name: str = "gpt-4o",
        **kwargs
    ) -> object:
        """创建 AI 配置 Row"""
        import json
        extra_params = kwargs.get('extra_params', {})
        data = {
            'id': id,
            'name': name,
            'provider': provider,
            'model_name': model_name,
            'api_key': kwargs.get('api_key', 'test-key'),
            'base_url': kwargs.get('base_url', ''),
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 2048),
            'extra_params': json.dumps(extra_params) if extra_params else None,
            'is_default': kwargs.get('is_default', 0),
            'is_enabled': kwargs.get('is_enabled', 1)
        }
        columns = ['id', 'name', 'provider', 'model_name', 'api_key', 'base_url',
                   'temperature', 'max_tokens', 'extra_params', 'is_default', 'is_enabled']
        return SQLiteHelper.create_row(data, columns)
