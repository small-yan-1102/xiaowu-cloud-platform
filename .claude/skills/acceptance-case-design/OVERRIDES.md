---
skill: acceptance-case-design
based_on: harness@1.0.0
he_path: linscode/skills/iteration/acceptance/acceptance-case-design
override_count: 1
last_updated: 2026-04-16
---

# acceptance-case-design 项目定制

## 新增 1：Phase 0 必问验收执行方式

**HE 原文位置**：Phase 0 → 问题列表
**HE 原文摘要**：Phase 0 问验收范围、PRD 路径等，不问执行方式。默认产出供 acceptance-walkthrough（AI+人工协同）执行的用例
**定制为**：Phase 0 问题列表之后，**必须**追加一个问题：

> **验收执行方式**：验收用例由谁执行？
>    - AI+人工协同（默认）：AI 操作浏览器执行客观断言，人工负责业务判断
>    - 纯人工：全部由验收工程师手动执行，用例按人工可读菜谱格式输出
>    - 按默认：AI+人工协同

⛔ **DO NOT** 跳过此问题。用户回答决定用例格式：
- AI+人工协同：步骤区分 AI 可执行（精确操作+断言）和人工判断（标注 `⚠️ [人工判断]`）
- 纯人工：全部步骤按人工可读菜谱格式（逐步操作 + 逐条预期，不含 selector/API 等机器细节）
