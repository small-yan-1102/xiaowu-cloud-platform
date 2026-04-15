---
description: 根据 PRD/流程图设计测试用例，输出可供 AI 直接执行的 Markdown 用例套件，支持 Mode A/B/C/D 四种模式
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/test-case-design/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-case-design/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-case-design/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/test-case-design/` 下的 Base 版本。
