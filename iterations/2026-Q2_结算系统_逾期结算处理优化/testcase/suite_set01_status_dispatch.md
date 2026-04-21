# SET-01 登记状态分发 测试用例

> **关联需求**：PRD V4.5 §SET-01-01
> **生成日期**：2026-04-16
> **生成模式**：Mode A（标准）
> **测试点覆盖基准**：test-points.md v2（TP-S01-001~015）
> **执行方式**：全部 `[执行方式: AI]`，API 触发 + API/DB 验证

---

## 系统注册表

| 系统标识 | 系统名称 | 测试环境 API Base | 认证方式 | 认证获取 | 说明 |
|---------|---------|------------------|---------|---------|------|
| SYS-A | 剧老板（分销商端） | `http://distribute.test.xiaowutw.com` | JWT (`accessToken` Header) | 剧老板登录接口获取 token（账号见 `credentials.md` §3.2） | 视频登记触发方 |
| SYS-B | 结算系统 | `http://172.16.24.200:{port}` | Sa-Token (`accessToken` Header) | SSO 接口 `POST http://172.16.24.200:8011/sso/doLogin`（账号见 `credentials.md` §3.1） | 状态分发处理方 |

**认证准备**（所有用例共享，执行前一次性完成）：

```
1. [SYS-A] 获取剧老板 accessToken：
   账号：Yancz-cool@outlook.com（主分销商，team_id=1988839584685428736）
   → 登录后提取 token → 设为变量 {剧老板Token}

2. [SYS-B] 获取结算系统 accessToken：
   POST http://172.16.24.200:8011/sso/doLogin
   参数：name=15057199668, pwd={见 credentials.md §3.1}
   → 响应中提取 token → 设为变量 {结算Token}
```

---

## 公共数据准备说明

SET-01 测试需要在两个系统中准备关联数据：

| 步骤 | 系统 | 操作 | 说明 |
|------|------|------|------|
| ① | SYS-A 剧老板 | 查询未登记视频列表 | `POST /appApi/videoComposition/pageList`，`related=2`，获取可登记视频 |
| ② | SYS-B 结算系统 DB | 确认/插入 `video_composition_overdue` 记录 | `status=0`，指定 `video_id` 和 `published_date` |
| ③ | SYS-A 剧老板 | 查询该视频的登记所需参数 | 从 pageList 响应中提取 `id`、`compositionId`、`amsCompositionId`、`servicePackageCode` 等 |

> **注意**：剧老板 bind API 需要 `compositionId`、`amsCompositionId` 等作品关联参数。测试前需确认测试环境中已有可关联的作品数据，或由开发提供测试用作品 ID。

---

## 用例依赖关系

```
所有用例独立执行，无依赖链。
```

---

## 执行顺序

| 序号 | 用例编号 | 用例名称 | 优先级 | 依赖 | ENV |
|------|---------|---------|-------|------|-----|
| 1 | OVERDUE-S01-001 | 跨期正常分发 0→3 | P0 | 无 | TEST |
| 2 | OVERDUE-S01-002 | 逾期登记分发 0→1 | P0 | 无 | TEST |
| 3 | OVERDUE-S01-003 | 跨系统 E2E 联动 | P0 | 无 | TEST |
| 4 | OVERDUE-S01-004 | 多月份记录批量分发 | P1 | 无 | TEST |
| 5 | OVERDUE-S01-005 | 边界值：恰好第28日 | P1 | 无 | TEST |
| 6 | OVERDUE-S01-006 | 边界值：恰好第29日 | P1 | 无 | TEST |
| 7 | OVERDUE-S01-007 | 时间精度：28日 23:59:59 | P1 | 无 | TEST |
| 8 | OVERDUE-S01-008 | 时间精度：29日 00:00:00 | P1 | 无 | TEST |
| 9 | OVERDUE-S01-009 | 无匹配记录 | P1 | 无 | TEST |
| 10 | OVERDUE-S01-010 | DB 写入失败 | P1 | 无 | TEST |
| 11 | OVERDUE-S01-011 | 并发登记同一视频 | P1 | 无 | TEST |
| 12 | OVERDUE-S01-013 | 重复登记幂等 | P1 | 无 | TEST |
| 13 | OVERDUE-S01-014 | videoTag 计算验证（技术漏爬） | P1 | 无 | TEST |
| 14 | OVERDUE-S01-015 | videoTag 边界值（恰好=截止时间） | P1 | 无 | TEST |
| 15 | OVERDUE-S01-016 | videoTag 双表一致性 | P1 | 014执行后 | TEST |
| 16 | OVERDUE-S01-017 | 并发批量拆分竞态 | P1 | 无 | TEST |
| — | ~~OVERDUE-S01-012~~ | ~~查询范围覆盖~~ | ~~暂缓~~ | — | — |

---

## 执行清单（状态记录入口）

> **操作说明**：
> - **人工**：鼠标点击 `- [ ]` 切换为 `- [x]` 表示**执行通过**；失败/阻塞/跳过**不勾选**，行尾追加 ` · ❌ BUG-{id}` / ` · 🚫 {原因}` / ` · ⏭ {原因}`
> - **AI（test-execution / api-test-execution）**：执行完成后自动勾选并追加 ` · ✅ AI {日期} · [报告](...)` 或 ` · ❌ AI {日期} · [失败详情](...)`
> - **真源定位**：本清单为**进度真源**；完整执行证据（步骤/断言/截图/堆栈）在 `execution/execution_report_*.md`

**① 正向分发**：

- [ ] **OVERDUE-S01-001** 跨期正常分发：登记日≤次月28日 → status=3（P0）
- [ ] **OVERDUE-S01-002** 逾期登记分发：登记日>次月28日 → status=1（P0）
- [ ] **OVERDUE-S01-003** 跨系统 E2E 联动：剧老板登记 → MQ → 结算系统状态变更（P0）
- [ ] **OVERDUE-S01-004** 多月份记录批量分发：同视频多月份逐条独立判定（P1）

**② 边界值与时间精度**：

- [ ] **OVERDUE-S01-005** 边界值：登记日恰好等于发布次月第28日 → status=3（P1）
- [ ] **OVERDUE-S01-006** 边界值：登记日恰好等于发布次月第29日 → status=1（P1）
- [ ] **OVERDUE-S01-007** 时间精度：28日 23:59:59 → status=3（未逾期）（P1）
- [ ] **OVERDUE-S01-008** 时间精度：29日 00:00:00 → status=1（逾期）（P1）

**③ 异常与降级**：

- [ ] **OVERDUE-S01-009** 无匹配记录：结算系统无该视频 status=0 记录 → 登记正常完成（P1）
- [ ] **OVERDUE-S01-010** DB 写入失败 → 登记成功 + 后台异常日志（P1）

**④ 并发与幂等**：

