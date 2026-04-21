# 冒烟测试套件 — 数据准备文档（开发自测）

> **适用对象**：开发工程师提测前自测 / AI 冒烟执行
> **套件文件**：[suite_smoke.md](../suite_smoke.md) — 7 条用例（5 Happy Path + 2 关键异常）
> **数据库**：silverdawn_finance @ 172.16.24.61:3306
> **创建日期**：2026-04-17
> **预计数据准备时间**：~5 分钟

---

## §0 部署就绪校验（V4.5 代码 check）

执行数据准备前先确认 V4.5 代码已部署，否则 SMOKE-004/005 会误判为 Bug。

```sql
-- Check 1: video_composition_overdue 新增 video_tag 字段
SHOW COLUMNS FROM video_composition_overdue LIKE 'video_tag';
-- 预期：返回 1 行，Type = int

-- Check 2: video_composition_overdue 新增 original_status 字段（V4.5 SET-02）
SHOW COLUMNS FROM video_composition_overdue LIKE 'original_status';
-- 预期：返回 1 行

-- Check 3: 接口支持 status=3 入参（手工调用）
-- POST http://172.16.24.200:8024/videoCompositionOverdue/page
-- Body: {"page":1,"pageSize":10,"status":3}
-- 预期：返回 code=0，不报"参数非法"
```

> ⚠️ 若 Check 1/2 返回 0 行 → V4.5 数据迁移未执行 → 阻塞 SMOKE-004/005，联系开发确认部署

---

## §1 SMOKE-001 — 导入无归属视频

### 1.1 现成资产

**文件**：`smoke_import_2026-01.xlsx` — 含 3 条 videoId：

| videoId | channel_id | CMS | 收益($) 2026-01 |
|---------|-----------|:---:|:---:|
| pHmZ-SP1DHA | UC_7iONjjMgVnZTfpia-MwUg | XW | 37.57 |
| xWuqfuYh3RQ | UC_7iONjjMgVnZTfpia-MwUg | XW | 54.84 |
| zZcAgM-V0cg | UC_7iONjjMgVnZTfpia-MwUg | XW | 78.28 |

### 1.2 READY CHECK

```sql
-- 收益表必须有 3 条 2026-01 数据
SELECT COUNT(*) AS cnt
FROM yt_month_channel_revenue_source
WHERE target_video_id IN ('pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg')
  AND month = '2026-01';
-- 预期：cnt = 3，否则 SMOKE-001 会因「收益表不存在」被阻断（TP-S03-007）

-- 冲销报表父行必须存在（2026-01 / 频道 UC_7iONjjMgVnZTfpia-MwUg）
SELECT id, channel_id, month, received_status, channel_split_status,
       settlement_created_status, ROUND(unattributed_revenue,2) AS unattr_rev
FROM yt_reversal_report
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg' AND month = '2026-01' AND channel_type = 2;
-- 预期：返回 1 条，received_status = 1（已到账）
```

> **当前库已验证 ✅**：冲销表 id=1138814, received_status=1, unattr_rev=$1008.15, settlement_created_status=2（已生成结算单）
> **注意**：settlement_created_status=2 触发 V4.5 新逻辑「已生成结算单允许拆分」（TP-S02-032），与 SMOKE-002 互为正交验证

### 1.3 可重跑恢复（每次自测前）

```sql
-- 若上一轮已导入过 → 清理 overdue 表对应记录，以便重跑
DELETE FROM video_composition_overdue
WHERE video_id IN ('pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg')
  AND receipted_month = '2026-01';
```

---

## §2 SMOKE-002 — 逾期拆分（status=1 → status=2）

### 2.1 方案选择

**方案 A（推荐，现成数据）**：使用库中已有的 5 条 status=1 记录（channel=`UC_7iONjjMgVnZTfpia-MwUg`，pipeline=`49a63dcba3ac453eb3c64bc1b41e98a5`）

**方案 B（DB 回填）**：用 HELLO BEAR + 频道 `UCFCWoVDSnCdw8bfmTkNS0Lg` 的 status=0 记录，通过剧老板登记自然变 status=1（当前 published_date='2026-01-01'，发布次月28日=2026-02-28 < 今天 2026-04-17 → 登记即变 status=1）

### 2.2 方案 A：READY CHECK（现成 status=1）

```sql
SELECT id, video_id, channel_id, pipeline_id, team_name, status
FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0
LIMIT 5;
-- 预期：≥ 1 条

-- 对应冲销表父行必须已到账
SELECT id, received_status FROM yt_reversal_report
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg' AND month = '2026-01' AND channel_type = 2;
-- 预期：received_status = 1
```

### 2.3 方案 B：DB 回填触发逾期

