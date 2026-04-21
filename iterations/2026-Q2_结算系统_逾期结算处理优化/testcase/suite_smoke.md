# 逾期结算处理 — 冒烟测试套件

> **生成日期**: 2026-04-15
> **模式**: Mode D（冒烟测试专项设计）
> **关联需求**: PRD V4.5（2026-04-10）
> **技术文档**: `systems/结算系统/knowledge/逾期结算处理.md`
> **预计全流程时间**: ~8 分钟（数据准备 ~2.5min + 执行 ~5.5min）

---

## 执行顺序

| 顺序 | 用例编号 | 类型 | 执行方式 | 预计时间 |
|------|---------|------|---------|---------|
| 1 | SMOKE-OVERDUE-001 | Happy Path | browser-use | ~90s |
| 2 | SMOKE-OVERDUE-EX-001 | 关键异常核心 | browser-use | ~30s |
| 3 | SMOKE-OVERDUE-002 | Happy Path | browser-use | ~90s |
| 4 | SMOKE-OVERDUE-EX-002 | 关键异常核心 | browser-use | ~30s |
| 5 | SMOKE-OVERDUE-003 | Happy Path | `[冒烟: API]` | ~30s |
| 6 | SMOKE-OVERDUE-004 | Happy Path | `[冒烟: API]` | ~60s |
| 7 | SMOKE-OVERDUE-005 | Happy Path | browser-use | ~90s |

---

## 执行清单（状态记录入口）

> **操作说明**：
> - **人工**：鼠标点击 `- [ ]` 切换为 `- [x]` 表示**执行通过**；失败/阻塞/跳过**不勾选**，行尾追加 ` · ❌ BUG-{id}` / ` · 🚫 {原因}` / ` · ⏭ {原因}`
> - **AI（test-execution / api-test-execution）**：执行完成后自动勾选并追加 ` · ✅ AI {日期} · [报告](...)` 或 ` · ❌ AI {日期} · [失败详情](...)`
> - **真源定位**：本清单为**进度真源**；完整执行证据（步骤/断言/截图/堆栈）在 `execution/execution_report_*.md`

- [ ] **SMOKE-OVERDUE-001** 导入无归属视频 → 异步完成 → 列表出现新记录
- [ ] **SMOKE-OVERDUE-EX-001** 导入幂等拦截 — 同月份重复导入被拒绝
- [ ] **SMOKE-OVERDUE-002** 批量拆分 → 记录进入已拆分Tab
- [ ] **SMOKE-OVERDUE-EX-002** 拆分幂等拦截 — 已存在未结算子集时拒绝
- [ ] **SMOKE-OVERDUE-003** [冒烟: API] MQ 登记同步 → status 0→1 + 字段同步
- [ ] **SMOKE-OVERDUE-004** [冒烟: API] MQ 登记同步 → status 0→3（跨期正常未拆分）
- [ ] **SMOKE-OVERDUE-005** 跨期正常未拆分 Tab → 批量拆分 → 已拆分（原状态=跨期正常）

---

## 数据准备（全套件共用）

> 在执行冒烟用例前，通过 API 调用准备以下数据。预计 ~2 分钟。

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 通过 SSO API 登录获取 token（POST `/sso/doLogin`） | 返回 token 非空 |
| 2 | 准备导入 Excel 文件（含 3 条有效 videoId），上传至 OSS | OSS 返回 fileKey |
| 3 | 确保 `yt_month_channel_revenue_source` 中存在对应 videoId 的收益数据（month = 到账月份-1） | 数据库查询返回 ≥1 条 |
| 4 | 确保 `video_composition_overdue` 中存在 status=1 的记录（供拆分用例使用） | 数据库查询返回 ≥1 条 |
| 5 | 确保对应冲销报表父行存在且 received_status ≠ 0 | 数据库查询确认 |
| 6 | 确保 `video_composition_overdue` 中存在 status=0 且 published_date 满足「当前日期 ≤ 发布次月28日」的记录（供 004 验证 0→3） | 数据库查询返回 ≥1 条 |
| 7 | 确保 `video_composition_overdue` 中存在 status=3 的记录（供 005 验证跨期正常拆分；或依赖 004 执行后产生） | 数据库查询返回 ≥1 条 |

---

## Happy Path 用例

### SMOKE-OVERDUE-001 导入无归属视频 → 异步完成 → 列表出现新记录

