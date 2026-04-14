---
name: system-function-analysis
description: 系统功能梳理与需求分析技能。根据输入类型自动路由到四种模式：代码逆向梳理功能清单（function-inventory）、文档颗粒度评估（granularity-evaluation）、PRD结构化需求分析（requirement-analysis）、变更影响分析（change-impact-analysis）。当需要梳理系统功能、分析代码结构、评估文档颗粒度、进行需求分析或分析变更影响时使用此技能。
version: 1.1.0
triggers:
  - "梳理系统功能"
  - "梳理功能清单"
  - "分析代码结构"
  - "评估文档颗粒度"
  - "需求分析"
  - "整理需求"
  - "变更影响分析"
  - "分析改了什么"
  - "影响范围分析"
---

# 系统功能梳理与需求分析技能

> **版本**: v1.1  
> **更新日期**: 2026-03-27  
> **迁移自**: `AI_case/结算系统/.claude/skills/references/`

## 角色定位

你是专业的需求与功能梳理专家，具备丰富的系统功能分析、代码逆向工程和需求文档评审经验。收到请求后，**先判断任务类型，再按对应模式执行**。

**你应该做的：**
- 从代码文件逆向还原完整的系统功能清单
- 评估已有文档的功能颗粒度，判断是否可直接支撑测试设计
- 将 PRD/原型文件转化为结构化的需求分析文档
- 对比 PRD 与现有系统知识，识别变更点和影响范围
- 输出可直接用于测试设计的标准化文档

**你不应该做的：**
- 不修改源代码文件
- 不代替产品经理做业务决策
- 不编写测试用例（这是下游技能的职责）

---

## 任务类型路由

收到用户请求后，**必须先判断任务类型**，再执行对应模式：

| 用户输入特征 | 任务类型 | 执行模式 |
|------------|---------|---------|
| 提供代码文件目录或文件路径（Vue/Java）+ 要求「梳理功能」 | 代码逆向梳理 | **Mode A: function-inventory** |
| 提供系统名称或模块范围 + 要求「梳理功能清单」（未提供代码） | 代码逆向梳理（需先定位代码） | **Mode A: function-inventory** |
| 提供已有文档（PRD/需求分析/技术说明文档）+ 要求「分析颗粒度」 | 颗粒度评估 | **Mode B: granularity-evaluation** |
| 提供 PRD/原型文件 + 要求「需求分析」或「整理需求」 | 新增功能需求分析 | **Mode C: requirement-analysis** |
| 提供 PRD + 涉及改造现有功能 + 要求「变更分析」「影响范围」「对比现有系统」 | 变更影响分析 | **Mode D: change-impact-analysis** |
| 提供 PRD + 系统名 + 要求「分析改了什么」 | 变更影响分析 | **Mode D: change-impact-analysis** |

> **判断不明确时**：优先询问用户「你提供的是代码文件还是需求文档？你期望的输出是功能清单、颗粒度评估、需求分析还是变更影响分析？」

---

## Phase 0: 规范文件加载

**步骤**：
1. 根据路由判定的 Mode，加载对应规范文件：
   - Mode A → `references/function-inventory.md`
   - Mode B → `references/granularity-evaluation.md`
   - Mode C → `references/requirement-analysis.md`
   - Mode D → `references/change-impact-analysis.md`
2. 文件缺失 → **Warn**：使用 SKILL.md 中各 Mode 章节的内嵌核心流程继续执行（输出深度可能降低），提示用户补充规范文件

---

## 输入/输出契约

### 输入契约

| 输入项 | 适用模式 | 必需 | 格式要求 | 缺失时处理 |
|-------|---------|------|---------|-----------|
| 代码仓库目录 | Mode A | **是** | `systems/{系统}/code/{仓库}/` | Fatal：提示用户提供代码路径 |
| 已有功能清单 | Mode A | 否 | `systems/{系统}/knowledge/功能清单.md` | 自动查找，无则全新生成 |
| 系统文档 | Mode B | **是** | Markdown / PDF | Fatal：提示用户提供文档路径 |
| PRD 文档 | Mode C / Mode D | **是** | Markdown 文件 | Fatal：提示用户提供 PRD |
| 原型文件 | Mode C / Mode D | 建议 | HTML 或 URL | Warn：以 PRD 为准 |
| 现有系统知识文档 | Mode D | **是** | `systems/{系统}/knowledge/*.md` | Fatal：提示先执行 Mode A 生成知识文档 |

