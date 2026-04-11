"""
文件工具测试
测试文件操作工具的所有功能
"""
import pytest
from pathlib import Path

from core.tools.base import SecurityContext
from core.tools.file_tools import create_file_tools


@pytest.fixture
def file_tools(temp_work_dir):
    """创建文件工具实例"""
    security = SecurityContext(str(temp_work_dir))
    tools = create_file_tools(security)
    # 返回工具字典，方便按名称访问
    return {tool.name: tool for tool in tools}


class TestReadFile:
    """read_file 工具测试"""

    def test_read_file_success(self, file_tools, temp_work_dir):
        """测试成功读取文件"""
        # 创建测试文件
        test_file = temp_work_dir / "test.txt"
        test_file.write_text("Hello, World!", encoding='utf-8')

        # 读取文件
        result = file_tools['read_file'].func("test.txt")
        assert result == "Hello, World!"

    def test_read_file_not_exist(self, file_tools):
        """测试文件不存在"""
        result = file_tools['read_file'].func("nonexistent.txt")
        assert "错误" in result
        assert "不存在" in result

    def test_read_file_outside_workdir(self, file_tools, temp_work_dir):
        """测试越界访问"""
        # 尝试读取工作目录外的文件
        result = file_tools['read_file'].func("../outside.txt")
        assert "错误" in result
        assert "不允许访问" in result

    def test_read_file_is_directory(self, file_tools, temp_work_dir):
        """测试读取目录"""
        dir_path = temp_work_dir / "subdir"
        dir_path.mkdir()

        result = file_tools['read_file'].func("subdir")
        assert "错误" in result
        assert "不是文件" in result

    def test_read_file_nested_path(self, file_tools, temp_work_dir):
        """测试读取嵌套路径的文件"""
        nested_dir = temp_work_dir / "a" / "b" / "c"
        nested_dir.mkdir(parents=True)
        nested_file = nested_dir / "nested.txt"
        nested_file.write_text("nested content", encoding='utf-8')

        result = file_tools['read_file'].func("a/b/c/nested.txt")
        assert result == "nested content"

    def test_read_file_chinese_content(self, file_tools, temp_work_dir):
        """测试读取中文内容"""
        test_file = temp_work_dir / "chinese.txt"
        test_file.write_text("你好，世界！", encoding='utf-8')

        result = file_tools['read_file'].func("chinese.txt")
        assert result == "你好，世界！"


class TestWriteFile:
    """write_file 工具测试"""

    def test_write_file_success(self, file_tools, temp_work_dir):
        """测试成功写入文件"""
        result = file_tools['write_file'].func("new.txt", "new content")
        assert "成功" in result

        # 验证文件已创建
        written_file = temp_work_dir / "new.txt"
        assert written_file.exists()
        assert written_file.read_text(encoding='utf-8') == "new content"

    def test_write_file_overwrite(self, file_tools, temp_work_dir):
        """测试覆盖现有文件"""
        test_file = temp_work_dir / "overwrite.txt"
        test_file.write_text("original", encoding='utf-8')

        result = file_tools['write_file'].func("overwrite.txt", "new content")
        assert "成功" in result

        # 验证内容已更新
        assert test_file.read_text(encoding='utf-8') == "new content"

    def test_write_file_create_dirs(self, file_tools, temp_work_dir):
        """测试自动创建父目录"""
        result = file_tools['write_file'].func("nested/dir/file.txt", "content")
        assert "成功" in result

        # 验证目录和文件已创建
        nested_file = temp_work_dir / "nested" / "dir" / "file.txt"
        assert nested_file.exists()
        assert nested_file.read_text(encoding='utf-8') == "content"

    def test_write_file_outside_workdir(self, file_tools):
        """测试越界写入"""
        result = file_tools['write_file'].func("../outside.txt", "content")
        assert "错误" in result
        assert "不允许访问" in result


class TestDeleteFile:
    """delete_file 工具测试"""

    def test_delete_file_success(self, file_tools, temp_work_dir):
        """测试成功删除文件"""
        test_file = temp_work_dir / "to_delete.txt"
        test_file.write_text("delete me", encoding='utf-8')

        result = file_tools['delete_file'].func("to_delete.txt")
        assert "成功" in result
        assert not test_file.exists()

    def test_delete_file_not_exist(self, file_tools):
        """测试删除不存在的文件"""
        result = file_tools['delete_file'].func("nonexistent.txt")
        assert "错误" in result
        assert "不存在" in result

    def test_delete_file_is_directory(self, file_tools, temp_work_dir):
        """测试删除目录（应该失败）"""
        dir_path = temp_work_dir / "subdir"
        dir_path.mkdir()

        result = file_tools['delete_file'].func("subdir")
        assert "错误" in result
        assert "不是文件" in result

    def test_delete_file_outside_workdir(self, file_tools):
        """测试越界删除"""
        result = file_tools['delete_file'].func("../outside.txt")
        assert "错误" in result
        assert "不允许访问" in result