**优先级**：P0
**用例类型**：冒烟测试
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 导入功能
**关联需求**：PRD V4.5 §SET-03
**关联PRJ用例**：TP-S03-001, TP-S03-032
**预计执行时间**：< 2 分钟

**前置条件**：
1. [登录态] 使用账号 15057199668 通过 SSO 登录结算系统，确认进入应用中心
2. [页面定位] 导航到「逾期结算处理」页面，确认看到 Tab 栏
3. [数据准备: API] Excel 文件已上传 OSS，含 3 条有效 videoId [验证: OSS fileKey 非空]

**测试步骤与预期结果**：

| 阶段 | 步骤 | 操作 | 预期结果 | 验证级别 |
|------|------|------|---------|---------|
| 阶段一：打开导入弹窗 | 1 | 点击「未登记」Tab | 「未登记」Tab 高亮，列表区域刷新并出现数据（或空状态提示） | L2 |
| | 2 | 点击「导入」按钮 | 弹窗出现，标题为"导入未登记视频"，包含"到账月份"输入框和"上传文件"区域 | L1 |
| 阶段二：填写并提交 | 3 | 点击「到账月份」输入框，选择当前测试月份 | 月份选择器关闭，输入框显示选中的月份 | L2 |
| | 4 | 上传已准备的 Excel 文件 | 文件名显示在上传区域 | L2 |
| | 5 | 点击「确认」按钮 | 弹窗消失，回到「未登记」Tab 列表页 | L1 |
| 阶段三：等待异步完成 | 6 | 等待右侧导入状态组件出现绿色对勾图标和"已同步"文字（超时上限 60 秒） | 导入状态区域显示绿色对勾 + "已同步"文字 | L1 |
| 阶段四：验证结果 | 7 | 输入导入的 videoId 到「视频ID」搜索框，点击搜索 | 列表中出现该 videoId 对应的记录，「收益($)」列显示非零数值 | L1 |

**预期结果汇总**：
- L1 强验证：
  1. 导入弹窗出现且包含必要输入项（步骤 2）
  2. 确认后弹窗消失，回到列表页（步骤 5）
  3. 导入状态区域出现绿色对勾 + "已同步"文字（步骤 6）
  4. 搜索导入的 videoId 在列表中可见，收益非零（步骤 7）
- L2 软验证：
  1. Tab 切换后列表区域刷新（步骤 1）
  2. 月份选择成功（步骤 3）
  3. 文件名显示在上传区域（步骤 4）

**是否需要人工介入**：否
**异步等待规则**：步骤 5 超过 60 秒未变为"已同步" → 标记 `⚠️ 环境性能异常`，不计为冒烟失败
**备注**：关联测试点 TP-S03-001, TP-S03-032

---

### SMOKE-OVERDUE-002 批量拆分 → 记录进入已拆分Tab

**优先级**：P0
**用例类型**：冒烟测试
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 批量拆分功能
**关联需求**：PRD V4.5 §SET-02
**关联PRJ用例**：TP-S02-004, TP-S02-029
**预计执行时间**：< 2 分钟

**前置条件**：
1. [登录态] 使用账号 15057199668 通过 SSO 登录结算系统（URL: http://172.16.24.200:7778/ssoLogin），确认进入应用中心
2. [页面定位] 导航到「逾期结算处理」页面（从应用中心进入结算系统 → 左侧菜单「分销商 → 逾期结算处理」）
3. [数据准备: API] `video_composition_overdue` 中存在 status=1 的记录，且对应冲销表父行已到账 [验证: 点击「逾期登记未拆分」Tab，列表中出现至少 1 条记录]

**测试步骤与预期结果**：

| 阶段 | 步骤 | 操作 | 预期结果 | 验证级别 |
|------|------|------|---------|---------|
| 阶段一：定位记录 | 1 | 点击「逾期登记未拆分」Tab | 「逾期登记未拆分」Tab 高亮，列表区域显示至少 1 条记录 | L1 |
| 阶段二：执行拆分 | 2 | 勾选列表中第 1 条记录的勾选框 | 勾选框变为选中状态 | L2 |
| | 3 | 点击「批量拆分」按钮 | 弹出确认弹窗，包含「确认」和「取消」按钮 | L1 |
| | 4 | 点击弹窗中的「确认」按钮 | 页面出现"操作成功"Toast 提示，弹窗消失，列表刷新后被拆分记录不再出现 | L1 |
| 阶段三：验证结果 | 5 | 点击「已拆分」Tab | 「已拆分」Tab 列表中出现刚才被拆分的记录 | L1 |
| | 6 | 查看该记录的「原状态」列 | 原状态列显示"逾期登记未拆分"（默认文字色） | L1 |