```sql
-- Step 1: 挑 5 条 HELLO BEAR status=0（已有 published_date='2026-01-01'）
SELECT id, video_id, published_date FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
ORDER BY id LIMIT 5;

-- Step 2: 走剧老板登记（Yancz-cool@outlook.com）
--   由于 published_date='2026-01-01' → 次月28日=2026-02-28 < 今天 → 系统自动判定 status=1
```

### 2.4 可重跑恢复（仅方案 A 已消耗后）

```sql
-- 若 SMOKE-002 已拆分过方案 A 数据，status 变 2 → 恢复为 1 以便重跑
-- ⚠️ 注意：重跑拆分会导致冲销表产生多条子行，慎用
UPDATE video_composition_overdue
SET status = 1
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 2 AND deleted = 0
LIMIT 5;
```

---

## §3 SMOKE-003 — MQ 同步（status 0→1 逾期）

### 3.1 数据要求

status=0 + published_date 早于「今天 - 2 个月」→ 登记触发 MQ 后变 status=1

### 3.2 READY CHECK（HELLO BEAR 主/备频道均可）

```sql
-- 从 UCFCWoVDSnCdw8bfmTkNS0Lg（备选频道，published_date='2026-01-01'）挑 1 条
SELECT id, video_id, channel_id, published_date, team_name
FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND published_date <= '2026-02-17'  -- 今天 - 2 个月边界
ORDER BY id
LIMIT 1;
-- 预期：≥ 1 条
```

### 3.3 触发方式

见 [suite_smoke.md](../suite_smoke.md) SMOKE-003 Step 1，方式 A（剧老板页面登记）。

### 3.4 可重跑恢复

```sql
-- 若已消耗 → 通过清理 SQL（§8）恢复 status=0
```

---

## §4 SMOKE-004 — MQ 同步（status 0→3 跨期正常）

### 4.1 数据准备

**已完成，见** [cross-period-normal-data-prep.md](./cross-period-normal-data-prep.md)（HELLO BEAR + 主/备频道 published_date 回填为 '2026-03-15'）

### 4.2 READY CHECK

```sql
SELECT COUNT(*) AS ready_cnt
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND published_date = '2026-03-15';
-- 预期：ready_cnt ≥ 1
-- 若 = 0，先执行 cross-period-normal-data-prep.md 的 Step 1~3
```

### 4.3 时效约束

⚠️ **有效期 2026-04-28 之前登记**：published_date='2026-03-15' → 次月28日=2026-04-28。超过此日期登记，会变 status=1（逾期）而非 status=3。

---

## §5 SMOKE-005 — 跨期正常拆分（status=3 → status=2）

### 5.1 方案选择

**方案 A（依赖 SMOKE-004）**：按顺序先跑 SMOKE-004 产生 status=3 记录，再跑 SMOKE-005

**方案 B（独立预置，推荐）**：提前用备选频道 `UCFCWoVDSnCdw8bfmTkNS0Lg` 登记 1 条视频产生 status=3，解耦串行依赖

### 5.2 方案 B：独立预置步骤

```sql
-- Step 1: 挑 1 条备选频道视频，回填 published_date
UPDATE video_composition_overdue
SET published_date = '2026-03-15'
WHERE id = (
  SELECT id FROM (
    SELECT id FROM video_composition_overdue
    WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
      AND team_name = 'HELLO BEAR'
      AND status = 0 AND deleted = 0
    ORDER BY id LIMIT 1
  ) AS t
);

-- Step 2: 通过剧老板登记该视频（Yancz-cool@outlook.com）→ status 自动变 3
-- Step 3: 验证 status=3 产生
SELECT id, video_id, status, pipeline_id FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg' AND status = 3 AND deleted = 0;
```

### 5.3 READY CHECK

```sql
SELECT COUNT(*) AS ready_cnt FROM video_composition_overdue
WHERE status = 3 AND deleted = 0
  AND channel_id IN ('UC4IGCtXW9sdyZN2235v7r_Q', 'UCFCWoVDSnCdw8bfmTkNS0Lg');
-- 预期：ready_cnt ≥ 1
```

---

## §6 SMOKE-EX-001 — 导入互斥拦截

### 6.1 数据要求

存在一条同月份、status=0（导入中）、created_at 在 30 分钟内的 `excel_import_task` 记录

### 6.2 excel_import_task 字段说明

| 字段 | 必填 | 说明 |
|------|:---:|------|
| month | Y | '2026-01'（与 SMOKE-001 xlsx 对齐） |
| import_type | Y | 'OVERDUE_SETTLEMENT' |
| file_name | Y | 任意字符串 |
| status | Y | **0 = 导入中**（触发互斥关键字段） |
| created_at | Y | NOW()（30 分钟内） |
| operator_id | N | 操作人 ID |
| deleted | Y | 0 |

