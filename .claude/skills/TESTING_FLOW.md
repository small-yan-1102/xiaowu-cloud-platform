# 测试侧完整流程

> 本文档描述测试侧各 Skill 的标准执行顺序、触发时机和衔接关系。

---

## 主流程

### 阶段一：需求理解
**触发时机**：PRD 冻结后立即开始

| Skill | 输入 | 输出 |
|-------|------|------|
| `test-prd-review` | PRD 文档 | PRD 审阅摘要（`review/test-prd-summary.md`）+ 审阅报告（`review/test-prd-review-report.md`）+ PRD 门禁结论（`review/prd-gate-result.md`）|

> **prd-gate 已内嵌为 Phase 5**：test-prd-review 执行完毕后自动判定 B-1～B-7 门禁条件，将结论写入 `review/prd-gate-result.md`，无需单独触发。
> - ❌ 不通过（任一 B-1～B-7 触发）→ 通知产品修复，阻塞后续流程
> - ✅ 通过 → 进入阶段二

---

### 阶段二：技术文档审阅
**触发时机**：PRD 门禁通过后，开发完成技术文档时触发（后端/前端两路并行）

| Skill | 输入 | 输出 |
|-------|------|------|
| `tech-doc-review` | 技术文档（`input/tech/*.md`）+ PRD（`input/prd/*.md`）| 模块判定报告（🟢/🟡/🔴）+ 审阅汇总（`review/tech-review-summary.md`）|

> **硬阻塞门禁**：任意模块出现 🔴 → **整个迭代停止，退回开发重新修改技术文档**（视严重程度可退回至 PRD 审阅阶段）。后端和前端两路均无 🔴 才可进入下一阶段。

---

### 阶段三：测试点提炼
**触发时机**：PRD 门禁通过 **且** 两路技术文档审阅全部通过（无 🔴）后

| Skill | 输入 | 输出 |
|-------|------|------|
| `test-point-extraction` | PRD 审阅摘要（`review/test-prd-summary.md`）+ 审阅报告（`review/test-prd-review-report.md`）| 结构化测试点清单（`review/test-points.md`）|

> 覆盖 7 个维度：PF 正向流程 / BV 边界值 / EX 异常场景 / AU 权限 / SM 状态机 / IN 集成依赖 / **UI 渲染状态**
> 读取审阅报告进行风险映射：B 系列问题→测试点升级 P0；S 系列→标注⚠️待补充；A 系列→标注歧义待确认
> 每个测试点标注 AI 可执行性标签（`[AI]` / `[AI+人工]` / `[人工]`），作为 test-case-design 的执行方式依据
> 输出结果作为 `test-case-design` Mode A 的覆盖基准，P0 测试点必须至少对应一条用例。
> **知识库自动加载**：自动检查 `knowledge/risk-profiles/{模块名}.md` 和 `knowledge/defect-patterns/{模块名}.md`，有则加载并在对应维度加深覆盖（测试点标注 `📚 知识库`），无则静默跳过。

---

### 阶段四：用例设计
**触发时机**：test-point-extraction 完成后，按以下顺序执行

| 顺序 | Skill | 适用场景 | 输入 | 输出 |
|------|-------|---------|------|------|
| 1 | `test-case-design` Mode A | 全部模块，基于测试点生成 UI 用例初稿 | 测试点清单（`review/test-points.md`）| `review/test-cases-ui.md` |
| 1 | `api-test-case-design` Mode A | 🟡 模块，初次生成接口用例 | 接口定义文档 | `review/test-cases-api.md` |
| 1 | `api-test-case-design` Mode B | 接口变更时补充回归用例 | 变更接口文档 | 追加至 `review/test-cases-api.md` |

> Mode A（UI 用例）与 api-test-case-design 并行执行，互不依赖。
> **知识库自动加载**：test-case-design Mode A 自动检查 `knowledge/constraints/{模块名}.md` 和 `knowledge/case-samples/{模块名}/`，有则加载业务约束和历史优质用例样例，无则静默跳过。

---

### 阶段四-审核：用例审核
**触发时机**：UI 用例和接口用例初稿均完成后

