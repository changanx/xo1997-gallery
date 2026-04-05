"""
状态卡片组件
"""
from qfluentwidgets import SimpleCardWidget, CaptionLabel, TitleLabel
from PySide6.QtWidgets import QVBoxLayout
from PySide6.QtCore import Qt


class StatusCardWidget(SimpleCardWidget):
    """状态显示卡片"""

    def __init__(self, title: str, value: str = "0", parent=None):
        super().__init__(parent)
        self._title = title
        self._value = value

        self._initUI()

    def _initUI(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        self.titleLabel = CaptionLabel(self._title, self)
        self.valueLabel = TitleLabel(self._value, self)

        self.titleLabel.setAlignment(Qt.AlignCenter)
        self.valueLabel.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.titleLabel)
        layout.addWidget(self.valueLabel)

    def setValue(self, value: str):
        """设置值"""
        self._value = str(value)
        self.valueLabel.setText(self._value)

    def value(self) -> str:
        """获取值"""
        return self._value