- [ ] **OVERDUE-S01-011** 并发登记同一视频 → 第二个请求被拦截（P1）
- [ ] **OVERDUE-S01-013** 重复登记幂等：status=1 记录收到重复 MQ → 仅同步字段不改状态（P1）
- [ ] **OVERDUE-S01-017** 并发批量拆分：两个会话同时拆分同维度记录（P1）

**⑤ videoTag（技术漏爬）**：

- [ ] **OVERDUE-S01-014** videoTag 计算验证：scrapedAt > 发布次月15日 → videoTag=1（P1）
- [ ] **OVERDUE-S01-015** videoTag 边界值：scrapedAt = 发布次月15日 23:59:59 → videoTag=null（P1）
- [ ] **OVERDUE-S01-016** videoTag 双表一致性：MQ 同步后两表 videoTag 一致（P1）

**暂缓**：~~OVERDUE-S01-012~~（设计阶段暂缓，不执行）

---

## P0 用例

---

### OVERDUE-S01-001 跨期正常分发：登记日≤次月28日 → status=3

**优先级**：P0
**用例类型**：功能测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R2、AC2
**关联测试点**：TP-S01-001（P0 PF）、TP-S01-011（P0 SM）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A 剧老板 accessToken 已获取（见公共认证准备）
2. [认证] SYS-B 结算系统 accessToken 已获取（见公共认证准备）
3. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条记录：
   - `video_id` = `{测试视频ID_001}`
   - `status` = 0（未登记）
   - `published_date` 设为**上月1日**（例：若当前 2026-04，则设为 `2026-03-01`）
   - 确保该视频发布次月28日 > 今天（即今天登记不逾期）
   [验证: `SELECT id, status, published_date FROM video_composition_overdue WHERE video_id='{测试视频ID_001}' AND status=0` 返回 1 条记录]
4. [数据准备: 环境预置] SYS-A 剧老板中该视频处于未登记状态（`related=2`），且已有可关联的作品数据
   [验证: `POST /appApi/videoComposition/pageList` 以 `videoId={测试视频ID_001}`, `related=2` 查询返回 `total ≥ 1`]

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_001}` | 从剧老板未登记列表中选取 |
| published_date | 上月1日 | 使次月28日 > 今天 → 登记时不逾期 |
| team_id | `1988839584685428736` | 主分销商 HELLO BEAR |

**测试步骤**：
1. [SYS-A] 调用剧老板视频登记接口触发登记
   ```
   POST http://distribute.test.xiaowutw.com/appApi/videoComposition/bind
   Headers: accessToken: {剧老板Token}, Content-Type: application/json
   Body: {
     "id": {视频记录ID},
     "videoId": "{测试视频ID_001}",
     "compositionId": {作品ID},
     "amsCompositionId": {AMS作品ID},
     "compositionName": "{作品名称}",
     "compositionServicePackageId": {运作模式ID},
     "servicePackageCode": "{运作模式CODE}",
     "servicePackageName": "{运作模式名称}",
     "channelId": "{频道ID}",
     "changeRelated": "2"
   }
   ```
2. 等待 MQ 消费完成（轮询结算系统 API，等待目标记录 status ≠ 0，最多 30 秒，每 5 秒查询一次）
3. [SYS-B] 调用结算系统列表查询接口验证状态
   ```
   POST {结算系统API}/videoCompositionOverdue/page
   Headers: accessToken: {结算Token}, Content-Type: application/json
   Body: {"videoId": "{测试视频ID_001}", "status": 3, "page": 1, "pageSize": 10}
   ```

**预期结果**：
1. [断言: API] SYS-A 剧老板 bind 接口返回 `code=0`，登记操作成功（L1）
2. [断言: API] SYS-B 结算系统 `/videoCompositionOverdue/page` 以 `status=3` 查询，`data.total ≥ 1`，`data.records` 中包含 `videoId={测试视频ID_001}` 的记录（L1）
   接口地址：`/videoCompositionOverdue/page`
   请求参数：`{"videoId": "{测试视频ID_001}", "status": 3}`
   预期响应：`data.total ≥ 1`
   比对字段：`data.records[].videoId`（精确匹配 `{测试视频ID_001}`）
3. [断言: DB-Query] `SELECT status, registration_time FROM video_composition_overdue WHERE video_id='{测试视频ID_001}' ORDER BY id DESC LIMIT 1` 返回 `status=3`，`registration_time` 不为空且在当前时间 ±5 分钟内（L1）
   比对字段：`status`=3（精确匹配）
4. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id='{测试视频ID_001}' AND status=3 ORDER BY id DESC LIMIT 1` → video_tag 值符合 scrapedAt 判定逻辑（L2）— **[V4.5 补充]** videoTag 计算验证

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-001

**是否需要人工介入**：否
**备注**：V4.5 新增核心路径。状态机验证（TP-S01-011）合并为预期结果第 3 条 DB 断言。

---

### OVERDUE-S01-002 逾期登记分发：登记日>次月28日 → status=1

**优先级**：P0
**用例类型**：功能测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R1、AC1
**关联测试点**：TP-S01-002（P0 PF）、TP-S01-012（P0 SM）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条记录：
   - `video_id` = `{测试视频ID_002}`
   - `status` = 0（未登记）
   - `published_date` 设为 **6 个月前的1日**（例：若当前 2026-04，则设为 `2025-10-01`）
   - 确保该视频发布次月28日 << 今天（即今天登记必定逾期）
   [验证: `SELECT id, status, published_date FROM video_composition_overdue WHERE video_id='{测试视频ID_002}' AND status=0` 返回 1 条记录]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频处于未登记状态（`related=2`）
   [验证: `POST /appApi/videoComposition/pageList` 以 `videoId={测试视频ID_002}`, `related=2` 查询返回 `total ≥ 1`]

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_002}` | 从剧老板未登记列表中选取 |
| published_date | 6 个月前的 1 日 | 使次月28日远早于今天 → 登记时必定逾期 |

**测试步骤**：
1. [SYS-A] 调用剧老板 `POST /appApi/videoComposition/bind`，参数同 OVERDUE-S01-001（替换为 `{测试视频ID_002}` 对应的字段）
2. 等待 MQ 消费完成（轮询结算系统 API，等待目标记录 status ≠ 0，最多 30 秒）
3. [SYS-B] 调用结算系统 `POST /videoCompositionOverdue/page`，以 `status=1` + `videoId={测试视频ID_002}` 查询

**预期结果**：
1. [断言: API] SYS-A bind 接口返回 `code=0`（L1）
2. [断言: API] SYS-B `/videoCompositionOverdue/page` 以 `status=1` 查询，`data.records` 中包含 `videoId={测试视频ID_002}`（L1）
   比对字段：`data.records[].videoId`（精确匹配）
3. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_002}' ORDER BY id DESC LIMIT 1` 返回 `status=1`（L1）
4. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id='{测试视频ID_002}' AND status=1 ORDER BY id DESC LIMIT 1` → video_tag 值符合 scrapedAt 判定逻辑（L2）— **[V4.5 补充]** videoTag 计算验证

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-002

**是否需要人工介入**：否
**备注**：回归验证，确认原有 0→1 路径不受 V4.5 新增 status=3 影响。状态机验证（TP-S01-012）合并为预期结果第 3 条。

---

### OVERDUE-S01-003 跨系统 E2E 联动：剧老板登记 → MQ → 结算系统状态变更

**优先级**：P0
**用例类型**：功能测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01（跨系统路径）
**关联测试点**：TP-S01-013（P0 IN）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条 `status=0` 记录，`video_id` = `{测试视频ID_003}`，`published_date` = 上月1日（不逾期）
   [验证: DB 查询确认记录存在]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频处于未登记状态
   [验证: pageList API 确认 `related=2`]

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_003}` | 两系统中均有对应数据 |
| published_date | 上月1日 | 不逾期，验证 0→3 全链路 |

