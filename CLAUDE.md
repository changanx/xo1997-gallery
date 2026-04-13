# xo1997 画廊 - 开发规范

## 项目概述

基于 PySide6 的桌面应用，主要功能：
- Excel 员工数据导入生成组织架构 PPT
- AI 智能助手（多模型对话 + 工具调用）

## 架构

```
app/           → 应用层（入口、视图、UI组件）
core/          → 业务层（Excel处理、PPT生成、AI模型管理）
data/          → 数据层（数据库、模型、仓库）
tests/         → 测试
```

---

# 测试规范

## 测试框架

- **pytest** - 测试框架
- **pytest-qt** - Qt 组件测试
- **pytest-cov** - 覆盖率报告

## 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 测试文件 | `test_<模块名>.py` | `test_security_context.py` |
| 测试类 | `Test<类名>` | `TestSecurityContext` |
| 测试方法 | `test_<功能描述>` | `test_is_safe_path_inside` |

## 目录结构

```
tests/
├── conftest.py              # 全局 fixtures
├── helpers.py               # 测试辅助工具
├── mocks/                   # Mock 对象
│   ├── __init__.py
│   └── langchain_mock.py
├── test_data/               # 数据层测试
├── test_core/               # 核心层测试
├── test_components/         # 组件层测试
├── test_views/              # 视图层测试
└── test_integration/        # 集成测试
```

## 编写规范

### 1. 测试类结构

```python
class TestSecurityContext:
    """SecurityContext 测试"""

    def setup_method(self):
        """每个测试前的准备工作"""
        pass

    def test_is_safe_path_inside(self, temp_work_dir):
        """测试路径在工作目录内返回 True"""
        # Arrange
        security = SecurityContext(temp_work_dir)
        
        # Act
        result = security.is_safe_path(temp_work_dir / "subdir" / "file.txt")
        
        # Assert
        assert result is True

    def teardown_method(self):
        """每个测试后的清理工作"""
        pass
```

### 2. Fixture 使用

```python
# conftest.py 中定义的 fixtures

# 临时工作目录（用于工具测试）
def test_file_operation(self, temp_work_dir):
    file_path = temp_work_dir / "test.txt"
    file_path.write_text("content")

# 示例 Excel 文件（用于导入测试）
def test_excel_import(self, sample_excel_file):
    processor = ExcelProcessor()
    processor.import_excel(sample_excel_file)

# Mock LangChain 模型（用于 AI 测试）
def test_chat(self, mock_chat_model):
    manager = ModelManager()
    manager._current_model = mock_chat_model
```

### 3. 参数化测试

```python
@pytest.mark.parametrize("path,expected", [
    ("file.txt", True),
    ("subdir/file.txt", True),
    ("../outside.txt", False),
    ("/etc/passwd", False),
])
def test_is_safe_path(self, temp_work_dir, path, expected):
    security = SecurityContext(temp_work_dir)
    result = security.is_safe_path(temp_work_dir / path)
    assert result is expected
```

### 4. 异常测试

```python
def test_create_model_invalid_provider(self):
    config = AIModelConfig(provider="invalid", model_name="test")
    manager = ModelManager()
    with pytest.raises(ValueError, match="不支持的模型提供商"):
        manager.create_chat_model(config)
```

### 5. GUI 组件测试

```python
class TestChatMessageWidget:
    """ChatMessageWidget 测试"""

    def test_creation_user_message(self, qtbot):
        """测试创建用户消息"""
        widget = ChatMessageWidget("user", "你好")
        qtbot.addWidget(widget)
        
        assert widget._role == "user"
        assert widget._content == "你好"

    def test_signal_emission(self, qtbot):
        """测试信号发射"""
        widget = FileSelectorWidget("选择文件")
        qtbot.addWidget(widget)
        
        with qtbot.waitSignal(widget.pathChanged, timeout=1000):
            widget.pathChanged.emit("/test/path.xlsx")
```

### 6. Mock 使用

```python
# Mock LangChain 模型
from tests.mocks.langchain_mock import MockChatModel

def test_chat_stream(self):
    mock_model = MockChatModel(responses=["Hello", " World"])
    manager = ModelManager()
    manager._current_model = mock_model
    
    chunks = list(manager.chat([{"role": "user", "content": "Hi"}]))
    assert len(chunks) == 2
```

## 各层级测试要点

### 数据层测试

- 测试 CRUD 操作
- 测试查询方法（find_by_id, find_all, find_by_parent 等）
- 测试数据模型解析（from_row）
- 测试边界条件（空数据、无效数据）

### 核心层测试

- **SecurityContext**: 路径安全验证、边界穿越检测
- **文件工具**: 读写删除、权限检查、错误处理
- **目录工具**: 创建列表删除、递归操作
- **ExcelProcessor**: 导入成功/失败、数据解析
- **PPTGenerator**: 文件生成、内容验证
- **ModelManager**: 模型创建、对话流程、工具调用

### 组件层测试

- 组件创建和初始化
- 属性设置和获取
- 信号发射
- 用户交互模拟

### 视图层测试

- 界面创建
- 组件布局
- 信号槽连接
- 用户操作响应

### 集成测试

- 完整工作流测试
- 多模块协作测试

## 运行命令

```bash
# 运行所有测试
pytest

# 运行指定目录
pytest tests/test_core/

# 运行指定文件
pytest tests/test_core/test_security_context.py

# 运行指定测试方法
pytest tests/test_core/test_security_context.py::TestSecurityContext::test_is_safe_path_inside

# 详细输出
pytest -v

# 带覆盖率报告
pytest --cov=app --cov=core --cov=data --cov-report=html

# 只运行失败的测试
pytest --lf

# 并行运行（需要 pytest-xdist）
pytest -n auto
```

## 覆盖率要求

| 层级 | 目标覆盖率 |
|------|------------|
| 数据层 | ≥ 90% |
| 核心层 | ≥ 80% |
| 组件层 | ≥ 85% |
| 视图层 | ≥ 70% |

## 测试数据管理

### 使用 tmp_path fixture

```python
def test_file_write(self, tmp_path):
    """使用 pytest 内置的 tmp_path"""
    file_path = tmp_path / "test.txt"
    file_path.write_text("content")
    assert file_path.exists()
```

### 使用项目 fixtures

```python
def test_with_sample_excel(self, sample_excel_file):
    """使用预定义的示例 Excel 文件"""
    processor = ExcelProcessor()
    processor.import_excel(sample_excel_file)
    assert processor.department_count() > 0
```

## 测试辅助工具

使用 `tests/helpers.py` 中的辅助类快速创建测试数据：

```python
from tests.helpers import DataHelper

def test_with_sample_data(self):
    dept = DataHelper.create_department(name="技术部", level=0)
    emp = DataHelper.create_employee(name="张三", department="技术部")
```

## 持续集成

每次提交代码时确保：
1. 所有测试通过
2. 覆盖率达标
3. 新功能有对应测试
4. 修改的功能更新了相关测试

---

# 开发工作流

## 新增功能

1. 编写测试用例（TDD）
2. 实现功能代码
3. 运行测试确保通过
4. 检查覆盖率

## 修改功能

1. 检查现有测试
2. 更新受影响的测试
3. 实现修改
4. 运行测试确保通过

## 修复 Bug

1. 编写复现 Bug 的测试
2. 修复 Bug
3. 运行测试确保通过
