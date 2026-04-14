# -*- coding: utf-8 -*-
"""
云效缺陷状态查询工具 - 从云效 Projex 查询缺陷工作项的当前状态

查询指定迭代（或全项目）下的 Bug 工作项，按严重等级统计开放/已关闭数量，
输出 JSON 供 test-report skill 等工具消费，同时支持人类可读的控制台输出。
也支持按状态筛选，列出待回归验证的已解决缺陷（供 defect-retest skill 使用）。

API 调用链路:
  POST /oapi/v1/projex/organizations/{orgId}/workitems:search   - 搜索工作项
  GET  /oapi/v1/projex/organizations/{orgId}/projects/{id}/workitemTypes/{typeId}/fields
                                                                  - 查询严重等级选项映射

使用方式:
  # 查询全部迭代（JSON 聚合统计）
  python query_defects.py --json

  # 查询指定迭代
  python query_defects.py --sprint-id <sprint_id>

  # 列出所有已解决（待回归）的缺陷明细
  python query_defects.py --list-resolved --json

  # 按任意状态筛选并列出明细
  python query_defects.py --list-items --filter-status 处理中 --json

  # 人类可读输出
  python query_defects.py

  # 模拟模式
  python query_defects.py --dry-run
"""

import os
import re
import sys
import json
import time
import argparse
import requests
import yaml
from typing import Dict, List, Optional, Tuple


# ============================================================
# 配置加载（与 create_defect.py 保持一致）
# ============================================================

def load_config(config_path: str = "") -> dict:
    """加载云效配置文件

    Args:
        config_path: 配置文件路径（为空时使用默认路径）

    Returns:
        dict: 包含 yunxiao 和 projex 配置的字典
    """
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    config_path = os.path.abspath(config_path)

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    yunxiao = data.get('yunxiao', {})
    projex = data.get('projex', {})

    # 环境变量覆盖
    yunxiao['personal_access_token'] = os.environ.get(
        'YUNXIAO_PAT', yunxiao.get('personal_access_token', '')
    )
    yunxiao['organization_id'] = os.environ.get(
        'YUNXIAO_ORG_ID', yunxiao.get('organization_id', '')
    )
    yunxiao['domain'] = yunxiao.get('domain', 'openapi-rdc.aliyuncs.com')

    return {'yunxiao': yunxiao, 'projex': projex}


def validate_config(config: dict) -> List[str]:
    """校验查询所需的必填配置

    Args:
        config: 配置字典

    Returns:
        list[str]: 错误信息列表（空列表表示通过）
    """
    errors = []
    yunxiao = config.get('yunxiao', {})
    projex = config.get('projex', {})

    if not yunxiao.get('personal_access_token'):
        errors.append("缺少 personal_access_token（PAT）")
    if not yunxiao.get('organization_id'):
        errors.append("缺少 organization_id（组织 ID）")
    if not projex.get('project_id'):
        errors.append("缺少 projex.project_id（Projex 项目 ID）")

    return errors


def _build_projex_base(config: dict) -> Tuple[str, dict]:
    """构建 Projex API 基础 URL 和认证请求头

    Args:
        config: 云效配置字典

    Returns:
        tuple: (base_url, headers)
    """
    yunxiao = config['yunxiao']
    domain = yunxiao['domain'].rstrip('/')
    if not domain.startswith('http'):
        domain = f"https://{domain}"
    org_id = yunxiao['organization_id']

    base_url = f"{domain}/oapi/v1/projex/organizations/{org_id}"
    headers = {
        'Content-Type': 'application/json',
        'x-yunxiao-token': yunxiao['personal_access_token'],
    }
    return base_url, headers


# ============================================================
# 严重等级选项映射（option_id -> 显示名称）
# ============================================================

# 默认严重等级文本 -> 标准名称映射（处理中英文、全角半角等差异）
_SEVERITY_NORMALIZE = {
    # 致命
    '致命': 'Fatal', 'fatal': 'Fatal', 'blocker': 'Fatal', 'p0': 'Fatal',
    # 严重
    '严重': 'Critical', 'critical': 'Critical', 'serious': 'Critical', 'p1': 'Critical',
    # 一般
    '一般': 'Major', 'major': 'Major', 'normal': 'Major', 'p2': 'Major',
    # 轻微
    '轻微': 'Minor', 'minor': 'Minor', 'trivial': 'Minor', 'low': 'Minor', 'p3': 'Minor',
}

