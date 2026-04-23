---
skill: submission-gate
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/submission-gate
override_count: 1
last_updated: 2026-04-23
---

# submission-gate 项目定制

## 新增 1：质量判定规则引用（跨 skill 共享）

**HE 原文位置**：SKILL.md 中涉及覆盖率阈值、通过率判定、缺陷等级等质量相关段落
**定制为**：

本 skill 的**质量判定逻辑**（分支覆盖率阈值、P0 门禁、缺陷等级定义等）**沿用**：

- **权威源**：[`.claude/skills/test-report/references/quality-rules.md`](../test-report/references/quality-rules.md)

**禁止**在本 skill 内独立定义阈值。若 HE 原文与 `quality-rules.md` 冲突 → **以权威源为准**。

### 关键对齐项

| 本 skill 检查项 | 权威源章节 |
|---|---|
| 单元测试分支覆盖率阈值（≥80%）| 本 skill 特有规则，**非** quality-rules.md 范畴（测试代码质量，不是测试结果质量）|
| P0 用例全通过要求 | quality-rules.md §三 |
| 缺陷等级定义 | quality-rules.md §六 |
| 🟢/🟡/🔴 整体结论 | quality-rules.md §一 |

### 例外说明

- **单元测试分支覆盖率 ≥80%** 是本 skill（提测前开发自测）专属门禁，与 quality-rules.md 的"测试结果质量"不同域，独立维护。
- 与 `acceptance-checkin` 的 80% 保持一致（已在 2026-04-22 对齐）。

### 设计动机

- 避免 test-report / release-gate / submission-gate 之间的**"质量结果"**判定漂移
- 但保留各自专属门禁的独立性（如 submission-gate 的 UT 覆盖率属于"开发交付"维度）
