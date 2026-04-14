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
import glob
import argparse
import mimetypes
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
    支持 projects (多项目) 和 projex (旧单项目) 两种模式

    Returns:
        dict: 包含 yunxiao、projex、projects 配置的字典
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
    projects = data.get('projects', {})

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

    return {
        'yunxiao': yunxiao,
        'projex': projex,
        'projects': projects,
        '_config_path': config_path,
    }


def validate_config(config: dict) -> List[str]:
    """校验缺陷创建所需的必填配置

    支持双模式:
    - 新模式 (projects 存在): 仅校验 yunxiao 认证信息
    - 旧模式 (仅 projex): 校验 projex 全部必填字段

    Args:
        config: 配置字典

    Returns:
        list[str]: 错误信息列表（空表示通过）
    """
    errors = []
    yunxiao = config.get('yunxiao', {})
    projex = config.get('projex', {})
    projects = config.get('projects', {})

    if not yunxiao.get('personal_access_token'):
        errors.append("缺少 personal_access_token (PAT)")
    if not yunxiao.get('organization_id'):
        errors.append("缺少 organization_id (组织ID)")

    # 新模式: projects 配置存在，不强制 projex 字段
    if projects:
        return errors

    # 旧模式: 回退到单项目 projex 校验
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
    project_config: Optional[dict] = None,
    sprint_id: str = "",
    severity: str = "",
    priority: str = "",
    dry_run: bool = False,
) -> Tuple[bool, dict]:
    """调用云效 Projex Open API 创建缺陷工作项

    API: POST /oapi/v1/projex/organizations/{orgId}/workitems?spaceId={projectId}
    认证: x-yunxiao-token 请求头

    支持两种模式:
    - 新模式: 通过 project_config 传入项目配置
    - 旧模式: 从 config['projex'] 读取（向后兼容）

    Args:
        config: 云效配置字典
        subject: 缺陷标题
        description: 缺陷描述（Markdown 格式）
        assigned_to: 指派人用户ID（为空使用配置默认值）
        project_config: 项目配置字典（来自 resolve_project）
        sprint_id: 迭代 ID（来自 resolve_sprint）
        severity: 严重程度名称（如 "一般"），为空使用项目默认
        priority: 优先级名称（如 "中"），为空使用项目默认
        dry_run: 模拟模式，不实际调用 API

    Returns:
        tuple: (成功标志, 响应数据或错误信息)
    """
    if project_config:
        # 新模式: 从 project_config 读取
        project_id = project_config.get('project_id', '')
        workitem_type_id = project_config.get('workitem_type_id', '')

        # severity: CLI 覆盖 > 项目默认
        sev_opts = project_config.get('severity_options', {})
        sev_name = severity or project_config.get('default_severity', '一般')
        severity_id = sev_opts.get(sev_name, '') or project_config.get('_severity_option_id', '')

        # priority: CLI 覆盖 > 项目默认
        pri_opts = project_config.get('priority_options', {})
        pri_name = priority or project_config.get('default_priority', '中')
        priority_id = pri_opts.get(pri_name, '') or project_config.get('_priority_option_id', '')

        # sprint: 参数传入 > 旧配置回退
        if not sprint_id:
            sprint_id = project_config.get('_sprint_id', '')

        # assignee: 已由 resolve_assignee 解析
        assignee = assigned_to or project_config.get('assignees', {}).get('default', '') or config['yunxiao'].get('assigned_to', '')
        project_name = project_config.get('name', '')
    else:
        # 旧模式: 从 config['projex'] 读取
        projex = config.get('projex', {})
        project_id = projex.get('project_id', '')
        workitem_type_id = projex.get('workitem_type_id', '')
        sprint_id = sprint_id or projex.get('sprint_id', '')
        severity_id = projex.get('severity_option_id', '')
        priority_id = projex.get('priority_option_id', '')
        assignee = assigned_to or projex.get('default_assignee', '') or config['yunxiao'].get('assigned_to', '')
        project_name = '(旧配置)'

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
        print(f"  项目:    {project_name} ({project_id})")
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
# 截图文件处理与附件上传
# ============================================================

def resolve_screenshot_paths(screenshot_arg: str, screenshots_dir: str = "") -> List[str]:
    """解析截图路径参数，支持逗号分隔路径和 glob 模式

    Args:
        screenshot_arg: 截图路径参数，如 "a.png,b.png" 或 "screenshots/*.png"
        screenshots_dir: 截图根目录（用于相对路径解析）

    Returns:
        list[str]: 解析后的截图文件绝对路径列表
    """
    if not screenshot_arg:
        return []

    paths = []
    for part in screenshot_arg.split(','):
        part = part.strip()
        if not part:
            continue

        # 如果是相对路径且指定了 screenshots_dir，拼接
        if not os.path.isabs(part) and screenshots_dir:
            part = os.path.join(screenshots_dir, part)

        # 尝试 glob 展开
        expanded = glob.glob(part)
        if expanded:
            paths.extend(expanded)
        elif os.path.exists(part):
            paths.append(part)

    # 只保留存在的文件
    return [p for p in paths if os.path.isfile(p)]