# 已关闭状态的关键词（不区分大小写）
_CLOSED_STATUS_KEYWORDS = {'已关闭', '已解决', '已拒绝', '重复', 'closed', 'resolved', 'rejected', 'duplicate', 'wontfix'}


def get_severity_option_map(config: dict, dry_run: bool = False) -> Dict[str, str]:
    """查询工作项类型字段，获取严重等级 option_id -> 显示名称 的映射

    API: GET /projects/{projectId}/workitemTypes/{typeId}/fields

    Args:
        config: 云效配置字典
        dry_run: 模拟模式

    Returns:
        dict: {option_id: 标准严重等级名称}，如 {"xxx-id-1": "Fatal", "xxx-id-2": "Critical"}
    """
    if dry_run:
        return {"dry_fatal": "Fatal", "dry_critical": "Critical", "dry_major": "Major", "dry_minor": "Minor"}

    projex = config.get('projex', {})
    project_id = projex.get('project_id', '')
    type_id = projex.get('workitem_type_id', '')

    if not project_id or not type_id:
        return {}

    base_url, headers = _build_projex_base(config)
    url = f"{base_url}/projects/{project_id}/workitemTypes/{type_id}/fields"

    try:
        resp = requests.get(url, headers=headers, timeout=30, allow_redirects=False)
        if resp.status_code != 200:
            return {}

        fields = resp.json()
        option_map = {}

        for field in fields:
            if field.get('id') != 'seriousLevel':
                continue
            for opt in field.get('options', []):
                opt_id = opt.get('id', '')
                display = (opt.get('displayValue') or opt.get('value') or '').strip()
                normalized = _SEVERITY_NORMALIZE.get(display.lower(), display)
                if opt_id:
                    option_map[opt_id] = normalized

        return option_map

    except Exception:
        return {}


def normalize_severity(raw: str, option_map: Dict[str, str]) -> str:
    """将 API 返回的严重等级值（option_id 或文字）转为标准名称

    Args:
        raw: API 返回的原始值（可能是 option_id 或显示文字）
        option_map: option_id -> 标准名称映射

    Returns:
        str: 标准严重等级名称（Fatal/Critical/Major/Minor/Unknown）
    """
    if not raw:
        return 'Unknown'

    # 先尝试 option_id 映射
    if raw in option_map:
        return option_map[raw]

    # 再尝试文字映射
    normalized = _SEVERITY_NORMALIZE.get(raw.strip().lower())
    if normalized:
        return normalized

    return raw  # 无法识别时原样返回


def is_closed(status: str) -> bool:
    """判断工作项状态是否为已关闭

    Args:
        status: 状态显示名称（如"已关闭"、"处理中"）

    Returns:
        bool: True = 已关闭，False = 开放中
    """
    return status.strip().lower() in _CLOSED_STATUS_KEYWORDS


# ============================================================
# 工作项查询
# ============================================================

