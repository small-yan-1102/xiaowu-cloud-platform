---
description: 将迭代设计文档转化为方案评审演讲稿。面向产品经理、前端、测试、研发负责人，图文并茂，支持新功能与原有功能对比分析，自动评估演讲时长。触发关键词：生成演讲稿、方案评审稿、技术评审演讲、准备评审会、将设计文档转演讲稿。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/technical-solution/backend-tech-design-presentation/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/backend-tech-design-presentation/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/backend-tech-design-presentation/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/technical-solution/backend-tech-design-presentation/` 下的 Base 版本。
