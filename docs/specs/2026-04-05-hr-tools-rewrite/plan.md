# HR 工具箱重写实现计划

## Overview
- **Goal**: 使用 TDD 重写 HR 工具箱 Excel→PPT 功能
- **Design Doc**: `docs/specs/2026-04-05-hr-tools-rewrite/design.md`
- **Branch**: feature/rewrite

## Context
- 原项目位于 `C:\Users\m1582\Desktop\AI\hr-tools`
- 核心功能：导入 Excel 员工数据 → 生成组织架构 PPT
- 使用 pyside6-dev 工作流

---

## Task 1: 项目初始化

**Files:**
- 创建: `requirements.txt`
- 创建: `pytest.ini`
- 创建: `app/__init__.py`
- 创建: `app/main.py`

**Test First:**
- 测试应用可以启动

Steps:
1. 清理旧文件（保留 data/ 目录）
2. 创建 requirements.txt
3. 创建 pytest.ini
4. 创建 app/__init__.py
5. 创建最小化 app/main.py

**Verification:**
- `python -c "from app import main"` 不报错

---

## Task 2: 数据层 - Database

**Files:**
- 创建: `data/__init__.py`
- 创建: `data/database.py`
- 创建: `tests/conftest.py`
- 创建: `tests/test_data/__init__.py`
- 创建: `tests/test_data/test_database.py`

**Test First:**
1. 测试 Database 单例模式
2. 测试数据库连接获取
3. 测试表初始化

Steps:
1. 创建测试文件
2. 实现 Database 类（单例 + 内存数据库）
3. 实现 Schema 初始化
4. 运行测试

**Verification:**
- `pytest tests/test_data/test_database.py -v`

---

## Task 3: 数据层 - Models

**Files:**
- 创建: `data/models/__init__.py`
- 创建: `data/models/department.py`
- 创建: `data/models/employee.py`
- 创建: `tests/test_data/test_models.py`

**Test First:**
1. 测试 Department dataclass 创建
2. 测试 Employee dataclass 创建
3. 测试 from_row 工厂方法

Steps:
1. 创建测试文件
2. 实现 Department dataclass
3. 实现 Employee dataclass
4. 实现 from_row 方法
5. 运行测试

**Verification:**
- `pytest tests/test_data/test_models.py -v`

---

## Task 4: 数据层 - Repositories

**Files:**
- 创建: `data/repositories/__init__.py`
- 创建: `data/repositories/department_repository.py`
- 创建: `data/repositories/employee_repository.py`
- 创建: `tests/test_data/test_department_repository.py`
- 创建: `tests/test_data/test_employee_repository.py`

**Test First:**
1. 测试 DepartmentRepository.count()
2. 测试 DepartmentRepository.save()
3. 测试 EmployeeRepository.count()
4. 测试 EmployeeRepository.save()
5. 测试 EmployeeRepository.get_stats_by_department()

Steps:
1. 创建测试文件
2. 实现 BaseRepository 基类
3. 实现 DepartmentRepository
4. 实现 EmployeeRepository
5. 运行测试

**Verification:**
- `pytest tests/test_data/ -v`

---

## Task 5: 核心层 - Excel Processor

**Files:**
- 创建: `core/__init__.py`
- 创建: `core/excel_processor.py`
- 创建: `tests/test_core/__init__.py`
- 创建: `tests/test_core/test_excel_processor.py`

**Test First:**
1. 测试 import_excel() 成功导入
2. 测试 import_excel() 处理无效文件
3. 测试 get_department_tree()

Steps:
1. 创建测试文件
2. 实现 ExcelProcessor.import_excel()
3. 实现 ExcelProcessor.get_department_tree()
4. 运行测试

**Verification:**
- `pytest tests/test_core/test_excel_processor.py -v`

---

## Task 6: 核心层 - PPT Generator

**Files:**
- 创建: `core/ppt_generator.py`
- 创建: `tests/test_core/test_ppt_generator.py`

**Test First:**
1. 测试 generate() 创建 PPT 文件
2. 测试部门树绘制
3. 测试员工统计表格

Steps:
1. 创建测试文件
2. 实现 PPTGenerator 类
3. 实现部门树绘制
4. 实现员工统计表格
5. 运行测试

**Verification:**
- `pytest tests/test_core/test_ppt_generator.py -v`

---

## Task 7: 组件层 - StatusCardWidget

**Files:**
- 创建: `app/components/__init__.py`
- 创建: `app/components/status_card_widget.py`
- 创建: `tests/test_components/__init__.py`
- 创建: `tests/test_components/test_status_card.py`

**Test First:**
1. 测试组件创建
2. 测试 setValue() 方法

Steps:
1. 创建测试文件
2. 实现 StatusCardWidget（继承 SimpleCardWidget）
3. 运行测试

**Verification:**
- `pytest tests/test_components/test_status_card.py -v`

---

## Task 8: 组件层 - FileSelectorWidget

**Files:**
- 创建: `app/components/file_selector_widget.py`
- 创建: `tests/test_components/test_file_selector.py`

**Test First:**
1. 测试组件创建
2. 测试 pathChanged 信号

Steps:
1. 创建测试文件
2. 实现 FileSelectorWidget（继承 CardWidget）
3. 运行测试

**Verification:**
- `pytest tests/test_components/test_file_selector.py -v`

---

## Task 9: Common 模块

**Files:**
- 创建: `app/common/__init__.py`
- 创建: `app/common/config.py`
- 创建: `app/common/signal_bus.py`
- 创建: `app/common/style_sheet.py`

Steps:
1. 创建配置类（使用 QConfig）
2. 创建信号总线
3. 创建 StyleSheet 枚举

**Verification:**
- `python -c "from app.common import config, signal_bus"` 不报错

---

## Task 10: 视图层 - ExcelPPTInterface

**Files:**
- 创建: `app/view/__init__.py`
- 创建: `app/view/excel_ppt_interface.py`
- 创建: `tests/test_views/__init__.py`
- 创建: `tests/test_views/test_excel_ppt_interface.py`

**Test First:**
1. 测试页面创建
2. 测试导入按钮点击
3. 测试生成按钮状态变化

Steps:
1. 创建测试文件
2. 实现 ExcelPPTInterface（继承 ScrollArea）
3. 连接组件信号
4. 运行测试

**Verification:**
- `pytest tests/test_views/test_excel_ppt_interface.py -v`

---

## Task 11: 视图层 - MainWindow

**Files:**
- 创建: `app/view/main_window.py`
- 创建: `tests/test_views/test_main_window.py`

**Test First:**
1. 测试窗口创建
2. 测试导航初始化

Steps:
1. 创建测试文件
2. 实现 MainWindow（继承 FluentWindow）
3. 运行测试

**Verification:**
- `pytest tests/test_views/test_main_window.py -v`

---

## Task 12: 集成测试

**Files:**
- 创建: `tests/test_integration/__init__.py`
- 创建: `tests/test_integration/test_full_workflow.py`

Steps:
1. 创建集成测试
2. 测试完整流程：导入 → 生成

**Verification:**
- `pytest tests/test_integration/ -v`

---

## Task 13: 最终验证

Steps:
1. 运行所有测试: `pytest tests/ -v`
2. 手动启动应用: `python app/main.py`
3. 测试完整功能

**Verification:**
- 所有测试通过
- 应用正常启动
- 功能正常工作
