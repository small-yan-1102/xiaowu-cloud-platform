# 研究报告：Google《5 Agent Skill Design Patterns》深度解析

**研究日期：** 2026-04-01
**原文作者：** Google Cloud Tech / Lavi Nigam
**发布时间：** 2026-03-17

---

## 一、背景与动机

随着 Google ADK（Agent Development Kit）的普及，`SKILL.md` 成为跨工具定义 Agent 能力的标准格式，已有 **30+ 个 Agent 工具**（Claude Code、Gemini CLI、Cursor 等）采用同一规范。

格式问题已基本解决，开发者真正面临的挑战转向了**内容设计**：如何让 Skill 在多轮对话中稳定执行？如何防止 Agent 跳步、假设、输出结构不一致？

通过研究跨生态（Anthropic、Vercel、Google 内部）的 Skill 构建方式，Google 提炼出了 **5 个反复出现的设计模式**。

---

## 二、SKILL.md 基本结构

每个 Skill 包含：

```
skill-name/
├── SKILL.md          # 主指令文件（触发词、描述、执行逻辑）
├── assets/           # 输出模板（如文档模板、脚手架）
└── references/       # 背景知识（如检查清单、规范文档、风格指南）
```

`SKILL.md` 的 `description` 字段充当**语义搜索索引**——必须包含精确的关键词，Agent 才能在正确时机激活该 Skill。

---

## 三、五大设计模式详解

### 模式一：Tool Wrapper（工具包装器）

**核心思想：** 将某个库/框架的使用规范打包成按需加载的专家知识，而非硬编码进系统提示词。

**目录结构：**

```
skill/
├── SKILL.md          # 监听特定库关键词，加载 references/
└── references/
    └── conventions.md  # 该库的最佳实践、规范
```

**工作机制：**

- Agent 只在用到该技术时加载上下文（节省 Token）
- `references/` 文档被视为绝对权威
- 典型用于：FastAPI 规范、Terraform 模式、安全策略、数据库查询优化

**适用场景：** 将团队内部编码规范直接注入开发者工作流

---

### 模式二：Generator（文档生成器）

**核心思想：** 用"填空"代替"自由发挥"，通过模板强制输出结构一致性。

**目录结构：**

```
skill/
├── SKILL.md          # 编排加载逻辑，逐节填充
├── assets/
│   └── template.md   # 输出模板（含占位符）
└── references/
    └── style-guide.md  # 风格/质量规范
```

**工作机制：**

1. 加载模板确定结构
2. 加载风格指南确定质量标准
3. 向用户询问缺失变量
4. 逐节填充，而非整体生成

**优势：** 替换模板或风格指南即可改变输出，无需修改指令逻辑

**适用场景：** 技术报告、API 文档、Commit 消息规范、项目脚手架

---

### 模式三：Reviewer（评审器）

**核心思想：** 将"检查什么"（检查清单）与"如何检查"（评审协议）分离，使评审逻辑模块化。

**目录结构：**

```
skill/
├── SKILL.md           # 加载清单，按严重等级输出报告
└── references/
    └── review-checklist.md  # 评审标准（含 error/warning/info 分级）
```

**工作机制：**

- Agent 加载清单后逐项打分
- 按严重等级（critical / warning / info）分组输出
- 换清单 = 换专业领域（Python 风格检查 → OWASP 安全审计），基础设施不变

**适用场景：** PR 自动评审、安全漏洞检测、编辑规范校验

---

### 模式四：Inversion（反转模式）

**核心思想：** 翻转交互方向——Agent 先提问收集需求，禁止在信息完整前开始执行。

**目录结构：**

```
skill/
├── SKILL.md          # 定义问题阶段 + 硬性门控指令
└── assets/
    └── synthesis-template.md  # 信息收集完毕后的综合模板
```

**核心机制：门控指令（Gate Condition）**

> "DO NOT start building or designing until all phases are complete."

没有这个硬性门控，Agent 会提前开始生成。这是该模式能否奏效的关键。

**工作流：**

1. 阶段一：收集基础需求
2. 阶段二：深化约束条件
3. 阶段三：确认边界情况
4. 门控通过后：加载模板，综合输出

**适用场景：** 项目规划、诊断排查面试、部署配置向导、ADK Agent 设计

---

### 模式五：Pipeline（流水线）

**核心思想：** 将复杂工作流拆解为带检查点的严格顺序步骤，每步都有明确的进入/退出条件。

**目录结构：**

```
skill/
├── SKILL.md          # 定义步骤序列 + 钻石门控条件
├── assets/           # 各步骤输出模板
└── references/       # 各步骤参考文档
```

**核心机制：钻石门控（Diamond Gate）**

> "DO NOT proceed to Step 3 until user confirms Step 2 output."

每个阶段按需加载资源，保持 context window 清洁。

**适用场景：** 文档生成流水线（解析→生成→组装→质检）、带人工确认的部署流程

---

## 四、模式对比与选型指南