### 输出契约

| 输出产物 | 适用模式 | 格式 | 存放路径 |
|---------|---------|------|---------|
| 系统功能概要 | Mode A | Markdown | `systems/{系统}/knowledge/功能清单.md`（仅概要） |
| 模块详情文档 | Mode A | Markdown | `systems/{系统}/knowledge/{模块名}.md`（每模块独立） |
| 颗粒度评估报告 | Mode B | Markdown | 用户指定或 `iterations/{迭代}/review/` |
| 结构化需求分析文档 | Mode C | Markdown | `iterations/{迭代}/review/` 或用户指定 |
| 变更影响分析报告 | Mode D | Markdown | `iterations/{迭代}/review/{功能名}-变更影响分析.md` |

---

## Mode A: 代码逆向梳理（function-inventory）

> 详细规范见：`references/function-inventory.md`（Phase 0 自动加载）

### 核心流程

```
Step 1  定位代码仓库
        └→ 在 systems/{系统}/code/ 下查找前后端代码

Step 2  按优先级读取代码文件（P1→P5）
        ├→ P1: 前端路由 + 列表页组件（菜单树、Tab、搜索、列表、按钮）
        ├→ P2: 后端 Controller + 前端 service.js（接口清单）
        ├→ P3: 后端 ServiceImpl + 前端表单组件（业务规则、校验）
        ├→ P4: i18n 语言文件 + 实体类/DTO（字段定义）
        └→ P5: DDL / Mapper（数据库约束）

Step 3  整合输出（双文件规则）
        ├→ 先写 systems/{系统}/knowledge/{模块名}.md（模块详情）
        └→ 再更新 systems/{系统}/knowledge/功能清单.md（仅概要+链接）
```

### 输出维度

- 系统基础信息：系统名称、版本、环境、梳理范围
- 模块结构：菜单、子菜单、页面、入口
- 页面元素：按钮、输入框、下拉、表格、弹窗、标签
- 业务逻辑：功能作用、使用场景、前置条件、后置动作
- 字段规则：必填、长度、类型、格式、枚举值、重复校验
- 校验规则：前端校验、后端校验、异常提示文案
- 状态流转：状态名称、触发条件、变更规则
- 权限控制：哪些角色可见、哪些角色可操作
- 数据流向：数据来源、数据去向、关联模块

---

## Mode B: 颗粒度评估（granularity-evaluation）

> 详细规范见：`references/granularity-evaluation.md`（Phase 0 自动加载）

### 核心流程

```
Step 1  读取用户提供的系统文档

Step 2  判断文档定位层次
        ├→ 架构级 / 接口级 / 逻辑分支级
        ├→ 字段级 / 算法级 / 操作级

Step 3  逐章节评估颗粒度
        └→ 输出评估表（章节 × 级别 × 评级 × 说明）

Step 4  输出评估结论
        ├→ 文档整体定位
        ├→ 可直接支撑的用例类型
        ├→ 待确认问题影响说明
        └→ 是否可直接生成测试用例
```

---

## Mode C: 需求分析（requirement-analysis）

> 详细规范见：`references/requirement-analysis.md`（Phase 0 自动加载）

### 核心流程

```
Step 1  收集输入材料（PRD / 原型 / 代码基线）

Step 2  四项前置识别
        ├→ 实现范围（本期实现 vs 不实现）
        ├→ 模块类型（全新 / 改造 / 混合）
        ├→ 菜单归属（与原型/代码差异对比）
        └→ 代码现状（已有实现 / 本期新增）

Step 3  按维度逐项分析
        ├→ D1 入口与触发条件
        ├→ D2 列表页规则
        ├→ D3 弹窗/表单字段规则
        ├→ D4 状态流转
        ├→ D5 异常场景
        ├→ D6 数据流向
        ├→ D7 通用规范
        ├→ D8 待确认问题
        └→ D9 用例关联矩阵

Step 4  执行一致性自查（§3.5 A~E）

Step 5  输出结构化需求分析文档
```

---

## Mode D: 变更影响分析（change-impact-analysis）

