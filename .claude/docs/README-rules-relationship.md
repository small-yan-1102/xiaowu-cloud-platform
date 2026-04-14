---
trigger: always_on
---
# 测试规则文件关系与使用流程

> **版本**: v3.8  
> **创建日期**: 2026-03-11  
> **更新日期**: 2026-03-31  
> **适用范围**: 测试规则体系（AI 直接执行模式 + 技术优化项目测试）+ Skill 体系

---

## 0. 版本演进说明

| 版本 | 执行模式 | 说明 |
|------|---------|------|
| v1.0 | AI 生成 Playwright + Pytest 脚本，由 CI 执行 | 已废弃 |
| v2.0 | 双模式并存（AI 直接执行 + 脚本自动化备用） | 过渡版本 |
| v3.0 | AI 读取 Markdown 用例 → 直接操作浏览器 → 自主判断结果 | 仅保留 3 个规则文件 |
| v3.1 | 同 v3.0，补充执行策略与报告规范 | 5 个规则文件 |
| **v3.2** | 同 v3.1，新增技术优化项目测试规则 + 数据准备规范升级 | 7 个规则文件 + 2 个模板 |
| **v3.3** | 同 v3.2，新增检索结果数量完整性验证规则 | 7 个规则文件 + 2 个模板 |
| **v3.4** | 新增 tech_doc_review.md、部署预检（§4.5）、U-8 互引、Skill/Agent 体系整合、D1-D5 工作流映射 | 8 个规则文件 + 2 个模板 + 7 个 Skill + 2 个 Agent |
| **v3.5** | 移除 Agent 体系（功能已被 Skill 覆盖） | 8 个规则文件 + 2 个模板 + 7 个 Skill |
| **v3.6** | 新增线上回归测试体系：G.3.5 线上回归适配规则、§8 生产环境约束、§9 D5 线上回归流程、§6 线上回归报告、Mode C 线上回归用例设计；D5 扩展为"发版 + 线上回归" | 8 个规则文件 + 2 个模板 + 7 个 Skill |
| **v3.7** | 新增数据就绪验证体系：E.3.5 验证特征规范、§6.3 数据就绪验证规则（自愈+失败处理）、test-data-preparation §八 验证输出 | 8 个规则文件 + 2 个模板 + 7 个 Skill |
| **v3.8（当前）** | 新增 AI 测试能力边界定义：§4.2 断言类型分类（视觉/API/DB）、§4.6 确定性断言编写规范、B.2 人工介入三级分级（Tier-1 可 Mock / Tier-2 必须人工 / Tier-3 专用工具）、E.7 静态数据池规范、§3.4 自愈边界规则（环境层 vs 业务层）、§5.6 确定性断言执行规则 | 8 个规则文件 + 2 个模板 + 7 个 Skill |

### 当前状态

#### AI 直接执行模式（功能测试/冒烟测试/线上回归）

| 文件 | 当前版本 | 职责 | 状态 |
|------|---------|------|------|
| `rules.md` | v2.0 | 基础规则（语言、环境、角色、执行模式定义） | 活跃 |
| `ai_test_case_design.md` | v3.6（AI直接执行版） | 测试用例设计规范（含附录 A-G，**§4.6 确定性断言规范**，**B.2 人工介入三级分级**，**E.7 静态数据池**） | 活跃 |
| `smoke_test_design.md` | v2.0（AI直接执行版） | 冒烟测试设计规范 | 活跃 |
| `ai_execution_strategy.md` | v2.2 | AI执行策略（浏览器操作、等待、重试、**§3.4 自愈边界规则**、**§5.6 确定性断言执行**、数据就绪验证、生产环境约束、线上回归流程） | 活跃 |
| `ai_execution_report.md` | v1.2 | AI执行报告（结果记录、截图规范、汇总报告、执行顺序、**线上回归报告**） | 活跃 |
| `tech_doc_review.md` | v2.3 | 技术文档审阅检查标准（供 tech-doc-review Skill 引用） | 活跃 |

#### 技术优化项目测试（无PRD的技术重构/优化）