### 6.3 预置 SQL（方案 B — DB 直接插入，推荐）

```sql
-- 执行前：预置一条"卡住"的导入任务
INSERT INTO excel_import_task
  (month, import_type, file_name, file_key, total_count,
   status, operator_id, operator_name, created_at, updated_at, deleted)
VALUES
  ('2026-01', 'OVERDUE_SETTLEMENT', 'smoke-mutex-blocker', 'finance/smoke-mutex/blocker.xlsx', 0,
   0, 'smoke-test', 'smoke-test-operator', NOW(), NOW(), 0);

-- 记录 id（供清理用）
SELECT LAST_INSERT_ID();
```

### 6.4 READY CHECK

```sql
SELECT id, month, import_type, status, created_at
FROM excel_import_task
WHERE month = '2026-01' AND import_type = 'OVERDUE_SETTLEMENT'
  AND status = 0 AND deleted = 0
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 MINUTE);
-- 预期：返回 1 条
```

### 6.5 时序约束

⚠️ **预置后 25 分钟内执行 SMOKE-EX-001**，否则 created_at 超过 30min 互斥失效

### 6.6 清理

```sql
-- 执行完 SMOKE-EX-001 后清理（防止污染后续其他导入测试）
DELETE FROM excel_import_task
WHERE file_name = 'smoke-mutex-blocker' AND operator_id = 'smoke-test';
-- 或用刚才记录的 id：DELETE FROM excel_import_task WHERE id = {刚才的 id};
```

---

## §7 SMOKE-EX-002 — 拆分互斥拦截

### 7.1 关键前提

**当前库冲销表零子行**（无 pipeline_id 非空记录）→ EX-002 必须**链式依赖 SMOKE-002**：

```
SMOKE-002 拆分 → 冲销表产生子行（pipeline_id=49a63... settlement_created_status=0）
   ↓
构造一条同 pipeline_id 的 status=1 新记录
   ↓
SMOKE-EX-002 触发拆分 → 因子行已存在被拦截
```

### 7.2 构造 status=1 新记录 SQL（SMOKE-002 执行完后再跑）

```sql
-- 复制一条已有的 status=1 样本，改 video_id 让它成为"新"记录（未被 SMOKE-002 消耗）
-- 方案：从 channel 下选一条 SMOKE-002 未用过的视频手动插入

-- Step 1: 查 SMOKE-002 已消耗的 video_id
SELECT video_id FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 2 AND deleted = 0;

-- Step 2: 插入一条新 status=1（pipeline_id 与子行同）
-- ⚠️ 需要真实存在的 video_id（yt_month_channel_revenue_source 中有收益），否则拆分会因 R1 阻断
-- 推荐做法：找频道下另一条 status=0 记录，通过剧老板登记转为 status=1
SELECT id, video_id FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND status = 0 AND deleted = 0
LIMIT 1;
-- 然后剧老板登记该 videoId（不在 SMOKE-002 消耗的 5 条内）
```

### 7.3 READY CHECK

```sql
-- 冲销表有 pipeline_id=49a63... 的子行，且 settlement_created_status=0
SELECT id, pipeline_id, settlement_created_status FROM yt_reversal_report
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND settlement_created_status = 0
  AND channel_type = 2;
-- 预期：≥ 1 条

-- overdue 表有同 pipeline_id 的 status=1 未消耗记录
SELECT COUNT(*) FROM video_composition_overdue
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0;
-- 预期：≥ 1 条
```

### 7.4 备选方案

若不想链式构造，可 **跳过 SMOKE-EX-002**，标记为「依赖 SET-02 完整执行后再验证」。

---

## §8 清理 SQL（分级）

### 8.1 重跑恢复（保留测试数据，仅复位状态）

```sql
-- SMOKE-001 清理导入结果（允许重跑导入）
DELETE FROM video_composition_overdue
WHERE video_id IN ('pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg')
  AND receipted_month = '2026-01';

-- SMOKE-002 方案 A 恢复 status=1
UPDATE video_composition_overdue SET status = 1
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 2 AND deleted = 0;

-- SMOKE-003/004/005 恢复 status=0（见 cross-period-normal-data-prep.md §清理 SQL）

-- SMOKE-EX-001 删互斥任务
DELETE FROM excel_import_task
WHERE file_name = 'smoke-mutex-blocker' AND operator_id = 'smoke-test';
```

### 8.2 彻底清理（冒烟整体结束后）

