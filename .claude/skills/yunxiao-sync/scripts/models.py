# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 数据模型定义

定义用例解析、同步过程中使用的核心数据结构。
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class SyncAction(Enum):
    """同步操作类型枚举"""
    CREATED = "created"
    SKIPPED = "skipped"
    UPDATED = "updated"
    FAILED = "failed"


@dataclass
class StepResult:
    """测试步骤-预期结果配对

    Attributes:
        step_number: 步骤序号
        action: 操作描述
        expected: 预期结果描述
        verify_level: 验证级别 (L1/L2/L3)
    """
    step_number: int
    action: str
    expected: str = ""
    verify_level: str = "L1"


@dataclass
class TestCase:
    """从 Markdown 解析出的标准化测试用例

    Attributes:
        case_id: 用例编号 (如 JQB-CERT-001)
        title: 用例标题
        module: 一级模块名 (如 企业认证模块)
        sub_module: 二级子模块 (如 功能测试/安全测试)
        priority: 优先级 (P0/P1/P2/P3)
        case_type: 用例类型 (功能测试/异常测试等)
        precondition: 前置条件文本
        steps: 步骤-结果配对列表
        test_data: 测试数据文本
        expected_results_raw: 原始预期结果文本
        smoke_id: 冒烟测试标识 (可选)
        related_requirement: 关联需求
        manual_intervention: 是否需要人工介入
        design_method: 设计方法
        tags: 标签列表
        source_file: 来源文件名
    """
    case_id: str
    title: str
    module: str = ""
    sub_module: str = ""
    priority: str = ""
    case_type: str = ""
    precondition: str = ""
    steps: List[StepResult] = field(default_factory=list)
    test_data: str = ""
    expected_results_raw: str = ""
    smoke_id: str = ""
    related_requirement: str = ""
    manual_intervention: str = "否"
    design_method: str = ""
    tags: List[str] = field(default_factory=list)
    source_file: str = ""


@dataclass
class SyncResult:
    """单条用例的同步结果

    Attributes:
        case_id: 用例编号
        title: 用例标题
        action: 同步操作类型
        yunxiao_case_id: 云效分配的用例ID (创建成功时)
        error_msg: 错误信息 (失败时)
    """
    case_id: str
    title: str
    action: SyncAction
    yunxiao_case_id: str = ""
    error_msg: str = ""


@dataclass
class SyncReport:
    """同步汇总报告

    Attributes:
        total: 总用例数
        created: 新创建数
        updated: 更新数
        skipped: 跳过数
        failed: 失败数
        results: 各用例同步结果
    """
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    results: List[SyncResult] = field(default_factory=list)

    def add_result(self, result: SyncResult):
        """添加一条同步结果并更新计数"""
        self.results.append(result)
        self.total += 1
        if result.action == SyncAction.CREATED:
            self.created += 1
        elif result.action == SyncAction.UPDATED:
            self.updated += 1
        elif result.action == SyncAction.SKIPPED:
            self.skipped += 1
        elif result.action == SyncAction.FAILED:
            self.failed += 1