def auto_discover_screenshots(case_id: str, screenshots_dir: str = "") -> List[str]:
    """根据用例ID自动发现关联截图文件

    在截图目录中搜索文件名包含用例编号的截图文件。
    默认搜索 test_reports/screenshots/ 下所有子目录。
    命名格式: {CP级别}_{用例编号}_{步骤}_{状态}_{时间戳}.png

    Args:
        case_id: 用例编号（如 AMS-VTD-001）
        screenshots_dir: 截图根目录，默认 test_reports/screenshots

    Returns:
        list[str]: 匹配的截图文件路径列表
    """
    if not case_id:
        return []

    if not screenshots_dir:
        # 默认截图目录：项目根/test_reports/screenshots
        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', '..')
        )
        screenshots_dir = os.path.join(project_root, 'test_reports', 'screenshots')

    if not os.path.isdir(screenshots_dir):
        return []

    # 搜索所有子目录中文件名包含 case_id 的图片
    matches = []
    # 支持连字符和下划线变体（AMS-VTD-001 -> AMS[-_]VTD[-_]001）
    case_id_pattern = case_id.replace('-', '[-_]')
    pat = re.compile(case_id_pattern, re.IGNORECASE)

    for root, _dirs, files in os.walk(screenshots_dir):
        for fname in files:
            if pat.search(fname) and fname.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.gif', '.webp')
            ):
                matches.append(os.path.join(root, fname))

    matches.sort()
    return matches


def get_attachment_upload_meta(
    config: dict, workitem_id: str, filename: str
) -> Tuple[bool, dict]:
    """获取云效工作项附件上传凭证（OSS STS 临时凭证）

    调用云效 Projex API 获取 OSS 临时上传凭证，
    会探测多个 API 路径模式以兼容不同 API 版本。

    Args:
        config: 云效配置字典
        workitem_id: 工作项ID
        filename: 文件名（含扩展名）

    Returns:
        tuple: (成功标志, 凭证数据字典或错误信息字典)
    """
    yunxiao = config['yunxiao']
    domain = yunxiao['domain'].rstrip('/')
    if not domain.startswith('http'):
        domain = f"https://{domain}"
    org_id = yunxiao['organization_id']
    headers = {
        'x-yunxiao-token': yunxiao['personal_access_token'],
    }

    # 探测多个 API 路径模式
    path_patterns = [
        f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}"
        f"/getAttachmentUploadMeta",
        f"/organization/{org_id}/workitem/{workitem_id}/attachment/createmeta",
    ]

    last_error = ""
    for path in path_patterns:
        url = f"{domain}{path}"
        params = {'fileName': filename}

        try:
            resp = requests.get(
                url, params=params, headers=headers,
                timeout=15, allow_redirects=False,
            )

            if resp.status_code == 302:
                continue  # 认证不匹配此路径，尝试下一个

            if resp.status_code == 200:
                data = resp.json()
                return True, data

            if resp.status_code == 404:
                continue

            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

        except Exception as e:
            last_error = str(e)
            continue

    return False, {'error': f'附件凭证获取失败: {last_error or "所有路径均不可用"}'}


def upload_file_to_oss(meta: dict, file_path: str) -> Tuple[bool, str]:
    """通过 OSS STS 临时凭证上传文件

    使用 get_attachment_upload_meta 返回的凭证，
    以 multipart/form-data 格式上传文件到 OSS。

    Args:
        meta: OSS 上传凭证（含 host, accessId, policy, signature, key 等字段）
        file_path: 本地文件绝对路径

    Returns:
        tuple: (成功标志, file_key 或错误消息)
    """
    # 解析凭证字段（兼容多种返回格式）
    host = meta.get('host') or meta.get('ossHost', '')
    access_id = meta.get('accessId') or meta.get('OSSAccessKeyId', '')
    policy = meta.get('policy', '')
    signature = meta.get('signature') or meta.get('Signature', '')
    file_key = meta.get('key') or meta.get('fileKey', '')
    callback = meta.get('callback', '')

    if not all([host, access_id, policy, signature, file_key]):
        missing = []
        if not host: missing.append('host')
        if not access_id: missing.append('accessId')
        if not policy: missing.append('policy')
        if not signature: missing.append('signature')
        if not file_key: missing.append('key')
        return False, f"OSS 凭证不完整，缺少: {', '.join(missing)}"

    if not host.startswith('http'):
        host = f"https://{host}"

    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

    # 构建 multipart/form-data 表单（字段顺序重要，file 必须在最后）
    form_fields = [
        ('OSSAccessKeyId', (None, access_id)),
        ('policy', (None, policy)),
        ('Signature', (None, signature)),
        ('key', (None, file_key)),
        ('success_action_status', (None, '200')),
    ]
    if callback:
        form_fields.append(('callback', (None, callback)))

    try:
        with open(file_path, 'rb') as f:
            form_fields.append(('file', (filename, f, content_type)))
            resp = requests.post(host, files=form_fields, timeout=60)

        if resp.status_code in (200, 204):
            return True, file_key
        else:
            return False, f"OSS 上传失败: HTTP {resp.status_code} - {resp.text[:200]}"

    except Exception as e:
        return False, f"OSS 上传异常: {e}"