**预期结果汇总**：
- L1 强验证：
  1. 逾期登记未拆分 Tab 有可用记录
  2. 确认弹窗出现
  3. 拆分执行成功（操作成功提示 + 记录消失）
  4. 已拆分 Tab 出现被拆分的记录
  5. 原状态列显示"逾期登记未拆分"（**[V4.5 补充]**）
- L2 软验证：
  1. 勾选框交互正常

**是否需要人工介入**：否
**备注**：关联测试点 TP-S02-004, TP-S02-029。**[V4.5 补充]** 步骤6 验证 originalStatus=1 正确记录并展示。

---

### SMOKE-OVERDUE-003 [冒烟: API] MQ 登记同步 → status 0→1 + 字段同步

**优先级**：P0
**用例维度**：正向（Happy Path）
**用例类型**：冒烟测试
**执行方式**：[冒烟: API]（由 api-test-execution 执行，非 browser-use）
**生成方式**：由 `/api-test-case-design` Skill 生成（非模板五手写）
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 剧老板登记同步
**关联接口**：[触发: MQ] RocketMQ tag=`distribution-video-composition` → [验证: HTTP] POST `/videoCompositionOverdue/page`
**关联需求**：PRD V4.5 §SET-01
**关联PRJ用例**：TP-S01-002, TP-S01-013
**依赖用例**：无
**预计执行时间**：< 1 分钟（含 MQ 等待 30s）

**前置条件**：
1. [认证] 调用 `POST http://172.16.24.200:8011/sso/doLogin`，参数 `name=15057199668, pwd={验证码}`，获取 Token
   [验证: 响应中 token 字段非空]
   {记录为:token}
2. [数据准备: API] 确认 `video_composition_overdue` 中存在 status=0 的记录
   [验证: DB-Query] `SELECT video_id, channel_id, receipted_month FROM video_composition_overdue WHERE status = 0 AND deleted = 0 LIMIT 1` 返回 ≥1 条
   {记录为:testVideoId} = 查询结果的 video_id
   {记录为:testChannelId} = 查询结果的 channel_id
   {记录为:testMonth} = 查询结果的 receipted_month
3. [数据准备: API] 记录同步前字段基线
   [验证: DB-Query] `SELECT pipeline_id, sign_channel_name, team_name FROM video_composition_overdue WHERE video_id = '{引用:testVideoId}' AND status = 0 AND deleted = 0`
   {记录为:beforePipelineId} = pipeline_id（预期为空或旧值）

**Step 1 — 触发 MQ 同步**：

> ⚠️ 本步骤的触发方式是 RocketMQ 消息，非直接 HTTP 调用。api-test-execution 执行时需选择以下方式之一：
> - **方式 A（推荐）**：在剧老板系统（`http://distribute.test.xiaowutw.com`）中，使用主分销商账号（Yancz-cool@outlook.com）对 {引用:testVideoId} 执行「视频登记」操作，登记类型选择「逾期登记」，触发 MQ 消息自动发送
> - **方式 B（备选）**：通过 RocketMQ 管理控制台向 topic 发送 tag=`distribution-video-composition` 的测试消息

- **MQ 消息体格式**：
  ```json
  {
    "videoCompositions": "[{\"videoId\":\"{引用:testVideoId}\",\"channelId\":\"{引用:testChannelId}\",\"relatedType\":\"OVERDUE\",\"pipelineId\":\"test-pipeline-001\",\"compositionName\":\"测试子集\",\"teamId\":\"1988839584685428736\",\"teamName\":\"HELLO BEAR\",\"publishedDate\":\"2026-01-15\",\"relatedAt\":\"2026-04-15 10:00:00\"}]"
  }
  > **[V4.5 注]**：消息体中 `relatedType` 字段保留但系统不再以此过滤。技术文档 §2.1.1 已移除 relatedType 过滤条件，对所有已登记视频统一执行逾期判定。此字段值不影响测试结果。

**Step 2 — 等待 MQ 消费完成**：

等待 30 秒（MQ 异步消费 + 事务提交）。超时上限 60 秒。

**Step 3 — HTTP 验证状态变更**：

- **Method**：POST
- **URL**：`http://172.16.24.200:8024/videoCompositionOverdue/page`
- **Headers**：
  ```json
  {
    "accessToken": "{引用:token}",
    "Content-Type": "application/json"
  }
  ```
