"""聊天平台的基础通道接口。"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage
from nanobot.bus.queue import MessageBus


class BaseChannel(ABC):
    """
    聊天通道实现的抽象基类。
    
    每个通道（Telegram、Discord等）都应实现此接口，
    以与nanobot消息总线集成。
    """
    
    # 通道名称，子类应覆盖此属性
    name: str = "base"
    
    def __init__(self, config: Any, bus: MessageBus):
        """
        初始化通道。
        
        Args:
            config: 通道特定的配置。
            bus: 用于通信的消息总线。
        """
        self.config = config
        self.bus = bus
        # 运行状态标志
        self._running = False
    
    @abstractmethod
    async def start(self) -> None:
        """
        启动通道并开始监听消息。
        
        这应该是一个长期运行的异步任务，需要：
        1. 连接到聊天平台
        2. 监听传入消息
        3. 通过_handle_message()将消息转发到总线
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """停止通道并清理资源。"""
        pass
    
    @abstractmethod
    async def send(self, msg: OutboundMessage) -> None:
        """
        通过此通道发送消息。
        
        Args:
            msg: 要发送的消息。
        """
        pass
    
    def is_allowed(self, sender_id: str) -> bool:
        """
        检查发送者是否被允许使用此机器人。
        
        Args:
            sender_id: 发送者的标识符。
        
        Returns:
            如果允许，返回True；否则返回False。
        """
        # 从配置中获取允许列表
        allow_list = getattr(self.config, "allow_from", [])
        
        # 如果没有允许列表，则允许所有人
        if not allow_list:
            return True
        
        sender_str = str(sender_id)
        # 检查发送者ID是否在允许列表中
        if sender_str in allow_list:
            return True
        # 处理包含"|"分隔符的发送者ID
        if "|" in sender_str:
            for part in sender_str.split("|"):
                if part and part in allow_list:
                    return True
        return False
    
    async def _handle_message(
        self,
        sender_id: str,
        chat_id: str,
        content: str,
        media: list[str] | None = None,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        处理来自聊天平台的传入消息。
        
        此方法检查权限并将消息转发到总线。
        
        Args:
            sender_id: 发送者的标识符。
            chat_id: 聊天/通道标识符。
            content: 消息文本内容。
            media: 可选的媒体URL列表。
            metadata: 可选的通道特定元数据。
        """
        # 检查发送者是否被允许
        if not self.is_allowed(sender_id):
            logger.warning(
                f"Access denied for sender {sender_id} on channel {self.name}. "
                f"Add them to allowFrom list in config to grant access."
            )
            return
        
        # 创建入站消息对象
        msg = InboundMessage(
            channel=self.name,
            sender_id=str(sender_id),
            chat_id=str(chat_id),
            content=content,
            media=media or [],
            metadata=metadata or {}
        )
        
        # 将消息发布到总线
        await self.bus.publish_inbound(msg)
    
    @property
    def is_running(self) -> bool:
        """检查通道是否正在运行。"""
        return self._running
