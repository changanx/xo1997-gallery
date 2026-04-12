"""
群聊管理器 - 多模型群聊功能
"""
import re
import json
import concurrent.futures
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass

from data.database import db
from data.models.group_chat import GroupChatSession, GroupChatParticipant, GroupChatMessage
from data.models.ai_config import AIModelConfig
from data.repositories.group_chat_repository import (
    GroupChatSessionRepository,
    GroupChatParticipantRepository,
    GroupChatMessageRepository,
)
from data.repositories.ai_config_repository import AIModelConfigRepository
from core.model_manager import ModelManager, MODEL_PROVIDERS
from core.tools import SecurityContext, create_all_tools
from app.common.logger import get_logger

logger = get_logger()


# 预设角色模板
ROLE_TEMPLATES = {
    "代码审查专家": """你是代码审查专家，专注于：
- 代码质量和可维护性
- 设计模式应用
- 潜在 bug 发现
- 代码规范检查""",

    "架构分析师": """你是架构分析师，专注于：
- 系统架构设计
- 模块划分和依赖关系
- 技术选型建议
- 扩展性和性能考量""",

    "性能优化师": """你是性能优化师，专注于：
- 性能瓶颈分析
- 算法复杂度优化
- 资源使用效率
- 并发和缓存策略""",

    "测试工程师": """你是测试工程师，专注于：
- 测试用例设计
- 边界条件分析
- 回归测试策略
- 自动化测试方案""",

    "安全审计员": """你是安全审计员，专注于：
- 安全漏洞检测
- 权限和认证问题
- 数据安全建议
- 最佳安全实践""",

    "自定义": "",
}


@dataclass
class ModelInstance:
    """模型实例，包含模型对象和配置"""
    model: Any
    config: AIModelConfig
    participant: GroupChatParticipant