- **Request Body**：
  ```json
  {
    "page": 1,
    "pageSize": 10,
    "videoId": "{引用:testVideoId}",
    "status": 1
  }
  ```

**Expected Response**：
```json
{
  "code": 0,
  "data": {
    "records": [
      {
        "videoId": "{引用:testVideoId}",
        "status": 1,
        "pipelineId": "{非空}",
        "signChannelName": "{非空}",
        "teamName": "{非空}"
      }
    ],
    "total": "{≥1}"
  }
}
```

**预期结果**：
1. HTTP 状态码：200（L1）
2. [断言: 响应体] `code` = 0（L1）
3. [断言: 响应体] `data.records` 数组长度 ≥ 1（L1）— 该 videoId 的 status=1 记录存在
4. [断言: 响应体] `data.records[0].videoId` = "{引用:testVideoId}"（L1）
5. [断言: 响应体] `data.records[0].status` = 1（L1）— 状态已从 0 更新为 1（逾期登记未拆分）
6. [断言: 响应体] `data.records[0].pipelineId` 非空（L1）— 发布通道ID已同步
7. [断言: 响应体] `data.records[0].signChannelName` 非空（L1）— 子集名称已同步
8. [断言: 响应体] `data.records[0].teamName` 非空（L1）— 分销商名称已同步
9. [断言: DB-Query] `SELECT COUNT(*) FROM video_composition_overdue WHERE video_id = '{引用:testVideoId}' AND status = 0 AND deleted = 0` → count = 0（L1）— 原 status=0 记录已不存在
10. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id = '{引用:testVideoId}' AND status = 1 AND deleted = 0 LIMIT 1` → video_tag 值符合 scrapedAt 判定逻辑（1=技术漏爬 或 NULL=非漏爬）（L2）— **[V4.5 补充]** videoTag 计算验证

**异步等待规则**：Step 2 超过 60 秒后 Step 3 仍查不到 status=1 记录 → 标记 `⚠️ 环境性能异常`（MQ 消费延迟），不计为冒烟失败
**清理步骤**：无（MQ 触发的状态变更为正向业务流转，不可逆且不需要回退）
**是否需要人工介入**：否
**备注**：纯后端逻辑，无 UI 操作入口。关联测试点 TP-S01-002, TP-S01-013

---

### SMOKE-OVERDUE-004 [冒烟: API] MQ 登记同步 → status 0→3（跨期正常未拆分）

> ⚠️ **前提**：status=3（跨期正常未拆分）为 PRD V4.5 新增状态，代码尚未实现（见 §13 Q-01）。本用例在代码上线后方可执行。

**优先级**：P0
**用例维度**：正向（Happy Path）
**用例类型**：冒烟测试
**执行方式**：[冒烟: API]（由 api-test-execution 执行，非 browser-use）
**生成方式**：由 `/api-test-case-design` Skill 生成（非模板五手写）
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 剧老板登记同步（跨期正常路径）
**关联接口**：[触发: MQ] RocketMQ tag=`distribution-video-composition` → [验证: HTTP] POST `/videoCompositionOverdue/page`
**关联需求**：PRD V4.5 §SET-01-01 R2
**关联PRJ用例**：TP-S01-001, TP-S01-004
**依赖用例**：无
**预计执行时间**：< 1 分钟（含 MQ 等待 30s）

**前置条件**：
1. [认证] 调用 `POST http://172.16.24.200:8011/sso/doLogin`，参数 `name=15057199668, pwd={验证码}`，获取 Token
   [验证: 响应中 token 字段非空]
   {记录为:token}
2. [数据准备: API] 确认 `video_composition_overdue` 中存在 status=0 的记录，且该视频的 `published_date` 满足：当前日期 ≤ published_date 次月28日（即登记时未逾期）
   [验证: DB-Query] `SELECT video_id, channel_id, receipted_month, published_date FROM video_composition_overdue WHERE status = 0 AND deleted = 0 AND DATE_ADD(DATE_FORMAT(CONCAT(published_date, '-01'), '%Y-%m-01'), INTERVAL 1 MONTH) + INTERVAL 27 DAY >= CURDATE() LIMIT 1` 返回 ≥1 条
   {记录为:testVideoId} = 查询结果的 video_id
   {记录为:testChannelId} = 查询结果的 channel_id
   {记录为:testPublishedDate} = 查询结果的 published_date

