# nanobot 源码分析与 TypeScript 框架设计指南

## 1. 项目概述

**nanobot** 是一个超轻量级的个人 AI 助手框架，其核心特点是代码极其精简，核心代理逻辑仅约 **3,448 行代码**，比同类项目小 99%。

### 核心特性
- 🪶 **超轻量级**：核心代码仅约 4,000 行
- 🔬 **研究友好**：代码清晰易读，便于理解和扩展
- ⚡️ **快速启动**：最小化资源占用，快速迭代
- 💎 **易于使用**：一键部署，开箱即用

### 技术栈
- **核心语言**：Python 3.11+
- **主要依赖**：
  - `typer` - 命令行接口
  - `litellm` - LLM 提供商统一接口
  - `pydantic` - 数据验证和配置管理
  - `websockets` - WebSocket 支持
  - `loguru` - 日志记录
  - `rich` - 终端美化

## 2. 整体架构分析

### 架构图解析

nanobot 采用了模块化、事件驱动的架构设计，主要包含以下核心组件：

1. **消息总线**：作为系统的神经中枢，负责在不同模块之间传递消息
2. **代理核心**：处理消息的核心逻辑，包括上下文构建、LLM 调用和工具执行
3. **工具系统**：提供各种实用工具，如文件操作、Shell 执行、Web 搜索等
4. **会话管理**：管理对话历史，使用 JSONL 格式持久化存储
5. **LLM 提供商**：统一接口对接各种 LLM 服务
6. **技能系统**：通过 Markdown 文件定义的可扩展技能
7. **聊天通道**：支持 Telegram、Discord、WhatsApp、飞书等多种聊天平台

### 数据流分析

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 聊天通道     │────>│ 消息总线     │────>│ 代理核心     │────>│ 消息总线     │────>│ 聊天通道     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                                      │                 │
                                      │                 │
                                      ▼                 ▼
                                ┌─────────────┐     ┌─────────────┐
                                │ 工具系统     │<────│ LLM 提供商   │
                                └─────────────┘     └─────────────┘
                                      │
                                      │
                                      ▼
                                ┌─────────────┐
                                │ 会话管理     │
                                └─────────────┘
                                      │
                                      │
                                      ▼
                                ┌─────────────┐
                                │ 技能系统     │
                                └─────────────┘
```

## 3. 核心模块详解

### 3.1 消息总线系统

消息总线是 nanobot 的核心通信机制，采用异步队列实现，实现了模块间的解耦。

#### 核心组件
- **InboundMessage**：从聊天通道接收的消息
- **OutboundMessage**：发送到聊天通道的消息
- **MessageBus**：异步消息队列，处理消息的发布和订阅

#### 关键实现
```python
class MessageBus:
    """
    Async message bus that decouples chat channels from the agent core.
    
    Channels push messages to the inbound queue, and the agent processes
    them and pushes responses to the outbound queue.
    """
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._outbound_subscribers: dict[str, list[Callable[[OutboundMessage], Awaitable[None]]]] = {}
        self._running = False
```

#### 工作流程
1. 聊天通道将消息发布到 `inbound` 队列
2. 代理核心从 `inbound` 队列消费消息
3. 代理核心处理消息后，将响应发布到 `outbound` 队列
4. 消息总线将 `outbound` 队列的消息分发给订阅的聊天通道

### 3.2 代理核心逻辑

代理核心是 nanobot 的大脑，负责处理消息、构建上下文、调用 LLM 和执行工具。

#### 核心组件
- **AgentLoop**：核心处理引擎
- **ContextBuilder**：构建 LLM 上下文
- **SessionManager**：管理会话历史

#### 关键实现
```python
async def _process_message(self, msg: InboundMessage) -> OutboundMessage | None:
    """
    Process a single inbound message.
    
    Args:
        msg: The inbound message to process.
    
    Returns:
        The response message, or None if no response needed.
    """
    # 获取或创建会话
    session = self.sessions.get_or_create(msg.session_key)
    
    # 构建上下文
    messages = self.context.build_messages(
        history=session.get_history(),
        current_message=msg.content,
        media=msg.media if msg.media else None,
        channel=msg.channel,
        chat_id=msg.chat_id,
    )
    
    # LLM 调用循环
    iteration = 0
    final_content = None
    
    while iteration < self.max_iterations:
        iteration += 1
        
        # 调用 LLM
        response = await self.provider.chat(
            messages=messages,
            tools=self.tools.get_definitions(),
            model=self.model
        )
        
        # 处理工具调用
        if response.has_tool_calls:
            # 执行工具
            for tool_call in response.tool_calls:
                result = await self.tools.execute(tool_call.name, tool_call.arguments)
                messages = self.context.add_tool_result(
                    messages, tool_call.id, tool_call.name, result
                )
        else:
            # 生成最终响应
            final_content = response.content
            break
    
    # 保存会话
    session.add_message("user", msg.content)
    session.add_message("assistant", final_content)
    self.sessions.save(session)
    
    return OutboundMessage(
        channel=msg.channel,
        chat_id=msg.chat_id,
        content=final_content
    )
