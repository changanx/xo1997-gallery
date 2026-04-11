"""
目录工具测试
测试目录操作工具的所有功能
"""
import pytest
from pathlib import Path

from core.tools.base import SecurityContext
from core.tools.directory_tools import create_directory_tools


@pytest.fixture
def dir_tools(temp_work_dir):
    """创建目录工具实例"""
    security = SecurityContext(str(temp_work_dir))
    tools = create_directory_tools(security)
    return {tool.name: tool for tool in tools}


class TestListDirectory:
    """list_directory 工具测试"""

    def test_list_directory_success(self, dir_tools, temp_work_dir):
        """测试成功列出目录"""
        # 创建一些文件和目录
        (temp_work_dir / "file1.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "file2.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "subdir").mkdir()

        result = dir_tools['list_directory'].func(".")

        assert "目录: ." in result
        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "subdir" in result

    def test_list_directory_empty(self, dir_tools, temp_work_dir):
        """测试空目录"""
        result = dir_tools['list_directory'].func(".")
        assert "目录为空" in result

    def test_list_directory_not_exist(self, dir_tools):
        """测试目录不存在"""
        result = dir_tools['list_directory'].func("nonexistent")
        assert "错误" in result
        assert "不存在" in result

    def test_list_directory_is_file(self, dir_tools, temp_work_dir):
        """测试列出文件（应该失败）"""
        test_file = temp_work_dir / "file.txt"
        test_file.write_text("content", encoding='utf-8')

        result = dir_tools['list_directory'].func("file.txt")
        assert "错误" in result
        assert "不是目录" in result

    def test_list_directory_nested(self, dir_tools, temp_work_dir):
        """测试列出嵌套目录"""
        nested_dir = temp_work_dir / "a" / "b"
        nested_dir.mkdir(parents=True)
        (nested_dir / "file.txt").write_text("content", encoding='utf-8')

        result = dir_tools['list_directory'].func("a/b")
        assert "file.txt" in result

    def test_list_directory_outside_workdir(self, dir_tools):
        """测试越界访问"""
        result = dir_tools['list_directory'].func("..")
        assert "错误" in result
        assert "不允许访问" in result


class TestCreateDirectory:
    """create_directory 工具测试"""

    def test_create_directory_success(self, dir_tools, temp_work_dir):
        """测试成功创建目录"""
        result = dir_tools['create_directory'].func("newdir")
        assert "成功" in result

        new_dir = temp_work_dir / "newdir"
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_directory_nested(self, dir_tools, temp_work_dir):
        """测试创建嵌套目录"""
        result = dir_tools['create_directory'].func("a/b/c/d")
        assert "成功" in result

        nested_dir = temp_work_dir / "a" / "b" / "c" / "d"
        assert nested_dir.exists()

    def test_create_directory_already_exists(self, dir_tools, temp_work_dir):
        """测试目录已存在"""
        dir_path = temp_work_dir / "existing"
        dir_path.mkdir()

        result = dir_tools['create_directory'].func("existing")
        assert "已存在" in result

    def test_create_directory_outside_workdir(self, dir_tools):
        """测试越界创建"""
        result = dir_tools['create_directory'].func("../outside")
        assert "错误" in result
        assert "不允许访问" in result


class TestDeleteDirectory:
    """delete_directory 工具测试"""

    def test_delete_directory_success(self, dir_tools, temp_work_dir):
        """测试成功删除空目录"""
        dir_path = temp_work_dir / "to_delete"
        dir_path.mkdir()

        result = dir_tools['delete_directory'].func("to_delete")
        assert "成功" in result
        assert not dir_path.exists()

    def test_delete_directory_not_empty_no_force(self, dir_tools, temp_work_dir):
        """测试删除非空目录（不强制）"""
        dir_path = temp_work_dir / "nonempty"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content", encoding='utf-8')

        result = dir_tools['delete_directory'].func("nonempty", force=False)
        # Windows 下错误消息可能不同
        assert "失败" in result or "错误" in result or "不是空" in result or "not empty" in result.lower()

    def test_delete_directory_force(self, dir_tools, temp_work_dir):
        """测试强制删除非空目录"""
        dir_path = temp_work_dir / "nonempty"
        dir_path.mkdir()
        (dir_path / "file.txt").write_text("content", encoding='utf-8')

        result = dir_tools['delete_directory'].func("nonempty", force=True)
        assert "成功" in result
        assert not dir_path.exists()

    def test_delete_directory_not_exist(self, dir_tools):
        """测试删除不存在的目录"""
        result = dir_tools['delete_directory'].func("nonexistent")
        assert "错误" in result
        assert "不存在" in result

    def test_delete_directory_is_file(self, dir_tools, temp_work_dir):
        """测试删除文件（应该失败）"""
        test_file = temp_work_dir / "file.txt"
        test_file.write_text("content", encoding='utf-8')

        result = dir_tools['delete_directory'].func("file.txt")
        assert "错误" in result
        assert "不是目录" in result

    def test_delete_directory_work_directory_itself(self, dir_tools):
        """测试删除工作目录本身（应该失败）"""
        result = dir_tools['delete_directory'].func(".")
        assert "错误" in result
        assert "不允许删除工作目录本身" in result

    def test_delete_directory_outside_workdir(self, dir_tools):
        """测试越界删除"""
        result = dir_tools['delete_directory'].func("../outside")
        assert "错误" in result

    def test_delete_nested_directory_with_content(self, dir_tools, temp_work_dir):
        """测试删除带内容的嵌套目录"""
        nested_dir = temp_work_dir / "a" / "b" / "c"
        nested_dir.mkdir(parents=True)
        (nested_dir / "file1.txt").write_text("content1", encoding='utf-8')
        (nested_dir / "file2.txt").write_text("content2", encoding='utf-8')

        result = dir_tools['delete_directory'].func("a", force=True)
        assert "成功" in result
        assert not (temp_work_dir / "a").exists()