```sql
-- 冲销表子行回滚（SMOKE-002 拆分产生的）
-- ⚠️ 谨慎执行，可能影响其他测试
DELETE FROM yt_reversal_report
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND settlement_created_status = 0
  AND channel_type = 2
  AND created_at >= '2026-04-17 00:00:00';  -- 限制今天产生的子行

-- cross-period-normal-data-prep.md 的清理 SQL 完整执行
```

---

## §9 账号与环境矩阵

| 角色 | 账号 | 密码来源 | 用途 |
|------|------|---------|------|
| 财务 | 15057199668 | `.claude/secrets/credentials.md` | 结算系统全 Tab + 拆分 |
| 分销商 | Yancz-cool@outlook.com | `.claude/secrets/credentials.md` | 剧老板触发登记（MQ 源） |
| DB | xiaowu_db | 开发工程师询问 DBA | SQL 预置/验证 |

| 环境 | URL |
|------|-----|
| 结算系统（测试） | http://172.16.24.200:7778/ssoLogin |
| 结算系统 API | http://172.16.24.200:8024 |
| 剧老板（测试） | http://distribute.test.xiaowutw.com |
| SSO | http://172.16.24.200:8011/sso/doLogin |
| 数据库 | 172.16.24.61:3306 / silverdawn_finance |

---

## §10 并发自测隔离指引

多名开发同时自测时，为避免数据互相污染：

| 隔离维度 | 建议 |
|---------|------|
| video_id 段位 | 开发 A：xlsx 中的 3 个；开发 B：另造一份 xlsx（换 3 个同频道 videoId） |
| pipeline_id | 开发 A 用 `49a63dcba3ac453eb3c64bc1b41e98a5`；开发 B 需先跑一次拆分产生新 pipeline |
| 频道 | 开发 A 用 `UC4IGCtXW9sdyZN2235v7r_Q`；开发 B 用 `UCFCWoVDSnCdw8bfmTkNS0Lg` |
| import_task | EX-001 的 `file_name` 加开发工号前缀（如 `smoke-mutex-blocker-001`） |

---

## §11 建议执行顺序与时序

### 推荐顺序（从独立到依赖）

```
准备：§0 部署校验 → §4 SMOKE-004 数据（已备） → §6 EX-001 预置

执行：
  1. SMOKE-001 导入           （独立，~90s）
  2. SMOKE-EX-001 互斥拦截    （依赖 §6 预置，必须 25min 内触发）
  3. SMOKE-003 MQ 0→1         （独立，~60s）
  4. SMOKE-004 MQ 0→3         （独立，~60s）
  5. SMOKE-002 逾期拆分       （用方案 A 现成 status=1，~90s）
  6. SMOKE-005 跨期正常拆分   （依赖 3/4，~90s）
  7. SMOKE-EX-002 拆分互斥    （依赖 5 产生的子行，~30s）

总计：~7 分钟 + 数据准备 ~5 分钟 = ~12 分钟
```

### 时序关键点

| 约束 | 要求 |
|------|------|
| SMOKE-004 登记有效期 | 2026-04-28 之前 |
| EX-001 互斥时效 | 预置后 25 min 内执行 |
| EX-002 链式依赖 | 必须在 SMOKE-002 之后 |

---

## 一键数据就绪自检 SQL

```sql
-- 复制全量执行，观察每行 status 是否 OK
SELECT 'SMOKE-001 收益表' AS item,
  CASE WHEN COUNT(*) = 3 THEN 'OK' ELSE 'MISSING' END AS status
FROM yt_month_channel_revenue_source
WHERE target_video_id IN ('pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg')
  AND month = '2026-01'
UNION ALL
SELECT 'SMOKE-001 冲销父行',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'MISSING' END
FROM yt_reversal_report
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg' AND month = '2026-01' AND channel_type = 2
UNION ALL
SELECT 'SMOKE-002 方案A status=1',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'MISSING' END
FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0
UNION ALL
SELECT 'SMOKE-003 status=0 可逾期',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'MISSING' END
FROM video_composition_overdue
WHERE team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND published_date <= '2026-02-17'
UNION ALL
SELECT 'SMOKE-004 status=0 跨期正常候选',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'MISSING' END
FROM video_composition_overdue
WHERE status = 0 AND deleted = 0
  AND published_date = '2026-03-15'
UNION ALL
SELECT 'EX-001 互斥任务 (需预置)',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'NEED_INSERT' END
FROM excel_import_task
WHERE month = '2026-01' AND status = 0 AND deleted = 0
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 MINUTE);
```

预期全部为 `OK`（或 `NEED_INSERT` 表示执行 EX-001 前再预置）。

---

*数据准备文档 | 冒烟测试套件 | 2026-04-17 创建*
