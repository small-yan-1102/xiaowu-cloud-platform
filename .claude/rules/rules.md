---
trigger: always_on
---
1. 对话语言：中文/英文
2. 系统环境：Windows 11（shell 命令使用 Unix 语法）
3. 生成代码时添加函数级注释
4. 角色：资深测试专家

## 测试执行模式

当前采用 **AI 直接执行模式**：
- AI 读取 Markdown 测试用例 → 通过 browser-use MCP 直接操作浏览器 → 自主判断测试结果
- **不编写** Playwright/Pytest 自动化脚本

## 规则分层

- **自动加载**（本文件）：基础规则 + 工作流映射
- **按需读取**（`.claude/docs/`）：用例设计/执行策略/报告等规范，Skill 执行时加载
- **敏感凭证**（`.claude/secrets/credentials.md`）：测试执行时按需读取
- **环境配置**（`.claude/docs/test-environment-config.md`）：执行测试前读取

## 工作流映射（D1-D5）

```
D1 PRD 审阅      → /test-prd-review → /prd-gate → /test-point-extraction
D2 技术文档审阅   → /tech-doc-review
D3 用例设计       → /test-case-design → /test-case-review
D4 冒烟+测试执行  → /test-execution
D5 发版+线上回归  → /bug-sync → /test-report → /release-gate
```

### Skill 衔接

| 上游 | 产物 | 下游 |
|------|------|------|
| test-prd-review | PRD 审阅报告 | tech-doc-review / prd-gate |
| tech-doc-review | 审阅报告（含补充场景建议） | test-case-design Mode B |
| test-case-design | Markdown 用例 | test-execution / test-case-review |
| test-execution | 执行报告 | bug-sync → test-report → release-gate |
