---
skill: test-case-review
based_on: harness@1.0.0
he_path: linscode/skills/iteration/testing/test-case-review
override_count: 4
last_updated: 2026-04-17
---

# test-case-review 项目定制

## 覆盖 1：Phase 0 默认用例路径

**HE 原文位置**：Phase 0 → 问题 1（UI 用例路径）和 问题 2（接口用例路径）
**HE 原文摘要**：默认 `review/test-cases-ui.md` 和 `review/test-cases-api.md`
**定制为**（本项目迭代目录 `testcase/` = 上游 `test_suites/`，见 `.claude/rules/rules.md` 路径别名）：
- UI 用例：自动扫描 `testcase/suite_*.md`；若未找到再尝试 `review/test-cases-ui.md`
- 接口用例：自动扫描 `testcase/api_suite_*.md`；若未找到再尝试 `review/test-cases-api.md`

## 覆盖 2：Phase 1 用例文件读取

**HE 原文位置**：Phase 1 → 步骤 2（读取 UI 用例文件）
**HE 原文摘要**：加载默认 `review/test-cases-ui.md`
**定制为**：先扫描 `testcase/suite_*.md`（test-case-design 标准输出路径），若未找到再尝试用户指定路径

## 新增 3：Phase 2 新增颗粒度合规性检查维度

**HE 原文位置**：Phase 2 → 4 个检查维度（覆盖完整性 / 边界异常 / 预期结果一致性 / 步骤可执行性）
**HE 原文摘要**：无颗粒度检查维度
**定制为**：新增第 5 个检查维度：

#### 维度 5：颗粒度合规性

加载 `.claude/skills/test-case-design/references/granularity-standard.md`（v4.0），逐条检查：

| 检查项 | 方法 | 输出标签 |
|--------|------|---------|
| 过粗检测 | 对每条用例执行 S4 失败归因测试，无法一句话归因 → 标记 | `[颗粒度-过粗]` |
| 硬规则违反 | 检查用例是否违反 R1~R14 任一规则 | `[颗粒度-R{N}违反]` |
| 过细检测 | 检查用例是否命中合并触发器 M1~M5（`granularity-review.md` §3） | `[颗粒度-过细]` |

**审核报告输出**：在原有 §一~§四 之后，新增 §五"颗粒度问题"章节：

```markdown
## 五、颗粒度问题

### 5.1 过粗用例（需拆分）

| 用例编号 | 用例名称 | 违反规则 | 建议拆分方式 | 预计拆为 |
|---------|---------|---------|------------|---------|
| XXX-001 | 验证所有搜索条件 | R11 | 按查询方式拆分 | 4 条 |

### 5.2 过细用例（建议合并）

| 用例编号组 | 用例名称 | 合并触发器 | 建议合并为 |
|-----------|---------|----------|----------|
| XXX-015 + XXX-016 | 排序验证 + 分页验证 | M3 | 1 条"通用列表交互" |

### 5.3 颗粒度评分

得分：{N}/95 → 评级：🟢/🟡/🟠/🔴
（评分细则见 `granularity-review.md` §5）
```

**与 Mode E / Mode F 的衔接**：审核报告 §六 审核结论中**必须**追加"推荐下一步"：

```
推荐下一步：
- 若 §一~§四 存在覆盖缺失或步骤问题 → 建议先执行 /test-case-design Mode E 补充缺失用例
- 若 §五 颗粒度得分 < 70 → 建议执行 /test-case-design Mode F 优化颗粒度
- 两者可串行：先 Mode E 补全 → 再 Mode F 优化（先保证覆盖完整，再调整粒度）
- 若 §一~§五 均通过 → 无需额外操作，用例可进入执行阶段
```

审核报告 §五 的颗粒度问题可直接作为 `/test-case-design Mode F` 的输入，用户说"按审核报告优化颗粒度"时自动触发 Mode F。

## 新增 4：Phase 2 新增"执行记录列格式"检查项

**HE 原文位置**：Phase 2 → 4 个检查维度之外
**HE 原文摘要**：无对套件顶部执行顺序表结构的格式检查
**定制为**：Phase 2 新增格式硬性检查项（独立于维度评分，失败直接标记审核不通过）：

```
☐ 套件顶部「执行顺序」表最右侧有且仅有一列「执行记录」
☐ 单元格状态前缀属于五态白名单：⏸ 待执行 / ✅ 通过 / ❌ 失败 / 🚫 阻塞 / ⏭ 跳过
☐ 新生成套件（未执行场景）默认值为 `⏸ 待执行`（无分隔符，无日期/备注）
☐ 非待执行状态使用 ` · ` 分隔状态/日期/备注（如 `✅ 通过 · 2026-04-17`）
```

**违规行为**：
- 缺列或保留旧"三列"结构（执行状态/执行日期/备注） → 审核不通过
- 状态前缀不在白名单（如出现"可执行""pass""done""pending"） → 审核不通过，列出每处违规的用例编号和实际值
- 分隔符混用 `|` `/` `-` 而非 ` · ` → 审核不通过
- 单元格出现换行或超过一行的详情 → 审核提示修复（详情应落 execution_report）

审核报告在 §六 审核结论中新增"**套件格式合规性**"小节，列出上述检查结果。任一项失败 → 整体审核结论为"不通过"（优先级高于颗粒度评分）。

**规范引用**：
- 生成规范见 `.claude/skills/test-case-design/OVERRIDES.md` §新增 10
- API 套件规范见 `.claude/skills/api-test-case-design/OVERRIDES.md` §新增 3
- 五态语义与 `.claude/skills/test-execution/OVERRIDES.md` §覆盖 2 对齐
