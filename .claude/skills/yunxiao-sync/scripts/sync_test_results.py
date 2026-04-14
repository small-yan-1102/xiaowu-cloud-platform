# -*- coding: utf-8 -*-
"""
同步 P0 测试执行结果到云效测试计划

通过 Yunxiao Testhub API 将本地测试结果同步到云效测试计划。
- 组织ID、令牌等敏感配置从 config.yaml 读取
- API: PUT /testPlans/{planId}/testcases/{caseId}
"""

import json
import requests
import yaml
import time
import sys
import os

def load_config():
    """加载云效配置"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_sync_state():
    """加载同步状态，获取 yunxiao_id 映射"""
    state_path = os.path.join(os.path.dirname(__file__), '..', 'sync_state.json')
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def update_test_result(config, plan_id, case_id, case_name, result='passed'):
    """更新测试计划中单条用例的执行结果

    Args:
        config: 云效配置
        plan_id: 测试计划ID
        case_id: 用例在云效中的ID
        case_name: 用例名称（用于日志）
        result: 执行结果 (passed/failed/blocked/skipped)

    Returns:
        tuple: (success: bool, message: str)
    """
    yunxiao = config['yunxiao']
    domain = yunxiao['domain']
    if not domain.startswith('http'):
        domain = f"https://{domain}"
    org_id = yunxiao['organization_id']

    url = f"{domain}/oapi/v1/testhub/organizations/{org_id}/testPlans/{plan_id}/testcases/{case_id}"
    headers = {
        'Content-Type': 'application/json',
        'x-yunxiao-token': yunxiao['personal_access_token'],
    }
    # API参数: status 可选值 TODO/PASS/FAILURE/POSTPONE, executor 为userId
    status_map = {
        'passed': 'PASS',
        'failed': 'FAILURE',
        'blocked': 'POSTPONE',
        'skipped': 'TODO',
    }
    body = {
        'status': status_map.get(result, 'PASS'),
        'executor': yunxiao.get('assigned_to', ''),
    }

    try:
        resp = requests.put(url, json=body, headers=headers, timeout=30, allow_redirects=False)
        if resp.status_code in (200, 204):
            return True, f"OK (HTTP {resp.status_code})"
        elif resp.status_code == 302:
            return False, f"认证失败 (302 -> {resp.headers.get('Location', '')})"
        else:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text[:200]
            return False, f"HTTP {resp.status_code}: {detail}"
    except Exception as e:
        return False, f"异常: {e}"

def main():
    """主函数：同步 10 个 P0 用例结果到云效测试计划"""
    config = load_config()
    sync_state = load_sync_state()

    plan_id = '0a9afc5d032cd52a48f8338614'

    # 10个P0用例及其执行结果
    p0_results = [
        ('JQB-TEAM-006', 'Tab切换功能验证', 'passed'),
        ('JQB-TEAM-001', '统计卡片数据正确性', 'passed'),
        ('JQB-TEAM-004', '企业信息展示验证', 'passed'),
        ('JQB-TEAM-008', '成员列表完整性', 'passed'),
        ('JQB-TEAM-012', '搜索成员功能', 'passed'),
        ('JQB-TEAM-048', '待加入Tab展示+取消', 'passed'),
        ('JQB-TEAM-022', '添加成员成功', 'passed'),
        ('JQB-TEAM-028', '添加成员完整验证', 'passed'),
        ('JQB-TEAM-034', '修改角色-版权运营提升为管理员', 'passed'),
        ('JQB-TEAM-042', '移除非自身成员成功', 'passed'),
    ]

    print(f"='*40")
    print(f"  云效测试计划结果同步")
    print(f"  测试计划ID: {plan_id}")
    print(f"  同步用例数: {len(p0_results)}")
    print(f"='*40")
    print()

    success_count = 0
    fail_count = 0

    for case_id_str, case_name, result in p0_results:
        # 从 sync_state 获取云效用例ID
        case_info = sync_state.get('synced_cases', {}).get(case_id_str, {})
        yunxiao_id = case_info.get('yunxiao_id', '')

        if not yunxiao_id:
            print(f"  [SKIP] {case_id_str} {case_name} - 未找到云效用例ID")
            fail_count += 1
            continue

        ok, msg = update_test_result(config, plan_id, yunxiao_id, case_name, result)

        if ok:
            print(f"  [OK]   {case_id_str} {case_name} -> {result} ({msg})")
            success_count += 1
        else:
            print(f"  [FAIL] {case_id_str} {case_name} -> {msg}")
            fail_count += 1

        # 避免API限流
        time.sleep(0.5)

    print()
    print(f"='*40")
    print(f"  同步完成: 成功={success_count}, 失败={fail_count}")
    print(f"='*40")

    return 0 if fail_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
