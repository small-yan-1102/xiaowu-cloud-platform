# 冒烟测试套件 — Round 2 数据准备文档（测试冒烟）

> **适用对象**：测试工程师在开发自测（Round 1）完成后执行冒烟测试
> **前置文档**：[smoke-data-prep.md](./smoke-data-prep.md)（Round 1 — 开发自测用）
> **套件文件**：[suite_smoke.md](../suite_smoke.md) — 同一套 7 条用例
> **数据库**：silverdawn_finance @ 172.16.24.61:3306
> **创建日期**：2026-04-17
> **预计数据准备时间**：~5 分钟

---

## §0 为什么需要 Round 2

Round 1（开发自测）跑完后，以下数据**不可回滚**：

| 污染点 | 原因 |
|--------|------|
| xlsx 中 3 个 videoId 已导入 | 同月份+同 videoId 禁止重复导入（去重规则） |
| 方案 A 的 5 条 `pipeline=49a63...` 已 status=2 | 无可用 status=1 |
| Round 1 登记过的 video 已 status=1/3 | 剧老板登记幂等，同 video 二次登记会抛 `VIDEO_ALREADY_RELATED`，MQ 不再发出 |
| 冲销表已有 `pipeline=49a63...` 子行 | 无法回滚至"零子行"原始态 |

Round 2 使用**另一套独立数据**，避开上述污染点。

---

## §1 SMOKE-001 — 导入（Round 2 新 xlsx）

### 1.1 Round 2 资产

**文件**：`smoke_import_2026-01_v2.xlsx` — 新 3 条 videoId（同频道，与 Round 1 不重合）：

| videoId | channel_id | CMS | 收益($) 2026-01 |
|---------|-----------|:---:|:---:|
| xamAKzz2WPg | UC_7iONjjMgVnZTfpia-MwUg | XW | 83.08 |
| GclPPYfhmHE | UC_7iONjjMgVnZTfpia-MwUg | XW | 46.30 |
| g7pWlMyl-gg | UC_7iONjjMgVnZTfpia-MwUg | XW | 42.29 |

### 1.2 READY CHECK

```sql
-- 新 videoId 收益表存在
SELECT COUNT(*) AS cnt
FROM yt_month_channel_revenue_source
WHERE target_video_id IN ('xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg')
  AND month = '2026-01';
-- 预期：cnt = 3

-- 冲销表父行（与 Round 1 共用同一条 id=1138814，不冲突）
SELECT id, received_status, settlement_created_status
FROM yt_reversal_report
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg' AND month = '2026-01' AND channel_type = 2;
-- 预期：仍是那条，received_status=1

-- 确认 Round 2 videoId 未被 Round 1 消耗
SELECT COUNT(*) AS overlap_cnt
FROM video_composition_overdue
WHERE video_id IN ('xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg')
  AND deleted = 0;
-- 预期：overlap_cnt = 0（Round 1 没用过这 3 个 videoId）
```

### 1.3 可重跑恢复

```sql
DELETE FROM video_composition_overdue
WHERE video_id IN ('xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg')
  AND receipted_month = '2026-01';
```

---

## §2 SMOKE-002 — 逾期拆分（Round 2 用方案 B）

### 2.1 方案选择（Round 2 只能用 B）

Round 1 方案 A 的 5 条 status=1 已被消耗。Round 2 改用 **方案 B**：用备选频道 `UCFCWoVDSnCdw8bfmTkNS0Lg` 的 5 条 status=0，通过剧老板登记转为 status=1。

### 2.2 Round 2 候选 videoId（避开 Round 1 可能用到的前 6 条）

```sql
-- 取 id=1378 及之后的 5 条（Round 1 若用方案 B 会从 id=1372 开始消耗前 5~6 条）
SELECT id, video_id, published_date
FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND id >= 1378
ORDER BY id LIMIT 5;
```

**当前候选**（已摸底）：

| id | video_id | published_date |
|----|----------|---------------|
| 1378 | ZpJZrM0NbDA | 2026-01-02 |
| 1379 | kyxIpqFOP6Q | 2026-01-02 |
| 1380 | Wv1Uzpi3Yzg | 2026-01-02 |
| 1381 | 2TjWkPwJgrM | 2026-01-02 |
| 1382+ | — | 2026-01-02 或更晚 |

### 2.3 执行步骤（方案 B）

