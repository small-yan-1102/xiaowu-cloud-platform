# Harness Engineering 完整指南

> 2026-04-01 | 理论体系 · 实战评估 · 编排器设计 · 钉钉自动化集成 · Skill 迭代反馈机制

---

## 目录

- [一、什么是 Harness Engineering](#一什么是-harness-engineering)
- [二、为何 Harness Engineering 会出现](#二为何-harness-engineering-会出现)
- [三、Harness 的核心组件](#三harness-的核心组件)
- [四、SKILL.md 技能文件规范](#四skillmd-技能文件规范)
- [五、5 大技能设计模式](#五5-大技能设计模式)
- [六、Anthropic 的长时运行 Agent 驾驭策略](#六anthropic-的长时运行-agent-驾驭策略)
- [七、实战案例：iteration 技能集评估](#七实战案例iteration-技能集评估)
- [八、编排器设计：如何启动 Sub-Agent](#八编排器设计如何启动-sub-agent)
- [九、钉钉自动化集成：Java 中间层方案](#九钉钉自动化集成java-中间层方案)
- [十、Skill 迭代反馈机制](#十skill-迭代反馈机制)
- [十一、基础设施落地：云效 + 阿里云 Serverless](#十一基础设施落地云效--阿里云-serverless)
- [十二、量化效果](#十二量化效果)
- [十三、最佳实践总结](#十三最佳实践总结)
- [十四、生态系统概览](#十四生态系统概览)
- [十五、核心结论](#十五核心结论)
- [参考资料](#参考资料)

---

## 一、什么是 Harness Engineering

Harness Engineering（驾驭工程）是 AI Agent 时代新兴的工程学科，处于 Prompt Engineering 与 Context Engineering 之上的更高抽象层次。

| 概念 | 关注点 |
|------|--------|
| **Prompt Engineering** | 问什么（what to ask） |
| **Context Engineering** | 发什么给模型（what to send the model） |
| **Harness Engineering** | 整个系统如何运作（how the whole thing operates） |

**核心定义**（来自 [Louis Bouchard](https://www.louisbouchard.ai/harness-engineering/)）：

> "作为驾驭工程师，你不是在编写智能本身，而是在构建智能所居住的世界。那个世界的质量——Agent 感知的清晰度、行动的精确度、可用知识的丰富度——直接决定了智能的表达效果。"

Harness 的词义本身即"马具/驾驭装置"：模型是马，Harness 是套在马身上的整套装备，决定马能跑多远、跑多稳。

---

## 二、为何 Harness Engineering 会出现

### 2.1 能力拐点触发系统性需求

> "Agents got good enough to be useful, but not reliable enough to trust on their own."

当 AI Agent 足够强大到能写代码、调用工具，开发者发现失败的原因不再是"模型不够聪明"，而是"**配置问题**"：

- 系统提示写得模糊
- 上下文膨胀导致"愚蠢区"（dumb zone）
- 没有验证和回压机制
- Agent 在多会话长任务中失去记忆

### 2.2 核心哲学转变

从"等待更好的模型"转向：

> **"每次 Agent 犯错，就工程化地改造环境，让它无法以同样的方式再犯同一个错误。"**

可靠性从模型属性变为**系统属性**。

---

## 三、Harness 的核心组件

来自 [HumanLayer Blog](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) 的权威框架，Harness 由以下五大组件构成：

### 3.1 全局指令文件（CLAUDE.md / AGENTS.md）

#### 本质

CLAUDE.md 是 Claude Code 的**项目持久记忆**——写一次，每次会话自动加载，无需重复交代上下文。它不是系统提示的一部分，而是以 user message 的形式注入到每次对话开头，Claude 读取后尝试遵守。

#### 三层记忆体系

Claude Code 的记忆由三层构成，互相补充：

| 层级 | 来源 | 内容 | 生命周期 |
|------|------|------|---------|
| **Session Memory** | 当前对话 | 所有提示、回复、工具输出、文件内容 | session 结束即消失 |
| **Project Memory（CLAUDE.md）** | 你手动编写 | 项目规范、构建命令、架构约定、团队规则 | 永久，每次 session 自动加载 |
| **Auto Memory** | Claude 自动写入 | 调试经验、代码风格偏好、工作流习惯 | 永久，自动积累 |

#### 文件位置与作用域

CLAUDE.md 可以放在多个层级，**范围越小优先级越高，不会相互覆盖而是叠加**：

```
/Library/Application Support/ClaudeCode/CLAUDE.md  ← 企业管控层（IT 统一部署，不可排除）
~/.claude/CLAUDE.md                                 ← 个人全局层（所有项目生效）
~/.claude/rules/                                    ← 个人规则目录
project-root/CLAUDE.md                              ← 项目层（团队共享，提交到 Git）
project-root/.claude/CLAUDE.md                      ← 项目层（等价位置）
project-root/.claude/rules/                         ← 项目规则目录
project-root/CLAUDE.local.md                        ← 本地个人层（.gitignore，不提交）
project-root/src/module/CLAUDE.md                   ← 子目录层（懒加载）
```

**加载机制**：
- Claude Code 从当前工作目录**向上**遍历到根目录，加载沿途所有 CLAUDE.md
- 当前目录**以下**的子目录 CLAUDE.md **不会在启动时加载**，只有当 Claude 实际读取该目录的文件时才懒加载
- 子目录规则只在处理对应目录的文件时生效，节省 token

#### AGENTS.md 与 CLAUDE.md 的关系

如果仓库已有 `AGENTS.md`（供其他 AI 工具使用），不要重复编写：

```markdown
<!-- CLAUDE.md -->
@AGENTS.md

## Claude Code 专有指令

billing/ 目录下的改动必须使用 plan mode。
```

Claude 加载时会把 `AGENTS.md` 内容导入，再追加 Claude 专有指令。

#### `.claude/rules/` — 模块化规则目录

超过 200 行时，把规则拆分到 `.claude/rules/` 目录，每个文件只覆盖一个主题：

```
.claude/
├── CLAUDE.md               # 核心指令 + 索引（保持简短）
└── rules/
    ├── code-style.md       # 代码风格
    ├── testing.md          # 测试规范
    ├── api-design.md       # API 设计规范
    └── security.md         # 安全要求
```

**路径条件规则**（Path-specific rules）——只在处理匹配文件时加载，其余时间不消耗 token：

```markdown
---
paths:
  - "src/api/**/*.ts"
---

# API 开发规范

- 所有接口必须包含入参校验
- 使用统一错误响应格式
- 必须附 OpenAPI 注释
```

#### `@` 导入语法

CLAUDE.md 可以用 `@` 语法引入其他文件，在会话启动时一并加载：

```markdown
<!-- CLAUDE.md -->
参考 @README.md 了解项目概览，@package.json 查看可用命令。

# 额外指令
- git 工作流 @docs/git-workflow.md
- 个人偏好 @~/.claude/my-preferences.md  ← 本机文件，不进 Git
```

最大递归深度 5 层。

#### Auto Memory — Claude 自动写入的记忆

Auto Memory 让 Claude 跨 session 积累知识，无需手动维护：

```
~/.claude/projects/<project>/memory/
├── MEMORY.md          # 索引文件，每次 session 加载前 200 行或 25KB
├── debugging.md       # 调试经验（按需读取）
├── api-conventions.md # API 设计决策（按需读取）
└── ...
```

- 当你说"记住用 pnpm 不用 npm"，Claude 自动写入 Auto Memory
- 想写入 CLAUDE.md，明确说"把这个加到 CLAUDE.md"
- 通过 `/memory` 命令可以查看、编辑、删除所有记忆文件

**CLAUDE.md vs Auto Memory**：
- CLAUDE.md = **你的要求**（团队规范、架构决策）
- Auto Memory = **Claude 的观察**（它发现的模式、你的偏好）

#### 编写原则

| 原则 | 说明 |
|------|------|
| **控制长度** | 每个 CLAUDE.md 目标 200 行以内；超出后合规率下降 |
| **写具体不写模糊** | `使用 2 空格缩进` 优于 `格式化代码` |
| **只写通用规则** | 只写对所有任务都适用的内容；写了不用等于没写 |
| **渐进式披露** | 告诉 Claude **如何找到**信息，而不是把所有信息都塞进来 |
| **避免冲突** | 两条规则矛盾时 Claude 会随机选一条，定期审查清理 |
| **HTML 注释不消耗 token** | `<!-- 维护者备注 -->` 对 Claude 不可见，可以用来写给人看的注释 |

#### 常见错误排查

| 问题 | 原因 | 解决方式 |
|------|------|---------|
| Claude 没有遵守 CLAUDE.md | 指令太模糊或存在冲突 | 运行 `/memory` 确认文件已加载；使指令更具体 |
| 指令在 `/compact` 后消失 | 指令只写在对话中，未写入 CLAUDE.md | 把重要指令写入 CLAUDE.md 文件 |
| CLAUDE.md 太大 | 把所有规则都堆进一个文件 | 拆分到 `.claude/rules/` 并用 `@` 导入 |
| 不知道 Auto Memory 保存了什么 | — | `/memory` → 选择 auto memory 文件夹查看 |

### 3.2 工具与 MCP Server

#### 什么是 MCP？

**MCP（Model Context Protocol，模型上下文协议）** 是 Anthropic 于 2024 年 11 月发布的开放标准，定义了 AI Agent 与外部工具之间的统一通信接口。

> 类比：MCP 之于 AI 工具，相当于 USB-C 之于硬件外设——统一接口，消除碎片化。

**采用曲线**：

| 时间 | 事件 | 月下载量 |
|------|------|---------|
| 2024-11 | Anthropic 发布 MCP | ~200 万 |
| 2025-04 | OpenAI 采用 | 2200 万 |
| 2025-07 | Microsoft Copilot Studio 集成 | 4500 万 |
| 2025-11 | AWS Bedrock 支持 | 6800 万 |
| 2026-03 | 所有主流厂商接入 | 9700 万 |

#### MCP 架构

```
┌─────────────────────────────────┐
│          Claude Code            │
│         (MCP Client)            │
└──────────────┬──────────────────┘
               │ JSON-RPC
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌──────▼──────┐
│ MCP Server  │  │ MCP Server  │  ...
│  (GitHub)   │  │ (DingTalk)  │
└─────────────┘  └─────────────┘
```

核心概念：
- **MCP Client**：Claude Code，发出工具调用请求
- **MCP Server**：轻量进程，将外部服务封装为标准工具
- **Tool**：带类型 schema 的单个可调用动作
- **Transport**：客户端与服务端的通信信道

#### 三种传输协议

| 协议 | 延迟 | 适用场景 |
|------|------|---------|
| **stdio** | < 10ms | 本地开发，隔离性最好 |
| **SSE** | 100-500ms | 团队共享服务器 |
| **HTTP Streamable** | 80-400ms | 云服务，**2026 年推荐标准** |

#### 主流 MCP Server 示例

```bash
# GitHub — 代码托管协作（15 个工具）
claude mcp add github \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=YOUR_TOKEN \
  -- npx -y @modelcontextprotocol/server-github

# Brave Search — 网络搜索（3 个工具）
claude mcp add brave-search \
  --env BRAVE_API_KEY=YOUR_KEY \
  -- npx -y @modelcontextprotocol/server-brave-search

# Playwright — 浏览器自动化（12 个工具）
claude mcp add playwright \
  -- npx -y @modelcontextprotocol/server-playwright
```

#### 项目级配置 `.mcp.json`

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    },
    "dingtalk": {
      "command": "java",
      "args": ["-jar", "tools/dingtalk-mcp/dingtalk-mcp.jar"],
      "env": { "DINGTALK_APP_KEY": "${DINGTALK_APP_KEY}" }
    }
  }
}
```

密钥单独存放在 `.claude/settings.local.json`（加入 `.gitignore`）。

#### MCP 安全最佳实践

1. **最小权限原则**：只连接当前任务需要的 MCP Server
2. **密钥隔离**：`.mcp.json` 只存配置，密钥走环境变量
3. **只信任官方来源**：MCP Server 有代码执行能力，第三方需审查源码
4. **Token 轮换**：生产环境 API Token 每 90 天轮换一次

### 3.3 Skills（技能文件）

- 实现**渐进式上下文披露**（Progressive Disclosure）
- Agent 只在需要时加载特定技能，其余时间不消耗 token
- 以 `SKILL.md` 文件格式定义，兼容 30+ AI 工具

### 3.4 Sub-Agents（子代理）

- 作为**上下文防火墙**（Context Firewall）隔离中间步骤
- 防止工具调用污染主会话上下文
- 支持分层模型策略（不同复杂度任务使用不同规格模型）
- **关键约束：Sub-Agent 不能再生子 Agent**

### 3.5 Hooks（钩子）与回压机制（Back-Pressure）

- 在生命周期事件触发自动化脚本（验证、通知、审批）
- **只暴露错误**，不输出冗长的成功日志
- 测试、类型检查、覆盖率报告让 Agent 可以自我验证工作

---

## 四、SKILL.md 技能文件规范

### 4.1 文件格式

```markdown
---
name: skill-name
description: 语义触发关键词，精确描述技能适用场景
triggers:
  - /skill-command
version: 1.0.0
dependencies: []
---

# 技能指令正文
```

### 4.2 技能目录结构

```
skill-name/
├── SKILL.md          # 主指令文件（触发逻辑、执行步骤）
├── assets/           # 输出模板（Generator 模式用）
└── references/       # 背景知识（标准、检查清单、示例）
```

### 4.3 关键设计原则

- **分层激活**：触发词 → 描述 → 完整指令 → 模板 → 参考资料，按需加载
- **description 字段是语义索引**：写得越精确，Agent 激活越准确
- **硬门控 > 软建议**：用 `DO NOT proceed until...` 而非 `Consider checking...`

---

## 五、5 大技能设计模式

来自 [Lavi Nigam - Google ADK](https://lavinigam.com/posts/adk-skill-design-patterns/) 的权威研究，从 Anthropic、Vercel、Google 内部实践中归纳出的普适规律：

### Pattern 1: Tool Wrapper（工具封装）

将特定库/框架的规范封装为按需知识。最简单，最广泛使用。

```
agent-name/
└── references/conventions.md   ← 只在实际用到该技术时加载
```

### Pattern 2: Generator（生成器）

用固定模板确保输出结构的一致性。

```
agent-name/
├── assets/output-template.md   ← 填空模板
└── references/style-guide.md   ← 风格规范
```

### Pattern 3: Reviewer（审查者）

将"检查什么"与"如何检查"分离，检查单可替换。

```
agent-name/
└── references/review-checklist.md   ← 可替换的检查维度
```

### Pattern 4: Inversion（倒置）

Agent 先采访用户再执行，核心是**强制门控（Hard Gate）**：

```
DO NOT start building until all phases are complete.
```

### Pattern 5: Pipeline（流水线）

多步骤任务的强制顺序执行与检查点机制。

```
agent-name/
├── assets/                      ← 各阶段输出模板
├── references/quality-checklist.md
└── SKILL.md                     ← 定义步骤顺序和门控条件
```

### 模式组合矩阵

| 组合 | 效果 |
|------|------|
| Inversion → Generator | 先收集需求，再用模板生成一致输出 |
| Pipeline + Reviewer | 多步流水线 + 末尾自动质量检查 |
| Tool Wrapper ⊂ Pipeline | 流水线中按需加载特定技术规范 |

---

## 六、Anthropic 的长时运行 Agent 驾驭策略

来自 [Anthropic Engineering Blog](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)，针对跨多个上下文窗口的长任务：

### 核心挑战

> "每个新会话以对之前发生的一切毫无记忆开始——就像一个由不同轮班工程师组成的软件项目，每个新工程师上班时对上一班发生的事情没有任何记忆。"

### 双代理解决方案

**Initializer Agent（初始化代理）**：首次运行建立环境，创建进度追踪文件和初始状态清单。

**Coding Agent（编码代理）**：
- 每次会话启动：读取进度文件 + 运行基础功能测试
- 每次只处理一个功能，完成后更新进度文件
- 使用端到端验证（Puppeteer MCP 等）

**核心原则**：不依赖 session 连续，依赖**显式状态文件**。

---

## 七、实战案例：iteration 技能集评估

### 7.1 评估结论：高度符合，有 3 个关键缺口

`skills/iteration/` 下的 4 个技能（backend-prd-review、frontend-prd-review、test-prd-review、backend-tech-design-mvc）是教科书级的 HE 实践：

| 评估维度 | 状态 | 说明 |
|---------|------|------|
| SKILL.md 格式规范 | ✅ | frontmatter 完整，description 精准 |
| 模式组合 | ✅ | Inversion(P0) + Generator(P3) + Reviewer(P4) 三模式叠加 |
| 强制门控 | ✅ | 每个关键节点都有 🔵 用户确认，拒绝跳过 |
| 渐进式披露 | ✅ | assets/ + references/ 按需加载，不预注入 |
| 双文档策略 | ✅ | 设计摘要（人读）+ AI 详设（AI 读）清晰分离 |
| 回压机制 | ✅ | 自审循环 + 奥卡姆剃刀过滤 |
| 模式感知 | ✅ | workflow mode / standalone mode 均已处理 |

### 7.2 缺口 1：跨会话状态管理（最核心的缺失）

目前项目里**没有 `state.md`**。新 session 启动后对之前的一切一无所知，编排器无法回答：现在在哪个阶段？哪些 skill 已完成？是否等待审批中？

#### state.md Schema 设计

```markdown
# 迭代工作流状态

## 基本信息
- iteration_name: xxx
- prd_path: .qoder/workflow/input/prd.md
- current_stage: stage-2-backend-review
- approvers: [张三, 李四]
- last_updated: 2026-04-01 14:30

## 阶段状态

| 阶段 | 状态 | 输出文件 | 审批状态 | 钉钉消息ID |
|------|------|---------|---------|-----------|
| stage-1-prd-input | ✅ completed | .qoder/workflow/input/prd.md | 不需要 | - |
| stage-2-backend-review | 🔄 in_progress | - | 待审批 | - |
| stage-3-frontend-review | ⏸ pending | - | - | - |
| stage-4-test-review | ⏸ pending | - | - | - |
| stage-5-tech-design | ⏸ pending | - | - | - |

## 当前阻塞
- type: awaiting_approval
- stage: stage-2-backend-review
- dingtalk_message_id: msg_xxxxxx
- output_file: .qoder/workflow/outputs/backend-review-report.md
- approval_status: pending
- approval_feedback:
- approved_by:
- approval_time:
```

### 7.3 缺口 2：钉钉通知的技术接入点

> Claude Code 是基于 session 的，不能在一个 session 里"暂停等待钉钉回复"。

| 方案 | 机制 | 复杂度 | 适合场景 |
|------|------|--------|---------|
| Hook + 手动触发 | skill 完成 → Hook 发钉钉 → 人工启动下一 session | 低 | 低频 |
| MCP Server | skill 调用发消息/读回复 → state.md 记录 → 编排器判断 | 中 | 中频 |
| **Java 中间层（推荐）** | 钉钉回调 → Java 解析 → 写 state.md → 触发 claude -p | 中高 | 生产环境 |

### 7.4 缺口 3：编排器的上下文隔离

在同一 session 里顺序调用 4 个 skill，上下文窗口会撑爆。正确姿势：**编排器启动 Sub-Agent，每个 Sub-Agent 有独立上下文**。

---

## 八、编排器设计：如何启动 Sub-Agent

### 8.1 核心约束

官方文档明确：

> **"Subagents cannot spawn other subagents."**

**编排器必须运行在主会话（main conversation）里**，由 SKILL.md 驱动，通过 Agent 工具派生子 Agent。

```
主会话（orchestrator SKILL.md 在这里运行）
  ├── 读 state.md
  ├── 启动 Sub-Agent → backend-prd-review（独立上下文）
  │     └── 完成 → 写 state.md → 退出
  ├── 更新 state.md，判断是否需要钉钉审批
  └── 发通知 → 写 state.md → 退出 session
```

### 8.2 三种启动写法

**写法一：自然语言（最简单）**

```markdown
使用 backend-prd-review sub-agent 对 [prd_path] 进行审查，
完成后将审查报告路径写入 state.md。
```

**写法二：@-mention 强制指定（推荐）**

```markdown
使用 @agent-backend-prd-reviewer 对以下 PRD 进行审查：
- PRD 文件：读取 state.md 中的 prd_path 字段
- 输出路径写入：.qoder/workflow/outputs/backend-review-report.md
- 完成后将 stage-2 状态更新为 completed
```

**写法三：Sub-Agent 定义文件 + skills 预加载（最工程化）**

在 `.claude/agents/backend-prd-reviewer.md`：

```markdown
---
name: backend-prd-reviewer
description: 对 PRD 进行后端技术可行性审查。当需要执行 backend PRD review 时使用。
tools: Read, Write, Bash, Glob, Grep
model: sonnet
skills:
  - backend-prd-review
memory: project
---

你是一名后端技术评审专家。
启动时先读取 .qoder/workflow/state.md 获取任务参数，
完成后将输出文件路径和状态更新写回 state.md。
```

> `skills` 字段：Sub-Agent 启动时全量注入指定 SKILL.md 内容，上下文直接就绪，无需再触发 skill。

### 8.3 Sub-Agent 定义文件清单

| 文件（.claude/agents/） | 预注入 Skill | 职责 |
|------------------------|-------------|------|
| `backend-prd-reviewer.md` | `backend-prd-review` | 后端视角 PRD 审查 |
| `frontend-prd-reviewer.md` | `frontend-prd-review` | 前端视角 PRD 审查 |
| `test-prd-reviewer.md` | `test-prd-review` | 测试视角 PRD 审查 |
| `backend-tech-designer.md` | `backend-tech-design-mvc` | MVC 技术设计生成 |

### 8.4 编排器 SKILL.md 骨架

```markdown
---
name: iteration-orchestrator
description: 迭代工作流编排器。统一管控 PRD 审查和技术设计的全流程。
triggers:
  - /iteration-start
  - /iteration-resume
version: 1.0.0
---

## 启动逻辑

读取 .qoder/workflow/state.md：
- 文件不存在 → [初始化流程]
- current_stage = "awaiting_approval" → [审批检查流程]
- 否则 → [执行流程]

## 初始化流程

询问：迭代名称？PRD 路径？
创建 state.md，current_stage = "stage-2-backend-review"，进入 [执行流程]。

## 执行流程

按 current_stage 顺序执行：

### stage-2-backend-review
启动 @agent-backend-prd-reviewer。完成后：
- 更新 state.md（completed + 输出路径）
- 调用钉钉 MCP 发送审批通知
- current_stage → "awaiting_approval"，退出 session

### stage-3-frontend-review → stage-4-test-review → stage-5-tech-design
（同上，使用对应 Sub-Agent）

## 审批检查流程

调用钉钉 MCP check_approval_status：
- approved → current_stage 推进到下一阶段，进入 [执行流程]
- rejected → 通知用户，终止工作流
- modify   → 将 approval_feedback 作为上下文，重新启动当前阶段 Sub-Agent
- pending  → 提示"审批未完成，请完成后运行 /iteration-resume"，退出
```

---

## 九、钉钉自动化集成：Java 中间层方案

### 9.1 为什么要 Java 中间层

**自定义机器人（Webhook 机器人）= 只能发，不能收。**

必须使用**企业内部机器人（App 机器人）**，配置回调地址后才能接收群消息。Java 中间层负责处理所有"可靠性"工作，让 Claude Code 只专注 AI 推理。

| 能力 | Python 脚本 | Java 服务 |
|------|------------|----------|
| 钉钉验签 | 手写 | Spring Security / 拦截器 |
| 并发回调 | 不处理 | 线程池自动处理 |
| state.md 原子写 | 可能竞争 | synchronized / 文件锁 |
| 失败重试 | 无 | Spring Retry |
| 日志与监控 | print | Logback + Actuator |

### 9.2 整体架构

```
┌─────────────────────────────────────┐
│           钉钉群                     │  人工交互层
│  审批人 @机器人 回复「修改：xxx」      │
└──────────────┬──────────────────────┘
               │ HTTP 回调
┌──────────────▼──────────────────────┐
│        Java 中间层（Spring Boot）    │  可靠性层
│  ├── 验签（HMAC-SHA256）             │
│  ├── 意图解析（通过/拒绝/修改）       │
│  ├── 写 state.md（原子操作）         │
│  ├── 触发 claude -p（异步）          │
│  └── 回复钉钉确认消息                │
└──────────────┬──────────────────────┘
               │ ProcessBuilder
┌──────────────▼──────────────────────┐
│        Claude Code（无头模式）       │  AI 执行层
│  claude -p "/iteration-resume"       │
│  ├── 读 state.md                    │
│  ├── approved → 继续下一阶段        │
│  └── modify   → 带 feedback 重跑   │
└─────────────────────────────────────┘
```

### 9.3 session 连续性说明

`claude -p` 每次都是**全新 session**，不是接着上一个 session 继续。连续性完全来自 `state.md`：

```
Session A（编排器）          Session B（Java 触发）
  执行 stage-2               读 state.md
  写 state.md ──────────→   看到 stage-2 completed + feedback
  退出                       从 stage-3 继续执行
```

新 session 启动后，编排器 SKILL.md 第一件事就是读 state.md，它"知道"的一切来自这个文件。这正是 Anthropic 所说的"轮班工程师交班记录"模式。

### 9.4 支持的回复指令

| 钉钉回复 | 触发效果 |
|---------|---------|
| `通过` / `approve` / `LGTM` | 推进到下一阶段 |
| `拒绝：[原因]` | 终止工作流，记录原因 |
| `修改：[具体反馈]` | 带反馈重跑当前阶段 |
| `状态` | 机器人回复当前 state.md 摘要 |

### 9.5 Java 核心实现

**Webhook Controller**

```java
@RestController
@RequestMapping("/dingtalk")
public class DingTalkWebhookController {

    @PostMapping("/callback")
    public DingTalkReply handleCallback(@RequestBody DingTalkMessage message) {
        String text   = message.getText().getContent().trim();
        String sender = message.getSenderNick();

        ApprovalIntent intent = IntentParser.parse(text);

        if (intent.getType() == IntentType.UNKNOWN) {
            return DingTalkReply.text("未识别指令，支持：通过 / 拒绝：原因 / 修改：反馈");
        }

        stateService.updateApproval(intent, sender);   // 写 state.md
        claudeService.resume(projectPath);              // 触发新 session（异步）

        return DingTalkReply.text("✅ 已收到「" + intent.getType() + "」，正在触发后续流程...");
    }
}
```

**意图解析**

```java
public class IntentParser {
    private static final Map<String, IntentType> KEYWORDS = Map.of(
        "通过",    IntentType.APPROVED,
        "approve", IntentType.APPROVED,
        "lgtm",    IntentType.APPROVED,
        "拒绝",    IntentType.REJECTED,
        "reject",  IntentType.REJECTED,
        "修改",    IntentType.MODIFY,
        "调整",    IntentType.MODIFY
    );

    public static ApprovalIntent parse(String text) {
        String lower = text.toLowerCase();
        for (var entry : KEYWORDS.entrySet()) {
            if (lower.contains(entry.getKey())) {
                String feedback = extractAfterKeyword(text, entry.getKey());
                return new ApprovalIntent(entry.getValue(), feedback);
            }
        }
        return new ApprovalIntent(IntentType.UNKNOWN, text);
    }
}
```

**触发 Claude Code 无头模式**

```java
@Service
public class ClaudeResumeService {

    public void resume(String projectPath) {
        // 异步执行，不阻塞钉钉回调响应
        CompletableFuture.runAsync(() -> {
            try {
                ProcessBuilder pb = new ProcessBuilder(
                    "claude", "-p", "/iteration-resume",
                    "--allowedTools", "Read,Write,Bash,Glob,Grep",
                    "--output-format", "text"
                );
                pb.directory(new File(projectPath));
                pb.environment().put("ANTHROPIC_API_KEY", System.getenv("ANTHROPIC_API_KEY"));
                pb.redirectErrorStream(true);

                Process process = pb.start();
                String output = new String(process.getInputStream().readAllBytes());
                log.info("Claude resume output:\n{}", output);
                process.waitFor(30, TimeUnit.MINUTES);
            } catch (Exception e) {
                log.error("Failed to resume Claude session", e);
            }
        });
    }
}
```

**写 state.md（原子操作）**

```java
@Service
public class StateService {

    public synchronized void updateApproval(ApprovalIntent intent, String sender) {
        Path path = Paths.get(stateFilePath);
        String content = Files.readString(path);

        content = content
            .replaceAll("- type: awaiting_approval",
                        "- type: " + intent.getType().name().toLowerCase())
            .replaceAll("- approval_status:.*",
                        "- approval_status: " + intent.getType().name().toLowerCase());

        if (!intent.getFeedback().isEmpty()) {
            content += "\n- approval_feedback: " + intent.getFeedback();
        }
        content += "\n- approved_by: " + sender;
        content += "\n- approval_time: " + LocalDateTime.now();

        Files.writeString(path, content);
    }
}
```

### 9.6 钉钉机器人配置步骤

```
钉钉开放平台 → 应用开发 → 企业内部应用
  → 创建应用
  → 机器人配置 → 开启「群消息接收」
  → 填写消息接收地址：https://your-server/dingtalk/callback
  → 获取 Token 和 EncodingAESKey
  → 将机器人加入目标群
```

> 本地开发时用 ngrok 暴露端口：`ngrok http 8080`

---

## 十、Skill 迭代反馈机制

HE 的核心哲学是：

> **"每次 Agent 犯错，就工程化地改造环境，让它无法以同样的方式再犯同一个错误。"**

这句话描述的不是一次性建好护栏，而是一个**持续迭代的闭环**。

### 10.1 当前设计的符合程度

iteration 技能集中，每个 checklist 条目、每个反模式、每个强制门控，**本身就是过去某次失败被固化成防护的结果**：

| 已有设计 | 防止了什么错误 |
|---------|--------------|
| Phase 0 Inversion | Agent 不问清楚范围就开始审查 |
| `DO NOT proceed until...` 硬门控 | Agent 跳过依赖检查直接执行 |
| 奥卡姆剃刀自审 | Agent 输出大量无意义的细枝末节 |
| 反模式清单（"支持大量数据"等） | Agent 放过模糊措辞不指出 |
| 9 个审查维度 checklist | Agent 漏掉某类问题 |
| 双文档策略 | AI 详设写成人读的，人读摘要写成 AI 读的 |

**结论：这些是这个原则的静态快照——过去的错误已经被工程化进去了。但缺少动态机制，让未来的错误也能持续被工程化进去。**

### 10.2 缺失的一环：反馈回路

```
Agent 犯错（skill 输出被钉钉打回）
        ↓
识别：这是哪类错误？根因在哪里？
  - checklist 遗漏了某个维度？
  - 门控条件不够严格？
  - 标准文件描述不够清晰？
        ↓
工程化：更新 SKILL.md 或 references 文件
        ↓
验证：同类错误不再出现
        ↓
（下次遇到新的错误模式，重复循环）
```

没有这个闭环，skill 系统会**老化**——护栏只反映过去的经验，不会随新的失败模式成长。

### 10.3 Skill 迭代协议设计

#### 触发时机

当某个 Sub-Agent 的输出在钉钉审批中被"拒绝"或"修改"时，Java 中间层在写 state.md 时同时追加失败记录：

```markdown
## 失败记录
- stage: stage-2-backend-review
- type: modify
- feedback: 接口命名不符合 RESTful 规范，漏掉了幂等性说明
- approved_by: 张三
- time: 2026-04-01 15:00
```

#### 工作流结束后的汇总

编排器在所有阶段完成后（stage-5 完成），执行最后一步：

```markdown
## 编排器 SKILL.md 末尾追加

## 工作流复盘（每次迭代结束后执行）

读取 state.md 中所有 type = modify 或 type = rejected 的记录。
如果存在记录，启动 @agent-skill-improver。
```

#### skill-improver Sub-Agent 定义

在 `.claude/agents/skill-improver.md`：

```markdown
---
name: skill-improver
description: 分析工作流失败记录，生成 skill 改进建议。在迭代工作流结束后触发。
tools: Read, Write, Glob
model: sonnet
memory: project
---

你是一名 skill 质量工程师。

启动时：
1. 读取 .qoder/workflow/state.md 中的所有失败记录
2. 对每条失败记录，分析根因：
   - 是 SKILL.md 的 checklist 缺少该维度？
   - 是 references 标准文件描述不清晰？
   - 是 Phase 0 的问题没有覆盖该场景？
3. 生成改进建议文件：.qoder/workflow/skill-improvement-suggestions.md
4. 格式如下：

---
# Skill 改进建议 - [迭代名称]

## backend-prd-review

### 问题
接口设计维度（API）未覆盖幂等性说明

### 建议修改
文件：skills/iteration/prd-review/backend-prd-review/references/backend-review-standard.md
位置：API 维度 checklist
增加条目：☐ 是否说明了接口的幂等性要求（POST/PUT/PATCH）

### 置信度
高（同类反馈出现 2 次以上）
---

5. 将建议文件路径写入 state.md。
6. 通过钉钉 MCP 发送通知，附上建议文件路径，请负责人确认是否合并。
```

#### 人工确认后合并

负责人在钉钉回复"合并"后，Java 中间层触发最后一个 session：

```bash
claude -p "读取 .qoder/workflow/skill-improvement-suggestions.md，
按建议修改对应的 SKILL.md 和 references 文件，
修改完成后提交 git commit。"
```

### 10.4 完整闭环示意

```
迭代工作流执行
      ↓
钉钉审批：「修改：接口缺幂等性说明」
      ↓
Java 中间层写 state.md（失败记录）
      ↓
工作流完成 → skill-improver 分析
      ↓
生成改进建议 → 钉钉通知负责人
      ↓
负责人确认「合并」
      ↓
Claude 自动修改 SKILL.md / references
      ↓
下次同类 PRD 审查：Agent 不再漏掉幂等性
```

这样，每次迭代的失败都会**沉淀为 skill 的永久改进**，系统持续进化而不是静态老化。

---

## 十一、基础设施落地：云效 + 阿里云 Serverless

本项目代码托管在**云效 Codeup**，CI/CD 流水线在**云效 Flow**，应用部署在**阿里云 SAE（Serverless 应用引擎）**。这套基础设施直接决定了各组件的部署位置。

### 11.1 核心架构决策：`claude -p` 在流水线里跑

**不要在本机运行 `claude -p`**，而是让云效 Flow 流水线承担 Claude Code 的执行环境。

原因：
- 本机运行依赖开发者在线，不可靠
- 流水线是已有的可靠基础设施，有日志、有监控、有重试
- 输入输出自然地走 git 管理，state.md 就在代码仓库里

### 11.2 完整部署架构

```
┌──────────────────────────────────────────────┐
│              钉钉群                           │
│  审批人 @机器人 回复「修改：接口缺幂等性说明」  │
└──────────────┬───────────────────────────────┘
               │ HTTP 回调
┌──────────────▼───────────────────────────────┐
│     Java 中间层（部署在阿里云 SAE）            │
│  ├── 验签 + 意图解析                          │
│  ├── 通过 Codeup API 提交 state.md 变更       │
│  └── 调用云效 Flow Webhook 触发流水线          │
└──────────────┬───────────────────────────────┘
               │ Webhook 触发
┌──────────────▼───────────────────────────────┐
│        云效 Flow 流水线                        │
│  Step 1: git checkout（拉取最新 state.md）     │
│  Step 2: claude -p "/iteration-resume"        │
│            ↓ 读 state.md → 执行 Sub-Agent     │
│            ↓ 生成报告 → 更新 state.md          │
│  Step 3: git add + commit + push              │
│  Step 4: 调用 SAE 上的 Java 服务发钉钉通知     │
└──────────────────────────────────────────────┘
```

### 11.3 state.md 存在哪里

**直接放在 Codeup 代码仓库里**，路径 `.qoder/workflow/state.md`。

这是最干净的方案：
- 不需要额外的 NAS / OSS
- state.md 的变更历史自然留在 git log 里
- 每次流水线拉代码就拿到最新状态
- 发生问题可以 `git log` 回溯每次状态转换

Claude Code 在流水线里运行时，用 git 工具提交对 state.md 和输出文件的修改：

```bash
# 流水线 Step 3 示意
git add .qoder/workflow/state.md
git add .qoder/workflow/outputs/
git commit -m "chore: [stage-2-backend-review] completed by Claude"
git push origin main
```

### 11.4 Java 中间层部署在 SAE

Spring Boot 应用直接部署到 SAE，零改造：

```yaml
# SAE 应用配置示意
应用名称: iteration-dingtalk-middleware
运行时: Java 17
部署包: jar
入口类: com.yourteam.DingTalkMiddlewareApplication
环境变量:
  ANTHROPIC_API_KEY: ${secret}
  CODEUP_ACCESS_TOKEN: ${secret}
  YUNXIAO_WEBHOOK_URL: ${secret}
  PROJECT_PATH: /home/admin/workspace
```

SAE 自动处理弹性伸缩，钉钉回调高峰时自动扩容，空闲时缩至 0 实例节省费用。

### 11.5 云效 Flow 流水线配置

在流水线里新增一个"Claude Code 执行"步骤：

```yaml
# 流水线 YAML 示意（云效 Flow）
stages:
  - name: AI 工作流执行
    steps:
      - name: 拉取代码
        type: checkout
        branch: main

      - name: 安装 Claude Code
        type: shell
        script: |
          npm install -g @anthropic-ai/claude-code
          claude --version

      - name: 执行迭代工作流
        type: shell
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        script: |
          claude -p "/iteration-resume" \
            --allowedTools "Read,Write,Bash,Glob,Grep" \
            --output-format text \
            --max-turns 50

      - name: 提交工作产物
        type: shell
        script: |
          git config user.name "Claude Code Bot"
          git config user.email "bot@yourteam.com"
          git add .qoder/workflow/
          git diff --staged --quiet || git commit -m "chore: workflow stage completed"
          git push origin main
```

### 11.6 Java 服务调用云效 Flow Webhook

Java 服务接到钉钉审批后，通过 Webhook 触发流水线：

```java
@Service
public class YunxiaoFlowService {

    @Value("${yunxiao.webhook.url}")
    private String webhookUrl;

    public void triggerPipeline(Map<String, String> envVars) {
        RestTemplate rest = new RestTemplate();

        Map<String, Object> body = new HashMap<>();
        body.put("envs", envVars);   // 可以透传审批结论、feedback 等

        rest.postForObject(webhookUrl, body, String.class);
        log.info("Triggered Yunxiao Flow pipeline");
    }
}
```

云效 Flow Webhook 触发命令：

```bash
curl -X POST \
  "http://flow-openapi.aliyun.com/pipeline/webhook/{your-token}" \
  -H "Content-Type: application/json" \
  -d '{"envs": {"APPROVAL_STATUS": "approved"}}'
```

### 11.7 通过 Codeup API 更新 state.md

Java 服务接到钉钉回复后，直接通过 Codeup Open API 提交 state.md 变更（不依赖本地 git）：

```java
@Service
public class CodeupStateService {

    // 云效 Codeup 文件更新 API
    // PUT /api/v3/projects/{id}/repository/files/{file_path}
    public void updateStateFile(String approvalStatus, String feedback, String sender) {
        String currentContent = getFileContent(".qoder/workflow/state.md");
        String newContent = patchApprovalFields(currentContent, approvalStatus, feedback, sender);

        codeupClient.updateFile(
            projectId,
            ".qoder/workflow/state.md",
            newContent,
            "chore: update approval status - " + approvalStatus
        );
    }
}
```

### 11.8 各组件部署位置汇总

| 组件 | 部署位置 | 说明 |
|------|---------|------|
| **SKILL.md 技能集** | Codeup 代码仓库 | 随代码管理，团队共享 |
| **state.md** | Codeup 代码仓库 | `.qoder/workflow/state.md` |
| **审查报告 / 设计文档** | Codeup 代码仓库 | `.qoder/workflow/outputs/` |
| **Java 钉钉中间层** | 阿里云 SAE | Spring Boot，零改造上云 |
| **Claude Code 执行** | 云效 Flow 流水线 | `claude -p` 作为流水线步骤 |
| **密钥管理** | SAE 环境变量 / 云效密钥组 | `ANTHROPIC_API_KEY` 等敏感信息 |

### 11.9 完整触发链路

```
1. 编排器完成某阶段 → git commit state.md（awaiting_approval）→ push Codeup
2. Java SAE 服务 → 钉钉发送审批消息 → 记录 message_id 到 state.md
3. 审批人在钉钉回复「修改：xxx」
4. 钉钉回调 → Java SAE 服务
5. Java SAE → Codeup API 更新 state.md（写入 approval_feedback）
6. Java SAE → 调用云效 Flow Webhook 触发流水线
7. 云效 Flow → git checkout → claude -p "/iteration-resume"
8. Claude Code → 读 state.md → 启动 Sub-Agent → 带 feedback 重跑当前阶段
9. Claude Code → git commit 输出文件 + state.md → push Codeup
10. 云效 Flow → 调用 Java SAE API → 发下一条钉钉通知
```

---

## 十二、量化效果

来自 [revfactory/harness](https://github.com/revfactory/harness) 的受控实验（15 个软件工程任务）：

| 指标 | 无 Harness | 有 Harness | 提升 |
|------|-----------|-----------|------|
| 平均质量分 | 49.5 | 79.3 | **+60%** |
| 胜率 | — | 15/15 | **100%** |
| 输出方差 | — | — | **-32%** |

> **任务越复杂，提升越显著。**

---

## 十三、最佳实践总结

### 配置原则

1. **从简单开始，被动配置**：Agent 失败时再工程化，不要预防性过度优化
2. **CLAUDE.md 保持 60 行以内**：冗长的全局指令比没有指令更危险
3. **只连接你信任的工具**：禁用未使用的 MCP Server
4. **Skills 优先于系统提示**：渐进式披露比一次性注入更高效

### 技能设计原则

5. **description 字段要精确**：这是语义触发的索引，决定技能激活的准确性
6. **硬门控 > 软建议**：用 `DO NOT proceed until...` 而非 `Consider checking...`
7. **Phase 0 倒置**：复杂任务必须先采访用户，确定范围后再执行
8. **自审循环**：每个技能最后加入奥卡姆剃刀自检步骤

### 长任务 / 多会话原则

9. **不依赖 session 连续，依赖显式状态文件**：state.md 是唯一的真相来源
10. **编排器跑在主会话，子技能跑在 Sub-Agent**：上下文隔离，互不污染
11. **Sub-Agent 用 skills 字段预注入**：上下文直接就绪，无需二次触发
12. **人机协作边界清晰**：人做判断（审批），AI 做执行（生成/审查）

### 推进顺序

```
Step 1  设计 state.md schema（基础中的基础）
   ↓
Step 2  创建 4 个 Sub-Agent 定义文件（.claude/agents/*.md）
   ↓
Step 3  编写编排器 SKILL.md（Pipeline 模式）
   ↓
Step 4  单独测试每个 Sub-Agent（standalone mode）
   ↓
Step 5  测试编排器端到端串联（不含钉钉，手动确认代替）
   ↓
Step 6  实现 Java 中间层（Spring Boot + 钉钉 Webhook）
   ↓
Step 7  接入钉钉，测试完整 pause/resume 循环
   ↓
Step 8  打包 install-iteration-skill
```

---

## 十四、生态系统概览

| 工具/资源 | 类型 | 说明 |
|-----------|------|------|
| [agentskills.io](https://agentskills.io) | 规范 | SKILL.md 格式规范，兼容 30+ AI 工具 |
| [build-with-adk](https://github.com/lavinigam-gcp/build-with-adk/tree/main/adk-skill-design-patterns) | 参考实现 | Google ADK 5 模式完整代码示例 |
| [revfactory/harness](https://github.com/revfactory/harness) | Meta-skill | 自动为项目生成 Agent 团队和技能文件 |
| [Anthropic Engineering Blog](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 权威文章 | 长时运行 Agent 的 Harness 策略 |
| [HumanLayer Blog](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) | 实践总结 | 工程化配置方法论 |
| [Claude Code Sub-agents Docs](https://code.claude.com/docs/en/sub-agents) | 官方文档 | Sub-Agent 定义与调用完整参考 |
| [Claude Code Headless Docs](https://code.claude.com/docs/en/headless) | 官方文档 | claude -p 无头模式完整参考 |

---

## 十五、核心结论

Harness Engineering 代表了 AI Agent 工程从"试验性使用"走向"生产级可靠"的关键跨越：

1. **可靠性是系统属性**，而非模型属性
2. **结构化技能 > 自由式提示**：模式化设计让 AI 在复杂流程中可重复执行
3. **state.md 是跨会话连续性的唯一来源**：不依赖 session 记忆，依赖显式文件
4. **编排器 + Sub-Agent + Java 中间层**：三层分工清晰，各负其责
5. **Harness 是投资**：任务越复杂、越频繁，投资回报越高（+60% 质量提升有据可查）

---

## 参考资料

- [Skill Issue: Harness Engineering for Coding Agents | HumanLayer Blog](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)
- [Harness Engineering: The Missing Layer Behind AI Agents | Louis Bouchard](https://www.louisbouchard.ai/harness-engineering/)
- [Effective Harnesses for Long-Running Agents | Anthropic Engineering](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [5 Agent Skill Design Patterns Every ADK Developer Should Know | Lavi Nigam](https://lavinigam.com/posts/adk-skill-design-patterns/)
- [5 Agent Skill Design Patterns | Google Cloud Tech](https://x.com/GoogleCloudTech/status/2033953579824758855)
- [Create custom subagents | Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Run Claude Code programmatically | Claude Code Docs](https://code.claude.com/docs/en/headless)
- [build-with-adk reference implementation | GitHub](https://github.com/lavinigam-gcp/build-with-adk/tree/main/adk-skill-design-patterns)
- [revfactory/harness Meta-skill | GitHub](https://github.com/revfactory/harness)
- [企业内部机器人 Webhook | 钉钉开放平台](https://open.dingtalk.com/document/group/assign-a-webhook-url-to-an-internal-chatbot)
- [机器人回复/发送消息 | 钉钉开发者百科](https://open-dingtalk.github.io/developerpedia/docs/learn/bot/appbot/reply/)
