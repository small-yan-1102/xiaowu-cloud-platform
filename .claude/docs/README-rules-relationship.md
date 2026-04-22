# 规则与文档体系 CHANGELOG + 文件详情索引

> **定位**：记录规则/文档体系的版本演进和每个 doc 文件的职责、引用关系。
> **当前权威来源**（不要在本文件重复，避免漂移）：
> - 📘 规则体系索引与文件清单：[CLAUDE.md](../../CLAUDE.md) §规则体系
> - 📘 工作流映射（D1-D5）与 Skill 衔接：[workflow-mapping.md](workflow-mapping.md)
> - 📘 本地 skills 目录身份索引：[../skills/README.md](../skills/README.md)
> - 📘 实际技能清单（动态扫描）：`python tools/find_unregistered.py`
>
> **本文件只负责**：(1) 版本演进 CHANGELOG —— 为什么每次调整；(2) 每个 docs/ 下 md 文件的职责与引用网 —— doc 间怎么互相引用。

---

## 1. CHANGELOG（版本演进）

| 版本 | 日期 | 执行模式 / 关键变更 | 规模 |
|---|---|---|---|
| v1.0 | — | AI 生成 Playwright + Pytest 脚本，由 CI 执行 | 已废弃 |
| v2.0 | — | 双模式并存（AI 直接执行 + 脚本自动化备用） | 过渡版本 |
| v3.0 | — | AI 读取 Markdown 用例 → 直接操作浏览器 → 自主判断结果 | 3 个规则文件 |
| v3.1 | — | 补充执行策略与报告规范 | 5 个规则文件 |
| v3.2 | — | 新增技术优化项目测试规则 + 数据准备规范升级（E.3/E.4） | 7 规则 + 2 模板 |
| v3.3 | — | 新增检索结果数量完整性验证规则（§4.5.2）+ 搜索/筛选类数据准备数量要求（E.3） | 7 规则 + 2 模板 |
| v3.4 | — | 新增 tech_doc_review.md、部署预检（§4.5）、U-8 互引、Skill/Agent 体系整合、D1-D5 工作流映射 | 8 规则 + 2 模板 + 7 Skill + 2 Agent |
| v3.5 | — | 移除 Agent 体系（功能已被 Skill 覆盖） | 8 规则 + 2 模板 + 7 Skill |
| v3.6 | — | 线上回归测试体系：G.3.5 适配规则、§8 生产环境约束、§9 D5 线上回归流程、§6 线上回归报告、Mode C 用例设计；D5 扩展为"发版+线上回归" | 8 规则 + 2 模板 + 7 Skill |
| v3.7 | — | 数据就绪验证体系：E.3.5 验证特征规范、§6.3 自愈+失败处理、test-data-preparation §八 | 8 规则 + 2 模板 + 7 Skill |
| v3.8 | — | AI 测试能力边界：§4.2 断言分类、§4.6 确定性断言、B.2 人工介入三级分级、E.7 静态数据池、§3.4 自愈边界、§5.6 确定性断言执行 | 8 规则 + 2 模板 + 7 Skill |
| v3.9 | 2026-04-10 | 规则文件分层：7 个规则从 `.claude/rules/` 迁移至 `.claude/docs/`（按需读取）；`rules/` 仅保留 `rules.md` + `test-environment-config.md`；敏感凭证分离至 `.claude/secrets/`；CLAUDE.md 精简 56% | 2 自动 + 7 按需 + 43 Skill |
| **v4.0** | **2026-04-21** | **结构重构周**：(a) 删重复技能 `frontend-prd-review` v1.0.0；(b) `rules.md` 剥离 D1-D5 工作流图和 Skill 衔接表至新建 [workflow-mapping.md](workflow-mapping.md)；(c) 命令加载协议统一（修复 `acceptance-case-design` 脱轨 + 原本指向错误路径的 bug）；(d) 新建 `.claude/skills/README.md` 建立 Override/Local/Shared 身份索引；(e) 命令文件 `check-overrides.md` description 硬编码"14 个"改为通配；(f) `test-case-design` 与 `frontend-testcase-gen` description 补充受众区分 | **1 自动 + 9 按需 + 46 Skill** |
| **v4.1** | **2026-04-22** | **本轮精简**：(a) 本文件从 545 行（综合文档）瘦身至 ~180 行（CHANGELOG + 引用网），删掉与 CLAUDE.md/workflow-mapping.md/skills/README.md 重复的章节；(b) 归档 `tech-optimization-*` 4 个闭环孤岛文件至 `_archive/tech-optimization/`；(c) 同步 CLAUDE.md 规则体系列表，删除归档项 | 1 自动 + 7 按需 + 46 Skill |

