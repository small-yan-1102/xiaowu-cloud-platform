# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 配置管理

支持三级优先级加载：环境变量 > config.yaml > 默认值。
认证方式：个人访问令牌（PAT），通过 x-yunxiao-token 请求头传递。
"""

import os
import sys
import yaml
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class YunxiaoConfig:
    """云效 API 连接配置

    Attributes:
        personal_access_token: 个人访问令牌（PAT）
        organization_id: 云效组织ID
        space_identifier: Testhub 用例库ID（testRepo id）
        space_name: Testhub 用例库名称（仅用于提示）
        assigned_to: 默认负责人用户ID
        domain: API 域名
    """
    personal_access_token: str = ""
    organization_id: str = ""
    space_identifier: str = ""
    space_name: str = ""
    assigned_to: str = ""
    domain: str = "openapi-rdc.aliyuncs.com"


@dataclass
class SyncConfig:
    """同步行为配置

    Attributes:
        md_case_dir: Markdown 用例目录（相对项目根目录）
        modules: 同步模块过滤（空=全部）
        dry_run: 模拟模式
        batch_size: 每批次处理数量
        retry_count: API 失败重试次数
        retry_delay: 重试间隔（秒）
    """
    md_case_dir: str = ".claude/skills/测试用例库/剧权宝用例库/测试脚本_v2/md_case"
    modules: List[str] = field(default_factory=list)
    dry_run: bool = False
    batch_size: int = 10
    retry_count: int = 3
    retry_delay: int = 2


@dataclass
class MappingConfig:
    """映射与状态文件配置

    Attributes:
        state_file: 同步状态持久化文件路径
    """
    state_file: str = ".claude/skills/yunxiao-sync/sync_state.json"


@dataclass
class AppConfig:
    """应用总配置

    Attributes:
        yunxiao: 云效 API 配置
        sync: 同步行为配置
        mapping: 映射配置
        project_root: 项目根目录绝对路径
    """
    yunxiao: YunxiaoConfig = field(default_factory=YunxiaoConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
    mapping: MappingConfig = field(default_factory=MappingConfig)
    project_root: str = ""


def load_config(config_path: str, project_root: str = "") -> AppConfig:
    """加载配置文件，合并环境变量覆盖

    优先级：环境变量 > config.yaml > 默认值

    Args:
        config_path: YAML 配置文件路径
        project_root: 项目根目录路径

    Returns:
        AppConfig: 合并后的配置对象
    """
    config = AppConfig()

    if not project_root:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(config_path))
        )))
    config.project_root = project_root

    # 加载 YAML 文件
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        # 解析 yunxiao 部分
        yx = data.get('yunxiao', {})
        config.yunxiao.personal_access_token = yx.get('personal_access_token', '')
        config.yunxiao.organization_id = yx.get('organization_id', '')
        config.yunxiao.space_identifier = yx.get('space_identifier', '')
        config.yunxiao.space_name = yx.get('space_name', config.yunxiao.space_name)
        config.yunxiao.assigned_to = yx.get('assigned_to', '')
        config.yunxiao.domain = yx.get('domain', config.yunxiao.domain)

        # 解析 sync 部分
        sc = data.get('sync', {})
        config.sync.md_case_dir = sc.get('md_case_dir', config.sync.md_case_dir)
        config.sync.modules = sc.get('modules', []) or []
        config.sync.dry_run = sc.get('dry_run', False)
        config.sync.batch_size = sc.get('batch_size', 10)
        config.sync.retry_count = sc.get('retry_count', 3)
        config.sync.retry_delay = sc.get('retry_delay', 2)

        # 解析 mapping 部分
        mp = data.get('mapping', {})
        config.mapping.state_file = mp.get('state_file', config.mapping.state_file)
    else:
        print(f"[警告] 配置文件 {config_path} 不存在，使用默认配置")

    # 环境变量覆盖（优先级最高）
    config.yunxiao.personal_access_token = os.environ.get(
        'YUNXIAO_PAT', config.yunxiao.personal_access_token
    )
    config.yunxiao.organization_id = os.environ.get(
        'YUNXIAO_ORG_ID', config.yunxiao.organization_id
    )
    config.yunxiao.assigned_to = os.environ.get(
        'YUNXIAO_ASSIGNED_TO', config.yunxiao.assigned_to
    )

    return config


def validate_config(config: AppConfig) -> List[str]:
    """校验配置必填项

    Args:
        config: 应用配置对象

    Returns:
        list[str]: 错误信息列表（空列表表示校验通过）
    """
    errors = []

    if not config.yunxiao.personal_access_token:
        errors.append("缺少 personal_access_token，请在 config.yaml 或环境变量 YUNXIAO_PAT 中配置")
    if not config.yunxiao.organization_id:
        errors.append("缺少 organization_id，请在 config.yaml 或环境变量 YUNXIAO_ORG_ID 中配置")
    if not config.yunxiao.space_identifier:
        errors.append("缺少 space_identifier（用例库ID），请在 config.yaml 中配置")

    # md_case_dir 校验
    md_dir = os.path.join(config.project_root, config.sync.md_case_dir)
    if not os.path.isdir(md_dir):
        errors.append(f"用例目录不存在: {md_dir}")

    return errors


def save_space_identifier(config_path: str, space_id: str):
    """将 Testhub 用例库ID 回写到配置文件

    Args:
        config_path: YAML 配置文件路径
        space_id: 用例库ID
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        if 'yunxiao' not in data:
            data['yunxiao'] = {}
        data['yunxiao']['space_identifier'] = space_id

        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

        print(f"[信息] 已将用例库ID {space_id} 写回配置文件")
    except Exception as e:
        print(f"[警告] 无法写回配置文件: {e}")
        print(f"[提示] 请手动将 space_identifier: {space_id} 添加到 config.yaml")
