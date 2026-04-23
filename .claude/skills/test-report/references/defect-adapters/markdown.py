#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown Defect Source Adapter

从本地 Markdown 缺陷清单文件扫描缺陷数据（降级兜底或小项目主选）。
契约见同目录 `_interface.md`。

扫描路径：
  1. 命令参数 `--path <glob>` 指定
  2. 默认扫 `iterations/*/review/bug_reports/bug-report-*.md`（最新迭代优先）
  3. 退化扫 `iterations/*/review/bugs/*.md`

支持的 Markdown 缺陷文件格式（宽松匹配）：
  ---
  id: BUG-001
  severity: critical | major | minor | fatal
  status: open | closed | resolved
  title: 标题
  related_cases: [CASE-1, CASE-2]
  ---

  正文...

或表格形式：
  | ID | 严重等级 | 状态 | 标题 | 关联用例 |
  |---|---|---|---|---|
  | BUG-001 | critical | open | xxx | CASE-1 |

用法:
  python markdown.py --json
  python markdown.py --json --path "iterations/2026-Q2_*/review/bug_reports/*.md"
  python markdown.py --selftest
"""
import sys
import os
import io
import json
import re
import glob
from datetime import datetime, timezone
from pathlib import Path

# Windows 下强制 UTF-8 输出（契约要求）
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ============================================================
# 路径
# ============================================================

ADAPTER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADAPTER_DIR.parents[4]


# ============================================================
# 自检
# ============================================================

def selftest():
    """检查是否有可扫描的缺陷文件"""
    # markdown adapter 依赖极少（只需 Python 标准库）
    # 若找不到任何缺陷文件 → 返回 0（仍可用，空数据集）
    # 若扫描路径完全错误 → 返回 2
    try:
        _find_bug_files()
        return 0
    except Exception:
        return 2


# ============================================================
# 扫描缺陷文件
# ============================================================

def _find_bug_files(custom_path=None):
    """按优先级查找缺陷文件"""
    patterns = []
    if custom_path:
        patterns.append(custom_path)
    else:
        # 默认扫当前项目
        patterns.extend([
            str(PROJECT_ROOT / 'iterations/*/review/bug_reports/bug-report-*.md'),
            str(PROJECT_ROOT / 'iterations/*/review/bugs/*.md'),
            str(PROJECT_ROOT / 'iterations/*/review/bug-*.md'),
        ])

    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))

    # 去重 + 按修改时间倒序（最新在前）
    files = list(set(files))
    files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return files


# ============================================================
# 解析单个缺陷文件
# ============================================================

# 严重等级归一化
SEVERITY_MAP = {
    # 英文
    'fatal': 'fatal', 'blocker': 'fatal',
    'critical': 'critical',
    'major': 'major',
    'minor': 'minor', 'trivial': 'minor',
    'env_block': 'env_block', 'env-block': 'env_block',
    # 中文
    '致命': 'fatal', '阻断': 'fatal',
    '严重': 'critical',
    '一般': 'major', '主要': 'major',
    '轻微': 'minor', '次要': 'minor',
    '环境阻塞': 'env_block',
}


def normalize_severity(raw):
    if not raw:
        return 'minor'  # 默认当 minor
    key = str(raw).strip().lower()
    for k, v in SEVERITY_MAP.items():
        if k.lower() == key or k in raw:
            return v
    return 'minor'


# 状态归一化
CLOSED_KEYWORDS = {'closed', 'resolved', 'fixed', 'done', '已关闭', '已解决', '已修复'}


def is_closed(status):
    if not status:
        return False
    return str(status).strip().lower() in CLOSED_KEYWORDS


def parse_frontmatter(text):
    """解析 YAML frontmatter，返回 dict 或 None"""
    m = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return None
    try:
        import yaml
        return yaml.safe_load(m.group(1)) or {}
    except ImportError:
        # 简单兜底解析
        result = {}
        for line in m.group(1).splitlines():
            ln = re.match(r'^(\w+)\s*:\s*(.*?)\s*$', line)
            if ln:
                result[ln.group(1)] = ln.group(2).strip().strip('"\'')
        return result


def parse_table_rows(text):
    """从 Markdown 表格解析缺陷行（非 frontmatter 格式）"""
    bugs = []
    # 匹配带 BUG/DEFECT 前缀的行
    table_rows = re.findall(
        r'\|\s*(BUG-\S+|DEFECT-\S+)\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*([^|]+?)\s*\|(?:[^|]*?\|)?',
        text,
    )
    for row in table_rows:
        bug_id, severity, status, title = row[0], row[1], row[2], row[3].strip()
        bugs.append({
            'id': bug_id.strip(),
            'severity': normalize_severity(severity),
            'status': 'closed' if is_closed(status) else 'open',
            'title': title,
            'related_cases': [],
        })
    return bugs


def parse_bug_file(filepath):
    """解析一个 bug 文件，返回缺陷列表"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return []

    # 尝试 frontmatter 格式
    fm = parse_frontmatter(text)
    if fm and ('id' in fm or 'ID' in fm):
        bug_id = fm.get('id') or fm.get('ID', '')
        related = fm.get('related_cases') or fm.get('related_case') or []
        if isinstance(related, str):
            related = [c.strip() for c in related.split(',') if c.strip()]
        return [{
            'id': str(bug_id).strip(),
            'severity': normalize_severity(fm.get('severity', '')),
            'status': 'closed' if is_closed(fm.get('status', '')) else 'open',
            'title': str(fm.get('title', '') or '').strip(),
            'related_cases': related if isinstance(related, list) else [],
        }]

    # 否则尝试表格格式
    return parse_table_rows(text)