def associate_attachment(
    config: dict, workitem_id: str, file_key: str, filename: str
) -> Tuple[bool, dict]:
    """将已上传的 OSS 文件关联为工作项附件

    API: POST /oapi/v1/projex/organizations/{orgId}/workitems/{wid}/attachment

    Args:
        config: 云效配置字典
        workitem_id: 工作项ID
        file_key: OSS 文件 key（从 upload_file_to_oss 返回）
        filename: 原始文件名

    Returns:
        tuple: (成功标志, 响应数据或错误信息)
    """
    yunxiao = config['yunxiao']
    domain = yunxiao['domain'].rstrip('/')
    if not domain.startswith('http'):
        domain = f"https://{domain}"
    org_id = yunxiao['organization_id']
    headers = {
        'Content-Type': 'application/json',
        'x-yunxiao-token': yunxiao['personal_access_token'],
    }

    body = {
        'fileKey': file_key,
        'originalFilename': filename,
    }

    # 探测多个路径模式
    path_patterns = [
        f"/oapi/v1/projex/organizations/{org_id}/workitems/{workitem_id}/attachment",
        f"/organization/{org_id}/workitem/{workitem_id}/attachment",
    ]

    last_error = ""
    for path in path_patterns:
        url = f"{domain}{path}"
        try:
            resp = requests.post(
                url, json=body, headers=headers,
                timeout=15, allow_redirects=False,
            )

            if resp.status_code == 302:
                continue

            if resp.status_code in (200, 201):
                return True, resp.json()

            if resp.status_code == 404:
                continue

            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

        except Exception as e:
            last_error = str(e)
            continue

    return False, {'error': f'附件关联失败: {last_error or "所有路径均不可用"}'}


def upload_screenshots_to_workitem(
    config: dict,
    workitem_id: str,
    screenshot_paths: List[str],
    dry_run: bool = False,
) -> List[dict]:
    """将截图文件上传到云效工作项附件（编排三步上传流程 + 降级策略）

    降级策略:
      L1: 上传成功，附件已关联到工作项
      L2: OSS上传或关联失败，回退为描述中文本引用
      L3: API 不可用（凭证获取失败），仅文本引用
      L4: 文件不存在，跳过

    Args:
        config: 云效配置字典
        workitem_id: 工作项ID
        screenshot_paths: 截图文件路径列表
        dry_run: 模拟模式，不实际调用上传 API

    Returns:
        list[dict]: 每个截图的上传结果，字段: filename, path, success, level, message
    """
    if not screenshot_paths:
        return []

    results = []

    for fpath in screenshot_paths:
        filename = os.path.basename(fpath)
        result = {
            'filename': filename,
            'path': fpath,
            'success': False,
            'level': 'L4',
            'message': '',
        }

        if not os.path.isfile(fpath):
            result['message'] = f'文件不存在: {fpath}'
            results.append(result)
            continue

        if dry_run:
            result['success'] = True
            result['level'] = 'L1'
            result['message'] = f'[DRY-RUN] 将上传: {filename}'
            print(f"    [DRY-RUN] 截图将上传: {filename}")
            results.append(result)
            continue

        # Step 1: 获取上传凭证
        print(f"    上传截图: {filename}")
        ok, meta = get_attachment_upload_meta(config, workitem_id, filename)
        if not ok:
            result['level'] = 'L3'
            result['message'] = meta.get('error', '凭证获取失败')
            print(f"      [降级L3] {result['message']}，将使用文本引用")
            results.append(result)
            continue

        # Step 2: 上传到 OSS
        ok, file_key = upload_file_to_oss(meta, fpath)
        if not ok:
            result['level'] = 'L2'
            result['message'] = f'OSS上传失败: {file_key}'
            print(f"      [降级L2] {result['message']}，将使用文本引用")
            results.append(result)
            continue

        # Step 3: 关联附件到工作项
        ok, assoc_data = associate_attachment(config, workitem_id, file_key, filename)
        if not ok:
            result['level'] = 'L2'
            result['message'] = f'关联失败: {assoc_data.get("error", "未知错误")}'
            print(f"      [降级L2] {result['message']}，文件已在OSS但未关联")
            results.append(result)
            continue

        # 上传成功
        result['success'] = True
        result['level'] = 'L1'
        result['message'] = '上传成功'
        print(f"      [OK] 截图已上传并关联: {filename}")
        results.append(result)

        time.sleep(0.3)  # 防限流

    return results


