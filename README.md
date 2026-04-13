# xo1997 画廊

基于 PySide6 + QFluentWidgets 的桌面应用，集成 AI 智能助手和组织架构生成功能。

## 功能特性

### AI 助手
- 多模型支持：OpenAI、Anthropic、DeepSeek、Ollama、智谱 AI 等
- 工具调用：AI 可操作本地文件（需设置工作目录）
- 思考过程：支持显示模型推理过程
- 会话持久化：聊天记录自动保存

### 群聊模式
- 多 AI 模型群聊讨论
- 自定义角色描述
- @ 提及特定模型
- 可配置讨论轮次

### Excel → PPT
- 导入 Excel 员工数据
- 自动生成组织架构 PPT
- 支持多级部门结构
- 员工统计图表

## 技术栈

| 类别 | 技术 |
|------|------|
| GUI | PySide6 + QFluentWidgets |
| AI | LangChain |
| 数据 | SQLite（双数据库架构） |
| 办公 | pandas + openpyxl + python-pptx |

## 项目结构

```
app/           应用层（入口、视图、UI组件）
core/          业务层（Excel处理、PPT生成、AI模型管理）
data/          数据层（数据库、模型、仓库）
tests/         测试
```

## 快速开始

### 环境要求

- Python >= 3.11
- uv 包管理器（推荐）或 pip

### 安装

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

### 运行

```bash
# 使用 uv
uv run python -m app.main

# 或直接运行
python -m app.main
```

### 配置 AI 模型

1. 启动应用后，进入「AI 设置」页面
2. 点击「添加模型配置」
3. 填写 API Key 和模型信息
4. 或通过环境变量自动配置：
   ```bash
   export ANTHROPIC_AUTH_TOKEN=your_api_key
   export ANTHROPIC_BASE_URL=https://api.lkeap.cloud.tencent.com/coding/anthropic
   export ANTHROPIC_MODEL=glm-5
   ```

## 开发

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 带覆盖率报告
uv run pytest --cov=app --cov=core --cov=data --cov-report=html
```

### 代码规范

- 测试框架：pytest + pytest-qt
- 测试命名：`test_<模块名>.py`、`Test<类名>`、`test_<功能描述>`
- 覆盖率要求：数据层 ≥90%、核心层 ≥80%、组件层 ≥85%

## 数据存储

- 默认位置：`C:/ProgramData/xo1997-pyside-gallery/db`
- 可在「AI 设置」中更改存储位置
- 支持数据迁移

## 许可证

MIT License
