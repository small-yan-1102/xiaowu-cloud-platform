---
skill: test-data-preparation
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/test-data-preparation
override_count: 1
override_files:
  - references/variable-handoff-protocol.md
last_updated: 2026-04-15
---

# test-data-preparation 项目定制

## 覆盖文件 1：references/variable-handoff-protocol.md

**HE 原文**：§一~§五 + §六 常见问题（共 6 章）
**定制为**：新增 §六「运行时变量优先级规则」（原 §六 常见问题改为 §七）：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| 1（最高）| test-execution / api-test-execution 运行时 `[输出:]` 捕获 | 反映实际执行后的最新状态 |
| 2 | data-prep-report 变量映射表 | 测试执行前 API 创建的预置数据 |
| 3（最低）| 用例中 `{引用:}` 的静态默认值 | 兜底值 |

含冲突处理规则和并行执行共享说明。

> **注意**：本定制修改的是 references/ 下的文件而非 SKILL.md。当 HE 更新时，需保留本项目版本的 `references/variable-handoff-protocol.md`。