def search_workitems(
    config: dict,
    sprint_id: str = "",
    page_size: int = 200,
    dry_run: bool = False,
) -> List[dict]:
    """查询 Projex 项目中的 Bug 工作项（分页，自动翻页）

    API: POST /oapi/v1/projex/organizations/{orgId}/workitems:search

    Args:
        config: 云效配置字典
        sprint_id: 迭代 ID（为空则查询全项目）
        page_size: 每页数量（最大 200）
        dry_run: 模拟模式

    Returns:
        list[dict]: 工作项列表，每项含 id, subject, status, customFieldValues 等字段
    """
    if dry_run:
        print("[DRY-RUN] 跳过云效 API 调用，返回模拟数据")
        return [
            {'id': 'DRY-001', 'subject': '[DRY] 模拟致命缺陷',
             'statDisplayName': '处理中', 'customFieldValues': {'seriousLevel': 'dry_fatal'}},
            {'id': 'DRY-002', 'subject': '[DRY] 模拟严重缺陷',
             'statDisplayName': '已关闭', 'customFieldValues': {'seriousLevel': 'dry_critical'}},
            {'id': 'DRY-003', 'subject': '[DRY] 模拟一般缺陷',
             'statDisplayName': '处理中', 'customFieldValues': {'seriousLevel': 'dry_major'}},
            {'id': 'DRY-004', 'subject': '[DRY] 模拟轻微缺陷',
             'statDisplayName': '已解决', 'customFieldValues': {'seriousLevel': 'dry_minor'}},
        ]

    projex = config.get('projex', {})
    project_id = projex.get('project_id', '')
    type_id = projex.get('workitem_type_id', '')

    base_url, headers = _build_projex_base(config)
    url = f"{base_url}/workitems:search"

    all_items = []
    page_no = 1

    while True:
        body = {
            'spaceId': project_id,
            'spaceType': 'Project',
            'pageNo': page_no,
            'pageSize': page_size,
        }

        # 按工作项类型过滤（Bug 类型）
        if type_id:
            body['workitemTypeIds'] = [type_id]

        # 按迭代过滤
        if sprint_id:
            body['sprintId'] = sprint_id

        last_error = None
        for attempt in range(3):
            try:
                resp = requests.post(
                    url, json=body, headers=headers,
                    timeout=30, allow_redirects=False,
                )

                if resp.status_code == 302:
                    raise Exception(f"认证失败 (302 -> {resp.headers.get('Location', '')})")

                if resp.status_code >= 400:
                    try:
                        detail = resp.json()
                    except Exception:
                        detail = resp.text[:300]
                    if attempt < 2:
                        wait = 2 * (attempt + 1)
                        print(f"  [重试] HTTP {resp.status_code}，等待 {wait}s ({attempt+1}/3)")
                        time.sleep(wait)
                        continue
                    raise Exception(f"HTTP {resp.status_code}: {detail}")

                data = resp.json()
                # 响应格式可能是列表，也可能是 {items: [...], total: N}
                if isinstance(data, list):
                    items = data
                    total = int(resp.headers.get('x-total', len(data)))
                elif isinstance(data, dict):
                    items = data.get('items', data.get('workitems', data.get('data', [])))
                    total = data.get('total', data.get('totalCount', len(items)))
                else:
                    items = []
                    total = 0

                all_items.extend(items)
                last_error = None
                break

            except Exception as e:
                last_error = e
                if attempt < 2:
                    wait = 2 * (attempt + 1)
                    print(f"  [重试] 异常: {e}，等待 {wait}s ({attempt+1}/3)")
                    time.sleep(wait)

        if last_error:
            raise last_error

        # 翻页判断
        if len(items) < page_size or len(all_items) >= total:
            break
        page_no += 1

    return all_items


# ============================================================
# 统计聚合
# ============================================================

SEVERITY_ORDER = ['Fatal', 'Critical', 'Major', 'Minor']


def aggregate(workitems: List[dict], option_map: Dict[str, str]) -> dict:
    """聚合工作项，按严重等级统计开放/已关闭数量

    Args:
        workitems: 工作项列表
        option_map: option_id -> 标准严重等级名称

    Returns:
        dict: 聚合结果，格式如下：
            {
              "total": N,
              "open": N,
              "closed": N,
              "by_severity": {
                "Fatal":    {"total": N, "open": N, "closed": N},
                "Critical": {"total": N, "open": N, "closed": N},
                "Major":    {"total": N, "open": N, "closed": N},
                "Minor":    {"total": N, "open": N, "closed": N},
                "Unknown":  {"total": N, "open": N, "closed": N},
              }
            }
    """
    summary = {
        'total': 0,
        'open': 0,
        'closed': 0,
        'by_severity': {},
    }

    for item in workitems:
        summary['total'] += 1

        # 状态
        status_name = (
            item.get('statDisplayName')
            or item.get('statusName')
            or (item.get('status') or {}).get('displayName', '')
            or str(item.get('status', ''))
        )
        closed = is_closed(status_name)

        if closed:
            summary['closed'] += 1
        else:
            summary['open'] += 1

        # 严重等级
        custom = item.get('customFieldValues') or {}
        raw_severity = custom.get('seriousLevel', '')
        severity = normalize_severity(raw_severity, option_map)

        if severity not in summary['by_severity']:
            summary['by_severity'][severity] = {'total': 0, 'open': 0, 'closed': 0}

        summary['by_severity'][severity]['total'] += 1
        if closed:
            summary['by_severity'][severity]['closed'] += 1
        else:
            summary['by_severity'][severity]['open'] += 1

    return summary


# ============================================================
# 明细列表（供 defect-retest 等工具使用）
# ============================================================

# 已解决但尚未关闭的状态（等待回归验证）
_RESOLVED_PENDING_RETEST = {'已解决', 'resolved'}

# 从缺陷标题提取关联用例编号（格式: "[JQB-TEAM-042] 标题"）
_CASE_ID_PATTERN = re.compile(r'^\[([A-Z0-9]+-[A-Z0-9]+-\d+)\]')


