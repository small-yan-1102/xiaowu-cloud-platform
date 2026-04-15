---
description: 当语义定位（可见文本/aria-label/placeholder/相对位置）全部失败后，通过截图分析定位目标元素的视觉坐标，作为 browser-use 元素定位的兜底机制。适用于无障碍标注缺失的遗留系统、Canvas 组件、自定义图形控件等场景。
---
## 加载顺序

1. **Base**：读取 `linscode/skills/iteration/testing/visual-location-fallback/SKILL.md` 作为主工作流
2. **Override**：读取 `.claude/skills/visual-location-fallback/OVERRIDES.md`，将其中的「覆盖」和「新增」条目应用到 Base 工作流对应位置
3. **执行**：按合并后的完整工作流执行

> 支撑文件优先使用 `.claude/skills/visual-location-fallback/` 下的本地版本，不存在时回退到 `linscode/skills/iteration/testing/visual-location-fallback/` 下的 Base 版本。
