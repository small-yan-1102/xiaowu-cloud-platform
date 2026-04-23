---
name: test-report
description: 聚合执行报告和缺陷清单，生成测试报告（本地定制 v2.0，完全替代上游）。产出 🟢/🟡/🔴 质量结论 + 三元通过率（AI/人工/总）+ 模块×优先级透视 + 需求覆盖矩阵。默认输出 MD，`--format=html` 追加 HTML。
version: 2.0.0
triggers:
  - "生成测试报告"
  - "写测试报告"
  - "测试报告"
  - "汇总测试结果"
  - "出测试报告"
---

# 测试报告生成技能（本地定制版 v2.0）

> **版本**：v2.0（本地定制，不对应 linscode 上游）
> **定位**：聚合 + 结论，不涉及缺陷登记/发布决策/用例修改
> **跨 skill 共享**：`references/quality-rules.md` 同时被 `release-gate` / `submission-gate` 引用
> **上游漂移检测**：`.upstream_baseline.json` + `C:/Users/1/.claude/tools/check_upstream_drift.py`

---

## 路径约定（本 skill 专用）

| 类别 | 路径 |
|---|---|
| 执行报告（输入）| `iterations/{迭代}/report/execution_report_*.md` |
| 用例套件（输入）| `iterations/{迭代}/testcase/suite_*.md` / `api_suite_*.md` |
| 测试点清单（可选输入）| `iterations/{迭代}/review/test-points.md` |
| 缺陷清单（可选输入）| `iterations/{迭代}/review/bug_reports/bug-report-*.md` 或云效 |
| 报告输出 | `iterations/{迭代}/report/test-report-YYYYMMDD.{md,html}` |

本 skill 使用**本地路径**。不使用上游 `test_suites/` / `test_reports/` 术语。

---

## 职责边界（硬约束）

### ✅ 本 skill 做
- 聚合 execution_report + 缺陷源 + test-points
- 计算三元通过率 / 风险等级 / 覆盖率
- 产出 🟢/🟡/🔴 质量结论
- 写入 MD（默认）/ HTML（opt-in）报告

### ❌ 本 skill 不做（越界即停，提示对应 skill）

| 用户请求 | 应调用 |
|---|---|
| 登记新缺陷 | `/bug-sync` |
| 判定是否可发布 | `/release-gate` |
| 修改用例文件 | `/test-case-design` / `/mark-case` |
| 重新执行测试 | `/test-execution` / `/api-test-execution` |
| 追加截图采集 | `/test-execution` Phase 4 |

**AI 行为规则**：识别到越界需求 → 明确提示对应 skill + **停止当前 Phase**。

---

## 附属资源

| 文件 | 路径 | 何时加载 |
|---|---|---|
| 报告模板 | `assets/report-template.md` | Phase 3 |
| HTML 外壳 | `assets/report-template.html` | Phase 4（仅 `--format=html`）|
| 质量规则 | `references/quality-rules.md` | Phase 2 |
| Adapter 契约 | `references/defect-adapters/_interface.md` | 按需（只在写新 adapter 时）|
| 云效 Adapter | `references/defect-adapters/yunxiao.py` | Phase 0.5 / Phase 1 |
| Markdown Adapter | `references/defect-adapters/markdown.py` | Phase 0.5 / Phase 1（降级兜底）|

---

## 核心工作流

```
Task Progress:
- [ ] Phase 0: 智能输入收集（参数齐全则跳过问答）
- [ ] Phase 0.5: 环境预检（自动，零人工）
- [ ] Phase 1: 加载源数据
- [ ] Phase 2: 计算 + 判定
- [ ] Phase 3: 填充模板
- [ ] Phase 4: 输出（按 --format 分支）
```

---

### Phase 0: 智能输入收集

**决策树**（按优先级尝试，任一满足即进入 Phase 0.5）：

