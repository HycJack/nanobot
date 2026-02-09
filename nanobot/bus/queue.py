"""
异步消息队列，用于解耦通道和代理之间的通信。
- 消息队列管理 ：维护入站和出站消息队列
- 消息发布与消费 ：提供异步方法发布和消费消息
- 订阅机制 ：支持通道订阅特定类型的消息
- 消息分发 ：将出站消息分发给相应的通道
"""

import asyncio
from typing import Callable, Awaitable

from loguru import logger

from nanobot.bus.events import InboundMessage, OutboundMessage


class MessageBus:
    """
    异步消息总线，用于解耦聊天通道和代理核心。
    
    通道将消息推送到入站队列，代理处理这些消息并将响应推送到出站队列。
    这种设计实现了通道和代理之间的完全解耦，提高了系统的可扩展性和可维护性。
    """
    
    def __init__(self):
        # 入站消息队列：存储从通道发送到代理的消息
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        # 出站消息队列：存储从代理发送到通道的响应
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        # 出站消息订阅者：按通道名称存储回调函数列表
        self._outbound_subscribers: dict[str, list[Callable[[OutboundMessage], Awaitable[None]]]] = {}
        # 运行状态标志：控制dispatch_outbound循环
        self._running = False
    
    async def publish_inbound(self, msg: InboundMessage) -> None:
        """将消息从通道发布到代理。
        
        Args:
            msg: 入站消息对象，包含通道、发送者、内容等信息
        """
        await self.inbound.put(msg)
    
    async def consume_inbound(self) -> InboundMessage:
        """消费下一条入站消息（阻塞直到消息可用）。
        
        Returns:
            入站消息对象
        """
        return await self.inbound.get()
    
    async def publish_outbound(self, msg: OutboundMessage) -> None:
        """将响应从代理发布到通道。
        
        Args:
            msg: 出站消息对象，包含目标通道、聊天ID、内容等信息
        """
        await self.outbound.put(msg)
    
    async def consume_outbound(self) -> OutboundMessage:
        """消费下一条出站消息（阻塞直到消息可用）。
        
        Returns:
            出站消息对象
        """
        return await self.outbound.get()
    
    def subscribe_outbound(
        self, 
        channel: str, 
        callback: Callable[[OutboundMessage], Awaitable[None]]
    ) -> None:
        """订阅特定通道的出站消息。
        
        Args:
            channel: 通道名称，如 'telegram', 'discord' 等
            callback: 当消息到达时要调用的异步回调函数
        """
        if channel not in self._outbound_subscribers:
            self._outbound_subscribers[channel] = []
        self._outbound_subscribers[channel].append(callback)
    
    async def dispatch_outbound(self) -> None:
        """
        将出站消息分发给订阅的通道。
        应作为后台任务运行。
        
        此方法会持续监听出站消息队列，当有消息到达时，根据消息的通道属性
        找到对应的订阅者并调用其回调函数。
        """
        self._running = True
        while self._running:
            try:
                # 等待出站消息，设置1秒超时以允许定期检查_running状态
                msg = await asyncio.wait_for(self.outbound.get(), timeout=1.0)
                # 获取该通道的所有订阅者
                subscribers = self._outbound_subscribers.get(msg.channel, [])
                # 调用每个订阅者的回调函数
                for callback in subscribers:
                    try:
                        await callback(msg)
                    except Exception as e:
                        logger.error(f"Error dispatching to {msg.channel}: {e}")
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环检查
                continue
    
    def stop(self) -> None:
        """停止分发器循环。"""
        self._running = False
    
    @property
    def inbound_size(self) -> int:
        """待处理的入站消息数量。"""
        return self.inbound.qsize()
    
    @property
    def outbound_size(self) -> int:
        """待处理的出站消息数量。"""
        return self.outbound.qsize()