**测试步骤**：
1. [SYS-B] 调用结算系统 API 确认初始状态
   ```
   POST {结算系统API}/videoCompositionOverdue/page
   Body: {"videoId": "{测试视频ID_003}", "status": 0}
   ```
   记录响应中 `data.total` 值为 `{记录为:初始未登记数}`
2. [SYS-A] 调用剧老板 `POST /appApi/videoComposition/bind` 触发登记
3. 等待 MQ 消费完成（轮询结算系统 API，等待 `status=0` 的 `total` 减少，最多 30 秒）
4. [SYS-B] 调用结算系统 API 验证状态已变更
   ```
   POST {结算系统API}/videoCompositionOverdue/page
   Body: {"videoId": "{测试视频ID_003}", "status": 3}
   ```
5. [SYS-B] 调用结算系统 API 确认原 status=0 记录已减少
   ```
   POST {结算系统API}/videoCompositionOverdue/page
   Body: {"videoId": "{测试视频ID_003}", "status": 0}
   ```

**预期结果**：
1. [断言: API] 步骤 1：`status=0` 查询返回 `data.total ≥ 1`，初始状态确认（L2）
2. [断言: API] 步骤 2：bind 接口返回 `code=0`，剧老板登记成功（L1）
3. [断言: API] 步骤 4：`status=3` 查询返回 `data.total ≥ 1`，`data.records` 中包含 `videoId={测试视频ID_003}`（L1）
   接口地址：`/videoCompositionOverdue/page`
   请求参数：`{"videoId": "{测试视频ID_003}", "status": 3}`
   比对字段：`data.records[].videoId`（精确匹配）
4. [断言: API] 步骤 5：`status=0` 查询的 `data.total` < `{引用:初始未登记数}`，确认记录已从未登记状态流出（L1）
5. [断言: DB-Query] `SELECT status, registration_time, pipeline_id, sign_channel_id FROM video_composition_overdue WHERE video_id='{测试视频ID_003}' ORDER BY id DESC LIMIT 1` 返回 `status=3`，`registration_time` 不为空，`pipeline_id` 不为空，`sign_channel_id` 不为空（L1）
   比对字段：`status`=3，`registration_time` IS NOT NULL，`pipeline_id` IS NOT NULL
6. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id='{测试视频ID_003}' AND status=3 ORDER BY id DESC LIMIT 1` → video_tag 值符合 scrapedAt 判定逻辑（L2）— **[V4.5 补充]** videoTag 计算验证

[输出: 测试视频ID_003_结果status = DB 查询返回的 status 值]

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-003

**是否需要人工介入**：否
**备注**：E2E 验证重点：①剧老板 API 调用成功 → ②MQ 消息发出并被结算系统消费 → ③结算系统状态正确变更 + 字段同步。本用例额外验证 `pipeline_id`、`sign_channel_id` 等字段同步（代码逆向文档 §2 确认 synVideoComposition 会同步这些字段）。

---

## P1 用例

---

### OVERDUE-S01-004 多月份记录批量分发：同视频多月份逐条独立判定

**优先级**：P1
**用例类型**：功能测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 AC4
**关联测试点**：TP-S01-003（P0 PF）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中为同一视频插入 **2 条** `status=0` 记录：
   - 记录 A：`video_id` = `{测试视频ID_004}`，`receipted_month` = `2026-03`，`published_date` = `2026-03-01`（次月28日=2026-04-28 > 今天 → 不逾期）
   - 记录 B：`video_id` = `{测试视频ID_004}`，`receipted_month` = `2025-11`，`published_date` = `2025-11-01`（次月28日=2025-12-28 << 今天 → 逾期）
   [验证: `SELECT id, receipted_month, status FROM video_composition_overdue WHERE video_id='{测试视频ID_004}' AND status=0` 返回 2 条记录]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频为未登记状态
   [验证: pageList API 确认]

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_004}` | 两系统中有对应数据 |
| 记录 A receipted_month | `2026-03` | 近期月份 → 不逾期 |
| 记录 B receipted_month | `2025-11` | 远期月份 → 逾期 |

**测试步骤**：
1. [SYS-A] 调用剧老板 `POST /appApi/videoComposition/bind` 触发登记
2. 等待 MQ 消费完成（轮询结算系统 DB，等待该视频所有 status=0 记录均已变更，最多 30 秒）
3. [SYS-B] 分别查询 status=1 和 status=3 的记录

**预期结果**：
1. [断言: API] bind 接口返回 `code=0`（L1）
2. [断言: DB-Query] `SELECT receipted_month, status FROM video_composition_overdue WHERE video_id='{测试视频ID_004}' AND status=3` 返回包含 `receipted_month=2026-03` 的记录（不逾期 → status=3）（L1）
   比对字段：`receipted_month`=`2026-03`，`status`=3
3. [断言: DB-Query] `SELECT receipted_month, status FROM video_composition_overdue WHERE video_id='{测试视频ID_004}' AND status=1` 返回包含 `receipted_month=2025-11` 的记录（逾期 → status=1）（L1）
   比对字段：`receipted_month`=`2025-11`，`status`=1
4. [断言: DB-Query] `SELECT COUNT(*) FROM video_composition_overdue WHERE video_id='{测试视频ID_004}' AND status=0` 返回 0（无遗漏未处理记录）（L1）

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-004

**是否需要人工介入**：否
**备注**：验证"逐条执行状态分发"：同一视频不同月份的记录根据各自 publishedDate 独立判定逾期与否，结果可以不同（一条 status=3，一条 status=1）。

---

### OVERDUE-S01-005 边界值：登记日恰好等于发布次月第28日 → status=3

