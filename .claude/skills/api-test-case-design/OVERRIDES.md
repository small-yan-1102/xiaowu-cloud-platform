---
skill: api-test-case-design
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/api-test-case-design
override_count: 1
last_updated: 2026-04-15
---

# api-test-case-design 项目定制

## 新增 1：数据准备策略标注

**HE 原文位置**：Phase 3 → 用例设计 → 数据标记之前
**HE 原文摘要**：无数据准备策略标注规则
**定制为**：新增第 6 项「数据准备策略标注」：
- 需要特定状态数据的用例 → 标注 `[数据准备: API]`
- 有依赖链的用例 → 标注 `[数据准备: 依赖用例]` 并声明依赖编号
- 无需特殊数据 → 无需标注
