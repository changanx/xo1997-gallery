"""
Excel→PPT 页面
"""
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout

from app.ui import (
    ScrollArea, TitleLabel, SubtitleLabel, BodyLabel,
    PrimaryPushButton, PushButton, InfoBar, InfoBarPosition,
    FluentIcon as FIF
)

from ..components.status_card_widget import StatusCardWidget
from ..components.file_selector_widget import FileSelectorWidget
from core.excel_processor import ExcelProcessor
from core.ppt_generator import PPTGenerator


class ExcelPPTInterface(ScrollArea):
    """Excel 生成 PPT 页面"""

    # 信号
    excelImported = Signal(bool, str)
    pptGenerated = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processor = ExcelProcessor()
        self._generator = PPTGenerator()
        self._excel_path: Optional[str] = None

        self._initUI()
        self._connectSignals()

    def _initUI(self):
        """初始化 UI"""
        # 滚动内容
        self.view = QWidget(self)
        self.vBoxLayout = QVBoxLayout(self.view)

        # 标题
        self.titleLabel = TitleLabel("Excel 生成 PPT", self)
        self.subtitleLabel = SubtitleLabel("导入员工 Excel 数据，生成组织架构 PPT", self)

        # Excel 文件选择
        self.excelSelector = FileSelectorWidget(
            "选择 Excel 文件",
            mode="open",
            filter="Excel Files (*.xlsx *.xls)"
        )

        # 状态卡片
        self.statusLayout = QHBoxLayout()
        self.deptCountCard = StatusCardWidget("部门数量", "0")
        self.empCountCard = StatusCardWidget("员工数量", "0")

        self.statusLayout.addWidget(self.deptCountCard)
        self.statusLayout.addWidget(self.empCountCard)
        self.statusLayout.addStretch()

        # 操作按钮
        self.actionLayout = QHBoxLayout()
        self.importBtn = PrimaryPushButton(FIF.DOCUMENT, "导入数据", self)
        self.generateBtn = PushButton(FIF.SHARE, "生成 PPT", self)
        self.generateBtn.setEnabled(False)

        self.actionLayout.addWidget(self.importBtn)
        self.actionLayout.addWidget(self.generateBtn)
        self.actionLayout.addStretch()

        # 输出路径
        self.outputSelector = FileSelectorWidget(
            "选择保存路径",
            mode="save",
            filter="PowerPoint Files (*.pptx)"
        )

        # 布局
        self.vBoxLayout.setSpacing(20)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 36)
        self.vBoxLayout.setAlignment(Qt.AlignTop)

        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.subtitleLabel)
        self.vBoxLayout.addWidget(BodyLabel("Excel 文件："))
        self.vBoxLayout.addWidget(self.excelSelector)
        self.vBoxLayout.addLayout(self.statusLayout)
        self.vBoxLayout.addLayout(self.actionLayout)
        self.vBoxLayout.addWidget(BodyLabel("输出路径："))
        self.vBoxLayout.addWidget(self.outputSelector)

        # 滚动设置
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        # 设置 objectName
        self.setObjectName('excelPptInterface')
        self.view.setObjectName('view')

    def _connectSignals(self):
        """连接信号"""
        self.excelSelector.pathChanged.connect(self._onExcelSelected)
        self.importBtn.clicked.connect(self._onImport)
        self.generateBtn.clicked.connect(self._onGenerate)

    def _onExcelSelected(self, path: str):
        """Excel 文件选中"""
        self._excel_path = path

    def _onImport(self):
        """导入按钮点击"""
        if not self._excel_path:
            self._showInfo(False, "请先选择 Excel 文件")
            return

        success, message = self._processor.import_excel(self._excel_path)

        if success:
            # 更新状态卡片
            self.deptCountCard.setValue(str(self._processor.department_count))
            self.empCountCard.setValue(str(self._processor.employee_count))
            # 启用生成按钮
            self.generateBtn.setEnabled(True)

        self._showInfo(success, message)
        self.excelImported.emit(success, message)

    def _onGenerate(self):
        """生成 PPT 按钮"""
        output_path = self.outputSelector.path()
        if not output_path:
            self._showInfo(False, "请先选择输出路径")
            return

        if not output_path.endswith('.pptx'):
            output_path += '.pptx'

        tree = self._processor.get_department_tree()
        stats = self._processor.get_employee_stats()

        success, message = self._generator.generate(tree, stats, output_path)
        self._showInfo(success, message)
        self.pptGenerated.emit(success, message)

    def _showInfo(self, success: bool, message: str):
        """显示提示信息"""
        if success:
            InfoBar.success(
                title="成功",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="失败",
                content=message,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
