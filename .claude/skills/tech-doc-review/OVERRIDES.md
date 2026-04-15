---
skill: tech-doc-review
based_on: harness@2.0.0
he_path: linscode/skills/iteration/testing/tech-doc-review
override_count: 2
last_updated: 2026-04-15
---

# tech-doc-review 项目定制

## 覆盖 1：Phase 1 模块 ID 校验

**HE 原文位置**：Phase 1 → 步骤 4（识别模块标识）→ 多模块分配标识
**HE 原文摘要**：为每个模块分配英文标识，仅允许 `[a-z0-9-]`，长度 ≤ 30
**定制为**：追加校验步骤——若用户提供的标识包含非法字符（大写字母、中文、空格、特殊符号）或超长，提示用户修正后再继续

## 新增 1：S>3 阈值量化依据

**HE 原文位置**：Phase 4 → 整体评估量化规则
**HE 原文摘要**：B=0 且 S≤3 → 通过；B=0 且 S>3 → 有条件通过；B≥1 → 不通过
**定制为**：追加阈值依据说明——S（补充）级问题平均处理时间约 0.5~1 天，S>3 意味着 2+ 天额外工作量，超出单迭代可消化范围

## 补充项

- 按需加载 `.claude/docs/tech_doc_review.md` (v2.3) 作为审阅维度标准补充