1. **命令参数齐全**：用户在 `/test-report` 后跟了 `--iteration=X --format=Y` 等参数 → 直接进入下一 Phase，**不询问**
2. **默认路径可扫到**：
   - 扫 `iterations/*/report/execution_report_*.md` 取最新迭代的文件
   - 扫 `iterations/*/review/test-points.md`
   - 扫 `iterations/*/review/bug_reports/bug-report-*.md` 或 `.claude/config/defect-source.yaml`
   - 全部可解析 → 明确输出"使用默认：{路径列表}"，**不等回答**，继续 Phase 0.5
3. **有缺失无法默认**：只问缺失项（一次性列完），拿到答案就继续

**支持参数**：

| 参数 | 说明 | 默认 |
|---|---|---|
| `--iteration=X` | 目标迭代目录名 | 最新（按目录 mtime）|
| `--exec-reports=path,...` | 指定执行报告列表 | 扫 `report/execution_report_*.md` |
| `--defect-source=yunxiao\|markdown` | 缺陷数据源 | Phase 0.5 自选 |
| `--format=md\|html\|md,html` | 输出格式 | `md` |
| `--version=X` | 版本号 / 周期标识 | 留空 |

> ⛔ **DO NOT**：默认路径存在时仍问用户。减少对话轮次是核心目标。

---

### Phase 0.5: 环境预检（自动，零人工）

**目标**：确定缺陷源 adapter，失败自动降级。**永不阻断 Phase 1**。

**步骤**：

1. **若用户指定 `--defect-source`** → 跳过自检，直接使用指定值
2. **否则按优先级自检**：
   - 尝试 `python .claude/skills/test-report/references/defect-adapters/yunxiao.py --selftest`
     - 退出 0 → `defect_source = yunxiao`
     - 退出非 0（依赖缺失/配置错误/网络不通）→ 静默降级
   - 尝试 `python .claude/skills/test-report/references/defect-adapters/markdown.py --selftest`
     - 退出 0 → `defect_source = markdown`
     - 退出非 0 → `defect_source = empty`（空缺陷集）
3. **记录降级原因**，在最终报告附录"数据源说明"章节展示

**输出**：`缺陷数据源：{source}（{reason}）`

**原则**：无论自检结果，Phase 1 都会运行。最坏情况报告标注"本轮无可用缺陷数据"。

---

### Phase 1: 加载源数据

**步骤**：

1. **读执行报告**（按 Phase 0 确定的路径）：

   对每条用例提取：
   - 编号 / 名称 / 优先级（P0-P3）/ 所属套件
   - **执行方式**：`AI` 或 `人工`（从 execution_report 的 `**执行人**` 字段或用例的 `[执行方式:]` 标注）
   - 结果：`✅通过` / `❌失败` / `🚫阻塞` / `⏭暂缓` / `⚠️部分通过`
   - 失败/部分通过用例：失败步骤 + L1 断言预期/实际 + **execution_report 锚点**
   - **关联测试点**（若有）：`[TP-001, TP-002]`

   对每个套件提取：
   - 套件总用例数 / 暂缓清单 / 执行方式分布

2. **读测试点清单**（`review/test-points.md`，可选）：
   - 提取每条：测试点编号 / 所属 PRD 模块 / 优先级
   - 构建 `{测试点 → [关联用例]}` 映射（反向查询 Phase 1.1 提取的关联关系）

3. **读缺陷源**：按 Phase 0.5 确定的 adapter：
   ```bash
   python references/defect-adapters/{source}.py --json [--sprint-id X]
   ```
   - 解析 JSON（契约见 `_interface.md`）
   - 失败 → 空缺陷集（不阻断）

4. **合并数据**：
   - 按（套件 → 用例编号）对齐
   - 用例编号去重（UI 报告 + API 报告可能重叠）
   - 补齐缺失字段（如 AI 执行报告漏了优先级 → 从套件 md 回查）