```

#### 工作流程
1. 接收消息并获取/创建会话
2. 构建包含系统提示词、历史消息和当前消息的上下文
3. 调用 LLM 并处理响应
4. 如果 LLM 请求工具调用，执行工具并将结果添加到上下文
5. 重复步骤 3-4，直到 LLM 生成最终响应
6. 保存会话并返回响应

### 3.3 工具系统

工具系统为 nanobot 提供了各种实用功能，如文件操作、Shell 执行、Web 搜索等。

#### 核心组件
- **ToolRegistry**：工具注册表，管理所有可用工具
- **Tool**：工具基类，定义了工具的基本接口
- **各种具体工具**：如 `ReadFileTool`、`ExecTool`、`WebSearchTool` 等

#### 关键实现
```python
class ToolRegistry:
    """
    Registry for agent tools.
    
    Allows dynamic registration and execution of tools.
    """
    
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
    
    async def execute(self, name: str, params: dict[str, Any]) -> str:
        """
        Execute a tool by name with given parameters.
        
        Args:
            name: Tool name.
            params: Tool parameters.
        
        Returns:
            Tool execution result as string.
        """
        tool = self._tools.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"

        try:
            errors = tool.validate_params(params)
            if errors:
                return f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
            return await tool.execute(**params)
        except Exception as e:
            return f"Error executing {name}: {str(e)}"
```

#### 工具类型
| 工具名称 | 功能描述 | 实现文件 |
|---------|---------|---------|
| `read_file` | 读取文件内容 | `filesystem.py` |
| `write_file` | 写入文件内容 | `filesystem.py` |
| `edit_file` | 编辑文件内容 | `filesystem.py` |
| `list_dir` | 列出目录内容 | `filesystem.py` |
| `exec` | 执行 Shell 命令 | `shell.py` |
| `web_search` | Web 搜索 | `web.py` |
| `web_fetch` | 获取网页内容 | `web.py` |
| `message` | 发送消息 | `message.py` |
| `spawn` | 创建子代理 | `spawn.py` |
| `cron` | 管理定时任务 | `cron.py` |

### 3.4 会话管理

会话管理系统负责存储和管理对话历史，使用 JSONL 格式持久化存储消息。

#### 核心组件
- **Session**：表示一个对话会话
- **SessionManager**：管理所有会话，处理会话的加载和保存

#### 关键实现
```python
class Session:
    """
    A conversation session.
    
    Stores messages in JSONL format for easy reading and persistence.
    """
    
    key: str  # channel:chat_id
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to the session."""
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
        Get message history for LLM context.
        
        Args:
            max_messages: Maximum messages to return.
        
        Returns:
            List of messages in LLM format.
        """
        # Get recent messages
        recent = self.messages[-max_messages:] if len(self.messages) > max_messages else self.messages
        
        # Convert to LLM format (just role and content)
        return [{"role": m["role"], "content": m["content"]} for m in recent]