**优先级**：P1
**用例类型**：边界值测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R1/R2
**关联测试点**：TP-S01-004（P0 BV）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条 `status=0` 记录：
   - `video_id` = `{测试视频ID_005}`
   - `published_date` 设置为使**发布次月28日 = 今天**的值
   - 计算方式：若今天是 M 月 D 日，且 D=28，则 `published_date` = 上月任意日（如上月1日）；若 D≠28，则本用例需在**每月28日**执行，或使用 DB 回填方案（见备注）
   [验证: DB 查询确认记录存在且 status=0]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频为未登记状态

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_005}` | |
| published_date | 使次月28日=今天 | 边界：登记日 = 次月28日 |

**测试步骤**：
1. [SYS-A] 调用剧老板 `POST /appApi/videoComposition/bind` 触发登记
2. 等待 MQ 消费完成（最多 30 秒）
3. [SYS-B] 查询结算系统验证状态

**预期结果**：
1. [断言: API] bind 返回 `code=0`（L1）
2. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_005}' ORDER BY id DESC LIMIT 1` 返回 `status=3`（L1）
   判定依据：登记日(今天) = 次月28日，满足 R2 条件"≤次月28日"→ 跨期正常

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-005

**是否需要人工介入**：否
**备注**：⚠️ **日期依赖**：本用例要求登记日 = 发布次月28日。有两种执行方式：
- **方式 A**（推荐）：在每月28日执行，publishedDate 设为上月任意日
- **方式 B**（DB 回填）：任意日期执行 bind → 登记完成后立即 `UPDATE registration_time = '{发布次月28日} 12:00:00' WHERE video_id='{测试视频ID_005}'` → 再查 status 验证（此方式绕过了实际判定逻辑，仅验证 DB 层面）

---

### OVERDUE-S01-006 边界值：登记日恰好等于发布次月第29日 → status=1

**优先级**：P1
**用例类型**：边界值测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R1
**关联测试点**：TP-S01-005（P0 BV）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条 `status=0` 记录：
   - `video_id` = `{测试视频ID_006}`
   - `published_date` 设置为使**发布次月28日 = 昨天**的值（即今天=次月29日）
   - 仅当今天是某月29日时完美匹配；否则见备注
   [验证: DB 查询确认记录存在且 status=0]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频为未登记状态

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_006}` | |
| published_date | 使次月29日=今天 | 边界：登记日 = 次月29日 |

**测试步骤**：
1. [SYS-A] 调用剧老板 `POST /appApi/videoComposition/bind` 触发登记
2. 等待 MQ 消费完成（最多 30 秒）
3. [SYS-B] 查询结算系统验证状态

**预期结果**：
1. [断言: API] bind 返回 `code=0`（L1）
2. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_006}' ORDER BY id DESC LIMIT 1` 返回 `status=1`（L1）
   判定依据：登记日(今天) = 次月29日 > 次月28日，满足 R1 条件">次月28日"→ 逾期

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-006

**是否需要人工介入**：否
**备注**：⚠️ **日期依赖**：与 OVERDUE-S01-005 对称。推荐在每月29日执行，或使用 DB 回填 registrationTime 方式验证。

---

### OVERDUE-S01-007 时间精度：28日 23:59:59 → status=3（未逾期）

**优先级**：P1
**用例类型**：边界值测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R1/R2；技术审阅 A-1
**关联测试点**：TP-S01-006（P1 BV）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条 `status=0` 记录：
   - `video_id` = `{测试视频ID_007}`
   - `published_date` = `2025-10-01`（固定值，次月28日=2025-11-28）
   [验证: DB 查询确认记录存在]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频为未登记状态

**测试步骤**（方案 A：DB 回填 + 重新触发 MQ）：
1. [SYS-B DB] 确保 `video_composition_overdue` 中存在 status=0 的记录，将 registrationTime 回填为精确边界值：
   ```sql
   UPDATE video_composition_overdue
   SET status = 0, registration_time = NULL
   WHERE video_id = '{测试视频ID_007}';
   ```
2. [SYS-B DB] 预设 `video_composition` 中该视频的 `related_at` 为精确边界值：
   ```sql
   UPDATE video_composition
   SET related_at = '2025-11-28 23:59:59'
   WHERE video_id = '{测试视频ID_007}';
   ```
   > `related_at` 是 syncOverdueSettlementStatus 中 registrationDate 的来源（COALESCE(changeRelatedAt, relatedAt)）
3. [SYS-A] 调用剧老板 bind 触发登记，产生 MQ 消息，使 syncOverdueSettlementStatus 重新执行判定
4. 等待 MQ 消费完成（最多 30 秒）
5. [SYS-B] 验证状态

**预期结果**：
1. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_007}' ORDER BY id DESC LIMIT 1` 返回 `status=3`（L1）
   判定依据：registrationDate(2025-11-28 23:59:59) ≤ deadline(2025-11-28 23:59:59) → 未逾期 → status=3
   比对字段：`status`=3

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-007

**是否需要人工介入**：否
**备注**：⚠️ **已确认为秒级比较**：代码 `calculateRelatedType()` 中截止时间设为次月28日 **23:59:59**（`Calendar.HOUR_OF_DAY=23, MINUTE=59, SECOND=59`），使用 `Date.after(deadline)` 比较（毫秒精度）。**执行方案 A**：通过 DB 预设 `video_composition.related_at` 为精确边界值，再触发 MQ 消费使 syncOverdueSettlementStatus 基于预设时间重新判定。

---

### OVERDUE-S01-008 时间精度：29日 00:00:00 → status=1（逾期）

**优先级**：P1
**用例类型**：边界值测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R1；技术审阅 A-1
**关联测试点**：TP-S01-007（P1 BV）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条 `status=0` 记录：
   - `video_id` = `{测试视频ID_008}`
   - `published_date` = `2025-10-01`（固定值，次月28日=2025-11-28）
   [验证: DB 查询确认记录存在]

**测试步骤**（方案 A：DB 回填 + 重新触发 MQ）：
1. [SYS-B DB] 确保记录为 status=0，预设 `video_composition` 中该视频的 `related_at` 为精确边界值：
   ```sql
   UPDATE video_composition_overdue
   SET status = 0, registration_time = NULL
   WHERE video_id = '{测试视频ID_008}';
   
   UPDATE video_composition
   SET related_at = '2025-11-29 00:00:00'
   WHERE video_id = '{测试视频ID_008}';
   ```
2. [SYS-A] 调用剧老板 bind 触发登记，产生 MQ 消息重新执行判定
3. 等待 MQ 消费完成（最多 30 秒）
4. [SYS-B] 验证状态

**预期结果**：
1. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_008}' ORDER BY id DESC LIMIT 1` 返回 `status=1`（L1）
   判定依据：registrationDate(2025-11-29 00:00:00) > deadline(2025-11-28 23:59:59) → 逾期 → status=1
   比对字段：`status`=1

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-008