| 文件 | 当前版本 | 职责 | 状态 |
|------|---------|------|------|
| `tech-optimization-ai-testing-rules.md` | v1.0 | 准入规则（素材链、开发交付物、职责分工、准入检查） | 活跃 |
| `tech-optimization-ai-testing-guide.md` | v1.0 | 使用说明（6 步操作指南、文件构成与角色关系） | 活跃 |
| `templates/tech-optimization-ai-test-skill-template.md` | v1.0 | AI Skill 模板（6 种工作模式） | 活跃 |
| `templates/tech-optimization-test-cases-template.md` | v1.0 | 测试用例模板（6 阶段结构） | 活跃 |

> v3.0 移除了全部脚本自动化相关的规则文件。v3.1 新增执行策略和报告规范。v3.2 新增技术优化项目测试规则体系 + 数据准备规范升级（E.3/E.4）。v3.3 新增检索结果数量完整性验证规则（§4.5.2）+ 搜索/筛选类用例数据准备数量要求（E.3）。v3.4 新增 tech_doc_review.md（审阅检查标准）、ai_execution_strategy.md 升级至 v1.2（新增 §4.5 部署预检 + §5.1 U-8 互引）、ai_execution_report.md 升级至 v1.1、整合 Skill/Agent 体系、建立 D1-D5 工作流映射。v3.5 移除 Agent 体系（test-case-consistency-maintainer、test-failure-analyzer），功能已被 Skill 体系覆盖。v3.6 新增线上回归测试体系：ai_test_case_design.md 升级至 v3.4（G.3.5 线上回归适配规则 + ENV 标签 + PROD 编号）、ai_execution_strategy.md 升级至 v2.0（§4.5 参数化 + §8 生产环境约束 + §9 D5 线上回归流程）、ai_execution_report.md 升级至 v1.2（§6 线上回归报告）、test-case-design Skill 升级至 v3.0（Mode C 线上回归用例设计）、D5 扩展为"发版 + 线上回归"。v3.7 新增数据就绪验证体系：ai_test_case_design.md 升级至 v3.5（E.3.5 验证特征编写规范 + §8.2 审查清单新增检查项 + E.6 自检公式扩展）、ai_execution_strategy.md 升级至 v2.1（§6.1 新增步骤 3 "数据就绪验证" + §6.3 验证执行规则/自愈策略/失败处理）、test-data-preparation Skill 升级至 v1.1（§3.1 新增验证特征列 + §八 数据就绪验证输出）。v3.8 新增 AI 测试能力边界定义：ai_test_case_design.md 升级至 v3.6（§4.2 断言类型分类 + §4.6 确定性断言编写规范 + B.2 人工介入三级分级 + E.7 静态数据池规范 + §8.2 审查清单扩展）、ai_execution_strategy.md 升级至 v2.2（§3.4 自愈边界规则 + §5.6 确定性断言执行规则）、test-case-design Skill 升级至 v3.2（Phase 4 新增断言/人工介入/数据池检查项）。

---

## 1. 文件清单及定位

| 文件 | 定位层级 | 核心职责 | trigger类型 |
|------|---------|---------|-------------|
| `rules.md` | **基础层** | 对话语言、系统环境、角色定义、执行模式 | `always_on` |
| `ai_test_case_design.md` | **设计层** | 测试用例设计原则、场景覆盖、验证判断规范、**线上回归适配规则** | `model_decision` |
| `smoke_test_design.md` | **设计层-专项** | 冒烟测试选取标准、设计原则、验证层级 | `model_decision` |
| `ai_execution_strategy.md` | **执行层** | 浏览器操作规范、等待策略、错误恢复与重试、环境准备、部署预检、AI判断校准、**生产环境约束**、**线上回归流程** | `model_decision` |
| `ai_execution_report.md` | **报告层** | 执行结果记录格式、截图规范、汇总报告模板、执行顺序策略、**线上回归报告** | `model_decision` |
| `tech_doc_review.md` | **审阅层** | 技术文档审阅检查标准（需求一致性、风险场景、AI可测试性） | `model_decision` |
| `tech-optimization-ai-testing-rules.md` | **专项-技术优化** | 技术优化项目准入规则、素材链、开发交付物、职责分工 | 手动引用 |
| `tech-optimization-ai-testing-guide.md` | **专项-技术优化** | 技术优化AI测试使用说明、操作指南 | 手动引用 |

---