```

#### JSONL 存储格式
```jsonl
{"_type": "metadata", "created_at": "2026-02-09T10:00:00", "updated_at": "2026-02-09T10:05:00", "metadata": {}}
{"role": "user", "content": "Hello!", "timestamp": "2026-02-09T10:00:00"}
{"role": "assistant", "content": "Hi there!", "timestamp": "2026-02-09T10:00:05"}
```

### 3.5 LLM 提供商系统

LLM 提供商系统为 nanobot 提供了统一的接口，支持多种 LLM 服务。

#### 核心组件
- **LLMProvider**：LLM 提供商的抽象基类
- **LiteLLMProvider**：基于 LiteLLM 的具体实现
- **ProviderRegistry**：提供商注册表，管理所有可用的 LLM 提供商

#### 关键实现
```python
class LiteLLMProvider(LLMProvider):
    """
    LLM provider using LiteLLM for multi-provider support.
    
    Supports OpenRouter, Anthropic, OpenAI, Gemini, and many other providers through
    a unified interface. Provider-specific logic is driven by the registry
    (see providers/registry.py) — no if-elif chains needed here.
    """
    
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat completion request via LiteLLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: Optional list of tool definitions in OpenAI format.
            model: Model identifier (e.g., 'anthropic/claude-sonnet-4-5').
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.
        
        Returns:
            LLMResponse with content and/or tool calls.
        """
        model = self._resolve_model(model or self.default_model)
        
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        # Apply model-specific overrides
        self._apply_model_overrides(model, kwargs)
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        try:
            response = await acompletion(**kwargs)
            return self._parse_response(response)
        except Exception as e:
            # Return error as content for graceful handling
            return LLMResponse(
                content=f"Error calling LLM: {str(e)}",
                finish_reason="error",
            )
```

#### 支持的 LLM 提供商
- OpenRouter（推荐，全球访问）
- Anthropic（Claude）
- OpenAI（GPT）
- DeepSeek
- Groq（支持 Whisper 语音转文字）
- Google Gemini
- 阿里云通义千问
- 月之暗面 Kimi
- 智谱 GLM
- vLLM（本地模型）

### 3.6 技能系统

技能系统为 nanobot 提供了可扩展的能力，通过 Markdown 文件定义技能。

#### 核心组件
- **SkillsLoader**：技能加载器，负责发现和加载技能
- **SKILL.md**：技能定义文件，使用 Markdown 格式

#### 关键实现
```python
class SkillsLoader:
    """
    Loader for agent skills.
    
    Skills are markdown files (SKILL.md) that teach the agent how to use
    specific tools or perform certain tasks.
    """
    
    def __init__(self, workspace: Path, builtin_skills_dir: Path | None = None):
        self.workspace = workspace
        self.workspace_skills = workspace / "skills"
        self.builtin_skills = builtin_skills_dir or BUILTIN_SKILLS_DIR
    
    def list_skills(self, filter_unavailable: bool = True) -> list[dict[str, str]]:
        """
        List all available skills.
        
        Args:
            filter_unavailable: If True, filter out skills with unmet requirements.
        
        Returns:
            List of skill info dicts with 'name', 'path', 'source'.
        """
        skills = []
        
        # Workspace skills (highest priority)
        if self.workspace_skills.exists():
            for skill_dir in self.workspace_skills.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists():
                        skills.append({"name": skill_dir.name, "path": str(skill_file), "source": "workspace"})
        
        # Built-in skills
        if self.builtin_skills and self.builtin_skills.exists():
            for skill_dir in self.builtin_skills.iterdir():
                if skill_dir.is_dir():
                    skill_file = skill_dir / "SKILL.md"
                    if skill_file.exists() and not any(s["name"] == skill_dir.name for s in skills):
                        skills.append({"name": skill_dir.name, "path": str(skill_file), "source": "builtin"})
        
        # Filter by requirements
        if filter_unavailable:
            return [s for s in skills if self._check_requirements(self._get_skill_meta(s["name"]))]
        return skills
```

#### 内置技能
| 技能名称 | 功能描述 | 实现文件 |
|---------|---------|---------|
| `github` | 与 GitHub 交互 | `skills/github/SKILL.md` |
| `weather` | 获取天气信息 | `skills/weather/SKILL.md` |
| `summarize` | 总结内容 | `skills/summarize/SKILL.md` |
| `tmux` | 控制 tmux 会话 | `skills/tmux/SKILL.md` |
| `skill-creator` | 创建新技能 | `skills/skill-creator/SKILL.md` |
| `cron` | 管理定时任务 | `skills/cron/SKILL.md` |

### 3.7 聊天通道

聊天通道系统为 nanobot 提供了与各种聊天平台集成的能力。

#### 核心组件
- **ChannelManager**：通道管理器，负责初始化和管理所有聊天通道
- **BaseChannel**：通道基类，定义了通道的基本接口
- **各种具体通道**：如 `TelegramChannel`、`DiscordChannel` 等

#### 支持的聊天平台
| 平台 | 实现文件 | 配置难度 |
|------|---------|---------|
| Telegram | `telegram.py` | 简单（仅需 token） |
| Discord | `discord.py` | 简单（需要 bot token + intents） |
| WhatsApp | `whatsapp.py` | 中等（需要扫码） |
| 飞书 | `feishu.py` | 中等（需要应用凭证） |
| 钉钉 | `dingtalk.py` | 中等（需要应用凭证） |

## 3. 技术亮点与设计模式

### 3.1 消息总线架构

**设计模式**：发布-订阅模式

**实现亮点**：
- 使用 `asyncio.Queue` 实现异步消息队列
- 支持通道订阅机制，实现消息的定向分发
- 解耦消息生产和消费，提高系统的可扩展性

**关键代码**：
```python
class MessageBus:
    """
    Async message bus that decouples chat channels from the agent core.
    
    Channels push messages to the inbound queue, and the agent processes
    them and pushes responses to the outbound queue.
    """
    
    def __init__(self):
        self.inbound: asyncio.Queue[InboundMessage] = asyncio.Queue()
        self.outbound: asyncio.Queue[OutboundMessage] = asyncio.Queue()
        self._outbound_subscribers: dict[str, list[Callable[[OutboundMessage], Awaitable[None]]]] = {}
        self._running = False
    
    async def dispatch_outbound(self) -> None:
        """
        Dispatch outbound messages to subscribed channels.
        Run this as a background task.
        """
        self._running = True
        while self._running:
            try:
                msg = await asyncio.wait_for(self.outbound.get(), timeout=1.0)
                subscribers = self._outbound_subscribers.get(msg.channel, [])
                for callback in subscribers:
                    try:
                        await callback(msg)
                    except Exception as e:
                        logger.error(f"Error dispatching to {msg.channel}: {e}")
            except asyncio.TimeoutError:
                continue
```

### 3.2 无分支提供商管理

**设计模式**：注册表模式 + 适配器模式

**实现亮点**：
- 使用 `ProviderSpec` 定义提供商的元数据
- 通过注册表驱动的提供商管理，避免了传统的 if-elif 链
- 支持自动检测网关和本地部署
- 易于添加新的 LLM 提供商，只需两步：
  1. 在 `PROVIDERS` 中添加 `ProviderSpec`
  2. 在配置 schema 中添加字段

**关键代码**：
```python
@dataclass(frozen=True)
class ProviderSpec:
    """One LLM provider's metadata. See PROVIDERS below for real examples."""
    # identity
    name: str                       # config field name, e.g. "dashscope"
    keywords: tuple[str, ...]       # model-name keywords for matching (lowercase)
    env_key: str                    # LiteLLM env var, e.g. "DASHSCOPE_API_KEY"
    display_name: str = ""          # shown in `nanobot status`
    
    # model prefixing
    litellm_prefix: str = ""                 # "dashscope" → model becomes "dashscope/{model}"
    skip_prefixes: tuple[str, ...] = ()      # don't prefix if model already starts with these
    
    # extra env vars, e.g. (("ZHIPUAI_API_KEY", "{api_key}"),)
    env_extras: tuple[tuple[str, str], ...] = ()
    
    # gateway / local detection
    is_gateway: bool = False                 # routes any model (OpenRouter, AiHubMix)
    is_local: bool = False                   # local deployment (vLLM, Ollama)
    detect_by_key_prefix: str = ""           # match api_key prefix, e.g. "sk-or-"
    detect_by_base_keyword: str = ""         # match substring in api_base URL
    default_api_base: str = ""               # fallback base URL