# ============================================================
# 聚合
# ============================================================

def aggregate(all_bugs):
    by_severity = {
        'fatal':     {'open': 0, 'closed': 0},
        'critical':  {'open': 0, 'closed': 0},
        'major':     {'open': 0, 'closed': 0},
        'minor':     {'open': 0, 'closed': 0},
        'env_block': {'open': 0},
    }
    case_mapping = {}
    open_defects = []

    for bug in all_bugs:
        sev = bug['severity']
        if sev not in by_severity:
            sev = 'minor'
        is_closed_ = bug['status'] == 'closed'
        if is_closed_:
            if 'closed' in by_severity[sev]:
                by_severity[sev]['closed'] += 1
        else:
            by_severity[sev]['open'] += 1
            open_defects.append({
                'id': bug['id'],
                'title': bug['title'],
                'severity': sev,
                'status': 'open',
            })

        if bug['related_cases']:
            case_mapping[bug['id']] = bug['related_cases']

    return by_severity, case_mapping, open_defects


# ============================================================
# 主入口
# ============================================================

def query(sprint_id=None, custom_path=None):
    files = _find_bug_files(custom_path)

    all_bugs = []
    notes_parts = []
    for fp in files:
        parsed = parse_bug_file(fp)
        all_bugs.extend(parsed)

    by_severity, case_mapping, open_defects = aggregate(all_bugs)
    total = sum(
        (v.get('open', 0) + v.get('closed', 0))
        for v in by_severity.values()
    )

    if not files:
        notes_parts.append('未找到任何缺陷清单文件（按默认路径扫描）')
    else:
        notes_parts.append(f'已扫描 {len(files)} 个缺陷清单文件')

    return {
        'source': 'markdown',
        'query_time': datetime.now(timezone.utc).isoformat(),
        'sprint_id': sprint_id,
        'total': total,
        'by_severity': by_severity,
        'case_mapping': case_mapping,
        'open_defects': open_defects,
        'notes': '; '.join(notes_parts) if notes_parts else None,
    }


def main():
    if '--selftest' in sys.argv:
        sys.exit(selftest())

    sprint_id = None
    custom_path = None
    if '--sprint-id' in sys.argv:
        i = sys.argv.index('--sprint-id')
        if i + 1 < len(sys.argv):
            sprint_id = sys.argv[i + 1]
    if '--path' in sys.argv:
        i = sys.argv.index('--path')
        if i + 1 < len(sys.argv):
            custom_path = sys.argv[i + 1]

    try:
        result = query(sprint_id, custom_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f'Error: {e}\n')
        sys.exit(4)


if __name__ == '__main__':
    main()
