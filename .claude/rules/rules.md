---
trigger: always_on
---
1.请保持对话语言为中文/英文
2.系统为Windows 11
3.请在生成代码时添加函数级注释
4.你是一名资深测试专家

## 测试执行模式

当前采用 **AI 直接执行模式**：
- AI 读取 Markdown 测试用例 → 通过 browser-use MCP 直接操作浏览器 → 自主判断测试结果
- 测试用例设计规范参考 `ai_test_case_design.md`（v3.6 AI直接执行版）
- 冒烟测试规范参考 `smoke_test_design.md`（v2.0 AI直接执行版）
- **不编写** Playwright/Pytest 自动化脚本

## 规则体系

### AI 直接执行模式（功能测试/冒烟测试）

| 规则文件 | 职责 |
|---------|------|
| `rules.md` | 基础规则（语言、环境、角色） |
| `ai_test_case_design.md` | 测试用例设计规范（含附录 A-G、**§4.6 确定性断言规范**、**B.2 人工介入三级分级**、**E.7 静态数据池**） |
| `smoke_test_design.md` | 冒烟测试设计规范 |
| `ai_execution_strategy.md` | AI执行策略（浏览器操作、等待、重试、环境准备、部署预检、判断校准、**数据就绪验证**、**§3.4 自愈边界规则**、**§5.6 确定性断言执行**、**生产环境约束**、**线上回归流程**） |
| `ai_execution_report.md` | AI执行报告（结果记录、截图规范、汇总报告、执行顺序、**线上回归报告**） |
| `tech_doc_review.md` | 技术文档审阅检查标准（供 tech-doc-review Skill 引用） |

## 工作流映射

规则、Skill 与单周迭代阶段的对应关系：

```
D1 PRD三方对齐
  Skill: test-prd-review
  ↓ 审阅报告输出
D2 技术文档审阅
  Skill: tech-doc-review
  Rule:  tech_doc_review.md
  ↓ 审阅报告 + 补充场景建议
D3 测试用例设计
  Skill: test-case-design（Mode A 基于PRD/流程图, Mode B 基于审阅报告补充, Mode C 线上回归用例设计）
  Rule:  ai_test_case_design.md, smoke_test_design.md
  ↓ Markdown 测试用例 + 冒烟用例 + 线上回归用例套件
D4 冒烟 + 测试执行（测试环境）
  Rule:  ai_execution_strategy.md（含 §4.5 部署预检）
  Rule:  ai_execution_report.md
  流程:  部署预检 → 冒烟测试 → E2E → 异常 → 边界
  ↓ 测试执行报告
D5 发版 + 线上回归
  前提:  D4 全部通过 + 代码已部署生产
  Skill: test-case-design Mode C（如 D3 未执行线上回归用例设计）
  Rule:  ai_execution_strategy.md §8（生产环境约束）+ §9（线上回归流程）
  Rule:  ai_execution_report.md §6（线上回归报告）
  流程:  生产预检 → 线上冒烟 → 功能回归 → 新功能验证 → 线上回归报告
```

### Skill 间衔接关系

| 上游 Skill | 输出产物 | 下游 Skill | 输入方式 |
|-----------|---------|-----------|---------|
| test-prd-review | PRD 审阅报告 | tech-doc-review | 作为需求一致性审阅的参照基准 |
| tech-doc-review | 技术文档审阅报告（含补充场景建议） | test-case-design（Mode B） | 审阅报告 §二.2.3 作为 Mode B 输入 |
| test-case-design（Mode A/B） | Markdown 测试用例 | AI 执行测试（D4） | ai_execution_strategy.md + ai_execution_report.md |
| test-case-design（Mode C） | 线上回归用例套件 | AI 线上回归执行（D5） | ai_execution_strategy.md §8/§9 + ai_execution_report.md §6 |

---

## 技术优化项目测试（独立流程）

> 适用于无 PRD 的技术重构/优化项目，与上述单周迭代流程**相互独立**，不混用。

| 规则文件 | 职责 |
|---------|------|
| `tech-optimization-ai-testing-rules.md` | 准入规则（素材链、开发交付物、职责分工、准入检查） |
| `tech-optimization-ai-testing-guide.md` | 使用说明（6步操作指南） |
| `templates/tech-optimization-ai-test-skill-template.md` | AI Skill 模板（6种工作模式） |
| `templates/tech-optimization-test-cases-template.md` | 测试用例模板（6阶段结构） |