class TestRenameFile:
    """rename_file 工具测试"""

    def test_rename_file_success(self, file_tools, temp_work_dir):
        """测试成功重命名文件"""
        old_file = temp_work_dir / "old.txt"
        old_file.write_text("content", encoding='utf-8')

        result = file_tools['rename_file'].func("old.txt", "new.txt")
        assert "成功" in result

        # 验证旧文件不存在，新文件存在
        assert not old_file.exists()
        new_file = temp_work_dir / "new.txt"
        assert new_file.exists()
        assert new_file.read_text(encoding='utf-8') == "content"

    def test_rename_file_move_to_subdir(self, file_tools, temp_work_dir):
        """测试移动到子目录"""
        old_file = temp_work_dir / "file.txt"
        old_file.write_text("content", encoding='utf-8')
        subdir = temp_work_dir / "subdir"
        subdir.mkdir()

        result = file_tools['rename_file'].func("file.txt", "subdir/moved.txt")
        assert "成功" in result

        assert not old_file.exists()
        moved_file = subdir / "moved.txt"
        assert moved_file.exists()

    def test_rename_file_old_not_exist(self, file_tools):
        """测试原文件不存在"""
        result = file_tools['rename_file'].func("nonexistent.txt", "new.txt")
        assert "错误" in result
        assert "不存在" in result

    def test_rename_file_cross_boundary(self, file_tools):
        """测试跨边界重命名"""
        result = file_tools['rename_file'].func("file.txt", "../outside.txt")
        assert "错误" in result

    def test_rename_file_new_path_outside(self, file_tools, temp_work_dir):
        """测试新路径越界"""
        old_file = temp_work_dir / "file.txt"
        old_file.write_text("content", encoding='utf-8')

        result = file_tools['rename_file'].func("file.txt", "../outside.txt")
        assert "错误" in result


class TestCopyFile:
    """copy_file 工具测试"""

    def test_copy_file_success(self, file_tools, temp_work_dir):
        """测试成功复制文件"""
        source = temp_work_dir / "source.txt"
        source.write_text("content", encoding='utf-8')

        result = file_tools['copy_file'].func("source.txt", "copy.txt")
        assert "成功" in result

        # 验证两个文件都存在
        assert source.exists()
        copy = temp_work_dir / "copy.txt"
        assert copy.exists()
        assert copy.read_text(encoding='utf-8') == "content"

    def test_copy_file_to_subdir(self, file_tools, temp_work_dir):
        """测试复制到子目录"""
        source = temp_work_dir / "file.txt"
        source.write_text("content", encoding='utf-8')
        subdir = temp_work_dir / "subdir"
        subdir.mkdir()

        result = file_tools['copy_file'].func("file.txt", "subdir/copy.txt")
        assert "成功" in result

        copy = subdir / "copy.txt"
        assert copy.exists()

    def test_copy_file_source_not_exist(self, file_tools):
        """测试源文件不存在"""
        result = file_tools['copy_file'].func("nonexistent.txt", "copy.txt")
        assert "错误" in result
        assert "不存在" in result

    def test_copy_file_source_outside(self, file_tools):
        """测试源文件越界"""
        result = file_tools['copy_file'].func("../outside.txt", "copy.txt")
        assert "错误" in result

    def test_copy_file_dest_outside(self, file_tools, temp_work_dir):
        """测试目标路径越界"""
        source = temp_work_dir / "file.txt"
        source.write_text("content", encoding='utf-8')

        result = file_tools['copy_file'].func("file.txt", "../outside.txt")
        assert "错误" in result


class TestFileInfo:
    """file_info 工具测试"""

    def test_file_info_success(self, file_tools, temp_work_dir):
        """测试获取文件信息"""
        test_file = temp_work_dir / "test.txt"
        test_file.write_text("Hello", encoding='utf-8')

        result = file_tools['file_info'].func("test.txt")

        assert "路径: test.txt" in result
        assert "类型: 文件" in result
        assert "大小: 5 字节" in result
        assert "创建时间:" in result
        assert "修改时间:" in result

    def test_file_info_directory(self, file_tools, temp_work_dir):
        """测试获取目录信息"""
        dir_path = temp_work_dir / "subdir"
        dir_path.mkdir()

        result = file_tools['file_info'].func("subdir")

        assert "路径: subdir" in result
        assert "类型: 目录" in result

    def test_file_info_not_exist(self, file_tools):
        """测试文件不存在"""
        result = file_tools['file_info'].func("nonexistent.txt")
        assert "错误" in result
        assert "不存在" in result

    def test_file_info_outside_workdir(self, file_tools):
        """测试越界访问"""
        result = file_tools['file_info'].func("../outside.txt")
        assert "错误" in result
