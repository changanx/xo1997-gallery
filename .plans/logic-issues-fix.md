---
name: 逻辑问题修复计划
description: 修复代码审查发现的 P0/P1/P2 级别问题
created: 2026-04-12
status: in_progress
completed_phase: 2
---

# 逻辑问题修复计划

## 概述

基于代码审查发现的问题，按优先级和依赖关系制定修复计划。

**问题统计：**
- P0（必须修复）：8 个
- P1（建议修复）：14 个
- P2（可选改进）：6 个

---

## 阶段一：安全阻塞问题（P0）✅ 已完成

### 1.1 命令注入漏洞修复 ✅

**问题：** `run_command` 使用 `shell=True` 且黑名单可绕过

**文件：** `core/tools/execute_tools.py`

**修复方案：**
- [x] 移除 `shell=True`，使用参数列表模式
- [x] 实现命令白名单机制
- [x] 添加参数验证
- [x] 更新相关测试

---

### 1.2 API Key 加密存储 ⏸️ 暂缓

**问题：** API Key 明文存储在数据库中

**修复方案：**
- [ ] 添加加密/解密工具函数
- [ ] 修改模型和仓库
- [ ] 添加数据迁移逻辑

**说明：** 此修改涉及数据迁移风险，需要更充分的测试，建议单独处理。

---

### 1.3 SecurityContext 符号链接检测 ✅

**问题：** 路径验证可被符号链接绕过

**文件：** `core/tools/base.py`

**修复方案：**
- [x] 添加符号链接检测逻辑
- [x] 修改 `is_safe_path` 方法
- [x] 使用严格路径比较替代 `startswith`
- [x] 更新测试用例

---

### 1.4 消息保存静默失败修复 ✅

**问题：** `message.id` 非空时不执行任何操作

**文件：**
- `data/repositories/ai_config_repository.py`
- `data/repositories/group_chat_repository.py`

**修复方案：**
- [x] 修改 `ChatMessageRepository.save()` 方法
- [x] 修改 `GroupChatMessageRepository.save()` 方法
- [x] 当 `id` 非空时抛出明确异常
- [x] 添加 `update_content()` 方法

---

### 1.5 群聊并发错误处理 ✅

**问题：** 并发调用时异常处理不完善，响应可能丢失

**文件：** `core/group_chat_manager.py`

**修复方案：**
- [x] 在 `_call_models_concurrent` 外层添加 try-except
- [x] 确保所有异常都 yield 错误事件
- [x] 添加超时控制
- [x] 限制并发数量 (max_workers=min(len(participants), 5))

---

### 1.6 工具调用 JSON 解析错误处理 ✅

**问题：** JSON 解析失败时静默返回 `{"raw": ...}`

**文件：** `core/model_manager.py`

**修复方案：**
- [x] 添加日志记录解析失败
- [x] 返回包含错误信息的结构 (`_parse_error`, `_raw_args`)
- [x] 在工具执行时检查 `_parse_error`
- [x] 更新测试用例

---

### 1.7 群聊上下文构建修复 ✅

**问题：** 串行讨论时看不到最新响应

**文件：** `core/group_chat_manager.py`

**修复方案：**
- [x] 在每轮讨论前重新构建 context
- [x] 修复 `_call_models_serial` yield complete 事件

---

### 1.8 测试数据库修复 ✅

**问题：** 测试清空了错误的数据库

**文件：**
- `tests/test_data/test_ai_config_repository.py`
- `tests/test_data/test_group_chat_repository.py`

**修复方案：**
- [x] 移除测试文件中的 `db.clear()` 调用
- [x] 依赖 `conftest.py` 中的 `clean_persistent_db` fixture

---

## 阶段二：稳定性问题（P1）✅ 已完成

### 2.1 ChatWorker 线程安全 ✅

**问题：** 快速发送消息时多个 worker 同时运行

**文件：** `app/view/ai_chat_interface.py`

