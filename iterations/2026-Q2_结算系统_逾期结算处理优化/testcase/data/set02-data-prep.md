# SET-02 财务结算处理 — 数据准备 SQL 清单

> **套件文件**：[suite_set02_settlement.md](../suite_set02_settlement.md) — 28 条用例
> **数据库**：silverdawn_finance @ 172.16.24.61:3306
> **创建日期**：2026-04-17
> **核心难点**：4 个校验拦截场景（S02-030/031/032/033）需构造特殊数据

---

## §0 现成数据盘点（执行前先跑）

### 0.1 可用 status=1 清单

```sql
SELECT o.channel_id, o.pipeline_id, o.receipted_month,
       COUNT(*) AS overdue_cnt, r.received_status, r.settlement_created_status, r.id AS reversal_id
FROM video_composition_overdue o
LEFT JOIN yt_reversal_report r
  ON r.channel_id = o.channel_id AND r.month = o.receipted_month
 AND r.channel_type = 2 AND (r.pipeline_id IS NULL OR r.pipeline_id = '')
WHERE o.status = 1 AND o.deleted = 0
GROUP BY o.channel_id, o.pipeline_id, o.receipted_month
ORDER BY overdue_cnt DESC;
```

**已知结果（2026-04-17）**：

| channel_id | pipeline_id | overdue 数 | 冲销表到账 | 冲销表 id |
|-----------|-------------|:---:|:---:|:---:|
| UC_7iONjjMgVnZTfpia-MwUg | 49a63dcba3ac453eb3c64bc1b41e98a5 | 13 | 已到账 | 1138814 |
| UC-Begn7OFOTv7fFbuVhX90Q | a02edca43a3e42b997428bf78c596e30 | 31 | 冲销表未匹配 | — |

### 0.2 可用 status=3 清单

```sql
SELECT channel_id, pipeline_id, receipted_month, COUNT(*)
FROM video_composition_overdue
WHERE status = 3 AND deleted = 0
GROUP BY channel_id, pipeline_id, receipted_month;
```

**当前库 0 条** → 必须先执行 [cross-period-normal-data-prep.md](./cross-period-normal-data-prep.md) 产生

### 0.3 4 个 Tab 数据分布

```sql
SELECT status, COUNT(*) FROM video_composition_overdue
WHERE deleted = 0 GROUP BY status;
-- 预期：status=0/1/2/3 各 >= 1 条
```

---

## §1 用例组 A：Tab 展示 + 筛选（S02-001/002a~c/011/023）

```sql
-- 确认各 Tab 有数据即可，用 §0.3 盘点结果
-- 筛选测试可直接用频道 UC_7iONjjMgVnZTfpia-MwUg
```

---

## §2 用例组 B：核心拆分（S02-003/004/006/028）

### 2.1 找可拆分的 status=1（冲销表已到账 + pipelineId 非空）

```sql
SELECT id, video_id, channel_id, pipeline_id, receipted_month, team_name
FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0
LIMIT 5;
```

### 2.2 找可拆分的 status=3（前提：cross-period-normal-data-prep.md 已执行）

```sql
SELECT id, video_id, channel_id, pipeline_id, receipted_month
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 3 AND deleted = 0
LIMIT 5;
```

---

## §3 用例组 C：校验拦截（核心 ⭐）

### 3.1 S02-030 冲销表未到账拦截

**场景**：冲销表父行 `received_status = 0` 时，拆分应被拒绝

```sql
-- Step 1: 记录原值（用于恢复）
SELECT id, received_status FROM yt_reversal_report WHERE id = 1138814;

-- Step 2: UPDATE 为未到账
UPDATE yt_reversal_report SET received_status = 0 WHERE id = 1138814;

-- Step 3: READY CHECK（找受影响的可拆分记录）
SELECT o.id, o.video_id, o.channel_id, o.pipeline_id, r.received_status
FROM video_composition_overdue o
JOIN yt_reversal_report r
  ON r.channel_id = o.channel_id AND r.month = o.receipted_month
 AND r.channel_type = 2 AND (r.pipeline_id IS NULL OR r.pipeline_id = '')
WHERE o.status IN (1, 3) AND o.deleted = 0
  AND r.received_status = 0
LIMIT 1;
-- 预期：>= 1 条

-- Step 4: 执行完用例后恢复
UPDATE yt_reversal_report SET received_status = 1 WHERE id = 1138814;
```

### 3.2 S02-031 子集已存在未结算单拦截

**场景**：冲销表已有同 `month+cms+pipeline_id` 子集行（settlement_created_status=0），新拆分应被拒绝

