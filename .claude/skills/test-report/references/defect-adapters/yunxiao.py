#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yunxiao Defect Source Adapter

包装 `linscode/lib/yunxiao/scripts/query_defects.py`，输出契约格式 JSON。
契约见同目录 `_interface.md`。

用法:
  python yunxiao.py --json                    # 查全部迭代
  python yunxiao.py --json --sprint-id 12345  # 限定迭代
  python yunxiao.py --selftest                # 自检（Phase 0.5 用）

退出码:
  0 - 成功
  1 - 依赖缺失（requests / yaml 等 Python 包未安装）
  2 - 配置错误（config.yaml 丢失 / 字段不完整）
  3 - 网络/权限错误（API 401/403/超时）
  4 - 数据解析错误
"""
import sys
import os
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Windows 下强制 UTF-8 输出（契约要求）
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# ============================================================
# 路径定位
# ============================================================

# 本 adapter 所在目录 → 项目根
ADAPTER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ADAPTER_DIR.parents[4]  # .../.claude/skills/test-report/references/defect-adapters/ → 项目根
LINSCODE_SCRIPT = PROJECT_ROOT / 'linscode' / 'lib' / 'yunxiao' / 'scripts' / 'query_defects.py'
CONFIG_PATH = PROJECT_ROOT / 'linscode' / 'lib' / 'yunxiao' / 'config.yaml'


# ============================================================
# 自检
# ============================================================

def selftest():
    """检查依赖、配置、连通性。成功=0，失败=1/2/3"""
    # 1. 检查 Python 依赖
    try:
        import requests  # noqa: F401
        import yaml  # noqa: F401
    except ImportError:
        return 1

    # 2. 检查上游脚本存在
    if not LINSCODE_SCRIPT.exists():
        return 2

    # 3. 检查配置文件存在 + 必需字段
    if not CONFIG_PATH.exists():
        return 2

    try:
        import yaml
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        yunxiao = config.get('yunxiao', {})
        projex = config.get('projex', {})
        # 必需字段
        required = {
            'yunxiao.personal_access_token': (yunxiao.get('personal_access_token') or os.environ.get('YUNXIAO_PAT')),
            'yunxiao.organization_id': (yunxiao.get('organization_id') or os.environ.get('YUNXIAO_ORG_ID')),
            'projex.project_id': projex.get('project_id'),
            'projex.workitem_type_id': projex.get('workitem_type_id'),
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            return 2
    except Exception:
        return 2

    # 4. 连通性（快速调用 --dry-run，若失败降级）
    # 不做实际网络调用以免 selftest 太慢。真失败会在 query 阶段退出 3
    return 0


# ============================================================
# 查询（调用上游脚本）
# ============================================================

def query(sprint_id=None):
    """调用 linscode/.../query_defects.py 并转换为契约格式"""
    cmd = ['python', str(LINSCODE_SCRIPT), '--json']
    if sprint_id:
        cmd += ['--sprint-id', sprint_id]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=str(PROJECT_ROOT),
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return None, 3
    except FileNotFoundError:
        return None, 1

    if result.returncode != 0:
        # 上游脚本的退出码映射到契约退出码
        stderr = result.stderr or ''
        if 'ImportError' in stderr or 'ModuleNotFoundError' in stderr:
            return None, 1
        if '401' in stderr or '403' in stderr or 'timeout' in stderr.lower():
            return None, 3
        return None, 4

    # 解析上游 JSON 输出
    try:
        upstream_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, 4

    return upstream_data, 0


def to_contract(upstream_data, sprint_id=None):
    """把上游脚本的 JSON 转换为契约格式"""
    by_severity_in = upstream_data.get('by_severity', {}) or {}

    # 严重等级映射（上游 normalize 后的 key → 契约 key）
    severity_map = {
        '致命': 'fatal', 'Fatal': 'fatal', 'blocker': 'fatal',
        '严重': 'critical', 'Critical': 'critical',
        '一般': 'major', 'Major': 'major', '主要': 'major',
        '轻微': 'minor', 'Minor': 'minor', '次要': 'minor', 'Trivial': 'minor',
        '环境阻塞': 'env_block', 'Env Block': 'env_block',
    }

    by_severity_out = {
        'fatal':     {'open': 0, 'closed': 0},
        'critical':  {'open': 0, 'closed': 0},
        'major':     {'open': 0, 'closed': 0},
        'minor':     {'open': 0, 'closed': 0},
        'env_block': {'open': 0},
    }

    total = 0
    for raw_key, counts in by_severity_in.items():
        contract_key = severity_map.get(raw_key, raw_key.lower())
        if contract_key not in by_severity_out:
            # 未知等级并入 minor
            contract_key = 'minor'
        open_cnt = counts.get('open', 0)
        closed_cnt = counts.get('closed', 0)
        by_severity_out[contract_key]['open'] = by_severity_out[contract_key].get('open', 0) + open_cnt
        if 'closed' in by_severity_out[contract_key]:
            by_severity_out[contract_key]['closed'] += closed_cnt
        total += open_cnt + closed_cnt

    return {
        'source': 'yunxiao',
        'query_time': datetime.now(timezone.utc).isoformat(),
        'sprint_id': sprint_id,
        'total': total,
        'by_severity': by_severity_out,
        # case_mapping / open_defects 需要上游脚本支持 --list-items 模式二次查询才能拿
        # v1.0 先置空，v1.1 再扩展
        'case_mapping': {},
        'open_defects': [],
        'notes': None,
    }


# ============================================================
# 主入口
# ============================================================

def main():
    # 自检模式
    if '--selftest' in sys.argv:
        sys.exit(selftest())

    # 解析参数
    sprint_id = None
    if '--sprint-id' in sys.argv:
        i = sys.argv.index('--sprint-id')
        if i + 1 < len(sys.argv):
            sprint_id = sys.argv[i + 1]

    # 执行查询
    upstream_data, rc = query(sprint_id)
    if rc != 0:
        sys.exit(rc)

    contract_output = to_contract(upstream_data, sprint_id)
    print(json.dumps(contract_output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == '__main__':
    main()