**修复方案：**
- [x] 在 `_sendMessage` 前检查 worker 是否运行
- [x] 移除 QThread 的 parent 设置
- [x] 添加等待线程结束逻辑

---

### 2.2 SQLite 多线程支持 ✅

**问题：** 多线程访问可能导致数据库锁定

**文件：** `data/database.py`

**修复方案：**
- [x] 启用 WAL 模式
- [x] 添加 `busy_timeout` 设置 (5 秒)

---

### 2.3 Excel 导入事务保护 ✅

**问题：** 导入失败时数据丢失

**文件：** `core/excel_processor.py`

**修复方案：**
- [x] 使用 `db.transaction()` 包裹导入操作
- [x] 失败时自动回滚

---

### 2.4 群聊状态一致性 ✅

**问题：** `_mentioned_models` 状态管理混乱

**文件：** `app/view/group_chat_interface.py`

**修复方案：**
- [x] 使用 `blockSignals` 修复 `_clearMentions`
- [x] 先清空集合再更新复选框

---

### 2.5 日志窗口信号管理 ✅

**问题：** 重复连接导致日志多次显示

**文件：** `app/components/log_viewer_window.py`

**修复方案：**
- [x] 连接前断开旧连接
- [x] 添加 `closeEvent` 断开连接

---

### 2.6 数据库路径变更处理 ⏸️ 暂缓

**问题：** 路径变更时数据丢失

**说明：** 需要用户交互确认，建议作为单独功能实现

---

### 2.7 set_default 事务保护 ✅

**问题：** 可能产生多个默认模型

**文件：** `data/repositories/ai_config_repository.py`

**修复方案：**
- [x] 使用单条 SQL 语句（CASE WHEN）确保原子性

---

### 2.8 @提及支持中文昵称 ✅

**问题：** 正则 `\w` 不匹配中文

**文件：** `core/group_chat_manager.py`

**修复方案：**
- [x] 修改正则为 `r'@([\w\u4e00-\u9fff]+)'`

---

### 2.9 工具执行速率限制 ⏸️ 暂缓

**问题：** 短时间内可能执行大量工具

**说明：** 需要用户确认机制，建议作为可选功能实现

---

### 2.10 外键约束处理 ⏸️ 暂缓

**问题：** 删除被引用的模型配置失败

**说明：** 需要业务层处理关联删除逻辑，建议作为单独功能实现

---

## 阶段二：稳定性问题（P1）

预计耗时：3-4 小时

### 2.1 ChatWorker 线程安全

**问题：** 快速发送消息时多个 worker 同时运行

**文件：** `app/view/ai_chat_interface.py`

**修复方案：**
- [ ] 在 `_sendMessage` 前检查 worker 是否运行
- [ ] 移除 QThread 的 parent 设置
- [ ] 添加窗口关闭时的线程清理

---

### 2.2 SQLite 多线程支持

**问题：** 多线程访问可能导致数据库锁定

**文件：** `data/database.py`

**修复方案：**
- [ ] 启用 WAL 模式
- [ ] 添加 `busy_timeout` 设置
- [ ] 考虑连接池或线程局部连接

---

### 2.3 Excel 导入事务保护

**问题：** 导入失败时数据丢失

**文件：** `core/excel_processor.py`

**修复方案：**
- [ ] 使用事务包裹导入操作
- [ ] 添加回滚逻辑

---

### 2.4 群聊状态一致性

**问题：** `_mentioned_models` 状态管理混乱

**文件：** `app/view/group_chat_interface.py`

**修复方案：**
- [ ] 使用 `blockSignals` 修复 `_clearMentions`
- [ ] 确保状态更新顺序正确

---

### 2.5 日志窗口信号管理

**问题：** 重复连接导致日志多次显示

**文件：** `app/components/log_viewer_window.py`

**修复方案：**
- [ ] 连接前断开旧连接
- [ ] 使用弱引用或单例模式

---

### 2.6 数据库路径变更处理

