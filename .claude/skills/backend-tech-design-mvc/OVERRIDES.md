---
skill: backend-tech-design-mvc
based_on: harness@2.1.0
he_path: linscode/skills/iteration/technical-solution/backend-tech-design-mvc
override_count: 2
last_updated: 2026-04-15
---

# backend-tech-design-mvc 项目定制

## 覆盖 1：Phase 6 偏差修复循环上限

**HE 原文位置**：Phase 6 → 步骤 4（审阅完成确认）→ 用户提出新偏差 → 回到步骤 3
**HE 原文摘要**：无循环次数限制，持续循环直到用户确认无偏差
**定制为**：步骤 3→4 的偏差修复循环**最多执行 3 轮**。达到上限后向用户展示未解决偏差清单，建议接受或标注「待线下确认」。

## 新增 1：路径解析规则 + 上游衔接

**HE 原文位置**：输入契约表后（MVC 编写规范行之后）
**HE 原文摘要**：无路径解析说明
**定制为**：
- 路径解析规则：输入契约中 `./` 前缀路径均相对于 `.claude/skills/backend-tech-design-mvc/` 目录解析
- 上游衔接：若已执行 `backend-prd-review`，用户可提供其产出的 `backend-prd-summary.md` 作为 PRD 输入
