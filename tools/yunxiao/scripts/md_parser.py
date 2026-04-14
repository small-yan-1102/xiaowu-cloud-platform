# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - Markdown 测试用例解析器

复用 convert_md_to_excel.py 的解析逻辑，扩展支持 JQB-INTRO 模块，
并新增步骤-预期结果配对功能供云效 API 使用。
"""

import re
import os
from typing import List, Optional, Tuple
from .models import TestCase, StepResult


# 用例ID正则 - 扩展支持 INTRO 模块
CASE_ID_PATTERN = re.compile(
    r'###\s+((?:JQB-(?:TEAM|CERT|CREDIT|SET|DASH|LOGIN|COPYRIGHT|INTRO)'
    r'-(?:\d+|[A-Z0-9]+-\d+))|SMOKE-\d+)\s*(.*)',
    re.IGNORECASE
)

# 模块前缀到一级模块名的映射
MODULE_MAP = {
    'JQB-LOGIN': '登录模块',
    'JQB-INTRO': '介绍页模块',
    'JQB-CERT': '企业认证模块',
    'JQB-CREDIT': '积分中心模块',
    'JQB-TEAM': '团队管理模块',
    'JQB-SET': '账号设置模块',
    'JQB-DASH': '数据总览模块',
    'JQB-COPYRIGHT': '版权保护模块',
    'SMOKE': '冒烟测试',
}

# 文件名到模块名的映射（用于 --module 参数过滤）
FILE_MODULE_MAP = {
    'test_cases_login.md': 'login',
    'test_cases_intro_page.md': 'intro',
    'test_cases_enterprise_cert.md': 'enterprise_cert',
    'test_cases_credits_center.md': 'credits_center',
    'test_cases_team_management.md': 'team_management',
    'test_cases_account_settings.md': 'account_settings',
    'test_cases_dashboard_overview.md': 'dashboard_overview',
}

# 子模块类型关键字
SUB_MODULE_KEYWORDS = {
    'SEC': '安全测试',
    'A11Y': '无障碍测试',
    'PERF': '性能测试',
    'BV': '边界值测试',
    'DATA': '数据一致性测试',
    'EXC': '异常场景测试',
    'COMP': '兼容性测试',
}


def parse_all_md_files(md_case_dir: str, module_filter: List[str] = None) -> List[TestCase]:
    """解析目录下所有 Markdown 用例文件

    Args:
        md_case_dir: md_case 目录绝对路径
        module_filter: 模块过滤列表（如 ['enterprise_cert', 'login']），空则全部

    Returns:
        list[TestCase]: 所有解析出的测试用例
    """
    all_cases = []

    if not os.path.isdir(md_case_dir):
        print(f"[错误] 用例目录不存在: {md_case_dir}")
        return all_cases

    md_files = sorted([
        f for f in os.listdir(md_case_dir)
        if f.endswith('.md') and f.startswith('test_cases_')
    ])

    for filename in md_files:
        # 模块过滤
        if module_filter:
            file_module = FILE_MODULE_MAP.get(filename, '')
            if file_module not in module_filter:
                continue

        filepath = os.path.join(md_case_dir, filename)
        cases = parse_single_md_file(filepath)
        all_cases.extend(cases)
        print(f"  {filename} -> {len(cases)} 条用例")

    return all_cases


def parse_single_md_file(filepath: str) -> List[TestCase]:
    """解析单个 Markdown 用例文件

    Args:
        filepath: Markdown 文件绝对路径

    Returns:
        list[TestCase]: 解析出的测试用例列表
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    cases = []
    filename = os.path.basename(filepath)
    matches = list(CASE_ID_PATTERN.finditer(content))

    for i, match in enumerate(matches):
        case_id = match.group(1).strip()
        case_title = match.group(2).strip() if match.group(2) else ""
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        case_body = content[start_pos:end_pos]

        try:
            case = _parse_case_body(case_id, case_title, case_body, filename)
            if case:
                cases.append(case)
        except Exception as e:
            print(f"  [警告] 解析 {case_id} 失败: {e}")

    return cases