**是否需要人工介入**：否
**备注**：与 OVERDUE-S01-007 对称，验证 29日 00:00:00 已越过边界（`29日 00:00:00.after(28日 23:59:59) = true` → 逾期）。**执行方案 A**：通过 DB 预设 `video_composition.related_at` 为精确边界值，再触发 MQ 重新判定。

---

### OVERDUE-S01-009 无匹配记录：结算系统无该视频 status=0 记录 → 登记正常完成

**优先级**：P1
**用例类型**：异常测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 R3、AC3
**关联测试点**：TP-S01-008（P0 EX）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 确认结算系统 `video_composition_overdue` 表中**不存在**该视频的 `status=0` 记录
   - `video_id` = `{测试视频ID_009}`（选取一个在结算系统无逾期记录的视频）
   [验证: `SELECT COUNT(*) FROM video_composition_overdue WHERE video_id='{测试视频ID_009}' AND status=0` 返回 0]
3. [数据准备: 环境预置] SYS-A 剧老板中该视频为未登记状态
   [验证: pageList API 确认]

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_009}` | 结算系统无对应 overdue 记录 |

**测试步骤**：
1. [SYS-A] 调用剧老板 `POST /appApi/videoComposition/bind` 触发登记
2. 等待 5 秒后查询（验证"无变更"场景无可观测信号，固定等待后确认状态未改变）[L3: 环境等待，不影响用例结论]
3. [SYS-B] 查询结算系统确认无新增记录

**预期结果**：
1. [断言: API] bind 返回 `code=0`，剧老板登记成功（登记本身不受影响）（L1）
2. [断言: DB-Query] `SELECT COUNT(*) FROM video_composition_overdue WHERE video_id='{测试视频ID_009}' AND status IN (1, 3)` 返回 0，无新增状态分发记录（L1）
   比对字段：`COUNT(*)`=0
3. [断言: API] SYS-A 剧老板 `POST /appApi/videoComposition/pageList` 以 `videoId={测试视频ID_009}`, `related=1` 查询返回 `total ≥ 1`，确认视频已登记成功（L2）

**清理步骤**：无（未产生逾期结算数据）

**是否需要人工介入**：否
**备注**：验证 PRD AC3：未找到未登记记录时正常完成登记、不抛异常。

---

### OVERDUE-S01-010 DB 写入失败 → 登记成功 + 后台异常日志

**优先级**：P1
**用例类型**：异常测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 ⑤异常-行1
**关联测试点**：TP-S01-009（P1 EX）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A accessToken 已获取
2. 测试环境结算系统服务正常运行

**测试步骤**：
1. ⚠️ 本用例无法通过常规 API 测试模拟 DB 写入失败。仅记录设计意图。

**预期结果**：
1. [L3 观察性] 当状态分发时 DB 写入失败，分销商端仍应收到"登记成功"响应（登记本身不受影响）
2. [L3 观察性] 结算系统后台应记录异常日志（具体日志格式需查看代码）

**清理步骤**：无

**是否需要人工介入**：否
**备注**：⚠️ **测试环境限制**：无法在不影响其他功能的情况下模拟 DB 故障。建议通过以下替代方式验证：①代码审查确认异常处理逻辑（try-catch 不影响登记响应）；②与开发约定在 staging 环境临时断开 overdue 表写入权限进行一次性验证。本用例标记为 L3 观察性，不计入通过/失败统计。

---

### OVERDUE-S01-011 并发登记同一视频 → 第二个请求被拦截

**优先级**：P1
**用例类型**：异常测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01 ⑤异常-行2
**关联测试点**：TP-S01-010（P1 EX）
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A 获取**同一分销商账号**的 accessToken：
   - Token：Yancz-cool@outlook.com（主分销商，team_id=1988839584685428736）
2. [数据准备: 环境预置] SYS-A 剧老板中目标视频为未登记状态（`related=2`），且属于该分销商可见范围
   [验证: `POST /appApi/videoComposition/pageList` 以 `videoId={测试视频ID_011}`, `related=2` 查询返回 `total ≥ 1`]

> ⚠️ **设计说明**：剧老板分销商端按 team_id 隔离数据，不同分销商不能看到同一视频。因此并发测试使用**同一账号发两次请求**模拟竞态，而非两个不同分销商。

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_011}` | 同一分销商可见的未登记视频 |

**测试步骤**：
1. [SYS-A] 使用同一 Token **近乎同时**发送两个 `POST /appApi/videoComposition/bind` 请求（相同 videoId + 相同参数，间隔 < 1 秒，使用异步并发发送）
2. 记录两个请求的响应

**预期结果**：
1. [断言: API] 两个请求中：恰好一个返回 `code=0`（成功），另一个返回错误码（如"该视频已被登记"）（L1）
   比对规则：两个响应的 `code` 值不完全相同（一成功一失败）
2. [断言: API] 失败的请求响应中包含拒绝原因（`message` 字段包含"已被登记"或"已登记"关键词）（L2）
3. [断言: DB-Query] `SELECT COUNT(*) FROM video_composition_overdue WHERE video_id='{测试视频ID_011}' AND status IN (1, 3)` 返回 ≤ 1（不因并发产生重复状态分发）（L1）
4. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_011}' AND status=0` 返回 0 条（原始 status=0 记录已正常流转，未残留脏数据）（L2）

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-011

**是否需要人工介入**：否
**备注**：测试并发防重机制。剧老板分销商端按 team_id 隔离视频数据，故使用同一账号并发请求模拟竞态。技术审阅 C-7-01 确认存在 TOCTOU 竞态窗口但实际并发概率极低。本用例验证行为基线。

---

### OVERDUE-S01-013 重复登记幂等：status=1 记录收到重复 MQ → 仅同步字段不改状态

**优先级**：P1
**用例类型**：异常测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：PRD V4.5 §SET-01-01；PRD 审阅 S-8
**关联测试点**：TP-S01-015（P1 EX）
**依赖用例**：无
**执行方式**：[执行方式: AI]

> ⚠️ **用例范围说明**：本用例验证的是"完全相同参数的重复登记"（幂等性），不包含"变更登记"场景。
> **重复登记 vs 变更登记的区别**：
> - **重复登记**：相同视频、相同参数再次 bind → 剧老板可能拦截，或 MQ 重发但结算系统幂等处理
> - **变更登记**：已登记视频修改关联信息（换子集/换套餐）→ `changeRelatedAt` 有值 → 按产品选项A，**不重新判定** relatedType，保持首次判定结果（跨期正常一旦判定就不再变更）
> 变更登记属于独立业务场景，如需覆盖应单独设计用例。

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] 结算系统 `video_composition_overdue` 表中存在一条 **status=1**（逾期登记未拆分）的记录：
   - `video_id` = `{测试视频ID_013}`
   - `status` = 1
   [验证: `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_013}' AND status=1` 返回 ≥ 1 条]