| Skill | 输入 | 输出 |
|-------|------|------|
| `test-case-review` | UI 用例（`review/test-cases-ui.md`）+ 接口用例（`review/test-cases-api.md`）+ 测试点清单（`review/test-points.md`）+ 技术文档（`input/tech/*.md`）| 审核报告（`review/case-review-report.md`）|

> AI 辅助扫描 4 个维度：覆盖完整性（对照 test-points.md）/ 边界/异常路径识别 / 预期结果与技术文档一致性 / 步骤可执行性
> 输出结论：🟢 通过 / 🟡 需修正 / 🔴 重新设计

---

### 阶段四-补充：用例补充与评审
**触发时机**：test-case-review 输出审核报告后（🟡/🔴 结论时）

| 顺序 | Skill | 说明 |
|------|-------|------|
| 1 | `test-case-design` Mode E | 读取 `review/case-review-report.md`，按覆盖缺失/边界缺失/可执行性问题生成补充用例 |
| 2 | 人工用例评审 | 三方评审会议确认用例基线，评审通过后冻结 |
| 3 | `test-case-design` Mode B | 依据技术文档补充风险场景（🟢 模块）|
| 4 | `test-case-design` Mode D | 生成冒烟套件（开发自测依据），从完整用例套件中提炼核心链路 |

> Mode B 和 Mode D 在用例基线冻结后执行，确保冒烟套件与最终用例保持一致。

---

### 阶段五：提测门禁
**触发时机**：开发完成功能开发并提测时

#### 触发门禁前，各方需准备好以下材料

| 准备方 | 需提供内容 | 对应检查项 | 说明 |
|-------|-----------|----------|------|
| **开发** | 按冒烟套件（`suite_smoke.md`）逐条执行并提交结果截图，包含 Happy Path 用例和 EX 关键异常核心用例；失败用例须说明原因（已知Bug/环境问题）| 检查③ | 必须以冒烟套件为执行依据，自制清单不接受；EX 用例须截图；纯口头"我测过了"不接受 |
| **开发** | 单元测试覆盖率证明（CI 流水线链接或覆盖率报告截图），**分支覆盖率 ≥ 60%** | 检查⑦ | 未提供或低于阈值则门禁不通过；纯前端静态页等不适用场景须由测试负责人确认 |
| **开发** | 本次提测对应的 MR/PR 链接（需已有 ≥ 1 人 Approve） | 检查⑧ | 无 Approve 或未提供链接则门禁不通过 |
| **开发** | API 契约测试 CI 报告链接或截图（Swagger/OpenAPI 自动校验接口入参/出参/状态码） | 检查⑨ | 已集成契约测试但存在失败项则门禁不通过；尚未集成则⚠️非阻塞警告 |
| **开发** | 本次提测的开发分支名称 + 是否已合并到 test 分支 | 检查④ | 测试部门依据此信息自行部署测试环境；未明确则门禁报告高亮⚠️警告 |
| **测试** | 完成测试环境部署后，提供测试环境 URL + 测试账号（用于 AI 自动执行登录预检）| 检查④ | 测试部门自行部署并确认环境可访问、账号有效后，再触发门禁 |

> ①②⑤⑥ 由 AI 从已有文件自动读取，无需人工准备：
> - 检查① / ②：来自 `review/tech-review-summary.md`（tech-doc-review 生成）
> - 检查⑤：来自 `review/prd-gate-result.md`（test-prd-review Phase 5 生成）
> - 检查⑥：来自 `test_suites/suite_smoke.md` + `suite_*.md`（test-case-design 生成）

#### 门禁检查项（九项）

| Skill | 检查项 | 结论 |
|-------|-------|------|
| `submission-gate` | ① tech-doc-review 全部完成（无 ⏳）<br>② 无 🔴 模块（🟡 模块有覆盖说明）<br>③ 开发按冒烟套件执行自测截图（Happy Path + EX 关键异常核心均须截图，无则直接不通过）<br>④ 测试环境就绪 + 登录预检<br>⑤ prd-gate 结论为通过（不存在→⚠️警告，不通过→阻塞）<br>⑥ 冒烟套件（`suite_smoke.md`）+ 至少一个模块套件存在<br>⑦ 单元测试分支覆盖率 ≥ 60%（未提供→阻塞）<br>⑧ MR/PR 已有 ≥ 1 人 Approve（未提供→阻塞）<br>⑨ API 契约测试通过（已集成时必须通过；未集成→⚠️警告） | ✅ 通过 → 进入测试执行<br>❌ 不通过 → 退回开发 |