def _parse_case_body(case_id: str, title: str, body: str, source_file: str) -> Optional[TestCase]:
    """解析单条用例的正文内容

    Args:
        case_id: 用例编号
        title: 用例标题
        body: 用例正文（从 ### 标题到下一个 ### 之间的内容）
        source_file: 来源文件名

    Returns:
        TestCase: 解析后的用例对象，解析失败返回 None
    """
    case = TestCase(case_id=case_id, title=title, source_file=source_file)

    # 一级模块
    case.module = _determine_module(case_id)
    # 二级子模块
    case.sub_module = _infer_sub_module(case_id)

    # 优先级
    m = re.search(r'\*\*优先级\*\*[：:]\s*(P\d)', body)
    if m:
        case.priority = m.group(1)

    # 用例类型
    m = re.search(r'\*\*用例类型\*\*[：:]\s*(.+?)(?:\s*\n|$)', body)
    if m:
        case.case_type = m.group(1).strip()

    # 前置条件 - 支持多行
    case.precondition = _extract_multiline_field(body, '前置条件')

    # 测试数据 - 支持表格
    case.test_data = _extract_multiline_field(body, '测试数据')

    # 关联需求
    m = re.search(r'\*\*关联需求\*\*[：:]\s*(.+?)(?:\s*\n|$)', body)
    if m:
        case.related_requirement = m.group(1).strip()

    # 冒烟标识
    m = re.search(r'\*\*冒烟标识\*\*[：:]\s*(SMOKE-[\w-]+)', body)
    if m:
        case.smoke_id = m.group(1).strip()

    # 是否需要人工介入
    m = re.search(r'\*\*是否需要人工介入\*\*[：:]\s*(.+?)(?:\s*\n|$)', body)
    if m:
        case.manual_intervention = m.group(1).strip()

    # 设计方法
    m = re.search(r'\*\*设计方法\*\*[：:]\s*(.+?)(?:\s*\n|$)', body)
    if m:
        case.design_method = m.group(1).strip()

    # 测试步骤文本
    steps_text = _extract_steps(body)
    # 预期结果文本
    expected_text = _extract_expected(body)
    case.expected_results_raw = expected_text

    # 步骤-结果配对
    case.steps = pair_steps_and_expected(steps_text, expected_text)

    # 构建标签
    case.tags = _build_tags(case)

    return case


def _determine_module(case_id: str) -> str:
    """根据用例ID前缀确定一级模块名

    Args:
        case_id: 用例编号

    Returns:
        str: 模块名称
    """
    upper_id = case_id.upper()
    for prefix, module in MODULE_MAP.items():
        if upper_id.startswith(prefix):
            return module
    return '其他'


def _infer_sub_module(case_id: str) -> str:
    """从用例ID推断二级子模块类型

    Args:
        case_id: 用例编号（如 JQB-CERT-SEC-001）

    Returns:
        str: 子模块名称
    """
    upper_id = case_id.upper()
    for keyword, sub_name in SUB_MODULE_KEYWORDS.items():
        if f'-{keyword}-' in upper_id:
            return sub_name
    return '功能测试'


def _extract_multiline_field(body: str, field_name: str) -> str:
    """提取多行字段内容（如前置条件、测试数据）

    Args:
        body: 用例正文
        field_name: 字段名（如 '前置条件'）

    Returns:
        str: 字段内容文本
    """
    # 匹配 **字段名**：后面的内容，直到下一个 **字段** 或 ### 标题
    pattern = rf'\*\*{field_name}\*\*[：:]\s*\n(.*?)(?=\n\*\*\w|$)'
    m = re.search(pattern, body, re.DOTALL)
    if m:
        return m.group(1).strip()

    # 尝试单行匹配
    pattern2 = rf'\*\*{field_name}\*\*[：:]\s*(.+?)(?:\s*\n|$)'
    m2 = re.search(pattern2, body)
    if m2:
        return m2.group(1).strip()

    return ""


def _extract_steps(body: str) -> str:
    """从用例正文中提取测试步骤文本

    Args:
        body: 用例正文

    Returns:
        str: 格式化的步骤文本（每步一行，带序号）
    """
    m = re.search(
        r'\*\*测试步骤\*\*[：:]\s*\n(.*?)(?=\*\*预期结果\*\*|\n### |\Z)',
        body, re.DOTALL
    )
    if not m:
        return ''

    lines = m.group(1).strip().split('\n')
    steps = []
    for line in lines:
        line = line.strip()
        if line and re.match(r'^\d+\.', line):
            steps.append(line)
    return '\n'.join(steps)