> **为什么只测 status=1 不测 status=3**：**[V4.5 更新]** 技术文档 2026041601 版 §2.1.1 步骤3 已将查询条件从 `status IN (0, 1)` 改为 `status = 0`。status=1 和 status=3 的记录均**不会被查出**，幂等性由查询条件直接保证。这同时意味着：若一个已流转的视频（status=1 或 3）做了变更登记，overdue 表的 status 不会被重新计算——**已确认符合产品选项A预期**（跨期正常一旦判定就不再变更，见 Q-10）。

**测试数据**：

| 字段 | 值 | 说明 |
|------|-----|------|
| video_id | `{测试视频ID_013}` | 已完成首次登记 |
| 当前 status | 1 | 逾期登记未拆分 |

**测试步骤**：
1. [SYS-B DB] 记录当前状态快照：
   ```sql
   SELECT status, registration_time, sign_channel_name, team_name
   FROM video_composition_overdue
   WHERE video_id = '{测试视频ID_013}' AND status = 1
   ```
   记录为 `{记录为:原始status}`、`{记录为:原始registration_time}`、`{记录为:原始sign_channel_name}`
2. [SYS-A] 再次调用剧老板 bind 接口（相同视频、相同参数）
   > 剧老板侧可能直接拦截重复登记（视频已 related=1），此时 bind 返回错误，MQ 不会发出——这本身就是正确的幂等行为
3. 等待 5 秒
4. [SYS-B DB] 查询状态是否变化

**预期结果**：
1. [断言: API] 剧老板 bind 返回错误码，message 包含"已登记"或"已关联"（L1）
   — 代码确认：`VideoCompositionBindCmd.java:104-107`，普通登记时 `related=1` → 抛 `VIDEO_ALREADY_RELATED`
2. [断言: 无 MQ] MQ 消息未发出（bind 失败不触发 MQ）（L1）
3. [断言: DB-Query] `SELECT status FROM video_composition_overdue WHERE video_id='{测试视频ID_013}' AND status=1 LIMIT 1` 返回 `status=1`，状态不变（L1）
   比对字段：`status`=1（精确匹配）

**清理步骤**：无（未改变数据状态）

**是否需要人工介入**：否
**备注**：
- ✅ **S-8 已确认**：剧老板 bind 接口已有重复登记拦截（`VideoCompositionBindCmd.java:104-107`），普通登记时 related=1 直接拒绝，MQ 不发出。幂等由剧老板端保证。
- **[V4.5 更新]** 技术文档 2026041601 版 §2.1.1 步骤3 已将查询条件从 `status IN (0, 1)` 改为 `status = 0`。status=1 和 status=3 的记录均不会被查出，幂等性由查询条件直接保证。
- ✅ **Q-10 已确认（2026-04-20）**：status=3 的视频做变更登记后，overdue 表不会更新 — 符合产品选项A预期（跨期正常一旦判定就不再变更，财务按"跨期正常"拆分，不扣违约金）。技术文档有意设计，见 §2.1.1 步骤3 注释。

---

## V4.5 技术审阅补充用例（Mode B）

> 来源：`review/tech-review-summary.md` §二 风险场景 + §2.1.1 videoTag 计算逻辑

---

### OVERDUE-S01-014 videoTag 计算验证：scrapedAt > 发布次月15日 → videoTag=1

**优先级**：P1
**用例类型**：功能测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发 / SET-04 漏抓责任界定
**关联需求**：PRD V4.5 §SET-04-01 R1；技术文档 §2.1.1 步骤5
**风险来源**：技术审阅 — videoTag 为 V4.5 新增，原用例未覆盖
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] `video_composition_overdue` 中存在 `status=0` 记录：
   - `video_id` = `{测试视频ID_VT01}`，`published_date` = `2025-10-01`
   [验证: DB 查询确认]
3. [数据准备: DB] `video_composition` 中该视频 `scraped_at` = `2025-11-20 10:00:00`（> crawlDeadline 2025-11-15 23:59:59）
   [验证: `SELECT scraped_at FROM video_composition WHERE video_id='{测试视频ID_VT01}'`]
4. [数据准备: 环境预置] SYS-A 剧老板中该视频为未登记状态

**测试步骤**：
1. [SYS-A] 调用剧老板 bind 触发登记
2. 等待 MQ 消费完成（最多 30 秒）
3. [SYS-B] 验证 videoTag