class GroupChatManager:
    """群聊管理器"""

    def __init__(self):
        self._session_repo = GroupChatSessionRepository()
        self._participant_repo = GroupChatParticipantRepository()
        self._message_repo = GroupChatMessageRepository()
        self._model_config_repo = AIModelConfigRepository()

        # 会话相关的模型实例缓存
        # session_id -> {model_config_id -> ModelInstance}
        self._session_models: Dict[int, Dict[int, ModelInstance]] = {}

        # 工具相关
        self._security_context: Optional[SecurityContext] = None
        self._tools: List[Any] = []

        # 当前会话
        self._current_session_id: Optional[int] = None

    # ==================== 会话管理 ====================

    def create_session(self, title: str = "新群聊", max_rounds: int = 3) -> GroupChatSession:
        """创建群聊会话"""
        session = GroupChatSession(title=title, max_discussion_rounds=max_rounds)
        session = self._session_repo.save(session)
        self._session_models[session.id] = {}
        logger.info("创建群聊会话", extra={"session_id": session.id, "title": title})
        return session

    def get_session(self, session_id: int) -> Optional[GroupChatSession]:
        """获取群聊会话"""
        return self._session_repo.find_by_id(session_id)

    def get_all_sessions(self, limit: int = 50) -> List[GroupChatSession]:
        """获取所有群聊会话"""
        return self._session_repo.find_all(limit)

    def delete_session(self, session_id: int) -> bool:
        """删除群聊会话"""
        if session_id in self._session_models:
            del self._session_models[session_id]
        return self._session_repo.delete(session_id)

    def set_current_session(self, session_id: int) -> bool:
        """设置当前会话"""
        session = self.get_session(session_id)
        if session:
            self._current_session_id = session_id
            # 确保模型实例已加载
            self._ensure_models_loaded(session_id)
            return True
        return False

    def get_current_session(self) -> Optional[GroupChatSession]:
        """获取当前会话"""
        if self._current_session_id:
            return self.get_session(self._current_session_id)
        return None

    # ==================== 参与者管理 ====================

    def add_participant(
        self,
        session_id: int,
        model_config_id: int,
        nickname: str = "",
        role_description: str = ""
    ) -> Optional[GroupChatParticipant]:
        """添加参与者"""
        # 检查模型配置是否存在
        config = self._model_config_repo.find_by_id(model_config_id)
        if not config:
            logger.warning("模型配置不存在", extra={"model_config_id": model_config_id})
            return None

        # 检查是否已存在
        existing = self._participant_repo.find_by_session_and_model(session_id, model_config_id)
        if existing:
            logger.warning("参与者已存在", extra={"session_id": session_id, "model_config_id": model_config_id})
            return None

        # 生成默认昵称
        if not nickname:
            nickname = f"@{config.name.lower().replace(' ', '_')}"

        participant = GroupChatParticipant(
            session_id=session_id,
            model_config_id=model_config_id,
            nickname=nickname,
            role_description=role_description
        )
        participant = self._participant_repo.save(participant)

        # 创建模型实例
        self._create_model_instance(session_id, participant, config)

        logger.info("添加参与者", extra={
            "session_id": session_id,
            "model_config_id": model_config_id,
            "nickname": nickname
        })
        return participant

    def remove_participant(self, participant_id: int) -> bool:
        """移除参与者"""
        participant = self._participant_repo.find_by_id(participant_id)
        if not participant:
            return False

        session_id = participant.session_id
        model_config_id = participant.model_config_id

        # 从缓存中移除
        if session_id in self._session_models:
            if model_config_id in self._session_models[session_id]:
                del self._session_models[session_id][model_config_id]

        return self._participant_repo.delete(participant_id)

    def get_participants(self, session_id: int) -> List[GroupChatParticipant]:
        """获取会话的所有参与者"""
        return self._participant_repo.find_by_session(session_id)

    def update_participant(
        self,
        participant_id: int,
        nickname: str = None,
        role_description: str = None
    ) -> Optional[GroupChatParticipant]:
        """更新参与者信息"""
        participant = self._participant_repo.find_by_id(participant_id)
        if not participant:
            return None

        if nickname is not None:
            participant.nickname = nickname
        if role_description is not None:
            participant.role_description = role_description

        participant = self._participant_repo.save(participant)

        # 更新模型实例
        session_id = participant.session_id
        if session_id in self._session_models:
            if participant.model_config_id in self._session_models[session_id]:
                self._session_models[session_id][participant.model_config_id].participant = participant

        return participant

    # ==================== 消息管理 ====================

    def get_messages(self, session_id: int) -> List[GroupChatMessage]:
        """获取会话的所有消息"""
        return self._message_repo.find_by_session(session_id)

    def clear_messages(self, session_id: int) -> int:
        """清空会话消息"""
        return self._message_repo.delete_by_session(session_id)

    # ==================== 工具管理 ====================

    def set_work_directory(self, directory: str) -> None:
        """设置工作目录并创建工具"""
        self._security_context = SecurityContext(directory)
        self._tools = create_all_tools(self._security_context)

        # 绑定工具到所有模型
        for session_id, models in self._session_models.items():
            for model_instance in models.values():
                if self._tools:
                    model_instance.model = model_instance.model.bind_tools(self._tools)

        logger.info("群聊工作目录已设置", extra={"directory": directory})

    def has_tools(self) -> bool:
        """检查是否已设置工具"""
        return len(self._tools) > 0

    # ==================== 核心对话功能 ====================

    def chat(
        self,
        user_message: str,
        mentioned_model_ids: List[int] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """
        发送消息并获取多模型回复

        流程：
        1. 保存用户消息
        2. 确定回复的模型列表
        3. 并发调用模型
        4. 串行讨论（每轮重新构建上下文）
        5. 判断讨论结束

        Yields:
            {"type": "thinking/content/tool_call/tool_result", ...}
        """
        if not self._current_session_id:
            raise RuntimeError("请先设置当前会话")

        session_id = self._current_session_id
        session = self.get_session(session_id)
        if not session:
            raise RuntimeError("会话不存在")

        participants = self.get_participants(session_id)
        if not participants:
            raise RuntimeError("会话没有参与者")

        # 确保模型已加载
        self._ensure_models_loaded(session_id)

        # 解析 @ 提及
        if mentioned_model_ids is None:
            mentioned_model_ids = self.parse_mentions(user_message, participants)

        # 确定回复的模型
        if mentioned_model_ids:
            replying_models = [
                p for p in participants
                if p.model_config_id in mentioned_model_ids
            ]
        else:
            replying_models = participants  # 默认全部回复

        if not replying_models:
            yield {"type": "content", "text": "没有可用的模型回复"}
            return

        # 获取当前讨论轮次
        current_round = self._message_repo.find_latest_round(session_id)

        # 保存用户消息
        user_msg = GroupChatMessage(
            session_id=session_id,
            role="user",
            content=user_message,
            mentioned_models=mentioned_model_ids,
            discussion_round=current_round
        )
        self._message_repo.save(user_msg)

        # 构建上下文（包含用户消息）
        context = self._build_context(session_id)

        # 首批并发回复
        yield {"type": "round_start", "round": current_round + 1}

        responses = []
        for event in self._call_models_concurrent(replying_models, context):
            yield event
            if event.get("type") == "model_response_complete":
                responses.append(event.get("content", ""))

        # 串行讨论
        discussion_round = current_round + 1
        while self._should_continue_discussion(responses, discussion_round, session.max_discussion_rounds):
            discussion_round += 1
            yield {"type": "round_start", "round": discussion_round}

            # 关键修复：每轮讨论前重新构建上下文，包含最新的消息
            context = self._build_context(session_id)

            round_responses = []
            for event in self._call_models_serial(participants, context, discussion_round):
                yield event
                if event.get("type") == "model_response_complete":
                    round_responses.append(event.get("content", ""))

            if not round_responses:
                break
            responses = round_responses

        yield {"type": "discussion_end"}

    def parse_mentions(self, content: str, participants: List[GroupChatParticipant]) -> List[int]:
        """解析消息中的 @ 提及（支持中文昵称）"""
        mentioned_ids = []

        # 匹配 @nickname，支持中文、字母、数字、下划线
        # 使用 Unicode 范围匹配中文字符
        pattern = r'@([\w\u4e00-\u9fff]+)'
        matches = re.findall(pattern, content)

        for match in matches:
            for p in participants:
                # 支持 @nickname 或 @name（去掉 @ 前缀）
                nick = p.nickname.lstrip('@')
                if nick.lower() == match.lower():
                    mentioned_ids.append(p.model_config_id)
                    break

        return list(set(mentioned_ids))  # 去重

    # ==================== 内部方法 ====================

    def _ensure_models_loaded(self, session_id: int) -> None:
        """确保会话的模型实例已加载"""
        if session_id not in self._session_models:
            self._session_models[session_id] = {}

        participants = self.get_participants(session_id)
        for p in participants:
            if p.model_config_id not in self._session_models[session_id]:
                config = self._model_config_repo.find_by_id(p.model_config_id)
                if config:
                    self._create_model_instance(session_id, p, config)

    def _create_model_instance(
        self,
        session_id: int,
        participant: GroupChatParticipant,
        config: AIModelConfig
    ) -> ModelInstance:
        """创建模型实例"""
        manager = ModelManager()
        model = manager.create_chat_model(config)

        # 绑定工具
        if self._tools:
            model = model.bind_tools(self._tools)

        instance = ModelInstance(
            model=model,
            config=config,
            participant=participant
        )

        if session_id not in self._session_models:
            self._session_models[session_id] = {}
        self._session_models[session_id][participant.model_config_id] = instance

        return instance

    def _build_system_prompt(
        self,
        participant: GroupChatParticipant,
        all_participants: List[GroupChatParticipant]
    ) -> str:
        """构建带角色描述的 system prompt"""
        others = [p.nickname for p in all_participants if p.id != participant.id]

        prompt = f"""你正在参与一个多模型群聊讨论。

你的昵称是: {participant.nickname}
其他参与者: {', '.join(others) if others else '无'}

{participant.role_description if participant.role_description else '你是一个 AI 助手，专注于提供有价值的见解。'}

当回复时：
1. 你可以引用其他模型的发言，例如："我同意 {others[0] if others else ''} 的观点..."
2. 如果用户 @ 了你，你应该优先回复
3. 如果你认为讨论已经结束，请在回复末尾说 [讨论结束]
4. 保持回复简洁，不要重复其他参与者已经说过的内容
"""
        return prompt

    def _build_context(self, session_id: int) -> List[Dict]:
        """构建对话上下文"""
        messages = self.get_messages(session_id)
        participants = self.get_participants(session_id)
        participant_map = {p.model_config_id: p for p in participants}

        context = []
        for msg in messages:
            if msg.role == "user":
                context.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.role == "assistant":
                participant = participant_map.get(msg.model_config_id)
                if participant:
                    # 在内容前加上模型标识
                    content = f"[{participant.nickname}]: {msg.content}"
                    context.append({
                        "role": "assistant",
                        "content": content
                    })

        return context

    def _call_models_concurrent(
        self,
        participants: List[GroupChatParticipant],
        context: List[Dict],
        timeout_per_model: int = 120
    ) -> Generator[Dict[str, Any], None, None]:
        """
        并发调用多个模型

        Args:
            participants: 参与者列表
            context: 对话上下文
            timeout_per_model: 每个模型的超时时间（秒）

        Yields:
            模型响应事件
        """
        session_id = self._current_session_id
        all_participants = self.get_participants(session_id)

        def call_model(participant: GroupChatParticipant):
            """调用单个模型"""
            model_instance = self._session_models[session_id].get(participant.model_config_id)
            if not model_instance:
                return participant.model_config_id, [], "模型实例未找到"

            system_prompt = self._build_system_prompt(participant, all_participants)
            messages = [{"role": "system", "content": system_prompt}] + context

            chunks = []
            try:
                for chunk in model_instance.model.stream(messages):
                    chunks.append(chunk)
            except Exception as e:
                logger.error("模型调用失败", extra={
                    "model": participant.nickname,
                    "error": str(e)
                })
                return participant.model_config_id, [], str(e)

            return participant.model_config_id, chunks, None

        # 限制并发数量，避免资源耗尽
        max_workers = min(len(participants), 5)

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(call_model, p): p
                    for p in participants
                }

                for future in concurrent.futures.as_completed(futures, timeout=timeout_per_model * len(participants)):
                    participant = futures[future]

                    yield {
                        "type": "model_response_start",
                        "model_config_id": participant.model_config_id,
                        "nickname": participant.nickname
                    }

                    try:
                        model_config_id, chunks, error = future.result(timeout=timeout_per_model)

                        if error:
                            yield {
                                "type": "content",
                                "model_config_id": model_config_id,
                                "text": f"错误: {error}"
                            }
                        else:
                            try:
                                content = self._process_model_chunks(model_config_id, chunks, participant)
                                yield {
                                    "type": "model_response_complete",
                                    "model_config_id": model_config_id,
                                    "content": content
                                }
                            except Exception as e:
                                logger.error("处理模型输出失败", extra={
                                    "model": participant.nickname,
                                    "error": str(e)
                                })
                                yield {
                                    "type": "content",
                                    "model_config_id": participant.model_config_id,
                                    "text": f"处理响应失败: {str(e)}"
                                }
                    except concurrent.futures.TimeoutError:
                        logger.warning("模型调用超时", extra={"model": participant.nickname})
                        yield {
                            "type": "content",
                            "model_config_id": participant.model_config_id,
                            "text": f"错误: 模型响应超时 ({timeout_per_model}秒)"
                        }
                    except Exception as e:
                        logger.error("Future 执行异常", extra={
                            "model": participant.nickname,
                            "error": str(e)
                        })
                        yield {
                            "type": "content",
                            "model_config_id": participant.model_config_id,
                            "text": f"错误: {str(e)}"
                        }

                    yield {
                        "type": "model_response_end",
                        "model_config_id": participant.model_config_id,
                        "nickname": participant.nickname
                    }

        except concurrent.futures.TimeoutError:
            logger.error("整体并发调用超时")
            yield {"type": "content", "text": "错误: 整体响应超时"}
        except Exception as e:
            logger.error("并发调用异常", extra={"error": str(e)})
            yield {"type": "content", "text": f"错误: {str(e)}"}

    def _call_models_serial(
        self,
        participants: List[GroupChatParticipant],
        context: List[Dict],
        round_num: int
    ) -> Generator[Dict[str, Any], None, None]:
        """串行调用多个模型（用于讨论阶段）"""
        session_id = self._current_session_id
        all_participants = self.get_participants(session_id)

        for participant in participants:
            model_instance = self._session_models[session_id].get(participant.model_config_id)
            if not model_instance:
                continue

            yield {
                "type": "model_response_start",
                "model_config_id": participant.model_config_id,
                "nickname": participant.nickname
            }

            system_prompt = self._build_system_prompt(participant, all_participants)
            # 添加讨论轮次提示
            system_prompt += f"\n\n当前是第 {round_num} 轮讨论。请基于之前的讨论继续发言，或者使用 [讨论结束] 标记结束。"

            messages = [{"role": "system", "content": system_prompt}] + context

            try:
                chunks = list(model_instance.model.stream(messages))
                content = self._process_model_chunks(participant.model_config_id, chunks, participant, round_num)
                yield {
                    "type": "model_response_complete",
                    "model_config_id": participant.model_config_id,
                    "content": content
                }
            except Exception as e:
                logger.error("模型调用失败", extra={
                    "model": participant.nickname,
                    "error": str(e)
                })
                yield {
                    "type": "content",
                    "model_config_id": participant.model_config_id,
                    "text": f"错误: {e}"
                }

            yield {
                "type": "model_response_end",
                "model_config_id": participant.model_config_id,
                "nickname": participant.nickname
            }

    def _process_model_chunks(
        self,
        model_config_id: int,
        chunks: List,
        participant: GroupChatParticipant,
        round_num: int = None
    ) -> str:
        """处理模型输出块并保存消息"""
        content = ""
        thinking = ""
        tool_calls = []

        for chunk in chunks:
            # 处理思考过程
            if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                reasoning = chunk.additional_kwargs.get('reasoning_content', '')
                if reasoning:
                    thinking += reasoning

            # 处理内容
            if hasattr(chunk, 'content') and chunk.content:
                if isinstance(chunk.content, list):
                    for block in chunk.content:
                        if isinstance(block, dict):
                            if block.get('type') == 'thinking':
                                thinking += block.get('thinking', '')
                            elif block.get('type') == 'text':
                                content += block.get('text', '')
                        elif hasattr(block, 'type'):
                            if block.type == 'thinking' and hasattr(block, 'thinking'):
                                thinking += block.thinking
                            elif block.type == 'text' and hasattr(block, 'text'):
                                content += block.text
                else:
                    content += str(chunk.content)

            # 收集工具调用
            if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
                tool_calls.extend(chunk.tool_call_chunks)

        # 保存消息
        session_id = self._current_session_id
        if round_num is None:
            round_num = self._message_repo.find_latest_round(session_id)

        msg = GroupChatMessage(
            session_id=session_id,
            role="assistant",
            model_config_id=model_config_id,
            content=content,
            discussion_round=round_num
        )
        self._message_repo.save(msg)

        return content

    def _should_continue_discussion(
        self,
        responses: List[str],
        current_round: int,
        max_rounds: int
    ) -> bool:
        """判断是否继续讨论"""
        if current_round >= max_rounds:
            return False

        # 检查是否有模型说 [讨论结束]
        for resp in responses:
            if "[讨论结束]" in resp:
                return False

        return True


# 全局群聊管理器实例
group_chat_manager = GroupChatManager()