## 2. 文件关系图

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     单周迭代工作流（D1-D5）                                    │
│                                                                              │
│  D1 ┌─────────────────┐                                                     │
│     │ test-prd-review  │ Skill: PRD 审阅                                     │
│     │  (PRD三方对齐)    │                                                     │
│     └────────┬─────────┘                                                     │
│              │ PRD 审阅报告                                                   │
│              ▼                                                                │
│  D2 ┌─────────────────┐    ┌──────────────────┐                              │
│     │ tech-doc-review  │───▶│ tech_doc_review  │                              │
│     │ Skill: 技术文档审阅│    │ v2.3 检查标准     │                              │
│     └────────┬─────────┘    └──────────────────┘                              │
│              │ 审阅报告 + 补充场景建议                                          │
│              ▼                                                                │
│  D3 ┌─────────────────────┐    ┌─────────────────────┐                       │
│     │  test-case-design   │    │  smoke_test_design   │                       │
│     │ Skill: 测试用例设计   │    │  v2.0 冒烟测试专项    │                       │
│     │ Mode A: PRD/流程图   │    └─────────────────────┘                       │
│     │ Mode B: 审阅报告补充  │                                                  │
│     │ Mode C: 线上回归设计  │    ┌──────────────────────────┐                  │
│     └────────┬────────────┘    │ ai_test_case_design v3.6 │                  │
│              │                  │ (用例设计规范+附录A-G)     │                  │
│              │                  │ (含G.3.5线上回归适配规则)  │                  │
│              │                  └──────────────────────────┘                  │
│              │ Markdown 测试用例 + 冒烟用例 + 线上回归用例套件                    │
│              ▼                                                                │
│  D4 ┌──────────────────────┐    ┌──────────────────────┐                     │
│     │ai_execution_strategy │    │ ai_execution_report  │                     │
│     │  v2.2 执行策略        │    │  v1.2 报告规范        │                     │
│     │ (部署预检→冒烟→E2E)   │    │ (记录/截图/汇总/顺序) │                     │
│     └──────────┬───────────┘    └──────────┬───────────┘                     │
│                │                            │                                 │
│                ▼                            ▼                                 │
│     ┌─────────────────────────────────────────────────┐                      │
│     │  部署预检 → 冒烟测试 → E2E → 异常 → 边界 → 报告   │                      │
│     │         (browser-use MCP / 浏览器自动化)          │                      │
│     └─────────────────────────────────────────────────┘                      │
│              │                                                                │
│              ▼                                                                │
│  D5 ┌──────────────────────────────────────────────────────┐                 │
│     │  发版 + 线上回归                                       │                 │
│     │                                                        │                 │
│     │  前提: D4 全部通过 + 代码已部署生产                       │                 │
│     │                                                        │                 │
│     │  ai_execution_strategy v2.2                            │                 │
│     │  §8 生产环境约束 + §9 线上回归流程                        │                 │
│     │                                                        │                 │
│     │  生产预检 → 线上冒烟 → 功能回归 → 新功能验证              │                 │
│     │                                                        │                 │
│     │  ai_execution_report v1.2                              │                 │
│     │  §6 线上回归报告                                        │                 │
│     └──────────────────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│              技术优化项目测试（独立流程，不混用）                                 │
│                                                                              │
│  ┌──────────────────────────────┐    ┌─────────────────────────────┐         │
│  │ tech-optimization-rules     │    │ tech-optimization-guide     │         │
│  │ v1.0 准入规则                │    │ v1.0 使用说明               │         │
│  │ (素材链/交付物/职责/准入)     │    │ (6步操作指南/文件构成)       │         │
│  └──────────┬──────────────────┘    └─────────────────────────────┘         │
│             │                                                                │
│             ▼                                                                │
│  ┌──────────────────────────────────────────────────┐                        │
│  │ templates/                                       │                        │
│  │ ├── skill-template (6种AI工作模式)                │                        │
│  │ └── test-cases-template (6阶段用例结构)           │                        │
│  └──────────────────────────────────────────────────┘                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 各文件详细说明

### 3.1 rules.md（基础层）

**定位**: 基础对话、环境约定和执行模式定义

**核心内容**:
- 对话语言（中文/英文）
- 系统环境（Windows 11）
- 代码注释要求
- 角色定义（资深测试专家）
- 测试执行模式（AI 直接执行）
- 规则体系清单
- 工作流映射（D1-D5 与 Skill/Rule 对应关系）
- Skill 间衔接关系

**trigger**: `always_on`（始终生效）

