---
skill: test-case-design
based_on: harness@4.0.0
he_path: linscode/skills/iteration/testing/test-case-design
override_count: 10
last_updated: 2026-04-17
---

# test-case-design 项目定制

## 覆盖 1：Phase 1 test-points.md 旧版本处理

**HE 原文位置**：Phase 1 → Mode A → 检查测试点清单 → 第 4 种情况（存在但无可执行性标签）
**HE 原文摘要**：默认全部视为 `[AI]`，在 Phase 5 输出摘要中注明
**定制为**：**Warn** 交互确认——向用户提示「test-points.md 缺少可执行性标签，建议先重新执行 test-point-extraction。是否继续？」用户确认继续则默认全部视为 `[AI]`；用户拒绝则终止。

## 覆盖 2：第一轮模块排序 Mode B

**HE 原文位置**：生成顺序规则 → 第一轮：模块排序
**HE 原文摘要**：Mode B 按审阅报告风险等级排序（单行描述）
**定制为**：按模式分支的决策树：
```
Mode B（补充风险场景）：
  1. 先按审阅报告风险等级排序（🔴 模块 > 🟡 模块 > 🟢 模块）
  2. 同等级内仍遵守模块依赖顺序（基础模块先于业务模块）
```

## 覆盖 3：Phase 5 输出路径

**HE 原文位置**：Phase 5 → 确定输出路径和文件名
**HE 原文摘要**：所有模式输出到 `test_suites/` 目录
**定制为**：输出到 `testcase/` 目录（与项目已有迭代保持一致）

| 模式 | HE 默认路径 | 本项目路径 |
|------|-----------|-----------|
| Mode A | `test_suites/suite_{模块名}.md` | `testcase/suite_{模块名}.md` |
| Mode B | `test_suites/suite_{模块名}_supplement.md` | `testcase/suite_{模块名}_supplement.md` |
| Mode C | `test_suites/suite_prod_regression.md` | `testcase/suite_prod_regression.md` |
| Mode D | `test_suites/suite_smoke.md` | `testcase/suite_smoke.md` |

测试数据配置文件输出到 `testcase/data/`。

## 覆盖 4：Phase 3 Mode D `[冒烟: API]` 用例生成委托

**HE 原文位置**：Phase 3 → Step A → Mode D 专项生成规则
**HE 原文摘要**：所有冒烟用例使用模板五生成
**定制为**：遇到 `[冒烟: API]` 类型的用例时，**必须**暂停 test-case-design 的 Phase 3 循环，使用 Skill 工具调用 `/api-test-case-design` 生成该用例。生成完成后将用例按 api-test-case-design 格式**内嵌在 `testcase/suite_smoke.md` 对应位置**（与 browser-use 用例并列排序），继续下一个模块。**禁止**使用模板五手写 API 用例。

## 覆盖 5：Phase 6 自检 `[冒烟: API]` 格式检查

**HE 原文位置**：Phase 6 → 模式专项 → Mode D
**HE 原文摘要**：无 `[冒烟: API]` 格式检查项
**定制为**：Phase 6 自检新增硬性检查项：
```
☐ [冒烟: API] 用例已通过 `/api-test-case-design` Skill 生成（非模板五手写）
☐ [冒烟: API] 用例格式包含 HTTP Method / URL / Headers / Request Body / Expected Response
☐ [冒烟: API] 用例内嵌在 suite_smoke.md 中（与 browser-use 用例同文件），头部标注 **执行方式**：[冒烟: API]
```
任一项不通过 → Phase 6 自检标记为失败，必须返回 Phase 3 重新生成。

## 覆盖 6：Phase 0 样例扫描链优先级 5 路径

**HE 原文位置**：Phase 0 → 测试思路样例扫描 → 优先级 5
**HE 原文摘要**：`test_suites/suite_*.md` 中同模块已有用例
**定制为**：路径改为 `testcase/suite_*.md`，与覆盖 3 的输出路径保持一致。

## 新增 7：Phase 0 必问用例适用对象

**HE 原文位置**：Phase 0 → 问题列表（4 个问题）
**HE 原文摘要**：Phase 0 问测试范围、优先级、模式、业务约束，不问执行对象。Phase 1 读 test-points.md 标签自动判定
**定制为**：Phase 0 的 4 个问题之后，**必须**追加第 5 个问题：

