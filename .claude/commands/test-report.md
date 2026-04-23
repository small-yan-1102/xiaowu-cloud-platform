---
description: 生成测试报告（本地定制 v2.0）。聚合执行报告+缺陷源+测试点，产出 🟢/🟡/🔴 质量结论 + 三元通过率（AI/人工/总）+ 模块×优先级透视 + 需求覆盖矩阵。默认 MD，--format=html 可追加 HTML。
---
请读取并严格执行 `.claude/skills/test-report/SKILL.md` 中定义的完整工作流。

技能所需的支撑文件（模板、质量规则、缺陷 adapter 等）位于 `.claude/skills/test-report/` 目录下，以该目录为基准解析相对路径。

> **本 skill 是本地定制 v2.0**，已完全替代 linscode 上游 `skills/iteration/testing/test-report/`。
> **跨 skill 共享**：`references/quality-rules.md` 同时被 `release-gate` / `submission-gate` 引用。
> **上游漂移**：运行 `python C:/Users/1/.claude/tools/check_upstream_drift.py` 定期检查。