---

### 3.2 ai_test_case_design.md（设计层-通用）

**版本**: v3.6（AI直接执行版）

**定位**: 测试用例设计的通用原则和 AI 执行规范

**核心内容**:
- 测试用例设计原则（完整性、独立性、可维护性、可读性）
- 用例结构规范（命名、Markdown模板、跨系统模板）
- 测试场景覆盖要求（正常/异常/边界/权限/安全/兼容性）
- 验证判断规范（L1/L2/L3验证层级、**§4.2 断言类型分类**、操作-验证配对原则、反向验证要求）
- **§4.6 确定性断言编写规范**（API 断言 / DB-Query 断言 / 混合断言）
- 测试数据管理
- 测试分层策略（L1-L5）
- AI 执行测试注意事项（执行步骤、判断原则）
- 附录 A-G（字段规范、**B.2 人工介入三级分级（Tier-1/Tier-2/Tier-3）**、验证强度分级、预期结果反模式、前置条件与数据准备、测试步骤编写、跨系统测试与用例组织）
- **E.3.5 验证特征编写规范**（验证标签格式、三种验证方式、编写原则）
- **E.7 静态数据池规范**（定义、适用场景、数据池文档结构、引用方式、管理规则）
- **G.3.5 线上回归用例适配规则**（ENV 标签体系、安全适配决策树、PROD 用例模板、PROD 编号规范）

**trigger**: `model_decision`

**glob 匹配规则**: `**/md_case/*.md`、`**/test_case*.md`、`**/*测试用例*.md`、`**/*test_plan*.md`

**引用关系**: 被 `smoke_test_design.md` 引用（冒烟测试是 L5 层的专项细化）；G.3.5 被 `test-case-design` Skill Mode C 引用

---

### 3.3 smoke_test_design.md（设计层-专项）

**版本**: v2.0（AI直接执行版）

**定位**: 冒烟测试的专项设计规则

**核心内容**:
- 冒烟测试定义与定位（L5层，快速健康检查）
- 核心约束（单条 <2分钟，套件 <5分钟，每模块3-5条）
- 冒烟用例选取标准（Include/Exclude/决策树）
- 编号规范（SMOKE-{MODULE}-{SEQ}）
- 设计原则（Happy Path Only、状态变更优于UI细节、步骤可合并、容错处理）
- 验证层级（L1 60-70%、L2 20-30%、L3 ≤10%）
- 失败阻塞策略
- 维护规则（新增模块同步、定期审查）

**trigger**: `model_decision`

**glob 匹配规则**: `**/md_case/*smoke*`、`**/*冒烟*.md`、`**/*smoke*.md`

**引用关系**: 引用 `ai_test_case_design.md`（是 L5 层的专项细化）

---

### 3.4 ai_execution_strategy.md（执行层）

**版本**: v2.2

**定位**: AI 执行测试时的操作行为规范，补充 `ai_test_case_design.md` 第 7 节

**核心内容**:
- 浏览器操作规范（元素定位优先级、操作类型规范、键盘操作）
- 等待策略（状态信号等待、超时设置、SPA 路由切换）
- 错误恢复与重试策略（重试决策矩阵、幂等性检查、熔断机制、意外弹窗处理）
- **§3.4 自愈边界规则**（环境层 vs 业务层判定、自愈决策树、自愈禁区）
- 测试环境准备（环境配置、浏览器初始状态、登录态管理、测试数据准备）
- **部署预检（§4.5）**：冒烟/线上回归前置 3 项检查（环境可访问、登录正常、核心页面可加载），支持测试/生产环境参数化
- AI 判断校准（文本匹配规则、元素可见性判断、数值比较容差、异步操作判断、Flaky 处理）
- **U-8 互引（§5.1）**：关联 `tech_doc_review.md` U-8 文案差异标注，AI 执行时以技术文档标注的实际渲染值为准
- **§5.6 确定性断言执行规则**（断言类型识别、API 断言执行流程、DB 断言执行流程、混合断言执行顺序、失败报告格式）
- 执行流程总览（单条用例流程、异常中断处理）
- **§6.3 数据就绪验证规则**（验证执行规则、自愈策略、失败处理，消费 `ai_test_case_design.md` E.3.5 的 `[验证:]` 标签）
- 截图检查点执行规范（双证据体系、三级检查点模型）
- 附录 A（常见操作的等待模式速查）
- **§8 生产环境执行约束**（五项原则：只读优先/幂等安全/数据隔离/时间窗口/操作审计 + 操作决策矩阵 + 生产熔断机制）
- **§9 D5 线上回归执行流程**（5 阶段：生产预检→线上冒烟→已有功能回归→新功能验证→报告）