5. **输出摘要**：
   ```
   ✅ 已加载：
   - 执行报告 {N} 份（{迭代名}）
   - 用例总数 {M} / 已执行 {X} / 暂缓 {Y}
   - 测试点 {K} 条（无 → 跳过覆盖矩阵）
   - 缺陷数据 {L} 条（来源：{source}）
   ```

> ⛔ **DO NOT** 进入 Phase 2，直到数据全部加载或明确降级完成。

---

### Phase 2: 计算 + 判定

**前置**：加载 `references/quality-rules.md` 作为权威规则源。

#### 计算 ① — 三元通过率

```
AI 通过率   = AI 通过数   ÷ (AI 执行数    - AI 暂缓   - AI 阻塞)
人工通过率  = 人工通过数  ÷ (人工执行数   - 人工暂缓  - 人工阻塞)
总通过率    = 总通过数    ÷ (总执行数     - 总暂缓    - 总阻塞)
```

**P0 通过率** / **P0+P1 通过率** 同样用"总执行数"作分母。

#### 计算 ② — 模块 × 优先级透视表

对每个（套件 × 优先级）组合：
- `{通过数}/{执行数}` （执行数不含暂缓/阻塞）
- 套件通过率 + 风险等级（用 `quality-rules.md` §模块风险等级 的阈值）

#### 计算 ③ — 需求覆盖矩阵（仅当 test-points.md 存在）

对每个测试点：
- 关联用例全通过 → 🟢 已覆盖
- 关联用例有失败 → 🔴 覆盖但失败
- 关联用例全阻塞/暂缓 → 🟡 覆盖未验证
- 无关联用例 → ⚪ 未关联（覆盖缺口）

计算 **P0 测试点覆盖率** + **覆盖缺口数**。

#### 计算 ④ — 缺陷指标

- 缺陷密度 = 总缺陷数 ÷ 已执行用例数
- 严重缺陷率 = (Fatal + Critical) ÷ 总缺陷数
- 缺陷修复率 = 已关闭 ÷ 总缺陷数

#### 判定 — 整体质量结论

按 `quality-rules.md` §判定阈值，用**总通过率**：

- 🟢 **可发布**：P0 全通过 + Open Fatal = 0 + Open Critical = 0 + 总通过率 ≥ 90%
- 🟡 **有已知风险**：P0 全通过 + Open Fatal = 0 + (Open Critical > 0 或 总通过率 80-89%)
- 🔴 **未达标**：P0 有失败 / Open Fatal > 0 / 总通过率 < 80%

> **若人工执行清单含 P0 用例**：结论后追加 ⚠️ "含 {N} 条 P0 人工执行用例，需测试工程师确认已人工验证"

#### 识别风险项

- **高风险**：P0 失败用例 / 开放 Fatal/Critical 缺陷
- **中风险**：通过率 < 90% 的模块 / 大量 L2 警告
- **需复测**：阻塞用例（环境/数据原因）

> ⛔ **DO NOT** 进入 Phase 3，直到所有指标和结论确定。

---

### Phase 3: 填充模板

**步骤**：

1. 加载 `assets/report-template.md`
2. 按模板占位符 `{...}` 逐项填入 Phase 2 的计算结果
3. 处理可选章节：
   - `<!-- OPTIONAL: when test-points.md exists -->` 标记段
   - 若无 test-points → 删除该段整个区块
4. **失败用例明细**：
   - ❌ 失败 + ⚠️ 部分通过 → 列表格，每行含 execution_report 锚点链接
   - ✅ 成功用例 → **不展开**，按套件归集显示"详见 execution_report_xxx.md"

**原则**：模板即权威。修改报告格式时**只改模板**，SKILL 不重复定义章节。

---

### Phase 4: 输出（按 --format 分支）

