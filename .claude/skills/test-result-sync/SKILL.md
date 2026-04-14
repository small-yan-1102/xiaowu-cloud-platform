---
name: test-result-sync
description: 将AI直接执行测试的结果回填到Excel或Markdown测试用例文档，生成执行统计报告（通过率/覆盖率）。仅处理本地执行结果，不查询缺陷数据。适用场景：同步测试结果、回填Excel、更新用例状态。如需生成包含缺陷分析的综合测试报告，请使用 test-report（在本技能完成后运行）。
version: 2.0.0
triggers:
  - "同步测试结果"
  - "回填测试结果"
  - "更新用例状态"
  - "统计覆盖率"
  - "回填Excel"
  - "结果同步"
  - "测试结果汇总"
---

# 测试结果回填技能

> **版本**: v2.0
> **更新日期**: 2026-04-02
> **适用模式**: Tool Wrapper Pattern — 解析 AI 执行报告 → 回填到 Markdown/Excel → 生成统计报告

---

## 附属资源文件

| 文件 | 路径 | 说明 |
|------|------|------|
| 执行报告格式规范 | `assets/execution-report-format.md` | AI 执行报告输入格式 + 回填格式 + 统计报告格式 + Excel 约定，Phase 1 解析和 Phase 3 输出时加载 |

---

## 核心工作流

```
Task Progress:
- [ ] Phase 0: 定向收集（Inversion）
- [ ] Phase 1: 解析 AI 执行报告
- [ ] Phase 2: 执行回填操作
- [ ] Phase 3: 输出统计报告
```

---

### Phase 0: 定向收集

**目标**：在任何操作开始前，确认执行报告路径和回填目标。

向用户提出以下问题，**等待用户回答后再进行任何操作**：

1. **执行报告路径**：AI 执行报告文件路径是什么？（默认：`test_reports/test_report_*.md`，取最新一份；线上回归默认：`test_reports/prod_regression_report_*.md`）
2. **回填目标**：需要回填到 Markdown 用例文档、Excel 文件，还是两者都要？
3. **目标文件路径**：
   - Markdown 用例文档路径是什么（默认：`test_suites/*.md`）？
   - Excel 文件路径是什么（如需回填 Excel）？
   - Excel 的结果列标识是什么（默认：G 列）？

> ⛔ **DO NOT** 读取任何文件，**DO NOT** 开始任何操作，直到用户回答上述问题。

将用户的回答记录为**定向上下文**，在后续所有 Phase 中使用。

**决策点**：
- 用户已回答 → 进入 Phase 1
- 用户表示"按默认来" → 使用默认路径，进入 Phase 1

---

### Phase 1: 解析 AI 执行报告

**目标**：读取执行报告，提取每条用例的执行结果。

**步骤**：

1. **读取执行报告格式规范**：加载 `assets/execution-report-format.md`，确认输入格式

2. **读取 AI 执行报告文件**

3. **按规范解析结果表格**：
   - 提取字段：用例编号（`PRJ-XXX-NNN` 或 `SMOKE-XXX-NNN`）、用例名称、结果（通过/失败/跳过）、耗时、备注
   - 提取失败详情：失败步骤、期望结果、实际结果

4. **构建结果映射表**：`{ 用例编号: { status, duration, note, failDetail } }`

5. **输出解析摘要**：共解析 N 条结果（通过 X / 失败 Y / 跳过 Z）

> ⛔ **DO NOT** 进入 Phase 2，直到执行报告已完整解析并输出摘要。

---

### Phase 2: 执行回填操作

**目标**：将解析结果回填到目标文件。

#### 回填到 Markdown 用例文档