```

### 3.3 渐进式技能加载

**设计模式**：懒加载模式

**实现亮点**：
- 首先加载技能摘要，减少上下文大小
- 当需要时，通过 `read_file` 工具加载完整技能内容
- 支持技能依赖检查，只显示可用的技能
- 工作区技能优先级高于内置技能，支持自定义技能

**关键代码**：
```python
def build_skills_summary(self) -> str:
    """
    Build a summary of all skills (name, description, path, availability).
    
    This is used for progressive loading - the agent can read the full
    skill content using read_file when needed.
    
    Returns:
        XML-formatted skills summary.
    """
    all_skills = self.list_skills(filter_unavailable=False)
    if not all_skills:
        return ""
    
    lines = ["<skills>"]
    for s in all_skills:
        name = escape_xml(s["name"])
        path = s["path"]
        desc = escape_xml(self._get_skill_description(s["name"]))
        skill_meta = self._get_skill_meta(s["name"])
        available = self._check_requirements(skill_meta)
        
        lines.append(f"  <skill available=\"{str(available).lower()}\">")
        lines.append(f"    <name>{name}</name>")
        lines.append(f"    <description>{desc}</description>")
        lines.append(f"    <location>{path}</location>")
        
        # Show missing requirements for unavailable skills
        if not available:
            missing = self._get_missing_requirements(skill_meta)
            if missing:
                lines.append(f"    <requires>{escape_xml(missing)}</requires>")
        
        lines.append(f"  </skill>")
    lines.append("</skills>")
    
    return "\n".join(lines)