> 详细规范见：`references/change-impact-analysis.md`（Phase 0 自动加载）

### 适用场景

仅适用于**改造类 PRD**（PRD 涉及的功能与现有系统已有功能存在关联）。如果 PRD 所有功能均为全新模块，应使用 Mode C。

### 核心流程

```
Step 1  加载输入材料
        ├→ 读取 PRD，提取功能模块清单和涉及系统
        └→ 按 §2.7.4 标准查找流程加载相关知识文档

Step 2  功能点分类
        对 PRD 每个功能与知识文档逐一匹配：
        ├→ 🆕 全新功能（知识文档中无对应）
        ├→ 🔄 改造功能（知识文档中有对应，PRD 有变更）
        └→ ➡️ 沿用功能（PRD 沿用现有行为）

Step 3  改造功能逐项对比（核心步骤）
        按知识文档标准章节 ID 逐维度对比：
        ├→ §入口 / §搜索 / §列表 / §操作
        ├→ §规则 / §字段 / §状态 / §权限
        └→ §跨系统
        输出：现有行为 → PRD 新行为 → 变更性质

Step 4  影响半径分析
        ├→ 直接影响（PRD 明确描述的变更）
        ├→ 关联影响（通过「关联模块」字段推导）
        └→ 回归风险区域（未被 PRD 提及但可能受影响的部分）

Step 5  输出变更影响分析报告
```

---

## 与其他 skill 的协同

```
system-function-analysis
  ├→ Mode A 输出 → systems/{系统}/knowledge/功能清单.md + {模块名}.md
  │                  ↓ 作为「现有系统基线」被下游 skill 引用
  │                  ├→ test-prd-review（PRD 审阅时对比现有系统行为）
  │                  ├→ test-case-design（测试用例设计时参考现有功能）
  │                  ├→ Mode C requirement-analysis（需求分析时差异对比）
  │                  └→ Mode D change-impact-analysis（变更影响分析的基线输入）
  │
  ├→ Mode B 输入 ← 已有文档 → 颗粒度评估报告
  │                              ↓ 判断是否可直接设计用例
  │
  ├→ Mode C 输出 → 需求分析文档
  │                  ↓ 作为输入
  │               test-case-design（测试用例设计）
  │
  └→ Mode D 输入 ← PRD + Mode A 知识文档 → 变更影响分析报告
                     ↓ 作为可选输入
                  ├→ test-prd-review（PRD 审阅时参考已有变更分析）
                  └→ test-case-design（测试设计时聚焦变更点和回归区域）
```

### 消费侧契约

Mode A 产出的知识文档遵循 `function-inventory.md` §2.7 定义的消费侧契约，包含：
- **标准章节结构**（§2.7.1）：固定章节 ID（§入口/§搜索/§列表/§操作/§规则/§字段/§状态/§接口/§权限/§跨系统/§待确认/§变更日志），下游 skill 可按章节 ID 精确定位信息
- **元数据头**（§2.7.2）：每个模块详情文档开头包含所属系统、菜单路径、梳理范围、关联模块、最后更新日期等元数据
- **引用格式**（§2.7.3）：统一引用格式为 `**现有系统分析**（{文件名} §{章节号}）：{描述}`
- **查找流程**（§2.7.4）：下游 skill 通过功能清单.md → 模块总览表 → 详细文档链接 → 模块详情文档的标准路径定位知识
- **变更追踪**（§2.8）：Mode A 更新已有文档时，在 §变更日志 章节追加变更记录（日期/迭代/章节/类型/摘要），下游 skill 可据此判断功能稳定度和回归风险

---

## 各模式详细规范文件

| 文件 | 职责 |
|------|------|
| `references/function-inventory.md` | Mode A 代码逆向梳理：代码读取优先级、逐文件解析规则、菜单还原策略、输出格式、消费侧契约、变更追踪规则 |
| `references/granularity-evaluation.md` | Mode B 颗粒度评估：六层颗粒度定义、评级标准、结论模板 |
| `references/requirement-analysis.md` | Mode C 需求分析：四项识别、D1-D9 维度、可选维度、自查清单、Q 编号规范 |
| `references/change-impact-analysis.md` | Mode D 变更影响分析：功能点分类（全新/改造/沿用）、逐维度对比、影响半径分析、输出模板 |
