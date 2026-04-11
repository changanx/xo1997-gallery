"""
数据模型模块
"""
from .department import Department
from .employee import Employee
from .ai_config import AIModelConfig, ChatMessage, ChatSession

__all__ = ["Department", "Employee", "AIModelConfig", "ChatMessage", "ChatSession"]
