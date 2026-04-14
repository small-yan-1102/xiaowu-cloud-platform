# 编排器启动 Sub-Agent 机制设计

> 2026-04-01 | 基于 Claude Code 官方文档 + iteration 项目实践

---

## 一、核心约束：Sub-Agent 无法再生子 Agent

官方文档明确：

> **"Subagents cannot spawn other subagents."**

这意味着：**编排器不能是一个 Sub-Agent**，它必须运行在**主会话（main conversation）**里。

```
主会话（orchestrator SKILL.md 在这里运行）
  ├── 读 state.md
  ├── 调用 Agent 工具 → 启动 backend-prd-review Sub-Agent（独立上下文）
  │     └── Sub-Agent 完成 → 返回结果给主会话
  ├── 更新 state.md
  ├── 调用 Agent 工具 → 启动 frontend-prd-review Sub-Agent
  └── ...
```

---

## 二、三种在 SKILL.md 里启动 Sub-Agent 的写法

### 写法一：自然语言指令（最简单）

在 SKILL.md 里直接写，Claude 自动根据 description 匹配调用哪个 Sub-Agent：

```markdown
## Phase 2：后端 PRD 审查

指令 Claude 执行：
使用 backend-prd-review sub-agent 对 [prd_path] 进行审查。
等待 sub-agent 完成后，将审查报告路径写入 state.md。
```

---

### 写法二：@-mention 强制指定（推荐，更精确）

```markdown
## Phase 2：后端 PRD 审查

使用 @agent-backend-prd-reviewer 对以下 PRD 进行审查：
- PRD 文件：读取 state.md 中的 prd_path 字段
- 输出报告路径写入：.qoder/workflow/outputs/backend-review-report.md
- 完成后在 state.md 中将 stage-2 状态更新为 completed
```

---

### 写法三：Sub-Agent 定义文件 + skills 预加载（最工程化）

**Step 1**：在 `.claude/agents/` 创建子 Agent 定义文件，把对应 SKILL.md 预注入：

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

**Step 2**：在编排器 SKILL.md 里引用：

```markdown
## Phase 2

启动 @agent-backend-prd-reviewer，传入以下上下文：
- 当前迭代: [从 state.md 读取]
- PRD 路径: [从 state.md 读取]
等待返回后继续 Phase 3。
```

> `skills` 字段的作用：Sub-Agent 启动时全量注入指定 SKILL.md 的内容，不需要 Sub-Agent 自己再去触发 skill——上下文直接就绪。

---

## 三、完整编排器 SKILL.md 骨架

```markdown
---
name: iteration-orchestrator
description: 迭代工作流编排器。统一管控 PRD 审查和技术设计的全流程。当需要启动或恢复迭代工作流时触发。
triggers:
  - /iteration-start
  - /iteration-resume
version: 1.0.0
---

# 迭代工作流编排器

## 启动逻辑

**第一步：读取状态**
读取 .qoder/workflow/state.md。
- 如果文件不存在 → 执行 [初始化流程]
- 如果 current_stage = "awaiting_approval" → 执行 [审批检查流程]
- 否则 → 执行 [恢复执行流程]

---

## 初始化流程

询问用户：
1. 迭代名称是什么？
2. PRD 文件路径在哪里？

收到回答后，创建 .qoder/workflow/state.md（使用 state 模板）。
将 current_stage 设为 "stage-2-backend-review"，进入 [执行流程]。

---

## 执行流程

读取 state.md 中的 current_stage，按以下顺序执行：

### stage-2-backend-review
使用 @agent-backend-prd-reviewer 执行后端 PRD 审查。
等待完成后：
- 将 stage-2 状态更新为 completed
- 将输出路径写入 state.md
- **需要人工审批** → 执行 [钉钉通知流程]，current_stage 设为 "awaiting_approval"，退出

### stage-3-frontend-review
（同上，使用 @agent-frontend-prd-reviewer）

### stage-4-test-review
（同上，使用 @agent-test-prd-reviewer）

### stage-5-tech-design
（同上，使用 @agent-backend-tech-designer）

---

## 钉钉通知流程

调用钉钉 MCP 工具 send_approval_request：
- title: "[迭代名称] [当前阶段] 完成，请审批"
- content: 包含报告文件路径和核心结论摘要
- approvers: 从 state.md 中读取 approvers 字段

将返回的 message_id 写入 state.md。
退出当前 session。

---

## 审批检查流程

调用钉钉 MCP 工具 check_approval_status，传入 state.md 中的 message_id。
- approved → 将 state.md 中 current_stage 推进到下一阶段，进入 [执行流程]
- rejected → 通知用户审批被拒，等待指示
- pending → 通知用户"审批尚未完成，请完成后再次运行 /iteration-resume"，退出
```

