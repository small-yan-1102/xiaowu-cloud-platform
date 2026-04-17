-- ============================================================
-- SET-03 导入误差处理 测试数据准备脚本
-- 关联用例：api_suite_set03_import_validation.md
-- 使用方式：按用例编号找到对应段落，复制执行
-- ============================================================

-- ============================================================
-- 标准测试频道 — 基础数据（R1~R6 全系列用例共用）
-- 执行一次即可，后续各用例只需调整 yt_month_cms_end
-- ============================================================

-- 1. 收益占比数据（3 个视频，占比 0.5 / 0.3 / 0.2）
INSERT INTO yt_month_channel_revenue_source
  (channel_id, cms, month, video_id, v_revenue_ratio, v_us_revenue_ratio, v_sg_revenue_ratio)
VALUES
  ('UC_TEST_R2R5', 'CMS_TEST', '2026-02', 'T03_STD_A50', 0.50000000, 0.50000000, 0.50000000),
  ('UC_TEST_R2R5', 'CMS_TEST', '2026-02', 'T03_STD_B30', 0.30000000, 0.30000000, 0.30000000),
  ('UC_TEST_R2R5', 'CMS_TEST', '2026-02', 'T03_STD_C20', 0.20000000, 0.20000000, 0.20000000)
ON DUPLICATE KEY UPDATE
  v_revenue_ratio = VALUES(v_revenue_ratio),
  v_us_revenue_ratio = VALUES(v_us_revenue_ratio),
  v_sg_revenue_ratio = VALUES(v_sg_revenue_ratio);

-- 2. 冲销报表（分配记录 channelType=2，占比=1.0，无子集记录）
INSERT INTO yt_reversal_report
  (channel_id, cms, month, channel_type, sign_channel_id, pipeline_id,
   source_channel_revenue_ratio, unattributed_revenue, unattributed_us_revenue, unattributed_sg_revenue,
   received_status)
VALUES
  ('UC_TEST_R2R5', 'CMS_TEST', '2026-03', 2, -1, 'PIPELINE_TEST',
   1.00000000, 100.00, 50.00, 30.00,
   1)
ON DUPLICATE KEY UPDATE
  source_channel_revenue_ratio = VALUES(source_channel_revenue_ratio),
  unattributed_revenue = VALUES(unattributed_revenue),
  unattributed_us_revenue = VALUES(unattributed_us_revenue),
  unattributed_sg_revenue = VALUES(unattributed_sg_revenue),
  received_status = VALUES(received_status);

-- 3. CMS 收益基准（默认值，各用例按需调整）
INSERT INTO yt_month_cms_end
  (channel_id, cms, month, revenue, us_revenue, sg_revenue,
   adjusted_amount_1, adjusted_amount_2, adjusted_amount_3)
VALUES
  ('UC_TEST_R2R5', 'CMS_TEST', '2026-03', 100.00, 50.00, 30.00, 0.00, 0.00, 0.00)
ON DUPLICATE KEY UPDATE
  revenue = VALUES(revenue), us_revenue = VALUES(us_revenue), sg_revenue = VALUES(sg_revenue),
  adjusted_amount_1 = VALUES(adjusted_amount_1), adjusted_amount_2 = VALUES(adjusted_amount_2),
  adjusted_amount_3 = VALUES(adjusted_amount_3);

-- 4. video_composition 基础数据（用于 videoTag 计算）
INSERT INTO video_composition (video_id, published_at, scraped_at, related_type)
VALUES
  ('T03_STD_A50', '2026-01-15 00:00:00', '2026-03-01 10:00:00', 'OVERDUE'),
  ('T03_STD_B30', '2026-01-15 00:00:00', '2026-02-10 10:00:00', 'OVERDUE'),
  ('T03_STD_C20', '2026-01-15 00:00:00', '2026-02-10 10:00:00', 'OVERDUE')
ON DUPLICATE KEY UPDATE
  published_at = VALUES(published_at), scraped_at = VALUES(scraped_at);
-- T03_STD_A50: scraped_at(3月1日) > 发布次月15日(2月15日) → videoTag=1
-- T03_STD_B30/C: scraped_at(2月10日) ≤ 发布次月15日(2月15日) → videoTag=NULL

