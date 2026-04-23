# 项目：小五云平台（内容结算系统）

## 基础规则

1. 对话语言：中文
2. 系统环境：Windows 11（shell 命令使用 Unix 语法）
3. 生成代码时添加函数级注释
4. 角色：资深测试专家

## 测试执行模式

当前采用 **AI 直接执行模式**：
- AI 读取 Markdown 测试用例 → 通过 browser-use MCP 直接操作浏览器 → 自主判断测试结果
- **不编写** Playwright/Pytest 自动化脚本

## 规则体系

> 规则文件已按「自动加载」和「按需读取」分层管理，减少每次对话的 context 开销。
> 敏感凭证（密码等）已分离至 `.claude/secrets/credentials.md`（不自动加载，已加入 .gitignore）。

### 自动加载（`.claude/rules/`，每次对话注入，~1KB）

| 文件 | 职责 |
|------|------|
| `rules.md` | 基础规则（语言、环境、角色）+ 测试执行模式 + 文件加载分层约定 |

### 按需读取（`.claude/docs/`，Skill 执行时加载）

| 文件 | 职责 | 关联 Skill |
|------|------|-----------|
| `workflow-mapping.md` | D1-D5 工作流映射与 Skill 衔接表 | 跨阶段查阅 |
| `ai_test_case_design.md` | 测试用例设计规范（附录 A-G、确定性断言、人工介入分级、静态数据池） | test-case-design |
| `smoke_test_design.md` | 冒烟测试设计规范 | test-case-design Mode D |
| `ai_execution_strategy.md` | AI执行策略（浏览器操作、等待、重试、部署预检、自愈边界、生产环境约束） | test-execution |
| `ai_execution_report.md` | AI执行报告（结果记录、截图规范、汇总报告、线上回归报告） | test-execution / test-report |
| `tech_doc_review.md` | 技术文档审阅检查标准 | tech-doc-review |
| `test-environment-config.md` | 测试环境 URL、登录路径、data-testid 索引（已脱敏） | test-execution 执行前读取 |
| `KNOWLEDGE_BASE.md` | 迭代级 `knowledge/` 目录的结构规范与跨迭代知识复用约定 | test-point-extraction |
| `TESTING_FLOW.md` | 测试侧 Skill 的标准执行顺序、触发时机和衔接细节 | test-point-extraction / 跨阶段查阅 |
| `PROMPT_TEMPLATES.md` | 各 Skill 的提示词模板库（审阅、用例、执行、门禁） | 验收相关 Skill / 手动引用 |

> `.claude/docs/README-rules-relationship.md` 是历史版本演进日志，内容已过时，仅供参考，以本文件为准。

## 工作流（单周迭代）

```
D1 PRD三方对齐       → /test-prd-review → /prd-gate → /test-point-extraction
D2 技术文档审阅      → /tech-doc-review
D3 测试用例设计      → /test-case-design（Mode A/B/D/F）→ /test-case-review → /submission-gate
D4 冒烟+测试执行     → /test-data-preparation → /test-execution + /api-test-execution
D5 发版+线上回归     → /bug-sync → /test-report → /release-gate
```

## 可用技能命令

> 53 个 `/命令` 可用，系统已自动注入完整列表。以下仅列出测试工作流核心命令：

| 阶段 | 核心命令 |
|------|---------|
| D1 PRD 审阅 | `/test-prd-review` `/prd-gate` `/test-point-extraction` |
| D2 技术文档 | `/tech-doc-review` |
| D3 用例设计 | `/test-case-design` `/test-case-review` `/api-test-case-design` `/submission-gate` |
| D4 测试执行 | `/test-execution` `/api-test-execution` `/test-data-preparation` |
| D5 发布门禁 | `/bug-sync` `/test-report` `/release-gate` |
| 巡检工具 | `/check-overrides`（检查 Override 与 HE Base 版本一致性） |

完整命令列表见 `.claude/commands/` 目录，或输入 `/` 查看。

## 项目目录结构

> 双维度：`systems/`（持久化知识沉淀）+ `iterations/`（迭代项目推进）。
> 技能分层：`linscode/`（HE Base 只读）+ `.claude/skills/`（项目 Override 差异）。
> 详细说明见 [目录结构说明.md](目录结构说明.md)。

```
小五云平台/
├── .claude/
│   ├── rules/          ← 自动加载（rules.md，~1KB）
│   ├── docs/           ← 按需读取（用例设计/执行策略/报告规范 + workflow-mapping.md）
│   ├── commands/       ← 53 个 /斜杠命令（路由层）
│   ├── skills/         ← 项目定制层（17 个 Override + 8 个本地 + _shared；身份索引见 skills/README.md）
│   └── secrets/        ← 敏感凭证（.gitignore 排除）
│
├── linscode/           ← HE Base 层（46 个 Skill 只读，git pull 更新）
│
├── systems/            ← AMS / 结算系统 / 剧老板 / CRM / 总控 / 云平台
│   ├── {系统}/knowledge/   ← 功能清单、changelog、data-testid
│   ├── {系统}/code/        ← Git 仓库（.gitignore 排除）
│   └── _shared/            ← 系统关系图、枚举字典、代码仓库管理
│
├── iterations/         ← 每次迭代一个目录
│   ├── 2026-Q1_AMS-V2.0.0_视频下架/         D4 完成
│   ├── 2026-Q1_AMS+CRM_作品管理与交接单改造/ D3 完成
│   └── 2026-Q2_结算系统_逾期结算处理优化/     D1 完成
│
├── tools/              ← 云效同步工具
├── templates/          ← 迭代/系统模板
└── scripts/            ← 工具脚本（批量更新仓库等）
```
