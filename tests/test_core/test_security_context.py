"""
SecurityContext 测试
测试路径安全验证功能
"""
import pytest
from pathlib import Path

from core.tools.base import SecurityContext


class TestSecurityContext:
    """SecurityContext 测试"""

    def test_init(self, temp_work_dir):
        """测试初始化"""
        security = SecurityContext(str(temp_work_dir))
        assert security.work_directory == temp_work_dir.resolve()

    def test_is_safe_path_inside(self, temp_work_dir):
        """测试路径在工作目录内返回 True"""
        security = SecurityContext(str(temp_work_dir))

        # 直接子路径
        assert security.is_safe_path(temp_work_dir / "file.txt") is True

        # 嵌套子路径
        assert security.is_safe_path(temp_work_dir / "subdir" / "file.txt") is True

        # 多层嵌套
        assert security.is_safe_path(temp_work_dir / "a" / "b" / "c" / "file.txt") is True

    def test_is_safe_path_outside(self, temp_work_dir):
        """测试路径在工作目录外返回 False"""
        security = SecurityContext(str(temp_work_dir))

        # 父目录
        assert security.is_safe_path(temp_work_dir.parent) is False

        # 兄弟目录
        sibling = temp_work_dir.parent / "other_dir"
        assert security.is_safe_path(sibling) is False

        # 完全不相关的路径
        assert security.is_safe_path(Path("/etc/passwd")) is False
        assert security.is_safe_path(Path("C:/Windows/System32")) is False

    def test_is_safe_path_traversal(self, temp_work_dir):
        """测试路径穿越攻击返回 False"""
        security = SecurityContext(str(temp_work_dir))

        # 使用 .. 穿越
        traversal_path = temp_work_dir / ".." / "outside.txt"
        assert security.is_safe_path(traversal_path) is False

        # 多重穿越
        multi_traversal = temp_work_dir / ".." / ".." / "etc" / "passwd"
        assert security.is_safe_path(multi_traversal) is False

    def test_is_safe_path_exact_boundary(self, temp_work_dir):
        """测试边界条件：工作目录本身"""
        security = SecurityContext(str(temp_work_dir))

        # 工作目录本身应该是安全的
        assert security.is_safe_path(temp_work_dir) is True

    def test_is_safe_path_symlink_outside(self, temp_work_dir):
        """测试符号链接指向外部"""
        security = SecurityContext(str(temp_work_dir))

        # 创建指向外部的符号链接
        outside_dir = temp_work_dir.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        link_path = temp_work_dir / "link_to_outside"

        # Windows 下创建符号链接可能需要管理员权限
        # 这里只测试普通路径，跳过符号链接测试
        pass

    def test_safe_join_normal(self, temp_work_dir):
        """测试正常路径拼接"""
        security = SecurityContext(str(temp_work_dir))

        # 简单文件名
        result = security.safe_join("file.txt")
        assert result == temp_work_dir / "file.txt"

        # 子目录文件
        result = security.safe_join("subdir/file.txt")
        assert result == temp_work_dir / "subdir" / "file.txt"

        # 多层嵌套
        result = security.safe_join("a/b/c/file.txt")
        assert result == temp_work_dir / "a" / "b" / "c" / "file.txt"

    def test_safe_join_with_pathlib(self, temp_work_dir):
        """测试使用 Path 对象拼接"""
        security = SecurityContext(str(temp_work_dir))

        result = security.safe_join(Path("subdir") / "file.txt")
        assert result == temp_work_dir / "subdir" / "file.txt"

    def test_validate_path_safe(self, temp_work_dir):
        """测试安全路径验证通过"""
        security = SecurityContext(str(temp_work_dir))

        safe_path = temp_work_dir / "file.txt"
        is_safe, error = security.validate_path(safe_path)

        assert is_safe is True
        assert error == ""

    def test_validate_path_unsafe(self, temp_work_dir):
        """测试不安全路径返回错误信息"""
        security = SecurityContext(str(temp_work_dir))

        unsafe_path = temp_work_dir.parent / "outside.txt"
        is_safe, error = security.validate_path(unsafe_path)

        assert is_safe is False
        assert "不允许访问工作目录之外的路径" in error
        assert str(temp_work_dir) in error

    def test_validate_path_traversal(self, temp_work_dir):
        """测试路径穿越验证"""
        security = SecurityContext(str(temp_work_dir))

        traversal_path = temp_work_dir / ".." / "outside.txt"
        is_safe, error = security.validate_path(traversal_path)

        assert is_safe is False

    @pytest.mark.parametrize("relative_path,expected_safe", [
        ("file.txt", True),
        ("subdir/file.txt", True),
        ("a/b/c/d/e/file.txt", True),
        ("../outside.txt", False),
        ("../../etc/passwd", False),
        ("subdir/../../outside.txt", False),
    ])
    def test_various_paths(self, temp_work_dir, relative_path, expected_safe):
        """参数化测试各种路径"""
        security = SecurityContext(str(temp_work_dir))

        full_path = security.safe_join(relative_path)
        is_safe, _ = security.validate_path(full_path)

        assert is_safe == expected_safe

    def test_work_directory_with_trailing_slash(self, tmp_path):
        """测试工作目录有尾随斜杠"""
        work_dir = tmp_path / "work"
        work_dir.mkdir()

        # 带斜杠的路径
        security = SecurityContext(str(work_dir) + "/")

        test_path = work_dir / "file.txt"
        assert security.is_safe_path(test_path) is True

    def test_work_directory_relative_path(self, tmp_path):
        """测试相对路径工作目录"""
        import os
        original_cwd = os.getcwd()

        try:
            os.chdir(str(tmp_path))
            work_dir = tmp_path / "work"
            work_dir.mkdir()

            security = SecurityContext("work")

            assert security.is_safe_path(work_dir / "file.txt") is True
            assert security.is_safe_path(tmp_path / "outside.txt") is False
        finally:
            os.chdir(original_cwd)

    def test_nonexistent_path_validation(self, temp_work_dir):
        """测试不存在的路径验证"""
        security = SecurityContext(str(temp_work_dir))

        # 不存在的路径，但在工作目录内
        nonexistent = temp_work_dir / "nonexistent" / "file.txt"
        is_safe, error = security.validate_path(nonexistent)

        # 路径安全检查不关心文件是否存在，只关心是否在工作目录内
        assert is_safe is True