class TestSearchFiles:
    """search_files 工具测试"""

    def test_search_files_by_extension(self, dir_tools, temp_work_dir):
        """测试按扩展名搜索"""
        (temp_work_dir / "file1.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "file2.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "file3.py").write_text("code", encoding='utf-8')

        result = dir_tools['search_files'].func("*.txt")

        assert "file1.txt" in result
        assert "file2.txt" in result
        assert "file3.py" not in result

    def test_search_files_by_prefix(self, dir_tools, temp_work_dir):
        """测试按前缀搜索"""
        (temp_work_dir / "test_file.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "test_dir").mkdir()
        (temp_work_dir / "other.txt").write_text("content", encoding='utf-8')

        result = dir_tools['search_files'].func("test*")

        assert "test_file.txt" in result
        assert "test_dir" in result
        assert "other.txt" not in result

    def test_search_files_no_match(self, dir_tools, temp_work_dir):
        """测试没有匹配"""
        (temp_work_dir / "file.txt").write_text("content", encoding='utf-8')

        result = dir_tools['search_files'].func("*.py")
        assert "没有找到" in result

    def test_search_files_in_subdirectory(self, dir_tools, temp_work_dir):
        """测试在子目录中搜索"""
        subdir = temp_work_dir / "subdir"
        subdir.mkdir()
        (subdir / "file.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "file.txt").write_text("content", encoding='utf-8')

        result = dir_tools['search_files'].func("*.txt", "subdir")

        # 路径分隔符可能是 / 或 \
        assert "file.txt" in result
        assert "subdir" in result

    def test_search_files_directory_not_exist(self, dir_tools):
        """测试目录不存在"""
        result = dir_tools['search_files'].func("*.txt", "nonexistent")
        assert "错误" in result


class TestTreeDirectory:
    """tree_directory 工具测试"""

    def test_tree_directory_simple(self, dir_tools, temp_work_dir):
        """测试简单目录树"""
        (temp_work_dir / "file.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "subdir").mkdir()

        result = dir_tools['tree_directory'].func(".")

        assert "📁 ." in result
        assert "file.txt" in result
        assert "subdir" in result

    def test_tree_directory_nested(self, dir_tools, temp_work_dir):
        """测试嵌套目录树"""
        (temp_work_dir / "a" / "b").mkdir(parents=True)
        (temp_work_dir / "a" / "file.txt").write_text("content", encoding='utf-8')
        (temp_work_dir / "a" / "b" / "nested.txt").write_text("content", encoding='utf-8')

        result = dir_tools['tree_directory'].func(".", max_depth=3)

        assert "a" in result
        assert "b" in result
        assert "nested.txt" in result

    def test_tree_directory_max_depth(self, dir_tools, temp_work_dir):
        """测试最大深度限制"""
        (temp_work_dir / "a" / "b" / "c").mkdir(parents=True)
        (temp_work_dir / "a" / "b" / "c" / "deep.txt").write_text("content", encoding='utf-8')

        result = dir_tools['tree_directory'].func(".", max_depth=2)

        # 深度超过限制的文件不应显示
        assert "deep.txt" not in result

    def test_tree_directory_empty(self, dir_tools, temp_work_dir):
        """测试空目录树"""
        result = dir_tools['tree_directory'].func(".")
        assert "📁 ." in result

    def test_tree_directory_not_exist(self, dir_tools):
        """测试目录不存在"""
        result = dir_tools['tree_directory'].func("nonexistent")
        assert "错误" in result