```

### 3.4 JSONL 会话存储

**设计模式**：简单文件存储模式

**实现亮点**：
- 使用 JSONL 格式存储消息，每行一个 JSON 对象
- 易于读写和追加，无需加载整个文件
- 容错性好，单行损坏不影响其他行
- 支持会话元数据和消息历史的分离存储

**关键代码**：
```python
def save(self, session: Session) -> None:
    """Save a session to disk."""
    path = self._get_session_path(session.key)
    
    with open(path, "w") as f:
        # Write metadata first
        metadata_line = {
            "_type": "metadata",
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "metadata": session.metadata
        }
        f.write(json.dumps(metadata_line) + "\n")
        
        # Write messages
        for msg in session.messages:
            f.write(json.dumps(msg) + "\n")
    
    self._cache[session.key] = session
```

### 3.5 动态工具系统

**设计模式**：注册表模式 + 命令模式

**实现亮点**：
- 工具可以动态注册和执行
- 支持参数验证
- 统一的错误处理
- 工具上下文管理，支持工具间的协作

**关键代码**：
```python
async def execute(self, name: str, params: dict[str, Any]) -> str:
    """
    Execute a tool by name with given parameters.
    
    Args:
        name: Tool name.
        params: Tool parameters.
    
    Returns:
        Tool execution result as string.
    
    Raises:
        KeyError: If tool not found.
    """
    tool = self._tools.get(name)
    if not tool:
        return f"Error: Tool '{name}' not found"

    try:
        errors = tool.validate_params(params)
        if errors:
            return f"Error: Invalid parameters for tool '{name}': " + "; ".join(errors)
        return await tool.execute(**params)
    except Exception as e:
        return f"Error executing {name}: {str(e)}"
```

## 4. TypeScript 框架设计方案

### 4.1 架构映射

| nanobot 模块 | TypeScript 对应 | 技术选型 |
|-------------|----------------|---------|
| 消息总线 | EventBus | RxJS 或自定义实现 |
| 代理核心 | AgentCore | TypeScript 类 |
| 工具系统 | ToolSystem | TypeScript 接口 + 实现 |
| 会话管理 | SessionManager | TypeScript 类 + 文件系统 |
| LLM 提供商 | LLMProvider | TypeScript 接口 + 适配器 |
| 技能系统 | SkillSystem | TypeScript 类 + Markdown 解析 |
| 聊天通道 | ChannelSystem | TypeScript 接口 + 实现 |

### 4.2 核心类型定义

```typescript
// 消息类型
interface InboundMessage {
  channel: string;
  senderId: string;
  chatId: string;
  content: string;
  timestamp: Date;
  media?: string[];
  metadata?: Record<string, any>;
}

interface OutboundMessage {
  channel: string;
  chatId: string;
  content: string;
  replyTo?: string;
  media?: string[];
  metadata?: Record<string, any>;
}

// 工具定义
interface Tool {
  name: string;
  description: string;
  parameters: Record<string, any>;
  execute(params: Record<string, any>): Promise<string>;
  validateParams(params: Record<string, any>): string[];
}

// LLM 响应
interface LLMResponse {
  content: string | null;
  toolCalls: ToolCallRequest[];
  finishReason: string;
  usage?: Record<string, number>;
  reasoningContent?: string;
}