**trigger**: `model_decision`

**glob 匹配规则**: `**/md_case/*.md`、`**/test_case*.md`、`**/*测试用例*.md`、`**/*smoke*.md`、`**/*冒烟*.md`

**引用关系**: 引用 `ai_test_case_design.md` 第 7 节、G.3.5 和 E.3.5、`smoke_test_design.md` 第 4.4 节、`tech_doc_review.md` U-8、`test-data-preparation` Skill §八；§9 引用 `ai_execution_report.md` §6

---

### 3.5 ai_execution_report.md（报告层）

**版本**: v1.2

**定位**: AI 执行测试后的结果记录与报告规范

**核心内容**:
- 单条用例执行结果格式（结果记录模板、状态定义、警告记录）
- 截图规范（必须截图场景、命名规范、存储目录）
- 测试套件执行顺序（套件级策略 P0→P1→P2→P3、模块内顺序、依赖链处理）
- 汇总报告模板（执行概览、冒烟结果、E2E结果、失败详情、警告汇总、环境问题）
- 结果同步（Excel 同步、缺陷关联）
- **§6 线上回归报告模板**（生产预检→线上冒烟→回归结果（含选取理由）→新功能验证→操作审计日志→回归结论 + 文件命名 `prod_regression_report_YYYYMMDD.md`）

**trigger**: `model_decision`

**glob 匹配规则**: `**/md_case/*.md`、`**/test_case*.md`、`**/*测试用例*.md`、`**/*测试报告*.md`、`**/*test_report*.md`、`**/*执行结果*.md`

**引用关系**: 引用 `ai_execution_strategy.md`、`ai_test_case_design.md`、`smoke_test_design.md`；§6 被 `ai_execution_strategy.md` §9 引用

---

### 3.6 tech_doc_review.md（审阅层）

**版本**: v2.3（精简版 - 检查标准）

**定位**: 技术文档审阅检查标准，供 tech-doc-review Skill 引用

**核心内容**:
- 需求一致性检查（PRD/原型与技术方案的对齐验证）
- 风险场景识别（并发、数据迁移、兼容性等）
- AI 可测试性检查（U-1 ~ U-8 检查项）
- U-8 文案差异标注（前端实际渲染值与 PRD/原型差异时要求开发标注）
- 审阅完成度机制（按完成度百分比判断审阅通过与否）

**trigger**: `model_decision`

**引用关系**: 被 `ai_execution_strategy.md` §5.1 引用（U-8 互引）；产出出口 → `test-case-design` Skill Mode B

---

### 3.7 tech-optimization-ai-testing-rules.md（专项-技术优化）

**版本**: v1.0

**定位**: 技术优化/重构项目的测试准入规则（独立于 AI 直接执行体系，平行使用）

**核心内容**:
- 素材链总览（开发交付 4 项 → 测试产出 2 项）
- 开发交付物清单（技术设计文档、变更确认表、测试补充文档、源代码/PR）
- 测试职责分工（开发：单元/集成测试；测试：流程/迁移/回归测试）
- 准入检查清单（必须项 + 建议项）
- AI 测试 Skill 规范（6 种工作模式）
- 测试用例组织规范（6 阶段结构）
- 适用边界

**trigger**: 手动引用（适用于无 PRD 的技术优化项目，不自动触发）

**引用关系**: 引用 `templates/tech-optimization-ai-test-skill-template.md`、`templates/tech-optimization-test-cases-template.md`

---

### 3.8 tech-optimization-ai-testing-guide.md（专项-技术优化）

**版本**: v1.0

**定位**: 技术优化 AI 测试的操作指南

**核心内容**:
- 规则解决的问题（不知道测什么、不知道怎么借助 AI、没有统一标准）
- 文件构成与角色关系
- 6 步使用方法（准入检查 → 补充文档 → 复检 → 编写用例 → 实例化 Skill → AI 直接执行）

**trigger**: 手动引用

---

## 4. 使用流程

