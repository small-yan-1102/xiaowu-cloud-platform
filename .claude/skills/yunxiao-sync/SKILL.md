---
name: yunxiao-sync
version: 1.0.0
description: 将 Markdown 测试用例同步到阿里云效 Testhub，支持增量同步、模拟运行和模块过滤。
triggers:
  - 同步用例到云效
  - 同步到 Testhub
  - 推送用例到云效
  - yunxiao sync
  - 云效同步
---

# 云效 Testhub 同步工具

将项目中的 Markdown 格式测试用例自动同步到阿里云效 (Yunxiao) Testhub 进行管理。

## 功能

- 解析 Markdown 测试用例文件，提取用例结构化数据
- 自动创建云效 Testhub 目录结构（模块 → 子模块）
- 用例字段映射：编号、标题、步骤、预期结果、优先级等
- 增量同步：通过本地状态文件避免重复创建
- 模拟运行（dry-run）：验证解析和映射正确性
- 模块过滤：按需同步指定模块

## 前置条件

1. Python 3.8+
2. 安装依赖：`pip install requests pyyaml`
3. 配置文件：复制 `config.example.yaml` 为 `config.yaml`，填入个人访问令牌（PAT）、组织ID 等

## 使用方式

```bash
# 进入脚本目录
cd .claude/skills/yunxiao-sync/scripts

# 模拟同步企业认证模块（推荐首次使用）
python main.py --module enterprise_cert --dry-run --verbose

# 同步单个模块
python main.py --module enterprise_cert

# 同步多个模块
python main.py --module enterprise_cert --module login

# 同步所有模块
python main.py

# 列出可用模块
python main.py --list-modules

# 强制重新同步（清除本地已同步状态）
python main.py --module login --force
```

## CLI 参数

| 参数 | 缩写 | 说明 |
|------|------|------|
| `--config` | `-c` | 配置文件路径（默认 `config.yaml`） |
| `--module` | `-m` | 限定同步模块（可多次指定） |
| `--dry-run` | `-n` | 模拟模式，不调用云效 API |
| `--force` | `-f` | 忽略已同步状态，强制重建 |
| `--list-modules` | `-l` | 列出可用模块及用例数 |
| `--verbose` | `-v` | 输出 DEBUG 级别日志 |

## 配置说明

配置优先级：环境变量 > config.yaml > 默认值

| 环境变量 | 对应配置项 | 说明 |
|----------|-----------|------|
| `YUNXIAO_PAT` | `yunxiao.personal_access_token` | 个人访问令牌（PAT） |
| `YUNXIAO_ORG_ID` | `yunxiao.organization_id` | 云效组织 ID |
| `YUNXIAO_ASSIGNED_TO` | `yunxiao.assigned_to` | 默认负责人用户 ID |

## 文件结构

```
yunxiao-sync/
├── SKILL.md              # 本说明文件
├── config.example.yaml   # 配置模板（可提交 Git）
├── config.yaml           # 实际配置（含密钥，勿提交）
├── sync_state.json       # 同步状态（自动生成）
└── scripts/
    ├── __init__.py       # 包初始化
    ├── main.py           # CLI 入口
    ├── config.py         # 配置加载与校验
    ├── models.py         # 数据模型定义
    ├── md_parser.py      # Markdown 用例解析器
    ├── field_mapper.py   # 用例 → 云效字段映射
    ├── api_client.py     # 云效 OpenAPI HTTP 客户端
    └── sync_engine.py    # 同步编排引擎
```

## 支持的模块

| 模块键值 | 对应文件 | 说明 |
|----------|---------|------|
| `login` | `test_cases_login.md` | 登录模块 |
| `intro` | `test_cases_intro_page.md` | 介绍页模块 |
| `enterprise_cert` | `test_cases_enterprise_cert.md` | 企业认证模块 |
| `credits_center` | `test_cases_credits_center.md` | 积分中心模块 |
| `team_management` | `test_cases_team_management.md` | 团队管理模块 |
| `account_settings` | `test_cases_account_settings.md` | 账号设置模块 |
| `dashboard_overview` | `test_cases_dashboard_overview.md` | 数据总览模块 |
