---
description: 基于技术文档和测试用例的前置条件，通过 API 调用自动准备测试数据，输出数据准备报告和变量映射表。支持三种模式：Mode A（数据准备/Setup）、Mode B（数据清理/Teardown）、Mode C（数据探查/Discovery）。当测试用例标注了 [数据准备:API] 策略时用 Mode A；测试执行完毕后用 Mode B 清理；执行前探查环境已有数据用 Mode C，输出三态结论（可直接执行 / 需补数据 / 阻断）。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/test-data-preparation/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/test-data-preparation/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/test-data-preparation/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/test-data-preparation/` 下的 Base 版本。
