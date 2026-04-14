# -*- coding: utf-8 -*-
"""
云效缺陷创建工具 - 将测试失败结果提交为云效 Projex 缺陷工作项

基于云效 Projex Open API，从测试执行报告中提取失败信息，
自动创建缺陷（Bug）工作项。复用 yunxiao-sync 的 config.yaml 认证配置。

API 调用链路:
  POST /oapi/v1/projex/organizations/{orgId}/testPlan/list        - 获取测试计划
  GET  /oapi/v1/projex/organizations/{orgId}/projects/{id}/sprints - 获取迭代列表
  GET  /oapi/v1/projex/organizations/{orgId}/projects/{id}/workitemTypes?category=Bug - 获取缺陷类型
  POST /oapi/v1/projex/organizations/{orgId}/workitems?spaceId={id} - 创建缺陷

使用方式:
  python create_defect.py --case-id JQB-TEAM-042 --title "移除成员后列表未刷新" \
    --steps "1.进入团队管理 2.点击移除 3.确认移除" \
    --expected "成员从列表消失" --actual "成员仍显示在列表中"

  python create_defect.py --from-report test_reports/test_report_20260325.md
"""

import os
import re
import sys
import json
import argparse
import requests
import yaml
import time
from typing import Dict, Optional, List, Tuple
from datetime import datetime


# ============================================================
# 配置加载
# ============================================================

def load_config() -> dict:
    """加载云效配置文件

    优先级: 环境变量 > config.yaml > 默认值

    Returns:
        dict: 包含 yunxiao 和 projex 配置的字典
    """
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
    yunxiao['assigned_to'] = os.environ.get(
        'YUNXIAO_ASSIGNED_TO', yunxiao.get('assigned_to', '')
    )

    return {'yunxiao': yunxiao, 'projex': projex}


def validate_config(config: dict) -> List[str]:
    """校验缺陷创建所需的必填配置

    Args:
        config: 配置字典

    Returns:
        list[str]: 错误信息列表（空表示通过）
    """
    errors = []
    yunxiao = config.get('yunxiao', {})
    projex = config.get('projex', {})

    if not yunxiao.get('personal_access_token'):
        errors.append("缺少 personal_access_token (PAT)")
    if not yunxiao.get('organization_id'):
        errors.append("缺少 organization_id (组织ID)")
    if not projex.get('project_id'):
        errors.append("缺少 projex.project_id (Projex项目ID)")
    if not projex.get('workitem_type_id'):
        errors.append("缺少 projex.workitem_type_id (缺陷类型ID)")
    if not projex.get('severity_option_id'):
        errors.append("缺少 projex.severity_option_id (严重程度选项ID)")
    if not projex.get('priority_option_id'):
        errors.append("缺少 projex.priority_option_id (优先级选项ID)")

    return errors


# ============================================================
# 缺陷数据构建
# ============================================================

