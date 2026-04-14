# Harness Engineering 完整报告

> 2026-04-01 | 基于公开权威资料与本地仓库深度整合

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

- 注入 system prompt 的仓库级 Markdown 文件
- **最佳实践**：保持 60 行以内，少即是多
- 定义全局行为规范、代码风格约定、禁止行为

### 3.2 工具与 MCP Server

#### 什么是 MCP？

**MCP（Model Context Protocol，模型上下文协议）** 是 Anthropic 于 2024 年 11 月发布的开放标准，定义了 AI Agent 与外部工具之间的统一通信接口。

> 类比：MCP 之于 AI 工具，相当于 USB-C 之于硬件外设——统一接口，消除碎片化。

在 MCP 出现之前，每个工具（GitHub、数据库、浏览器）都需要单独集成；MCP 建立了标准化的 JSON-RPC 通信层，让任何工具都能以相同方式接入任何 AI 客户端。

**采用曲线**（体现其重要性）：

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
│  (GitHub)   │  │ (Browser)   │
└─────────────┘  └─────────────┘
       ↓                ↓
  GitHub API      Playwright
```

核心概念：
- **MCP Client**：Claude Code，发出工具调用请求
- **MCP Server**：轻量进程，将外部服务封装为标准工具
- **Tool**：带类型 schema 的单个可调用动作（如 `create_issue`、`search_code`）
- **Transport**：客户端与服务端的通信信道

#### 三种传输协议

| 协议 | 延迟 | 适用场景 | 说明 |
|------|------|---------|------|
| **stdio** | < 10ms | 本地开发 | Claude Code 启动子进程，通过 stdin/stdout 通信；隔离性最好 |
| **SSE** | 100-500ms | 团队共享服务器 | 基于 HTTP 的服务器推送，适合远程服务 |
| **HTTP Streamable** | 80-400ms | 云服务（推荐） | 2025-03 规范新增，双向流式传输，**2026 年推荐标准** |

#### 主流 MCP Server 示例

**GitHub** — 代码托管与协作

```bash
claude mcp add github \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=YOUR_TOKEN \
  -- npx -y @modelcontextprotocol/server-github
```

暴露 15 个工具：`list_issues`、`create_pull_request`、`search_code`、`get_file_contents` 等。

Agent 能力扩展：自动读取 Issue → 分析代码 → 提交 PR，全程无需人工。

---

**Brave Search** — 网络搜索

```bash
claude mcp add brave-search \
  --env BRAVE_API_KEY=YOUR_KEY \
  -- npx -y @modelcontextprotocol/server-brave-search
```

3 个核心工具：`web_search`、`news_search`、`local_search`。
Agent 能力扩展：实时查阅文档、搜索错误解决方案。

---

**Playwright** — 浏览器自动化

```bash
claude mcp add playwright \
  -- npx -y @modelcontextprotocol/server-playwright
```

12 个工具：`navigate`、`click`、`screenshot`、`fill`、`evaluate` 等。
Agent 能力扩展：端到端测试验证、UI 交互截图、表单自动填写。

---

**Filesystem** — 本地文件系统

```bash
claude mcp add filesystem \
  -- npx -y @modelcontextprotocol/server-filesystem /path/to/workspace
```

基础读写工具，适用于隔离沙箱环境中的文件操作。

---

**自定义 MCP Server（50 行代码示例）**

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server({ name: "my-db-server", version: "1.0.0" });

server.setRequestHandler("tools/list", async () => ({
  tools: [{
    name: "query_db",
    description: "执行只读 SQL 查询",
    inputSchema: {
      type: "object",
      properties: { sql: { type: "string" } },
      required: ["sql"]
    }
  }]
}));

server.setRequestHandler("tools/call", async (req) => {
  const result = await db.query(req.params.arguments.sql);
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
});

await server.connect(new StdioServerTransport());
```

#### 配置方式

**方式一：CLI 命令（推荐快速上手）**

```bash
# 添加服务
claude mcp add <name> -- <command>

# 查看已配置
claude mcp list

# 移除服务
claude mcp remove <name>
```

