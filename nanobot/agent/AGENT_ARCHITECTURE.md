# Agent 架构与功能分析

## 1. 项目概述

nanobot 是一个超轻量级的个人 AI 助手，核心代码仅约 4,000 行，比类似项目小 99%。Agent 目录包含了 nanobot 的核心智能代理逻辑，负责处理用户请求、执行工具操作、管理内存和技能等功能。

## 2. Agent 目录结构

```
nanoagent/
├── __init__.py         # 导出核心类
├── context.py          # 构建 LLM 上下文
├── loop.py             # 核心代理循环
├── memory.py           # 内存存储系统
├── skills.py           # 技能加载器
├── subagent.py         # 子代理管理器
└── tools/              # 内置工具集
    ├── __init__.py
    ├── base.py         # 工具基类
    ├── cron.py         # 定时任务工具
    ├── filesystem.py   # 文件系统工具
    ├── message.py      # 消息工具
    ├── registry.py     # 工具注册表
    ├── shell.py        # 命令执行工具
    ├── spawn.py        # 子代理生成工具
    └── web.py          # 网络搜索工具
```

## 3. 核心组件分析

### 3.1 AgentLoop（核心代理循环）

AgentLoop 是 nanobot 的核心处理引擎，负责：

- 接收来自消息总线的消息
- 构建上下文（历史记录、内存、技能）
- 调用 LLM 提供商
- 执行工具调用
- 生成响应并发送回用户

**核心工作流程**：
1. 从消息总线消费入站消息
2. 获取或创建会话
3. 构建初始消息上下文
4. 进入代理循环，调用 LLM 并处理工具调用
5. 生成最终响应并保存到会话
6. 发布出站消息到消息总线

### 3.2 ContextBuilder（上下文构建器）

ContextBuilder 负责构建 LLM 的上下文，包括：

- 系统提示（从引导文件、内存和技能构建）
- 对话历史记录
- 当前用户消息
- 可选的媒体内容

**主要功能**：
- 加载引导文件（AGENTS.md、SOUL.md、USER.md 等）
- 读取内存上下文（长期记忆和今日笔记）
- 加载技能（始终加载的技能和可用技能摘要）
- 构建完整的消息列表用于 LLM 调用

### 3.3 MemoryStore（内存存储系统）

MemoryStore 提供持久化内存功能，支持：

- 日常笔记（memory/YYYY-MM-DD.md）
- 长期记忆（MEMORY.md）
- 最近记忆检索

**主要功能**：
- 读取和写入今日笔记
- 读取和写入长期记忆
- 获取过去 N 天的记忆
- 列出所有内存文件
- 构建内存上下文用于 LLM

### 3.4 SkillsLoader（技能加载器）

SkillsLoader 负责加载和管理代理技能，技能是 Markdown 文件（SKILL.md），用于教导代理如何使用特定工具或执行特定任务。

**主要功能**：
- 列出所有可用技能（工作区技能优先于内置技能）
- 加载技能内容
- 构建技能摘要（用于渐进式加载）
- 检查技能要求（命令行工具、环境变量）
- 获取标记为始终加载的技能

### 3.5 SubagentManager（子代理管理器）

SubagentManager 负责管理后台子代理执行，子代理是轻量级的代理实例，用于处理特定任务。

**主要功能**：
- 生成子代理以在后台执行任务
- 为子代理构建专注的系统提示
- 执行子代理任务并处理工具调用
- 向主代理宣布子代理执行结果
- 管理运行中的子代理任务

### 3.6 ToolRegistry（工具注册表）

ToolRegistry 负责注册和管理代理工具，提供工具定义和执行功能。

**内置工具**：
- 文件系统工具（读取、写入、编辑、列出目录）
- 命令执行工具（执行 shell 命令）
- 网络工具（网页搜索、网页抓取）
- 消息工具（发送消息到聊天平台）
- 子代理工具（生成子代理）
- 定时任务工具（添加、列出、删除定时任务）

## 4. 工作流程

### 4.1 消息处理流程

1. **消息接收**：Channel 接收用户消息并发布到消息总线
2. **会话管理**：SessionManager 获取或创建会话
3. **上下文构建**：ContextBuilder 构建 LLM 上下文
4. **LLM 调用**：AgentLoop 调用 LLM 提供商
5. **工具执行**：如果 LLM 返回工具调用，执行相应工具
6. **结果处理**：将工具执行结果添加到上下文
7. **响应生成**：生成最终响应并发送给用户
8. **会话保存**：保存会话历史到磁盘

### 4.2 子代理执行流程

1. **子代理生成**：主代理通过 SpawnTool 生成子代理
2. **任务执行**：子代理在后台执行指定任务
3. **工具调用**：子代理可以调用文件、命令、网络等工具
4. **结果宣布**：子代理完成任务后，向主代理宣布结果
5. **用户通知**：主代理将结果总结后通知用户

## 5. 关键功能

### 5.1 内存管理