---

### 阶段六：测试执行
**触发时机**：提测门禁通过后，按顺序执行

| 顺序 | Skill | 说明 |
|------|-------|------|
| ⓪ | `test-execution` Mode S（冒烟验证） | 测试团队独立验证核心链路（区别于开发自测证明）；仅跑 P0 冒烟套件；**30分钟内发现 P0 → 快速失败标注**；连续 2 次快速失败 → 🚨 下次提测须技术负责人陪同走查签字；非快速失败第 2 次起 → 🚨升级处理（暂停提测组织团队排查）；通过后继续 |
| 1 | `api-test-execution` | 先验证接口层，HTTP 执行接口用例 |
| 2 | `test-data-preparation` Mode A | 接口通过后，通过 API 创建 UI 测试所需数据（含环境预置检查清单、人工执行变量速查表）|
| 3 | `test-execution` | 数据就绪后执行 UI E2E 测试用例；`[执行方式: 人工]` 用例跳过 AI 执行并列入人工清单；`[验证:]` 失败标记🚫阻塞而非❌失败 |
| 4 | `test-result-sync` 并行 `bug-sync` | 两者均从执行报告读取，互不依赖，并行执行：test-result-sync 回填 MD/Excel 用例执行状态；bug-sync 从❌失败用例生成缺陷清单 |
| 5 | `test-data-preparation` Mode B | 清理本次准备的测试数据，还原测试环境 |

> **顺序依据**：接口是 UI 的底层依赖；`test-data-preparation` 通过 API 创建数据，依赖接口可用；UI 测试依赖数据就绪；Mode B 清理在结果同步后执行，确保数据已不再被引用。

---

### 阶段七：报告与发布判定

| Skill | 输入 | 输出 |
|-------|------|------|
| `test-report` | 执行报告 + 缺陷清单 + 云效实时缺陷状态 | 质量结论（🟢/🟡/🔴）；`[人工执行]` 用例单独列出不计入通过率 |
| `release-gate` | 执行报告 + test-report + 缺陷状态 | 六项检查：P0全通过、无Fatal、无Critical、P0+P1通过率≥阈值、阻塞+跳过占比≤上限、Major缺陷数；二元结论：可发布 / 阻塞 |

---

### 阶段八：缺陷修复回归
**触发时机**：开发修复缺陷并在云效标记「已解决」后，可多轮循环

| Skill | 说明 |
|-------|------|
| `defect-retest` | 从云效拉「已解决」缺陷 → 定向重执行关联用例 → 指引关闭或重新打开 |

循环条件：`defect-retest` 完成后，若 Fatal/Critical 全部关闭 → 重新触发 `release-gate`

---

### 阶段九：线上验证
**触发时机**：发布上线后

| Skill | 说明 |
|-------|------|
| `test-execution` Mode D5 | 生产环境核心链路回归，内置熔断机制 |

---

## 按需质检工具

以下工具**不占流程位置**，根据具体情况随时触发，不影响主流程推进：

| Skill | 触发场景 |
|-------|---------|
| `test-case-prd-consistency` | **① PRD 发生版本变更后强制触发**（输出受影响用例清单）；② 怀疑用例与 PRD 存在偏差；③ 用例由多人分批生成担心版本混乱；④ 生成质量异常时排查 |
| `test-case-code-coverage` | 需验证用例是否覆盖关键代码路径；新功能涉及复杂分支逻辑担心遗漏 |

---

## 补充执行能力

以下技能**按需引入**，不强制加载。test-execution 执行测试用例时，遇到对应注解才启用；未加载时记录「跳过」，不影响其余步骤。

| Skill | 适用场景 | 注解标识 |
|-------|---------|---------|
| `multimodal-visual-assertion` | 图表（折线/柱状/饼图）趋势、Canvas 渲染内容、图片是否正常显示、PDF/文档预览、复杂布局——无法通过 DOM 文本验证的视觉内容 | `[断言: 视觉-AI]` |
| `visual-location-fallback` | 可见文本 / aria-label / placeholder / 相对位置四种语义定位全部失败时，通过截图分析输出坐标进行点击兜底；适用于无障碍标注缺失的遗留系统、Canvas 组件、自定义图形控件 | `[定位: 视觉兜底]`（显式）或自动触发 |

