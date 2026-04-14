# 测试侧技能提示词模版

> 按迭代流程顺序排列。每个技能包含：用途说明、所需材料、可直接复制的触发语句。
> 说"按默认来"可跳过路径询问，AI 将使用默认文件路径。

---

## 目录

1. [test-prd-review — PRD 审阅](#1-test-prd-review--prd-审阅)
2. [prd-gate — PRD 质量门禁（内嵌）](#2-prd-gate--prd-质量门禁内嵌)
3. [tech-doc-review — 技术文档审阅](#3-tech-doc-review--技术文档审阅)
4. [test-point-extraction — 测试点提炼](#4-test-point-extraction--测试点提炼)
5. [test-case-design — 测试用例设计](#5-test-case-design--测试用例设计)
6. [api-test-case-design — 接口测试用例设计](#6-api-test-case-design--接口测试用例设计)
7. [test-case-review — 用例审核](#7-test-case-review--用例审核)
8. [test-case-prd-consistency — 用例与 PRD 一致性排查](#8-test-case-prd-consistency--用例与-prd-一致性排查)
9. [test-case-code-coverage — 用例代码覆盖分析](#9-test-case-code-coverage--用例代码覆盖分析)
10. [submission-gate — 提测门禁](#10-submission-gate--提测门禁)
11. [test-data-preparation — 测试数据准备](#11-test-data-preparation--测试数据准备)
12. [test-execution — UI 测试执行](#12-test-execution--ui-测试执行)
13. [api-test-execution — 接口测试执行](#13-api-test-execution--接口测试执行)
14. [test-result-sync — 测试结果回填](#14-test-result-sync--测试结果回填)
15. [bug-sync — 缺陷同步](#15-bug-sync--缺陷同步)
16. [test-report — 测试报告生成](#16-test-report--测试报告生成)
17. [release-gate — 发布门禁](#17-release-gate--发布门禁)
18. [defect-retest — 缺陷回归验证](#18-defect-retest--缺陷回归验证)
19. [multimodal-visual-assertion — 多模态视觉断言（补充执行能力）](#19-multimodal-visual-assertion--多模态视觉断言补充执行能力)
20. [visual-location-fallback — 视觉定位兜底（补充执行能力）](#20-visual-location-fallback--视觉定位兜底补充执行能力)

---

## 1. test-prd-review — PRD 审阅

**用途**：从测试视角审阅产品 PRD，识别需求缺陷、遗漏、歧义和不一致，输出需求理解总结和审阅报告。末尾自动执行 prd-gate 门禁判定，无需单独触发。

**位于**：流程起点，PRD 就绪后触发

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| PRD 文档 | `input/prd/*.md` | 必须 |
| 产品原型 | `*prototype*/**/*.html` 或 URL | 可选，有则对比 PRD 与原型一致性 |
| 历史版本 PRD | `docs/PRD-*-v*.md` | 可选，用于版本一致性检查 |

**触发语句**

```
测试评审 PRD，按默认来
```

```
从测试角度看看这个 PRD，PRD 路径 input/prd/prd-v1.md，全量审阅
```

```
测试 PRD 审阅，重点关注权限模块和状态机部分
```

---

## 2. prd-gate — PRD 质量门禁（内嵌）

**用途**：判定 PRD 质量是否达到可以开始设计测试用例的标准，输出通过 / 不通过二元结论。

> ⚠️ **正常流程下无需手动触发**：prd-gate 已内嵌在 test-prd-review 末尾自动执行，结论写入 `review/prd-gate-result.md`。仅在需要单独重新判定时手动触发。

**位于**：test-prd-review 末尾自动执行；手动触发时位于 test-prd-review 之后 → test-point-extraction 之前

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| PRD 审阅报告 | `review/test-prd-review-report.md` | 由 test-prd-review 生成 |

**触发语句（仅手动重新判定时使用）**

```
PRD 门禁，审阅报告按默认来
```

```
重新执行 PRD 门禁检查，报告路径 review/test-prd-review-report.md
```

---

## 3. tech-doc-review — 技术文档审阅

**用途**：审阅开发提交的技术文档，对每个模块输出 🟢 / 🟡 / 🔴 判定，内置放行 / 阻塞门禁。后端技术文档和前端技术文档分别触发，或合并触发。

**位于**：prd-gate 通过后 → test-point-extraction 之前（两路并行）

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| 技术文档 | `input/tech/*.md` | 接口定义 / 系统设计 / 前端规格 / 交互设计等 |
| PRD 文档 | `input/prd/*.md` | 用于需求一致性对比 |

**触发语句**

```
技术文档审阅，按默认来
```

```
// 后端技术文档
审阅后端技术文档，文档路径 input/tech/backend-design.md，PRD 按默认来
```

```
// 前端技术文档（含交互设计）
审阅前端技术文档，文档路径 input/tech/frontend-spec.md，PRD 按默认来
```

```
// 重点关注指定模块
tech-doc-review，重点关注权限设计和状态机部分，按默认来
```

---

## 4. test-point-extraction — 测试点提炼

**用途**：从 PRD 审阅摘要中提炼结构化测试点清单，覆盖正向流程、边界值、异常场景、权限、状态机等维度，输出 `test-points.md` 作为用例设计的覆盖基准。

**位于**：prd-gate 通过 + 两路技术文档审阅全部通过后 → test-case-design Mode A 之前

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| PRD 审阅摘要 | `review/test-prd-summary.md` | 由 test-prd-review 生成 |
| PRD 审阅报告 | `review/test-prd-review-report.md` | 用于提取高风险问题加密覆盖 |

**触发语句**

```
提炼测试点，按默认来
```

```
生成测试点清单，摘要路径 review/test-prd-summary.md，全量提炼所有模块
```

```
测试点提炼，权限控制模块历史问题较多，需要重点关注
```

> **知识库自动加载**：系统自动检查 `knowledge/risk-profiles/{模块名}.md` 和 `knowledge/defect-patterns/{模块名}.md`，有则加载历史高风险维度和缺陷模式并在对应测试点升级标注，无则静默跳过，无需手动指定。

---

## 5. test-case-design — 测试用例设计

**用途**：根据 PRD / 测试点清单 / 技术文档设计测试用例，支持五种模式：

| 模式 | 用途 |
|------|------|
| **Mode A** | 基于 PRD 初次生成 UI 用例初稿 |
| **Mode B** | 依据技术文档补充风险场景用例 |
| **Mode C** | 线上回归用例设计与发版验证 |
| **Mode D** | 冒烟测试专项（核心链路 Happy Path + EX 关键异常，作为开发自测依据） |
| **Mode E** | 基于用例审核报告补充缺失用例（test-case-review 之后触发） |

**位于**：test-point-extraction 之后（Mode A）/ tech-doc-review 放行后（Mode B）/ 发版前（Mode C）/ 提测前（Mode D）/ test-case-review 之后（Mode E）

**需要提前准备**

| 材料 | 默认路径 | 模式 |
|------|---------|------|
| PRD 文档 | `input/prd/*.md` | A / B / C |
| 测试点清单 | `review/test-points.md` | A |
| 技术文档审阅报告 | `review/tech-review-summary.md` | B |
| 已有用例文件 | `test_suites/*.md` | B / C |
| 用例审核报告 | `review/case-review-report.md` | E |

**触发语句**

```
// Mode A：PRD 初稿用例
设计测试用例 Mode A，PRD 路径 input/prd/prd-v1.md，按默认来
```

```
// Mode B：技术文档风险场景补全
test-case-design Mode B，技术审阅报告按默认来
```

```
// Mode C：线上回归
生成线上回归用例 Mode C，PRD 路径 input/prd/prd-v2.md
```

```
// Mode D：冒烟套件（开发自测用）
生成冒烟测试套件 Mode D，PRD 按默认来
```

```
// Mode E：基于审核报告补充缺失用例
基于审核报告补充用例，审核报告按默认来
```

> **知识库自动加载（Mode A）**：系统自动检查 `knowledge/constraints/{模块名}.md` 和 `knowledge/case-samples/{模块名}/`，有则加载业务约束规则和历史优质用例样例，无则静默跳过，无需手动指定。

---

## 6. api-test-case-design — 接口测试用例设计

**用途**：基于接口定义文档设计接口测试用例，覆盖正向、边界值、等价类、错误码、鉴权、幂等、响应结构七个维度，输出可供 api-test-execution 直接执行的用例套件。

| 模式 | 用途 |
|------|------|
| **Mode A** | 基于接口文档初次全量生成 |
| **Mode B** | 针对变更接口设计增量回归用例 |

**位于**：tech-doc-review 放行后，与 test-case-design Mode A 并行

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| 接口定义文档 | `input/tech/*.md` | 含入参/出参/状态码/错误码 |
| 变更接口列表 | 用户提供 | 仅 Mode B 需要 |

**触发语句**

```
// Mode A：首次生成
设计接口测试用例，接口文档路径 input/tech/api-spec.md
```

```
// Mode B：接口变更回归
接口回归用例，变更了用户登录接口和权限校验接口，接口文档按默认来
```

---

## 7. test-case-review — 用例审核

**用途**：对 test-case-design 和 api-test-case-design 生成的用例进行 AI 辅助审核，对照 test-points.md 检查覆盖完整性、边界/异常路径遗漏、预期结果与技术文档一致性、步骤可执行性，输出审核报告。

**位于**：test-case-design Mode A + api-test-case-design 完成后 → 用例补充（test-case-design Mode E）之前

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| UI 用例文件 | `review/test-cases-ui.md` | 由 test-case-design 生成 |
| 接口用例文件 | `review/test-cases-api.md` | 由 api-test-case-design 生成 |
| 测试点清单 | `review/test-points.md` | 覆盖完整性的检查基准 |
| 技术文档 | `input/tech/*.md` | 预期结果一致性参考 |

**触发语句**

```
审核用例，按默认来
```

```
用例审核，UI 用例和接口用例都审，按默认来
```

```
检查用例覆盖，只审核 UI 用例，路径 review/test-cases-ui.md
```

---

## 8. test-case-prd-consistency — 用例与 PRD 一致性排查

**用途**：排查测试用例与 PRD 文档不一致的问题，提供根因分析和修复方案。PRD 发生版本变更后**必须触发**。

**位于**：PRD 版本变更后 / 怀疑用例偏差时随时触发

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| PRD 文档 | `input/prd/*.md` | 当前版本 |
| 测试用例文件 | `test_suites/*.md` | 全量或指定模块 |

**触发语句**

```
// PRD 变更后（必选）
PRD 有变更，v1.2 升级到 v1.3，检查用例是否需要更新，PRD 和用例按默认来
```

```
// 怀疑偏差
用例跟需求不一样，排查用例 TC-LOGIN-003 和 TC-LOGIN-007
```

```
// 全量质检
全量排查用例与 PRD 一致性，按默认来
```

---

## 9. test-case-code-coverage — 用例代码覆盖分析

**用途**：基于语义分析将测试用例映射到源代码分支 / 路径，识别未覆盖的代码路径和用例盲区。

**位于**：用例设计完成后，按需触发

**需要提前准备**

| 材料 | 说明 |
|------|------|
| 测试用例文件 | `test_suites/*.md` |
| 源代码文件 | 需要分析覆盖度的业务代码 |

**触发语句**

```
分析用例代码覆盖，用例文件 test_suites/suite_login.md，源码目录 src/modules/auth/
```

```
用例覆盖代码分析，排查支付模块的用例盲区
```

---

## 10. submission-gate — 提测门禁

**用途**：执行九项提测门禁检查，核验开发侧自测证明，输出通过 / 不通过结论。全部通过后方可进入测试执行阶段。

**九项检查**：①技术文档审阅完成度 ②无🔴模块 ③开发自测截图（Happy Path+EX 逐条截图） ④测试环境登录预检 ⑤PRD门禁 ⑥用例套件存在 ⑦单测分支覆盖率≥60% ⑧MR/PR已Approve ⑨API契约测试

**位于**：用例基线冻结之后 → 测试执行（冒烟验证）之前，作为进入第六阶段的入口门禁

**需要提前准备**

| 材料 | 默认路径 / 来源 | 说明 |
|------|--------------|------|
| 技术文档审阅汇总 | `review/tech-review-summary.md` | 由 tech-doc-review 生成 |
| 开发自测截图 | 开发提供 | Happy Path + EX 用例逐条截图/录屏 |
| 单元测试覆盖率报告 | CI 报告链接或截图 | 分支覆盖率 ≥ 60% |
| MR/PR 链接 | 开发提供 | 须已有 ≥ 1 人 Approve |
| API 契约测试状态 | CI 报告 / 说明 | 已集成须通过，未集成提供原因 |
| 测试环境 URL + 账号 | 测试提供 | 用于 AI 执行登录预检 |

**触发语句**

```
提测门禁，审阅报告按默认来
```

```
执行提测门禁，tech-review-summary 在 review/tech-review-summary.md，检查全部模块
```

```
可以提测吗？按默认来
```

---

## 11. test-data-preparation — 测试数据准备

**用途**：通过 API 自动创建测试所需数据（Mode A），或在测试完成后清理测试数据（Mode B）。适用于前置条件标注了 `[数据准备: API]` 的用例，或 UI 创建步骤超过 5 步的场景。

**位于**：submission-gate 通过后（Mode A）/ 测试执行完毕后（Mode B）

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| 技术文档 | `input/tech/*.md` | 用于了解 API 结构 |
| 测试用例文件 | `test_suites/*.md` | 含 `[数据准备: API]` 标注的用例 |
| 测试环境 Base URL | 用户提供 | API 调用地址 |
| 认证账号 | 用户提供 | 用于获取 Token |

**触发语句**

```
// Mode A：准备数据
准备测试数据，用例文件 test_suites/suite_team.md，环境 https://test.example.com，账号 admin/123456
```

```
// Mode B：清理数据
清理测试数据，数据准备报告按默认来
```

---

## 12. test-execution — UI 测试执行

**用途**：通过 browser-use MCP 直接操作浏览器执行 UI 测试用例，自主判断结果并生成执行报告。支持三种模式：

| 模式 | 触发关键词 | 说明 |
|------|-----------|------|
| **冒烟验证（Mode S）** | "冒烟验证" / "提测冒烟" | 只跑冒烟套件（P0），输出通过/打回结论 |
| **标准执行** | "执行测试用例" / "跑用例" | 测试环境全量执行 |
| **线上回归（D5）** | "线上回归" / "D5验证" | 生产环境执行，含熔断机制 |

**位于**：submission-gate 通过后（冒烟验证）/ test-data-preparation 之后（标准执行）

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| 测试用例文件 | `test_suites/*.md` | Markdown 格式用例套件 |
| 数据准备报告 | `test_suites/data-prep-report-*.md` | 如有，提供变量映射 |
| 测试环境 Base URL | 用户提供 | 浏览器访问地址 |
| 认证账号 | 用户提供 | 登录所需账号密码 |

**触发语句**

```
// 冒烟验证（提测后，测试团队独立验证）
冒烟验证，用例文件 test_suites/suite_smoke.md，环境 https://test.example.com，账号 admin/123456
```

```
// 标准执行
执行测试用例，用例文件 test_suites/suite_login.md，环境 https://test.example.com，账号 admin/123456
```

```
// 线上回归
线上回归 D5，用例文件 test_suites/suite_smoke.md，生产环境 https://www.example.com，账号 admin/123456
```

---

## 13. api-test-execution — 接口测试执行

**用途**：读取 Markdown 接口测试用例，直接发送 HTTP 请求，自主断言响应结果并生成执行报告。

**位于**：api-test-case-design 之后，与 test-execution 并列

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| 接口测试用例文件 | `test_suites/api_suite_*.md` | 由 api-test-case-design 生成 |
| 数据准备报告 | `test_suites/data-prep-report-*.md` | 如有，含变量映射表 |
| 测试环境 Base URL | 用户提供 | 接口服务地址 |
| 认证账号 | 用户提供 | 获取 Token 用 |

**触发语句**

```
执行接口测试，用例文件 test_suites/api_suite_user.md，环境 https://test.example.com，账号 admin/123456
```

```
跑接口用例，只跑 P0 级别，按默认来，环境 https://test.example.com，账号 admin/123456
```

---

## 14. test-result-sync — 测试结果回填

**用途**：将 AI 执行报告中的测试结果同步回填到 Markdown 用例文档或 Excel，生成覆盖率和通过率统计报告。

**位于**：test-execution / api-test-execution 之后，与 bug-sync 并行触发

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| AI 执行报告 | `test_reports/test_report_*.md` | 由 test-execution 生成 |
| 目标用例文档 | `test_suites/*.md` 或 Excel 文件 | 需要回填结果的文件 |

**触发语句**

```
同步测试结果，执行报告和用例文件按默认来
```

```
回填测试结果到 Excel，执行报告 test_reports/test_report_20260408.md，Excel 文件 testcase.xlsx
```

```
更新用例状态，执行报告按默认来，回填到 Markdown
```

---

## 15. bug-sync — 缺陷同步

**用途**：从测试执行报告中提取失败用例，生成结构化缺陷记录。支持输出 Markdown 缺陷清单、CSV 导入文件，或自动提交到云效 Projex。

**位于**：test-execution / api-test-execution 之后，与 test-result-sync 并行触发 → test-report 之前

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| UI 执行报告 | `test_reports/test_report_*.md` | 取最新一份 |
| 接口执行报告 | `test_reports/api_report_*.md` | 如有 |
| 云效配置（可选） | `tools/yunxiao/config.yaml` | 选择云效输出时，AI 会引导填写 |

**触发语句**

```
// 输出 Markdown 缺陷清单
同步缺陷，执行报告按默认来，输出 Markdown
```

```
// 自动提交到云效
提交缺陷到云效，执行报告按默认来
```

```
// 同时输出本地报告 + 云效
生成缺陷报告并提交云效，报告按默认来
```

> 选择云效输出时，AI 会自动检查配置并引导填写：PAT、组织 ID（首次）、项目 ID、当前迭代 ID。

---

## 16. test-report — 测试报告生成

**用途**：聚合执行报告和缺陷清单，生成包含测试范围、执行结果、缺陷分布和质量结论的完整测试报告。

**位于**：test-result-sync + bug-sync 完成后 → release-gate 之前

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| UI 执行报告 | `test_reports/test_report_*.md` | 取最新一份 |
| 接口执行报告 | `test_reports/api_report_*.md` | 如有 |
| 缺陷清单 | `bug_reports/bug-report-*.md` | 由 bug-sync 生成 |

**触发语句**

```
生成测试报告，按默认来
```

```
出测试报告，迭代名称「用户中心 v2.1」，报告和缺陷清单按默认来
```

---

## 17. release-gate — 发布门禁

**用途**：读取测试执行报告和缺陷清单，核验 P0 通过率、开放 Fatal/Critical 缺陷数等发布就绪条件，输出可发布 / 不可发布结论。

**位于**：test-report 之后 → 发布操作之前

**需要提前准备**

| 材料 | 默认路径 | 说明 |
|------|---------|------|
| UI 执行报告 | `test_reports/test_report_*.md` | 取最新一份 |
| 接口执行报告 | `test_reports/api_report_*.md` | 如有 |
| 测试报告 | `test_reports/test-report-*.md` | 由 test-report 生成 |

**触发语句**

```
发布门禁，按默认来
```

```
可以发布吗？报告按默认来
```

```
上线门禁，P0+P1 通过率要求 95%，按默认来
```

---

## 18. defect-retest — 缺陷回归验证

**用途**：开发修复缺陷后，针对关联测试用例重新执行定向回归，按结果更新云效缺陷状态（通过→关闭，失败→重新打开），输出回归验证报告。

**位于**：bug-sync 之后，开发完成修复后触发 → 下一轮 release-gate 之前

**需要提前准备**

| 材料 | 默认路径 / 来源 | 说明 |
|------|--------------|------|
| 缺陷清单 | `bug_reports/bug-report-*.md` | 或从云效实时查询 |
| 测试用例文件 | `test_suites/*.md` | 关联的用例套件 |
| 测试环境 Base URL | 用户提供 | 验证修复的环境地址 |
| 认证账号 | 用户提供 | 登录账号 |
| 云效配置（可选） | `tools/yunxiao/config.yaml` | 用于更新缺陷状态 |

**触发语句**

```
缺陷回归，缺陷清单按默认来，环境 https://test.example.com，账号 admin/123456
```

```
开发修完了，验证修复，从云效查询已解决缺陷，环境 https://test.example.com，账号 admin/123456
```

```
回归验证，只回归缺陷 BUG-LOGIN-001 和 BUG-LOGIN-003
```

---

## 19. multimodal-visual-assertion — 多模态视觉断言（补充执行能力）

**用途**：使用 AI 视觉模型对页面截图执行多模态断言，处理无法通过 DOM 文本验证的内容：图表趋势、Canvas 渲染、图片是否正常显示、PDF 预览、复杂布局等。与 test-execution 配合使用，处理用例中标注了 `[断言: 视觉-AI]` 的预期结果。

**位于**：test-execution 执行过程中，遇到 `[断言: 视觉-AI]` 注解时按需引入

> ⚠️ **不适用场景**：纯文字内容（用 `[断言: 视觉]`）、精确数值（用 `[断言: API]`）、数据库状态（用 `[断言: DB-Query]`）。

**在用例预期结果中的标注方式**

```markdown
预期结果：
- [断言: 视觉-AI] 折线图显示近 7 天数据呈上升趋势，最后一个数据点高于第一个数据点
- [断言: 视觉-AI] 页面右上角头像区域显示用户头像，非默认灰色占位图
- [断言: 视觉-AI] 导出的图表缩略图与页面展示内容一致（颜色、图例、大致形状）
```

**需要提前准备**

| 材料 | 说明 |
|------|------|
| 用例中的 `[断言: 视觉-AI]` 标注 | 附带自然语言描述的验证目标 |
| 当前页面或已有截图 | test-execution 执行到该步骤时自动采集 |

**触发语句**

```
// 由 test-execution 自动触发（遇到 [断言: 视觉-AI] 时）
// 不需要单独触发；以下为独立使用时的示例

视觉断言，验证截图 test_reports/screenshots/2026-04-13/CP1_xxx.png 中折线图是否呈上升趋势
```

```
// 对当前页面执行视觉断言
图表验证，验证当前页面折线图数据呈上升趋势，近 7 天最后一个数据点高于第一个
```

---

## 20. visual-location-fallback — 视觉定位兜底（补充执行能力）

**用途**：当语义定位（可见文本 / aria-label / placeholder / 相对位置）全部失败后，通过截图分析定位目标元素的视觉坐标，作为 test-execution 元素定位的最后兜底机制。适用于无障碍标注缺失的遗留系统、Canvas 组件、自定义图形控件等场景。

**位于**：test-execution 执行过程中，语义定位全部失败时自动触发；或用例步骤显式标注 `[定位: 视觉兜底]` 时直接进入

> ⚠️ **仅在语义定位全部失败后使用**：视觉坐标定位受分辨率和布局变化影响，脆弱性高；优先修复用例的语义定位描述或推动开发补充 aria-label。

**在用例步骤中的标注方式（显式）**

```markdown
步骤：
3. [定位: 视觉兜底] 点击画布左上角的"新建节点"图标按钮（蓝色圆形，内含加号）
```

**需要提前准备**

| 材料 | 说明 |
|------|------|
| 当前页面（已正常加载） | 语义定位失败后，页面必须处于正常加载状态（非白屏/加载中）|
| 目标元素的视觉特征描述 | 颜色、形状、图标样式、大致位置、相邻参照物 |

**触发语句**

```
// 由 test-execution 自动触发（语义定位全部失败后）
// 不需要单独触发；以下为独立使用时的示例

视觉定位，找画布左上角的蓝色圆形加号按钮，点击
```

```
// 独立定位并执行操作
坐标定位，目标：表格第一行操作列的删除图标（红色垃圾桶），执行点击
```
