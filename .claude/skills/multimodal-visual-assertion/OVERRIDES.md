---
skill: multimodal-visual-assertion
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/multimodal-visual-assertion
override_count: 1
last_updated: 2026-04-15
---

# multimodal-visual-assertion 项目定制

## 新增 1：集成约束章节

**HE 原文位置**：用例标注方式 → 描述要求之后
**HE 原文摘要**：无集成约束说明
**定制为**：新增「集成约束」章节：

**由 test-execution 调用时**（主要使用方式）：
- test-execution 遇到 `[断言: 视觉-AI]` 时自动调用
- 同一步骤多条 `[断言: 视觉-AI]` → 逐条调用，共享同一张截图
- 断言结果嵌入 test-execution 执行记录，无独立输出文件
- 同一步骤既需 visual-location-fallback 又需本 Skill → 先定位后断言

**独立调用时**：
- 输出路径：`test_reports/visual-assertion-report-{YYYYMMDD-HHmmss}.md`
