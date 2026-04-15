---
description: 审阅技术文档，执行需求一致性、风险场景识别和AI可测试性检查，输出结构化审阅报告
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/tech-doc-review/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/tech-doc-review/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/tech-doc-review/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/tech-doc-review/` 下的 Base 版本。
