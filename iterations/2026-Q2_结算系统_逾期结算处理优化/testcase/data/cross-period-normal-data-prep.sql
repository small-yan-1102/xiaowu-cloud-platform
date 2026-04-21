-- ============================================================
-- 跨期正常未拆分（status=3）测试数据准备
-- ============================================================
-- 目标：产生 status=3 的逾期结算记录，用于 SET-02 跨期正常 Tab 展示和拆分测试
-- 分销商：HELLO BEAR（team_id=1988839584685428736）
-- 频道：UC4IGCtXW9sdyZN2235v7r_Q（冲销报表有 $675.84 无归属收益，已到账，未拆）
-- 方案：A（修改 published_date → 剧老板触发登记 → MQ 同步 → status 自动变 3）
-- 前提：V4.5 代码已部署到测试环境
-- 创建日期：2026-04-17
-- 数据库：silverdawn_finance
-- ============================================================

-- ====================
-- Step 1: 查看将要修改的数据（先看后改）
-- ====================

SELECT id, video_id, channel_id, receipted_month, published_date,
       team_id, team_name, status, pipeline_id
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND team_name = 'HELLO BEAR'
ORDER BY id
LIMIT 5;

-- 预期返回 5 条记录：
-- id=26841 video_id=U426E9K27KE  published_date=2026-02-01
-- id=26844 video_id=q85jo2BlQSM  published_date=2026-02-01
-- id=26845 video_id=gxvrGG56JPI  published_date=2026-02-01
-- id=26846 video_id=Fm0GA8zhb6Y  published_date=2026-02-01
-- id=26847 video_id=LgkztcKmz-k  published_date=2026-02-01


-- ====================
-- Step 2: 修改 published_date 为 2026-03-15
-- ====================
-- 原理：published_date = 2026-03-15
--       → 发布次月28日 = 2026-04-28
--       → 今天(2026-04-17) ≤ 2026-04-28 23:59:59
--       → 登记时判定为跨期正常 → status = 3
--
-- ⚠️ 有效期：此数据在 2026-04-28 之前登记才会变 status=3
--    2026-04-29 及之后登记会变 status=1（逾期）

UPDATE video_composition_overdue
SET published_date = '2026-03-15'
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND team_name = 'HELLO BEAR'
LIMIT 5;


-- ====================
-- Step 3: 验证修改结果
-- ====================

SELECT id, video_id, published_date, status, team_name
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 0 AND deleted = 0
  AND published_date = '2026-03-15';

-- 预期：5 条记录，published_date 均为 2026-03-15，status 仍为 0


-- ====================
-- Step 4: 从剧老板触发登记（手动操作，非 SQL）
-- ====================
-- 操作方式：
--   1. 用 HELLO BEAR 分销商账号登录剧老板系统
--      账号：Yancz-cool@outlook.com（team_id=1988839584685428736）
--   2. 进入「视频登记」→「未登记」Tab
--   3. 找到 video_id 为以下之一的视频：
--      gxvrGG56JPI / LgkztcKmz-k / U426E9K27KE / q85jo2BlQSM / Fm0GA8zhb6Y
--   4. 点击【登记】→ 选择作品 → 确认
--   5. 等待 MQ 消费完成（约 5~30 秒）
--
-- 或通过 API 触发：
--   POST http://distribute.test.xiaowutw.com/appApi/videoComposition/bind
--   Headers: accessToken: {剧老板Token}
--   Body: { "videoId": "gxvrGG56JPI", ... }


-- ====================
-- Step 5: 验证 status=3 产生
-- ====================

SELECT id, video_id, published_date, status, registration_time,
       pipeline_id, sign_channel_name, team_name
FROM video_composition_overdue
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND published_date = '2026-03-15' AND deleted = 0;

-- 预期：
-- 已登记的视频 → status = 3（跨期正常未拆分）
-- registration_time 有值，且 ≤ 2026-04-28 23:59:59
-- pipeline_id / sign_channel_name 由 MQ 同步填充


-- ====================
-- Step 6: 验证页面展示
-- ====================
-- 1. 登录结算系统 → 逾期结算处理页面
-- 2. 点击【跨期正常未拆分】Tab
-- 3. 搜索频道 UC4IGCtXW9sdyZN2235v7r_Q
-- 4. 确认刚登记的视频出现在列表中


-- ====================
-- 关联信息
-- ====================
-- 冲销报表数据（用于后续 SET-02 批量拆分）：
--   频道：UC4IGCtXW9sdyZN2235v7r_Q
--   结算月份：2026-01
--   无归属收益：$675.84
--   到账状态：已到账
--   拆分状态：未拆
--   可结算子集：0（需先完成逾期拆分才产生子集）

SELECT id, channel_id, month,
       ROUND(unattributed_revenue, 2) as unattr_rev,
       received_status, channel_split_status
FROM yt_reversal_report
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND channel_type = 2;


-- ====================
-- 备选频道：UCFCWoVDSnCdw8bfmTkNS0Lg
-- ====================
-- 用途：当主频道不够用、或需要 CMS=AC 对照数据时使用
-- 分销商：HELLO BEAR（team_id=1988839584685428736）
-- status=0 可用：190 条
-- CMS：AC
-- 冲销报表无归属：$2398.45（金额最大，适合批量拆分）
-- 到账状态：已到账，拆分状态：未拆

-- Step 1: 查看数据
SELECT id, video_id, published_date, team_name
FROM video_composition_overdue
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status = 0 AND deleted = 0
  AND team_name = 'HELLO BEAR'
ORDER BY id
LIMIT 5;

-- Step 2: 修改 published_date
UPDATE video_composition_overdue
SET published_date = '2026-03-15'
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status = 0 AND deleted = 0
  AND team_name = 'HELLO BEAR'
LIMIT 5;

-- 备选频道清理 SQL
-- 恢复 published_date
UPDATE video_composition_overdue
SET published_date = '2026-02-01'
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND published_date = '2026-03-15' AND deleted = 0;

-- 恢复 status
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL,
    pipeline_id = NULL, sign_channel_id = NULL, sign_channel_name = NULL,
    cp_name = NULL, service_package_code = NULL, lang_code = NULL
WHERE channel_id = 'UCFCWoVDSnCdw8bfmTkNS0Lg'
  AND status = 3 AND deleted = 0;


-- ====================
-- 其他可用频道（数据量小，仅供简单验证）
-- ====================
-- UCxm0qJBXSxNyn_duuhkFltw: 5 条, CMS=XW, 冲销无归属 $116.27  → 边界/小批量验证
-- UC7Ke0DR561Q5qnL9z7_Fwbw: 126 条, CMS=XW, 冲销无归属 $27.18  → 金额较低，不优先


-- ====================
-- 清理 SQL（测试完毕后恢复数据）
-- ====================

-- 恢复 published_date
UPDATE video_composition_overdue
SET published_date = '2026-02-01'
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND published_date = '2026-03-15' AND deleted = 0;

-- 恢复 status（如果已变为 3）
UPDATE video_composition_overdue
SET status = 0, registration_time = NULL,
    pipeline_id = NULL, sign_channel_id = NULL, sign_channel_name = NULL,
    cp_name = NULL, service_package_code = NULL, lang_code = NULL
WHERE channel_id = 'UC4IGCtXW9sdyZN2235v7r_Q'
  AND status = 3 AND deleted = 0
  AND video_id IN ('gxvrGG56JPI', 'LgkztcKmz-k', 'U426E9K27KE', 'q85jo2BlQSM', 'Fm0GA8zhb6Y');
