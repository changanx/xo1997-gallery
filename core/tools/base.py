"""
工具基础模块 - 安全上下文和工具注册
"""
import os
from pathlib import Path
from typing import Dict, Any, Callable, List, Optional

from app.common.logger import get_logger

logger = get_logger()


class SecurityContext:
    """安全上下文，限制文件操作范围"""

    def __init__(self, work_directory: str):
        self.work_directory = Path(work_directory).resolve()

    def is_safe_path(self, path: Path) -> bool:
        """
        检查路径是否在工作目录内

        安全检查包括：
        1. 符号链接检测 - 防止通过符号链接访问外部目录
        2. 路径穿越检测 - 防止通过 .. 访问上级目录
        3. 严格路径比较 - 使用分隔符确保精确匹配
        """
        try:
            # 检查符号链接
            # 如果路径本身是符号链接，需要检查其真实目标
            check_path = Path(path)
            if check_path.is_symlink():
                real_target = check_path.resolve()
                real_str = str(real_target)
                work_str = str(self.work_directory)
                # 符号链接的真实目标必须在工作目录内
                if not (real_str == work_str or real_str.startswith(work_str + os.sep)):
                    logger.warning(
                        "符号链接指向工作目录外",
                        extra={"symlink": str(path), "target": real_str, "work_dir": work_str}
                    )
                    return False

            # 解析路径（会处理 .. 和符号链接）
            resolved = Path(path).resolve()
            resolved_str = str(resolved)
            work_str = str(self.work_directory)

            # 严格路径比较：确保是工作目录本身或其子目录
            # 使用 os.sep 确保不会出现前缀匹配问题（如 /home/user 匹配 /home/user2）
            is_safe = resolved_str == work_str or resolved_str.startswith(work_str + os.sep)

            if not is_safe:
                logger.warning(
                    "路径安全验证失败",
                    extra={"resolved": resolved_str, "work_dir": work_str}
                )

            return is_safe
        except Exception as e:
            logger.error("路径验证异常", extra={"path": str(path), "error": str(e)})
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