**问题：** 路径变更时数据丢失

**文件：** `data/database.py`, `app/common/storage_config.py`

**修复方案：**
- [ ] 添加数据迁移选项
- [ ] 发出明确警告

---

### 2.7 set_default 事务保护

**问题：** 可能产生多个默认模型

**文件：** `data/repositories/ai_config_repository.py`

**修复方案：**
- [ ] 使用事务或合并为单条 SQL

---

### 2.8 @提及支持中文昵称

**问题：** 正则 `\w` 不匹配中文

**文件：** `core/group_chat_manager.py`

**修复方案：**
- [ ] 修改正则为 `r'@([^\s@]+)'` 或 `r'@([\w\u4e00-\u9fff]+)'`

---

### 2.9 工具执行速率限制

**问题：** 短时间内可能执行大量工具

**文件：** `core/model_manager.py`

**修复方案：**
- [ ] 添加速率限制机制
- [ ] 对破坏性操作添加确认（可选）

---

### 2.10 外键约束处理

**问题：** 删除被引用的模型配置失败

**文件：** `data/database.py`

**修复方案：**
- [ ] 添加 `ON DELETE CASCADE` 或 `ON DELETE SET NULL`
- [ ] 或在业务层处理关联删除

---

## 阶段三：代码质量改进（P2）

预计耗时：2 小时

### 3.1 PPT 生成路径验证

- [ ] 检查输出目录是否存在
- [ ] 自动创建父目录
- [ ] 检查写入权限

### 3.2 Excel 列名验证

- [ ] 导入前检查必需列
- [ ] 给出明确的错误提示

### 3.3 数据模型验证

- [ ] 在 `from_row` 中添加基本验证
- [ ] 对关键字段使用枚举

### 3.4 JSON 解析日志

- [ ] 解析失败时记录警告日志

### 3.5 敏感信息脱敏

- [ ] 日志中脱敏工具参数
- [ ] 完全不记录 API Key

### 3.6 会话状态同步

- [ ] 会话创建失败时恢复 UI 状态

---

## 执行顺序

```
阶段一（P0）必须完成才能发布
├── 1.1 命令注入 ──────┐
├── 1.2 API Key 加密 ──┼── 无依赖，可并行
├── 1.3 符号链接检测 ──┘
├── 1.4 消息保存 ──────┐
├── 1.5 群聊并发 ──────┼── 无依赖，可并行
├── 1.6 JSON 解析 ─────┘
├── 1.7 群聊上下文 ────→ 依赖 1.5
└── 1.8 测试数据库 ────→ 最后执行，验证修复

阶段二（P1）
├── 2.1 ChatWorker ────┐
├── 2.2 SQLite WAL ────┼── 无依赖，可并行
├── 2.3 Excel 事务 ────┘
├── 2.4 群聊状态 ──────→ 依赖 1.5
├── 2.5 日志窗口 ──────┐
├── 2.6 路径变更 ──────┼── 无依赖，可并行
├── 2.7 set_default ───┤
├── 2.8 中文昵称 ──────┤
├── 2.9 速率限制 ──────┤
└── 2.10 外键约束 ─────┘

阶段三（P2）可选
└── 3.1 ~ 3.6 可按需执行
```

---

## 验证清单

每个阶段完成后：

- [ ] 所有测试通过 (`pytest`)
- [ ] 覆盖率达标
- [ ] 手动测试核心功能
- [ ] 代码审查确认

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| API Key 加密迁移失败 | 用户配置丢失 | 提供降级方案，保留明文读取能力 |
| WAL 模式兼容性 | 旧版 SQLite 不支持 | 检测 SQLite 版本，降级处理 |
| 命令白名单限制 | 用户功能受限 | 提供配置文件扩展白名单 |

---

## 预计总耗时

- 阶段一：2-3 小时
- 阶段二：3-4 小时
- 阶段三：2 小时

**总计：7-9 小时**