1. **无需改 published_date**：2026-01-02 → 发布次月28日 = 2026-02-28 < 今天 → 登记即变 status=1
2. 用 HELLO BEAR 分销商账号（Yancz-cool@outlook.com）登录剧老板
3. 逐个登记上述 5 个 videoId
4. MQ 消费 5~30s → status 自动变 1
5. 对应冲销表父行（UCFCWoVDSnCdw8bfmTkNS0Lg）已有 $2398.45 未拆无归属收益 + received_status=1（已到账），拆分条件满足

### 2.4 READY CHECK

```sql
SELECT id, video_id, channel_id, status, pipeline_id
FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status = 1 AND deleted = 0
  AND video_id IN ('ZpJZrM0NbDA', 'kyxIpqFOP6Q', 'Wv1Uzpi3Yzg', '2TjWkPwJgrM');
-- 预期：≥ 4 条，pipeline_id 非空（由 MQ 同步填充）
```

### 2.5 可重跑恢复

```sql
-- 若已拆分 → 恢复 status=1
UPDATE video_composition_overdue SET status = 1
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status = 2 AND deleted = 0
  AND video_id IN ('ZpJZrM0NbDA', 'kyxIpqFOP6Q', 'Wv1Uzpi3Yzg', '2TjWkPwJgrM');
```

---

## §3 SMOKE-003 — MQ 同步（Round 2 新 video）

### 3.1 候选 videoId

挑 UCFCWoVDSnCdw8bfmTkNS0Lg 下更靠后的 1 条（避开 SMOKE-002 Round 2 用的 4 条）：

```sql
SELECT id, video_id, published_date
FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND id >= 1383  -- 避开 Round 2 SMOKE-002 的 1378~1382
ORDER BY id LIMIT 1;
```

### 3.2 READY CHECK

```sql
SELECT id, video_id FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND id >= 1383
ORDER BY id LIMIT 1;
-- 预期：≥ 1 条
```

---

## §4 SMOKE-004 — MQ 同步 status=3（Round 2 主频道补量）

### 4.1 情况分析

[cross-period-normal-data-prep.md](./cross-period-normal-data-prep.md) 原预置了 5 条 `published_date='2026-03-15'`。Round 1 会消耗 1 条。若剩余 ≥1 条，直接复用；否则 Round 2 需补量。

### 4.2 READY CHECK（先查是否有余量）

```sql
SELECT id, video_id FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND published_date = '2026-03-15'
LIMIT 1;
-- 若返回 ≥ 1 条 → 直接使用，跳到 4.4
-- 若返回 0 条 → 需执行 4.3 补量
```

### 4.3 补量 SQL（若无余量）

```sql
-- 从主频道 HELLO BEAR 取 5 条未被改过 published_date 的 status=0，改为 2026-03-15
UPDATE video_composition_overdue
SET published_date = '2026-03-15'
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND published_date != '2026-03-15'
ORDER BY id
LIMIT 5;

-- 验证
SELECT COUNT(*) FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND published_date = '2026-03-15';
-- 预期：≥ 5 条
```

### 4.4 执行步骤

同 [cross-period-normal-data-prep.md](./cross-period-normal-data-prep.md) Step 4~6，但挑剩余未登记的 videoId。

### 4.5 时效约束

⚠️ **2026-04-28 之前登记有效**：必须在此日期前完成测试冒烟，否则 status=3 会变 status=1。

---

## §5 SMOKE-005 — 跨期正常拆分

### 5.1 方案

Round 2 依赖 SMOKE-004 产生的 status=3（Round 1 的 status=3 已被拆分变 status=2，不可复用）。

### 5.2 READY CHECK（SMOKE-004 执行后）

```sql
SELECT id, video_id, status, pipeline_id
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 3 AND deleted = 0
LIMIT 1;
-- 预期：≥ 1 条（由 Round 2 SMOKE-004 产生）
```

---

## §6 SMOKE-EX-001 — 导入互斥（Round 2 新 file_name）

### 6.1 预置 SQL（区分 Round 1）

```sql
INSERT INTO excel_import_task
  (month, import_type, file_name, file_key, total_count,
   status, operator_id, operator_name, created_at, updated_at, deleted)
VALUES
  ('2026-01', 'OVERDUE_SETTLEMENT', 'smoke-mutex-blocker-round2',
   'finance/smoke-mutex/round2-blocker.xlsx', 0,
   0, 'smoke-test-round2', 'smoke-test-round2-operator', NOW(), NOW(), 0);

SELECT LAST_INSERT_ID();
```

