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

### 自动加载（`.claude/rules/`，每次对话注入）

| 文件 | 职责 |
|------|------|
| `rules.md` | 基础规则（语言、环境、角色）+ D1-D5 工作流映射 |
| `test-environment-config.md` | 测试环境 URL、登录路径、data-testid 索引（已脱敏） |

### 按需读取（`.claude/docs/`，Skill 执行时加载）

| 文件 | 职责 | 关联 Skill |
|------|------|-----------|
| `ai_test_case_design.md` | 测试用例设计规范（附录 A-G、确定性断言、人工介入分级、静态数据池） | test-case-design |
| `smoke_test_design.md` | 冒烟测试设计规范 | test-case-design Mode D |
| `ai_execution_strategy.md` | AI执行策略（浏览器操作、等待、重试、部署预检、自愈边界、生产环境约束） | test-execution |
| `ai_execution_report.md` | AI执行报告（结果记录、截图规范、汇总报告、线上回归报告） | test-execution / test-report |
| `tech_doc_review.md` | 技术文档审阅检查标准 | tech-doc-review |
| `tech-optimization-ai-testing-rules.md` | 技术优化项目测试准入规则 | 手动引用 |
| `tech-optimization-ai-testing-guide.md` | 技术优化项目使用说明 | 手动引用 |

规则间关系详见 `.claude/docs/README-rules-relationship.md`（按需查阅）。

## 工作流（单周迭代）

```
D1 PRD三方对齐       → /test-prd-review
D2 技术文档审阅      → /tech-doc-review
D3 测试用例设计      → /test-case-design（Mode A/B/C/D）
D4 冒烟+测试执行     → 参考 .claude/docs/ai_execution_strategy.md + ai_execution_report.md
D5 发版+线上回归     → /test-case-design Mode C + .claude/docs/ai_execution_strategy.md §8/§9
```

## 可用技能命令（`.claude/commands/`）

使用 `/命令名` 调用，例如 `/test-prd-review`：

| 命令 | 说明 |
|------|------|
| `/test-prd-review` | 测试视角审阅 PRD，输出阻塞性问题/补充项/不一致项报告 |
| `/test-case-design` | 设计测试用例（Mode A PRD初次生成 / Mode B 补充 / Mode C 线上回归 / Mode D 冒烟） |
| `/tech-doc-review` | 审阅技术文档，执行需求一致性和AI可测试性检查 |
| `/test-case-prd-consistency` | 排查用例与 PRD 不一致，提供根因分析和修复方案 |
| `/test-result-sync` | 将AI测试结果同步到 Excel/Markdown 用例文档，生成统计报告 |
| `/yunxiao-sync` | 将 Markdown 测试用例同步到阿里云效 Testhub |
| `/system-function-analysis` | 系统功能梳理（功能清单逆向/颗粒度评估/需求分析/变更影响分析） |
| `/req-gen` | 基于 PRD 和原型生成前端用户故事文档 |
| `/user-story-update` | 根据三路审阅意见更新用户故事文档 |
| `/frontend-testcase-review` | 前端视角审阅测试用例（覆盖度/交互/UI状态/前端专属测试点） |
| `/backend-prd-review` | 后端视角审阅 PRD（接口设计/数据结构/边界处理） |
| `/frontend-prd-review` | 前端视角审阅 PRD（交互逻辑/组件复用/性能体验） |
| `/backend-solution-review` | 前端视角审阅后端方案（接口设计/消费友好性/性能影响） |
| `/code-review` | 结构化代码审查（正确性/安全性/性能/可读性/项目规范） |
| `/api-integration` | 前端接口联调（数据对接/异常处理/联调报告） |
| `/ui-mock-gen` | 无接口时通过原型图+PRD搭建前端界面（Mock数据） |
| `/add-data-testid` | 按测试用例在 DOM 元素上添加 data-testid 属性 |
| `/test-data-preparation` | 测试数据准备（生成/导入/清理测试环境数据） |
| `/test-point-extraction` | 从 PRD 审阅摘要提炼结构化测试点清单（覆盖正向/边界/异常/权限/状态机维度） |
| `/prd-gate` | PRD 质量门禁，判定 PRD 是否达到可开始用例设计的标准 |
| `/api-test-case-design` | 设计接口测试用例（Mode A 初次生成 / Mode B 变更回归），输出可供 api-test-execution 执行的套件 |
| `/test-case-review` | 用例质量审核（覆盖完整性/边界遗漏/断言可执行性/禁用词），输出审核报告 |
| `/submission-gate` | 提测门禁九项检查（审阅完成度/自测证明/覆盖率/CR/契约测试/环境/PRD门禁/套件存在性） |
| `/test-execution` | 通过 browser-use MCP 直接操作浏览器执行测试用例，含部署预检、截图双证据体系、生产环境熔断 |
| `/api-test-execution` | 直接执行 HTTP 接口测试用例，自主断言响应，生成执行报告 |
| `/bug-sync` | 从测试执行报告提取失败用例，生成结构化缺陷清单（Markdown / CSV 导入格式） |
| `/test-report` | 聚合执行报告和缺陷清单，生成含覆盖率/通过率/质量结论的完整测试报告 |
| `/release-gate` | 发布门禁，核验 P0 通过率和开放缺陷数，输出可发布 / 不可发布结论 |

