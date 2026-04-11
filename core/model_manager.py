"""
AI 模型管理器 - 基于 LangChain
"""
from typing import Optional, List, Dict, Any, Generator
from dataclasses import dataclass
import json
import uuid

from data.models.ai_config import AIModelConfig
from app.common.logger import get_logger

logger = get_logger()


@dataclass
class ModelProvider:
    """模型提供商配置"""
    id: str
    name: str
    default_base_url: str
    default_models: List[str]
    requires_api_key: bool = True
    supports_custom_url: bool = True


# 预定义的模型提供商
MODEL_PROVIDERS = {
    "tencent_claude": ModelProvider(
        id="tencent_claude",
        name="腾讯云 Claude",
        default_base_url="https://api.lkeap.cloud.tencent.com/coding/anthropic",
        default_models=["glm-5", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229"],
        requires_api_key=True,
        supports_custom_url=True,
    ),
    "openai": ModelProvider(
        id="openai",
        name="OpenAI",
        default_base_url="https://api.openai.com/v1",
        default_models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        requires_api_key=True,
        supports_custom_url=True,
    ),
    "azure": ModelProvider(
        id="azure",
        name="Azure OpenAI",
        default_base_url="",
        default_models=["gpt-4o", "gpt-4", "gpt-35-turbo"],
        requires_api_key=True,
        supports_custom_url=True,
    ),
    "anthropic": ModelProvider(
        id="anthropic",
        name="Anthropic",
        default_base_url="https://api.anthropic.com",
        default_models=["claude-opus-4-20250514", "claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"],
        requires_api_key=True,
        supports_custom_url=True,
    ),
    "deepseek": ModelProvider(
        id="deepseek",
        name="DeepSeek",
        default_base_url="https://api.deepseek.com/v1",
        default_models=["deepseek-chat", "deepseek-coder"],
        requires_api_key=True,
        supports_custom_url=True,
    ),
    "zhipu": ModelProvider(
        id="zhipu",
        name="智谱 AI",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
        default_models=["glm-4", "glm-4-flash", "glm-3-turbo"],
        requires_api_key=True,
        supports_custom_url=True,
    ),
    "ollama": ModelProvider(
        id="ollama",
        name="Ollama (本地)",
        default_base_url="http://localhost:11434",
        default_models=["llama3", "qwen2", "mistral", "codellama"],
        requires_api_key=False,
        supports_custom_url=True,
    ),
    "custom": ModelProvider(
        id="custom",
        name="自定义",
        default_base_url="",
        default_models=[],
        requires_api_key=False,
        supports_custom_url=True,
    ),
}


class ModelManager:
    """模型管理器"""

    def __init__(self):
        self._current_model: Optional[Any] = None
        self._current_config: Optional[AIModelConfig] = None
        self._tools: List[Any] = []
        self._tool_executors: Dict[str, Any] = {}  # 工具名 -> 执行函数
        self._work_directory: Optional[str] = None

    def get_provider(self, provider_id: str) -> Optional[ModelProvider]:
        """获取提供商配置"""
        return MODEL_PROVIDERS.get(provider_id)

    def get_all_providers(self) -> List[ModelProvider]:
        """获取所有提供商"""
        return list(MODEL_PROVIDERS.values())

    def set_work_directory(self, directory: str) -> None:
        """设置工作目录并创建工具"""
        from .tools import create_all_tools, SecurityContext

        self._work_directory = directory
        security = SecurityContext(directory)
        self._tools = create_all_tools(security)

        # 保存工具执行函数
        for tool in self._tools:
            self._tool_executors[tool.name] = tool.func

        logger.info("工作目录已设置", extra={"directory": directory, "tools_count": len(self._tools)})

        # 如果已有模型，绑定工具
        if self._current_model and self._tools:
            self._current_model = self._current_model.bind_tools(self._tools)
            logger.debug("工具已绑定到当前模型")

    def get_work_directory(self) -> Optional[str]:
        """获取当前工作目录"""
        return self._work_directory

    def has_tools(self) -> bool:
        """检查是否已设置工具"""
        return len(self._tools) > 0

    def create_chat_model(self, config: AIModelConfig) -> Any:
        """
        根据配置创建聊天模型

        Args:
            config: 模型配置

        Returns:
            LangChain 聊天模型实例
        """
        provider = config.provider
        model_kwargs = {
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }

        # 合并额外参数
        if config.extra_params:
            model_kwargs.update(config.extra_params)

        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key or None,
                base_url=config.base_url or None,
                **model_kwargs
            )

        elif provider == "tencent_claude":
            # 腾讯云 Claude 兼容 API (Anthropic 格式)
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config.model_name,
                api_key=config.api_key,
                anthropic_api_url=config.base_url or "https://api.lkeap.cloud.tencent.com/coding/anthropic",
                **model_kwargs
            )

        elif provider == "azure":
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_deployment=config.model_name,
                api_key=config.api_key,
                azure_endpoint=config.base_url,
                **model_kwargs
            )

        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config.model_name,
                api_key=config.api_key,
                **model_kwargs
            )

        elif provider == "deepseek":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url or "https://api.deepseek.com/v1",
                **model_kwargs
            )

        elif provider == "zhipu":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key,
                base_url=config.base_url or "https://open.bigmodel.cn/api/paas/v4",
                **model_kwargs
            )

        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=config.model_name,
                base_url=config.base_url or "http://localhost:11434",
                **model_kwargs
            )

        elif provider == "custom":
            # 自定义 OpenAI 兼容 API
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config.model_name,
                api_key=config.api_key or "none",
                base_url=config.base_url,
                **model_kwargs
            )

        else:
            raise ValueError(f"不支持的模型提供商: {provider}")

    def set_current_model(self, config: AIModelConfig) -> None:
        """设置当前使用的模型"""
        logger.info("切换模型", extra={"provider": config.provider, "model": config.model_name})
        self._current_model = self.create_chat_model(config)
        self._current_config = config

        # 如果已有工具，绑定到新模型
        if self._current_model and self._tools:
            self._current_model = self._current_model.bind_tools(self._tools)
            logger.debug("工具已绑定到新模型")

    def get_current_model(self) -> Optional[Any]:
        """获取当前模型"""
        return self._current_model

    def get_current_config(self) -> Optional[AIModelConfig]:
        """获取当前模型配置"""
        return self._current_config

    def chat(self, messages: List[Dict[str, str]], stream: bool = True) -> Generator[Dict[str, str], None, None]:
        """
        发送消息并获取响应

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            stream: 是否流式输出

        Yields:
            响应字典 {"type": "thinking"|"content", "text": "..."}
        """
        if self._current_model is None:
            raise RuntimeError("请先设置模型")

        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        # 转换消息格式
        lc_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))

        if stream:
            for chunk in self._current_model.stream(lc_messages):
                # 处理思考过程 (DeepSeek/腾讯云 glm-5 等)
                if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                    reasoning = chunk.additional_kwargs.get('reasoning_content', '')
                    if reasoning:
                        yield {"type": "thinking", "text": reasoning}
                        continue

                # 处理 Anthropic extended thinking
                if hasattr(chunk, 'content') and isinstance(chunk.content, list):
                    for block in chunk.content:
                        if hasattr(block, 'type') and block.type == 'thinking':
                            if hasattr(block, 'thinking'):
                                yield {"type": "thinking", "text": block.thinking}
                        elif hasattr(block, 'type') and block.type == 'text':
                            if hasattr(block, 'text') and block.text:
                                yield {"type": "content", "text": block.text}
                    continue

                # 普通内容
                if chunk.content:
                    yield {"type": "content", "text": chunk.content}
        else:
            response = self._current_model.invoke(lc_messages)
            # 检查是否有思考过程
            if hasattr(response, 'additional_kwargs') and response.additional_kwargs:
                reasoning = response.additional_kwargs.get('reasoning_content', '')
                if reasoning:
                    yield {"type": "thinking", "text": reasoning}
            yield {"type": "content", "text": response.content}

    def chat_with_tools(self, messages: List[Dict[str, str]], stream: bool = True) -> Generator[Dict[str, Any], None, None]:
        """
        支持工具调用的对话

        Args:
            messages: 消息列表 [{"role": "user/assistant/system", "content": "..."}]
            stream: 是否流式输出

        Yields:
            响应字典:
            - {"type": "thinking", "text": "..."} - 思考过程
            - {"type": "content", "text": "..."} - 文本内容
            - {"type": "tool_call", "name": "...", "args": {...}, "id": "..."} - 工具调用
            - {"type": "tool_result", "name": "...", "result": "..."} - 工具执行结果
        """
        if self._current_model is None:
            raise RuntimeError("请先设置模型")

        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage

        # 转换消息格式
        lc_messages = self._convert_messages(messages)

        # 工具调用循环
        max_iterations = 10  # 防止无限循环
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if stream:
                # 收集响应
                tool_calls_chunks = []
                has_content = False

                for chunk in self._current_model.stream(lc_messages):
                    # 处理思考过程
                    if hasattr(chunk, 'additional_kwargs') and chunk.additional_kwargs:
                        reasoning = chunk.additional_kwargs.get('reasoning_content', '')
                        if reasoning:
                            yield {"type": "thinking", "text": reasoning}

                    # 处理 content（可能是字符串或列表）
                    if hasattr(chunk, 'content') and chunk.content:
                        if isinstance(chunk.content, list):
                            # Anthropic 格式: content 是列表
                            for block in chunk.content:
                                if isinstance(block, dict):
                                    block_type = block.get('type', '')
                                    if block_type == 'thinking':
                                        if block.get('thinking'):
                                            yield {"type": "thinking", "text": block['thinking']}
                                    elif block_type == 'text':
                                        if block.get('text'):
                                            yield {"type": "content", "text": block['text']}
                                            has_content = True
                                elif hasattr(block, 'type'):
                                    if block.type == 'thinking' and hasattr(block, 'thinking'):
                                        yield {"type": "thinking", "text": block.thinking}
                                    elif block.type == 'text' and hasattr(block, 'text') and block.text:
                                        yield {"type": "content", "text": block.text}
                                        has_content = True
                        else:
                            # OpenAI 格式: content 是字符串
                            yield {"type": "content", "text": str(chunk.content)}
                            has_content = True

                    # 收集工具调用（不要用 continue 跳过）
                    if hasattr(chunk, 'tool_call_chunks') and chunk.tool_call_chunks:
                        tool_calls_chunks.extend(chunk.tool_call_chunks)
                    if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                        # 直接使用已聚合的 tool_calls
                        for tc in chunk.tool_calls:
                            if tc.get('name'):  # 确保有工具名
                                tool_calls_chunks.append(tc)

                # 处理工具调用
                if tool_calls_chunks:
                    aggregated = self._aggregate_tool_calls(tool_calls_chunks)
                    for tc in aggregated:
                        # 通知工具调用
                        yield {
                            "type": "tool_call",
                            "name": tc["name"],
                            "args": tc["args"],
                            "id": tc.get("id", "")
                        }

                        # 执行工具
                        result = self._execute_tool(tc["name"], tc["args"])
                        yield {"type": "tool_result", "name": tc["name"], "result": result}

                        # 添加消息到历史
                        lc_messages.append(AIMessage(
                            content="",
                            tool_calls=[tc]
                        ))
                        lc_messages.append(ToolMessage(
                            content=result,
                            tool_call_id=tc.get("id", str(uuid.uuid4()))
                        ))
                else:
                    # 没有工具调用，结束循环
                    break
            else:
                # 非流式模式
                response = self._current_model.invoke(lc_messages)

                if response.content:
                    yield {"type": "content", "text": response.content}

                if hasattr(response, 'tool_calls') and response.tool_calls:
                    for tc in response.tool_calls:
                        yield {
                            "type": "tool_call",
                            "name": tc["name"],
                            "args": tc["args"],
                            "id": tc.get("id", "")
                        }

                        result = self._execute_tool(tc["name"], tc["args"])
                        yield {"type": "tool_result", "name": tc["name"], "result": result}

                        lc_messages.append(response)
                        lc_messages.append(ToolMessage(
                            content=result,
                            tool_call_id=tc.get("id", str(uuid.uuid4()))
                        ))
                else:
                    break

        if iteration >= max_iterations:
            yield {"type": "content", "text": "\n[已达到最大工具调用次数限制]"}

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List:
        """转换消息格式为 LangChain 消息"""
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                lc_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            elif role == "system":
                lc_messages.append(SystemMessage(content=content))
        return lc_messages

    def _aggregate_tool_calls(self, chunks: List) -> List[Dict[str, Any]]:
        """聚合流式工具调用片段"""
        aggregated = {}

        for chunk in chunks:
            # chunk 可能是 dict 或对象
            if isinstance(chunk, dict):
                idx = chunk.get("index", 0)
                name = chunk.get("name", "")
                args_str = chunk.get("args", "")
                tc_id = chunk.get("id", "")
            else:
                idx = getattr(chunk, "index", 0) or getattr(chunk, "get", lambda k, d: d)("index", 0)
                name = getattr(chunk, "name", "") or getattr(chunk, "get", lambda k, d: d)("name", "")
                args_str = getattr(chunk, "args", "") or getattr(chunk, "get", lambda k, d: d)("args", "")
                tc_id = getattr(chunk, "id", "") or getattr(chunk, "get", lambda k, d: d)("id", "")

            if idx not in aggregated:
                aggregated[idx] = {
                    "id": tc_id or str(uuid.uuid4()),
                    "name": name,
                    "args_str": ""
                }

            if name:
                aggregated[idx]["name"] = name
            if args_str:
                aggregated[idx]["args_str"] += args_str
            if tc_id:
                aggregated[idx]["id"] = tc_id

        # 解析参数
        results = []
        for idx, tc in aggregated.items():
            args = {}
            if tc["args_str"]:
                try:
                    args = json.loads(tc["args_str"])
                except json.JSONDecodeError:
                    args = {"raw": tc["args_str"]}

            results.append({
                "id": tc["id"],
                "name": tc["name"],
                "args": args
            })

        return results

    def _execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """执行工具"""
        if name not in self._tool_executors:
            logger.warning("未知的工具调用", extra={"tool": name})
            return f"错误: 未知的工具 '{name}'"

        try:
            logger.info("执行工具", extra={"tool": name, "args": args})
            executor = self._tool_executors[name]
            result = str(executor(**args))
            logger.debug("工具执行完成", extra={"tool": name, "result_length": len(result)})
            return result
        except Exception as e:
            logger.error("工具执行失败", extra={"tool": name, "error": str(e)})
            return f"工具执行错误 ({name}): {str(e)}"


# 全局模型管理器实例
model_manager = ModelManager()
