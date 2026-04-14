# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 配置管理

从 config.yaml 加载配置，提供类型安全的配置数据类，
并支持将 space_identifier 回写到 YAML 文件。
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# 配置数据类
# ============================================================

@dataclass
class YunxiaoConfig:
    """云效平台连接配置"""
    personal_access_token: str    # 个人访问令牌 (PAT)
    organization_id: str          # 组织 ID
    domain: str = "openapi-rdc.aliyuncs.com"  # API 域名
    space_name: str = "测试用例库"  # Testhub 空间名称
    space_identifier: str = ""    # Testhub 空间 ID（首次同步后自动回写）
    assigned_to: str = ""         # 默认指派人（用户ID）


@dataclass
class SyncConfig:
    """同步行为配置"""
    md_case_dir: str = "test_suites"   # Markdown 用例目录（相对于项目根目录）
    modules: List[str] = field(default_factory=list)  # 模块过滤（空列表 = 同步全部）
    batch_size: int = 10               # 批次间隔（每N条暂停1秒，防限流）
    dry_run: bool = False              # 模拟模式（不实际调用 API）


@dataclass
class MappingConfig:
    """本地状态映射配置"""
    state_file: str = "tools/yunxiao/sync_state.json"  # 同步状态文件路径（相对于项目根目录）


@dataclass
class AppConfig:
    """完整应用配置"""
    yunxiao: YunxiaoConfig
    sync: SyncConfig
    mapping: MappingConfig
    project_root: str = ""    # 项目根目录（运行时自动推断）


# ============================================================
# 配置加载
# ============================================================

def load_config(config_path: str = "", project_root: str = "") -> AppConfig:
    """从 YAML 文件加载配置

    Args:
        config_path: 配置文件路径。为空时依次查找：
                     1. 环境变量 YUNXIAO_CONFIG
                     2. <script_dir>/../config.yaml（适合从 scripts/ 调用）
        project_root: 项目根目录。为空时从 config_path 向上推断（上3层）

    Returns:
        AppConfig: 类型安全的配置对象

    Raises:
        FileNotFoundError: 配置文件不存在时抛出
        KeyError: 必填配置缺失时抛出
    """
    # 确定配置文件路径
    if not config_path:
        config_path = os.environ.get('YUNXIAO_CONFIG', '')
    if not config_path:
        # 默认: scripts/ 的父目录下的 config.yaml
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, '..', 'config.yaml')
    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请复制 config.example.yaml 为 config.yaml 并填写必要配置"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}

    # 推断项目根目录（config.yaml 位于 tools/yunxiao/，向上3层）
    if not project_root:
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(config_path)
            )
        )

    # ── 云效连接配置 ──────────────────────────────────────────
    y = raw.get('yunxiao', {})
    yunxiao = YunxiaoConfig(
        personal_access_token=os.environ.get('YUNXIAO_PAT', y.get('personal_access_token', '')),
        organization_id=os.environ.get('YUNXIAO_ORG_ID', y.get('organization_id', '')),
        domain=y.get('domain', 'openapi-rdc.aliyuncs.com'),
        space_name=y.get('space_name', '测试用例库'),
        space_identifier=y.get('space_identifier', ''),
        assigned_to=os.environ.get('YUNXIAO_ASSIGNED_TO', y.get('assigned_to', '')),
    )

    # ── 同步行为配置 ──────────────────────────────────────────
    s = raw.get('sync', {})
    sync = SyncConfig(
        md_case_dir=s.get('md_case_dir', 'test_suites'),
        modules=s.get('modules', []) or [],
        batch_size=int(s.get('batch_size', 10)),
        dry_run=bool(s.get('dry_run', False)),
    )

    # ── 状态映射配置 ──────────────────────────────────────────
    m = raw.get('mapping', {})
    mapping = MappingConfig(
        state_file=m.get('state_file', 'tools/yunxiao/sync_state.json'),
    )

    return AppConfig(
        yunxiao=yunxiao,
        sync=sync,
        mapping=mapping,
        project_root=project_root,
    )


def validate_config(config: AppConfig) -> List[str]:
    """校验必填配置项

    Args:
        config: 应用配置

    Returns:
        list[str]: 错误信息列表，空列表表示校验通过
    """
    errors = []
    y = config.yunxiao

    if not y.personal_access_token:
        errors.append("缺少 yunxiao.personal_access_token（个人访问令牌）")
    if not y.organization_id:
        errors.append("缺少 yunxiao.organization_id（组织ID）")

    return errors


def save_space_identifier(config_path: str, space_id: str):
    """将 space_identifier 回写到 config.yaml

    首次同步获取到 space_id 后调用，避免下次再重复查询。

    Args:
        config_path: 配置文件路径
        space_id: Testhub 空间 ID
    """
    config_path = os.path.abspath(config_path)
    if not os.path.exists(config_path):
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f) or {}

    raw.setdefault('yunxiao', {})['space_identifier'] = space_id

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(raw, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"space_identifier 已回写到 {config_path}: {space_id}")