def build_screenshot_summary(upload_results: List[dict]) -> str:
    """根据截图上传结果构建描述文本

    上传成功的截图显示「已上传为附件」，
    失败的截图回退为本地路径的文本引用。

    Args:
        upload_results: upload_screenshots_to_workitem 的返回值

    Returns:
        str: Markdown 格式的截图摘要文本
    """
    if not upload_results:
        return ""

    lines = []
    for r in upload_results:
        if r['success']:
            lines.append(f"- {r['filename']} (已上传为附件)")
        else:
            lines.append(f"- {r['filename']} (本地路径: {r['path']}, {r['message']})")

    return '\n'.join(lines)


# ============================================================
# 报告解析
# ============================================================

def parse_failures_from_report(report_path: str) -> List[dict]:
    """从测试执行报告中解析失败用例信息

    支持多种报告格式:
      - "**失败步骤**: ..." (粗体标签格式)
      - "- **失败步骤**: ..." (列表+粗体格式)
      - "- 失败步骤: ..." (纯列表格式，无粗体)

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

    # 边界限制: (?:(?!\n### ).)*? 防止 .*? 跨越 ### 章节标题
    _NX = r'(?:(?!\n### )[\s\S])*?'

    # 模式1: "**失败步骤**: ..." (粗体标签)
    pattern1 = re.compile(
        r'### \[?(?P<case_id>[A-Z]+-[A-Z]+-\d+)\]?\s+(?P<title>[^\n]+)\n'
        + _NX +
        r'\*\*失败步骤\*\*:\s*(?P<step>[^\n]+)\n'
        + _NX +
        r'\*\*期望\*\*:\s*(?P<expected>[^\n]+)\n'
        + _NX +
        r'\*\*实际\*\*:\s*(?P<actual>[^\n]+)',
    )

    # 模式2: "- **失败步骤**: ..." (列表+粗体)
    pattern2 = re.compile(
        r'### \[?(?P<case_id>[A-Z]+-[A-Z]+-\d+)\]?\s+(?P<title>[^\n]+)\n'
        + _NX +
        r'-\s*\*\*失败步骤\*\*:\s*(?P<step>[^\n]+)\n'
        + _NX +
        r'-\s*\*\*期望\*\*:\s*(?P<expected>[^\n]+)\n'
        + _NX +
        r'-\s*\*\*实际\*\*:\s*(?P<actual>[^\n]+)',
    )

    # 模式3: "- 失败步骤: ..." (纯列表，无粗体标记)
    pattern3 = re.compile(
        r'### \[?(?P<case_id>[A-Z]+-[A-Z]+-\d+)\]?\s+(?P<title>[^\n]+)\n'
        + _NX +
        r'-\s*失败步骤:\s*(?P<step>[^\n]+)\n'
        + _NX +
        r'-\s*期望:\s*(?P<expected>[^\n]+)\n'
        + _NX +
        r'-\s*实际:\s*(?P<actual>[^\n]+)',
    )

    for pat in [pattern1, pattern2, pattern3]:
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
# 多项目路由 / Sprint 管理 / 负责人解析
# ============================================================

def resolve_project(
    config: dict,
    case_id: str,
    cli_project: str = "",
    interactive: bool = True,
) -> Tuple[str, Optional[dict]]:
    """根据 case_id 前缀或 CLI 参数解析目标项目

    优先级: CLI --project > case_id 前缀匹配 > 交互式选择 > 旧 projex 配置回退

    Args:
        config: 完整配置字典
        case_id: 用例编号（如 AMS-VTD-002）
        cli_project: CLI 手动指定的项目标识（如 AMS）
        interactive: 是否允许交互式提示

    Returns:
        tuple: (project_key, project_config) 或 ('', None) 表示无法匹配
    """
    projects = config.get('projects', {})

    # 1. CLI 手动指定
    if cli_project:
        key_upper = cli_project.upper()
        if key_upper in projects:
            return key_upper, projects[key_upper]
        # 按 name 模糊匹配
        for key, proj in projects.items():
            if proj.get('name', '').upper() == key_upper or key.upper() == key_upper:
                return key, proj
        print(f"  [警告] --project '{cli_project}' 未在配置中找到")

    # 2. case_id 前缀自动匹配
    if case_id and projects:
        case_upper = case_id.upper()
        for key, proj in projects.items():
            patterns = proj.get('prefix_patterns', [])
            for pat in patterns:
                if case_upper.startswith(pat.upper()):
                    return key, proj

    # 3. 交互式选择
    if projects and interactive:
        print("  无法自动匹配项目，请手动选择:")
        choice_key = prompt_user_choice(
            list(projects.keys()),
            labels=[f"{k} ({v.get('name', '')})" for k, v in projects.items()],
        )
        if choice_key:
            return choice_key, projects[choice_key]

    # 4. 回退到旧 projex 配置
    projex = config.get('projex', {})
    if projex.get('project_id'):
        return '', projex

    return '', None


def prompt_user_choice(
    keys: List[str],
    labels: Optional[List[str]] = None,
    prompt_msg: str = "请选择",
) -> str:
    """通用交互式选择器，从标准输入读取用户选择

    Args:
        keys: 选项标识列表
        labels: 显示标签列表（与 keys 等长），为 None 则使用 keys
        prompt_msg: 提示信息

    Returns:
        str: 用户选中的 key，输入无效或 EOF 时返回空字符串
    """
    display = labels or keys
    for i, label in enumerate(display):
        print(f"    [{i+1}] {label}")

    try:
        raw = input(f"  {prompt_msg} [1-{len(keys)}]: ").strip()
        idx = int(raw) - 1
        if 0 <= idx < len(keys):
            return keys[idx]
    except (ValueError, EOFError, KeyboardInterrupt):
        pass

    return ''


def resolve_sprint(
    config: dict,
    project_config: dict,
    sprint_name: str,
    dry_run: bool = False,
) -> str:
    """解析迭代: 按名称查找已有 Sprint，不存在则自动创建

    Args:
        config: 完整配置字典
        project_config: 项目配置（含 project_id）
        sprint_name: 迭代名称（如 "AMS冒烟-20260330"）
        dry_run: 模拟模式，不实际创建

    Returns:
        str: sprint_id，无法解析时返回空字符串
    """
    if not sprint_name:
        return ''

    project_id = project_config.get('project_id', '')
    if not project_id:
        return ''

    base_url, headers = _build_api_base(config)

    # GET 已有迭代列表
    url = f"{base_url}/projects/{project_id}/sprints"
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
        if resp.status_code == 200:
            sprints = resp.json()
            if isinstance(sprints, dict):
                sprints = sprints.get('data', sprints.get('sprints', []))
            if isinstance(sprints, list):
                for sp in sprints:
                    if sp.get('name') == sprint_name:
                        sid = sp.get('id', sp.get('sprintId', ''))
                        print(f"  迭代: {sprint_name} (已存在, id={sid})")
                        return sid
    except Exception as e:
        print(f"  [警告] 查询迭代列表失败: {e}")

    # 自动创建
    if dry_run:
        print(f"  [DRY-RUN] 将创建迭代: {sprint_name}")
        return 'DRY-RUN-SPRINT'

    sid = create_sprint(config, project_config, sprint_name)
    if sid:
        print(f"  迭代: {sprint_name} (新建, id={sid})")
    return sid


def create_sprint(
    config: dict,
    project_config: dict,
    sprint_name: str,
) -> str:
    """调用云效 API 创建新迭代

    API: POST /projects/{pid}/sprints
    注意: owners 为必填字段

    Args:
        config: 完整配置字典
        project_config: 项目配置
        sprint_name: 迭代名称

    Returns:
        str: 新创建的 sprint_id，失败返回空字符串
    """
    project_id = project_config.get('project_id', '')
    if not project_id:
        return ''

    base_url, headers = _build_api_base(config)
    url = f"{base_url}/projects/{project_id}/sprints"

    # owners 取默认负责人
    owner_id = (
        project_config.get('assignees', {}).get('default', '')
        or config['yunxiao'].get('assigned_to', '')
    )
    if not owner_id:
        print("  [警告] 创建迭代失败: 没有可用的 owner_id")
        return ''

    body = {
        'name': sprint_name,
        'owners': [owner_id],
    }

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=15, allow_redirects=False)
        if resp.status_code in (200, 201):
            data = resp.json()
            return data.get('id', data.get('sprintId', ''))
        else:
            print(f"  [警告] 创建迭代失败: HTTP {resp.status_code} - {resp.text[:200]}")
            return ''
    except Exception as e:
        print(f"  [警告] 创建迭代异常: {e}")
        return ''


def resolve_assignee(
    project_config: dict,
    config: dict,
    assignee_type: str = "",
    cli_assignee: str = "",
    interactive: bool = True,
) -> str:
    """解析缺陷负责人

    优先级: cli_assignee > assignee_type(前端/后端) > 交互式 > 项目默认 > 全局默认

    Args:
        project_config: 项目配置
        config: 完整配置字典
        assignee_type: 前端/后端标识 ('frontend' 或 'backend')
        cli_assignee: CLI 直接指定的 user_id
        interactive: 是否允许交互式提示

    Returns:
        str: 负责人 user_id
    """
    # 1. CLI 直接指定
    if cli_assignee:
        return cli_assignee

    assignees = project_config.get('assignees', {})

    # 2. 按前端/后端类型选取
    if assignee_type in ('frontend', 'backend'):
        uid = assignees.get(assignee_type, '')
        if uid:
            return uid
        # 类型指定了但未配置，提示警告
        print(f"  [警告] 项目未配置 {assignee_type} 负责人，使用默认")

    # 3. 交互式选择（仅在单条模式且有多个候选时）
    if interactive and assignees:
        candidates = {}
        for role in ('frontend', 'backend', 'default'):
            uid = assignees.get(role, '')
            if uid:
                candidates[role] = uid
        if len(candidates) > 1:
            print("  请选择负责人类型:")
            choice = prompt_user_choice(
                list(candidates.keys()),
                labels=[f"{k}: {v}" for k, v in candidates.items()],
                prompt_msg="负责人",
            )
            if choice and candidates.get(choice):
                return candidates[choice]

    # 4. 项目默认
    default_uid = assignees.get('default', '')
    if default_uid:
        return default_uid

    # 5. 全局默认
    return config.get('yunxiao', {}).get('assigned_to', '')


def query_project_metadata(config: dict, project_id: str) -> dict:
    """查询单个项目的缺陷类型和字段选项元数据

    API:
      GET /projects/{pid}/workitemTypes?category=Bug
      GET /projects/{pid}/fields (通过 workitemType 获取字段选项)

    Args:
        config: 配置字典
        project_id: 项目 ID

    Returns:
        dict: 包含 workitem_type_id, severity_options, priority_options
    """
    base_url, headers = _build_api_base(config)
    result = {'workitem_type_id': '', 'severity_options': {}, 'priority_options': {}}

    # 获取缺陷工作项类型
    url = f"{base_url}/projects/{project_id}/workitemTypes?category=Bug"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            types = data if isinstance(data, list) else data.get('data', [])
            if types:
                result['workitem_type_id'] = types[0].get('id', '')
    except Exception as e:
        print(f"  [错误] 查询工作项类型失败: {e}")

    return result


def init_projects(config: dict) -> int:
    """查询组织下所有 Projex 项目，输出配置信息

    API: POST /projects:search

    Args:
        config: 配置字典

    Returns:
        int: 退出码
    """
    base_url, headers = _build_api_base(config)
    url = f"{base_url}/projects:search"
    body = {"pageSize": 100, "pageNum": 1}

    print("\n查询组织项目列表...")
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"[错误] HTTP {resp.status_code}: {resp.text[:300]}")
            return 1

        data = resp.json()
        items = data.get('data', data.get('projects', []))
        if not items:
            print("未找到项目")
            return 0

        print(f"\n组织内共 {len(items)} 个项目:\n")
        print(f"{'标识':<12} {'名称':<20} {'项目ID':<30}")
        print("-" * 62)

        for p in items:
            pid = p.get('id', p.get('projectId', ''))
            name = p.get('name', '')
            ident = p.get('identifier', p.get('key', ''))
            print(f"{ident:<12} {name:<20} {pid:<30}")

        print(f"\n提示: 将需要的项目添加到 config.yaml 的 projects 节中")
        return 0

    except Exception as e:
        print(f"[错误] 查询失败: {e}")
        return 1


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
        description='将测试失败结果提交为云效 Projex 缺陷工作项（支持多项目路由）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 手动创建单个缺陷（自动匹配 AMS 项目）
  python create_defect.py --case-id AMS-VTD-002 \\
    --title "按视频ID搜索失败" --actual "无结果" \\
    --sprint "AMS冒烟-20260330" --assignee-type backend

  # 从测试报告批量创建（按 case_id 前缀自动路由项目）
  python create_defect.py --from-report test_reports/test_report_20260330_smoke.md \\
    --sprint "冒烟测试-20260330"

  # 手动指定项目（覆盖自动匹配）
  python create_defect.py --case-id X-001 --project AMS --title "测试" \\
    --actual "实际结果" --sprint "v2.0.0"

  # 初始化: 查询组织所有项目元数据
  python create_defect.py --init-projects
        """,
    )

    # 单条缺陷参数
    parser.add_argument('--case-id', help='关联测试用例编号 (如 AMS-VTD-002, JQB-TEAM-042)')
    parser.add_argument('--title', help='缺陷标题')
    parser.add_argument('--steps', help='重现步骤')
    parser.add_argument('--expected', help='预期结果')
    parser.add_argument('--actual', help='实际结果')
    parser.add_argument('--assigned-to', default='', help='指派人用户ID (直接指定，覆盖所有其他规则)')
    parser.add_argument(
        '--screenshot', default='',
        help='截图文件路径，支持逗号分隔多个或 glob 模式 (如 "a.png,b.png" 或 "screenshots/*.png")',
    )
    parser.add_argument('--environment', default='', help='测试环境 URL')

    # 多项目参数
    parser.add_argument(
        '--project', '-p', default='',
        help='手动指定目标项目标识 (如 AMS, JQB, CRM)，覆盖 case_id 自动匹配',
    )
    parser.add_argument(
        '--sprint', '-s', default='',
        help='迭代名称 (不存在则自动创建，如 "AMS冒烟-20260330")',
    )
    parser.add_argument(
        '--assignee-type', default='', choices=['frontend', 'backend', ''],
        help='指派给前端或后端负责人 (从项目配置的 assignees 中选取)',
    )
    parser.add_argument(
        '--severity', default='',
        help='覆盖严重程度 (致命/严重/一般/轻微)',
    )
    parser.add_argument(
        '--priority', default='',
        help='覆盖优先级 (紧急/高/中/低)',
    )
    parser.add_argument(
        '--no-interactive', action='store_true',
        help='禁止交互式提示 (CI/CD 场景)',
    )

    # 截图上传参数
    parser.add_argument(
        '--screenshots-dir', default='',
        help='截图根目录 (批量模式下自动按用例ID发现截图，默认 test_reports/screenshots)',
    )
    parser.add_argument(
        '--no-upload', action='store_true',
        help='禁用截图上传，仅在描述中以文本引用截图路径',
    )

    # 批量模式
    parser.add_argument('--from-report', help='从测试报告文件批量创建失败用例的缺陷')

    # 初始化命令
    parser.add_argument(
        '--init-projects', action='store_true',
        help='查询组织所有项目元数据，输出项目列表及配置信息',
    )

    # 通用参数
    parser.add_argument('--dry-run', '-n', action='store_true', help='模拟模式，不实际调用 API')
    parser.add_argument('--config', '-c', default='', help='配置文件路径 (默认 ../config.yaml)')

    return parser


