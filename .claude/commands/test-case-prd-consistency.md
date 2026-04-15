---
description: 排查测试用例与 PRD 不一致问题，检查断言可执行性，提供根因分析和修复方案
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/qa-tools/test-case-prd-consistency/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-case-prd-consistency/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-case-prd-consistency/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/qa-tools/test-case-prd-consistency/` 下的 Base 版本。