```sql
-- Step 1: 先执行一次拆分（用 §2.1 样本），拆完后冲销表会产生子行
-- 拆分后验证子行存在
SELECT id, pipeline_id, month, cms, settlement_created_status
FROM yt_reversal_report
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND settlement_created_status = 0
  AND channel_type = 2;
-- 预期：>= 1 条（拆分后产生）

-- Step 2: 构造新 status=1 记录匹配同 pipeline_id
-- 方式：找一个未被消耗的 video_id，通过剧老板登记
SELECT target_video_id FROM yt_month_channel_revenue_source
WHERE target_channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND month = '2026-01'
  AND target_video_id NOT IN (
    SELECT video_id FROM video_composition_overdue
    WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5' AND deleted = 0
  )
LIMIT 1;
-- 取到后在剧老板登记该 video_id（Yancz-cool@outlook.com）
-- MQ 同步后产生新 status=1 记录，pipeline_id 自动填为 49a63...

-- Step 3: READY CHECK
SELECT COUNT(*) FROM video_composition_overdue
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0;
-- 预期：>= 1 条（新登记产生的）
```

### 3.3 S02-032 子集已存在已结算单（允许拆分）

**场景**：在 S02-031 基础上，子行 `settlement_created_status=1`（已生成结算单），新拆分应**允许**

```sql
-- Step 1: 记录原值
SELECT id, settlement_created_status FROM yt_reversal_report
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND channel_type = 2 AND settlement_created_status = 0;

-- Step 2: UPDATE 为已生成结算单
UPDATE yt_reversal_report SET settlement_created_status = 1
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND settlement_created_status = 0
  AND channel_type = 2;

-- Step 3: READY CHECK
SELECT id, pipeline_id, settlement_created_status FROM yt_reversal_report
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND channel_type = 2;
-- 预期：子行 settlement_created_status = 1

-- Step 4: 执行完恢复（若希望保留供其他用例）
UPDATE yt_reversal_report SET settlement_created_status = 0
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND channel_type = 2 AND id = {Step1的id};
```

### 3.4 S02-033 视频 pipelineId 为空拦截

**场景**：video_composition 表 pipeline_id = NULL 时，对应 overdue 记录无法拆分

```sql
-- Step 1: 找一条 video_composition 记录（配合现有 status=1 数据）
SELECT o.video_id, vc.id AS vc_id, vc.pipeline_id AS original_pipeline
FROM video_composition_overdue o
JOIN video_composition vc ON vc.video_id = o.video_id
WHERE o.status = 1 AND o.deleted = 0
  AND vc.pipeline_id IS NOT NULL AND vc.pipeline_id != ''
LIMIT 1;
-- 记录 {vc_id} 和 {original_pipeline}

-- Step 2: UPDATE 为 NULL
UPDATE video_composition SET pipeline_id = NULL WHERE id = {vc_id};

-- Step 3: READY CHECK
SELECT id, video_id, pipeline_id FROM video_composition WHERE id = {vc_id};
-- 预期：pipeline_id IS NULL

-- Step 4: 执行完用例后恢复
UPDATE video_composition SET pipeline_id = '{original_pipeline}' WHERE id = {vc_id};
```

---

## §4 用例组 D：自动扩展同维度（S02-029a/029b）

### 4.1 找同频道+月份+pipelineId 多条 status=1（S02-029a）

```sql
SELECT channel_id, receipted_month, pipeline_id, COUNT(*) AS cnt
FROM video_composition_overdue
WHERE status = 1 AND deleted = 0
GROUP BY channel_id, receipted_month, pipeline_id
HAVING cnt >= 3
ORDER BY cnt DESC;
-- 已知：UC_7iONjjMgVnZTfpia-MwUg + 49a63... 有 13 条 ✅
```

### 4.2 找同频道同时有 status=1 和 status=3（S02-029b 状态隔离）

```sql
SELECT channel_id,
  SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS s1_cnt,
  SUM(CASE WHEN status = 3 THEN 1 ELSE 0 END) AS s3_cnt
FROM video_composition_overdue
WHERE deleted = 0
GROUP BY channel_id
HAVING s1_cnt > 0 AND s3_cnt > 0;
-- 当前库暂无（status=3 为 0 条），需先执行 cross-period-normal-data-prep.md
```

---

## §5 用例组 E：结果验证（S02-006/012/026）

```sql
-- 拆分后验证 original_status 字段（V4.5 新增）
SELECT video_id, status, original_status, pipeline_id, updated_at
FROM video_composition_overdue
WHERE status = 2 AND deleted = 0
ORDER BY updated_at DESC LIMIT 10;
-- 预期：original_status = 1（逾期拆分）或 3（跨期正常拆分）
```

---

## §6 用例组 F：导出（S02-019/020/022）

