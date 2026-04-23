# 测试报告

> **本文件是 `test-report` skill v2.0 的权威输出模板**。
> Phase 3 按此模板逐节填充占位符 `{...}`，可选章节按条件保留/删除。
> 修改报告格式 → 只改此文件，SKILL.md 不重复定义结构。

---

<!-- 以下为报告正文（从占位符开始）-->

# 测试报告

| 项目 | 内容 |
|---|---|
| **版本 / 迭代** | {version} |
| **测试周期** | {start_date} ~ {end_date} |
| **测试环境** | {env_urls} |
| **报告生成时间** | {timestamp} |
| **执行方式** | AI 自动执行 {ai_count} 条 + 人工执行 {manual_count} 条 |
| **缺陷数据来源** | {defect_source} {defect_source_note} |
| **关联 PRD** | {prd_link} |

---

## 一、质量结论

> ## {conclusion_emoji} {conclusion_text}

**判定依据**：{conclusion_rationale}

{p0_manual_warning}

---

## 二、执行结果汇总

### 2.1 三元通过率

| 口径 | 通过 | 已执行 | 通过率 |
|---|---|---|---|
| AI | {ai_pass} | {ai_exec} | {ai_rate} |
| 人工 | {manual_pass} | {manual_exec} | {manual_rate} |
| **总计** | **{total_pass}** | **{total_exec}** | **{total_rate}** ← 判定基准 |

> **分母定义**：已执行 = 总执行数 - 暂缓 - 阻塞。

**关键口径**：

| 指标 | 数值 |
|---|---|
| 用例总数 | {total_cases}（可执行 {executable} + 暂缓 {deferred}） |
| ✅ 通过 | {total_pass}（{total_rate}） |
| ⚠️ 部分通过 | {partial} |
| ❌ 失败 | {failed} |
| 🚫 阻塞 | {blocked} |
| ⏭ 暂缓 | {deferred} |
| L2 警告 | {l2_warnings} |
| **P0 通过率** | {p0_rate}（{p0_pass}/{p0_exec}） |
| **P0+P1 通过率** | {p01_rate}（{p01_pass}/{p01_exec}） |

### 2.2 模块 × 优先级透视

| 模块 \ 优先级 | P0 | P1 | P2 | P3 | 合计 | 通过率 | 风险 |
|---|---|---|---|---|---|---|---|
{matrix_rows}
| **合计** | {total_p0} | {total_p1} | {total_p2} | {total_p3} | **{grand_total}** | **{grand_rate}** | {overall_risk} |

> **风险等级**：≥95% 🟢 / 90-94% 🟡 / <90% 🔴

### 2.3 暂缓用例列表

{deferred_table}

---

<!-- OPTIONAL: when review/test-points.md exists -->
## 三、需求覆盖矩阵

基于 [test-points.md](../review/test-points.md) 聚合：

### 3.1 总览

| PRD 模块 | 测试点数 | 关联用例数 | 🟢 已覆盖 | 🔴 覆盖但失败 | 🟡 覆盖未验证 | ⚪ 未关联 | 覆盖率 |
|---|---|---|---|---|---|---|---|
{coverage_summary_rows}
| **合计** | **{tp_total}** | **{case_total}** | **{green}** | **{red}** | **{yellow}** | **{gray}** | **{coverage_rate}** |

### 3.2 关键指标

- **P0 测试点覆盖率**：{p0_coverage}（{p0_covered}/{p0_total}）
- **覆盖缺口**：{gap_count} 个测试点未关联用例 {gap_note}

### 3.3 测试点明细（仅列有问题的）

> 仅展示 🔴/🟡/⚪ 状态的测试点。全 🟢 状态不展开。

| 测试点 | 所属模块 | 优先级 | 状态 | 关联用例 | 说明 |
|---|---|---|---|---|---|
{coverage_problem_rows}

<!-- /OPTIONAL -->

---

## 四、缺陷汇总

### 4.1 缺陷分布

| 严重等级 | 总数 | 开放 | 已关闭 |
|---|---|---|---|
| 致命（Fatal） | {fatal_total} | {fatal_open} | {fatal_closed} |
| 严重（Critical） | {critical_total} | {critical_open} | {critical_closed} |
| 一般（Major） | {major_total} | {major_open} | {major_closed} |
| 轻微（Minor） | {minor_total} | {minor_open} | {minor_closed} |
| 环境阻塞 | {env_block_total} | — | — |
| **合计** | **{defect_total}** | **{defect_open}** | **{defect_closed}** |

