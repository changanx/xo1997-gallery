"""
工具模块 - 提供文件、目录、执行等操作工具
"""
from typing import List
from langchain_core.tools import BaseTool

from .base import SecurityContext, register_tool, get_tool, execute_tool
from .file_tools import create_file_tools
from .directory_tools import create_directory_tools
from .execute_tools import create_execute_tools


def create_all_tools(security: SecurityContext) -> List[BaseTool]:
    """
    创建所有工具并注册

    Args:
        security: 安全上下文，限制操作范围

    Returns:
        工具列表
    """
    tools = []
    tools.extend(create_file_tools(security))
    tools.extend(create_directory_tools(security))
    tools.extend(create_execute_tools(security))

    # 注册所有工具到全局注册表
    for tool in tools:
        register_tool(tool.name, tool.func)

    return tools


__all__ = [
    'SecurityContext',
    'register_tool',
    'get_tool',
    'execute_tool',
    'create_file_tools',
    'create_directory_tools',
    'create_execute_tools',
    'create_all_tools',
]
