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

## 规则体系（`.claude/rules/`）

| 规则文件 | 职责 |
|---------|------|
| `rules.md` | 基础规则（语言、环境、角色）+ 工作流映射 |
| `ai_test_case_design.md` | 测试用例设计规范（含附录 A-G、§4.6 确定性断言、B.2 人工介入分级、E.7 静态数据池） |
| `smoke_test_design.md` | 冒烟测试设计规范 |
| `ai_execution_strategy.md` | AI执行策略（浏览器操作、等待、重试、环境准备、部署预检、§3.4 自愈边界、生产环境约束） |
| `ai_execution_report.md` | AI执行报告（结果记录、截图规范、汇总报告、线上回归报告） |
| `tech_doc_review.md` | 技术文档审阅检查标准 |
| `tech-optimization-ai-testing-rules.md` | 技术优化项目测试准入规则 |
| `test-environment-config.md` | 测试环境基础设施（DB/服务器/登录账号/data-testid 索引），执行测试前必读 |

规则间关系详见 `.claude/docs/README-rules-relationship.md`（按需查阅，非每次对话必读）。

## 工作流（单周迭代）

```
D1 PRD三方对齐       → /test-prd-review
D2 技术文档审阅      → /tech-doc-review
D3 测试用例设计      → /test-case-design（Mode A/B/C/D）
D4 冒烟+测试执行     → 参考 ai_execution_strategy.md + ai_execution_report.md
D5 发版+线上回归     → /test-case-design Mode C + ai_execution_strategy.md §8/§9
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
│   ├── commands/                                ← /斜杠命令入口（40 个）
│   ├── rules/                                   ← 规则文件（设计规范/执行策略/报告格式）
│   │   └── templates/                           ← 技术优化测试模板
│   ├── skills/                                  ← 技能支撑文件（40 个 skill 目录）
│   └── settings.local.json                      ← 权限配置
│
├── systems/                                     ← 维度一：系统知识库（持久化，跨迭代沉淀）
│   ├── _shared/                                 ← 跨系统共享（系统关系图/枚举值字典/环境信息）
│   ├── AMS/
│   │   ├── knowledge/                           ← AMS 功能清单、changelog、data-testid 映射
│   │   └── code/                                ← 代码仓库（silverdawn-ams-web / server）
│   ├── 结算系统/
│   │   ├── knowledge/                           ← 结算功能清单、YT核算逻辑、data-testid（11模块）
│   │   └── code/                                ← 代码仓库（silverdawn-finance-web / server）
│   ├── 剧老板/
│   │   ├── knowledge/                           ← 剧老板功能清单、权限逻辑、data-testid
│   │   └── code/                                ← 代码仓库（distribution-web / server）
│   ├── CRM/
│   │   ├── knowledge/                           ← CRM 功能清单、交接单管理
│   │   └── code/                                ← 代码仓库（待补充仓库名）
│   ├── 总控系统/
│   │   ├── knowledge/                           ← 总控功能清单、额度规则
│   │   └── code/                                ← 代码仓库（待补充仓库名）
│   └── 云平台/
│       └── knowledge/                           ← SSO 登录、应用中心功能清单、data-testid
│
├── iterations/                                  ← 维度二：迭代管理（按时间推进，每次迭代一个目录）
│   ├── 2026-Q1_AMS-V2.0.0_视频下架/
│   │   ├── input/prd/  input/tech/              ← 需求输入（PRD + 技术文档）
│   │   ├── review/                              ← 审阅报告
│   │   ├── testcase/                            ← 测试用例套件（suite_*.md）
│   │   └── report/screenshots/                  ← 测试报告 + 执行截图
│   ├── 2026-Q1_AMS+CRM_作品管理与交接单改造/
│   │   ├── input/  review/  testcase/  report/
│   └── 2026-Q2_结算系统_逾期结算处理优化/
│       ├── input/prd/  input/tech/
│       ├── review/                              ← PRD审阅报告（D1已完成）
│       ├── testcase/                            ← 测试用例（D3 待设计）
│       └── report/
│
├── templates/                                   ← 迭代/系统模板（iteration_readme、changelog 等）
└── scripts/                                     ← 工具脚本（update-all-repos.ps1）
```
