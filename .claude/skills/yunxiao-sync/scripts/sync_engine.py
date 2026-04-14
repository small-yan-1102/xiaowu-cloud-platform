# -*- coding: utf-8 -*-
"""
云效 Testhub 同步工具 - 同步引擎

编排解析 → 目录创建 → 去重 → 用例创建的完整流程。
支持增量同步和状态持久化。
"""

import os
import re
import json
import time
import logging
from typing import Dict, List, Set, Optional
from datetime import datetime

from .models import TestCase, SyncResult, SyncReport, SyncAction
from .config import AppConfig, save_space_identifier
from .md_parser import parse_all_md_files
from .field_mapper import map_to_yunxiao_request, format_case_for_display
from .api_client import YunxiaoApiClient

logger = logging.getLogger(__name__)


def run_sync(config: AppConfig, config_path: str = "", force_update: bool = False) -> SyncReport:
    """执行完整同步流程

    Args:
        config: 应用配置
        config_path: 配置文件路径（用于回写 space_id）
        force_update: 为 True 时，已存在的用例执行更新而非跳过

    Returns:
        SyncReport: 同步汇总报告
    """
    report = SyncReport()

    # 1. 初始化 API 客户端
    print("\n初始化云效 API 客户端...")
    client = YunxiaoApiClient(config)

    # 2. 确认/创建 Testhub 空间
    space_id = _ensure_testhub_space(client, config, config_path)
    if not space_id:
        print("[错误] 无法获取 Testhub 空间ID，终止同步")
        return report
    config.yunxiao.space_identifier = space_id

    # 2.5 获取字段选项映射（优先级、用例类型的 option ID）
    print("\n获取字段选项映射...")
    field_option_map = client.build_field_option_map()
    if field_option_map:
        priority_count = len(field_option_map.get('tc.priority', {}))
        type_count = len(field_option_map.get('tc.type', {}))
        print(f"  优先级选项: {priority_count} 个, 类型选项: {type_count} 个")
    else:
        print("  [提示] 未获取到字段映射（dry-run 模式或 API 异常），优先级/类型将不设置")

    # 3. 加载同步状态
    state = _load_sync_state(config)

    # 4. 解析 Markdown 用例
    md_dir = os.path.join(config.project_root, config.sync.md_case_dir)
    print(f"\n解析 Markdown 用例文件 ({md_dir})...")
    test_cases = parse_all_md_files(md_dir, config.sync.modules or None)
    print(f"共解析 {len(test_cases)} 条用例")

    if not test_cases:
        print("[提示] 未找到需要同步的用例")
        return report

    # 5. 构建目录结构
    print("\n构建云效目录结构...")
    dir_mapping = _ensure_directories(client, config, test_cases, state)

    # 6. 去重检查
    print("\n检查已同步用例（去重）...")
    existing_ids = _get_existing_case_ids(client, config, state)
    print(f"远端已有 {len(existing_ids)} 条用例")

    # 7. 逐条同步
    print(f"\n开始同步用例 ({len(test_cases)} 条)...")
    print("=" * 60)

    for i, tc in enumerate(test_cases):
        idx_str = f"[{i+1:03d}/{len(test_cases):03d}]"

        # 查找目录ID
        dir_key = f"{tc.module}/{tc.sub_module}"
        directory_id = dir_mapping.get(dir_key, dir_mapping.get(tc.module, ''))

        if not directory_id:
            result = SyncResult(
                case_id=tc.case_id, title=tc.title,
                action=SyncAction.FAILED,
                error_msg=f"未找到目录: {dir_key}"
            )
            report.add_result(result)
            print(f"  {idx_str} {tc.case_id} -> 失败（未找到目录 {dir_key}）")
            continue

        # 判断用例是否已存在
        existing_yunxiao_id = existing_ids.get(tc.case_id)

        if existing_yunxiao_id and not force_update:
            # 已存在且非强制更新 -> 跳过
            result = SyncResult(
                case_id=tc.case_id, title=tc.title,
                action=SyncAction.SKIPPED,
                yunxiao_case_id=existing_yunxiao_id
            )
            report.add_result(result)
            print(f"  {idx_str} {tc.case_id} -> 已存在，跳过")
            continue

        # 创建或更新用例
        try:
            request_body = map_to_yunxiao_request(tc, directory_id, config, field_option_map)

            if existing_yunxiao_id and force_update:
                # 已存在 + 强制更新 -> 删除+重建
                if config.sync.dry_run:
                    print(f"  {idx_str} {tc.case_id} -> [DRY-RUN] 将删除+重建 ({existing_yunxiao_id})")
                    yunxiao_id = existing_yunxiao_id
                else:
                    yunxiao_id = client.update_test_case(existing_yunxiao_id, request_body)
                    print(f"  {idx_str} {tc.case_id} -> 删除+重建成功 ({yunxiao_id})")

                result = SyncResult(
                    case_id=tc.case_id, title=tc.title,
                    action=SyncAction.UPDATED,
                    yunxiao_case_id=yunxiao_id
                )
            else:
                # 不存在 -> 创建
                if config.sync.dry_run:
                    print(f"  {idx_str} {tc.case_id} -> [DRY-RUN] 将创建")
                    print(format_case_for_display(tc, directory_id, config, field_option_map))
                    yunxiao_id = f"dry_{tc.case_id}"
                else:
                    yunxiao_id = client.create_test_case(request_body)
                    print(f"  {idx_str} {tc.case_id} -> 创建成功 ({yunxiao_id})")

                result = SyncResult(
                    case_id=tc.case_id, title=tc.title,
                    action=SyncAction.CREATED,
                    yunxiao_case_id=yunxiao_id
                )

            report.add_result(result)

            # 更新状态
            state.setdefault('synced_cases', {})[tc.case_id] = {
                'yunxiao_id': yunxiao_id,
                'synced_at': datetime.now().isoformat()
            }

        except Exception as e:
            result = SyncResult(
                case_id=tc.case_id, title=tc.title,
                action=SyncAction.FAILED,
                error_msg=str(e)
            )
            report.add_result(result)
            print(f"  {idx_str} {tc.case_id} -> 失败: {e}")

        # 批次间隔（防限流）
        if (i + 1) % config.sync.batch_size == 0 and i + 1 < len(test_cases):
            if not config.sync.dry_run:
                time.sleep(1)

    # 8. 保存同步状态
    _save_sync_state(config, state)

    return report


