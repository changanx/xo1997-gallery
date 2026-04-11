"""
文件操作工具
"""
from langchain_core.tools import tool
from .base import SecurityContext, register_tool


def create_file_tools(security: SecurityContext):
    """创建文件操作工具"""

    @tool
    def read_file(file_path: str) -> str:
        """读取指定路径的文件内容。路径相对于工作目录。

        Args:
            file_path: 相对于工作目录的文件路径

        Returns:
            文件内容字符串
        """
        full_path = security.safe_join(file_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg
        try:
            if not full_path.exists():
                return f"错误: 文件不存在 - {file_path}"
            if not full_path.is_file():
                return f"错误: 路径不是文件 - {file_path}"
            return full_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return f"错误: 无法解码文件 (可能不是文本文件) - {file_path}"
        except PermissionError:
            return f"错误: 没有权限读取文件 - {file_path}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"

    @tool
    def write_file(file_path: str, content: str) -> str:
        """向指定路径写入文件内容。路径相对于工作目录。如果文件不存在会创建，存在则覆盖。

        Args:
            file_path: 相对于工作目录的文件路径
            content: 要写入的文件内容

        Returns:
            操作结果信息
        """
        full_path = security.safe_join(file_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            return f"文件写入成功: {file_path} ({len(content)} 字符)"
        except PermissionError:
            return f"错误: 没有权限写入文件 - {file_path}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"

    @tool
    def delete_file(file_path: str) -> str:
        """删除指定路径的文件。路径相对于工作目录。

        Args:
            file_path: 相对于工作目录的文件路径

        Returns:
            操作结果信息
        """
        full_path = security.safe_join(file_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg
        try:
            if not full_path.exists():
                return f"错误: 文件不存在 - {file_path}"
            if not full_path.is_file():
                return f"错误: 路径不是文件 - {file_path}"
            full_path.unlink()
            return f"文件删除成功: {file_path}"
        except PermissionError:
            return f"错误: 没有权限删除文件 - {file_path}"
        except Exception as e:
            return f"删除文件失败: {str(e)}"

    @tool
    def rename_file(old_path: str, new_path: str) -> str:
        """重命名或移动文件。路径相对于工作目录。

        Args:
            old_path: 原文件路径
            new_path: 新文件路径

        Returns:
            操作结果信息
        """
        old_full = security.safe_join(old_path)
        new_full = security.safe_join(new_path)

        is_safe_old, error_old = security.validate_path(old_full)
        if not is_safe_old:
            return error_old

        is_safe_new, error_new = security.validate_path(new_full)
        if not is_safe_new:
            return error_new

        try:
            if not old_full.exists():
                return f"错误: 原文件不存在 - {old_path}"
            new_full.parent.mkdir(parents=True, exist_ok=True)
            old_full.rename(new_full)
            return f"文件重命名成功: {old_path} -> {new_path}"
        except PermissionError:
            return f"错误: 没有权限重命名文件"
        except Exception as e:
            return f"重命名失败: {str(e)}"

    @tool
    def copy_file(source_path: str, dest_path: str) -> str:
        """复制文件到新位置。路径相对于工作目录。

        Args:
            source_path: 源文件路径
            dest_path: 目标文件路径

        Returns:
            操作结果信息
        """
        import shutil
        source_full = security.safe_join(source_path)
        dest_full = security.safe_join(dest_path)

        is_safe_source, error_source = security.validate_path(source_full)
        if not is_safe_source:
            return error_source

        is_safe_dest, error_dest = security.validate_path(dest_full)
        if not is_safe_dest:
            return error_dest

        try:
            if not source_full.exists():
                return f"错误: 源文件不存在 - {source_path}"
            dest_full.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_full, dest_full)
            return f"文件复制成功: {source_path} -> {dest_path}"
        except PermissionError:
            return f"错误: 没有权限复制文件"
        except Exception as e:
            return f"复制失败: {str(e)}"

    @tool
    def file_info(file_path: str) -> str:
        """获取文件详细信息。路径相对于工作目录。

        Args:
            file_path: 相对于工作目录的文件路径

        Returns:
            文件信息字符串
        """
        import os
        from datetime import datetime

        full_path = security.safe_join(file_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if not full_path.exists():
                return f"错误: 文件不存在 - {file_path}"

            stat = full_path.stat()
            info = [
                f"路径: {file_path}",
                f"类型: {'目录' if full_path.is_dir() else '文件'}",
                f"大小: {stat.st_size} 字节",
                f"创建时间: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
                f"修改时间: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            return "\n".join(info)
        except Exception as e:
            return f"获取文件信息失败: {str(e)}"

    return [read_file, write_file, delete_file, rename_file, copy_file, file_info]
