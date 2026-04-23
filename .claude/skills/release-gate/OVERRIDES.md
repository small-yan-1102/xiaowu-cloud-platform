---
skill: release-gate
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/release-gate
override_count: 1
last_updated: 2026-04-23
---

# release-gate 项目定制

## 新增 1：质量判定规则引用（跨 skill 共享）

**HE 原文位置**：SKILL.md 中与质量阈值/通过率判定相关的任何段落
**定制为**：

本 skill 的**所有质量判定逻辑**（阈值表、通过率公式、模块风险等级、缺陷等级定义、覆盖状态规则等）**沿用**：

- **权威源**：[`.claude/skills/test-report/references/quality-rules.md`](../test-report/references/quality-rules.md)

**禁止**在本 skill 内独立定义阈值、公式、边界条件。若发现与 HE 原文不一致 → **以 `quality-rules.md` 为准**。

### 设计动机

- 避免 `test-report` / `release-gate` / `submission-gate` 三方规则漂移
- 单一事实来源，改阈值只改一处
- 配合 `verify_descriptions.py` 扫描机制定期自检

### 关键对齐项

| 判定 | 权威源章节 |
|---|---|
| 🟢/🟡/🔴 整体结论阈值 | quality-rules.md §一 |
| 三元通过率 | §二 |
| P0 / P0+P1 通过率 | §三 |
| 模块风险等级 | §四 |
| 需求覆盖状态 | §五 |
| 缺陷指标与等级定义 | §六 |
| 风险项识别 | §七 |
| 后续建议分支 | §八 |
