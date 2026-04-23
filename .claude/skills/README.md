# `.claude/skills/` 目录身份索引

> 本目录下每个子目录的身份分 3 类：**override / local / shared**。本文件维护身份索引，避免混淆。
> 目录结构本身不区分身份（都在 `.claude/skills/<name>/` 一层），通过本索引和文件名约定区分。

## 📚 身份约定

| 身份 | 文件名约定 | 含义 |
|---|---|---|
| **override** | 目录下存在 `OVERRIDES.md` | 对 `linscode/skills/**/<name>/SKILL.md` 的本地覆盖层，Base + Override 合并执行 |
| **local** | 目录下存在 `SKILL.md` | 完全本地定义的技能，无上游 linscode 源 |
| **shared** | 目录名以 `_` 开头（如 `_shared`） | 共享资源（如变量语法说明），供其他技能引用 |

## 📋 当前索引（按身份分组）

### 🔧 Override（17 个）

对应 `linscode/skills/**/<name>/SKILL.md` 的本地覆盖：

| 目录 | Base（linscode 路径） |
|---|---|
| `acceptance-case-design/` | `iteration/testing/acceptance/acceptance-case-design/` |
| `api-test-case-design/` | `iteration/testing/api-test-case-design/` |
| `api-test-execution/` | `iteration/testing/api-test-execution/` |
| `backend-solution-review/` | `iteration/frontend-coding/requirements/backend-solution-review/` |
| `backend-tech-design-mvc/` | `iteration/technical-solution/backend-tech-design-mvc/` |
| `backend-tech-design-presentation/` | `iteration/technical-solution/backend-tech-design-presentation/` |
| `multimodal-visual-assertion/` | `iteration/testing/multimodal-visual-assertion/` |
| `release-gate/` | `iteration/testing/release-gate/`（引用 test-report quality-rules）|
| `submission-gate/` | `iteration/testing/submission-gate/`（引用 test-report quality-rules）|
| `tech-doc-review/` | `iteration/testing/tech-doc-review/` |
| `test-case-design/` | `iteration/testing/test-case-design/` |
| `test-case-prd-consistency/` | `iteration/testing/qa-tools/test-case-prd-consistency/` |
| `test-case-review/` | `iteration/testing/test-case-review/` |
| `test-data-preparation/` | `iteration/testing/test-data-preparation/` |
| `test-execution/` | `iteration/testing/test-execution/` |
| `test-point-extraction/` | `iteration/testing/test-point-extraction/` |
| `visual-location-fallback/` | `iteration/testing/visual-location-fallback/` |

### 🏠 Local（8 个）

无上游 linscode 源，本地独立维护：

| 目录 | 说明 |
|---|---|
| `acceptance-criteria/` | 基于需求文档的验收标准逐条检查 |
| `code-implementation/` | 基于 API 文档对比 mock 数据，生成接口联调实施计划 |
| `mark-case/` | 交互式勾选用例执行状态（人工用） |
| `requirements-update/` | 需求变更同步 |
| `session-recover/` | 会话恢复 |
| `system-function-analysis/` | 系统功能梳理（4 模式：代码→功能清单 / 文档→颗粒度 / 全新 PRD→需求分析 / 改造 PRD→变更影响） |
| `test-report/` | 测试报告生成（本地 v2.0，跨 skill 共享质量规则）|
| `yunxiao-sync/` | 测试用例同步到阿里云效 Testhub |

### 📦 Shared（1 个）

供其他技能引用的共享资源：

| 目录 | 内容 |
|---|---|
| `_shared/variable-syntax.md` | 变量命名语法规范 |

## 🛠️ 自动识别

工具脚本可通过下列逻辑自动判别身份（无需维护手工索引）：

```python
for d in Path('.claude/skills').iterdir():
    if not d.is_dir():
        continue
    if d.name.startswith('_'):
        identity = 'shared'
    elif (d / 'OVERRIDES.md').exists():
        identity = 'override'
    elif (d / 'SKILL.md').exists():
        identity = 'local'
    else:
        identity = 'unknown'  # 异常，需排查
```

参考 `C:/Users/1/.claude/tools/find_unregistered.py` 中的 `scan_claude_skills`。

## ⚠️ 变更规范

- **新增 override**：建 `<name>/OVERRIDES.md`，必含 frontmatter `based_on`（如 `harness@4.0.0`）和 `he_path`（指向 linscode 源）
- **新增 local**：建 `<name>/SKILL.md`，frontmatter 含 `name`、`description`、`version`
- **新增 shared**：目录名以 `_` 开头，不建 SKILL.md / OVERRIDES.md
- **同步 override 版本**：执行 `/check-overrides` 查一致性；HE 升级后须及时更新 `based_on`

---

*维护：自动化工具可直接读本文档或走扫描逻辑；人工新增/删除技能时请同步更新本索引。*