**Step 1 — 触发 MQ 同步（未逾期登记）**：

> ⚠️ 本步骤的触发方式是 RocketMQ 消息，非直接 HTTP 调用。api-test-execution 执行时需选择以下方式之一：
> - **方式 A（推荐）**：在剧老板系统（`http://distribute.test.xiaowutw.com`）中，对 {引用:testVideoId} 执行「视频登记」操作，**确保登记日 ≤ 发布次月28日**
> - **方式 B（备选）**：通过 RocketMQ 管理控制台发送消息

- **MQ 消息体格式**（关键：`relatedAt` 在 `publishedDate` 次月28日之内）：
  ```json
  {
    "videoCompositions": "[{\"videoId\":\"{引用:testVideoId}\",\"channelId\":\"{引用:testChannelId}\",\"relatedType\":\"OVERDUE\",\"pipelineId\":\"test-pipeline-002\",\"compositionName\":\"测试子集-跨期\",\"teamId\":\"1988839584685428736\",\"teamName\":\"HELLO BEAR\",\"publishedDate\":\"{引用:testPublishedDate}\",\"relatedAt\":\"{当月15日，确保≤发布次月28日}\"}]"
  }
  ```
  > **[V4.5 注]**：同 SMOKE-003，`relatedType` 字段保留但系统不再以此过滤，不影响测试结果。

**Step 2 — 等待 MQ 消费完成**：

等待 30 秒。超时上限 60 秒。

**Step 3 — HTTP 验证状态变更为 status=3**：

- **Method**：POST
- **URL**：`http://172.16.24.200:8024/videoCompositionOverdue/page`
- **Headers**：
  ```json
  {
    "accessToken": "{引用:token}",
    "Content-Type": "application/json"
  }
  ```
- **Request Body**：
  ```json
  {
    "page": 1,
    "pageSize": 10,
    "videoId": "{引用:testVideoId}",
    "status": 3
  }
  ```

**Expected Response**：
```json
{
  "code": 0,
  "data": {
    "records": [
      {
        "videoId": "{引用:testVideoId}",
        "status": 3,
        "pipelineId": "{非空}",
        "signChannelName": "{非空}",
        "teamName": "{非空}"
      }
    ],
    "total": "{≥1}"
  }
}
```

