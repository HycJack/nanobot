"""
通道管理器，用于协调聊天通道。
ChannelManager 负责管理所有聊天通道，协调消息路由。主要功能包括：
- 通道初始化 ：根据配置启用相应的通道（Telegram、WhatsApp、Discord、Feishu、DingTalk）
- 通道生命周期管理 ：启动和停止所有通道
- 消息分发 ：将出站消息路由到相应的通道
- 状态管理 ：提供通道状态查询功能
"""

from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from loguru import logger

from nanobot.bus.events import OutboundMessage
from nanobot.bus.queue import MessageBus
from nanobot.channels.base import BaseChannel
from nanobot.config.schema import Config

if TYPE_CHECKING:
    from nanobot.session.manager import SessionManager


class ChannelManager:
    """
    管理聊天通道并协调消息路由。
    
    职责：
    - 初始化启用的通道（Telegram、WhatsApp等）
    - 启动/停止通道
    - 路由出站消息
    - 管理通道状态
    """
    
    def __init__(self, config: Config, bus: MessageBus, session_manager: "SessionManager | None" = None):
        """初始化通道管理器。
        
        Args:
            config: 配置对象，包含通道配置信息
            bus: 消息总线，用于消息传递
            session_manager: 会话管理器，用于管理用户会话
        """
        self.config = config
        self.bus = bus
        self.session_manager = session_manager
        # 通道字典：键为通道名称，值为通道实例
        self.channels: dict[str, BaseChannel] = {}
        # 出站消息分发任务
        self._dispatch_task: asyncio.Task | None = None
        
        # 初始化通道
        self._init_channels()
    
    def _init_channels(self) -> None:
        """根据配置初始化通道。"""
        
        # Telegram通道
        if self.config.channels.telegram.enabled:
            try:
                from nanobot.channels.telegram import TelegramChannel
                self.channels["telegram"] = TelegramChannel(
                    self.config.channels.telegram,
                    self.bus,
                    groq_api_key=self.config.providers.groq.api_key,
                    session_manager=self.session_manager,
                )
                logger.info("Telegram channel enabled")
            except ImportError as e:
                logger.warning(f"Telegram channel not available: {e}")
        
        # WhatsApp通道
        if self.config.channels.whatsapp.enabled:
            try:
                from nanobot.channels.whatsapp import WhatsAppChannel
                self.channels["whatsapp"] = WhatsAppChannel(
                    self.config.channels.whatsapp, self.bus
                )
                logger.info("WhatsApp channel enabled")
            except ImportError as e:
                logger.warning(f"WhatsApp channel not available: {e}")

        # Discord通道
        if self.config.channels.discord.enabled:
            try:
                from nanobot.channels.discord import DiscordChannel
                self.channels["discord"] = DiscordChannel(
                    self.config.channels.discord, self.bus
                )
                logger.info("Discord channel enabled")
            except ImportError as e:
                logger.warning(f"Discord channel not available: {e}")
        
        # Feishu通道
        if self.config.channels.feishu.enabled:
            try:
                from nanobot.channels.feishu import FeishuChannel
                self.channels["feishu"] = FeishuChannel(
                    self.config.channels.feishu, self.bus
                )
                logger.info("Feishu channel enabled")
            except ImportError as e:
                logger.warning(f"Feishu channel not available: {e}")

        # DingTalk通道
        if self.config.channels.dingtalk.enabled:
            try:
                from nanobot.channels.dingtalk import DingTalkChannel
                self.channels["dingtalk"] = DingTalkChannel(
                    self.config.channels.dingtalk, self.bus
                )
                logger.info("DingTalk channel enabled")
            except ImportError as e:
                logger.warning(f"DingTalk channel not available: {e}")
    
    async def _start_channel(self, name: str, channel: BaseChannel) -> None:
        """启动通道并记录任何异常。
        
        Args:
            name: 通道名称
            channel: 通道实例
        """
        try:
            await channel.start()
        except Exception as e:
            logger.error(f"Failed to start channel {name}: {e}")

    async def start_all(self) -> None:
        """启动所有通道和出站消息分发器。"""
        if not self.channels:
            logger.warning("No channels enabled")
            return
        
        # 启动出站消息分发器
        self._dispatch_task = asyncio.create_task(self._dispatch_outbound())
        
        # 启动所有通道
        tasks = []
        for name, channel in self.channels.items():
            logger.info(f"Starting {name} channel...")
            tasks.append(asyncio.create_task(self._start_channel(name, channel)))
        
        # 等待所有任务完成（通道应该会一直运行）
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def stop_all(self) -> None:
        """停止所有通道和分发器。"""
        logger.info("Stopping all channels...")
        
        # 停止分发器
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有通道
        for name, channel in self.channels.items():
            try:
                await channel.stop()
                logger.info(f"Stopped {name} channel")
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
    
    async def _dispatch_outbound(self) -> None:
        """将出站消息分发到相应的通道。"""
        logger.info("Outbound dispatcher started")
        
        while True:
            try:
                # 等待出站消息，设置1秒超时以允许定期检查任务状态
                msg = await asyncio.wait_for(
                    self.bus.consume_outbound(),
                    timeout=1.0
                )
                
                # 查找目标通道
                channel = self.channels.get(msg.channel)
                if channel:
                    try:
                        # 发送消息到通道
                        await channel.send(msg)
                    except Exception as e:
                        logger.error(f"Error sending to {msg.channel}: {e}")
                else:
                    logger.warning(f"Unknown channel: {msg.channel}")
                    
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except asyncio.CancelledError:
                # 任务被取消，退出循环
                break
    
    def get_channel(self, name: str) -> BaseChannel | None:
        """通过名称获取通道。
        
        Args:
            name: 通道名称
            
        Returns:
            通道实例，如果不存在则返回None
        """
        return self.channels.get(name)
    
    def get_status(self) -> dict[str, Any]:
        """获取所有通道的状态。
        
        Returns:
            通道状态字典，包含每个通道的启用状态和运行状态
        """
        return {
            name: {
                "enabled": True,
                "running": channel.is_running
            }
            for name, channel in self.channels.items()
        }
    
    @property
    def enabled_channels(self) -> list[str]:
        """获取启用的通道名称列表。
        
        Returns:
            启用的通道名称列表
        """
        return list(self.channels.keys())