def create_single_defect(args, config: dict) -> int:
    """创建单条缺陷，支持多项目路由、Sprint 自动创建、前后端负责人指派

    流程: 解析项目 → 解析迭代 → 解析负责人 → 构建缺陷 → 创建工作项 → 上传截图

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

    interactive = not getattr(args, 'no_interactive', False)

    # 1. 解析目标项目
    project_key, project_config = resolve_project(
        config, args.case_id or '', args.project, interactive=interactive,
    )
    if not project_config:
        print("[错误] 无法确定目标项目，请使用 --project 指定")
        return 1
    if project_key:
        print(f"  项目: {project_key} ({project_config.get('name', '')})")

    # 2. 解析迭代
    sprint_id = resolve_sprint(
        config, project_config, args.sprint, dry_run=args.dry_run,
    )

    # 3. 解析负责人
    assignee = resolve_assignee(
        project_config, config,
        assignee_type=args.assignee_type,
        cli_assignee=args.assigned_to,
        interactive=interactive,
    )

    # 4. 解析截图路径
    screenshot_paths = resolve_screenshot_paths(
        args.screenshot, getattr(args, 'screenshots_dir', ''),
    )
    if not screenshot_paths and args.case_id:
        screenshot_paths = auto_discover_screenshots(
            args.case_id, getattr(args, 'screenshots_dir', ''),
        )
        if screenshot_paths:
            print(f"  自动发现 {len(screenshot_paths)} 个截图文件")

    screenshot_text = args.screenshot
    if screenshot_paths and not screenshot_text:
        screenshot_text = ', '.join(os.path.basename(p) for p in screenshot_paths)

    # 5. 构建缺陷
    subject = build_defect_title(args.case_id or '', args.title)
    description = build_defect_description(
        case_id=args.case_id or '',
        steps=args.steps or '(未提供)',
        expected=args.expected or '(未提供)',
        actual=args.actual or '(未提供)',
        environment=args.environment,
        screenshot=screenshot_text,
    )

    # 6. 创建工作项
    print(f"\n创建缺陷: {subject}")
    ok, data = create_workitem(
        config, subject, description,
        assigned_to=assignee,
        project_config=project_config,
        sprint_id=sprint_id,
        severity=args.severity,
        priority=args.priority,
        dry_run=args.dry_run,
    )

    if ok:
        defect_id = data.get('id', 'N/A')
        print(f"  [OK] 缺陷已创建: {defect_id}")

        # 7. 上传截图附件
        no_upload = getattr(args, 'no_upload', False)
        if screenshot_paths and not no_upload and defect_id != 'N/A':
            print(f"  上传 {len(screenshot_paths)} 个截图...")
            upload_results = upload_screenshots_to_workitem(
                config, defect_id, screenshot_paths, dry_run=args.dry_run,
            )
            uploaded = sum(1 for r in upload_results if r['success'])
            total = len(upload_results)
            print(f"  截图上传完成: {uploaded}/{total} 成功")
        elif screenshot_paths and no_upload:
            print(f"  [跳过] --no-upload 已设置，{len(screenshot_paths)} 个截图仅文本引用")

        return 0
    else:
        print(f"  [FAIL] 创建失败: {data}")
        return 1


def create_from_report(args, config: dict) -> int:
    """从测试报告批量创建缺陷，按 case_id 前缀自动路由到不同项目

    流程: 解析报告 → 按 case_id 路由项目 → 按项目缓存 Sprint → 逐条创建 → 上传截图

    Args:
        args: 命令行参数
        config: 配置字典

    Returns:
        int: 退出码 (0=全部成功, 1=有失败)
    """
    report_path = args.from_report
    screenshots_dir = getattr(args, 'screenshots_dir', '')
    no_upload = getattr(args, 'no_upload', False)
    interactive = not getattr(args, 'no_interactive', False)

    print(f"\n解析测试报告: {report_path}")

    failures = parse_failures_from_report(report_path)
    if not failures:
        print("未找到失败用例，无需创建缺陷")
        return 0

    print(f"发现 {len(failures)} 个失败用例\n")

    # Sprint 缓存: 按 project_key 缓存已解析的 sprint_id（不同项目的同名 Sprint ID 不同）
    sprint_cache = {}
    success_count = 0
    fail_count = 0
    skip_count = 0
    upload_stats = {'total': 0, 'success': 0}
    project_stats = {}  # 按项目统计

    for i, f in enumerate(failures):
        case_id = f['case_id']

        # 1. 按 case_id 路由项目
        project_key, project_config = resolve_project(
            config, case_id, args.project, interactive=interactive,
        )
        if not project_config:
            print(f"[{i+1}/{len(failures)}] [{case_id}] 跳过 - 无法匹配项目")
            skip_count += 1
            continue

        project_name = project_config.get('name', project_key)

        # 2. 解析迭代（按项目缓存）
        if project_key not in sprint_cache and args.sprint:
            sprint_cache[project_key] = resolve_sprint(
                config, project_config, args.sprint, dry_run=args.dry_run,
            )
        sprint_id = sprint_cache.get(project_key, '')

        # 3. 解析负责人
        assignee = resolve_assignee(
            project_config, config,
            assignee_type=args.assignee_type,
            cli_assignee=args.assigned_to,
            interactive=False,  # 批量模式不交互询问负责人
        )

        # 4. 自动发现截图
        case_screenshots = auto_discover_screenshots(case_id, screenshots_dir)
        screenshot_text = f.get('screenshot', '')
        if case_screenshots and not screenshot_text:
            screenshot_text = ', '.join(os.path.basename(p) for p in case_screenshots)

        # 5. 构建缺陷
        subject = build_defect_title(case_id, f['title'])
        description = build_defect_description(
            case_id=case_id,
            steps=f['step'],
            expected=f['expected'],
            actual=f['actual'],
            screenshot=screenshot_text,
        )

        print(f"[{i+1}/{len(failures)}] [{project_name}] {subject}")
        if case_screenshots:
            print(f"  发现 {len(case_screenshots)} 个关联截图")

        # 6. 创建工作项
        ok, data = create_workitem(
            config, subject, description,
            assigned_to=assignee,
            project_config=project_config,
            sprint_id=sprint_id,
            severity=args.severity,
            priority=args.priority,
            dry_run=args.dry_run,
        )

        if ok:
            defect_id = data.get('id', 'N/A')
            print(f"  [OK] {defect_id}")
            success_count += 1
            project_stats[project_name] = project_stats.get(project_name, 0) + 1

            # 7. 上传截图附件
            if case_screenshots and not no_upload and defect_id != 'N/A':
                upload_results = upload_screenshots_to_workitem(
                    config, defect_id, case_screenshots, dry_run=args.dry_run,
                )
                upload_stats['total'] += len(upload_results)
                upload_stats['success'] += sum(1 for r in upload_results if r['success'])
        else:
            print(f"  [FAIL] {data}")
            fail_count += 1

        # 防限流
        if not args.dry_run:
            time.sleep(0.5)

    print(f"\n{'='*40}")
    print(f"批量创建完成: 成功={success_count}, 失败={fail_count}, 跳过={skip_count}")
    if project_stats:
        print(f"项目分布: {', '.join(k + '=' + str(v) for k, v in project_stats.items())}")
    if upload_stats['total'] > 0:
        print(f"截图上传统计: {upload_stats['success']}/{upload_stats['total']} 成功")
    print(f"{'='*40}")

    return 0 if fail_count == 0 else 1


def main():
    """CLI 主入口函数"""
    parser = build_parser()
    args = parser.parse_args()

    print("=" * 50)
    print("云效缺陷创建工具 (v2 - 多项目支持)")
    print("=" * 50)

    # 加载配置
    if args.config:
        os.environ.setdefault('YUNXIAO_CONFIG', args.config)
    config = load_config()

    # --init-projects 子命令
    if getattr(args, 'init_projects', False):
        errors = validate_config(config)
        if errors:
            print("\n[错误] 配置校验失败:")
            for err in errors:
                print(f"  - {err}")
            return 1
        return init_projects(config)

    # 校验
    if not args.dry_run:
        errors = validate_config(config)
        if errors:
            print("\n[错误] 配置校验失败:")
            for err in errors:
                print(f"  - {err}")
            print("\n请检查 config.yaml 中的 yunxiao 和 projects 配置项")
            return 1

    # 显示项目配置摘要
    projects = config.get('projects', {})
    if projects:
        print(f"已配置 {len(projects)} 个项目: {', '.join(projects.keys())}")

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