### 单周迭代流程（D1-D5）

```
D1 PRD 三方对齐
    └── Skill: test-prd-review
            ├── 输出 PRD 审阅报告
            └── 识别功能点和边界条件

D2 技术文档审阅
    └── Skill: tech-doc-review
            ├── 参考 tech_doc_review.md v2.3（检查标准）
            ├── 以 D1 PRD 审阅报告为参照基准
            ├── 执行需求一致性 + 风险场景 + AI 可测试性检查
            └── 输出审阅报告（含补充场景建议 §二.2.3）

D3 测试用例设计
    └── Skill: test-case-design
            ├── Mode A: 基于 PRD/流程图设计
            │       └── 参考 ai_test_case_design.md v3.6
            ├── Mode B: 基于 D2 审阅报告补充
            │       └── 审阅报告 §二.2.3 作为输入
            ├── Mode C: 线上回归用例设计
            │       ├── 参考 ai_test_case_design.md G.3.4（回归选取）+ G.3.5（线上适配）
            │       ├── 参考 ai_execution_strategy.md §8（生产环境约束）
            │       └── 输出 suite_prod_regression.md
            └── 冒烟用例
                    └── 参考 smoke_test_design.md v2.0

D4 冒烟 + 测试执行（测试环境）
    └── 参考 ai_execution_strategy.md v2.2
            ├── §4.5 部署预检（环境可访问、登录正常、页面可加载）
            ├── 冒烟测试（失败则打回开发）
            ├── E2E → 异常 → 边界
            ├── §5.1 文本匹配以技术文档标注值为准（U-8 互引）
            └── 参考 ai_execution_report.md v1.2（结果记录 + 汇总报告）

D5 发版 + 线上回归
    前提: D4 全部通过 + 代码已部署生产
    └── Skill: test-case-design Mode C（如 D3 未执行）
    └── 参考 ai_execution_strategy.md v2.2
            ├── §8 生产环境执行约束（只读优先/幂等安全/数据隔离/时间窗口/操作审计）
            └── §9 D5 线上回归执行流程
                    ├── 阶段 1: 生产环境预检（复用 §4.5）
                    ├── 阶段 2: 线上冒烟（[ENV: PROD] P0 用例）
                    ├── 阶段 3: 已有功能回归（[ENV: PROD] 回归用例）
                    ├── 阶段 4: 新功能线上验证（PROD-{MODULE}-{SEQ} 用例）
                    └── 阶段 5: 生成线上回归报告
                            └── 参考 ai_execution_report.md v1.2 §6
```

### 按任务查规则

| 任务 | 参考规则/Skill |
|------|--------------|
| PRD 审阅 | Skill: `test-prd-review` |
| 技术文档审阅 | Skill: `tech-doc-review` + Rule: `tech_doc_review.md` v2.3 |
| 设计测试用例 | Skill: `test-case-design` Mode A/B + Rule: `ai_test_case_design.md` v3.6 |
| 设计冒烟用例 | Rule: `smoke_test_design.md` v2.0 |
| 设计线上回归用例 | Skill: `test-case-design` Mode C + Rule: `ai_test_case_design.md` v3.6 G.3.4/G.3.5 |
| 部署预检 | Rule: `ai_execution_strategy.md` v2.2 §4.5 |
| 执行测试（操作/等待/重试） | Rule: `ai_execution_strategy.md` v2.2 |
| 记录结果/生成报告 | Rule: `ai_execution_report.md` v1.2 |
| 线上回归执行 | Rule: `ai_execution_strategy.md` v2.2 §8/§9 |
| 线上回归报告 | Rule: `ai_execution_report.md` v1.2 §6 |
| 结果同步到 Excel | Skill: `test-result-sync` |
| 技术优化项目准入检查 | Rule: `tech-optimization-ai-testing-rules.md` v1.0 |
| 技术优化项目测试操作 | Rule: `tech-optimization-ai-testing-guide.md` v1.0 |

---

## 5. 引用关系矩阵