def extract_case_id_from_subject(subject: str) -> str:
    """从缺陷标题中提取关联用例编号

    create_defect.py 的 build_defect_title() 生成格式: "[JQB-TEAM-042] 标题"

    Args:
        subject: 缺陷标题

    Returns:
        str: 用例编号，无法提取时返回空字符串
    """
    m = _CASE_ID_PATTERN.match(subject.strip())
    return m.group(1) if m else ''


def list_workitems(
    workitems: List[dict],
    option_map: Dict[str, str],
    filter_status: str = "",
) -> List[dict]:
    """将工作项列表转为简化记录，支持按状态名称过滤

    Args:
        workitems: search_workitems() 返回的原始工作项列表
        option_map: option_id -> 标准严重等级名称
        filter_status: 状态名称过滤（精确匹配，空字符串表示不过滤）

    Returns:
        list[dict]: 简化记录列表，每项含:
            id, subject, case_id, severity, status, is_closed
    """
    result = []
    for item in workitems:
        status_name = (
            item.get('statDisplayName')
            or item.get('statusName')
            or (item.get('status') or {}).get('displayName', '')
            or str(item.get('status', ''))
        ).strip()

        if filter_status and status_name.lower() != filter_status.strip().lower():
            continue

        subject = item.get('subject', '')
        custom = item.get('customFieldValues') or {}
        raw_severity = custom.get('seriousLevel', '')

        result.append({
            'id': str(item.get('id', '')),
            'subject': subject,
            'case_id': extract_case_id_from_subject(subject),
            'severity': normalize_severity(raw_severity, option_map),
            'status': status_name,
            'is_closed': is_closed(status_name),
        })
    return result


def list_resolved_defects(
    workitems: List[dict],
    option_map: Dict[str, str],
) -> List[dict]:
    """筛选状态为「已解决」（等待回归验证）的缺陷列表

    Args:
        workitems: search_workitems() 返回的原始工作项列表
        option_map: option_id -> 标准严重等级名称

    Returns:
        list[dict]: 已解决缺陷列表（格式同 list_workitems）
    """
    result = []
    for item in workitems:
        status_name = (
            item.get('statDisplayName')
            or item.get('statusName')
            or (item.get('status') or {}).get('displayName', '')
            or str(item.get('status', ''))
        ).strip()

        if status_name.lower() not in {s.lower() for s in _RESOLVED_PENDING_RETEST}:
            continue

        subject = item.get('subject', '')
        custom = item.get('customFieldValues') or {}
        raw_severity = custom.get('seriousLevel', '')

        result.append({
            'id': str(item.get('id', '')),
            'subject': subject,
            'case_id': extract_case_id_from_subject(subject),
            'severity': normalize_severity(raw_severity, option_map),
            'status': status_name,
            'is_closed': False,
        })
    return result


def format_resolved_table(resolved: List[dict]) -> str:
    """将已解决缺陷列表格式化为人类可读表格

    Args:
        resolved: list_resolved_defects() 返回的列表

    Returns:
        str: 格式化文本
    """
    if not resolved:
        return "无待回归缺陷（云效中无「已解决」状态工作项）"

    lines = []
    lines.append("=" * 60)
    lines.append(f"待回归验证缺陷列表（共 {len(resolved)} 条）")
    lines.append("=" * 60)
    lines.append(f"{'严重等级':<10} {'关联用例':<18} {'缺陷标题'}")
    lines.append("-" * 60)
    for d in resolved:
        case = d['case_id'] or '(未提取)'
        title = d['subject'][:35] + '…' if len(d['subject']) > 36 else d['subject']
        lines.append(f"{d['severity']:<10} {case:<18} {title}")
    lines.append("=" * 60)
    return '\n'.join(lines)


# ============================================================
# 输出格式化
# ============================================================