interface ToolCallRequest {
  id: string;
  name: string;
  arguments: Record<string, any>;
}
```

### 4.3 技术栈选择

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 核心语言 | TypeScript | 5.0+ | 类型安全的 JavaScript 超集 |
| 包管理 | npm/yarn/pnpm | 最新版 | 依赖管理 |
| 构建工具 | Vite/tsup | 最新版 | 快速构建 |
| 命令行 | commander/yargs | 最新版 | 命令行接口 |
| 响应式编程 | RxJS | 7.0+ | 消息总线实现 |
| 数据验证 | zod | 3.0+ | 数据验证（替代 Pydantic） |
| 日志记录 | winston/pino | 最新版 | 结构化日志 |
| HTTP 客户端 | node-fetch/axios | 最新版 | API 调用 |
| 文件系统 | fs-extra | 最新版 | 文件操作 |
| Markdown 解析 | marked | 最新版 | 技能文件解析 |
| 定时任务 | node-cron | 最新版 | 定时任务管理 |

### 4.4 核心模块实现方案

#### 消息总线
```typescript
class MessageBus {
  private inbound: Queue<InboundMessage> = new Queue();
  private outbound: Queue<OutboundMessage> = new Queue();
  private outboundSubscribers: Map<string, Array<(msg: OutboundMessage) => Promise<void>>> = new Map();
  private running: boolean = false;

  async publishInbound(msg: InboundMessage): Promise<void> {
    await this.inbound.put(msg);
  }

  async consumeInbound(): Promise<InboundMessage> {
    return await this.inbound.get();
  }

  async publishOutbound(msg: OutboundMessage): Promise<void> {
    await this.outbound.put(msg);
  }

  subscribeOutbound(channel: string, callback: (msg: OutboundMessage) => Promise<void>): void {
    if (!this.outboundSubscribers.has(channel)) {
      this.outboundSubscribers.set(channel, []);
    }
    this.outboundSubscribers.get(channel)!.push(callback);
  }

  async dispatchOutbound(): Promise<void> {
    this.running = true;
    while (this.running) {
      try {
        const msg = await this.outbound.get();
        const subscribers = this.outboundSubscribers.get(msg.channel) || [];
        for (const callback of subscribers) {
          try {
            await callback(msg);
          } catch (e) {
            console.error(`Error dispatching to ${msg.channel}:`, e);
          }
        }
      } catch (e) {
        continue;
      }
    }
  }

  stop(): void {
    this.running = false;
  }
}
```

#### 代理核心
```typescript
class AgentCore {
  private bus: MessageBus;
  private provider: LLMProvider;
  private workspace: string;
  private model: string;
  private maxIterations: number;
  private tools: ToolRegistry;
  private sessions: SessionManager;
  private contextBuilder: ContextBuilder;

  constructor(config: AgentConfig) {
    this.bus = config.bus;
    this.provider = config.provider;
    this.workspace = config.workspace;
    this.model = config.model || this.provider.getDefaultModel();
    this.maxIterations = config.maxIterations || 20;
    this.tools = new ToolRegistry();
    this.sessions = new SessionManager(this.workspace);
    this.contextBuilder = new ContextBuilder(this.workspace);
    
    this.registerDefaultTools();
  }

  private registerDefaultTools(): void {
    // 注册默认工具
    this.tools.register(new ReadFileTool());
    this.tools.register(new WriteFileTool());
    this.tools.register(new ExecTool());
    this.tools.register(new WebSearchTool());
    // ... 其他工具
  }

