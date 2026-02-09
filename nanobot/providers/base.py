"""LLM提供商的基础接口。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCallRequest:
    """来自LLM的工具调用请求。"""
    # 工具调用的唯一标识符
    id: str
    # 要调用的工具名称
    name: str
    # 工具参数，以字典形式表示
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """LLM提供商的响应。"""
    # 响应内容，如果有工具调用则可能为None
    content: str | None
    # 工具调用请求列表，默认为空列表
    tool_calls: list[ToolCallRequest] = field(default_factory=list)
    # 完成原因，默认为"stop"
    finish_reason: str = "stop"
    # 令牌使用情况，默认为空字典
    usage: dict[str, int] = field(default_factory=dict)
    # 推理内容，用于支持Kimi、DeepSeek-R1等模型的思考输出
    reasoning_content: str | None = None  # Kimi, DeepSeek-R1 etc.
    
    @property
    def has_tool_calls(self) -> bool:
        """检查响应是否包含工具调用。"""
        return len(self.tool_calls) > 0


class LLMProvider(ABC):
    """
    LLM提供商的抽象基类。
    
    实现应该处理每个提供商API的具体细节，
    同时保持一致的接口。
    """
    
    def __init__(self, api_key: str | None = None, api_base: str | None = None):
        """
        初始化LLM提供商。
        
        Args:
            api_key: API密钥，用于认证
            api_base: API基础URL，用于自定义API端点
        """
        self.api_key = api_key
        self.api_base = api_base
    
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        发送聊天完成请求。
        
        Args:
            messages: 消息字典列表，包含'role'和'content'。
            tools: 可选的工具定义列表。
            model: 模型标识符（提供商特定）。
            max_tokens: 响应中的最大令牌数。
            temperature: 采样温度。
        
        Returns:
            包含内容和/或工具调用的LLMResponse。
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """获取此提供商的默认模型。"""
        pass