def format_table(summary: dict) -> str:
    """将聚合结果格式化为人类可读的文本表格

    Args:
        summary: aggregate() 返回的聚合结果

    Returns:
        str: 格式化后的文本
    """
    lines = []
    lines.append("=" * 46)
    lines.append("云效缺陷状态查询结果")
    lines.append("=" * 46)
    lines.append(f"总计: {summary['total']} 条  |  开放: {summary['open']} 条  |  已关闭: {summary['closed']} 条")
    lines.append("")
    lines.append(f"{'严重等级':<12} {'总数':>6} {'开放':>6} {'已关闭':>8}")
    lines.append("-" * 36)

    by_sev = summary.get('by_severity', {})

    for sev in SEVERITY_ORDER:
        if sev in by_sev:
            d = by_sev[sev]
            lines.append(f"{sev:<12} {d['total']:>6} {d['open']:>6} {d['closed']:>8}")

    # 输出不在预定义列表中的等级（如 Unknown 或自定义）
    for sev, d in by_sev.items():
        if sev not in SEVERITY_ORDER:
            lines.append(f"{sev:<12} {d['total']:>6} {d['open']:>6} {d['closed']:>8}")

    lines.append("=" * 46)
    return '\n'.join(lines)


# ============================================================
# CLI 入口
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        prog='query_defects',
        description='查询云效 Projex 缺陷工作项的当前状态（按严重等级统计开放/已关闭数）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询全项目缺陷状态（人类可读输出）
  python query_defects.py

  # 查询指定迭代的缺陷
  python query_defects.py --sprint-id <sprint_id>

  # JSON 输出（供 test-report 等工具程序化消费）
  python query_defects.py --json

  # 模拟模式（不调用云效 API）
  python query_defects.py --dry-run
        """,
    )
    parser.add_argument('--sprint-id', default='', help='按迭代 ID 过滤（留空则查全项目）')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出结果')
    parser.add_argument('--dry-run', '-n', action='store_true', help='模拟模式，不实际调用 API')
    parser.add_argument('--config', '-c', default='', help='配置文件路径（默认 ../config.yaml）')

    # 明细列表模式
    parser.add_argument('--list-resolved', action='store_true',
                        help='列出状态为「已解决」的缺陷明细（供 defect-retest 使用）')
    parser.add_argument('--list-items', action='store_true',
                        help='列出所有工作项明细（与 --filter-status 配合使用）')
    parser.add_argument('--filter-status', default='',
                        help='按状态名称过滤（精确匹配，如 "处理中"、"已解决"；与 --list-items 配合）')
    return parser


def main():
    """CLI 主入口函数"""
    parser = build_parser()
    args = parser.parse_args()

    if not args.json:
        print("=" * 50)
        print("云效缺陷状态查询工具")
        print("=" * 50)

    # 加载并校验配置
    config = load_config(args.config)

    if not args.dry_run:
        errors = validate_config(config)
        if errors:
            msg = {"error": "配置校验失败", "details": errors}
            if args.json:
                print(json.dumps(msg, ensure_ascii=False))
            else:
                print("\n[错误] 配置校验失败:")
                for e in errors:
                    print(f"  - {e}")
                print("\n请检查 config.yaml 中的 yunxiao 和 projex 配置项")
            return 1

    # 获取严重等级映射
    if not args.json:
        print("\n正在获取严重等级字段映射...")
    option_map = get_severity_option_map(config, dry_run=args.dry_run)

    # 查询工作项
    if not args.json:
        sprint_hint = f"迭代 {args.sprint_id}" if args.sprint_id else "全项目"
        print(f"正在查询 {sprint_hint} 的缺陷工作项...")

    try:
        workitems = search_workitems(
            config,
            sprint_id=args.sprint_id,
            dry_run=args.dry_run,
        )
    except Exception as e:
        msg = {"error": f"查询失败: {e}"}
        if args.json:
            print(json.dumps(msg, ensure_ascii=False))
        else:
            print(f"\n[错误] {e}")
        return 1

    # ── 明细列表模式 ──────────────────────────────────────────
    if args.list_resolved:
        resolved = list_resolved_defects(workitems, option_map)
        if args.json:
            print(json.dumps(resolved, ensure_ascii=False, indent=2))
        else:
            print(f"\n共查询到 {len(workitems)} 条工作项\n")
            print(format_resolved_table(resolved))
        return 0

    if args.list_items:
        items = list_workitems(workitems, option_map, filter_status=args.filter_status)
        if args.json:
            print(json.dumps(items, ensure_ascii=False, indent=2))
        else:
            print(f"\n共 {len(items)} 条（过滤后）\n")
            for it in items:
                print(f"  [{it['severity']}] {it['case_id'] or '-':18} {it['status']:8} {it['subject'][:50]}")
        return 0

    # ── 聚合统计模式（默认）──────────────────────────────────
    summary = aggregate(workitems, option_map)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"\n共查询到 {len(workitems)} 条工作项\n")
        print(format_table(summary))

    return 0


if __name__ == '__main__':
    sys.exit(main())
