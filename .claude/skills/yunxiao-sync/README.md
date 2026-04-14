# 云效测试工具集

将 Markdown 格式的测试用例自动同步到阿里云效 (Yunxiao) Testhub，支持增量同步、模块过滤、模拟运行、测试结果回写和缺陷自动提交。

---

## 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [使用方式](#使用方式)
  - [用例同步](#用例同步)
  - [测试结果回写](#测试结果回写)
  - [缺陷创建](#缺陷创建)
- [CLI 参数](#cli-参数)
  - [用例同步参数 (main.py)](#用例同步参数-mainpy)
  - [缺陷创建参数 (create_defect.py)](#缺陷创建参数-create_defectpy)
- [文件结构](#文件结构)
- [工作原理](#工作原理)
- [常见问题](#常见问题)

---

## 功能特性

| 功能 | 说明 |
|------|------|
| Markdown 解析 | 自动解析 Markdown 测试用例文件，提取编号、标题、步骤、预期结果、优先级等结构化数据 |
| 目录自动创建 | 根据用例的模块/子模块结构，自动在云效 Testhub 创建对应目录 |
| 增量同步 | 通过本地状态文件 (`sync_state.json`) 记录已同步用例，避免重复创建 |
| 模块过滤 | 按模块名筛选，仅同步指定模块的用例 |
| 模拟运行 | `--dry-run` 模式仅解析和映射，不调用云效 API，适合首次验证 |
| 强制重建 | `--force` 模式忽略已同步状态，重新创建/更新所有用例 |
| 测试结果回写 | 将 AI 执行测试的结果（通过/失败等）同步到云效测试计划 |
| 缺陷自动提交 | 将测试失败结果自动创建为云效 Projex 缺陷工作项，支持单条和从报告批量创建 |
| 多项目路由 | 按 case_id 前缀自动路由缺陷到不同项目（AMS/CRM/JQB 等），支持手动指定 |
| Sprint 自动管理 | 指定迭代名称自动创建或复用已有 Sprint，按项目独立管理 |
| 前后端负责人 | 支持按 frontend/backend 指定缺陷负责人，从项目配置中读取 |
| 自动重试 | API 调用失败时自动重试（指数退避），防限流 |

---

## 环境要求

- **Python**: 3.8 及以上
- **依赖库**: `requests`, `pyyaml`
- **网络**: 可访问 `https://openapi-rdc.aliyuncs.com`
- **云效权限**: 个人访问令牌 (PAT) 需具备「测试管理」和「项目协作」读写权限

---

## 快速开始

### 1. 安装依赖

```bash
pip install requests pyyaml
```

### 2. 创建配置文件

```bash
cd .claude/skills/yunxiao-sync
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填入以下信息：

```yaml
yunxiao:
  personal_access_token: "pt-your-token-here"  # 个人访问令牌
  organization_id: "your-org-id"                # 组织ID
  space_identifier: "your-space-id"             # 用例库ID
  assigned_to: "your-user-id"                   # 负责人用户ID

# 缺陷创建功能需要额外配置
projex:
  project_id: "your-projex-project-id"       # Projex 项目ID（非 Testhub 用例库ID）
  workitem_type_id: "your-bug-type-id"       # 缺陷类型ID
  severity_option_id: "your-severity-id"     # 严重程度选项ID
  priority_option_id: "your-priority-id"     # 优先级选项ID
  sprint_id: "your-sprint-id"               # 迭代ID（可选）
```

> **安全提示**: `config.yaml` 包含敏感令牌，已被 `.gitignore` 排除，请勿提交到版本库。

### 3. 验证配置（模拟运行）

```bash
cd .claude/skills/yunxiao-sync/scripts
python main.py --dry-run --verbose
```

### 4. 正式同步

```bash
python main.py
```

---

## 配置说明

### 配置文件

复制 `config.example.yaml` 为 `config.yaml`，按注释填写各字段。

### 配置优先级

环境变量 > `config.yaml` > 默认值

### 环境变量

| 环境变量 | 对应配置项 | 说明 |
|----------|-----------|------|
| `YUNXIAO_PAT` | `yunxiao.personal_access_token` | 个人访问令牌 |
| `YUNXIAO_ORG_ID` | `yunxiao.organization_id` | 云效组织 ID |
| `YUNXIAO_ASSIGNED_TO` | `yunxiao.assigned_to` | 默认负责人用户 ID |

### 获取配置值的方法

| 配置项 | 获取路径 |
|--------|---------|
| **PAT 令牌** | 云效 -> 右上角头像 -> 个人设置 -> 个人访问令牌 -> 新建（勾选「测试管理」+「项目协作」权限） |
| **组织 ID** | 云效控制台 -> 设置 -> 组织信息 -> 组织ID |
| **用例库 ID** | 云效 -> 测试管理 -> 用例库 -> 用例库设置 -> 用例库ID |
| **项目 ID** | 云效 -> 项目协作 -> 进入项目 -> 项目设置 -> 基本信息 -> 项目ID |
| **用户 ID** | 云效 -> 设置 -> 成员管理 -> 点击用户查看 ID |

### 同步行为配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `sync.md_case_dir` | (见模板) | Markdown 用例目录（相对项目根目录） |
| `sync.modules` | `[]` (全部) | 限定同步的模块列表 |
| `sync.dry_run` | `false` | 模拟模式 |
| `sync.batch_size` | `10` | 每批次处理数量（防 API 限流） |
| `sync.retry_count` | `3` | API 失败重试次数 |
| `sync.retry_delay` | `2` | 重试基础间隔（秒，实际按指数递增） |

### 缺陷创建配置

**多项目模式 (`projects`)** - 推荐:

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `projects.{KEY}.name` | 是 | 项目显示名称 |
| `projects.{KEY}.prefix_patterns` | 是 | case_id 前缀匹配规则列表（如 `["AMS-"]`） |
| `projects.{KEY}.project_id` | 是 | Projex 项目ID |
| `projects.{KEY}.workitem_type_id` | 是 | 缺陷工作项类型ID |
| `projects.{KEY}.severity_options` | 是 | 严重程度名称→ID 映射（致命/严重/一般/轻微） |
| `projects.{KEY}.priority_options` | 是 | 优先级名称→ID 映射（紧急/高/中/低） |
| `projects.{KEY}.default_severity` | 否 | 默认严重程度（默认 "一般"） |
| `projects.{KEY}.default_priority` | 否 | 默认优先级（默认 "中"） |
| `projects.{KEY}.assignees.frontend` | 否 | 前端负责人 user_id |
| `projects.{KEY}.assignees.backend` | 否 | 后端负责人 user_id |
| `projects.{KEY}.assignees.default` | 否 | 默认负责人 user_id |

> 使用 `python create_defect.py --init-projects` 查询组织所有项目，获取 project_id 等配置值。

**旧单项目模式 (`projex`)** - 向后兼容:

| 配置项 | 必填 | 说明 |
|--------|------|------|
| `projex.project_id` | 是 | Projex 项目ID |
| `projex.workitem_type_id` | 是 | 缺陷工作项类型ID |
| `projex.severity_option_id` | 是 | 严重程度选项ID |
| `projex.priority_option_id` | 是 | 优先级选项ID |
| `projex.default_assignee` | 否 | 缺陷默认指派人 |
| `projex.sprint_id` | 否 | 关联迭代ID |

---

## 使用方式

### 用例同步

用例同步工具（`main.py`）将 Markdown 测试用例推送到云效 Testhub 用例库。

```bash
cd .claude/skills/yunxiao-sync/scripts

# 列出所有可用模块及用例数
python main.py --list-modules

# 模拟同步指定模块（推荐首次使用）
python main.py --module team_management --dry-run --verbose

# 同步单个模块
python main.py --module team_management

# 同步多个模块
python main.py --module team_management --module login

# 同步所有模块
python main.py

# 强制重新同步（清除本地已同步状态，重新创建）
python main.py --module login --force
```

### 测试结果回写

测试结果回写工具（`sync_test_results.py`）将 AI 执行测试的通过/失败结果同步到云效测试计划。

```bash
cd .claude/skills/yunxiao-sync/scripts
python sync_test_results.py
```

**工作流程**:
1. 从 `config.yaml` 读取云效认证信息
2. 从 `sync_state.json` 读取用例的云效 ID 映射
3. 调用云效 API 更新测试计划中每条用例的执行状态

**API 参数映射**:

| 本地结果 | 云效 status | 说明 |
|----------|------------|------|
| `passed` | `PASS` | 通过 |
| `failed` | `FAILURE` | 失败 |
| `blocked` | `POSTPONE` | 阻塞/延期 |
| `skipped` | `TODO` | 待执行 |

> **注意**: 使用此脚本前，需先通过 `main.py` 完成用例同步，以生成 `sync_state.json` 中的 ID 映射。

### 缺陷创建

缺陷创建工具（`create_defect.py`）将测试失败结果自动提交为云效 Projex 缺陷（Bug）工作项。v2 版本支持多项目路由、Sprint 自动创建和前后端负责人指派。

#### 前置条件

1. `config.yaml` 中已配置 `yunxiao` 基础认证信息
2. `config.yaml` 中已配置 `projects` 多项目配置（推荐），或 `projex` 旧单项目配置
3. PAT 令牌需具备「项目协作」写权限

#### 配置模式

**推荐: 多项目模式 (`projects`)**

在 `config.yaml` 中配置多个项目，工具按 case_id 前缀自动路由：

```yaml
projects:
  AMS:
    name: "AMS"
    prefix_patterns: ["AMS-"]      # AMS-VTD-002 → 匹配此项目
    project_id: "your-ams-project-id"
    workitem_type_id: "your-bug-type-id"
    severity_options:
      致命: "id1"
      严重: "id2"
      一般: "id3"
      轻微: "id4"
    default_severity: "一般"
    priority_options:
      紧急: "id1"
      高: "id2"
      中: "id3"
      低: "id4"
    default_priority: "中"
    assignees:
      frontend: "frontend-user-id"
      backend: "backend-user-id"
      default: "default-user-id"
  CRM:
    name: "CRM"
    prefix_patterns: ["CRM-"]
    # ... 同上
```

**获取配置值**: 使用 `--init-projects` 查询组织所有项目：

```bash
python create_defect.py --init-projects
```

**兼容: 旧单项目模式 (`projex`)**

当 `projects` 中无法匹配到项目时，自动回退到 `projex` 配置。

#### 单条缺陷创建

```bash
cd .claude/skills/yunxiao-sync/scripts

# 自动匹配项目（AMS-VTD-002 → AMS 项目）+ 自动创建 Sprint
python create_defect.py \
  --case-id AMS-VTD-002 \
  --title "按视频ID搜索失败" \
  --actual "无结果返回" \
  --sprint "冒烟测试-20260330" \
  --assignee-type backend

# 手动指定项目（覆盖自动匹配）
python create_defect.py \
  --case-id X-001 --project AMS \
  --title "测试缺陷" --actual "实际结果" \
  --sprint "v2.0.0"

# 指定严重程度和优先级
python create_defect.py \
  --case-id JQB-TEAM-042 \
  --title "移除成员后列表未刷新" \
  --actual "成员仍显示在列表中" \
  --severity "严重" --priority "高"
```

#### 从测试报告批量创建

```bash
# 按 case_id 前缀自动路由到不同项目，按项目独立创建 Sprint
python create_defect.py \
  --from-report test_reports/test_report_20260330_smoke.md \
  --sprint "冒烟测试-20260330"

# 模拟模式（不实际调用 API）
python create_defect.py \
  --from-report test_report.md --sprint "v2.0" --dry-run

# CI/CD 场景（禁用交互式提示）
python create_defect.py \
  --from-report test_report.md --sprint "v2.0" --no-interactive
```

**批量模式特性**:
- 按 case_id 前缀自动路由到不同项目
- 同名 Sprint 按项目独立创建（AMS 和 JQB 各自有独立的同名 Sprint）
- Sprint 缓存机制：同项目只创建/查询一次
- 输出项目分布统计（如 `AMS=3, JQB=2, CRM=1`）

#### 截图上传

工具支持将截图文件作为附件上传到云效缺陷工作项，采用三步 OSS 上传流程（获取凭证 → 上传 OSS → 关联附件），并提供 4 级降级策略确保缺陷创建不受截图上传失败影响。

```bash
# 单条缺陷：指定截图文件（支持 glob 模式和逗号分隔多个）
python create_defect.py \
  --case-id AMS-VTD-002 \
  --title "视频ID复用导致创建失败" \
  --steps "步骤8" --expected "创建中" --actual "创建失败" \
  --screenshot "test_reports/screenshots/2026-03-30/CP1_AMS-VTD-002_*.png"

# 批量模式：自动按用例ID发现截图
python create_defect.py \
  --from-report test_reports/test_report_20260330_smoke.md \
  --screenshots-dir test_reports/screenshots

# 禁用上传：仅在描述中以文本引用截图路径
python create_defect.py \
  --from-report test_report.md --no-upload
```

**截图自动发现规则**（批量模式）:
- 在 `--screenshots-dir`（默认 `test_reports/screenshots`）下递归搜索
- 匹配文件名包含用例编号的图片（支持连字符/下划线变体）
- 命名格式: `{CP级别}_{用例编号}_{步骤}_{状态}_{时间戳}.png`

**降级策略**:

| 级别 | 条件 | 行为 |
|------|------|------|
| L1 | 上传成功 | 截图作为附件关联到工作项 |
| L2 | OSS上传或关联失败 | 回退为描述中的文本引用 |
| L3 | API 不可用（凭证获取失败） | 仅文本引用 |
| L4 | 截图文件不存在 | 跳过 |

#### 缺陷描述格式

工具自动生成的缺陷描述包含以下 Markdown 章节：

```markdown
## 关联用例
JQB-TEAM-042

## 重现步骤
1.进入团队管理页面 2.点击移除 3.确认移除

## 预期结果
成员从列表消失

## 实际结果
成员仍显示在列表中

## 测试环境
https://test-dramarightsbao.xiaowuxiongdi.com
```

---

## CLI 参数

### 用例同步参数 (main.py)

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--config PATH` | `-c` | 配置文件路径（默认 `../config.yaml`） |
| `--module NAME` | `-m` | 限定同步模块（可多次指定） |
| `--dry-run` | `-n` | 模拟模式，仅解析和映射，不调用云效 API |
| `--force` | `-f` | 忽略已同步状态，强制重新创建/更新 |
| `--list-modules` | `-l` | 列出可用模块及用例数量 |
| `--verbose` | `-v` | 输出 DEBUG 级别日志 |

### 缺陷创建参数 (create_defect.py)

**基础参数**:

| 参数 | 说明 |
|------|------|
| `--case-id ID` | 关联测试用例编号（如 AMS-VTD-002, JQB-TEAM-042） |
| `--title TEXT` | 缺陷标题（必填） |
| `--steps TEXT` | 重现步骤 |
| `--expected TEXT` | 预期结果 |
| `--actual TEXT` | 实际结果（与 --steps 至少提供一个） |
| `--assigned-to ID` | 指派人用户ID（直接指定，覆盖所有其他规则） |
| `--environment URL` | 测试环境地址 |

**多项目参数** (v2 新增):

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--project KEY` | `-p` | 手动指定目标项目标识（如 AMS, JQB），覆盖 case_id 自动匹配 |
| `--sprint NAME` | `-s` | 迭代名称，不存在则自动创建（如 "冒烟测试-20260330"） |
| `--assignee-type TYPE` | | 指派给前端或后端负责人（`frontend` / `backend`） |
| `--severity LEVEL` | | 覆盖严重程度（致命/严重/一般/轻微） |
| `--priority LEVEL` | | 覆盖优先级（紧急/高/中/低） |
| `--no-interactive` | | 禁止交互式提示（CI/CD 场景） |
| `--init-projects` | | 查询组织所有项目元数据 |

**截图参数**:

| 参数 | 说明 |
|------|------|
| `--screenshot FILE` | 截图文件路径，支持逗号分隔多个或 glob 模式 |
| `--screenshots-dir DIR` | 截图根目录，批量模式下按用例ID自动发现截图 |
| `--no-upload` | 禁用截图上传，仅在描述中以文本引用 |

**通用参数**:

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--from-report PATH` | | 从测试报告批量创建失败用例的缺陷 |
| `--dry-run` | `-n` | 模拟模式，不实际调用 API |
| `--config PATH` | `-c` | 配置文件路径 |

---

## 文件结构

```
yunxiao-sync/
├── README.md                # 本说明文档
├── SKILL.md                 # Qoder Skill 描述文件
├── config.example.yaml      # 配置模板（安全，可提交 Git）
├── config.yaml              # 实际配置（含令牌，已 gitignore）
├── sync_state.json          # 同步状态（自动生成，已 gitignore）
└── scripts/
    ├── __init__.py           # 包初始化
    ├── main.py               # CLI 入口 - 用例同步
    ├── sync_test_results.py  # 测试结果回写脚本
    ├── create_defect.py      # 缺陷创建工具
    ├── config.py             # 配置加载与校验
    ├── models.py             # 数据模型（TestCase, SyncResult 等）
    ├── md_parser.py          # Markdown 用例解析器
    ├── field_mapper.py       # 用例字段 -> 云效字段映射
    ├── api_client.py         # 云效 OpenAPI HTTP 客户端
    └── sync_engine.py        # 同步编排引擎
```

---

## 工作原理

### 用例同步流程

```
Markdown 用例文件
       |
       v
+------------------+
|  md_parser.py    |  解析 Markdown，提取结构化用例数据
+--------+---------+
         v
+------------------+
|  field_mapper.py |  将用例字段映射为云效 API 请求参数
+--------+---------+
         v
+------------------+
|  sync_engine.py  |  编排: 目录创建 -> 去重检查 -> 批量同步
+--------+---------+
         v
+------------------+
|  api_client.py   |  调用云效 OpenAPI（PAT 认证 + 自动重试）
+--------+---------+
         v
   云效 Testhub 用例库
```

### 缺陷创建流程 (v2)

```
测试失败信息（手动输入 或 测试报告解析）
       |
       v
+--------------------+
| 1. resolve_project |  按 case_id 前缀 / --project / 交互选择 → 确定目标项目
+--------+-----------+
         v
+--------------------+
| 2. resolve_sprint  |  按 --sprint 名称查找已有迭代，不存在则自动创建
+--------+-----------+    POST /projects/{pid}/sprints
         v
+--------------------+
| 3. resolve_assignee|  --assigned-to > --assignee-type > 交互选择 > 项目默认
+--------+-----------+
         v
+--------------------+
| 4. create_workitem |  POST /workitems?spaceId={projectId}
| (Projex Open API)  |  body: subject, assignedTo, sprint, customFieldValues
+--------+-----------+
         v
   缺陷工作项已创建 (workitem_id)
         |
         v  (如有截图文件)
+--------------------+
| 5. 截图附件上传     |  获取凭证 → 上传 OSS → 关联附件
+--------------------+
         |
    降级策略: L1(成功) → L2(OSS失败) → L3(API不可用) → L4(文件不存在)
```

### 增量同步机制

1. 每次同步后，工具将「本地用例编号 -> 云效用例 ID」映射保存到 `sync_state.json`
2. 下次同步时，先比对本地状态，已存在的用例自动跳过
3. 使用 `--force` 可清除状态，强制重新同步
4. 首次运行且无本地状态时，工具会查询云效远端进行去重

### 云效 API 认证方式

使用**个人访问令牌 (PAT)** 认证，通过 HTTP 请求头 `x-yunxiao-token` 传递：

```
x-yunxiao-token: pt-xxxx****xxxx
```

API 域名（中心版）: `https://openapi-rdc.aliyuncs.com`

### 支持的模块

| 模块键值 | 对应用例文件 | 说明 |
|----------|-------------|------|
| `login` | `test_cases_login.md` | 登录模块 |
| `intro` | `test_cases_intro_page.md` | 介绍页模块 |
| `enterprise_cert` | `test_cases_enterprise_cert.md` | 企业认证模块 |
| `credits_center` | `test_cases_credits_center.md` | 积分中心模块 |
| `team_management` | `test_cases_team_management.md` | 团队管理模块 |
| `account_settings` | `test_cases_account_settings.md` | 账号设置模块 |
| `dashboard_overview` | `test_cases_dashboard_overview.md` | 数据总览模块 |

---

## 常见问题

### Q: 认证失败 (302 重定向)

**原因**: PAT 令牌无效或权限不足。

**解决**:
1. 确认 `config.yaml` 中的 `personal_access_token` 正确
2. 确认令牌勾选了「测试管理」和「项目协作」相关权限
3. 检查令牌是否已过期

### Q: HTTP 400 "status and operator both not exist"

**原因**: 测试结果回写时请求参数格式错误。

**解决**: 确保使用的是 `status` (PASS/FAILURE/TODO/POSTPONE) 和 `executor` (用户ID) 字段，而非 `result`。

### Q: 缺陷创建失败，提示配置校验错误

**原因**: 配置不完整。

**解决**: 推荐使用多项目模式，确保 `yunxiao` 认证信息和 `projects` 配置完整：
```bash
# 查询组织项目信息
python create_defect.py --init-projects
```
如使用旧 `projex` 模式，确保所有必填项已配置。

### Q: case_id 无法匹配到项目

**原因**: case_id 前缀不在任何项目的 `prefix_patterns` 中。

**解决**:
1. 使用 `--project AMS` 手动指定项目
2. 或在 `config.yaml` 的对应项目中添加 `prefix_patterns`

### Q: 缺陷创建返回 "工作项类型未启用"

**原因**: 使用了错误的 `project_id`（如 Testhub 用例库ID），或该项目未启用 Bug 工作项类型。

**解决**:
1. 确认 `projex.project_id` 来自 `testPlan/list` 返回的 `spaceIdentifier`
2. 确认项目的 `workitemTypes?category=Bug` 返回非空列表

### Q: 同步时提示用例已存在但云效中找不到

**原因**: 本地 `sync_state.json` 与云效实际状态不一致。

**解决**: 使用 `--force` 参数强制重新同步：
```bash
python main.py --module team_management --force
```

### Q: API 限流 (429 / Throttling)

**原因**: 短时间内请求过于频繁。

**解决**: 工具内置自动重试（指数退避）。如仍频繁限流，可调大 `config.yaml` 中的 `batch_size` 间隔或 `retry_delay`。

### Q: 如何新增模块支持

1. 在用例目录下新建 `test_cases_<module_name>.md` 文件
2. 按照 `ai_test_case_design.md` 规范编写用例
3. 运行 `python main.py --list-modules` 确认模块已被识别
4. 运行 `python main.py --module <module_name> --dry-run` 验证解析