> **5. 用例适用对象**：生成的用例由谁执行？
>    - 全部 `[AI]`：AI 自动执行（browser-use / api-test-execution 直接跑）
>    - 全部 `[人工]`：人工执行（测试工程师按菜谱操作）
>    - 混合：我来指定哪些 AI、哪些人工
>    - 按默认：读取 test-points.md 标签自动判定

⛔ **DO NOT** 跳过此问题。用户回答是最终标准，test-points.md 标签仅在用户选"按默认"时作为兜底。

用户回答后记录到定向上下文，Phase 3 生成时按标签决定写法：
- `[AI]`：全自动格式（精确步骤 + 精确断言 + 清理步骤）
- `[AI+人工]`：自动格式 + 人工介入点标注 `⚠️ [人工介入]`
- `[人工]`：人工可读菜谱格式（逐步操作 + 逐条预期，颗粒度与 `[AI]` 一致，不含机器执行细节）

## 新增 8：Phase 3 Step A/B 人工执行颗粒度标准

**HE 原文位置**：Phase 3 → Step A 生成 + Step B 审查
**HE 原文摘要**：无用例颗粒度标准定义
**定制为**：Phase 0 选择"人工执行"或"混合"格式时，Phase 3 **必须**加载 `.claude/skills/test-case-design/references/granularity-standard.md`：
- Step A 生成时：按 R1~R14 硬规则判断是否拆分，按 S1~S10 软指标控制粒度
- Step B 审查时：逐条执行"失败归因测试"（S4），不通过则按硬规则拆分

> ⚠️ 规则版本同步：本覆盖项引用的规则编号须与 `granularity-standard.md` 当前版本（v4.0）保持一致。granularity-standard.md 升级时同步更新此处。

## 新增 9：Mode F 颗粒度优化模式

**HE 原文位置**：模式路由表（5 种模式）
**HE 原文摘要**：Mode A~E，无颗粒度优化模式
**定制为**：新增 Mode F，对已有用例执行颗粒度审查与优化。

**触发词**："优化用例颗粒度" / "调整用例粒度" / "用例太粗/太细" / "按颗粒度标准重构" / "颗粒度优化"

**Phase 0**：
1. 确认待优化的用例文件路径（默认扫描 `testcase/suite_*.md`）
2. 确认优化范围（全量 or 指定模块）

**Phase 1**：加载待优化用例 + `references/granularity-standard.md` + `references/granularity-review.md`

**Phase 2**：逐条扫描，按 `granularity-review.md` §2 流程标记过粗/过细/合理

**Phase 3**：输出审查报告（颗粒度评分 + 过粗/过细统计 + 逐条建议）→ 用户确认优化方案

**Phase 4**：执行拆分/合并 → 覆盖度守恒检查 → 输出优化后用例文件 + 变更摘要

**输出路径**：原文件覆盖写入（优化前自动备份为 `{原文件名}.bak.md`）

**关键规范文件**：
- 拆分规则：`references/granularity-standard.md` R1~R14（硬规则） + S1~S10（软指标）
- 合并触发器：`references/granularity-review.md` M1~M5
- 评分表：`references/granularity-review.md` §5
- 覆盖度守恒检查：`references/granularity-review.md` Phase 5

## 新增 10：套件「执行清单」段作为唯一状态记录入口

**HE 原文位置**：Phase 3 Step A 生成套件首部 → 执行顺序表结构 / 套件末尾章节
**HE 原文摘要**：执行顺序表只含用例元数据（序号/编号/名称/优先级/依赖等），无执行进度字段；套件末尾为统计摘要和人工校验提示，无面向执行阶段的状态入口
**定制为**：所有套件（`suite_*.md` / `api_suite_*.md`）**必须**：
1. 执行顺序表**不得**包含「执行记录」列（状态不进表格）
2. 在**执行顺序表之后、首个用例分节之前**插入一段 `## 执行清单（状态记录入口）`，作为**人工 + AI 共享的唯一状态记录位置**

### 设计动机

- VSCode 原生支持 Markdown 任务列表 `- [ ]` 的鼠标点击切换，**不支持**表格内 checkbox
- 单源原则：状态只在一处记录，避免表格列与清单段不同步
- 真源分工：清单段 = 进度快照（扫一眼知道哪些过了）；`execution/execution_report_*.md` = 审计证据（失败时查原因）

### 段落骨架（必填）