| 模式 | 核心价值 | 复杂度 | 目录使用 | 最适合 |
|------|----------|--------|----------|--------|
| Tool Wrapper | 按需专家知识 | 低 | references/ | 库/框架规范 |
| Generator | 结构一致性 | 中 | assets/ + references/ | 固定格式文档 |
| Reviewer | 标准化评审 | 中 | references/ | 质量检查/审计 |
| Inversion | 需求完整性 | 中（多轮） | assets/ | 先收集后执行 |
| Pipeline | 流程可靠性 | 高 | 全部 | 多步骤工作流 |

---

## 五、模式组合（Composition）

这五种模式**并非互斥**，生产系统通常组合 2-3 个：

```
Inversion → Generator → Reviewer  （内嵌于 Pipeline 框架）
     ↓            ↓           ↓
  收集需求    填充模板    质量把关
```

典型组合：

- **Pipeline + Reviewer**：流水线最后一步自动质检
- **Inversion + Generator**：先收集变量，再填充模板
- **Tool Wrapper + Reviewer**：特定技术栈的代码评审

---

## 六、批判性分析：设计与实现之间的差距

基于 [jimo.studio 的深度分析](https://jimo.studio/blog/deep-dive-into-five-agent-skill-design-patterns-of-google-adk/)，ADK 底层实现并不像设计文档那样强健：

| 模式 | 实现完整度 | 主要问题 |
|------|-----------|----------|
| Tool Wrapper | ★★★★★ | 最完整，`LoadSkillResourceTool` 原生支持 |
| Generator | ★★★☆☆ | 无模板完整性验证，依赖 LLM 遵守指令 |
| Reviewer | ★★★☆☆ | 底层代码与 Tool Wrapper 相同，纯提示词差异 |
| Inversion | ★★☆☆☆ | **框架无阶段状态管理**，5-10 轮后门控失效 |
| Pipeline | ★☆☆☆☆ | **最弱实现**，无检查点机制/步骤状态机 |

**核心设计理念：**

> "ADK Skill 定义知识，ADK Agent 编排流程"

这是刻意的职责分离，但对于 Inversion 和 Pipeline 这类依赖状态管理的模式，需要额外工程补强：

- **Inversion 加固：** 使用 `before_tool_callback` + `tool_context.state` 实现显式状态机
- **Pipeline 加固：** 采用 `SequentialAgent + require_confirmation` 或集成 LangGraph
- **Generator/Reviewer 加固：** 添加 Pydantic 输出结构验证

---

## 七、关键洞察与实践建议

### 1. `description` 字段是激活的关键

模糊描述导致 Skill 无法在正确时机触发。**具体关键词 > 通用描述**。

### 2. 渐进式披露节省 Token

- L1：仅名称 + 描述（~100 tokens）
- L2：完整指令（按需加载）
- L3：references/ 资源（仅在需要时加载）

### 3. 门控指令必须使用强制语气

`"DO NOT proceed until..."` 远比 `"Please wait until..."` 可靠。

### 4. 单一模式 vs 组合模式的选择

- 简单任务：单一模式
- 生产系统：通常需要 2-3 个模式组合

### 5. 模式本身不是终点

正如 [Zenn 的对比文章](https://zenn.dev/shio_shoppaize/articles/shogun-skill-patterns-google?locale=en)指出：Google 的分类基于"让 AI 做什么"，而非"技能结构是什么"。在实际设计中，理解**结构**往往比记住模式名称更重要。

---

## 八、总结

Google 的五大 Agent Skill 设计模式为 AI 工程师提供了一套清晰的**思维框架**，解决了 Agent 开发中最常见的失败模式：

| 失败模式 | 对应解法 |
|----------|----------|
| 输出结构每次不同 | Generator |
| Agent 跳过关键步骤 | Pipeline / Inversion |
| Context 充满无关信息 | Tool Wrapper（按需加载） |
| 复杂工作流无法维护 | Pipeline（步骤拆解） |
| 评审标准不一致 | Reviewer（清单驱动） |

这些模式的本质是：**用结构化的 SKILL.md 设计替代脆弱的系统提示词工程**。

---

## 参考来源

- [5 Agent Skill Design Patterns Every ADK Developer Should Know — Lavi Nigam](https://lavinigam.com/posts/adk-skill-design-patterns/)
- [Google Cloud Tech 官方推文](https://x.com/GoogleCloudTech/status/2033953579824758855)
- [5 Agent Skill Design Patterns — tool.lu 镜像](https://tool.lu/en_US/article/7JA/preview)
- [深度解析 Google ADK 的 5 类 Agent Skill 设计模式 — jimo.studio](https://jimo.studio/blog/deep-dive-into-five-agent-skill-design-patterns-of-google-adk/)
- [Google ADK Agent Skill 5 大设计模式 — ofox.ai](https://ofox.ai/zh/blog/google-adk-agent-skill-design-patterns-2026/)
- [与 Google 5 SKILL.md 模式的对比分析 — Zenn](https://zenn.dev/shio_shoppaize/articles/shogun-skill-patterns-google?locale=en)
