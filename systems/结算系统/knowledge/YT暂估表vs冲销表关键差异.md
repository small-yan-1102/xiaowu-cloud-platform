# 暂估表 vs 冲销表：关键差异对比

> 两表共用同一套频道分类骨架、合约匹配规则（`AmsCrmManager.handleYtContract`）、差额法拆分逻辑和不结算名单匹配流程，以下仅列出**实质性差异点**。

## 一、数据来源与生命周期

| 维度 | 暂估表 | 冲销表 |
|------|--------|--------|
| **上游数据** | `yt_month_channel_revenue`，`data_type=2`（月初） | `yt_month_channel_revenue`，按 `receipted_at` 区间查询 |
| **汇率月份** | **N+1月**（预估，早于到账） | **当月**（到账所在月份） |
| **生命周期** | 仅供预览，**不产生结算单** | 到账确认后可**生成结算单** |

## 二、字段体系差异（核心）

| 字段 | 暂估表 | 冲销表 |
|------|--------|--------|
| `settlement_created_status` | **无此字段** | 存在；父行=2，命中不结算=2，生成结算单=1 |
| `received_status` | **无此字段** | 存在；需手动标记到账才能生成结算单 |
| `cms_revenue_adjust`（调差） | **无** | 存在；参与 `distributableIncome` 计算，子集行强制清零 |
| `rpt_revenue`（财报收益） | 子集行直接保留 source 值 | 子集行**强制置 0**（v1.5.6+），仅父行保留 |
| CID 特殊行 | **无** | 全量生成时写入 `channel_id='CID'` 的 UGC 汇总行 |

## 三、重新生成方式差异

| 方式 | 暂估表 | 冲销表 |
|------|--------|--------|
| 按月/频道重新拆分 | `reSplitEstimateBatch`（按 ids） | `reSplitReversalBatch`（按月份+channelIds） |
| **按合约重新生成** | `reversalRegenerateByContractNum`：无结算状态校验，无 Redis 锁，直接先删后插 | `reversalRegenerateByContractNum`：先校验 `settlement_created_status=1` 则拒绝，加 `PrChannelIdNo:YT:` 自增锁，先删后插 |

## 四、子集删除权限差异

| 操作 | 暂估表 | 冲销表 |
|------|--------|--------|
| 单条删除结算状态校验 | **无**，直接删除 | `settlement_created_status=1` 时**禁止**删除 |
| 批量删除过滤条件 | 仅 `channel_type=SUBSET` | 额外过滤 `settlement_created_status ≠ 1` |
| Excel 导入预清理 | `deleteSubset()`（无状态限制） | `deleteSubsetByNeSettle()`（已结算子集不删） |
| 拆分子集并发保护 | **无** Redis 锁 | 加 `REPORT:SPLIT:{id}` 锁 |
