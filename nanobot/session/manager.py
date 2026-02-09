"""会话管理，用于存储对话历史。"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from loguru import logger

from nanobot.utils.helpers import ensure_dir, safe_filename


@dataclass
class Session:
    """
    对话会话类。
    
    使用JSONL格式存储消息，便于读取和持久化。
    """
    
    # 会话键，通常格式为 channel:chat_id
    key: str
    # 消息列表
    messages: list[dict[str, Any]] = field(default_factory=list)
    # 创建时间
    created_at: datetime = field(default_factory=datetime.now)
    # 更新时间
    updated_at: datetime = field(default_factory=datetime.now)
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """向会话添加消息。
        
        Args:
            role: 消息角色，如 "user" 或 "assistant"
            content: 消息内容
            **kwargs: 额外的消息属性
        """
        msg = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.messages.append(msg)
        self.updated_at = datetime.now()
    
    def get_history(self, max_messages: int = 50) -> list[dict[str, Any]]:
        """
        获取用于LLM上下文的消息历史。
        
        Args:
            max_messages: 返回的最大消息数。
        
        Returns:
            LLM格式的消息列表。
        """
        # 获取最近的消息
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        
        # 转换为LLM格式（仅包含role和content）
        return [{"role": m["role"], "content": m["content"]} for m in recent]
    
    def clear(self) -> None:
        """清除会话中的所有消息。"""
        self.messages = []
        self.updated_at = datetime.now()


class SessionManager:
    """
    会话管理器。
    
    会话以JSONL文件形式存储在sessions目录中。
    """
    
    def __init__(self, workspace: Path):
        """
        初始化会话管理器。
        
        Args:
            workspace: 工作目录路径
        """
        self.workspace = workspace
        # 确保会话目录存在
        self.sessions_dir = ensure_dir(Path.home() / ".nanobot" / "sessions")
        # 会话缓存，提高访问速度
        self._cache: dict[str, Session] = {}
    
    def _get_session_path(self, key: str) -> Path:
        """获取会话的文件路径。
        
        Args:
            key: 会话键
            
        Returns:
            会话文件路径
        """
        # 将会话键转换为安全的文件名
        safe_key = safe_filename(key.replace(":", "_"))
        return self.sessions_dir / f"{safe_key}.jsonl"
    
    def get_or_create(self, key: str) -> Session:
        """
        获取现有会话或创建新会话。
        
        Args:
            key: 会话键（通常为 channel:chat_id）。
        
        Returns:
            会话对象。
        """
        # 检查缓存
        if key in self._cache:
            return self._cache[key]
        
        # 尝试从磁盘加载
        session = self._load(key)
        if session is None:
            session = Session(key=key)
        
        # 存入缓存
        self._cache[key] = session
        return session
    
    def _load(self, key: str) -> Session | None:
        """从磁盘加载会话。
        
        Args:
            key: 会话键
            
        Returns:
            会话对象，如果不存在则返回None
        """
        path = self._get_session_path(key)
        
        if not path.exists():
            return None
        
        try:
            messages = []
            metadata = {}
            created_at = None
            
            # 读取JSONL文件
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    data = json.loads(line)
                    
                    # 处理元数据行
                    if data.get("_type") == "metadata":
                        metadata = data.get("metadata", {})
                        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
                    # 处理消息行
                    else:
                        messages.append(data)
            
            return Session(
                key=key,
                messages=messages,
                created_at=created_at or datetime.now(),
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"Failed to load session {key}: {e}")
            return None
    
    def save(self, session: Session) -> None:
        """将会话保存到磁盘。
        
        Args:
            session: 要保存的会话对象
        """
        path = self._get_session_path(session.key)
        
        # 写入JSONL文件
        with open(path, "w") as f:
            # 先写入元数据
            metadata_line = {
                "_type": "metadata",
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "metadata": session.metadata
            }
            f.write(json.dumps(metadata_line) + "\n")
            
            # 再写入每条消息
            for msg in session.messages:
                f.write(json.dumps(msg) + "\n")
        
        # 更新缓存
        self._cache[session.key] = session
    
    def delete(self, key: str) -> bool:
        """
        删除会话。
        
        Args:
            key: 会话键。
        
        Returns:
            如果删除成功返回True，否则返回False。
        """
        # 从缓存中移除
        self._cache.pop(key, None)
        
        # 删除文件
        path = self._get_session_path(key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    def list_sessions(self) -> list[dict[str, Any]]:
        """
        列出所有会话。
        
        Returns:
            会话信息字典列表。
        """
        sessions = []
        
        # 遍历所有会话文件
        for path in self.sessions_dir.glob("*.jsonl"):
            try:
                # 只读取元数据行
                with open(path) as f:
                    first_line = f.readline().strip()
                    if first_line:
                        data = json.loads(first_line)
                        if data.get("_type") == "metadata":
                            sessions.append({
                                "key": path.stem.replace("_", ":"),  # 还原会话键格式
                                "created_at": data.get("created_at"),
                                "updated_at": data.get("updated_at"),
                                "path": str(path)
                            })
            except Exception:
                continue
        
        # 按更新时间排序
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
