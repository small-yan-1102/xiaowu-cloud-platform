---
description: 读取 Markdown 接口测试用例，直接执行 HTTP 请求，自主断言响应结果并生成执行报告。与 test-execution（浏览器执行）并列，专用于接口测试场景。包含变量传递、认证管理、清理步骤执行。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/api-test-execution/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/api-test-execution/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/api-test-execution/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/api-test-execution/` 下的 Base 版本。