def _ensure_testhub_space(client: YunxiaoApiClient, config: AppConfig, config_path: str) -> str:
    """确认或创建 Testhub 空间

    Args:
        client: API 客户端
        config: 应用配置
        config_path: 配置文件路径

    Returns:
        str: 空间ID
    """
    if config.yunxiao.space_identifier:
        print(f"使用已配置的 Testhub 空间: {config.yunxiao.space_identifier}")
        return config.yunxiao.space_identifier

    # dry-run 模式下使用模拟空间ID
    if config.sync.dry_run:
        fake_id = "dry_run_space_001"
        print(f"[DRY-RUN] 使用模拟空间ID: {fake_id}")
        return fake_id

    print(f"Testhub 空间未配置，需要手动在云效控制台创建用例库后填入 space_identifier")
    print(f"提示: 登录云效 -> 测试管理 -> 用例库 -> 创建用例库 \"{config.yunxiao.space_name}\"")
    print(f"然后将用例库ID填入 config.yaml 的 yunxiao.space_identifier 字段")
    return ""


def _ensure_directories(
    client: YunxiaoApiClient,
    config: AppConfig,
    test_cases: List[TestCase],
    state: dict
) -> Dict[str, str]:
    """确保云效中存在所需的目录结构

    先从远端查询已有目录构建映射，再按需创建缺失的目录。

    Args:
        client: API 客户端
        config: 应用配置
        test_cases: 测试用例列表
        state: 同步状态

    Returns:
        dict: {目录路径: 目录ID} 映射
    """
    dir_mapping = state.get('directories', {})

    # 先从远端加载已有目录（即使本地缓存有，也刷新一次保证准确）
    if not config.sync.dry_run:
        try:
            remote_dirs = client.list_directories()
            # 构建 {id: {name, parentId}} 和 {parentId: [children]} 索引
            dir_by_id = {d['id']: d for d in remote_dirs}
            root_id = None
            for d in remote_dirs:
                if d.get('parentId') is None:
                    root_id = d['id']
                    break

            # 构建 name -> id 映射（支持二级路径）
            for d in remote_dirs:
                if d.get('parentId') is None:
                    continue  # 跳过根目录
                parent = dir_by_id.get(d.get('parentId'))
                if parent and parent.get('parentId') is None:
                    # 一级目录（父目录是根目录）
                    dir_mapping[d['name']] = d['id']
                elif parent:
                    # 二级目录
                    # 找到一级目录名
                    parent_name = parent.get('name', '')
                    dir_mapping[f"{parent_name}/{d['name']}"] = d['id']
                    # 确保父目录也在映射中
                    if parent_name not in dir_mapping:
                        dir_mapping[parent_name] = parent['id']

            if dir_mapping:
                print(f"  从远端加载 {len(dir_mapping)} 个目录映射")
        except Exception as e:
            print(f"  [警告] 查询远端目录失败: {e}，使用本地缓存")

    # 从用例中收集需要的目录结构
    needed_dirs = set()
    for tc in test_cases:
        needed_dirs.add(tc.module)
        if tc.sub_module:
            needed_dirs.add(f"{tc.module}/{tc.sub_module}")

    # 仅创建缺失的目录
    for dir_path in sorted(needed_dirs):
        if dir_path in dir_mapping:
            print(f"  目录已存在: {dir_path} -> {dir_mapping[dir_path]}")
            continue

        parts = dir_path.split('/')

        if len(parts) == 1:
            # 一级目录
            try:
                dir_id = client.create_directory(parts[0])
                dir_mapping[dir_path] = dir_id
                print(f"  创建目录: {dir_path} -> {dir_id}")
            except Exception as e:
                print(f"  [警告] 创建目录 {dir_path} 失败: {e}")
        elif len(parts) == 2:
            # 二级目录 - 确保父目录存在
            parent_path = parts[0]
            parent_id = dir_mapping.get(parent_path)
            if not parent_id:
                try:
                    parent_id = client.create_directory(parts[0])
                    dir_mapping[parent_path] = parent_id
                    print(f"  创建目录: {parent_path} -> {parent_id}")
                except Exception as e:
                    print(f"  [警告] 创建父目录 {parent_path} 失败: {e}")
                    continue

            try:
                dir_id = client.create_directory(parts[1], parent_id)
                dir_mapping[dir_path] = dir_id
                print(f"  创建目录: {dir_path} -> {dir_id}")
            except Exception as e:
                print(f"  [警告] 创建目录 {dir_path} 失败: {e}")

    # 更新状态中的目录映射
    state['directories'] = dir_mapping
    return dir_mapping