### 6.2 READY CHECK

```sql
SELECT id, month, status, created_at FROM excel_import_task
WHERE file_name = 'smoke-mutex-blocker-round2'
  AND status = 0 AND deleted = 0
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 MINUTE);
-- 预期：1 条
```

### 6.3 时序约束

⚠️ 预置后 **25 分钟内** 执行 SMOKE-EX-001

### 6.4 清理

```sql
DELETE FROM excel_import_task WHERE file_name = 'smoke-mutex-blocker-round2';
```

---

## §7 SMOKE-EX-002 — 拆分互斥（Round 2 链式依赖）

### 7.1 策略

Round 2 SMOKE-002 拆分 UCFCWoVDSnCdw8bfmTkNS0Lg 的 4+ 条 status=1 → 会在冲销表产生**新 pipeline_id 的子行**（与 Round 1 的 `49a63...` 不同）。

拦截条件：同 pipeline_id 的 status=1 记录再次拆分 → 触发"子集已存在"拦截。

### 7.2 步骤

#### Step A：Round 2 SMOKE-002 完成后，查新产生的 pipeline_id

```sql
-- 新 pipeline（UCFCWoVDSnCdw8bfmTkNS0Lg 频道的）
SELECT DISTINCT pipeline_id
FROM yt_reversal_report
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND channel_type = 2
  AND pipeline_id IS NOT NULL
  AND pipeline_id NOT IN ('unattributed', '-1')
  AND settlement_created_status = 0;
-- 记录为 {newPipelineId}
```

#### Step B：登记一条同频道新 video 让 status 变 1（pipeline 会自动同步为 {newPipelineId}）

```sql
-- 取 id >= 1385 的未消耗 video_id
SELECT id, video_id FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND id >= 1385
ORDER BY id LIMIT 1;

-- 然后剧老板登记该 videoId → MQ 同步后 status=1 + pipeline_id={newPipelineId}
```

#### Step C：READY CHECK

```sql
-- 冲销表已有 newPipelineId 子行
SELECT id, pipeline_id, settlement_created_status
FROM yt_reversal_report
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND pipeline_id IS NOT NULL
  AND pipeline_id NOT IN ('unattributed', '-1')
  AND settlement_created_status = 0;
-- 预期：1 条

-- overdue 表有同 pipeline 的新 status=1
SELECT COUNT(*) FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status = 1 AND deleted = 0;
-- 预期：≥ 1 条（Step B 登记的 video）
```

### 7.3 备选方案

若测试同学不想重新构造，可 **复用 Round 1 留下的 pipeline=`49a63...` 子行**：只要该子行 `settlement_created_status` 还是 0，就仍然能触发拦截。但需要新构造一条同 pipeline 的 status=1 记录（Round 2 若手动 INSERT 需配合收益表）。**推荐 Step A~C 原生路径**。

---

## §8 清理 SQL（Round 1 + Round 2 合并清理）

Round 2 执行完毕后，两轮数据统一清理：

### 8.1 清理 overdue 表

```sql
-- Round 1 + Round 2 导入的 xlsx videoId
DELETE FROM video_composition_overdue
WHERE video_id IN ('pHmZ-SP1DHA', 'xWuqfuYh3RQ', 'zZcAgM-V0cg',
                   'xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg')
  AND receipted_month = '2026-01';

-- Round 1 SMOKE-002 方案 A 恢复 status=1（若用过）
UPDATE video_composition_overdue SET status = 1
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 2 AND deleted = 0;

-- Round 2 SMOKE-002/003 备选频道登记记录恢复 status=0（可选）
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL,
    pipeline_id = NULL, sign_channel_id = NULL, sign_channel_name = NULL,
    cp_name = NULL, service_package_code = NULL, lang_code = NULL
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status IN (1, 2, 3) AND deleted = 0
  AND registration_time >= '2026-04-17 00:00:00';  -- 限定今天登记的
```

### 8.2 清理冲销表子行

```sql
-- 清理两轮拆分产生的子行
DELETE FROM yt_reversal_report
WHERE pipeline_id IS NOT NULL
  AND pipeline_id NOT IN ('unattributed', '-1')
  AND settlement_created_status = 0
  AND channel_id IN ('UC_7iONjjMgVnZTfpia-MwUg', 'UCFCWoVDSnCdw8bfmTkNS0Lg')
  AND created_at >= '2026-04-17 00:00:00';
```

