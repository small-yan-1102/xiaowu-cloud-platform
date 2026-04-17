---
skill: test-case-design
based_on: harness@4.0.0
he_path: linscode/skills/iteration/testing/test-case-design
override_count: 9
last_updated: 2026-04-16
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

## 补充项

- 按需加载 `.claude/docs/ai_test_case_design.md` 作为设计规范补充
- 按需加载 `.claude/docs/smoke_test_design.md`（仅 Mode D）