> **引入方式**：在触发 test-execution 前声明需要使用哪些补充能力，或在用例步骤/预期结果中使用上述注解（test-execution 遇到注解后自动加载对应 skill）。

---

## 流程全貌

```
PRD 冻结
  └─ test-prd-review（含内嵌 prd-gate，B-1～B-7）
       ├─ ❌ → 通知产品修复，阻塞
       └─ ✅ → 输出 prd-gate-result.md

开发完成技术文档（后端 + 前端，两路并行）
  └─ tech-doc-review
       ├─ 🔴 任意模块 → 整个迭代停止，退回开发修复技术文档（或退回 PRD 审阅阶段）
       └─ 全部 🟢/🟡 → 放行

两路技术文档审阅全部通过
  └─ test-point-extraction（7维度 + AI可执行性标签 + 审阅报告风险映射）
       └─ test-case-design Mode A        → review/test-cases-ui.md（UI 初稿）
          api-test-case-design (A/B)     → review/test-cases-api.md（并行）
               └─ test-case-review
                    ├─ 🟢 通过 → 进入补充阶段
                    └─ 🟡/🔴 → test-case-design Mode E（按审核报告补充）
                         └─ 人工用例评审（冻结基线）
                              └─ test-case-design Mode B（风险场景）
                                   └─ test-case-design Mode D → suite_smoke.md（冒烟套件）

开发提测
  └─ submission-gate（九项检查，核验开发自测证明）
       ├─ ❌ → 退回开发
       └─ ✅
            └─ ⓪ test-execution Mode S（测试团队独立冒烟验证）
                 ├─ ❌ 第1~2次 → 打回开发
                 ├─ ❌ 第2次起 → 🚨升级处理
                 └─ ✅ → 全量执行
                      └─ ① api-test-execution
                           └─ ② test-data-preparation Mode A
                                └─ ③ test-execution（[人工执行]跳过AI/[验证:]失败→阻塞）
                                     └─ ④ test-result-sync 并行 bug-sync
                                          └─ ⑤ test-data-preparation Mode B（清理）

测试人员触发
  └─ test-report（人工执行用例单独统计）
       └─ release-gate（六项检查）
            ├─ ❌ → defect-retest → （循环）→ release-gate
            └─ ✅ → 发布上线
                         └─ test-execution Mode D5（线上验证）
```

---

## Skill 索引

| Skill | 所在阶段 | 类型 |
|-------|---------|------|
| `test-prd-review` | 阶段一 | 主流程（含内嵌 prd-gate）|
| `prd-gate` | 阶段一（内嵌）| 主流程（门禁，B-1～B-7，由 test-prd-review 自动执行）|
| `tech-doc-review` | 阶段二 | 主流程（硬阻塞门禁）|
| `test-point-extraction` | 阶段三 | 主流程 |
| `test-case-design` | 阶段四 | 主流程 |
| `api-test-case-design` | 阶段四 | 主流程 |
| `test-case-review` | 阶段四-审核 | 主流程 |
| `submission-gate` | 阶段五 | 主流程（门禁，九项检查）|
| `api-test-execution` | 阶段六 | 主流程 |
| `test-data-preparation` | 阶段六 | 主流程 |
| `test-execution` | 阶段六、九 | 主流程 |
| `test-result-sync` | 阶段六 | 主流程（与 bug-sync 并行）|
| `bug-sync` | 阶段六 | 主流程（与 test-result-sync 并行）|
| `test-report` | 阶段七 | 主流程 |
| `release-gate` | 阶段七 | 主流程（门禁，六项检查）|
| `defect-retest` | 阶段八 | 主流程（循环）|
| `test-case-prd-consistency` | — | 按需质检工具 |
| `test-case-code-coverage` | — | 按需质检工具 |
| `multimodal-visual-assertion` | 阶段六（按需）| 补充执行能力 |
| `visual-location-fallback` | 阶段六（按需）| 补充执行能力 |