def build_defect_description(
    case_id: str,
    steps: str,
    expected: str,
    actual: str,
    environment: str = "",
    screenshot: str = "",
    extra: str = "",
) -> str:
    """构建缺陷描述的 Markdown 内容

    Args:
        case_id: 关联测试用例编号
        steps: 重现步骤
        expected: 预期结果
        actual: 实际结果
        environment: 测试环境 URL
        screenshot: 截图文件名或路径
        extra: 附加信息

    Returns:
        str: Markdown 格式的缺陷描述
    """
    lines = []
    lines.append(f"## 关联用例\n\n{case_id}\n")
    lines.append(f"## 重现步骤\n\n{steps}\n")
    lines.append(f"## 预期结果\n\n{expected}\n")
    lines.append(f"## 实际结果\n\n{actual}\n")

    if environment:
        lines.append(f"## 测试环境\n\n{environment}\n")
    if screenshot:
        lines.append(f"## 截图证据\n\n{screenshot}\n")
    if extra:
        lines.append(f"## 补充信息\n\n{extra}\n")

    lines.append(f"\n---\n*由 AI 测试执行工具自动提交 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    return '\n'.join(lines)


def build_defect_title(case_id: str, title: str) -> str:
    """构建缺陷标题

    Args:
        case_id: 用例编号
        title: 缺陷简述

    Returns:
        str: 格式化的标题，如 "[JQB-TEAM-042] 移除成员后列表未刷新"
    """
    if case_id and not title.startswith(f"[{case_id}]"):
        return f"[{case_id}] {title}"
    return title


# ============================================================
# 云效 API 调用
# ============================================================

def _build_api_base(config: dict) -> Tuple[str, dict]:
    """构建 API 基础 URL 和请求头

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


def create_workitem(
    config: dict,
    subject: str,
    description: str,
    assigned_to: str = "",
    dry_run: bool = False,
) -> Tuple[bool, dict]:
    """调用云效 Projex Open API 创建缺陷工作项

    API: POST /oapi/v1/projex/organizations/{orgId}/workitems?spaceId={projectId}
    认证: x-yunxiao-token 请求头

    Args:
        config: 云效配置字典
        subject: 缺陷标题
        description: 缺陷描述（Markdown 格式）
        assigned_to: 指派人用户ID（为空使用配置默认值）
        dry_run: 模拟模式，不实际调用 API

    Returns:
        tuple: (成功标志, 响应数据或错误信息)
    """
    projex = config.get('projex', {})
    project_id = projex.get('project_id', '')
    workitem_type_id = projex.get('workitem_type_id', '')
    sprint_id = projex.get('sprint_id', '')
    severity_id = projex.get('severity_option_id', '')
    priority_id = projex.get('priority_option_id', '')

    # 指派人
    assignee = assigned_to or projex.get('default_assignee', '') or config['yunxiao'].get('assigned_to', '')

    base_url, headers = _build_api_base(config)
    url = f"{base_url}/workitems?spaceId={project_id}"

    body = {
        'subject': subject,
        'assignedTo': assignee,
        'workitemTypeId': workitem_type_id,
        'description': description,
        'customFieldValues': {
            'seriousLevel': severity_id,
            'priority': priority_id,
        },
    }

    # 可选: 关联迭代
    if sprint_id:
        body['sprint'] = sprint_id

    if dry_run:
        print("\n[DRY-RUN] 将创建以下缺陷（未实际调用 API）:")
        print(f"  URL:     {url}")
        print(f"  标题:    {subject}")
        print(f"  指派:    {assignee}")
        print(f"  项目:    {project_id}")
        print(f"  类型ID:  {workitem_type_id}")
        print(f"  迭代ID:  {sprint_id}")
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return True, {'id': 'DRY-RUN-001'}

    # 带重试的 API 调用
    last_error = None
    for attempt in range(3):
        try:
            resp = requests.post(
                url, json=body, headers=headers,
                timeout=30, allow_redirects=False,
            )

            if resp.status_code == 302:
                return False, {'error': f"认证失败 (302 -> {resp.headers.get('Location', '')})"}

            if resp.status_code >= 400:
                try:
                    detail = resp.json()
                except Exception:
                    detail = resp.text[:500]
                if attempt < 2:
                    wait = 2 * (attempt + 1)
                    print(f"  [重试] HTTP {resp.status_code}，等待 {wait}s ({attempt+1}/3)")
                    time.sleep(wait)
                    continue
                return False, {'error': f"HTTP {resp.status_code}", 'detail': detail}

            data = resp.json()
            return True, data

        except Exception as e:
            last_error = e
            if attempt < 2:
                wait = 2 * (attempt + 1)
                print(f"  [重试] 异常: {e}，等待 {wait}s ({attempt+1}/3)")
                time.sleep(wait)
            else:
                return False, {'error': str(e)}

    return False, {'error': str(last_error)}


# ============================================================
# 报告解析
# ============================================================

def parse_failures_from_report(report_path: str) -> List[dict]:
    """从测试执行报告中解析失败用例信息

    Args:
        report_path: 测试报告 Markdown 文件路径

    Returns:
        list[dict]: 失败用例列表，每项包含 case_id, title, step, expected, actual, screenshot
    """
    if not os.path.exists(report_path):
        print(f"[错误] 报告文件不存在: {report_path}")
        return []

    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    failures = []

    # 匹配 "### [用例编号] 用例名称" 后跟失败详情
    pattern = re.compile(
        r'### \[?(?P<case_id>[A-Z]+-[A-Z]+-\d+)\]?\s+(?P<title>[^\n]+)\n'
        r'.*?'
        r'\*\*失败步骤\*\*:\s*(?P<step>[^\n]+)\n'
        r'.*?'
        r'\*\*期望\*\*:\s*(?P<expected>[^\n]+)\n'
        r'.*?'
        r'\*\*实际\*\*:\s*(?P<actual>[^\n]+)',
        re.DOTALL,
    )

    # 也尝试匹配列表格式 "- **失败步骤**: ..."
    pattern2 = re.compile(
        r'### \[?(?P<case_id>[A-Z]+-[A-Z]+-\d+)\]?\s+(?P<title>[^\n]+)\n'
        r'.*?'
        r'-\s*\*\*失败步骤\*\*:\s*(?P<step>[^\n]+)\n'
        r'.*?'
        r'-\s*\*\*期望\*\*:\s*(?P<expected>[^\n]+)\n'
        r'.*?'
        r'-\s*\*\*实际\*\*:\s*(?P<actual>[^\n]+)',
        re.DOTALL,
    )

    for pat in [pattern, pattern2]:
        for m in pat.finditer(content):
            failures.append({
                'case_id': m.group('case_id'),
                'title': m.group('title').strip(),
                'step': m.group('step').strip(),
                'expected': m.group('expected').strip(),
                'actual': m.group('actual').strip(),
                'screenshot': '',
            })

    # 去重（以 case_id 为键）
    seen = set()
    unique = []
    for f in failures:
        if f['case_id'] not in seen:
            seen.add(f['case_id'])
            unique.append(f)

    return unique


# ============================================================
# CLI 入口
# ============================================================

def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器

    Returns:
        argparse.ArgumentParser: 参数解析器
    """
    parser = argparse.ArgumentParser(
        prog='create_defect',
        description='将测试失败结果提交为云效 Projex 缺陷工作项',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 手动创建单个缺陷
  python create_defect.py --case-id JQB-TEAM-042 \\
    --title "移除成员后列表未刷新" \\
    --steps "1.进入团队管理 2.点击移除 3.确认移除" \\
    --expected "成员从列表消失" \\
    --actual "成员仍显示在列表中"

  # 从测试报告批量创建（仅处理失败用例）
  python create_defect.py --from-report test_reports/test_report_20260325.md

  # 模拟模式（不实际调用 API）
  python create_defect.py --case-id JQB-TEAM-042 --title "测试缺陷" \\
    --steps "步骤" --expected "预期" --actual "实际" --dry-run
        """,
    )

    # 单条缺陷参数
    parser.add_argument('--case-id', help='关联测试用例编号 (如 JQB-TEAM-042)')
    parser.add_argument('--title', help='缺陷标题')
    parser.add_argument('--steps', help='重现步骤')
    parser.add_argument('--expected', help='预期结果')
    parser.add_argument('--actual', help='实际结果')
    parser.add_argument('--assigned-to', default='', help='指派人用户ID (默认使用配置)')
    parser.add_argument('--screenshot', default='', help='截图文件名')
    parser.add_argument('--environment', default='', help='测试环境 URL')

    # 批量模式
    parser.add_argument('--from-report', help='从测试报告文件批量创建失败用例的缺陷')

    # 通用参数
    parser.add_argument('--dry-run', '-n', action='store_true', help='模拟模式，不实际调用 API')
    parser.add_argument('--config', '-c', default='', help='配置文件路径 (默认 ../config.yaml)')

    return parser


def create_single_defect(args, config: dict) -> int:
    """创建单条缺陷

    Args:
        args: 命令行参数
        config: 配置字典

    Returns:
        int: 退出码 (0=成功, 1=失败)
    """
    if not args.title:
        print("[错误] 缺少 --title 参数")
        return 1
    if not args.steps and not args.actual:
        print("[错误] 至少需要 --steps 或 --actual 参数")
        return 1

    subject = build_defect_title(args.case_id or '', args.title)
    description = build_defect_description(
        case_id=args.case_id or '',
        steps=args.steps or '(未提供)',
        expected=args.expected or '(未提供)',
        actual=args.actual or '(未提供)',
        environment=args.environment,
        screenshot=args.screenshot,
    )

    print(f"\n创建缺陷: {subject}")
    ok, data = create_workitem(
        config, subject, description,
        assigned_to=args.assigned_to,
        dry_run=args.dry_run,
    )

    if ok:
        defect_id = data.get('id', 'N/A')
        print(f"  [OK] 缺陷已创建: {defect_id}")
        return 0
    else:
        print(f"  [FAIL] 创建失败: {data}")
        return 1


def create_from_report(args, config: dict) -> int:
    """从测试报告批量创建缺陷

    Args:
        args: 命令行参数
        config: 配置字典

    Returns:
        int: 退出码 (0=全部成功, 1=有失败)
    """
    report_path = args.from_report
    print(f"\n解析测试报告: {report_path}")

    failures = parse_failures_from_report(report_path)
    if not failures:
        print("未找到失败用例，无需创建缺陷")
        return 0

    print(f"发现 {len(failures)} 个失败用例\n")

    success_count = 0
    fail_count = 0

    for i, f in enumerate(failures):
        subject = build_defect_title(f['case_id'], f['title'])
        description = build_defect_description(
            case_id=f['case_id'],
            steps=f['step'],
            expected=f['expected'],
            actual=f['actual'],
            screenshot=f.get('screenshot', ''),
        )

        print(f"[{i+1}/{len(failures)}] {subject}")

        ok, data = create_workitem(
            config, subject, description,
            dry_run=args.dry_run,
        )

        if ok:
            defect_id = data.get('id', 'N/A')
            print(f"  [OK] {defect_id}")
            success_count += 1
        else:
            print(f"  [FAIL] {data}")
            fail_count += 1

        # 防限流
        if not args.dry_run:
            time.sleep(0.5)

    print(f"\n{'='*40}")
    print(f"批量创建完成: 成功={success_count}, 失败={fail_count}")
    print(f"{'='*40}")

    return 0 if fail_count == 0 else 1


def main():
    """CLI 主入口函数"""
    parser = build_parser()
    args = parser.parse_args()

    print("=" * 50)
    print("云效缺陷创建工具")
    print("=" * 50)

    # 加载配置
    if args.config:
        os.environ.setdefault('YUNXIAO_CONFIG', args.config)
    config = load_config()

    # 校验
    if not args.dry_run:
        errors = validate_config(config)
        if errors:
            print("\n[错误] 配置校验失败:")
            for err in errors:
                print(f"  - {err}")
            print("\n请检查 config.yaml 中的 projex 配置项")
            return 1

    # 分派模式
    if args.from_report:
        return create_from_report(args, config)
    elif args.title or args.case_id:
        return create_single_defect(args, config)
    else:
        parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
