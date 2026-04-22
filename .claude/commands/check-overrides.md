---
description: 检查 `.claude/skills/*/OVERRIDES.md` 与 HE Base SKILL.md 的版本一致性，发现 HE 升级后 Override 未同步的情况。
---
## 执行步骤

逐一检查 `.claude/skills/*/OVERRIDES.md` 文件：

1. 读取 OVERRIDES.md 的 frontmatter，提取 `based_on`（如 `harness@4.0.0` → 版本 `4.0.0`）和 `he_path`
2. 读取 `{he_path}/SKILL.md` 的 frontmatter，提取 `version`
3. 比对两个版本号

## 输出格式

```
Override 版本一致性检查报告
========================

| Skill | Override based_on | HE 当前版本 | 状态 |
|-------|-------------------|-------------|------|
| test-case-design | 4.0.0 | 4.0.0 | ✅ 一致 |
| tech-doc-review  | 2.0.0 | 2.1.0 | ⚠️ 需同步 |
...

结论：X/14 一致，Y/14 需同步
```

对于 `⚠️ 需同步` 的项，追加差异摘要：
- 列出 HE SKILL.md 相比 OVERRIDES.md `based_on` 版本有哪些章节发生了变化
- 判断变化是否影响 OVERRIDES.md 中的覆盖点
- 给出建议：「仅更新 based_on 版本号」或「需要审阅并调整 Override 内容」
