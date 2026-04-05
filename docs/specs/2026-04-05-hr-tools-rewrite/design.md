# HR 工具箱重写设计文档

## Overview
- **Goal**: 使用 pyside6-dev 工作流完全重写 HR 工具箱，提升代码质量和可维护性
- **Date**: 2026-04-05

## Requirements

### 核心功能
1. **Excel 导入**: 导入员工 Excel 数据（department + employee 两张表）
2. **PPT 生成**: 根据导入的数据生成组织架构 PPT

### 非功能性需求
- 遵循 pyside6-dev 工作流
- 使用 PyQt-Fluent-Widgets Fluent Design
- 完整的单元测试覆盖
- 清晰的代码架构

## Architecture

### 目录结构

```
hr-tools/
├── app/
│   ├── __init__.py
│   ├── main.py                    # 应用入口
│   │
│   ├── common/
│   │   ├── __init__.py
│   │   ├── config.py              # QConfig 配置
│   │   ├── signal_bus.py          # 全局信号总线
│   │   └── style_sheet.py         # StyleSheet 管理
│   │
│   ├── view/
│   │   ├── __init__.py
│   │   ├── main_window.py         # 主窗口
│   │   └── excel_ppt_interface.py # Excel→PPT 页面
│   │
│   ├── components/
│   │   ├── __init__.py
│   │   ├── file_selector_widget.py    # 文件选择器
│   │   └── status_card_widget.py      # 状态卡片
│   │
│   └── resource/
│       └── qss/
│           ├── light/
│           └── dark/
│
├── core/
│   ├── __init__.py
│   ├── excel_processor.py         # Excel 处理器
│   └── ppt_generator.py           # PPT 生成器
│
├── data/
│   ├── __init__.py
│   ├── database.py                # SQLite 连接管理
│   ├── models/
│   │   ├── __init__.py
│   │   ├── department.py
│   │   └── employee.py
│   └── repositories/
│       ├── __init__.py
│       ├── department_repository.py
│       └── employee_repository.py
│
├── tests/
│   ├── conftest.py
│   ├── test_components/
│   └── test_core/
│
├── docs/
│   └── specs/
│
├── requirements.txt
├── pytest.ini
└── README.md
```

## Component Design

### 1. MainWindow

继承 `FluentWindow`，单页面导航。

```python
class MainWindow(FluentWindow):
    def __init__(self):
        self.excelPptInterface = ExcelPPTInterface(self)
        self.initNavigation()
        self.initWindow()
    
    def initNavigation(self):
        self.addSubInterface(self.excelPptInterface, FIF.DOCUMENT, 'Excel→PPT')
    
    def initWindow(self):
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)
        self.setWindowTitle('HR 工具箱')
```

### 2. ExcelPPTInterface

主要工作页面，包含文件选择、状态显示、操作按钮。

```python
class ExcelPPTInterface(ScrollArea):
    # Signals
    excelImported = Signal(bool, str)
    pptGenerated = Signal(bool, str)
    
    def __init__(self):
        # Header
        self.titleLabel = TitleLabel("Excel 生成 PPT")
        
        # File selector
        self.fileSelector = FileSelectorWidget("选择 Excel 文件")
        
        # Status cards
        self.deptCountCard = StatusCardWidget("部门数量", "0")
        self.empCountCard = StatusCardWidget("员工数量", "0")
        
        # Actions
        self.importBtn = PrimaryPushButton("导入数据")
        self.generateBtn = PushButton("生成 PPT")
        self.generateBtn.setEnabled(False)
        
        # Output
        self.outputPathSelector = FileSelectorWidget("保存路径")
```

### 3. FileSelectorWidget

可复用的文件选择组件。

```python
class FileSelectorWidget(CardWidget):
    pathChanged = Signal(str)
    
    def __init__(self, label: str, mode: str = "open", parent=None):
        # mode: "open" | "save" | "folder"
        self.label = label
        self.mode = mode
        
        self.pathEdit = LineEdit()
        self.browseBtn = PushButton("浏览")
```

### 4. StatusCardWidget

状态展示卡片。

```python
class StatusCardWidget(SimpleCardWidget):
    def __init__(self, title: str, value: str, parent=None):
        self.titleLabel = CaptionLabel(title)
        self.valueLabel = TitleLabel(value)
    
    def setValue(self, value: str):
        self.valueLabel.setText(value)
```

## Data Layer Design

### Database

```python
# data/database.py
class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def connection(self) -> sqlite3.Connection:
        # 使用 :memory: 内存数据库
        pass
```

### Models

```python
@dataclass
class Department:
    id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str = ""
    level: int = 0

@dataclass
class Employee:
    id: Optional[int] = None
    name: str = ""
    employee_number: str = ""
    department_level1: str = ""
    department_level2: str = ""
    department_level3: str = ""
    department_level4: str = ""
    department_level5: str = ""
    rank: str = ""
    category: str = ""
```

### Repositories

```python
class DepartmentRepository:
    def find_all(self) -> List[Department]
    def find_by_id(self, id: int) -> Optional[Department]
    def save(self, dept: Department) -> Department
    def count(self) -> int

class EmployeeRepository:
    def find_all(self) -> List[Employee]
    def find_by_id(self, id: int) -> Optional[Employee]
    def save(self, emp: Employee) -> Employee
    def count(self) -> int
    def get_stats_by_department(self) -> List[Tuple]
```

## Testing Strategy

### Unit Tests
- 每个 Component 有对应的测试
- 每个 Repository 有对应的测试
- Excel 处理器测试
- PPT 生成器测试

### Test Structure

```
tests/
├── conftest.py                    # Fixtures
├── test_components/
│   ├── test_file_selector.py
│   └── test_status_card.py
├── test_core/
│   ├── test_excel_processor.py
│   └── test_ppt_generator.py
└── test_data/
    ├── test_department_repository.py
    └── test_employee_repository.py
```

## Technical Stack

| 技术 | 版本 | 用途 |
|------|------|------|
| PySide6 | 6.x | Qt 框架 |
| PyQt-Fluent-Widgets | 1.11.x | Fluent Design UI |
| SQLite | 3.x | 本地数据存储 |
| pandas | 2.x | Excel 处理 |
| python-pptx | 1.x | PPT 生成 |
| pytest | 7.x | 测试框架 |
| pytest-qt | 4.x | Qt 测试 |