### 4.2 关键指标

| 指标 | 数值 |
|---|---|
| 缺陷密度 | {defect_density} |
| 严重缺陷率 | {critical_rate} |
| 缺陷修复率 | {fix_rate} |

### 4.3 开放缺陷详情

{open_defects_table}

---

## 五、失败与部分通过用例

### ❌ 失败用例（{fail_count} 条）

{failed_cases_table}

### ⚠️ 部分通过用例（{partial_count} 条）

{partial_cases_table}

### ✅ 成功用例归集

> 详情见各套件执行报告，本节不展开以避免冗余：

{success_by_suite}

---

## 六、风险项与建议

### 高风险项

{high_risk_items}

### 中风险项

{medium_risk_items}

### 需复测项

{recheck_items}

---

## 七、后续建议

{next_steps_by_conclusion}

---

## 附录 A：执行报告引用

{execution_report_links}

## 附录 B：执行脚本清单

{scripts_list}

## 附录 C：数据源说明

- **缺陷数据来源**：{defect_source_detail}
- **执行报告来源**：{exec_reports_summary}
- **测试点清单**：{test_points_source}
- **降级记录**（如有）：{fallback_notes}

---

**报告生成时间**：{timestamp}
**报告生成 Skill**：`test-report` v2.0（本地定制）

<!-- ======================================================= -->
<!-- 占位符填充规范（Phase 3 AI 依据）                        -->
<!-- ======================================================= -->
<!--
【顶级字段】
  {version} - 版本号 / 迭代名称，如 "结算系统 V4.5 · 2026-Q2 逾期结算处理优化"
  {start_date} / {end_date} - YYYY-MM-DD
  {env_urls} - 逗号分隔的环境基础 URL
  {timestamp} - YYYY-MM-DD HH:mm:ss
  {ai_count} / {manual_count} - 执行方式分布
  {defect_source} - "yunxiao" / "markdown" / "empty"
  {defect_source_note} - 降级时写原因，如 "（云效 API 不可达，降级到 Markdown）"
  {prd_link} - [PRD 文档]{path} 或 "-"

【质量结论】
  {conclusion_emoji} - 🟢 / 🟡 / 🔴
  {conclusion_text} - 一句话结论，如 "质量良好，可进入发布流程"
  {conclusion_rationale} - 一句话判定依据
  {p0_manual_warning} - P0 人工执行时追加 "> ⚠️ 含 {N} 条 P0 人工执行用例，需测试工程师确认已人工验证"；否则留空

【三元通过率】
  通过率保留 2 位百分比，如 "98.99%"

【模块 × 优先级透视】
  {matrix_rows} 每行格式：
    | {套件名} | {p0_pass}/{p0_exec} | {p1_pass}/{p1_exec} | ... | {rate} | {risk_emoji} |
  单元格若无用例填 "0" 或 "-"

【需求覆盖矩阵】
  仅当 review/test-points.md 存在时保留；否则删除整个 <!-- OPTIONAL --> 区块
  {gap_note} - 缺口非零时 "（建议由 test-case-design 补充用例）"

【缺陷】
  空缺陷集时 {defect_total} 写 0，{open_defects_table} 写 "> 本轮无缺陷登记记录"

【失败/部分通过】
  表格格式：
    | 用例编号 | 模块 | 优先级 | 失败点摘要 | 关联缺陷 | 详情 |
    | {id} | {module} | P{n} | {一句话} | {bug_id} / "—" | [execution_report#{anchor}]({path}) |
  无失败/部分通过时写 "> 无"

【成功用例归集】
  按套件列出：
    - {套件名}：{pass_count} 条，详见 [execution_report_{date}.md]({path})

【风险项】
  高/中/无时写 "> 无"

【后续建议】
  按 quality-rules.md §后续建议 的模板选择：
    - 🟢 → "进入 release-gate 发布门禁检查"
    - 🟡 → "确认 Open Critical 影响范围，与产品/开发决策后再 release-gate"
    - 🔴 → "修复高风险项 → 重新执行 → bug-sync → 重新生成报告"

【附录 B 脚本清单】
  {scripts_list} 格式：
    | 脚本 | 用途 |
    | {filename} | {description} |
  无脚本时写 "> 本轮未使用独立脚本（见执行报告内嵌命令）"
-->
