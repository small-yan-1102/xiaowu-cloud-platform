---
skill: test-case-design
based_on: harness@4.0.0
he_path: linscode/skills/iteration/testing/test-case-design
override_count: 2
last_updated: 2026-04-15
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

## 补充项

- 按需加载 `.claude/docs/ai_test_case_design.md` 作为设计规范补充
- 按需加载 `.claude/docs/smoke_test_design.md`（仅 Mode D）
