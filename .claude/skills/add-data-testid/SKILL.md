---
name: add-data-testid
description: 根据测试用例文档,在对应组件的 DOM 元素上添加 data-testid 属性。当用户说"添加 data-testid"、"按用例打标签"、"添加测试 ID"时使用。
version: 3.0.0
patterns:
  - Inversion（Phase 0 收集模块信息和用例文档路径）
  - Pipeline（Phase 1-4 严格顺序执行,映射确认后才执行修改）
triggers:
  - "添加 data-testid"
  - "按用例打标签"
  - "添加测试 ID"
  - "add-data-testid"
dependencies: []
---

# 添加 data-testid 技能

> **设计模式**：Inversion（收集信息）→ Pipeline（读取用例 → 分析文件 → 确认映射 → 添加属性），映射确认前不执行任何修改

## 输入/输出契约

### 输入
| 输入项 | 来源 | 缺失时处理 |
|-------|------|----------|
| 测试用例文档 | 用户指定路径 | Fatal：向用户索取 |
| 目标模块名称和编号 | 用户提供 | Fatal：向用户询问 |
| Vue 文件路径 | 用户指定或自动查找 | Warn：自动搜索相关组件 |

### 输出
| 输出产物 | 格式 |
|---------|------|
| 添加 data-testid 的 Vue 文件 | 修改后的 .vue 文件 |
| 映射关系清单 | 控制台输出(Phase 3 确认用) |

---

## 命名规范

参考 `references/naming-convention.md`

**格式**: `{模块编号}_{场景编号}_{序号}`

示例:
- `03_layout_01` (第三模块-布局-01)
- `03_S1-01_01` (第三模块-场景1-01-元素01)

---

## 核心工作流

```
Task Progress:
- [ ] Phase 0: 信息收集（Inversion）
- [ ] Phase 1: 读取用例文档
- [ ] Phase 2: 分析目标 Vue 文件
- [ ] Phase 3: 确定映射关系（需用户确认）
- [ ] Phase 4: 添加 data-testid
```

### Phase 0: 信息收集（Inversion 模式）

**⚠️ 硬门控：DO NOT proceed until all information is collected.**

使用 AskUserQuestion 收集：
- 目标模块名称和编号
- 用例文档路径
- 对应的 Vue 文件路径

---

### Phase 1: 读取用例文档

- 找出所有场景（Quest/Case），记录编号和对应操作
- 列出每个场景中需要打标签的 DOM 交互点：
  - 页面根容器
  - 按钮、输入框、弹窗触发点
  - 条件渲染的容器
  - 列表/表格行元素

**⚠️ 硬门控：DO NOT proceed to Phase 2 until:**
- [ ] 测试用例文档已读取
- [ ] 所有场景已提取
- [ ] DOM 交互点已识别

---

### Phase 2: 分析目标 Vue 文件

- 找到对应的 `.vue` 文件
- 识别与用例操作匹配的 DOM 元素
- 检查已有 `data-testid` 避免重复

**⚠️ 硬门控：DO NOT proceed to Phase 3 until:**
- [ ] Vue 文件已找到
- [ ] DOM 元素已识别
- [ ] 已有 data-testid 已检查

---

### Phase 3: 确定映射关系

**⚠️ 硬门控：DO NOT proceed to Phase 4 until user confirms the mapping.**

在执行修改前，列出完整映射清单：

```
页面根容器         → data-testid="XX_layout_01"
主要内容区         → data-testid="XX_layout_02"
场景 1 触发按钮    → data-testid="XX_S1-01_01"
场景 1 弹窗        → data-testid="XX_S1-01_02"
...
```

**必须先向用户展示映射清单并获得确认。**

---

### Phase 4: 添加 data-testid

按 `references/review-checklist.md` 检查清单逐项添加:

**添加规则**:
- **静态元素**：`data-testid="XX_layout_01"`
- **动态/条件渲染**：`:data-testid="condition ? 'XX_S1-01_01' : 'XX_S1-01_02'"`
- **v-for 列表**：不在循环项上加固定 testid，在容器上加
- **弹窗组件**：加在弹窗组件本身
- **不修改任何业务逻辑、class、样式**

---

## 约束

- 映射关系必须由用户确认后才执行修改
- 不修改任何业务逻辑、class 或样式代码
- 已存在的 `data-testid` 不覆盖,除非用户明确要求
- 所有命名必须符合 references/naming-convention.md 规范
- 必须按检查清单逐项检查(references/review-checklist.md)

## 附属资源文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 命名规范 | `references/naming-convention.md` | data-testid 命名规则 |
| 检查清单 | `references/review-checklist.md` | 添加检查清单 |
