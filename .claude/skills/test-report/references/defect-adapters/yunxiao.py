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

# 配置文件按优先级查找（避免把敏感 PAT 放进 linscode 仓库）：
#   1. 本地 .claude/skills/yunxiao-sync/config.yaml（yunxiao-sync skill 共用，已 gitignore）
#   2. linscode/lib/yunxiao/config.yaml（上游默认位置，不推荐）
CONFIG_CANDIDATES = [
    PROJECT_ROOT / '.claude' / 'skills' / 'yunxiao-sync' / 'config.yaml',
    PROJECT_ROOT / 'linscode' / 'lib' / 'yunxiao' / 'config.yaml',
]


def resolve_config_path():
    """返回第一个存在的配置文件路径，或 None"""
    for p in CONFIG_CANDIDATES:
        if p.exists():
            return p
    return None


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
    config_path = resolve_config_path()
    if config_path is None:
        return 2

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
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
    config_path = resolve_config_path()
    cmd = ['python', str(LINSCODE_SCRIPT), '--json']
    if config_path:
        cmd += ['--config', str(config_path)]
    if sprint_id:
        cmd += ['--sprint-id', sprint_id]

    try:
        # 不让 subprocess 自动 decode（Windows 上 query_defects.py 的 stdout 可能混 cp936）
        # 自己按 utf-8 + errors='replace' 解码，容错
        env = dict(os.environ)
        env['PYTHONIOENCODING'] = 'utf-8'  # 迫使上游脚本用 utf-8 输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            cwd=str(PROJECT_ROOT),
            timeout=30,
            env=env,
        )
        stdout = result.stdout.decode('utf-8', errors='replace')
        stderr = result.stderr.decode('utf-8', errors='replace')
        returncode = result.returncode
    except subprocess.TimeoutExpired:
        return None, 3
    except FileNotFoundError:
        return None, 1

    # 把 stdout / stderr 合并当 payload 做错误分析（上游脚本会把 HTTP 错误写到 stdout 而非 stderr）
    combined = (stdout or '') + (stderr or '')

    if returncode != 0:
        # 上游脚本的退出码映射到契约退出码
        if 'ImportError' in combined or 'ModuleNotFoundError' in combined:
            return None, 1
        # HTTP 4xx/5xx / 认证 / 超时 / API schema 错误 → 归为"网络/权限/API 失败"
        if any(k in combined for k in ['HTTP 4', 'HTTP 5', '401', '403', 'timeout',
                                         'InvaildData', '不能为空', 'InvalidData']):
            return None, 3
        return None, 4

    # 解析上游 JSON 输出（有时 returncode=0 但 stdout 含 error 字段）
    try:
        upstream_data = json.loads(stdout)
    except json.JSONDecodeError:
        return None, 4

    # 上游脚本在 API 错误时可能仍返回 exit 0，但 JSON 里含 error 字段
    if isinstance(upstream_data, dict) and 'error' in upstream_data:
        return None, 3

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
