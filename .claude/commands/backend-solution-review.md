---
description: 前端视角审阅后端方案，检查接口设计合理性、消费友好性和性能影响
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/frontend-coding/requirements/backend-solution-review/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/backend-solution-review/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/backend-solution-review/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/frontend-coding/requirements/backend-solution-review/` 下的 Base 版本。
