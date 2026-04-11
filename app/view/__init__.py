"""
视图模块
"""
from .main_window import MainWindow
from .excel_ppt_interface import ExcelPPTInterface
from .ai_chat_interface import AIChatInterface
from .ai_settings_interface import AISettingsInterface

__all__ = [
    "MainWindow",
    "ExcelPPTInterface",
    "AIChatInterface",
    "AISettingsInterface",
]