| 文件 | 被谁引用 | 引用谁 |
|------|---------|--------|
| `rules.md` | - | - |
| `ai_test_case_design.md` v3.6 | `smoke_test_design.md`、`ai_execution_strategy.md`（§9 引用 G.3.5、§6.3 引用 E.3.5）、`ai_execution_report.md`、`test-case-design` Skill Mode C | - |
| `smoke_test_design.md` v2.0 | `ai_execution_strategy.md`、`ai_execution_report.md` | `ai_test_case_design.md` |
| `ai_execution_strategy.md` v2.2 | `ai_execution_report.md` | `ai_test_case_design.md`（第 7 节 + G.3.5 + E.3.5）、`smoke_test_design.md`、`tech_doc_review.md`（U-8）、`ai_execution_report.md`（§6）、`test-data-preparation` Skill（§八） |
| `ai_execution_report.md` v1.2 | `ai_execution_strategy.md`（§9 引用 §6） | `ai_execution_strategy.md`、`ai_test_case_design.md`、`smoke_test_design.md` |
| `tech_doc_review.md` v2.3 | `ai_execution_strategy.md`（§5.1 U-8 互引） | 产出出口 → `test-case-design` Mode B |
| `tech-optimization-ai-testing-rules.md` v1.0 | `tech-optimization-ai-testing-guide.md` | `templates/*`（Skill 模板、用例模板） |
| `tech-optimization-ai-testing-guide.md` v1.0 | - | `tech-optimization-ai-testing-rules.md` |

---

## 6. Skill 体系

### 核心 Skill（单周迭代流程）

| Skill | 迭代阶段 | 职责 | 引用的规则 |
|-------|---------|------|-----------|
| `test-prd-review` | D1 | PRD 审阅，输出需求理解总结和审阅报告 | - |
| `tech-doc-review` | D2 | 技术文档审阅，执行需求一致性/风险场景/AI可测试性检查 | `tech_doc_review.md` v2.3 |
| `test-case-design` | D3/D5 | 测试用例设计（Mode A 基于PRD, Mode B 基于审阅报告补充, **Mode C 线上回归用例设计**） | `ai_test_case_design.md` v3.6、`smoke_test_design.md` v2.0、`ai_execution_strategy.md` v2.2 §8 |

### Skill 间衔接关系

| 上游 Skill | 输出产物 | 下游 Skill | 输入方式 |
|-----------|---------|-----------|---------|
| test-prd-review | PRD 审阅报告 | tech-doc-review | 作为需求一致性审阅的参照基准 |
| tech-doc-review | 技术文档审阅报告（含补充场景建议） | test-case-design（Mode B） | 审阅报告 §二.2.3 作为 Mode B 输入 |
| test-case-design（Mode A/B） | Markdown 测试用例 | AI 执行测试（D4） | ai_execution_strategy.md + ai_execution_report.md |
| test-case-design（Mode C） | 线上回归用例套件（suite_prod_regression.md） | AI 线上回归执行（D5） | ai_execution_strategy.md §8/§9 + ai_execution_report.md §6 |

### 辅助 Skill

| Skill | 职责 | 使用场景 |
|-------|------|---------|
| `test-case-prd-consistency` | 排查测试用例与 PRD 不一致的问题 | 用例步骤/预期结果与 PRD 不符时 |
| `test-data-preparation` | 基于技术系分文档通过 API 准备测试数据 | 用例标注 `[数据准备: API]` 或 UI 步骤 >5 步时 |
| `test-result-sync` | 测试结果同步到 Excel/Markdown，生成覆盖率统计 | D4 测试执行完成后 |
| `yunxiao-sync` | Markdown 测试用例同步到阿里云效 Testhub | 用例需要同步到云效时 |

---

## 7. trigger 类型说明

| trigger类型 | 含义 | 文件 |
|------------|------|------|
| `always_on` | 始终生效 | `rules.md`、`README-rules-relationship.md` |
| `model_decision` | 由 AI 判断何时使用（基于文件 glob 匹配） | `ai_test_case_design.md`、`smoke_test_design.md`、`ai_execution_strategy.md`、`ai_execution_report.md`、`tech_doc_review.md` |

### glob 匹配规则

| 文件 | glob 匹配规则 |
|------|-------------|
| `ai_test_case_design.md` | `**/md_case/*.md`、`**/test_case*.md`、`**/*测试用例*.md`、`**/*test_plan*.md` |
| `smoke_test_design.md` | `**/md_case/*smoke*`、`**/*冒烟*.md`、`**/*smoke*.md` |
| `ai_execution_strategy.md` | `**/md_case/*.md`、`**/test_case*.md`、`**/*测试用例*.md`、`**/*smoke*.md`、`**/*冒烟*.md` |
| `ai_execution_report.md` | `**/md_case/*.md`、`**/test_case*.md`、`**/*测试用例*.md`、`**/*测试报告*.md`、`**/*test_report*.md`、`**/*执行结果*.md` |

