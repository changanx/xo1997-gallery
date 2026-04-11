"""
工具基础模块 - 安全上下文和工具注册
"""
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

from app.common.logger import get_logger

logger = get_logger()


class SecurityContext:
    """安全上下文，限制文件操作范围"""

    def __init__(self, work_directory: str):
        self.work_directory = Path(work_directory).resolve()

    def is_safe_path(self, path: Path) -> bool:
        """检查路径是否在工作目录内"""
        try:
            resolved = Path(path).resolve()
            return str(resolved).startswith(str(self.work_directory))
        except Exception:
            return False

    def safe_join(self, relative_path: str) -> Path:
        """安全拼接路径，返回绝对路径"""
        return self.work_directory / relative_path

    def validate_path(self, path: Path) -> tuple[bool, str]:
        """验证路径安全性，返回 (是否安全, 错误信息)"""
        if not self.is_safe_path(path):
            logger.warning(
                "路径安全验证失败",
                extra={"work_dir": str(self.work_directory), "requested_path": str(path)},
            )
            return False, f"错误: 不允许访问工作目录之外的路径\n工作目录: {self.work_directory}\n请求路径: {path}"
        return True, ""


# 全局工具注册表
_TOOL_REGISTRY: Dict[str, Callable] = {}


def register_tool(name: str, func: Callable) -> None:
    """注册工具"""
    _TOOL_REGISTRY[name] = func


def get_tool(name: str) -> Optional[Callable]:
    """获取工具"""
    return _TOOL_REGISTRY.get(name)


def execute_tool(name: str, args: Dict[str, Any]) -> str:
    """执行工具"""
    tool = get_tool(name)
    if tool is None:
        return f"错误: 未知的工具 '{name}'"
    try:
        return tool(**args)
    except Exception as e:
        return f"工具执行错误: {str(e)}"