```sql
-- 导出筛选联动：确认 4 Tab 漏抓+非漏抓混合分布
SELECT status,
  SUM(CASE WHEN video_tag = 1 THEN 1 ELSE 0 END) AS 漏抓,
  SUM(CASE WHEN video_tag IS NULL THEN 1 ELSE 0 END) AS 非漏抓,
  COUNT(*) AS 总计
FROM video_composition_overdue
WHERE deleted = 0 AND status IN (1, 2, 3)
GROUP BY status;
-- 若漏抓列为 0 → 需执行 SET-04 数据预置（scraped_at 回填）
```

---

## §7 用例组 G：并发/空状态/历史（S02-034/035/011/012）

```sql
-- S02-011 空状态：查空月份
SELECT receipted_month, COUNT(*) FROM video_composition_overdue
WHERE status = 3 AND deleted = 0
GROUP BY receipted_month;

-- S02-012 历史记录
SELECT id, video_id, status, original_status, updated_at
FROM video_composition_overdue
WHERE status = 2 AND deleted = 0
ORDER BY updated_at DESC LIMIT 10;
```

---

## §8 数据准备优先级与难度

| 准备项 | 难度 | 时间 | 备注 |
|--------|:---:|:---:|------|
| status=1 现成数据 | ⭐ | 0min | UC_7iONjjMgVnZTfpia-MwUg + 49a63... 13 条，够用 |
| status=3 数据 | ⭐⭐ | 10min | 先执行 cross-period-normal-data-prep.md |
| S02-030 未到账 | ⭐ | 1min | 单行 UPDATE + 恢复 |
| S02-031 子集已存在 | ⭐⭐⭐ | 15min | 先拆分 1 次 + 剧老板登记造 status=1 新记录 |
| S02-032 结算单已生成 | ⭐⭐ | 2min | S02-031 基础上 UPDATE 子行 |
| S02-033 pipelineId 空 | ⭐⭐ | 2min | UPDATE video_composition + 记录原值 |

### 建议执行顺序

```
A 盘点
  → B 正向拆分（S02-003/004）
    → D 自动扩展（S02-029）
      → C-030（UPDATE 未到账）→ 恢复
        → C-031（先拆分 1 次造子集） → 跨到 C-032
          → C-032（UPDATE 子行结算状态） → 恢复
            → C-033（UPDATE pipeline 置空） → 恢复
```

---

## §9 清理 SQL（SET-02 测试完毕后）

```sql
-- 9.1 恢复冲销表父行到账状态
UPDATE yt_reversal_report SET received_status = 1 WHERE id = 1138814;

-- 9.2 恢复冲销表子行结算状态（若 S02-032 改过）
UPDATE yt_reversal_report SET settlement_created_status = 0
WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND channel_type = 2 AND settlement_created_status = 1
  AND created_at >= '2026-04-17 00:00:00';

-- 9.3 恢复 video_composition 的 pipeline_id（S02-033 用过的）
-- 根据测试记录的原值手动恢复：
-- UPDATE video_composition SET pipeline_id = '{原值}' WHERE id = {vc_id};

-- 9.4 删除 S02-031 登记产生的新记录（若需）
-- DELETE FROM video_composition_overdue
-- WHERE video_id = '{Step2登记的videoId}' AND deleted = 0;

-- 9.5 清理拆分产生的冲销表子行（谨慎！会影响其他迭代）
-- DELETE FROM yt_reversal_report
-- WHERE pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
--   AND channel_type = 2 AND settlement_created_status = 0
--   AND created_at >= '2026-04-17 00:00:00';
```

---

## §10 READY CHECK 一键自检

```sql
SELECT 'B-1 status=1 可拆分' AS item,
  CASE WHEN COUNT(*) >= 5 THEN 'OK' ELSE 'MISSING' END AS status
FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0
UNION ALL
SELECT 'B-2 status=3 可拆分',
  CASE WHEN COUNT(*) >= 1 THEN 'OK' ELSE 'MISSING (需 cross-period-normal-data-prep)' END
FROM video_composition_overdue
WHERE status = 3 AND deleted = 0
UNION ALL
SELECT 'D 自动扩展多条同维度',
  CASE WHEN COUNT(*) >= 3 THEN 'OK' ELSE 'MISSING' END
FROM video_composition_overdue
WHERE channel_id = 'UC_7iONjjMgVnZTfpia-MwUg'
  AND pipeline_id = '49a63dcba3ac453eb3c64bc1b41e98a5'
  AND status = 1 AND deleted = 0
UNION ALL
SELECT 'F 导出漏抓/非漏抓混合',
  CASE WHEN SUM(CASE WHEN video_tag = 1 THEN 1 ELSE 0 END) > 0
         AND SUM(CASE WHEN video_tag IS NULL THEN 1 ELSE 0 END) > 0
       THEN 'OK' ELSE 'MISSING' END
FROM video_composition_overdue
WHERE deleted = 0 AND status IN (1, 2, 3);
```

---

*SET-02 数据准备 SQL 清单 | 2026-04-17 创建*
