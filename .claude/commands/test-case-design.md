---
description: 根据 PRD/流程图设计测试用例，输出可供 AI 直接执行的 Markdown 用例套件，支持 Mode A/B/C/D 四种模式
---
请读取并严格执行 `.claude/skills/test-case-design/SKILL.md` 中定义的完整工作流。

> 根据 PRD/流程图设计测试用例，覆盖等价类、边界值、场景法、CRUD 全流程，输出可供 AI 直接浏览器执行的 Markdown 用例套件。支持四种模式：Mode A 基于 PRD 初次生成、Mode B 依据技术文档补充风险场景、Mode C 线上回归用例设计与发版验证、Mode D 冒烟测试专项设计（核心链路快速健康检查，每条 <2 分钟，套件 <5 分钟，失败阻塞部署）。

技能所需的支撑文件（模板、检查清单等）位于 `.claude/skills/test-case-design/` 目录下，以该目录为基准解析相对路径。
