---
description: 基于MVC架构，根据产品PRD结合现有实现，生成/更新迭代设计文档。产出同时服务于人类阅读和AI代码生成。当用户需要进行MVC架构的后端技术设计迭代时使用此技能。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/technical-solution/backend-tech-design-mvc/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/backend-tech-design-mvc/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/backend-tech-design-mvc/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/technical-solution/backend-tech-design-mvc/` 下的 Base 版本。
