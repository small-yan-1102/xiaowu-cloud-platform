---
description: 从 PRD 审阅摘要中提炼结构化测试点清单，覆盖正向流程、边界值、异常场景、权限、状态机等维度，输出 test-points.md 作为 test-case-design 的覆盖基准。位于 prd-gate 通过之后、test-case-design Mode A 之前。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/test-point-extraction/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-point-extraction/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-point-extraction/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/test-point-extraction/` 下的 Base 版本。
