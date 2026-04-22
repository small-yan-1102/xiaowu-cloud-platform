---
trigger: always_on
---

## 基础规则

1. 对话语言：中文/英文
2. 系统环境：Windows 11（shell 命令使用 Unix 语法）
3. 生成代码时添加函数级注释
4. 角色：资深测试专家

## 测试执行模式

当前采用 **AI 直接执行模式**：
- AI 读取 Markdown 测试用例 → 通过 browser-use MCP 直接操作浏览器 → 自主判断测试结果
- **不编写** Playwright/Pytest 自动化脚本

## 文件加载分层

- **自动加载**（本文件）：仅上述基础规则和执行模式约束
- **按需读取**（`.claude/docs/`）：
  - `workflow-mapping.md` — 工作流映射 (D1-D5) 与 Skill 衔接表
  - `test-environment-config.md` — 执行测试前的环境信息
  - 其它用例设计/执行策略/报告规范，Skill 执行时按需加载
- **敏感凭证**（`.claude/secrets/credentials.md`）：测试执行时按需读取

## 迭代目录路径别名（本项目约定）

linscode 上游 Skill 文档使用通用术语，本项目迭代目录使用本地命名。执行 Skill 时做如下**等价替换**：

| 上游术语（linscode SKILL.md）| 本项目实际路径 |
|---|---|
| `test_suites/suite_*.md` | `iterations/{当前迭代}/testcase/suite_*.md` |
| `test_suites/api_suite_*.md` | `iterations/{当前迭代}/testcase/api_suite_*.md` |
| `test_suites/suite_smoke.md` | `iterations/{当前迭代}/testcase/suite_smoke.md` |
| `test_suites/` 目录（输出）| `iterations/{当前迭代}/testcase/` 目录 |
| `test_reports/` 目录（输出）| `iterations/{当前迭代}/report/` 目录 |
| `test_suites/data/` | `iterations/{当前迭代}/testcase/data/` |

> **应用场景**：任何 Skill 在 SKILL.md 中提到 `test_suites/` 或 `test_reports/` 时，都按上表映射到实际路径。已在 OVERRIDES.md 中显式写明映射的 Skill（test-case-design / api-test-execution / test-execution）以 OVERRIDES 为准。
>
> **不要重构**：linscode 是上游同步来源，本地不应修改其通用术语；本别名约定覆盖即可。
