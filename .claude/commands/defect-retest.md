---
description: 开发修复缺陷后的定向回归验证。从缺陷清单提取待回归项，针对关联测试用例重新执行，按结果指导云效缺陷状态更新（通过→关闭，失败→重新打开），输出回归验证报告。位于 bug-sync 之后、下一轮 release-gate 之前。
---
请读取并严格执行 `linscode/skills/iteration/testing/defect-retest/SKILL.md` 中定义的完整工作流。

技能所需的支撑文件（模板、检查清单等）位于 `linscode/skills/iteration/testing/defect-retest/` 目录下，以该目录为基准解析相对路径。