---

## 四、Sub-Agent 定义文件清单

按照写法三，需要在 `.claude/agents/` 下创建以下文件：

| 文件名 | 预注入 Skill | 职责 |
|--------|-------------|------|
| `backend-prd-reviewer.md` | `backend-prd-review` | 后端视角 PRD 审查 |
| `frontend-prd-reviewer.md` | `frontend-prd-review` | 前端视角 PRD 审查 |
| `test-prd-reviewer.md` | `test-prd-review` | 测试视角 PRD 审查 |
| `backend-tech-designer.md` | `backend-tech-design-mvc` | MVC 技术设计生成 |

每个文件的通用结构：

```markdown
---
name: <agent-name>
description: <精确描述，供编排器匹配>
tools: Read, Write, Bash, Glob, Grep
model: sonnet
skills:
  - <对应的 skill name>
memory: project
---

你是 [角色描述]。

启动时：
1. 读取 .qoder/workflow/state.md，获取 prd_path 和 iteration_name
2. 执行对应 skill 的完整工作流
3. 将输出文件路径写入 state.md 的对应阶段字段
4. 将阶段状态更新为 completed
```

---

## 五、state.md Schema 设计

编排器和所有 Sub-Agent 共享这个文件作为"交班记录"：

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
- type: in_progress
- stage: stage-2-backend-review
- message: backend-prd-reviewer sub-agent 执行中
```

审批等待时的状态：

```markdown
## 当前阻塞
- type: awaiting_approval
- stage: stage-2-backend-review
- message: 等待后端负责人审批 backend-prd-review 报告
- dingtalk_message_id: msg_xxxxxx
- output_file: .qoder/workflow/outputs/backend-review-report.md
```

---

## 六、推进顺序

```
Step 1  定义 state.md schema（本文档已给出草案）
   ↓
Step 2  创建 4 个 Sub-Agent 定义文件（.claude/agents/*.md）
   ↓
Step 3  编写编排器 SKILL.md（本文档骨架已给出）
   ↓
Step 4  单独测试每个 Sub-Agent（standalone mode）
   ↓
Step 5  测试编排器端到端串联（不含钉钉，人工确认代替）
   ↓
Step 6  实现钉钉 MCP Server（send + check 两个工具）
   ↓
Step 7  接入钉钉，测试完整 pause/resume 循环
   ↓
Step 8  打包 install-iteration-skill
```

---

## 七、关键约束速查

| 问题 | 答案 |
|------|------|
| 编排器能是 Sub-Agent 吗？ | **不能**，Sub-Agent 不能生子 Agent |
| 编排器在哪里运行？ | 主会话（main conversation），由 SKILL.md 驱动 |
| 怎么给子 Agent 注入 Skill？ | Sub-Agent 定义文件的 `skills` 字段，启动时全量注入 |
| 怎么跨 session 恢复？ | 依赖 `state.md`，新 session 触发 `/iteration-resume` → 编排器读 state → 继续 |
| 钉钉的 pause 怎么做？ | 发通知 → 写 state.md → 退出 session；审批后手动或 webhook 触发新 session |

---

## 参考资料

- [Create custom subagents | Claude Code Docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Customization: Skills, Subagents | alexop.dev](https://alexop.dev/posts/claude-code-customization-guide-claudemd-skills-subagents/)
- [Multi-agent orchestration for Claude Code | Shipyard](https://shipyard.build/blog/claude-code-multi-agent/)