  async processMessage(msg: InboundMessage): Promise<OutboundMessage | null> {
    // 获取或创建会话
    const session = this.sessions.getOrCreate(msg.channel + ':' + msg.chatId);
    
    // 构建上下文
    const messages = this.contextBuilder.buildMessages({
      history: session.getHistory(),
      currentMessage: msg.content,
      media: msg.media,
      channel: msg.channel,
      chatId: msg.chatId
    });
    
    // LLM 调用循环
    let iteration = 0;
    let finalContent: string | null = null;
    
    while (iteration < this.maxIterations) {
      iteration++;
      
      // 调用 LLM
      const response = await this.provider.chat({
        messages,
        tools: this.tools.getDefinitions(),
        model: this.model
      });
      
      // 处理工具调用
      if (response.toolCalls && response.toolCalls.length > 0) {
        for (const toolCall of response.toolCalls) {
          const result = await this.tools.execute(toolCall.name, toolCall.arguments);
          messages.push({
            role: 'tool',
            toolCallId: toolCall.id,
            name: toolCall.name,
            content: result
          });
        }
      } else {
        finalContent = response.content;
        break;
      }
    }
    
    // 保存会话
    session.addMessage('user', msg.content);
    session.addMessage('assistant', finalContent || '');
    this.sessions.save(session);
    
    return {
      channel: msg.channel,
      chatId: msg.chatId,
      content: finalContent || 'I have no response for you.'
    };
  }
}
```

#### 会话管理
```typescript
class Session {
  readonly key: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp: string;
    [key: string]: any;
  }> = [];
  createdAt: Date;
  updatedAt: Date;
  metadata: Record<string, any> = {};

  constructor(key: string) {
    this.key = key;
    this.createdAt = new Date();
    this.updatedAt = new Date();
  }

  addMessage(role: string, content: string, extras?: Record<string, any>): void {
    this.messages.push({
      role,
      content,
      timestamp: new Date().toISOString(),
      ...extras
    });
    this.updatedAt = new Date();
  }

  getHistory(maxMessages: number = 50): Array<{ role: string; content: string }> {
    const recent = this.messages.slice(-maxMessages);
    return recent.map(msg => ({
      role: msg.role,
      content: msg.content
    }));
  }

  clear(): void {
    this.messages = [];
    this.updatedAt = new Date();
  }
}

class SessionManager {
  private workspace: string;
  private sessionsDir: string;
  private cache: Map<string, Session> = new Map();

  constructor(workspace: string) {
    this.workspace = workspace;
    this.sessionsDir = path.join(os.homedir(), '.nanobot', 'sessions');
    fs.mkdirSync(this.sessionsDir, { recursive: true });
  }

  getOrCreate(key: string): Session {
    // 检查缓存
    if (this.cache.has(key)) {
      return this.cache.get(key)!;
    }

    // 尝试从磁盘加载
    const session = this.load(key);
    if (session) {
      this.cache.set(key, session);
      return session;
    }

    // 创建新会话
    const newSession = new Session(key);
    this.cache.set(key, newSession);
    return newSession;
  }

  private load(key: string): Session | null {
    const filePath = this.getSessionPath(key);
    if (!fs.existsSync(filePath)) {
      return null;
    }

    try {
      const content = fs.readFileSync(filePath, 'utf8');
      const lines = content.split('\n').filter(line => line.trim());
      
      let session: Session | null = null;
      let messages: Array<any> = [];
      
      for (const line of lines) {
        const data = JSON.parse(line);
        if (data._type === 'metadata') {
          session = new Session(key);
          session.createdAt = new Date(data.createdAt);
          session.updatedAt = new Date(data.updatedAt);
          session.metadata = data.metadata || {};
        } else {
          messages.push(data);
        }
      }
      
      if (session) {
        session.messages = messages;
        return session;
      }
      
      return null;
    } catch (error) {
      console.error(`Error loading session ${key}:`, error);
      return null;
    }
  }

  save(session: Session): void {
    const filePath = this.getSessionPath(session.key);
    
    try {
      const lines: string[] = [];
      
      // 写入元数据
      const metadata = {
        _type: 'metadata',
        createdAt: session.createdAt.toISOString(),
        updatedAt: session.updatedAt.toISOString(),
        metadata: session.metadata
      };
      lines.push(JSON.stringify(metadata));
      
      // 写入消息
      for (const msg of session.messages) {
        lines.push(JSON.stringify(msg));
      }
      
      fs.writeFileSync(filePath, lines.join('\n'));
      this.cache.set(session.key, session);
    } catch (error) {
      console.error(`Error saving session ${session.key}:`, error);
    }
  }

