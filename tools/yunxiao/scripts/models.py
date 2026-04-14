# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 数据模型

定义同步过程中使用的数据结构：
- SyncAction: 同步操作类型枚举
- StepResult: 单步执行结果
- TestCase: 测试用例模型
- SyncResult: 单条同步结果
- SyncReport: 批次同步汇总报告
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class SyncAction(Enum):
    """同步操作类型"""
    CREATED = "created"    # 新建
    UPDATED = "updated"    # 更新（删除重建）
    SKIPPED = "skipped"    # 跳过（已存在且非强制更新）
    FAILED  = "failed"     # 失败


@dataclass
class StepResult:
    """测试步骤与预期结果配对"""
    step_number: int
    action: str           # 步骤操作描述
    expected: str         # 对应的预期结果
    verify_level: str     # L1 / L2 / L3


@dataclass
class TestCase:
    """测试用例数据模型（从 Markdown 解析而来）"""
    case_id: str                              # 用例编号，如 JQB-TEAM-001
    title: str                                # 用例名称
    module: str                               # 所属模块（一级目录）
    sub_module: str                           # 子模块（二级目录，可为空）
    priority: str                             # 优先级：P0 / P1 / P2 / P3
    case_type: str                            # 用例类型：功能测试 / 边界值测试 / 异常测试等
    precondition: str                         # 前置条件（合并后的文本）
    steps: List[StepResult]                   # 步骤列表
    test_data: str                            # 测试数据（原始文本）
    expected_results_raw: str                 # 预期结果原始文本
    smoke_id: str = ""                        # 冒烟用例关联的 SMOKE-XXX 编号
    related_requirement: str = ""             # 关联需求（如 PRD V5.1 第3节）
    manual_intervention: str = "否"           # 是否需要人工介入
    design_method: str = "等价类划分法"        # 设计方法
    tags: List[str] = field(default_factory=list)  # 标签列表
    source_file: str = ""                     # 来源 Markdown 文件路径


@dataclass
class SyncResult:
    """单条用例的同步结果"""
    case_id: str
    title: str
    action: SyncAction
    yunxiao_case_id: str = ""    # 云效侧的用例 ID
    error_msg: str = ""          # 失败时的错误信息


@dataclass
class SyncReport:
    """批次同步汇总报告"""
    total: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    results: List[SyncResult] = field(default_factory=list)

    def add_result(self, result: SyncResult):
        """添加单条同步结果并更新统计

        Args:
            result: 单条同步结果
        """
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
