"""
一次性迁移脚本：
1. 删除套件「执行顺序」表最右侧的「执行记录」列
2. 把文件内「执行清单（人工勾选）」段重命名为「执行清单（状态记录入口）」
3. 替换操作说明 blockquote 为新版（含 AI 回写格式）

执行一次后可保留，或移入 scripts/archive/。
"""
import re
from pathlib import Path

BASE = Path(r"e:\Orange\小五云平台")
SUITE_FILES = [
    BASE / "iterations/2026-Q2_结算系统_逾期结算处理优化/testcase/suite_smoke.md",
    BASE / "iterations/2026-Q2_结算系统_逾期结算处理优化/testcase/suite_set01_status_dispatch.md",
    BASE / "iterations/2026-Q2_结算系统_逾期结算处理优化/testcase/suite_set02_settlement.md",
    BASE / "iterations/2026-Q2_结算系统_逾期结算处理优化/testcase/suite_set04_tag.md",
    BASE / "iterations/2026-Q2_结算系统_逾期结算处理优化/testcase/suite_e2e.md",
    BASE / "iterations/2026-Q2_结算系统_逾期结算处理优化/testcase/api_suite_set03_import_validation.md",
]

OLD_BLOCKQUOTE_PATTERN = re.compile(
    r"## 执行清单(?:（人工勾选）|（状态记录入口）)\n\n"
    r"> \*\*操作说明\*\*：\n"
    r"(?:>.*\n)+",
    re.MULTILINE
)

NEW_HEADER_AND_BLOCKQUOTE = (
    "## 执行清单（状态记录入口）\n\n"
    "> **操作说明**：\n"
    "> - **人工**：鼠标点击 `- [ ]` 切换为 `- [x]` 表示**执行通过**；失败/阻塞/跳过**不勾选**，行尾追加 ` · ❌ BUG-{id}` / ` · 🚫 {原因}` / ` · ⏭ {原因}`\n"
    "> - **AI（test-execution / api-test-execution）**：执行完成后自动勾选并追加 ` · ✅ AI {日期} · [报告](...)` 或 ` · ❌ AI {日期} · [失败详情](...)`\n"
    "> - **真源定位**：本清单为**进度真源**；完整执行证据（步骤/断言/截图/堆栈）在 `execution/execution_report_*.md`\n"
)


def strip_last_column_from_exec_order_table(content: str) -> str:
    """
    仅对「执行顺序」表格删除最右列 `| 执行记录 |`。
    识别方式：找到 "## 执行顺序" 后的第一个 Markdown 表格块。
    """
    lines = content.split("\n")
    in_target_section = False
    in_target_table = False
    passed_separator = False

    for i, line in enumerate(lines):
        if line.startswith("## ") and "执行顺序" in line:
            in_target_section = True
            in_target_table = False
            passed_separator = False
            continue
        if in_target_section and line.startswith("## "):
            # 进入下一段（清单段或用例段），停止处理表
            in_target_section = False
            in_target_table = False
            continue
        if not in_target_section:
            continue

        stripped = line.strip()
        # 表头/分隔/数据行（全部以 | 开头、以 | 结尾）
        if stripped.startswith("|") and stripped.endswith("|"):
            if not in_target_table:
                # 找到表头
                in_target_table = True
                passed_separator = False
            # 去掉最右一列
            # 以 | 分隔后，去掉最右一个数据段
            parts = line.rstrip().split("|")
            # parts[0]='' 头, parts[-1]='' 尾, 中间为各单元格
            if len(parts) >= 4:  # 至少 2 列
                new_parts = parts[:-2] + [""]  # 去掉倒数第二个数据段
                lines[i] = "|".join(new_parts)
        else:
            # 非表格行（空行/文字）
            if in_target_table and stripped == "":
                # 表结束
                in_target_table = False
            # 继续扫到下一个 ## 段停止

    return "\n".join(lines)


def upgrade_checklist_blockquote(content: str) -> str:
    """
    替换「执行清单」段的标题 + 操作说明 blockquote。
    保留后续用例勾选行不动。
    """
    m = OLD_BLOCKQUOTE_PATTERN.search(content)
    if not m:
        return content
    return content[: m.start()] + NEW_HEADER_AND_BLOCKQUOTE + content[m.end():]


def main():
    for f in SUITE_FILES:
        if not f.exists():
            print(f"[SKIP] 文件不存在: {f}")
            continue
        original = f.read_text(encoding="utf-8")
        step1 = strip_last_column_from_exec_order_table(original)
        step2 = upgrade_checklist_blockquote(step1)
        if step2 == original:
            print(f"[NOCHG] {f.name}")
        else:
            f.write_text(step2, encoding="utf-8")
            print(f"[WROTE] {f.name}")


if __name__ == "__main__":
    main()
