---
skill: test-case-review
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/test-case-review
override_count: 2
last_updated: 2026-04-15
---

# test-case-review 项目定制

## 覆盖 1：Phase 0 默认用例路径

**HE 原文位置**：Phase 0 → 问题 1（UI 用例路径）和 问题 2（接口用例路径）
**HE 原文摘要**：默认 `review/test-cases-ui.md` 和 `review/test-cases-api.md`
**定制为**：
- UI 用例：自动扫描 `test_suites/suite_*.md`；若未找到再尝试 `review/test-cases-ui.md`
- 接口用例：自动扫描 `test_suites/api_suite_*.md`；若未找到再尝试 `review/test-cases-api.md`

## 覆盖 2：Phase 1 用例文件读取

**HE 原文位置**：Phase 1 → 步骤 2（读取 UI 用例文件）
**HE 原文摘要**：加载默认 `review/test-cases-ui.md`
**定制为**：先扫描 `test_suites/suite_*.md`（test-case-design 标准输出路径），若未找到再尝试用户指定路径
