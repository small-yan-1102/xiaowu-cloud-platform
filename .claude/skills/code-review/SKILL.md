---
name: code-review
description: 对当前分支变更进行结构化代码审查,按正确性、安全性、性能、可读性、项目规范五个维度输出分级审查报告。当用户说"审查代码"、"review"、"代码审查"时使用。
version: 3.0.0
patterns:
  - Reviewer（基于检查清单的多维度评审）
  - Generator（基于模板生成审查报告）
triggers:
  - "审查代码"
  - "review"
  - "代码审查"
  - "看看改得怎么样"
  - "code-review"
dependencies: []
---

# 代码审查技能

> **设计模式**：Reviewer（检查清单驱动）+ Generator（模板化输出报告）

## 输入/输出契约

### 输入
| 输入项 | 来源 | 缺失时处理 |
|-------|------|----------|
| 变更文件列表 | `git diff {base-branch} --name-only` | Fatal：无变更则无需审查 |
| 项目编码规范 | 项目 rules 目录（如有） | Warn：跳过项目规范检查 |
| 审查检查清单 | `references/review-checklist.md` | 自动加载 |

### 输出
| 输出产物 | 格式 |
|---------|------|
| 代码审查报告 | 基于 `assets/review-report-template.md` 生成 |

---

## 核心工作流

```
Task Progress:
- [ ] Phase 1: 变更文件收集
- [ ] Phase 2: 逐文件审查（基于检查清单）
- [ ] Phase 3: 输出审查报告
```

### Phase 1: 变更文件收集

1. 运行 `git diff {base-branch} --name-only` 列出变更文件
2. 如项目有编码规范文件，读取并理解
3. 识别变更文件的类型和关联关系
4. 加载审查检查清单 `references/review-checklist.md`

**⚠️ 硬门控：DO NOT proceed to Phase 2 until:**
- [ ] 变更文件列表已获取
- [ ] 文件类型已分类
- [ ] 审查检查清单已加载

### Phase 2: 逐文件审查（Reviewer 检查清单）

**⚠️ 硬门控：DO NOT proceed to Phase 3 until all files are reviewed.**

对每个变更文件，按 `references/review-checklist.md` 中的五个维度逐一审查：

1. **正确性** (Correctness)
2. **安全性** (Security)
3. **性能** (Performance)
4. **可读性** (Readability)
5. **项目规范** (Project Standards)

**审查流程**:
1. 按文件类型选择对应的检查清单
2. 逐项检查并记录问题
3. 按 Critical/Warning/Info 分级
4. 给出具体修复建议

### Phase 3: 输出审查报告

基于 `assets/review-report-template.md` 模板生成审查报告,包含:

1. **审查概览**: 各维度问题统计
2. **文件审查详情**: 每个文件的具体问题
3. **问题汇总**: 按 Critical/Warning/Info 分级
4. **审查结论**: 通过/有建议/需修改
5. **后续行动**: 需要修复的问题清单

---

## 问题严重度分级

| 级别 | 定义 | 处理要求 |
|------|------|---------|
| **Critical** | 必须修复 — bug、安全问题、数据损坏风险 | 阻断合并 |
| **Warning** | 建议修复 — 性能、可读性、潜在风险 | 合并前建议修复 |
| **Info** | 仅供参考 — 风格、优化建议 | 可选修复 |

---

## 约束

- 审查聚焦变更代码，不对未变更代码提出修改建议
- 不借审查机会做重构建议（除非变更本身引入了架构问题）
- Critical 问题必须给出具体修复方案，而非仅指出问题
- 问题分级必须准确，不允许夸大或弱化
- 所有问题必须标注具体位置（文件路径 + 行号）

## 附属资源文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 审查检查清单 | `references/review-checklist.md` | 多维度检查清单，按文件类型分类 |
| 审查报告模板 | `assets/review-report-template.md` | 标准审查报告格式 |
