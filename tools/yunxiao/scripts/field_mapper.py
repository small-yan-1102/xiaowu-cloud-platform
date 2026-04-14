# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 字段映射器

将 TestCase 对象转换为云效 CreateTestCase OpenAPI 的请求参数。
API 文档: POST /oapi/v1/testhub/organizations/{orgId}/testRepos/{id}/testcases
"""

from typing import Dict, List, Any, Optional
from .models import TestCase
from .config import AppConfig

# 用例类型别名映射：Markdown 中的值 -> 云效字段选项的 displayValue
_CASE_TYPE_ALIASES = {
    '安全测试': '安全性测试',
    '边界值测试': '功能测试',
    '异常测试': '功能测试',
    'UI测试': '功能测试',
    '接口测试': '功能测试',
    '兼容性测试': '兼容性测试',
    '性能测试': '性能测试',
    '冒烟测试': '冒烟测试',
    '功能测试': '功能测试',
}


def map_to_yunxiao_request(
    test_case: TestCase,
    directory_id: str,
    config: AppConfig,
    field_option_map: Optional[Dict[str, Dict[str, str]]] = None
) -> Dict[str, Any]:
    """将 TestCase 转换为云效 CreateTestCase API 请求体

    Args:
        test_case: 解析后的测试用例对象
        directory_id: 云效目录ID
        config: 应用配置
        field_option_map: 字段选项映射 {fieldId: {displayValue: optionId}}

    Returns:
        dict: 符合云效 OpenAPI 格式的请求参数
    """
    # 构建 subject: [JQB-CERT-001] 用例标题
    subject = f"[{test_case.case_id}] {test_case.title}"

    # 构建前置条件（附加测试数据）
    precondition = _build_precondition(test_case)

    # 构建步骤-结果列表（TABLE 格式）
    step_content = _build_step_content(test_case)

    request_body = {
        'subject': subject,
        'directoryId': directory_id,
        'preCondition': precondition,
        'testSteps': {
            'contentType': 'TABLE',
            'content': step_content,
        },
    }

    # 负责人
    if config.yunxiao.assigned_to:
        request_body['assignedTo'] = config.yunxiao.assigned_to

    # 标签（仅保留冒烟ID和人工介入标记，不含优先级/类型）
    tags = _build_labels(test_case)
    if tags:
        request_body['labels'] = tags

    # 自定义字段值（优先级、用例类型）
    custom_fields = _build_custom_field_values(test_case, field_option_map)
    if custom_fields:
        request_body['customFieldValues'] = custom_fields

    return request_body


def _build_precondition(test_case: TestCase) -> str:
    """构建前置条件文本，包含测试数据附加

    Args:
        test_case: 测试用例对象

    Returns:
        str: 合并后的前置条件文本
    """
    parts = []

    if test_case.precondition:
        parts.append(test_case.precondition)

    # 附加测试数据
    if test_case.test_data and test_case.test_data not in ('无', '无额外数据', '无额外测试数据'):
        parts.append("\n--- 测试数据 ---")
        parts.append(test_case.test_data)

    # 附加关联需求
    if test_case.related_requirement:
        parts.append(f"\n关联需求: {test_case.related_requirement}")

    return '\n'.join(parts)


def _build_step_content(test_case: TestCase) -> List[Dict[str, str]]:
    """构建云效 API 的 testSteps.content（TABLE 格式）

    API 要求 contentType=TABLE 时，content 为 [{step, expected}] 数组。

    Args:
        test_case: 测试用例对象

    Returns:
        list[dict]: 步骤-预期结果配对列表
    """
    if not test_case.steps:
        return [{'step': '参见用例描述', 'expected': '参见用例描述'}]

    result = []
    for step in test_case.steps:
        result.append({
            'step': step.action if step.action else '',
            'expected': step.expected if step.expected else '',
        })

    return result


def _build_labels(test_case: TestCase) -> List[str]:
    """构建用例标签列表（不含优先级和类型，这两个走 customFieldValues）

    Args:
        test_case: 测试用例对象

    Returns:
        list[str]: 标签列表
    """
    labels = []

    if test_case.smoke_id:
        labels.append(f"冒烟:{test_case.smoke_id}")

    if test_case.manual_intervention.startswith('是'):
        labels.append('需人工介入')

    return labels


def _build_custom_field_values(
    test_case: TestCase,
    field_option_map: Optional[Dict[str, Dict[str, str]]] = None
) -> Dict[str, str]:
    """构建 customFieldValues（优先级、用例类型的字段选项ID）

    Args:
        test_case: 测试用例对象
        field_option_map: 字段选项映射 {fieldId: {displayValue: optionId}}

    Returns:
        dict: {fieldId: optionId} 映射
    """
    if not field_option_map:
        return {}

    custom_values = {}

    # 映射优先级 tc.priority: P0/P1/P2/P3
    priority_map = field_option_map.get('tc.priority', {})
    if test_case.priority and priority_map:
        option_id = priority_map.get(test_case.priority)
        if option_id:
            custom_values['tc.priority'] = option_id

    # 映射用例类型 tc.type: 功能测试/安全性测试 等
    type_map = field_option_map.get('tc.type', {})
    if test_case.case_type and type_map:
        # 先尝试直接匹配
        option_id = type_map.get(test_case.case_type)
        # 再尝试别名映射
        if not option_id:
            alias = _CASE_TYPE_ALIASES.get(test_case.case_type)
            if alias:
                option_id = type_map.get(alias)
        if option_id:
            custom_values['tc.type'] = option_id

    return custom_values


def format_case_for_display(
    test_case: TestCase,
    directory_id: str,
    config: AppConfig,
    field_option_map: Optional[Dict[str, Dict[str, str]]] = None
) -> str:
    """格式化用例信息用于 dry-run 显示

    Args:
        test_case: 测试用例对象
        directory_id: 云效目录ID
        config: 应用配置
        field_option_map: 字段选项映射

    Returns:
        str: 格式化的显示文本
    """
    request = map_to_yunxiao_request(test_case, directory_id, config, field_option_map)
    steps = request.get('testSteps', {}).get('content', [])
    custom_fields = request.get('customFieldValues', {})

    lines = [
        f"  用例: {request['subject']}",
        f"  优先级: {test_case.priority or '未设置'} -> {custom_fields.get('tc.priority', '未映射')}",
        f"  类型: {test_case.case_type or '未设置'} -> {custom_fields.get('tc.type', '未映射')}",
        f"  目录ID: {directory_id}",
        f"  前置条件: {request.get('preCondition', '')[:80]}...",
        f"  步骤数: {len(steps)}",
    ]

    # 显示前3个步骤
    for i, step in enumerate(steps[:3]):
        lines.append(f"    步骤{i+1}: {step['step'][:60]}")
        lines.append(f"    预期{i+1}: {step['expected'][:60]}")
    if len(steps) > 3:
        lines.append(f"    ... 还有 {len(steps) - 3} 个步骤")

    return '\n'.join(lines)