**预期结果**：
1. [断言: API] bind 返回 `code=0`（L1）
2. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id='{测试视频ID_VT01}' AND status IN (1,3) ORDER BY id DESC LIMIT 1` → `video_tag=1`（L1）
3. [断言: API] `POST /videoCompositionOverdue/page` 以 `videoId={测试视频ID_VT01}` 查询 → `videoTagName` = "技术漏爬"（L1）

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-014

**是否需要人工介入**：否

---

### OVERDUE-S01-015 videoTag 边界值：scrapedAt = 发布次月15日 23:59:59 → videoTag=null

**优先级**：P1
**用例类型**：边界值测试
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发 / SET-04 漏抓责任界定
**关联需求**：PRD V4.5 §SET-04-01 R2；技术文档 §2.1.1 步骤5
**风险来源**：技术审阅 A-2 建议补充
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-A、SYS-B accessToken 已获取
2. [数据准备: DB] `video_composition_overdue` 中存在 `status=0` 记录：
   - `video_id` = `{测试视频ID_VT02}`，`published_date` = `2025-10-01`
3. [数据准备: DB] `video_composition` 中该视频 `scraped_at` = `2025-11-15 23:59:59`（= crawlDeadline，不满足 > 条件）

**测试步骤**：
1. [SYS-A] 调用剧老板 bind 触发登记
2. 等待 MQ 消费完成（最多 30 秒）
3. [SYS-B] 验证 videoTag

**预期结果**：
1. [断言: API] bind 返回 `code=0`（L1）
2. [断言: DB-Query] `SELECT video_tag FROM video_composition_overdue WHERE video_id='{测试视频ID_VT02}' AND status IN (1,3) ORDER BY id DESC LIMIT 1` → `video_tag IS NULL`（L1）
3. [断言: API] `POST /videoCompositionOverdue/page` 查询 → `videoTag` = null（L1）

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-015

**是否需要人工介入**：否

---

### OVERDUE-S01-016 videoTag 双表一致性：MQ 同步后两表 videoTag 一致

**优先级**：P1
**用例类型**：功能测试（C-10 数据依赖完整性）
**执行环境**：[ENV: TEST]
**所属模块**：SET-01 登记状态分发
**关联需求**：技术文档 §2.1.1 步骤5+8
**风险来源**：技术审阅 R-3
**依赖用例**：OVERDUE-S01-014 执行后（复用数据），或独立准备
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-B 结算系统 accessToken 已获取
2. [数据准备: DB] `video_composition_overdue` 中存在 `video_tag IS NOT NULL` 的记录
   [验证: `SELECT video_id FROM video_composition_overdue WHERE video_tag IS NOT NULL AND deleted=0 LIMIT 5` 返回 ≥1 条]
   {记录为:checkVideoIds}

**测试步骤**：
1. [SYS-B DB] 联表查询两表 videoTag

**预期结果**：
1. [断言: DB-Query] 执行：
   ```sql
   SELECT vco.video_id, vco.video_tag AS overdue_tag, vc.video_tag AS composition_tag
   FROM video_composition_overdue vco
   LEFT JOIN video_composition vc ON vco.video_id = vc.video_id
   WHERE vco.video_id IN ({checkVideoIds}) AND vco.deleted = 0
   ```
   预期：每行 `overdue_tag` = `composition_tag`（L1）

**清理步骤**：无（只读查询）
**是否需要人工介入**：否

---

### OVERDUE-S01-017 并发批量拆分：两个会话同时拆分同维度记录

**优先级**：P1
**用例类型**：功能测试（C-7 并发竞态）
**执行环境**：[ENV: TEST]
**所属模块**：SET-02 财务结算处理
**关联需求**：技术文档 §2.2.2（batchSplit 整体事务）
**风险来源**：技术审阅 R-1
**依赖用例**：无
**执行方式**：[执行方式: AI]

**前置条件**：
1. [认证] SYS-B 结算系统获取两个 accessToken（Token A、Token B）
2. [数据准备: DB] 同一 `receipted_month + channel_id` 下 ≥4 条 `status=1` 记录
   [验证: `SELECT COUNT(*) FROM video_composition_overdue WHERE receipted_month='{月份}' AND channel_id='{频道}' AND status=1 AND deleted=0` ≥4]
   {记录为:targetIds} = 前 4 条 id
3. [数据准备: DB] 对应冲销报表父行已到账（`received_status ≠ 0`）

**测试步骤**：
1. [SYS-B 并发] Token A 和 Token B 同时（间隔 < 500ms）发送：
   - 请求 A：`POST /videoCompositionOverdue/batchSplit` Body: `[{targetIds[0]}, {targetIds[1]}]`
   - 请求 B：`POST /videoCompositionOverdue/batchSplit` Body: `[{targetIds[2]}, {targetIds[3]}]`
2. 记录两个响应
3. [SYS-B DB] 查询最终状态

**预期结果**：
1. [断言: API] 至少一个返回 `code=0`（L1）
2. [断言: DB-Query] 冲销报表中不存在重复 pipeline_id（L1）：
   ```sql
   SELECT pipeline_id, COUNT(*) cnt FROM yt_reversal_report
   WHERE month='{月份}' AND channel_id='{频道}' GROUP BY pipeline_id HAVING cnt > 1
   ```
   → 返回 0 行
3. [断言: DB-Query] `status=2` 的记录数合理（不重复拆分）（L1）

**清理步骤**：见文档末尾 [清理 SQL 汇总](#清理SQL汇总) → OVERDUE-S01-017（需人工协助）
**是否需要人工介入**：是（清理涉及冲销表数据回滚，需 DBA 配合）
**备注**：⚠️ 高风险。维度扩展逻辑可能使两个会话扩展到相同记录集，产生竞态。

---

## 暂缓用例

---

### ~~OVERDUE-S01-012 查询范围覆盖~~

> **状态**：暂缓
> **依赖**：B-1（查询起始月份 2026-01 已确认，但截止点和多频道维度待回复）
> **关联测试点**：TP-S01-014（P1 IN）
> **恢复条件**：B-1 完整回复后补充

---

## 用例统计摘要

| 维度 | P0 | P1 | 暂缓 | 合计 |
|------|----|----|------|------|
| 功能测试 | 3 | 5 | 0 | 8 |
| 边界值测试 | 0 | 5 | 0 | 5 |
| 异常测试 | 0 | 3 | 0 | 3 |
| 暂缓 | 0 | 0 | 1 | 1 |
| **合计** | **3** | **13** | **1** | **17** |

> **V4.5 Mode B 补充**（+4 条）：OVERDUE-S01-014（videoTag 功能）、015（videoTag 边界值）、016（双表一致性）、017（并发拆分）

**P0 测试点覆盖率**：9/9 P0 测试点已覆盖（3 条直接覆盖 + 2 条合并为 DB 断言 + 4 条降级为 P1 用例覆盖）

| P0 测试点 | 覆盖用例 | 方式 |
|-----------|---------|------|
| TP-S01-001 | OVERDUE-S01-001 (P0) | 直接 |
| TP-S01-002 | OVERDUE-S01-002 (P0) | 直接 |
| TP-S01-003 | OVERDUE-S01-004 (P1) | 降级：完整性验证 |
| TP-S01-004 | OVERDUE-S01-005 (P1) | 降级：边界值 |
| TP-S01-005 | OVERDUE-S01-006 (P1) | 降级：边界值 |
| TP-S01-008 | OVERDUE-S01-009 (P1) | 降级：异常兜底 |
| TP-S01-011 | OVERDUE-S01-001 (P0) | 合并为 DB 断言 |
| TP-S01-012 | OVERDUE-S01-002 (P0) | 合并为 DB 断言 |
| TP-S01-013 | OVERDUE-S01-003 (P0) | 直接 |

**`[AI+人工]` 和 `[人工]` 用例**：无（全部为 `[执行方式: AI]`）

**知识库使用情况**：
- ✅ `systems/结算系统/knowledge/逾期结算处理.md`（代码逆向：状态流转、syncOverdueSettlementStatus 逻辑）
- ✅ `systems/结算系统/knowledge/data-testid/11_逾期结算处理.md`（前端元素定位参考）
- ✅ `iterations/.../input/tech/iteration/逾期结算处理-API接口设计.md`（API 端点、请求参数）
- ✅ `iterations/.../review/tech-review-report-main-backend.md`（开发回复：MQ 触发方式、并发防护等）

**数据清理说明**：清理 SQL 已统一收集到文档末尾 [清理 SQL 汇总](#清理SQL汇总)。AI 执行时**不自动清理**，测试工程师验证数据后手动执行或告知 AI 执行清理。

---

## 人工校验提示

> AI 已完成用例生成，请测试工程师按以下步骤完成人工校验，再提交/执行用例。

**校验步骤**：
1. 使用 `references/human-review-checklist.md` 中的清单逐项检查
2. 将发现的问题汇总后反馈给 AI，要求批量修改
3. 修改完成后，重新执行第1步（仅检查修改涉及的关项）
4. 全部项通过后，在清单底部填写"校验结论"并签名

**高风险项提示**（优先检查）：
- 第一关第1项：核心业务规则是否全部有用例覆盖
- 第二关第6-8项：字段名/按钮名/提示语是否与 PRD 一致
- 第三关第15项：预期结果是否可被 AI 判断

**SET-01 专项校验**：
- [ ] 剧老板 bind API 的完整参数列表是否已确认（compositionId 等作品关联参数）
- [ ] 测试环境中是否有满足条件的未登记视频（两系统均有对应数据）
- [ ] 边界日期用例（005~008）的执行日期约束是否可接受，或需改为 DB 回填方案
- [x] OVERDUE-S01-013 的预期结果：S-8（重复登记拦截）与 Q-10（变更登记不重新判定，产品选项A）均已确认，2026-04-20 已更新

---

## 清理 SQL 汇总 {#清理SQL汇总}

> **使用说明**：AI 执行用例时**不自动执行**清理步骤。测试工程师验证执行结果后，按需逐条或批量执行以下 SQL。
> **数据库**：`silverdawn_finance`（Host: 172.16.24.61:3306）
> **剧老板侧清理**：视频登记状态恢复需人工 DB 操作或通过变更登记机制，建议所有用例验证完毕后统一清理。

---

### OVERDUE-S01-001

```sql
-- 验证数据（清理前先确认）
SELECT id, video_id, status, registration_time, video_tag
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_001}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL, video_tag = NULL
WHERE video_id = '{测试视频ID_001}' AND status = 3;
```

---

### OVERDUE-S01-002

```sql
-- 验证数据
SELECT id, video_id, status, registration_time, video_tag
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_002}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL, video_tag = NULL
WHERE video_id = '{测试视频ID_002}' AND status = 1;
```

---

### OVERDUE-S01-003

```sql
-- 验证数据
SELECT id, video_id, status, registration_time, pipeline_id, sign_channel_id, team_name
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_003}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL,
    pipeline_id = NULL, sign_channel_id = NULL, sign_channel_name = NULL,
    cp_name = NULL, service_package_code = NULL, lang_code = NULL,
    team_id = NULL, team_name = NULL