**方式二：项目级 `.mcp.json`（推荐团队协作）**

在项目根目录创建 `.mcp.json`，提交到版本库（不含密钥）：

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"]
    }
  }
}
```

密钥单独存放在 `.claude/settings.local.json`（加入 `.gitignore`）：

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_xxxxxxxxxxxx"
  }
}
```

**方式三：全局配置 `~/.claude/settings.json`**

适用于所有项目共享的工具（如搜索、浏览器）。

#### MCP 与上下文管理

MCP 对上下文窗口的影响比直觉上小得多：

> **工具定义延迟加载**：会话启动时只加载工具名称列表；Agent 通过搜索工具发现需要的工具；只有实际调用的工具定义才进入上下文。

这意味着配置 20 个 MCP Server 对 token 消耗的影响，远小于在系统提示中列出 20 个工具的影响。

#### 安全最佳实践

1. **最小权限原则**：只连接当前任务需要的 MCP Server，任务结束后禁用
2. **密钥隔离**：`.mcp.json` 只存配置，密钥走环境变量，敏感文件加入 `.gitignore`
3. **权限三级审批**：系统提示预授权 → 会话级授权 → 永久授权，按需升级
4. **Token 轮换**：生产环境 API Token 每 90 天轮换一次
5. **只信任官方来源**：MCP Server 有代码执行能力，第三方 Server 需审查源码

### 3.3 Skills（技能文件）

- 实现**渐进式上下文披露**（Progressive Disclosure）
- Agent 只在需要时加载特定技能，其余时间不消耗 token
- 以 `SKILL.md` 文件格式定义，兼容 30+ AI 工具

### 3.4 Sub-Agents（子代理）

- 作为**上下文防火墙**（Context Firewall）隔离中间步骤
- 防止工具调用污染主会话上下文
- 支持分层模型策略（不同复杂度任务使用不同规格模型）

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

### 4.2 关键设计原则

**分层激活（Layered Activation）**：触发词 → 描述 → 完整指令 → 模板 → 参考资料，按需加载

**技能目录结构**：

```
skill-name/
├── SKILL.md          # 主指令文件（触发逻辑、执行步骤）
├── assets/           # 输出模板（Generator 模式用）
└── references/       # 背景知识（标准、检查清单、示例）
```

`description` 字段是技能的"语义索引"——写得越精确，Agent 激活越准确。

---

## 五、Google ADK 发布的 5 大技能设计模式