def _extract_expected(body: str) -> str:
    """从用例正文中提取预期结果文本

    Args:
        body: 用例正文

    Returns:
        str: 格式化的预期结果文本（每条一行，带序号）
    """
    m = re.search(
        r'\*\*预期结果\*\*[：:]\s*\n(.*?)(?=\n---|\n\*\*是否需要|\n\*\*自动化|\n\*\*备注|\n### |\Z)',
        body, re.DOTALL
    )
    if not m:
        return ''

    lines = m.group(1).strip().split('\n')
    results = []
    idx = 1
    for line in lines:
        line = line.strip()
        if line.startswith('- '):
            text = line[2:].strip()
            results.append(f"{idx}. {text}")
            idx += 1
        elif line and re.match(r'^\d+\.', line):
            results.append(line)
    return '\n'.join(results)


def pair_steps_and_expected(steps_text: str, expected_text: str) -> List[StepResult]:
    """将步骤和预期结果按序号一一配对

    配对策略：
    - 步骤数 = 结果数 → 一对一
    - 结果多于步骤 → 多余结果合并到最后一步
    - 步骤多于结果 → 多余步骤的预期结果置空

    Args:
        steps_text: 步骤文本（每步一行）
        expected_text: 预期结果文本（每条一行）

    Returns:
        list[StepResult]: 配对后的步骤列表
    """
    steps_lines = _parse_numbered_lines(steps_text)
    expected_lines = _parse_numbered_lines(expected_text)

    results = []
    step_count = len(steps_lines)
    exp_count = len(expected_lines)

    for i in range(max(step_count, 1)):
        step_text = steps_lines[i] if i < step_count else ""

        if i < exp_count:
            exp_text = expected_lines[i]
        elif i == step_count - 1 and exp_count > step_count:
            # 多余的预期结果合并到最后一步
            exp_text = '\n'.join(expected_lines[i:])
        else:
            exp_text = ""

        # 提取验证级别
        verify_level, clean_expected = _extract_verify_level(exp_text)

        results.append(StepResult(
            step_number=i + 1,
            action=_clean_step_text(step_text),
            expected=clean_expected,
            verify_level=verify_level
        ))

    return results


def _parse_numbered_lines(text: str) -> List[str]:
    """解析带序号的文本行

    Args:
        text: 多行文本

    Returns:
        list[str]: 去除序号后的文本列表
    """
    if not text.strip():
        return []

    lines = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line:
            # 去除序号前缀 "1. "
            cleaned = re.sub(r'^\d+\.\s*', '', line)
            if cleaned:
                lines.append(cleaned)
    return lines


def _clean_step_text(text: str) -> str:
    """清理步骤文本

    Args:
        text: 原始步骤文本

    Returns:
        str: 清理后的文本
    """
    return re.sub(r'^\d+\.\s*', '', text.strip())


def _extract_verify_level(text: str) -> Tuple[str, str]:
    """从预期结果文本中提取验证级别标记

    Args:
        text: 预期结果文本（可能含 【L1强断言】等标记）

    Returns:
        tuple: (验证级别, 清理后的文本)
    """
    level = "L1"
    clean = text

    m = re.search(r'【(L[123])[^】]*】', text)
    if m:
        level = m.group(1)
        # 保留原始标记文本（它们提供有用的语义信息）
        clean = text

    return level, clean


def _build_tags(case: TestCase) -> List[str]:
    """为用例构建标签列表

    Args:
        case: 测试用例对象

    Returns:
        list[str]: 标签列表
    """
    tags = []

    if case.case_type:
        tags.append(case.case_type)

    if case.smoke_id:
        tags.append(f"冒烟:{case.smoke_id}")

    if case.design_method:
        tags.append(case.design_method)

    if case.manual_intervention.startswith('是'):
        tags.append('需人工介入')

    return tags


def list_available_modules(md_case_dir: str) -> dict:
    """列出所有可用模块及其用例数量

    Args:
        md_case_dir: md_case 目录绝对路径

    Returns:
        dict: {module_key: {'file': filename, 'count': case_count}}
    """
    modules = {}

    if not os.path.isdir(md_case_dir):
        return modules

    for filename, module_key in FILE_MODULE_MAP.items():
        filepath = os.path.join(md_case_dir, filename)
        if os.path.exists(filepath):
            cases = parse_single_md_file(filepath)
            modules[module_key] = {
                'file': filename,
                'count': len(cases)
            }

    return modules