```python
import re
from datetime import datetime

def sync_ai_results_to_markdown(report_path: str, case_doc_path: str):
    """
    将 AI 执行报告中的结果回填到 Markdown 用例文档

    Args:
        report_path: AI 执行报告文件路径
        case_doc_path: 测试用例 Markdown 文件路径
    """
    results = parse_ai_report(report_path)
    
    with open(case_doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for case_id, result in results.items():
        status_map = {'通过': 'PASS', '失败': 'FAIL', '跳过': 'SKIP', '阻塞': 'BLOCKED', '人工执行': 'MANUAL'}
        status_badge = status_map.get(result['status'], result['status'])
        pattern = rf'(### {re.escape(case_id)}\s+.+?)(\s+【[A-Z]+\s+\d{{4}}-\d{{2}}-\d{{2}}】)?(\n)'
        replacement = rf'\1 【{status_badge} {datetime.now().strftime("%Y-%m-%d")}】\3'
        content = re.sub(pattern, replacement, content)
    
    with open(case_doc_path, 'w', encoding='utf-8') as f:
        f.write(content)

def parse_ai_report(report_path: str) -> dict:
    """
    解析 AI 执行报告

    Args:
        report_path: 报告文件路径

    Returns:
        dict: {用例编号: {status, duration, note}}
    """
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    results = {}
    row_pattern = r'\|\s*((?:PRJ|SMOKE|PROD)-[\w-]+)\s*\|\s*(.+?)\s*\|\s*(通过|失败|跳过|阻塞|人工执行)\s*\|\s*(.+?)\s*\|\s*(.*?)\s*\|'
    for match in re.finditer(row_pattern, content):
        case_id = match.group(1)
        results[case_id] = {
            'name': match.group(2).strip(),
            'status': match.group(3),
            'duration': match.group(4).strip(),
            'note': match.group(5).strip()
        }
    
    return results
```

#### 回填到 Excel

```python
import openpyxl
from datetime import datetime

def sync_ai_results_to_excel(report_path: str, excel_path: str, result_column: str = 'G'):
    """
    将 AI 执行报告中的结果回填到 Excel 用例文档

    Args:
        report_path: AI 执行报告文件路径
        excel_path: Excel 文件路径
        result_column: 结果列标识（默认 G 列）
    """
    results = parse_ai_report(report_path)
    
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    
    id_col = find_case_id_column(ws)
    if not id_col:
        raise ValueError("未找到用例ID列（第1行需包含含'用例'和'ID'的列头）")
    
    result_col = openpyxl.utils.column_index_from_string(result_column)
    
    for row in range(2, ws.max_row + 1):
        case_id = ws.cell(row=row, column=id_col).value
        if case_id and case_id in results:
            ws.cell(row=row, column=result_col).value = results[case_id]['status']
    
    wb.save(excel_path)

def find_case_id_column(ws) -> int:
    """
    自动识别用例ID列：第1行匹配以下任一列头变体（不区分大小写）
    支持：用例ID / 用例号 / 用例编号 / 测试用例号 / Case ID / CaseID / TestCase
    """
    CASE_ID_PATTERNS = [
        lambda h: '用例' in h and ('id' in h.lower() or '号' in h or '编号' in h),
        lambda h: 'case' in h.lower() and ('id' in h.lower() or 'no' in h.lower()),
        lambda h: 'testcase' in h.lower().replace(' ', ''),
    ]
    candidates = []
    for col in range(1, ws.max_column + 1):
        header = ws.cell(row=1, column=col).value
        if header:
            h = str(header).strip()
            if any(pattern(h) for pattern in CASE_ID_PATTERNS):
                candidates.append((col, h))
    if len(candidates) == 1:
        return candidates[0][0]
    if len(candidates) > 1:
        # 优先精确匹配"用例ID"，其次取第一个候选
        for col, h in candidates:
            if h in ('用例ID', '用例编号', 'Case ID'):
                return col
        return candidates[0][0]
    return None
```

> ⛔ **DO NOT** 进入 Phase 3，直到所有目标文件均已回填完毕。

---

### Phase 3: 输出统计报告

**目标**：汇总执行结果，生成可读的统计报告。

**步骤**：

1. **读取执行报告格式规范**中的统计报告格式

2. **计算统计数据**：

