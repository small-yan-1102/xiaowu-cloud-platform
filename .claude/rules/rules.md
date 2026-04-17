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
D3 用例设计       → /test-case-design → /test-case-review → /submission-gate
D4 冒烟+测试执行  → /test-data-preparation → /test-execution + /api-test-execution
D5 发版+线上回归  → /bug-sync → /test-report → /release-gate
```

> **submission-gate 位置说明**：提测门禁放在 D3 末尾（用例设计完成后），因为其九项检查中包含"用例套件存在性"，必须在用例产出后才能通过。通过后释放 D4 执行。

### Skill 衔接

| 上游 | 产物 | 下游 |
|------|------|------|
| test-prd-review | PRD 审阅报告 | prd-gate / tech-doc-review |
| prd-gate | 通过/不通过 | test-point-extraction |
| test-point-extraction | test-points.md | test-case-design Mode A |
| tech-doc-review | 审阅报告（含补充场景建议） | test-case-design Mode B |
| test-case-design | Markdown 用例套件 | test-case-review |
| test-case-review | 审核报告（含§五颗粒度） | test-case-design Mode E（补缺）/ Mode F（优化颗粒度） |
| test-case-review 通过 | — | submission-gate |
| submission-gate | 通过/不通过 | test-data-preparation → test-execution / api-test-execution |
| test-execution + api-test-execution | 执行报告 | bug-sync → test-report → release-gate |
| release-gate 不通过 | 阻塞项 | defect-retest → 循环回 test-execution |