nanobot 通过 MemoryStore 提供持久化内存功能：

- **日常笔记**：自动创建每日笔记文件，记录当天的重要信息
- **长期记忆**：存储长期重要信息，如用户偏好、重要事件等
- **记忆检索**：支持获取过去 N 天的记忆，为 LLM 提供上下文

### 5.2 技能系统

nanobot 的技能系统允许轻松扩展代理能力：

- **技能定义**：使用 Markdown 文件定义技能，包含描述、使用方法等
- **技能要求**：支持指定技能所需的命令行工具和环境变量
- **渐进式加载**：默认只加载技能摘要，需要时再读取完整内容
- **技能优先级**：工作区技能优先于内置技能，支持自定义扩展

### 5.3 子代理系统

子代理系统允许代理在后台执行复杂任务：

- **后台执行**：子代理在后台运行，不阻塞主代理
- **专注任务**：子代理具有专注的系统提示，只完成指定任务
- **工具访问**：子代理可以使用文件、命令、网络等工具
- **结果通知**：子代理完成后自动通知用户

### 5.4 多平台集成

通过消息总线和通道系统，nanobot 支持多种聊天平台：

- Telegram
- WhatsApp
- Discord
- Feishu
- DingTalk

## 6. 代码示例

### 6.1 使用 AgentLoop 处理消息

```python
# 初始化 AgentLoop
agent_loop = AgentLoop(
    bus=message_bus,
    provider=llm_provider,
    workspace=workspace_path,
    model="anthropic/claude-opus-4-5",
    brave_api_key="your_brave_api_key",
    restrict_to_workspace=True
)

# 运行代理循环
await agent_loop.run()

# 处理直接消息
response = await agent_loop.process_direct("What is 2+2?")
print(response)  # 输出: "4"
```

### 6.2 使用 MemoryStore 管理内存

```python
# 初始化内存存储
memory = MemoryStore(workspace=workspace_path)

# 追加今日笔记
await memory.append_today("用户喜欢意大利菜")

# 写入长期记忆
memory.write_long_term("用户的重要信息：\n- 喜欢意大利菜\n- 生日：1990-01-01")

# 获取内存上下文
context = memory.get_memory_context()
print(context)
```

### 6.3 使用 SubagentManager 生成子代理

```python
# 初始化子代理管理器
subagent_manager = SubagentManager(
    provider=llm_provider,
    workspace=workspace_path,
    bus=message_bus,
    model="anthropic/claude-opus-4-5"
)

# 生成子代理执行任务
status = await subagent_manager.spawn(
    task="研究 Python 3.12 的新特性",
    label="Python 3.12 研究",
    origin_channel="telegram",
    origin_chat_id="123456789"
)
print(status)  # 输出: "Subagent [Python 3.12 研究] started (id: abc123). I'll notify you when it completes."
```

## 7. 配置与依赖

### 7.1 主要配置项

- **providers**：LLM 提供商配置（API 密钥、模型等）
- **channels**：聊天平台配置（令牌、允许的用户等）
- **tools**：工具配置（执行超时、工作区限制等）
- **agents**：代理配置（默认模型、最大迭代次数等）

### 7.2 核心依赖

- **Python 3.11+**：运行环境
- **loguru**：日志管理
- **pydantic**：配置验证
- **aiosignal**：异步信号处理
- **litellm**：LLM 提供商集成
- **telegram**：Telegram 集成（可选）
- **discord**：Discord 集成（可选）
- **whatsapp-web.js**：WhatsApp 集成（可选）
- **feishu**：Feishu 集成（可选）

## 8. 总结

nanobot 的 Agent 架构设计简洁而强大，通过模块化的组件和清晰的工作流程，实现了一个功能完整的智能代理系统。其核心优势包括：

- **轻量级设计**：核心代码仅约 4,000 行，启动快，资源占用低
- **模块化架构**：各组件职责明确，易于理解和扩展
- **丰富的工具集**：支持文件操作、命令执行、网络搜索等多种工具
- **持久化内存**：通过文件系统实现持久化内存，无需额外数据库
- **技能系统**：通过 Markdown 文件定义技能，易于扩展
- **子代理系统**：支持后台执行复杂任务，提高用户体验
- **多平台集成**：支持多种聊天平台，随时随地与代理交互

nanobot 的设计理念是"小而美"，通过最小化代码量和依赖，实现了一个功能完整、易于部署和扩展的 AI 助手系统。这种设计使其成为研究和开发的理想起点，也为个人用户提供了一个轻量级但功能强大的 AI 助手解决方案。

## 9. 未来发展方向

- **多模态支持**：增加对图像、语音、视频的支持
- **长期记忆增强**：改进记忆检索和管理机制
- **更好的推理能力**：实现多步规划和反思
- **更多集成**：支持 Slack、邮件、日历等更多服务
- **自我改进**：从用户反馈中学习和改进

---

*nanobot - 超轻量级个人 AI 助手*