| `--format` 值 | 输出 |
|---|---|
| `md`（默认）| `iterations/{迭代}/report/test-report-YYYYMMDD.md` |
| `html` | 追加 `.html`（同名同目录），加载 `assets/report-template.html` 外壳 + 内容填充 |
| `md,html` | 两份同时输出 |

**HTML 生成策略**（按优先级尝试）：
1. 检测 `pandoc` 可用 → 用 `pandoc {md} -o {html} --standalone --css=...`
2. pandoc 不可用 → AI 字符串拼接（Markdown 表格 → `<table>`、标题 → `<h2>`，按 `report-template.html` 占位符填）
3. 两者都不行 → 只产出 MD，报告摘要标注"HTML 生成失败，已降级为 MD only"

**同日重跑**：`test-report-YYYYMMDD.md` 已存在 → 追加序号 `-2.md` / `-3.md`

**向用户展示（最终摘要）**：
```
✅ 测试报告已生成

📊 质量结论：🟢/🟡/🔴 + 判定依据
📈 三元通过率：AI {X%} / 人工 {Y%} / 总 {Z%}
🐛 开放缺陷：Fatal {a} / Critical {b} / Major {c}
📁 报告文件：
  - MD: {path}
  - HTML: {path}  ← 如有
⚠️ 风险摘要：{高风险项简述}
📋 需求覆盖率：P0 测试点覆盖 {N%}，未覆盖 {M} 个（若有 test-points）
💡 数据源：{defect_source}
```

---

## 验收标准

### 数据准确性
- [ ] 三元通过率各自分母正确（不含暂缓/阻塞）
- [ ] P0 人工执行时结论标注 ⚠️
- [ ] 覆盖矩阵每个测试点有状态标识（🟢🔴🟡⚪）
- [ ] 缺陷源标注明确（yunxiao/markdown/empty + 降级原因）

### 报告完整性
- [ ] MD 报告已写入 `report/test-report-YYYYMMDD.md`
- [ ] `--format=html` 时 HTML 同名同目录
- [ ] 必含章节：质量结论 / 三元通过率 / 模块×优先级透视 / 需求覆盖矩阵（如有）/ 失败明细 / 缺陷汇总 / 风险项 / 后续建议
- [ ] 失败用例有 execution_report 锚点链接
- [ ] 成功用例**不内嵌截图**，指向执行报告

### 职责边界
- [ ] 报告不含新缺陷登记指令
- [ ] 报告不含发布决策
- [ ] 报告不修改用例文件
- [ ] 识别越界请求时明确提示对应 skill

### 自动化兜底
- [ ] Phase 0.5 adapter 失败时自动降级，不阻断
- [ ] Phase 4 HTML 生成失败时自动降级为 MD only
- [ ] 同日重跑自动加序号

---

## 与其他 Skill 的衔接

| 上游 Skill | 提供 | 说明 |
|---|---|---|
| `test-execution` | UI 执行报告 | 主数据源 |
| `api-test-execution` | 接口执行报告 | 主数据源 |
| `bug-sync` | 缺陷清单 | Markdown adapter 的源 |
| `test-point-extraction` | `review/test-points.md` | 需求覆盖矩阵 |

| 下游 Skill | 触发条件 | 说明 |
|---|---|---|
| `release-gate` | 质量结论 🟢 或 🟡 | 发布二元判定，**复用** `quality-rules.md` |
| 重新执行测试 | 质量结论 🔴 | 由用户手动触发 `test-execution` 等 |

---

## 跨 skill 共享说明

**`references/quality-rules.md`** 是**唯一权威**判定规则源。任何 skill（`release-gate` / `submission-gate` 等）的判定阈值改动，**只改此文件**，不在各 skill 内重复定义。

引用方式（其他 skill 在 SKILL 或 OVERRIDES 里写）：
```
本 skill 的质量判定沿用 `.claude/skills/test-report/references/quality-rules.md`，避免阈值漂移。
```

---

*版本：v2.0（本地定制）| 上次更新：2026-04-23*
