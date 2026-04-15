---
description: 基于接口定义文档设计接口测试用例，覆盖正向、边界值、等价类、错误码、鉴权、幂等、响应结构七个维度，输出可供 api-test-execution 直接执行的 Markdown 接口用例套件。支持两种模式：Mode A 基于接口文档初次生成、Mode B 针对变更接口设计回归用例。可选加载 test-points.md 作为覆盖基准（存在时自动对照测试点补全用例）。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/api-test-case-design/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/api-test-case-design/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/api-test-case-design/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/api-test-case-design/` 下的 Base 版本。
