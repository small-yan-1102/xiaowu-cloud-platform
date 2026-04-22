# 测试工作流映射与 Skill 衔接

> **定位**：`.claude/rules/rules.md` 从架构文档中剥离的补充材料。
> **加载方式**：按需读取，不自动加载。
> **何时读**：
> - 执行跨阶段 Skill 前（需要理清上下游依赖）
> - 排查某个 Skill 的输入输出契约
> - 向新人介绍团队测试流程时

---

## 工作流映射（D1–D5）

```
D1 PRD 审阅      → /test-prd-review → /prd-gate → /test-point-extraction
D2 技术文档审阅   → /tech-doc-review
D3 用例设计       → /test-case-design → /test-case-review → /submission-gate
D4 冒烟+测试执行  → /test-data-preparation → /test-execution + /api-test-execution
D5 发版+线上回归  → /bug-sync → /test-report → /release-gate
```

> **submission-gate 位置说明**：提测门禁放在 D3 末尾（用例设计完成后），因为其九项检查中包含"用例套件存在性"，必须在用例产出后才能通过。通过后释放 D4 执行。

---

## Skill 衔接表

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
