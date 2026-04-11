"""
目录操作工具
"""
from langchain_core.tools import tool
from .base import SecurityContext


def create_directory_tools(security: SecurityContext):
    """创建目录操作工具"""

    @tool
    def list_directory(dir_path: str = ".") -> str:
        """列出指定目录下的文件和子目录。路径相对于工作目录，默认为当前目录。

        Args:
            dir_path: 相对于工作目录的目录路径，默认为 "." (工作目录本身)

        Returns:
            目录内容列表
        """
        full_path = security.safe_join(dir_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if not full_path.exists():
                return f"错误: 目录不存在 - {dir_path}"
            if not full_path.is_dir():
                return f"错误: 路径不是目录 - {dir_path}"

            items = []
            for item in sorted(full_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                if item.is_dir():
                    item_type = "📁"
                    size = "-"
                else:
                    item_type = "📄"
                    try:
                        size = f"{item.stat().st_size:,} bytes"
                    except:
                        size = "?"

                items.append(f"{item_type} {item.name:<40} {size}")

            if not items:
                return f"目录为空: {dir_path}"

            header = f"目录: {dir_path}\n{'='*60}"
            return f"{header}\n" + "\n".join(items)
        except PermissionError:
            return f"错误: 没有权限访问目录 - {dir_path}"
        except Exception as e:
            return f"列出目录失败: {str(e)}"

    @tool
    def create_directory(dir_path: str) -> str:
        """创建目录，包括必要的父目录。路径相对于工作目录。

        Args:
            dir_path: 相对于工作目录的目录路径

        Returns:
            操作结果信息
        """
        full_path = security.safe_join(dir_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if full_path.exists():
                return f"目录已存在: {dir_path}"
            full_path.mkdir(parents=True, exist_ok=True)
            return f"目录创建成功: {dir_path}"
        except PermissionError:
            return f"错误: 没有权限创建目录 - {dir_path}"
        except Exception as e:
            return f"创建目录失败: {str(e)}"

    @tool
    def delete_directory(dir_path: str, force: bool = False) -> str:
        """删除目录。路径相对于工作目录。

        Args:
            dir_path: 相对于工作目录的目录路径
            force: 是否强制删除非空目录 (默认 False，只删除空目录)

        Returns:
            操作结果信息
        """
        import shutil

        full_path = security.safe_join(dir_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if not full_path.exists():
                return f"错误: 目录不存在 - {dir_path}"
            if not full_path.is_dir():
                return f"错误: 路径不是目录 - {dir_path}"

            # 防止删除工作目录本身
            if full_path == security.work_directory:
                return "错误: 不允许删除工作目录本身"

            if force:
                shutil.rmtree(full_path)
                return f"目录删除成功 (包括内容): {dir_path}"
            else:
                full_path.rmdir()
                return f"目录删除成功: {dir_path}"
        except OSError as e:
            if "not empty" in str(e).lower() or "非空" in str(e):
                return f"错误: 目录不为空，使用 force=True 强制删除 - {dir_path}"
            return f"删除目录失败: {str(e)}"
        except PermissionError:
            return f"错误: 没有权限删除目录 - {dir_path}"
        except Exception as e:
            return f"删除目录失败: {str(e)}"

    @tool
    def search_files(pattern: str, dir_path: str = ".") -> str:
        """在目录中搜索匹配的文件和目录。支持通配符。

        Args:
            pattern: 搜索模式，支持通配符 (* 和 ?)，例如 "*.py" 或 "test*"
            dir_path: 搜索的起始目录，默认为工作目录

        Returns:
            匹配的文件列表
        """
        full_path = security.safe_join(dir_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if not full_path.exists():
                return f"错误: 目录不存在 - {dir_path}"
            if not full_path.is_dir():
                return f"错误: 路径不是目录 - {dir_path}"

            matches = list(full_path.glob(pattern))

            if not matches:
                return f"没有找到匹配 '{pattern}' 的文件"

            # 过滤掉工作目录外的结果
            safe_matches = [m for m in matches if security.is_safe_path(m)]

            results = []
            for m in sorted(safe_matches):
                rel_path = m.relative_to(security.work_directory)
                item_type = "📁" if m.is_dir() else "📄"
                results.append(f"{item_type} {rel_path}")

            return f"搜索结果 ({len(results)} 个匹配):\n" + "\n".join(results)
        except Exception as e:
            return f"搜索失败: {str(e)}"

    @tool
    def tree_directory(dir_path: str = ".", max_depth: int = 3) -> str:
        """以树形结构显示目录内容。

        Args:
            dir_path: 相对于工作目录的目录路径
            max_depth: 最大显示深度 (默认 3)

        Returns:
            目录树形结构
        """
        full_path = security.safe_join(dir_path)
        is_safe, error_msg = security.validate_path(full_path)
        if not is_safe:
            return error_msg

        try:
            if not full_path.exists():
                return f"错误: 目录不存在 - {dir_path}"
            if not full_path.is_dir():
                return f"错误: 路径不是目录 - {dir_path}"

            lines = [f"📁 {dir_path}"]

            def walk(path: str, prefix: str, depth: int):
                if depth > max_depth:
                    return
                try:
                    items = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                    for i, item in enumerate(items):
                        if not security.is_safe_path(item):
                            continue
                        is_last = i == len(items) - 1
                        connector = "└── " if is_last else "├── "
                        icon = "📁" if item.is_dir() else "📄"
                        lines.append(f"{prefix}{connector}{icon} {item.name}")
                        if item.is_dir() and depth < max_depth:
                            new_prefix = prefix + ("    " if is_last else "│   ")
                            walk(item, new_prefix, depth + 1)
                except PermissionError:
                    lines.append(f"{prefix}└── [权限不足]")

            walk(full_path, "", 1)
            return "\n".join(lines)
        except Exception as e:
            return f"生成目录树失败: {str(e)}"

    return [list_directory, create_directory, delete_directory, search_files, tree_directory]