def _get_existing_case_ids(
    client: YunxiaoApiClient,
    config: AppConfig,
    state: dict
) -> Dict[str, str]:
    """获取已同步的用例ID集合（本地状态 + 远端查询）

    Args:
        client: API 客户端
        config: 应用配置
        state: 同步状态

    Returns:
        dict: {case_id: yunxiao_id} 已存在的用例映射
    """
    existing = {}

    # 从本地状态加载
    synced = state.get('synced_cases', {})
    for case_id, info in synced.items():
        existing[case_id] = info.get('yunxiao_id', '')

    if existing:
        print(f"  本地状态记录 {len(existing)} 条已同步用例")

    # 远端查询兜底（首次运行时本地状态为空）
    if not existing and not config.sync.dry_run:
        try:
            remote_cases = client.list_all_test_cases()
            for rc in remote_cases:
                # 从 subject 中提取 [JQB-XXX-NNN] 格式的 case_id
                m = re.search(r'\[([A-Z]+-[A-Z]+-[A-Z0-9-]+|SMOKE-\d+)\]', rc.get('subject', ''))
                if m:
                    existing[m.group(1)] = rc.get('id', '')
            if existing:
                print(f"  远端查询到 {len(existing)} 条已有用例")
        except Exception as e:
            print(f"  [警告] 远端查询用例失败: {e}，将忽略去重")

    return existing


def _load_sync_state(config: AppConfig) -> dict:
    """加载同步状态文件

    Args:
        config: 应用配置

    Returns:
        dict: 同步状态
    """
    state_path = os.path.join(config.project_root, config.mapping.state_file)

    if os.path.exists(state_path):
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            print(f"加载同步状态: {state_path}")
            return state
        except Exception as e:
            print(f"[警告] 加载状态文件失败: {e}，使用空状态")

    return {'synced_cases': {}, 'directories': {}}


def _save_sync_state(config: AppConfig, state: dict):
    """保存同步状态文件

    Args:
        config: 应用配置
        state: 同步状态
    """
    state_path = os.path.join(config.project_root, config.mapping.state_file)
    state['last_sync_time'] = datetime.now().isoformat()

    try:
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        print(f"\n同步状态已保存: {state_path}")
    except Exception as e:
        print(f"\n[警告] 保存状态文件失败: {e}")


def print_report(report: SyncReport):
    """打印同步汇总报告

    Args:
        report: 同步报告对象
    """
    print("\n" + "=" * 60)
    print("同步报告")
    print("=" * 60)
    print(f"  总计: {report.total}")
    print(f"  新建: {report.created}")
    print(f"  更新: {report.updated}")
    print(f"  跳过: {report.skipped}")
    print(f"  失败: {report.failed}")

    # 打印失败详情
    failed = [r for r in report.results if r.action == SyncAction.FAILED]
    if failed:
        print("\n失败详情:")
        for r in failed:
            print(f"  {r.case_id}: {r.error_msg}")

    print("=" * 60)