---

## 2. 文件详情索引

> 按 `.claude/docs/` 下文件逐一说明。CLAUDE.md §规则体系已列出文件清单，本节补充每个文件的**职责深度、引用关系、历史版本**。

### 2.1 `ai_test_case_design.md`

- **定位**：测试用例设计的通用原则和 AI 执行规范
- **当前版本**：v3.6（AI 直接执行版）
- **核心内容**：
  - 测试用例设计原则（完整性、独立性、可维护性、可读性）
  - 用例结构规范（命名、Markdown 模板、跨系统模板）
  - 测试场景覆盖要求（正常/异常/边界/权限/安全/兼容性）
  - 验证判断规范（L1/L2/L3 验证层级、**§4.2 断言类型分类**、操作-验证配对、反向验证）
  - **§4.6 确定性断言编写规范**（API 断言 / DB-Query 断言 / 混合断言）
  - 测试分层策略（L1-L5）
  - AI 执行注意事项（执行步骤、判断原则）
  - 附录 A-G：字段规范、**B.2 人工介入三级分级（Tier-1/2/3）**、验证强度分级、预期结果反模式、前置条件与数据准备、测试步骤编写、跨系统测试与用例组织
  - **E.3.5 验证特征编写规范**（验证标签格式、三种验证方式）
  - **E.7 静态数据池规范**
  - **G.3.5 线上回归用例适配规则**（ENV 标签 / PROD 编号）
- **引用关系**：被 `smoke_test_design.md` 引用；G.3.5 被 `test-case-design` Skill Mode C 引用

### 2.2 `smoke_test_design.md`

- **定位**：冒烟测试的专项设计规则
- **当前版本**：v2.0（AI 直接执行版）
- **核心内容**：
  - 冒烟定义（L5 层，快速健康检查）
  - 核心约束（单条 <2 min，套件 <5 min，每模块 3-5 条）
  - 用例选取标准（Include/Exclude/决策树）
  - 编号规范（`SMOKE-{MODULE}-{SEQ}`）
  - 设计原则（Happy Path Only、状态变更优先、步骤合并、容错）
  - 验证层级分布（L1 60-70% / L2 20-30% / L3 ≤10%）
  - 失败阻塞策略
- **引用关系**：引用 `ai_test_case_design.md`（是 L5 层的专项细化）

### 2.3 `ai_execution_strategy.md`

- **定位**：AI 执行测试时的操作行为规范，补充 `ai_test_case_design.md` §7
- **当前版本**：v2.2
- **核心内容**：
  - 浏览器操作规范（元素定位优先级、操作类型、键盘）
  - 等待策略（状态信号等待、超时、SPA 路由切换）
  - 错误恢复与重试（决策矩阵、幂等性、熔断、意外弹窗）
  - **§3.4 自愈边界规则**（环境层 vs 业务层、决策树、自愈禁区）
  - 测试环境准备（配置、登录态、数据准备）
  - **§4.5 部署预检**：冒烟/线上回归前置 3 项（可访问/登录正常/核心页面可加载）
  - AI 判断校准（文本匹配、元素可见性、数值容差、异步判断、Flaky 处理）
  - **§5.1 U-8 互引**：引 `tech_doc_review.md` U-8 文案差异
  - **§5.6 确定性断言执行规则**（API / DB / 混合）
  - **§6.3 数据就绪验证规则**（消费 E.3.5 的 `[验证:]` 标签）
  - 截图检查点（双证据体系、三级检查点）
  - **§8 生产环境执行约束**（只读优先/幂等/隔离/时间窗/审计 + 操作矩阵 + 生产熔断）
  - **§9 D5 线上回归执行流程**（5 阶段）
