---
skill: test-point-extraction
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/test-point-extraction
override_count: 1
last_updated: 2026-04-15
---

# test-point-extraction 项目定制

## 覆盖 1：AI 可执行性标签细分

**HE 原文位置**：Phase 2 → 提炼规则 → AI 可执行性标签表
**HE 原文摘要**：3 个标签 `[AI]` / `[AI+人工]` / `[人工]`
**定制为**：`[AI+人工]` 细分为 4 个子类型：

| 标签 | 含义 | 典型场景 |
|------|------|---------|
| `[AI+人工:验证码]` | 需人工输入验证码/短信码 | 短信验证码、图形验证码 |
| `[AI+人工:文件]` | 需人工操作文件 | 文件上传、下载验证 |
| `[AI+人工:第三方]` | 需人工完成第三方操作 | 微信支付、扫码登录 |
| `[AI+人工:其他]` | 其他类型人工介入 | 人脸识别等 |

> test-case-design 消费时统一识别 `[AI+人工:*]` 前缀，子类型用于人工介入步骤的具体描述。