```python
def generate_statistics(results: dict) -> dict:
    """
    生成测试统计

    Args:
        results: 测试结果字典

    Returns:
        dict: 统计数据
    """
    total = len(results)
    passed = sum(1 for r in results.values() if r['status'] == '通过')
    failed = sum(1 for r in results.values() if r['status'] == '失败')
    skipped = sum(1 for r in results.values() if r['status'] == '跳过')
    blocked = sum(1 for r in results.values() if r['status'] == '阻塞')
    manual = sum(1 for r in results.values() if r['status'] == '人工执行')
    ai_executed = total - manual - skipped  # 人工执行和跳过用例均不计入 AI 通过率分母
    # SKIP 处理规则：跳过用例不计入通过率分母，在统计报告中单独列出跳过原因分布
    
    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'blocked': blocked,
        'manual': manual,
        'pass_rate': f"{passed/ai_executed*100:.1f}%" if ai_executed > 0 else "N/A",
        'fail_rate': f"{failed/ai_executed*100:.1f}%" if ai_executed > 0 else "N/A",
    }
```

3. **按统计报告格式输出**（参照 `assets/execution-report-format.md` §三）

4. **将统计报告写入文件**：`test_suites/execution-report-{YYYY-MM-DD}-{HHmmss}.md`

5. **向用户展示**：回填路径 + 统计摘要 + 失败用例列表

---

## 扩展：同步结果到云效测试计划

> 本节为**手动触发**的可选操作，不属于核心工作流。

当需要将测试执行结果回写到云效 Testhub 测试计划（而非仅回填本地文件）时，可使用共享工具库中的同步脚本。

**工具路径**：`tools/yunxiao/scripts/sync_test_results.py`

**前置条件**：
1. `tools/yunxiao/config.yaml` 已配置云效认证信息（PAT、organization_id）
2. `tools/yunxiao/sync_state.json` 中已有用例的云效 ID 映射（由 `main.py` 同步用例后自动生成）
3. 需在脚本中指定目标测试计划 ID

**使用方式**：

```bash
cd tools/yunxiao/scripts
python sync_test_results.py
```

**详细说明**：参见 `tools/yunxiao/README.md`

> 此工具当前为脚本级集成（需手动编辑脚本中的测试计划 ID 和结果映射），尚未与本 Skill 的 Phase 1-3 自动化流程直接打通。

---

## 与 test-report 的职责边界

| 职责 | test-result-sync | test-report |
|------|-----------------|-------------|
| 数据来源 | 本地 AI 执行报告（Markdown） | 本地执行报告 + 云效缺陷（实时查询） |
| 缺陷数据 | **不处理** | 通过 `query_defects.py` 从云效实时获取 |
| 输出产物 | 执行统计报告（通过率/覆盖率）+ 回填文件 | 综合测试报告（含缺陷分布/质量结论） |
| 运行时机 | 测试执行完成后立即运行 | test-result-sync 完成后运行 |
| 下游 | test-report | release-gate |

**推荐执行顺序**：
```
测试执行完成
  → test-result-sync（回填结果 + 执行统计）
    → test-report（读取执行统计 + 查询缺陷 + 生成综合报告）
      → release-gate（发布决策）
```

---

## 验收标准

### 回填完整性

- [ ] Markdown 用例文档中所有匹配用例编号均已标注执行状态
- [ ] Excel 文件中所有匹配用例编号的结果列均已填写
- [ ] 重复执行时覆盖旧状态标记（不产生重复标记）

### 统计准确性

- [ ] 总用例数 = 通过 + 失败 + 跳过 + 阻塞 + 人工执行
- [ ] 人工执行用例已识别并标记为 `MANUAL`，不丢失
- [ ] 通过率、失败率以 AI 执行用例数（总数 - 人工执行数）为分母
- [ ] 失败用例详情已在统计报告中列出

### 输出完整性

- [ ] 统计报告已写入正确路径
- [ ] 统计报告包含执行时间、环境信息、统计数字、失败用例列表