### 8.3 清理 excel_import_task

```sql
DELETE FROM excel_import_task
WHERE file_name IN ('smoke-mutex-blocker', 'smoke-mutex-blocker-round2');
```

### 8.4 清理 cross-period-normal 回填数据

见 [cross-period-normal-data-prep.md](./cross-period-normal-data-prep.md) 清理章节。

---

## §9 Round 1 → Round 2 交接清单

建议开发自测完成后，交付以下信息给测试：

| 交付项 | 说明 | 示例 |
|--------|------|------|
| 实际消耗的 videoId 清单 | Round 1 SMOKE-001~005 具体登记/导入的 videoId | `pHmZ-SP1DHA, _OvlYLHd2OQ, kyH7W2upjgw...` |
| Round 1 产生的 pipeline_id | SMOKE-002 拆分后产生的新 pipeline（若方案 A 则为 49a63...） | `49a63dcba3ac453eb3c64bc1b41e98a5` |
| Round 1 已清理的 excel_import_task | 是否已删 `smoke-mutex-blocker` | Y/N |
| 遗留问题清单 | 若 Round 1 有失败用例，记录原因 | — |

测试据此交接清单，执行 Round 2 的 READY CHECK 前可**精确定位是否有冲突**。

---

## §10 与 Round 1 的核心差异速查

| 维度 | Round 1 | Round 2 |
|------|---------|---------|
| SMOKE-001 xlsx | smoke_import_2026-01.xlsx | **smoke_import_2026-01_v2.xlsx** |
| SMOKE-001 videoId | pHmZ-SP1DHA, xWuqfuYh3RQ, zZcAgM-V0cg | **xamAKzz2WPg, GclPPYfhmHE, g7pWlMyl-gg** |
| SMOKE-002 方案 | A（现成 pipeline=49a63...） | **B（UCFCWoVDSnCdw8bfmTkNS0Lg 登记路径）** |
| SMOKE-002 消耗 id | 已有的 11307~11311 | **1378~1381（需登记）** |
| SMOKE-003/005 video | 前 N 条 UCFCWoVDSnCdw8bfmTkNS0Lg | **id≥1383 的后位 video** |
| SMOKE-004 主频道 | 原预置 5 条中第 1 条 | **剩余 4 条 或 UPDATE 补量** |
| EX-001 file_name | smoke-mutex-blocker | **smoke-mutex-blocker-round2** |
| EX-002 pipeline | 49a63... | **UCFCWoVDSnCdw8bfmTkNS0Lg 新产生的 pipeline** |

---

## §11 一键 READY CHECK SQL（Round 2 专用）

```sql
SELECT 'R2-SMOKE-001 收益表 (新 videoId)' AS item,
  CASE WHEN COUNT(*) = 3 THEN 'OK' ELSE 'MISSING' END AS status
FROM yt_month_channel_revenue_source
WHERE target_video_id IN ('xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg')
  AND month = '2026-01'
UNION ALL
SELECT 'R2-SMOKE-001 videoId 未被 Round 1 消耗',
  CASE WHEN COUNT(*) = 0 THEN 'OK' ELSE 'CONFLICT' END
FROM video_composition_overdue
WHERE video_id IN ('xamAKzz2WPg', 'GclPPYfhmHE', 'g7pWlMyl-gg')
  AND deleted = 0
UNION ALL
SELECT 'R2-SMOKE-002 备选频道 status=0 余量',
  CASE WHEN COUNT(*) >= 5 THEN 'OK' ELSE 'LOW' END
FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND team_name = 'HELLO BEAR'
  AND status = 0 AND deleted = 0
  AND id >= 1378
UNION ALL
SELECT 'R2-SMOKE-004 跨期候选余量',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'NEED_BACKFILL' END
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND published_date = '2026-03-15'
UNION ALL
SELECT 'R2-EX-001 互斥任务 (Round 2 专用)',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'NEED_INSERT' END
FROM excel_import_task
WHERE file_name = 'smoke-mutex-blocker-round2'
  AND status = 0 AND deleted = 0
  AND created_at >= DATE_SUB(NOW(), INTERVAL 30 MINUTE);
```

---

*Round 2 数据准备文档 | 冒烟测试套件 | 2026-04-17 创建*
