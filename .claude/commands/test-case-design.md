---
description: 【测试团队用】根据 PRD/流程图设计通用测试用例（UI/API/业务/回归），输出 `test_suites/suite_*.md`。Mode A/B/C/D/E 覆盖初次生成、技术文档补充、线上回归、冒烟、审核后补齐。前端开发工程师若仅需 UI 层用例，请用 /frontend-testcase-gen（输出前缀 `suite_ui_*.md`）。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/test-case-design/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-case-design/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-case-design/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/test-case-design/` 下的 Base 版本。
