---
description: 使用 AI 视觉模型对页面截图执行多模态视觉断言，适用于无法通过 DOM 文本验证的内容：图表、图形、画布渲染、图片展示、PDF 预览、复杂布局等。与 test-execution 配合使用，处理 [断言: 视觉-AI] 标注的预期结果。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/multimodal-visual-assertion/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/multimodal-visual-assertion/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/multimodal-visual-assertion/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/multimodal-visual-assertion/` 下的 Base 版本。