---

## 8. 分层架构总结

```
┌─────────────────────────────────────────┐
│  报告层                                  │
│  ai_execution_report.md v1.2            │
│  （结果记录、截图、汇总报告、执行顺序、    │
│    线上回归报告）                         │
├─────────────────────────────────────────┤
│  执行层                                  │
│  ai_execution_strategy.md v2.2          │
│  （操作/等待/重试/部署预检/U-8互引/校准    │
│    /生产环境约束/线上回归流程）            │
├─────────────────────────────────────────┤
│  审阅层                                  │
│  tech_doc_review.md v2.3                │
│  （需求一致性/风险场景/AI可测试性检查）     │
├─────────────────────────────────────────┤
│  设计层-专项                              │
│  smoke_test_design.md v2.0              │
│  （冒烟测试选取标准、验证层级）             │
├─────────────────────────────────────────┤
│  设计层-通用                              │
│  ai_test_case_design.md v3.6            │
│  （用例设计原则、验证判断、AI执行规范、     │
│    线上回归适配规则）                      │
├─────────────────────────────────────────┤
│  基础层                                  │
│  rules.md                               │
│  （环境、语言、角色约定、执行模式、工作流）   │
└─────────────────────────────────────────┘

D1 PRD审阅 → D2 技术文档审阅 → D3 用例设计 → D4 部署预检→冒烟→执行→报告 → D5 发版+线上回归

┌─────────────────────────────────────────┐
│  专项-技术优化（独立流程，不混用）          │
│  tech-optimization-rules v1.0           │
│  tech-optimization-guide v1.0           │
│  templates/ (Skill模板 + 用例模板)       │
│  （准入规则、素材链、6种AI工作模式）        │
└─────────────────────────────────────────┘
```

---

## 9. 文件路径总览

```
.claude/
├── rules/                                       # 自动加载（每次对话注入，~30KB）
│   ├── rules.md                         (基础层 - always_on)
│   └── test-environment-config.md       (环境配置 - always_on，已脱敏)
│
├── docs/                                        # 按需读取（Skill 执行时加载，~160KB）
│   ├── README-rules-relationship.md     (本文档 - 规则/Skill 关系说明)
│   ├── ai_test_case_design.md           (设计层 v3.6 - AI直接执行版)
│   ├── smoke_test_design.md             (设计层-专项 v2.0 - AI直接执行版)
│   ├── ai_execution_strategy.md         (执行层 v2.2 - 执行策略+部署预检+数据就绪验证+自愈边界规则+确定性断言执行+生产环境约束+线上回归流程)
│   ├── ai_execution_report.md           (报告层 v1.2 - 报告规范+线上回归报告)
│   ├── tech_doc_review.md               (审阅层 v2.3 - 技术文档审阅检查标准)
│   ├── tech-optimization-ai-testing-rules.md   (专项-技术优化 v1.0 - 准入规则)
│   ├── tech-optimization-ai-testing-guide.md   (专项-技术优化 v1.0 - 使用说明)
│   └── templates/
│       ├── tech-optimization-ai-test-skill-template.md   (AI Skill 模板)
│       └── tech-optimization-test-cases-template.md      (测试用例模板)
│
├── secrets/                                     # 敏感凭证（.gitignore 排除）
│   └── credentials.md                   (数据库/服务器/系统登录密码)
│
└── skills/
    ├── test-prd-review/SKILL.md         (D1 PRD 审阅)
    ├── tech-doc-review/SKILL.md         (D2 技术文档审阅)
    ├── test-case-design/SKILL.md        (D3/D5 测试用例设计 - Mode A/B/C)
    ├── test-case-prd-consistency/SKILL.md (用例-PRD 一致性排查)
    ├── test-data-preparation/SKILL.md   (API 测试数据准备)
    ├── test-result-sync/SKILL.md        (结果同步到 Excel)
    └── yunxiao-sync/SKILL.md            (同步到云效 Testhub)
```

---

> **文档维护**: 测试团队  
> **生效日期**: 2026-03-30