## 项目目录结构

> 双维度结构：`systems/`（持久化知识沉淀）+ `iterations/`（迭代项目推进）

```
E:\Orange\小五云平台\
├── CLAUDE.md                                    ← 本文件（每个 session 自动加载）
├── README.md                                    ← 根目录快速指南
├── 目录结构说明.md                               ← 详细目录结构使用说明
├── .claude/
│   ├── commands/                                ← /斜杠命令入口（43 个）
│   ├── rules/                                   ← 自动加载规则（rules.md + 环境配置，~30KB）
│   ├── docs/                                    ← 按需读取规则（用例设计/执行策略/报告等，~160KB）
│   │   └── templates/                           ← 技术优化测试模板
│   ├── skills/                                  ← 技能支撑文件（43 个 skill 目录）
│   ├── secrets/                                 ← 敏感凭证（已加入 .gitignore）
│   └── settings.local.json                      ← 权限配置
│
├── systems/                                     ← 维度一：系统知识库（持久化，跨迭代沉淀）
│   ├── _shared/                                 ← 跨系统共享（系统关系图/枚举值字典/代码仓库管理）
│   ├── AMS/                                     ← 资产管理系统
│   │   ├── knowledge/                           ← 功能清单、changelog、data-testid（2模块）
│   │   └── code/                                ← silverdawn-ams-web + silverdawn-ams-server
│   ├── 结算系统/                                 ← 财务结算系统
│   │   ├── knowledge/                           ← 功能清单、YT核算逻辑、data-testid（11模块）
│   │   └── code/                                ← silverdawn-finance-web + silverdawn-finance-server
│   ├── 剧老板/                                   ← 分销商端
│   │   ├── knowledge/                           ← 功能清单、权限逻辑、data-testid（3模块）
│   │   └── code/                                ← distribution-server-web + distribution-server
│   ├── CRM/                                     ← 客户关系管理
│   │   ├── knowledge/                           ← 功能清单、交接单管理
│   │   └── code/                                ← silverdawn-recruitment-web + silverdawn-crm-server
│   ├── 总控系统/                                 ← 额度/配额管理
│   │   └── knowledge/                           ← 功能清单、额度规则
│   └── 云平台/                                   ← SSO 统一登录 + 应用中心
│       └── knowledge/                           ← 功能清单、data-testid（登录+应用中心）
│
├── linscode/                                    ← Harness 工程化工具链（独立 Git 仓库）
├── tools/                                       ← 云效 Testhub 同步工具
├── docs/                                        ← 参考文档（指向 linscode/）
│
├── iterations/                                  ← 维度二：迭代管理（按时间推进，每次迭代一个目录）
│   ├── 2026-Q1_AMS-V2.0.0_视频下架/             ← D4 完成（含执行报告+截图）
│   │   ├── input/prd/README.md                  ← 基线: 视频下架PRD-2026040202.md
│   │   ├── review/  testcase/  report/
│   ├── 2026-Q1_AMS+CRM_作品管理与交接单改造/     ← D3 完成（10 个用例套件）
│   │   ├── input/prd/README.md                  ← 基线: 作品管理与交接单改造-PRD.md
│   │   ├── review/  testcase/  report/
│   └── 2026-Q2_结算系统_逾期结算处理优化/         ← D1 完成（PRD审阅+测试点提取）
│       ├── input/prd/README.md                  ← 基线: PRD-V4.5-2026041001.md
│       ├── review/  testcase/  report/
│
├── templates/                                   ← 迭代/系统模板（iteration_readme、changelog 等）
└── scripts/                                     ← 工具脚本（update-all-repos.ps1）
```