  private getSessionPath(key: string): string {
    const safeKey = key.replace(/:/g, '_');
    return path.join(this.sessionsDir, `${safeKey}.jsonl`);
  }
}
```

## 4. 源码分析总结

### 4.1 核心优势

1. **代码精简**：核心逻辑仅约 3,448 行，比同类项目小 99%
2. **架构清晰**：模块化设计，职责分明，易于理解和扩展
3. **性能优秀**：最小化资源占用，快速启动和响应
4. **扩展性强**：插件化的工具和技能系统，易于添加新功能
5. **多平台支持**：支持多种聊天平台和 LLM 提供商
6. **易于部署**：一键部署，支持 Docker 容器化

### 4.2 技术创新

1. **无分支提供商管理**：使用注册表驱动的提供商管理，避免传统的 if-elif 链
2. **渐进式技能加载**：首先加载技能摘要，减少上下文大小，提高性能
3. **JSONL 会话存储**：使用简单高效的 JSONL 格式存储会话，易于读写和追加
4. **消息总线架构**：基于异步队列的消息总线，实现模块间的解耦
5. **动态工具系统**：工具可以动态注册和执行，支持参数验证和统一错误处理

### 4.3 应用场景

1. **个人助手**：日常任务管理、信息查询、提醒等
2. **开发者工具**：代码生成、调试、文档编写等
3. **研究平台**：AI 代理研究、LLM 能力测试等
4. **教育辅助**：学习资料整理、问题解答、学习计划制定等
5. **市场分析**：实时市场信息查询、趋势分析等

## 5. 开发建议与最佳实践

### 5.1 源码阅读建议

1. **从宏观到微观**：先了解整体架构，再深入具体实现
2. **核心流程追踪**：从用户输入开始，追踪数据流向和处理过程
3. **设计模式识别**：识别代码中的设计模式和最佳实践
4. **技术决策分析**：思考为什么采用特定的实现方式，评估其合理性
5. **笔记和总结**：记录关键设计决策和技术亮点，整理问题和疑问

### 5.2 TypeScript 框架开发建议

1. **架构对齐**：保持与 nanobot 相似的模块划分，适配 TypeScript 的类型系统
2. **技术选型**：选择适合 Node.js 环境的库和工具，利用 TypeScript 的类型安全优势
3. **渐进式开发**：先实现核心功能（消息总线、代理循环、工具系统），再扩展高级特性
4. **测试策略**：单元测试核心模块，集成测试关键流程，E2E 测试完整功能
5. **文档优先**：创建详细的设计文档，保持代码文档与实现同步
6. **性能优化**：
   - 使用 TypeScript 的类型推断减少运行时开销
   - 合理使用异步编程提高并发性能
   - 实现缓存机制减少重复计算和 I/O 操作
   - 优化 LLM 调用，减少不必要的 API 请求

### 5.3 部署与运维建议

1. **配置管理**：使用环境变量和配置文件分离敏感信息
2. **日志系统**：实现结构化日志，便于问题排查
3. **监控告警**：添加基本的监控和告警机制
4. **容器化部署**：使用 Docker 容器化部署，简化环境管理
5. **持续集成**：设置 CI/CD 流程，自动测试和部署

## 6. 未来发展方向

1. **多模态支持**：增强对图像、音频、视频等多模态内容的处理能力
2. **长-term 记忆**：实现更强大的长期记忆系统，避免上下文丢失
3. **自主学习**：让系统能够从交互中学习，不断改进性能
4. **多代理协作**：实现多个代理之间的协作，解决复杂任务
5. **更丰富的工具生态**：扩展工具库，支持更多场景
6. **更智能的技能推荐**：根据用户需求自动推荐相关技能
7. **安全性增强**：加强系统安全性，防止恶意使用

## 7. 结论

nanobot 是一个设计精良的轻量级 AI 助手框架，通过精简的代码实现了丰富的功能。其核心优势在于模块化的架构设计、高效的消息处理机制、灵活的工具系统和可扩展的技能系统。

通过本文档的分析，我们可以看到 nanobot 的设计理念和实现细节，这些都可以作为开发 TypeScript 框架的重要参考。无论是从架构设计、模块划分还是具体实现，nanobot 都提供了很多值得借鉴的经验。

希望本文档能够帮助你理解 nanobot 的设计理念和实现细节，从而指导你开发出更加优秀的 TypeScript AI 助手框架。

---

**参考资料**：
- [nanobot GitHub 仓库](https://github.com/HKUDS/nanobot)
- [LiteLLM 文档](https://docs.litellm.ai/)
- [Python 异步编程文档](https://docs.python.org/3/library/asyncio.html)
- [TypeScript 官方文档](https://www.typescriptlang.org/docs/)
- [RxJS 文档](https://rxjs.dev/docs/)