WHERE video_id = '{测试视频ID_003}' AND status = 3;
```

---

### OVERDUE-S01-004

```sql
-- 验证数据（应有两条：一条 status=3，一条 status=1）
SELECT id, video_id, receipted_month, status, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_004}' ORDER BY receipted_month;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL
WHERE video_id = '{测试视频ID_004}' AND status IN (1, 3);
```

---

### OVERDUE-S01-005

```sql
-- 验证数据
SELECT id, video_id, status, published_date, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_005}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL
WHERE video_id = '{测试视频ID_005}' AND status = 3;
```

---

### OVERDUE-S01-006

```sql
-- 验证数据
SELECT id, video_id, status, published_date, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_006}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL
WHERE video_id = '{测试视频ID_006}' AND status = 1;
```

---

### OVERDUE-S01-007

```sql
-- 验证数据
SELECT id, video_id, status, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_007}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL
WHERE video_id = '{测试视频ID_007}';
```

---

### OVERDUE-S01-008

```sql
-- 验证数据
SELECT id, video_id, status, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_008}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL
WHERE video_id = '{测试视频ID_008}';
```

---

### OVERDUE-S01-009

无需清理（未产生逾期结算数据）。

---

### OVERDUE-S01-010

无需清理（观察性用例）。

---

### OVERDUE-S01-011

```sql
-- 验证数据
SELECT id, video_id, status, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_011}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL
WHERE video_id = '{测试视频ID_011}' AND status IN (1, 3);
```

---

### OVERDUE-S01-013

无需清理（未改变数据状态）。

---

### OVERDUE-S01-014

```sql
-- 验证数据
SELECT id, video_id, status, video_tag, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_VT01}' ORDER BY id DESC LIMIT 5;

-- 清理 overdue 表
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL, video_tag = NULL
WHERE video_id = '{测试视频ID_VT01}' AND status IN (1, 3);

-- 清理 composition 表
UPDATE video_composition
SET video_tag = NULL
WHERE video_id = '{测试视频ID_VT01}';
```

---

### OVERDUE-S01-015

```sql
-- 验证数据
SELECT id, video_id, status, video_tag, registration_time
FROM video_composition_overdue
WHERE video_id = '{测试视频ID_VT02}' ORDER BY id DESC LIMIT 5;

-- 清理
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL, video_tag = NULL
WHERE video_id = '{测试视频ID_VT02}' AND status IN (1, 3);
```

---

### OVERDUE-S01-016

无需清理（只读查询）。

---

### OVERDUE-S01-017

> ⚠️ **需人工协助**：涉及冲销表（`yt_reversal_report`）数据回滚，需 DBA 配合。

```sql
-- 验证数据：查看 overdue 表状态
SELECT id, video_id, status
FROM video_composition_overdue
WHERE receipted_month = '{月份}' AND channel_id = '{频道}' AND status = 2 AND deleted = 0;

-- 验证数据：查看冲销表新增子集行
SELECT id, pipeline_id, sign_channel_id, ROUND(cms_revenue, 2) as rev, settlement_created_status
FROM yt_reversal_report
WHERE parent_channel_id = '{频道}' AND month = '{结算月份}' AND channel_type = 1
ORDER BY id DESC LIMIT 10;

-- 清理 overdue 表
UPDATE video_composition_overdue
SET status = 1, operator_id = NULL, operator_name = NULL, operate_time = NULL
WHERE receipted_month = '{月份}' AND channel_id = '{频道}' AND status = 2 AND deleted = 0;

-- 清理冲销表（需 DBA 确认后执行）
-- DELETE FROM yt_reversal_report WHERE id IN ({本次拆分新增的子集行ID列表});
-- UPDATE yt_reversal_report SET channel_split_status = 1, unattributed_revenue = {原始值} WHERE id = {父行ID};
```

---

### 一键全量清理（慎用）

> ⚠️ 仅在所有用例验证完毕后使用。执行前务必确认变量已替换为实际值。

```sql
-- 批量恢复 status
UPDATE video_composition_overdue SET status = 0, registration_time = NULL, video_tag = NULL
WHERE video_id IN (
    '{测试视频ID_001}', '{测试视频ID_002}', '{测试视频ID_003}',
    '{测试视频ID_004}', '{测试视频ID_005}', '{测试视频ID_006}',
    '{测试视频ID_007}', '{测试视频ID_008}', '{测试视频ID_011}',
    '{测试视频ID_VT01}', '{测试视频ID_VT02}'
) AND status IN (1, 3) AND deleted = 0;

-- OVERDUE-S01-003 额外字段清理
UPDATE video_composition_overdue
SET pipeline_id = NULL, sign_channel_id = NULL, sign_channel_name = NULL,
    cp_name = NULL, service_package_code = NULL, lang_code = NULL,
    team_id = NULL, team_name = NULL
WHERE video_id = '{测试视频ID_003}' AND deleted = 0;

-- videoTag 清理
UPDATE video_composition SET video_tag = NULL
WHERE video_id IN ('{测试视频ID_VT01}', '{测试视频ID_VT02}');
```
