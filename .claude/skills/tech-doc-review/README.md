# 技术文档审阅 - 规则与Skill体系说明

> **Skill管"怎么做"（审阅流程），规则管"做成什么样"（检查标准）。**

## 概述

本 Skill 用于提测前审阅开发提供的技术文档，确保：
1. 技术方案忠实实现了 PRD 需求
2. 技术方案具备 AI 测试的可执行性
3. 识别 AI 标准不覆盖的风险场景

## 涉及的文件

| 文件 | 类型 | 职责 |
|------|------|------|
| `tech-doc-review/SKILL.md` | Skill | 定义**审阅流程**：5 Phase 工作流 |
| `tech_doc_review.md` | 规则 | 定义**检查标准**：C/U/F/O/D/A/T/R/K 各维度检查项 |
| `ai_test_case_design.md` | 规则 | 判断 AI 标准覆盖范围（风险去重依据） |

## 使用流程

```
┌─────────────────────────────────────────────────────────────┐
│                    技术文档审阅流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   输入材料                                                  │
│   ┌──────────────┐  ┌──────────────┐                       │
│   │ 技术文档      │  │ PRD 基线     │                       │
│   │ input/tech/  │  │ input/prd/   │                       │
│   └──────┬───────┘  └──────┬───────┘                       │
│          │                 │                                │
│          └────────┬────────┘                                │
│                   ▼                                         │
│   ┌──────────────────────────────────┐                     │
│   │  tech-doc-review Skill           │                     │
│   │  ─────────────────────────────── │                     │
│   │  Phase 0: 定向收集               │                     │
│   │  Phase 1: 输入收集               │                     │
│   │  Phase 2: 文档分类               │                     │
│   │  Phase 3: 执行审阅 ◀─ 引用规则   │                     │
│   │  Phase 4: 问题汇总               │                     │
│   │  Phase 5: 输出报告               │                     │
│   └──────────────┬───────────────────┘                     │
│                  ▼                                          │
│   ┌──────────────────────────────────────────────────────┐     │
│   │  审阅报告（按模块+文档类型独立输出）                    │     │
│   │  review/tech-review-report-order-backend.md         │     │
│   │  review/tech-review-report-order-frontend.md        │     │
│   │  review/tech-review-report-payment-backend.md       │     │
│   │  review/tech-review-summary.md（汇总+模块级判定）    │     │
│   └──────────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 职责分工

| 维度 | Skill 负责 | 规则负责 |
|------|-----------|---------|
| 输入收集与确认 | Skill Phase 1 | - |
| 文档分类与维度选择 | Skill Phase 2 | 规则附录B |
| 检查项定义 | - | 规则 §1-§2 |
| 问题分级 | - | 规则 §3 |
| 风险去重判定 | Skill Phase 4 调用 | 规则 §1.2.2 |
| 报告模板 | Skill §四 | - |

## 触发方式

当用户请求中包含以下关键词时，触发本 Skill：
- "审阅技术文档"
- "技术文档测试评审"
- "技术设计审阅"
- "检查技术方案的可测试性"

## 输出约定

| 输出物 | 路径 |
|-------|------|
| 单文档审阅报告 | `review/tech-review-report-{module}-{type}.md` |
| 单文档复审报告 | `review/tech-review-report-{module}-{type}-r{N}.md` |
| 审阅汇总报告 | `review/tech-review-summary.md` |

> `{module}` = 功能模块英文标识（如 `order`, `payment`, `user-center`），单模块默认 `main`
> `{type}` = `backend` | `frontend` | `api` | `db` | `testid` | `full`

## 与 test-case-design 的衔接

审阅汇总报告 `review/tech-review-summary.md` 中 §二（聚合补充场景）和 §三（聚合用例建议）的内容，将作为 `test-case-design` skill「技术文档补充模式」的输入。Mode B 可指定目标模块 scope，按模块过滤聚合内容。

```
tech-doc-review skill
        │
        │ 输出单文档审阅报告（按模块+类型）
        │ review/tech-review-report-order-backend.md
        │ review/tech-review-report-order-frontend.md
        │ review/tech-review-report-payment-backend.md
        │
        │ 同步更新汇总报告
        │ review/tech-review-summary.md
        ▼
test-case-design skill (Mode B)
        │
        │ 读取汇总报告 §〇 模块级判定
        │ 按模块过滤 §二/§三 聚合补充场景
        ▼
  补充测试用例输出（按模块分文件）
  test_suites/suite_order_supplement.md
  test_suites/suite_payment_supplement.md
```

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| v1.4 | 2026-04-09 | 新增 Phase 0 定向收集（询问审阅范围、模式、模块标识、文档路径、历史报告状态） |
| v1.3 | 2026-03-30 | 工作流概览补充 Phase 编号；输出约定增加复审轮次说明 |
| v1.2 | 2026-03-30 | 多模块支持：输出路径增加 `{module}` 维度，汇总报告增加模块级判定 |
| v1.1 | 2026-03-30 | 审阅报告拆分：按文档类型独立输出 + 汇总文件 |
| v1.0 | 2026-03-30 | 从 tech_doc_review.md 规则拆分出审阅流程 |
