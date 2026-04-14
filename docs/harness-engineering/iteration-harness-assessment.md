# iteration 技能集 Harness Engineering 符合性评估

> 2026-04-01 | 基于 skills/iteration/ 全量文件分析

---

## 结论：高度符合，有 3 个关键缺口

---

## 一、已有部分：非常扎实

你的 4 个 Skills（backend-prd-review、frontend-prd-review、test-prd-review、backend-tech-design-mvc）是教科书级的 HE 实践：

| 评估维度 | 状态 | 说明 |
|---------|------|------|
| SKILL.md 格式规范 | ✅ | frontmatter 完整，description 精准 |
| 模式组合 | ✅ | Inversion(P0) + Generator(P3) + Reviewer(P4) 三模式叠加 |
| 强制门控 | ✅ | 每个关键节点都有 🔵 用户确认，拒绝跳过 |
| 渐进式披露 | ✅ | assets/ + references/ 按需加载，不预注入 |
| 双文档策略 | ✅ | 设计摘要（人读）+ AI 详设（AI 读）清晰分离 |
| 回压机制 | ✅ | 自审循环 + 奥卡姆剃刀过滤 |
| 模式感知 | ✅ | workflow mode / standalone mode 均已处理 |

---

## 二、缺口 1：跨会话状态管理（最核心的缺失）

你提到"用一个整体控制这些 skills 工作"，但目前项目里**没有 `state.md`**。

这是 HE 最强调的一点（Anthropic 原话是"轮班工程师交班记录"）。你的编排器 skill 在执行过程中，中途停止、钉钉通知、等待人工确认……然后新 session 启动——**新 session 对之前发生的一切一无所知**。

没有显式状态文件，编排器无法回答：

- 现在在哪个阶段？
- 哪些 skill 已完成？输出文件在哪？
- 是等待人工确认中，还是可以继续？
- 上一次人工确认的结论是什么？

### state.md 设计草案

```markdown
# 迭代工作流状态

## 基本信息
- 迭代名称: xxx
- PRD 文件: .qoder/workflow/input/prd.md
- 当前阶段: stage-2-backend-review
- 最后更新: 2026-04-01 14:30

## 阶段状态
| 阶段 | 状态 | 输出文件 | 人工审批 | 审批时间 |
|------|------|---------|---------|---------|
| stage-1-prd-input      | ✅ completed  | -                           | 不需要   | -                   |
| stage-2-backend-review | 🔄 in_progress | -                          | 待审批   | -                   |
| stage-3-frontend-review| ⏸ pending     | -                           | -        | -                   |
| stage-4-test-review    | ⏸ pending     | -                           | -        | -                   |
| stage-5-tech-design    | ⏸ pending     | -                           | -        | -                   |

## 当前阻塞
- 类型: awaiting_human_approval
- 说明: backend-prd-review 完成，等待后端负责人确认审查报告
- 钉钉消息 ID: xxxx
```

---

## 三、缺口 2：钉钉通知的技术接入点

概念上完全正确——HE 强调"人做判断，AI 做执行"，钉钉是人机交互的界面。但实现上有一个根本性挑战：

> Claude Code 是基于 session 的。你不能在一个 session 里"暂停等待钉钉回复"。

### 三种接入方案对比

| 方案 | 机制 | 复杂度 | 适合场景 |
|------|------|--------|---------|
| **Hook + 手动触发** | skill 完成 → Hook 脚本发钉钉 → 人确认后手动启动下一 session | 低 | 低频，人工介入多 |
| **MCP Server（推荐）** | 钉钉 MCP Server → skill 直接调用发消息/读回复 → state.md 记录审批 → 编排器自动判断 | 中 | 中频，半自动 |
| **Remote Trigger** | 钉钉 Webhook → 写 state.md → 触发新的 Claude Agent session 自动继续 | 高 | 高频，全自动 |

### 推荐方案：MCP Server

建议从 MCP Server 方案切入，只需暴露两个工具：

```typescript
// 钉钉 MCP Server（约 50 行）
tools: [
  {
    name: "send_approval_request",
    description: "发送钉钉审批通知，返回消息 ID",
    inputSchema: {
      title: string,      // 审批标题
      content: string,    // 审批内容（附报告链接）
      approvers: string[] // 审批人列表
    }
  },
  {
    name: "check_approval_status",
    description: "查询钉钉消息的审批状态",
    inputSchema: {
      message_id: string  // send_approval_request 返回的消息 ID
    }
    // 返回: approved | rejected | pending
  }
]
```

编排器在需要人工审批时调用 `send_approval_request`，将 message_id 写入 state.md，退出 session。新 session 启动后，编排器读 state.md，调用 `check_approval_status`，根据结果决定继续还是中止。

---

## 四、缺口 3：编排器的上下文隔离

如果在同一个 session 里顺序调用 4 个 skill，**上下文窗口会撑爆**。每个 skill 执行时会大量读文件、生成文档，4 个 skill 跑完大约消耗 4 倍正常用量的 token。

HE 的正确姿势：**编排器不内联执行子 skill，而是启动 Sub-Agent**。

```
编排器 Orchestrator
  ├── 读 state.md，判断当前阶段
  ├── 启动 Sub-Agent → backend-prd-review（独立上下文，不污染主 session）
  ├── Sub-Agent 完成 → 写输出文件 → 更新 state.md → 退出
  ├── 编排器读 state.md，判断是否需要钉钉通知
  ├── 调用钉钉 MCP → 发送审批请求 → 写 message_id 到 state.md → 退出 session
  └── 人工审批后 → 新 session 启动编排器 → 读 state.md → 继续下一阶段
```

每个子 skill 有干净的上下文窗口，互不污染，也便于单独调试。

---

## 五、推进路线图

### Phase 1 — 设计状态协议（最优先）

设计 `workflow/state.md` 的完整 schema。这是其他所有东西的基础——编排器依赖它判断阶段，钉钉集成依赖它存储审批状态，新 session 依赖它恢复进度。

**产出**：`state.md` schema 文档 + 阶段枚举定义

### Phase 2 — 构建编排器 SKILL.md

用 **Pipeline 模式** 编写编排器，核心逻辑：

1. 读 `state.md`，判断当前阶段和阻塞类型
2. 如果 `awaiting_human_approval`，调用钉钉 MCP 检查审批结果
3. 如有阶段 `in_progress`，恢复执行或启动对应 Sub-Agent
4. Sub-Agent 完成 → 更新 `state.md` → 判断下一步
5. 需要人工审批时，发钉钉通知 → 写 state.md → 退出 session

**产出**：`skills/iteration/orchestrator/SKILL.md`

### Phase 3 — 接入钉钉 MCP

实现钉钉 MCP Server，暴露 `send_approval_request` 和 `check_approval_status` 两个工具，在 `.mcp.json` 中注册。

**产出**：`tools/dingtalk-mcp/` + `.mcp.json` 配置

### Phase 4 — 打包 install-skill

参考现有 `install-skill` 模式，把 iteration 整套技能（含编排器 + 钉钉 MCP 配置）做成可安装的包，面向其他项目复用。

**产出**：`skills/install-iteration-skill/SKILL.md`

---

## 六、一句话总结

你的架构方向完全正确，单个 skill 的质量已经很高。现在缺的不是更多 skill，而是**把这些 skill 串联起来的基础设施**：

> **状态协议（state.md schema）→ 编排器（orchestrator SKILL.md）→ 钉钉接入（MCP Server）**

先把 state.md 设计清楚，后面的东西就都顺了。