来自 [Lavi Nigam - Google ADK](https://lavinigam.com/posts/adk-skill-design-patterns/) 的权威研究，这 5 个模式是从 Anthropic、Vercel、Google 内部实践中归纳出的普适规律：

### Pattern 1: Tool Wrapper（工具封装）

**目的**：将特定库/框架的规范封装为按需知识

```
agent-name/
└── references/conventions.md   ← 只在实际用到该技术时加载
```

> 示例：让 Agent 成为 FastAPI 专家，只在编写/审查 FastAPI 代码时加载约定

**适用场景**：单一技术栈的专家知识下沉，最简单也最广泛使用。

---

### Pattern 2: Generator（生成器）

**目的**：用固定模板确保输出结构的一致性

```
agent-name/
├── assets/output-template.md   ← 填空模板
└── references/style-guide.md   ← 风格规范
```

> 技能充当"项目经理"：加载模板 → 读规范 → 向用户收集缺失变量 → 填充生成

**适用场景**：API 文档生成、提交信息标准化、项目架构脚手架。

---

### Pattern 3: Reviewer（审查者）

**目的**：将"检查什么"与"如何检查"分离

```
agent-name/
└── references/review-checklist.md   ← 可替换的检查维度
```

替换 Python 风格检查单 → OWASP 安全检查单，即得到完全不同的专业审查，基础设施不变。

**适用场景**：PR 自动审查、安全漏洞扫描、代码质量评估。

---

### Pattern 4: Inversion（倒置）

**目的**：Agent 先采访用户，再执行——翻转传统交互方向

核心是**强制门控（Hard Gate）**：

```
DO NOT start building until all phases are complete.
（在所有阶段完成之前，绝对不要开始构建）
```

分阶段提问 → 等待明确回答 → 再进入下一阶段 → 所有信息收集完毕才合成输出

**适用场景**：需求不明确的复杂任务、防止 Agent 基于假设行动。

---

### Pattern 5: Pipeline（流水线）

**目的**：多步骤任务的强制顺序执行与检查点机制

```
agent-name/
├── assets/                      ← 各阶段输出模板
├── references/quality-checklist.md
└── SKILL.md                     ← 定义步骤顺序和门控条件
```

可在末尾嵌入 Reviewer 步骤进行自检——这正是**模式组合**的体现。

**适用场景**：有严格先后依赖的复杂工作流。

---

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

**Initializer Agent（初始化代理）**：
- 首次运行时建立环境
- 创建 `init.sh`、进度追踪文件、初始 git commit
- 生成包含 200+ 功能的 JSON 特性清单（初始全部标记为 failing）

**Coding Agent（编码代理）**：
- 每次会话启动时：读取 git 历史 + 进度文件 + 运行基础功能测试
- 每次只处理一个功能，完成后 commit（带描述性信息）并更新进度文件
- 使用浏览器自动化工具（如 Puppeteer MCP）端到端验证

**效果**：Claude Opus 4.5 成功跨多个上下文窗口构建复杂 Web 应用。

---

## 七、实战案例：harness-engineering 项目深度解析

本地仓库 `harness-engineering` 是 Harness Engineering 实践的完整参考实现，将上述所有概念落地为产品研发工作流。

### 7.1 项目定位

将 AI Agent 的**技能化**（Skill-based）框架用于软件产品研发流程，核心命题：

> 用结构化技能定义替代脆弱的系统提示工程，让 AI 在复杂多轮工作流中可靠执行

### 7.2 技能体系

```
harness-engineering/
├── skills/
│   ├── install-skill/              # 技能安装工具
│   ├── prd-review/
│   │   ├── backend-prd-review/     # 后端工程师视角的 PRD 审查
│   │   ├── frontend-prd-review/    # 前端工程师视角的 PRD 审查
│   │   └── test-prd-review/        # QA 工程师视角的 PRD 审查
│   └── technical-solution/
│       └── backend-tech-design-mvc/ # MVC 架构后端技术设计生成
```

### 7.3 PRD 审查工作流（4 阶段）

所有审查技能均采用 **Inversion + Generator + Reviewer** 组合模式：

| 阶段 | 名称 | 核心动作 |
|------|------|----------|
| Phase 0 | 定向（Inversion） | 提 3 个范围界定问题，等待用户明确回答后才继续 |
| Phase 1 | 依赖检查 | 验证模板、标准、PRD 文件、原型、代码是否就位 |
| Phase 2 | 需求梳理 | 读取所有输入，生成带图表的综合摘要文档 |
| Phase 3 | 模板化审查 | 按维度检查清单（后端 9 维、前端 9 维、测试 6 维）分类问题 |
| Phase 4 | 自审循环 | 奥卡姆剃刀原则过滤，迭代至无遗漏 |

**审查维度（后端）**：

| 维度 | 说明 |
|------|------|
| DM | 数据模型 |
| API | 接口设计 |
| PF | 性能 |
| SC | 安全 |
| BL | 业务逻辑 |
| AM | 歧义识别 |
| CP | 完整性 |
| NF | 非功能需求 |
| SG | 建议 |

### 7.4 MVC 技术设计工作流（7 阶段）

采用 **Generator + Inversion** 模式，具备人工审查循环：

| 阶段 | 名称 | 核心动作 |
|------|------|----------|
| 1 | 模式检测 | 工作流模式 vs 独立模式，定位基线设计文档 |
| 2 | PRD 分析 | 获取 PRD，4 维度验证完整性 |
| 3 | 对比分析 | 映射 PRD 到现有设计，代码走查，标注 [新增]/[修改]/[删除] |
| 4 | 初始化生成 | 建立迭代目录，生成变更摘要、领域文档、API 文档、设计摘要 |
| 5 | AI 自检 | 7 维度审查（结构/规范/覆盖/一致性/映射/架构/AI 充分性） |
| 6 | 人工审查 | 展示设计摘要，收集 4 维度反馈（业务规则/API 契约/数据模型/并发），迭代修复 |
| 7 | 工作流集成 | 生成 manifest，更新工作流状态 |

### 7.5 双文档策略（Two-Document Strategy）

| 文档 | 受众 | 内容 |
|------|------|------|
| **设计摘要**（人读） | 产品/研发 | ≤2 屏，一句话背景 + 核心决策 + 变更范围 + 风险 + 分歧确认清单 |
| **AI 详设文档**（AI 读） | 下一轮 Agent | 完整技术规格、检查清单、数据模型、代码映射 |

这一策略直接解决了 Anthropic 提出的"跨会话记忆"问题——详设文档是 Agent 的"交班记录"。

---

## 八、量化效果

来自 [revfactory/harness](https://github.com/revfactory/harness) 的受控实验（15 个软件工程任务）：

| 指标 | 无 Harness | 有 Harness | 提升 |
|------|-----------|-----------|------|
| 平均质量分 | 49.5 | 79.3 | **+60%** |
| 胜率 | — | 15/15 | **100%** |
| 输出方差 | — | — | **-32%** |

> **任务越复杂，提升越显著。**

---

## 九、最佳实践总结

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

### 长任务原则

9. **双代理策略**：Initializer + Coding Agent 分离职责
10. **显式状态追踪**：`state.md` 是 Agent 的交班本，不依赖模型记忆
11. **端到端验证**：使用浏览器自动化，而非仅凭代码审查判断功能完成

---

## 十、生态系统概览

| 工具/资源 | 类型 | 说明 |
|-----------|------|------|
| [agentskills.io](https://agentskills.io) | 规范 | SKILL.md 格式规范，兼容 30+ AI 工具 |
| [build-with-adk](https://github.com/lavinigam-gcp/build-with-adk/tree/main/adk-skill-design-patterns) | 参考实现 | Google ADK 5 模式完整代码示例 |
| [revfactory/harness](https://github.com/revfactory/harness) | Meta-skill | 自动为项目生成 Agent 团队和技能文件 |
| [Anthropic Engineering Blog](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) | 权威文章 | 长时运行 Agent 的 Harness 策略 |
| [HumanLayer Blog](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents) | 实践总结 | 工程化配置方法论 |

---

## 十一、核心结论

Harness Engineering 代表了 AI Agent 工程从"试验性使用"走向"生产级可靠"的关键跨越：

1. **可靠性是系统属性**，而非模型属性
2. **结构化技能 > 自由式提示**：模式化设计让 AI 在复杂流程中可重复执行
3. **人机协作边界要清晰**：人做判断（Phase 0 定向、Phase 6 设计审查），AI 做执行
4. **渐进式上下文披露**是效率与质量的双赢策略
5. **Harness 是投资**：任务越复杂、越频繁，投资回报越高（+60% 质量提升有据可查）

---

## 参考资料

- [Skill Issue: Harness Engineering for Coding Agents | HumanLayer Blog](https://www.humanlayer.dev/blog/skill-issue-harness-engineering-for-coding-agents)
- [Harness Engineering: The Missing Layer Behind AI Agents | Louis Bouchard](https://www.louisbouchard.ai/harness-engineering/)
- [Effective Harnesses for Long-Running Agents | Anthropic Engineering](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [5 Agent Skill Design Patterns Every ADK Developer Should Know | Lavi Nigam](https://lavinigam.com/posts/adk-skill-design-patterns/)
- [5 Agent Skill Design Patterns | Google Cloud Tech](https://x.com/GoogleCloudTech/status/2033953579824758855)
- [build-with-adk reference implementation | GitHub](https://github.com/lavinigam-gcp/build-with-adk/tree/main/adk-skill-design-patterns)
- [revfactory/harness Meta-skill | GitHub](https://github.com/revfactory/harness)
- [What Is Harness Engineering? Complete Guide 2026 | NxCode](https://www.nxcode.io/resources/news/what-is-harness-engineering-complete-guide-2026)
