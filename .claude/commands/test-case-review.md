---
description: 对 test-case-design 和 api-test-case-design 生成的用例进行 AI 辅助审核，对照 test-points.md 检查覆盖完整性、边界/异常路径遗漏、预期结果与技术文档一致性、步骤可执行性、断言可执行性（含层级标注/禁用词/数值断言升级），输出审核报告供测试工程师修正。位于用例生成之后、用例补充之前。适用场景：用例刚生成后的结构质量门禁。不适用：PRD 版本变更后的受影响用例识别 → 使用 test-case-prd-consistency。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/test-case-review/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-case-review/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-case-review/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/test-case-review/` 下的 Base 版本。
