# Defect Source Adapter 契约

> **版本**：v1.0
> **用途**：统一 `test-report` 加载不同缺陷源的接口，让 SKILL 与具体缺陷管理系统（云效 / Jira / Markdown 清单 / ...）解耦。
> **所在位置**：`.claude/skills/test-report/references/defect-adapters/`

---

## 一、Adapter 类型清单

本项目目前提供的 adapter：

| 文件 | 数据源 | 用途 |
|---|---|---|
| `yunxiao.py` | 阿里云云效 Projex | 生产环境主选 |
| `markdown.py` | `bug_reports/bug-report-*.md` | 本地降级 / 小项目 |

添加新 adapter：复制任一现有文件，按本契约实现接口。

---

## 二、命令行接口

### 必需支持的参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `--json` | flag | 输出 JSON 格式到 stdout |
| `--selftest` | flag | 自检模式：检查依赖/配置/连通性，不输出数据 |
| `--sprint-id <id>` | string（可选）| 限定特定迭代/Sprint |

### 调用示例

```bash
# 主查询
python yunxiao.py --json

# 限定迭代
python yunxiao.py --json --sprint-id 12345

# 自检（Phase 0.5 用）
python yunxiao.py --selftest
```

---

## 三、输出契约（stdout JSON）

### 完整结构

```json
{
  "source": "yunxiao",
  "query_time": "2026-04-23T10:30:00Z",
  "sprint_id": "12345",
  "total": 15,
  "by_severity": {
    "fatal": {
      "open": 0,
      "closed": 0
    },
    "critical": {
      "open": 0,
      "closed": 1
    },
    "major": {
      "open": 2,
      "closed": 5
    },
    "minor": {
      "open": 1,
      "closed": 6
    },
    "env_block": {
      "open": 0
    }
  },
  "case_mapping": {
    "BUG-001": ["PRJ-TEAM-002", "PRJ-TEAM-003"],
    "BUG-002": ["PRJ-AUTH-005"]
  },
  "open_defects": [
    {
      "id": "BUG-002",
      "title": "登录失败",
      "severity": "major",
      "status": "open",
      "assignee": "张三",
      "created_at": "2026-04-20",
      "url": "https://..."
    }
  ],
  "notes": null
}
```

### 字段说明

| 字段 | 必需 | 说明 |
|---|---|---|
| `source` | ✅ | adapter 标识（"yunxiao" / "markdown" / ...）|
| `query_time` | ✅ | ISO 8601 时间戳（UTC）|
| `sprint_id` | ❌ | 限定的迭代 ID，无则 null |
| `total` | ✅ | 缺陷总数（Open + Closed 之和）|
| `by_severity` | ✅ | 5 个等级 × `open` / `closed`（`env_block` 只有 `open`）|
| `case_mapping` | ⚠️ | 缺陷→关联用例映射。无法提供则 `{}`（空对象）|
| `open_defects` | ⚠️ | 开放缺陷详情（用于报告 §4.3 展示）。无法提供则 `[]` |
| `notes` | ❌ | 补充说明（降级原因 / 数据局限等），无则 null |

**必需字段** 全部缺失 → 退出码非 0
**可选字段** 缺失 → 对应章节显示"无数据"但不阻断

---

## 四、退出码规范

| 码 | 含义 | Phase 0.5 处理 |
|---|---|---|
| 0 | 成功，输出完整 JSON | 选用此 adapter |
| 1 | 依赖缺失（Python 包未安装）| 降级下一个 adapter |
| 2 | 配置错误（yaml 丢失 / 字段缺失）| 降级 |
| 3 | 网络/权限错误（API 401/403/超时）| 降级 |
| 4 | 数据解析错误（源数据格式异常）| 降级 + 记录 notes |
| 其他非 0 | 未预期错误 | 降级 + 记录 |

`--selftest` 时只返回退出码，不输出 JSON。

---

## 五、实现指南（给 adapter 作者）

### 最小骨架

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""{Source 名} Defect Source Adapter"""
import sys, json
from datetime import datetime, timezone

def selftest():
    """检查依赖、配置、连通性。成功返回 0，失败返回 1-3"""
    try:
        # 1. 检查依赖
        import requests  # 示例
        # 2. 检查配置
        # 3. 尝试连通性（ping API / 读取文件）
        return 0
    except ImportError:
        return 1
    except (FileNotFoundError, KeyError):
        return 2
    except Exception:
        return 3

def query(sprint_id=None):
    """查询并返回符合契约的 dict"""
    return {
        "source": "example",
        "query_time": datetime.now(timezone.utc).isoformat(),
        "sprint_id": sprint_id,
        "total": 0,
        "by_severity": {
            "fatal":     {"open": 0, "closed": 0},
            "critical":  {"open": 0, "closed": 0},
            "major":     {"open": 0, "closed": 0},
            "minor":     {"open": 0, "closed": 0},
            "env_block": {"open": 0}
        },
        "case_mapping": {},
        "open_defects": [],
        "notes": None
    }

def main():
    if '--selftest' in sys.argv:
        sys.exit(selftest())
    sprint_id = None
    if '--sprint-id' in sys.argv:
        i = sys.argv.index('--sprint-id')
        if i + 1 < len(sys.argv):
            sprint_id = sys.argv[i + 1]
    try:
        result = query(sprint_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    except ImportError:
        sys.exit(1)
    except (FileNotFoundError, KeyError):
        sys.exit(2)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(4)

if __name__ == '__main__':
    main()
```

### 严重等级映射

不同缺陷系统的等级字段可能不同，adapter 内部统一映射到契约的 5 等级：

| 契约等级 | 云效字段 | Jira | 常见中文 |
|---|---|---|---|
| fatal | 致命 | Blocker | 阻断 / 致命 |
| critical | 严重 | Critical | 严重 |
| major | 一般 | Major | 主要 / 一般 |
| minor | 轻微 | Minor / Trivial | 轻微 / 次要 |
| env_block | — | — | 环境阻塞（非代码缺陷）|

### JSON 输出规范

- **UTF-8** 编码（`ensure_ascii=False`）
- **2 空格缩进**（`indent=2`）便于人工 debug
- **stdout 仅输出 JSON**，错误信息走 stderr

---

## 六、配置文件约定（可选）

若 adapter 需要凭证/端点配置：

**位置**：`.claude/config/defect-source.yaml`

```yaml
default_source: yunxiao  # Phase 0.5 默认尝试的 adapter

yunxiao:
  personal_access_token: "${YUNXIAO_PAT}"  # 环境变量
  organization_id: "xxx"
  project_id: "xxx"
  workitem_type_id: "xxx"
  endpoint: "https://openapi.aliyun.com/..."

markdown:
  pattern: "iterations/{iteration}/review/bug_reports/bug-report-*.md"
  # 其他配置...
```

**读取方式**：adapter 自己读此文件，不经过 SKILL。SKILL 只负责调用 adapter 命令行。

---

## 七、测试建议

每个 adapter 应有以下测试：

1. **selftest 模式**：
   - 依赖完整时退出 0
   - 缺包时退出 1
   - 配置错误时退出 2

2. **query 模式**：
   - 空数据源 → 输出 total=0 的合规 JSON
   - 真实数据 → 输出符合契约的 JSON
   - 数据格式异常 → 退出 4 + stderr 错误信息

3. **JSON 合规性**：
   - 必需字段全部存在
   - 严重等级映射正确
   - UTF-8 编码

---

*版本：v1.0 | 最后更新：2026-04-23*
