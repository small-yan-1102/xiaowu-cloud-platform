---
skill: visual-location-fallback
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/visual-location-fallback
override_count: 1
last_updated: 2026-04-15
---

# visual-location-fallback 项目定制

## 覆盖 1：使用前提（触发条件澄清）

**HE 原文位置**：使用前提
**HE 原文摘要**：本 skill 仅在以下条件**全部满足**时启用（3 个条件）
**定制为**：改为两种启用方式（满足其一即可）：

**方式 A：自动触发**（语义定位失败后兜底）
- test-execution 已按优先级依次尝试 4 种语义定位方式
- 上述 4 种方式均未能定位到目标元素
- 页面已正常加载（非白屏、非加载中状态、无 loading 遮罩）

**方式 B：显式标注**（用例预声明，跳过语义定位）
- 用例步骤中标注 `[定位: 视觉兜底]` 时直接进入本 skill
