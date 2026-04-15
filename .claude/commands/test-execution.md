---
description: 读取Markdown测试用例，通过browser-use MCP直接操作浏览器执行测试，自主判断结果并生成执行报告。支持测试环境完整执行和生产环境线上回归验证（D5）。包含部署预检、数据就绪验证、截图双证据体系、生产环境熔断机制。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/test-execution/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-execution/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-execution/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/test-execution/` 下的 Base 版本。