- **引用关系**：引 `ai_test_case_design.md` §7/G.3.5/E.3.5、`smoke_test_design.md` §4.4、`tech_doc_review.md` U-8、`test-data-preparation` Skill §八；§9 引 `ai_execution_report.md` §6

### 2.4 `ai_execution_report.md`

- **定位**：AI 执行测试后的结果记录与报告规范
- **当前版本**：v1.2
- **核心内容**：
  - 单条用例执行结果格式
  - 截图规范（必须截图场景、命名、存储目录）
  - 套件执行顺序（P0→P1→P2→P3、模块内顺序、依赖链）
  - 汇总报告模板（执行概览、冒烟/E2E 结果、失败详情、警告、环境问题）
  - 结果同步（Excel 同步、缺陷关联）
  - **§6 线上回归报告模板**（生产预检→线上冒烟→回归结果→新功能验证→审计日志→结论；`prod_regression_report_YYYYMMDD.md`）
- **引用关系**：引 `ai_execution_strategy.md` / `ai_test_case_design.md` / `smoke_test_design.md`；§6 被 `ai_execution_strategy.md` §9 引用

### 2.5 `tech_doc_review.md`

- **定位**：技术文档审阅检查标准，供 `tech-doc-review` Skill 引用
- **当前版本**：v2.3（精简版 - 检查标准）
- **核心内容**：
  - 需求一致性检查（PRD/原型 vs 技术方案）
  - 风险场景识别（并发、数据迁移、兼容性等）
  - AI 可测试性检查（U-1 ~ U-8）
  - U-8 文案差异标注
  - 审阅完成度机制
- **引用关系**：被 `ai_execution_strategy.md` §5.1 引用（U-8 互引）；出口 → `test-case-design` Skill Mode B

### 2.6 `test-environment-config.md`

- **定位**：测试环境 URL、登录路径、data-testid 索引（已脱敏）
- **加载方式**：`test-execution` 执行前按需读取
- **引用关系**：被各测试 Skill 执行前引用

### 2.7 `workflow-mapping.md` *(v4.0 新增)*

- **定位**：从 `rules.md` 剥离的工作流映射与 Skill 衔接表
- **核心内容**：D1-D5 流程图 + Skill 上下游关系表
- **加载方式**：跨阶段查阅时按需读取

---

## 3. 已归档的文件

v4.0 (2026-04-22) 将以下 4 个文件从 `.claude/docs/` 归档至 `_archive/tech-optimization/`：

- `tech-optimization-ai-testing-rules.md` — 技术优化项目测试准入规则
- `tech-optimization-ai-testing-guide.md` — 技术优化 AI 测试操作指南
- `templates/tech-optimization-ai-test-skill-template.md` — AI Skill 模板
- `templates/tech-optimization-test-cases-template.md` — 用例模板

**归档原因**：4 个文件形成闭环孤岛，无外部消费者；唯一含"优化"字样的迭代实际走 PRD 正常流程。

**恢复条件**：出现真正无 PRD 的技术重构项目时，移回原路径并更新 CLAUDE.md。详见 [`_archive/tech-optimization/README.md`](_archive/tech-optimization/README.md)。

---

*本文件仅覆盖 `.claude/docs/` 下文件的版本演进和引用网。若要查规则体系总入口、工作流图或 skills 身份，请看文件顶部的"当前权威来源"。*