```markdown
---

## 执行清单（状态记录入口）

> **操作说明**：
> - **人工**：鼠标点击 `- [ ]` 切换为 `- [x]` 表示**执行通过**；失败/阻塞/跳过**不勾选**，行尾追加 ` · ❌ BUG-{id}` / ` · 🚫 {原因}` / ` · ⏭ {原因}`
> - **AI（test-execution / api-test-execution）**：执行完成后自动勾选并追加 ` · ✅ AI {日期} · [报告](...)` 或 ` · ❌ AI {日期} · [失败详情](...)`
> - **真源定位**：本清单为**进度真源**；完整执行证据（步骤/断言/截图/堆栈）在 `execution/execution_report_*.md`

{分组勾选列表}

**暂缓**：{已删除/合并/暂缓用例一句话列出（可选）}
```

### 分组规则

1. **套件包含阶段/①②③分节** → 按阶段分组，每组一个小标题（如 `**① 权限与入口**：`），组内按执行顺序列出
2. **套件仅有 P0/P1 分类** → 按优先级分组（`**P0**：` / `**P1**：`）
3. **套件扁平无分组** → 直接一串列表，不分组（如冒烟套件）

### 行格式（每条用例一行）

**默认（未执行）**：
```
- [ ] **{用例编号}** {用例名称}（{优先级 · 可选人工标注}）
```

**人工执行后示例**：
```
- [x] **SMOKE-001** 导入无归属视频（P0）                    ← 通过（点一下）
- [ ] **SMOKE-002** 批量拆分（P0） · ❌ BUG-123             ← 失败
- [ ] **SMOKE-003** MQ 同步（P0） · 🚫 前置数据缺失          ← 阻塞
- [ ] **SMOKE-004** 跨期拆分（P0） · ⏭ 本轮不测              ← 跳过
```

**AI 执行后示例**（由 test-execution / api-test-execution 回写）：
```
- [x] **SMOKE-001** 导入无归属视频（P0） · ✅ AI 2026-04-17 · [报告](execution/execution_report_20260417.md#smoke-001)
- [ ] **SMOKE-002** 批量拆分（P0） · ❌ AI 2026-04-17 · [失败详情](execution/execution_report_20260417.md#smoke-002)
- [ ] **SMOKE-003** MQ 同步（P0） · 🚫 AI · 前置数据缺失
```

### 硬性约束

1. **执行顺序表不得含「执行记录」列**——状态唯一入口是本清单段
2. Phase 3 新生成的套件，所有用例行默认为**未勾选** `- [ ]`
3. 不得使用 Unicode checkbox（`☐/☑/■/□`）代替 `- [ ]`——那些不可鼠标切换
4. 本段**不得嵌入表格内**——表格单元格 checkbox VSCode 无法点击
5. 用例编号加粗（`**{编号}**`），便于视觉扫描
6. 暂缓用例**不出现**在勾选列表，另列于 `**暂缓**：` 行内以 `~~strikethrough~~` 标注
7. Phase 6 自检硬性检查项：
   ```
   ☐ 执行顺序表最右列不是「执行记录」（已废除）
   ☐ 套件存在 `## 执行清单（状态记录入口）` 段，位于执行顺序表之后、首个用例分节之前
   ☐ 段首含标准操作说明块（人工 / AI / 真源定位三条）
   ☐ 每条可执行用例均有 `- [ ] **编号** 名称（P?）` 形式的行
   ☐ 勾选行数量 = 执行顺序表中非暂缓用例数量
   ☐ 暂缓/跳过用例不出现在勾选列表（仅在 `**暂缓**：` 行列出）
   ```

### 与执行回写的衔接

- 本覆盖项约束**生成阶段**的格式（默认全部 `- [ ]`）
- 执行阶段的回写逻辑由 `test-execution` / `api-test-execution` OVERRIDES 定义（见各自覆盖 2）
- 回写目标：**本清单段对应行**（勾选 + 行尾追加 AI 标记 + 报告链接）
- 审计证据：`execution/execution_report_*.md` 为**真源**（失败详情/截图/步骤明细），本清单是进度索引
- 冲突处理：以 `execution_report` 为最终事实；清单段被人工与 AI 共同维护，按最后修改者为准

### 人工填写便利性

- 通过 → 鼠标点一下 `- [ ]`（零输入）
- 失败/阻塞/跳过 → 行尾手写或用 `/mark-case` 让 AI 代填

## 补充项

- 按需加载 `.claude/docs/ai_test_case_design.md` 作为设计规范补充
- 按需加载 `.claude/docs/smoke_test_design.md`（仅 Mode D）