-- ============================================================
-- API-S03-014 R3 精确匹配：差额 = $0.00
-- ============================================================
-- CMS收益=$100.00, unattributed=$100.00
-- ROUND(0.5×100,2)=50.00 + ROUND(0.3×100,2)=30.00 + ROUND(0.2×100,2)=20.00 = 100.00
-- 差额 = 100.00 - 100.00 = $0.00 ✓
UPDATE yt_month_cms_end
SET revenue = 100.00, adjusted_amount_1 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 100.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- ============================================================
-- API-S03-012 R2 零值清理：T03_STD_C20 ROUND 后 = 0.00
-- ============================================================
-- CMS收益=$0.02, unattributed=$0.02
-- ROUND(0.5×0.02,2)=0.01, ROUND(0.3×0.02,2)=0.01, ROUND(0.2×0.02,2)=0.00 → 舍弃C
-- 保留求和=0.02, unattributed=0.02, 差额=0.00
UPDATE yt_month_cms_end
SET revenue = 0.02, adjusted_amount_1 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 0.02
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- ============================================================
-- API-S03-013 R3 误差抹平：差额 = -$0.01
-- ============================================================
-- CMS收益=$99.99, unattributed=$99.99
-- ROUND(0.5×99.99,2)=50.00, ROUND(0.3×99.99,2)=30.00, ROUND(0.2×99.99,2)=20.00
-- 求和=100.00, 差额=99.99-100.00=-0.01 → 抹平到A → A最终=49.99
UPDATE yt_month_cms_end
SET revenue = 99.99, adjusted_amount_1 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 99.99
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- ============================================================
-- API-S03-016 R4 边界：差额恰好 = $1.00 → 通过
-- ============================================================
-- 目标：unattributed - ROUND求和 = ±$1.00
-- 设 CMS收益=$101.00, unattributed=$100.00
-- ROUND(0.5×101,2)=50.50 + ROUND(0.3×101,2)=30.30 + ROUND(0.2×101,2)=20.20 = 101.00
-- 差额 = 100.00 - 101.00 = -$1.00（绝对值=1.00 ≤ 1 → 通过）
-- 抹平: A=50.50+(-1.00)=49.50, B=30.30, C=20.20, 求和=100.00 ✓
UPDATE yt_month_cms_end
SET revenue = 101.00, adjusted_amount_1 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 100.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- 预期结果：
-- T03_STD_A50 revenue = $49.50（50.50 - 1.00）
-- T03_STD_B30 revenue = $30.30
-- T03_STD_C20 revenue = $20.20
-- 求和 = $100.00 = unattributed ✓

-- ============================================================
-- API-S03-017 R4 边界：差额 = $1.01 → 阻断
-- ============================================================
-- 设 CMS收益=$101.01, unattributed=$100.00
-- ROUND(0.5×101.01,2)=50.51 + ROUND(0.3×101.01,2)=30.30 + ROUND(0.2×101.01,2)=20.20 = 101.01
-- 差额 = 100.00 - 101.01 = -$1.01（绝对值=1.01 > 1 → 阻断）
UPDATE yt_month_cms_end
SET revenue = 101.01, adjusted_amount_1 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 100.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- 预期结果：频道阻断，3 个视频均不入库

-- ============================================================
-- API-S03-018 R5 极端：全部 ROUND = 0.00
-- ============================================================
-- CMS收益=$0.001
-- ROUND(0.5×0.001,2)=0.00, ROUND(0.3×0.001,2)=0.00, ROUND(0.2×0.001,2)=0.00
-- 全部为零 → R5 触发阻断
UPDATE yt_month_cms_end
SET revenue = 0.001, adjusted_amount_1 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 0.001
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- ============================================================
-- API-S03-021 R6 任一阻断→整体阻断
-- 场景：总收益通过，美国收益差额 > $1 → 整体阻断
-- ============================================================
-- 总收益：CMS revenue=$100, unattributed=$100 → 差额$0 → 通过
-- 美国收益：CMS us_revenue=$201, unattributed_us=$200
--   ROUND(0.5×201,2)=100.50 + ROUND(0.3×201,2)=60.30 + ROUND(0.2×201,2)=40.20 = 201.00
--   差额 = 200.00 - 201.00 = -$1.00 → 还是通过…需要调大
-- 修正：CMS us_revenue=$202, unattributed_us=$200
--   ROUND(0.5×202,2)=101.00 + ROUND(0.3×202,2)=60.60 + ROUND(0.2×202,2)=40.40 = 202.00
--   差额 = 200.00 - 202.00 = -$2.00 → 阻断 ✓
-- 新加坡收益：CMS sg_revenue=$30, unattributed_sg=$30 → 差额$0 → 通过
UPDATE yt_month_cms_end
SET revenue = 100.00, adjusted_amount_1 = 0.00,
    us_revenue = 202.00, adjusted_amount_2 = 0.00,
    sg_revenue = 30.00, adjusted_amount_3 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 100.00,
    unattributed_us_revenue = 200.00,
    unattributed_sg_revenue = 30.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- 预期结果：
-- 总收益差额=$0 通过, 美国收益差额=-$2.00 > $1 阻断
-- → 整体阻断，3个视频均不入库

-- ============================================================
-- API-S03-022 Happy path 全流程成功
-- ============================================================
-- 恢复基础数据：CMS=$100, unattributed=$100（三种收益均无差额）
UPDATE yt_month_cms_end
SET revenue = 100.00, adjusted_amount_1 = 0.00,
    us_revenue = 50.00, adjusted_amount_2 = 0.00,
    sg_revenue = 30.00, adjusted_amount_3 = 0.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

UPDATE yt_reversal_report
SET unattributed_revenue = 100.00,
    unattributed_us_revenue = 50.00,
    unattributed_sg_revenue = 30.00
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03' AND channel_type = 2;

-- ============================================================
-- 清理脚本（全部用例执行完后统一清理）
-- ============================================================
DELETE FROM video_composition_overdue
WHERE channel_id = 'UC_TEST_R2R5' AND receipted_month = '2026-03';

DELETE FROM yt_month_channel_revenue_source
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-02';

DELETE FROM yt_reversal_report
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';

DELETE FROM yt_month_cms_end
WHERE channel_id = 'UC_TEST_R2R5' AND cms = 'CMS_TEST' AND month = '2026-03';