**预期结果**：
1. HTTP 状态码：200（L1）
2. [断言: 响应体] `code` = 0（L1）
3. [断言: 响应体] `data.records` 数组长度 ≥ 1（L1）— 该 videoId 的 status=3 记录存在
4. [断言: 响应体] `data.records[0].status` = 3（L1）— 状态为「跨期正常未拆分」（非 status=1）
5. [断言: 响应体] `data.records[0].pipelineId` 非空（L1）— 发布通道ID已同步
6. [断言: 响应体] `data.records[0].signChannelName` 非空（L1）— 子集名称已同步
7. [断言: 响应体] `data.records[0].teamName` 非空（L1）— 分销商名称已同步
8. [断言: DB-Query] `SELECT COUNT(*) FROM video_composition_overdue WHERE video_id = '{引用:testVideoId}' AND status = 0 AND deleted = 0` → count = 0（L1）— 原 status=0 记录已不存在
9. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id = '{引用:testVideoId}' AND status = 3 AND deleted = 0 LIMIT 1` → video_tag 值符合 scrapedAt 判定逻辑（L2）— **[V4.5 补充]** videoTag 计算验证

**异步等待规则**：Step 2 超过 60 秒后 Step 3 仍查不到 status=3 记录 → 标记 `⚠️ 环境性能异常`，不计为冒烟失败
**清理步骤**：无
**是否需要人工介入**：否
**备注**：**本期核心新增路径**。与 SMOKE-OVERDUE-003（status 0→1 逾期）互为对照。关联测试点 TP-S01-001, TP-S01-004

---

### SMOKE-OVERDUE-005 跨期正常未拆分 Tab → 批量拆分 → 已拆分（原状态=跨期正常）

> ⚠️ **前提**：status=3（跨期正常未拆分）及新 Tab 为 PRD V4.5 新增，代码尚未实现。本用例在代码上线后方可执行。

**优先级**：P0
**用例类型**：冒烟测试
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 跨期正常未拆分 Tab 批量拆分
**关联需求**：PRD V4.5 §SET-02-01
**关联PRJ用例**：TP-S02-003, TP-S02-004, TP-S02-007, TP-S02-016
**预计执行时间**：< 2 分钟

**前置条件**：
1. [登录态] 使用账号 15057199668 通过 SSO 登录结算系统（URL: http://172.16.24.200:7778/ssoLogin），确认进入应用中心
2. [页面定位] 导航到「逾期结算处理」页面（从应用中心进入结算系统 → 左侧菜单「分销商 → 逾期结算处理」）
3. [数据准备: API] `video_composition_overdue` 中存在 status=3 的记录，且对应冲销表父行已到账 [验证: 点击「跨期正常未拆分」Tab，列表中出现至少 1 条记录]

**测试步骤与预期结果**：

| 阶段 | 步骤 | 操作 | 预期结果 | 验证级别 |
|------|------|------|---------|---------|
| 阶段一：定位 Tab | 1 | 点击「跨期正常未拆分」Tab | Tab 高亮，列表区域显示至少 1 条记录；右上角注释文案显示"注：此类视频登记时间未超过发布次月28日…" | L1 |
| 阶段二：执行拆分 | 2 | 勾选列表中第 1 条记录的勾选框 | 勾选框变为选中状态 | L2 |
| | 3 | 点击「批量拆分」按钮 | 弹出确认弹窗，包含「确认」和「取消」按钮 | L1 |
| | 4 | 点击弹窗中的「确认」按钮 | 页面出现"操作成功"Toast 提示，弹窗消失，列表刷新后被拆分记录不再出现 | L1 |
| 阶段三：验证结果 | 5 | 点击「已拆分」Tab | 「已拆分」Tab 列表中出现刚才被拆分的记录 | L1 |
| | 6 | 查看该记录的「原状态」列 | 原状态列显示"跨期正常"文字（绿色） | L1 |

**预期结果汇总**：
- L1 强验证：
  1. 跨期正常未拆分 Tab 有可用记录且注释文案正确（步骤 1）
  2. 确认弹窗出现（步骤 3）
  3. 拆分执行成功（操作成功提示 + 记录消失）（步骤 4）
  4. 已拆分 Tab 出现被拆分的记录（步骤 5）
  5. 原状态列显示"跨期正常"（绿色）（步骤 6）
- L2 软验证：
  1. 勾选框交互正常（步骤 2）

**是否需要人工介入**：否
**备注**：**本期核心新增 Tab 和拆分路径**。验证 status=3 → status=2 流转，且 original_status=3 正确记录。与 SMOKE-OVERDUE-002（逾期 Tab 拆分）互为对照。关联测试点 TP-S02-003, TP-S02-004, TP-S02-007, TP-S02-016

---

## 关键异常核心（Critical Exception Core）

### SMOKE-OVERDUE-EX-001 导入幂等拦截 — 同月份重复导入被拒绝

**优先级**：P0
**用例类型**：冒烟测试（关键异常核心）
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 导入功能
**关联需求**：逾期结算处理.md §4.2 任务互斥
**关联PRJ用例**：TP-S03-022
**预计执行时间**：< 30 秒

**前置条件**：
1. [登录态] 使用账号 15057199668 通过 SSO 登录结算系统（URL: http://172.16.24.200:7778/ssoLogin），确认进入应用中心
2. [页面定位] 导航到「逾期结算处理」→「未登记」Tab
3. [数据准备: API] 同月份已有一个 status=0（导入中）的异步导入任务，创建时间 ≤ 30 分钟 [验证: 调用 GET `/videoCompositionOverdue/import/status` 返回 status=0]

**测试步骤与预期结果**：

| 阶段 | 步骤 | 操作 | 预期结果 | 验证级别 |
|------|------|------|---------|---------|
| 触发 | 1 | 点击「导入」按钮，选择同月份，上传 Excel 文件，点击「确认」 | 页面出现错误提示"当前存在导入中的任务，请稍后再试" | L1 |
| 验证无副作用 | 2 | [断言: DB-Query] `SELECT COUNT(*) FROM video_composition_overdue WHERE receipted_month = '{月份}' AND import_task_id = '{新taskId}'` | count = 0（无新数据写入） | L1 |

**是否需要人工介入**：否
**备注**：幂等拦截，防止同月份重复导入导致数据污染。关联测试点 TP-S03-022

---

### SMOKE-OVERDUE-EX-002 拆分幂等拦截 — 已存在未结算子集时拒绝

**优先级**：P0
**用例类型**：冒烟测试（关键异常核心）
**执行环境**：[ENV: TEST]
**所属模块**：逾期结算处理 — 批量拆分功能
**关联需求**：逾期结算处理.md §5.3 checkPipelineIdExist
**关联PRJ用例**：TP-S02-031
**预计执行时间**：< 30 秒

**前置条件**：
1. [登录态] 使用账号 15057199668 通过 SSO 登录结算系统（URL: http://172.16.24.200:7778/ssoLogin），确认进入应用中心
2. [页面定位] 导航到「逾期结算处理」→「逾期登记未拆分」Tab
3. [数据准备: API] 冲销报表中已存在相同 month+cms+pipeline_id 维度的子集行且 settlement_created_status=0 [验证: 数据库查询 `SELECT id FROM yt_reversal_report WHERE month='{m}' AND cms='{cms}' AND pipeline_id='{pid}' AND settlement_created_status=0` 返回 ≥1 条]
4. [数据准备: API] `video_composition_overdue` 中存在 status=1 且 pipelineId 与上述子集行匹配的记录 [验证: 「逾期登记未拆分」Tab 列表中可见对应记录]

**测试步骤与预期结果**：

| 阶段 | 步骤 | 操作 | 预期结果 | 验证级别 |
|------|------|------|---------|---------|
| 触发 | 1 | 在「逾期登记未拆分」Tab 勾选对应记录，点击「批量拆分」→「确认」 | 系统提示"该子集已存在未生成结算单的数据，不允许重复拆分" | L1 |
| 验证无副作用 | 2 | 刷新「逾期登记未拆分」Tab | 被勾选的记录仍在列表中，status 未变（仍为 1） | L1 |

**是否需要人工介入**：否
**备注**：幂等拦截，防止冲销表子集重复拆分。关联测试点 TP-S02-031

---

## 统计摘要

| 指标 | 值 |
|------|-----|
| 总用例数 | 7 |
| Happy Path | 5（SMOKE-OVERDUE-001/002/003/004/005） |
| 关键异常核心 | 2（SMOKE-OVERDUE-EX-001/002） |
| `[冒烟: API]` 用例 | 2（SMOKE-OVERDUE-003/004） |
| `[AI+人工]` 用例 | 0 |
| `[人工]` 用例 | 0 |
| L1 强验证占比（Happy Path） | 30/35 = 86% ✅（browser-use 13/18 + API 17/17） |
| 关键异常核心断言全为 L1 | ✅（4/4） |
| 总步骤数 | 28 步（browser-use 18 + API 6 + 关键异常核心 4） |
| 预估执行时间 | ~5.5 min ✅（< 8 min 含数据准备） |
| 预估全流程时间 | ~8 min ✅（= 8 min 上限） |
| ⚠️ 待代码实现 | SMOKE-OVERDUE-004/005 依赖 status=3 代码上线 |

### 开发自测说明

本冒烟套件可作为开发提测前的自测依据：
- **Happy Path 5 条**：验证导入→拆分→MQ同步（逾期+跨期正常）→跨期正常Tab拆分的核心链路畅通
- **关键异常核心 2 条**：验证幂等拦截屏障有效（导入互斥 + 子集重复拆分拦截）
- ⚠️ SMOKE-OVERDUE-004/005 需 status=3 代码上线后方可执行
- 自测时需逐条执行并截图，截图作为提测门禁的开发自测证明

---

## 人工校验提示

> AI 已完成用例生成，请测试工程师按以下步骤完成人工校验，再提交/执行用例。

**校验步骤**：
1. 使用 `references/human-review-checklist.md` 中的清单逐项检查
2. 将发现的问题汇总后反馈给 AI，要求批量修改
3. 修改完成后，重新执行第1步（仅检查修改涉及的关项）
4. 全部项通过后，在清单底部填写"校验结论"并签名

**高风险项提示**（优先检查）：
- SMOKE-OVERDUE-003 的 MQ 消息体格式是否与实际一致
- SMOKE-OVERDUE-EX-001/002 的数据准备前置条件是否在测试环境可构造
- 异步等待超时（60s）是否需要根据环境调整

---

*冒烟套件 | test-case-design Mode D v4.0*
