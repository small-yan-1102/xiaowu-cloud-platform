---
skill: test-execution
based_on: harness@2.0.0
he_path: linscode/skills/iteration/testing/test-execution
override_count: 1
last_updated: 2026-04-15
---

# test-execution 项目定制

## 覆盖 1：冒烟模式 Flaky 规则

**HE 原文位置**：Phase 2-S → 步骤 4（判定单条结论）→ 重试上限说明
**HE 原文摘要**：每条用例最多重试 1 次，不做 Flaky 判定，冒烟结论只有通过/失败两态
**定制为**：在重试上限说明后追加 Flaky 与冒烟关系的明确定义：
- 冒烟模式中即使重试后通过，也**不**记录为 Flaky（冒烟关注阻断性问题而非稳定性）
- 仅当用例在标准执行模式中出现重试才适用 Flaky 升级规则
- 冒烟中的失败**始终计入连续失败次数**，不因 Flaky 而豁免
