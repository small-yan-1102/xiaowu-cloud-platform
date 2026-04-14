# 测试数据配置

> 基于数据库查询结果生成  
> 涉及数据库：silverdawn_ams / dispatcher（均 @ 172.16.24.61:3306，user=xiaowu_db，password=}C7n%7Wklq6P）  
> 查询时间：2026-03-31（第五次更新：限定双频道数据，新增橙汁频道，扩充至10个可用作品/19个视频）  
> 适用套件：所有测试套件（suite_smoke.md, suite_ams_video_takedown.md, suite_ams_termination.md, suite_integration.md 等）  
> 连接方式：SSH隧道（172.16.24.200 跳板 → 172.16.24.61 数据库）

---

## 1. 系统登录信息

| 占位符 | 实际值 | 说明 |
|--------|--------|------|
| {AMS_TEST_URL} | http://172.16.24.200:7778/MyApps | 云平台入口，登录后选择【资产管理系统】进入 AMS |
| {AMS_ADMIN_USER} | 15057199668 | 验证码登录 |
| {AMS_ADMIN_PASS} | 1111 | 固定验证码 |
| {JLB_TEST_URL} | http://distribute.test.xiaowutw.com/login | 剧老板入口 |
| {JLB_DIST_USER} | Yancz-cool@outlook.com | 邮箱登录，主分销商（HELLO BEAR），authType=2 (ALL)，team_id=1988839584685428736 |
| {JLB_DIST_PASS} | TxdvZ06y | 密码 |
| {JLB_LIMITED_USER} | 15057199668 | 手机号登录，authType=1（部门级，仅本部门数据），所属团队 YUJA-001 (team_id=1985522863929118720) |
| {JLB_LIMITED_PASS} | 4aYkEmKJ | 密码 |
| {JLB_EMPTY_USER} | 18506850780 | 手机号登录，authType=3（SCOPE），scope 管理 user 2016071682205720576，所属团队 YUJA-001 |
| {JLB_EMPTY_PASS} | 1KXuVhmT | 密码 |
| {JLB_DIST_B_USER} | 17835727272 | 手机号登录，第二分销商，authType=2 (ALL)，team_id=1988520080772243456 |
| {JLB_DIST_B_PASS} | Jlb123456 | 密码 |

### 1.1 基础设施信息

| 项目 | 值 | 说明 |
|------|-----|------|
| 测试服务器 A | 172.16.24.200（user=test，pwd=wgu4&Q_2） | 前端 + 部分后端服务 |
| 测试服务器 B | 172.16.24.204（user=test，pwd=wgu4&Q_2） | 后端服务 |
| Redis | 172.16.24.200:6379 | 测试环境 Redis |
| 数据库 | 172.16.24.61:3306（user=xiaowu_db，pwd=}C7n%7Wklq6P） | MySQL 8.0 |

---

## 2. 业务数据 - 作品与频道

### 2.1 已在任务中使用的作品 — D的气泡水

> **勘误**：composition_id=19584 的作品名称在 `ams_publish_channel.sign_channel_name` 中为 **D的气泡水**（非亚历山大moto）。亚历山大moto 的 composition_id=99354。

| 字段 | 值 | 来源 |
|------|-----|------|
| 作品名称 | **D的气泡水** | ams_publish_channel.sign_channel_name (composition_id=19584) |
| CP名称 | 境外一号南盾小饼干 | video_takedown_task_composition.cp_name |
| 绑定海外频道 | 4个频道：604292219431376(哈哈哈历险), UC3OASOStqIRqtk7awPoOkEw(新开频道), UClDJc5bJntyxdJoHB94GVgg(@林), UCtrVMtqUt5ICmjZeYsoafxA(@@@杨宇月@@@) | register_channel_ids |
| 已下架视频 | ~~_ivssajl8C0, 8osKZ-x8QXE, 380Ns7AJ0O4~~（3个均已被多次 VIDEO_DELETE） | 被 V2603300001/V2603300005/V2603300007 处理 |
| 可用视频 | @林 频道上仍有可用视频（详见§10 数据链） | dispatcher.video_order |
| 复用状态 | **可复用** — 多条已完成任务不阻塞新创建 | |

> **注意**：D的气泡水已被 8 个任务单使用（详见§3.0），3 个视频均已被 VIDEO_DELETE。`is_linked` 字段对视频下架操作无影响。
> **VTD-001 优先推荐**：使用 §10 中的 **蓝天上的流云**(215579) 代替 D的气泡水，有 3 个全新可用视频。

### 2.2 YouTube频道信息（仅限测试使用频道）

> **约束：后续所有测试套件只能使用以下两个 YT 频道对应的数据。**

| 序号 | 频道ID | 频道名称 | 用途说明 |
|:---:|--------|---------|---------|
| 1 | `UClDJc5bJntyxdJoHB94GVgg` | @林 | 主测试频道，13个可用视频，覆盖6个作品 |
| 2 | `UCA17JOb1Bo5YQdggQwJN20Q` | 橙汁的测试频道-0627-02 | 辅助测试频道，6个可用视频，覆盖6个作品 |

> 两个频道合计：10个不同作品、19个可用视频（去重后）。详见 §10。

### 2.3 有分配记录的作品（可用于解约单测试）

> 来源：composition_allocate JOIN composition_allocate_detail（注意：分销商信息在 composition_allocate 父表中，detail 表仅含 allocate_id 关联）

**HELLO BEAR 前10条活跃作品**：

| 作品ID | 作品名称 | CP类型 |
|--------|---------|--------|
| 16425 | 版权采买作品001 | 2 (采买) |
| 20004 | 我叫阮甜甜 | 3 |
| 20006 | 麻辣婆媳逗 | 2 (采买) |
| 77353 | 整个娱乐圈都在等我们离婚 | 2 (采买) |
| 77360 | 被离婚后我成为了千亿总裁 | 2 (采买) |
| 77369 | 我的合约老婆 | 3 |
| 77581 | 流浪之家 | 3 |
| 86439 | 山之影落烟火圆 | 3 |
| 86444 | 植物大战僵尸战棋 | 1 (自有) |

---

## 3. 已存在的任务单数据

> **数据状态（2026-03-31 更新）**：video_takedown_task 表中有 **8 条**记录。  
> 作品均为 **D的气泡水** (composition_id=19584)，频道均为 **@林** (UClDJc5bJntyxdJoHB94GVgg)。

### 3.0 任务单快速查阅表

| 任务单编号 | 状态 | 处理方式 | 下架原因 | 来源 | 视频数 | 展开状态 | 可用于测试 |
|-----------|------|---------|---------|------|:-----:|---------|-----------|
| **V2603300001** | **COMPLETED** | VIDEO_DELETE | DISTRIBUTOR_TERMINATION | PAGE_CREATE | 3 | SUCCESS | VTD-004(详情)、VTD-005(搜索)、VTD-008(队列) |
| **V2603300002** | **CREATE_FAILED** | VIDEO_PRIVACY | DISTRIBUTOR_TERMINATION | DISTRIBUTOR | 1 | SUCCESS | ~~VTD-006~~(已用V2603300003替代) |
| **V2603300003** | **PENDING_REVIEW** | VIDEO_DELETE | TEMP_COPYRIGHT_DISPUTE | PAGE_CREATE | 0 | PENDING | VTD-006已重测通过（编辑→重提交） |
| **V2603300004** | **PENDING_REVIEW** | VIDEO_DELETE | TEMP_COPYRIGHT_DISPUTE | PAGE_CREATE | 3 | SUCCESS | VTD-003(审核)、VTD-005(搜索) |
| **V2603300005** | **COMPLETED** | VIDEO_DELETE | TEMP_COPYRIGHT_DISPUTE | PAGE_CREATE | 3 | SUCCESS | VTD-004(详情) |
| **V2603300006** | **PENDING_REVIEW** | VIDEO_DELETE | ADJUST_LAUNCH_TIME | PAGE_CREATE | 0 | PENDING | VTD-003(审核)、VTD-006(编辑) |
| **V2603300007** | **COMPLETED** | VIDEO_DELETE | TEMP_COPYRIGHT_DISPUTE | PAGE_CREATE | 3 | SUCCESS | VTD-004(详情) |
| **V2603300009** | **PENDING_REVIEW** | VIDEO_DELETE | TEMP_COPYRIGHT_DISPUTE | PAGE_CREATE | 3 | SUCCESS | VTD-003(审核)、VTD-005(搜索) |

> **按状态分组**：
> - COMPLETED（3条）：V2603300001、V2603300005、V2603300007
> - PENDING_REVIEW（4条）：V2603300003、V2603300004、V2603300006、V2603300009
> - CREATE_FAILED（1条）：V2603300002

### 3.1 V2603300001 详情（已完成 - 首个测试任务）

| 字段 | 值 |
|------|-----|
| 任务单编号 | V2603300001 |
| 状态 | **COMPLETED（已完成）** |
| 处理方式 | VIDEO_DELETE（视频删除） |
| 下架原因 | DISTRIBUTOR_TERMINATION（分销商解约） |
| 创建方式 | BY_COMPOSITION（按作品创建） |
| 作品 | D的气泡水 (19584) |
| 视频 | 380Ns7AJ0O4, 8osKZ-x8QXE, _ivssajl8C0（3条，均 COMPLETED） |
| 审核时间 | 2026-03-30 14:10:30 |

### 3.2 V2603300002 详情（创建失败）

| 字段 | 值 |
|------|-----|
| 任务单编号 | V2603300002 |
| 状态 | **CREATE_FAILED（创建失败）** |
| 处理方式 | VIDEO_PRIVACY（视频私享） |
| 任务来源 | DISTRIBUTOR（分销商） |
| 创建方式 | BY_VIDEO_ID（按视频ID创建） |
| 视频 | 380Ns7AJ0O4（FAILED - 视频已被 V2603300001 删除） |
| 失败原因 | 无权限或未找到发布通道 |

### 3.3 V2603300003 详情（待审核 - VTD-006 重测使用）

| 字段 | 值 |
|------|-----|
| 任务单编号 | V2603300003 |
| 状态 | **PENDING_REVIEW（待审核）** |
| 历史状态 | REVIEW_REJECTED → 编辑 → 重提交 → PENDING_REVIEW |
| 处理方式 | VIDEO_DELETE（视频删除） |
| 展开状态 | PENDING（未展开） |
| 冒烟测试用途 | VTD-006 重测通过，证明编辑+重提交功能正常 |

> **综合影响**：
> - 3 条 COMPLETED 任务 → 可用于 **VTD-004**（查看详情）和 **VTD-008**（执行队列）
> - 4 条 PENDING_REVIEW 任务 → 可用于 **VTD-003**（审核）和 **VTD-005**（搜索/筛选）
> - V2603300002 CREATE_FAILED → 可用于 **VTD-006**（编辑重提交）的备选数据
> - 所有任务均使用 D的气泡水(19584) 的 3 个视频（380Ns7AJ0O4, 8osKZ-x8QXE, _ivssajl8C0），这些视频已被多次 VIDEO_DELETE

### 3.4 分发层执行队列（dispatcher.video_takedown_queue）

> 数据库：`dispatcher @ 172.16.24.61:3306`（user=xiaowu_db）  
> YouTube 后台视频下架成功后，需在此表查询对应状态。

**当前状态（2026-03-31）：9 条记录**

| 来源任务 | 视频ID | 队列状态 | 处理方式 | 执行时间 | 完成时间 |
|---------|--------|---------|---------|---------|---------|
| V2603300001 | 380Ns7AJ0O4 | **completed** | VIDEO_DELETE | 14:10:32 | 14:10:47 |
| V2603300001 | 8osKZ-x8QXE | **completed** | VIDEO_DELETE | 14:10:32 | 14:10:47 |
| V2603300001 | _ivssajl8C0 | **completed** | VIDEO_DELETE | 14:10:32 | 14:10:47 |
| V2603300005 | 380Ns7AJ0O4 | filtered | VIDEO_DELETE | - | - |
| V2603300005 | 8osKZ-x8QXE | filtered | VIDEO_DELETE | - | - |
| V2603300005 | _ivssajl8C0 | filtered | VIDEO_DELETE | - | - |
| V2603300007 | 380Ns7AJ0O4 | filtered | VIDEO_DELETE | - | - |
| V2603300007 | 8osKZ-x8QXE | filtered | VIDEO_DELETE | - | - |
| V2603300007 | _ivssajl8C0 | filtered | VIDEO_DELETE | - | - |

> **说明**：
> - **completed(3条)**：V2603300001 审核通过后执行成功，可用于 **VTD-008** 执行队列验证
> - **filtered(6条)**：V2603300005/V2603300007 的视频因已被删除而被过滤，未实际执行

**表结构关键字段（21列）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | bigint | 关联 AMS video_takedown_task.id |
| task_detail_id | bigint | 关联 AMS video_takedown_task_detail.id |
| video_id | varchar(50) | YouTube 视频ID |
| register_channel_id | varchar(50) | YouTube 频道ID |
| pipeline_id | varchar | 管道ID（新增字段） |
| process_method | varchar(20) | VIDEO_DELETE / VIDEO_PRIVACY |
| queue_status | varchar(20) | 队列状态：pending -> completed |
| priority | int | 执行优先级 |
| deadline_date | varchar(10) | 截止日期 |
| approve_time | timestamp | 审核时间（新增字段） |
| source_data_id | bigint | 来源数据ID（新增字段） |
| biz_id | varchar | 业务ID（新增字段） |
| execute_time | timestamp | 开始执行时间 |
| complete_time | timestamp | 完成时间 |
| status_detail | varchar(512) | 失败时的错误详情 |
| retry_count | tinyint | 重试次数 |
| version | int | 乐观锁版本号（新增字段） |
| deleted | tinyint | 逻辑删除标志（新增字段） |

**测试验证用 SQL：**

```sql
-- 按视频ID查询执行状态
SELECT video_id, queue_status, process_method, execute_time, complete_time, status_detail
FROM dispatcher.video_takedown_queue
WHERE video_id = '{VIDEO_ID}';

-- 按任务单ID查询所有视频执行状态
SELECT video_id, queue_status, status_detail, retry_count, execute_time, complete_time
FROM dispatcher.video_takedown_queue
WHERE task_id = {TASK_ID};
```

> **数据流向**：AMS 审核通过 -> dispatcher.video_takedown_queue (queue_status=pending) -> YouTube API 执行 -> queue_status=completed -> 回写 AMS 任务单状态 -> MQ 同步到剧老板

---

## 4. 解约单数据

### 4.1 现有解约单（34条）

> **数据更新（2026-03-30 查询）**：解约单从 29 条增加到 34 条。新增 5 条均有 `need_takedown=1`（联动视频下架），但对应的视频下架任务单（V2603270015~V2603270027）已随 task 表清空而不存在。

**need_takedown 分布：**
| need_takedown | 数量 | 说明 |
|:---:|:---:|------|
| NULL | 29 | V2.0 之前创建的旧解约单 |
| 1 | 5 | V2.0 联动功能创建，关联任务单已删除 |

**terminate_type 分布：**
| 解约类型 | 数量 |
|---------|:---:|
| 1 (双方协商) | 23 |
| 2 (分销商解约) | 5 |
| 3 (上游版权解约) | 6 |

**最近 5 条联动解约单：**

| 解约单编号 | 解约类型 | 分销商 | 下架原因 | 关联任务单 | 截止日期 | 创建时间 |
|-----------|---------|--------|---------|-----------|---------|---------|
| C202603270011 | 3 (上游版权) | HELLO BEAR | COPYRIGHT_TERMINATION | V2603270027（**已删除**） | 2026-03-30 | 2026-03-27 20:58 |
| C202603270010 | 3 (上游版权) | HELLO BEAR | COPYRIGHT_TERMINATION | V2603270024（**已删除**） | 2026-03-30 | 2026-03-27 19:57 |
| C202603270009 | 2 (分销商) | 马小强 | DISTRIBUTOR_TERMINATION | V2603270019（**已删除**） | 2026-03-27 | 2026-03-27 18:28 |
| C202603270008 | 2 (分销商) | 境外--YUJA--002 | DISTRIBUTOR_TERMINATION | V2603270016（**已删除**） | 2026-03-31 | 2026-03-27 16:10 |
| C202603270007 | 1 (双方协商) | 我的运气爆棚 | COPYRIGHT_TERMINATION | V2603270015（**已删除**） | 2026-03-27 | 2026-03-27 16:07 |

> **注意**：5 条联动解约单的关联任务单（takedown_task_code）均已随 task 表重置而不存在。这不影响 AMS-TER-001 测试——冒烟用例会创建新的解约单。

---

## 5. 字典枚举值

### 5.1 下架原因 (videoTakedownReasons)

| 标签 | 值 |
|------|-----|
| 上游版权方解约 | COPYRIGHT_TERMINATION |
| 分销商解约 | DISTRIBUTOR_TERMINATION |
| 单作品解约 | SINGLE_TERMINATION |
| 临时版权纠纷 | TEMP_COPYRIGHT_DISPUTE |
| 调整上线时间 | ADJUST_LAUNCH_TIME |
| 其他原因 | OTHER |

### 5.2 处理方式 (videoTakedownProcessMethods)

| 标签 | 值 |
|------|-----|
| 视频删除 | VIDEO_DELETE |
| 视频私享 | VIDEO_PRIVACY |

### 5.3 解约类型 (compositionTerminationType)

| 标签 | 值 |
|------|-----|
| 双方协商一致 | 1 |
| 分销商解约 | 2 |
| 上游版权解约 | 3 |

---

## 6. 用例 -> 数据映射表（2026-03-31 更新）

> **冒烟测试已完成**：7 PASS / 0 FAIL / 4 BLOCKED / 1 待人工验证。以下为当前数据可用性。

| 用例编号 | 冒烟结果 | 所需数据 | 推荐数据 | 状态 |
|---------|---------|---------|---------|------|
| **AMS-VTD-001** | **PASS** | 签约作品 + 海外频道 | 蓝天上的流云(215579) 或 D的气泡水(19584) + @林频道 | **可用** |
| **AMS-VTD-002** | BLOCKED | 分销商 + Excel + 视频ID | HELLO BEAR + zdNh8rzITgA | **可用**（需未删除视频） |
| **AMS-VTD-003** | **PASS** | "待审核"任务单 | V2603300004/V2603300006/V2603300009 | **可用** |
| **AMS-VTD-004** | **PASS** | "已完成"任务单 | V2603300001/V2603300005/V2603300007 | **可用** |
| **AMS-VTD-005** | **PASS** | 多状态任务单编号 | 8条任务单覆盖3种状态 | **可用** |
| **AMS-VTD-006** | **PASS** | "审核拒绝/创建失败"任务单 | V2603300003(已用)/V2603300002(备选) | **可用** |
| **AMS-VTD-007** | BLOCKED | "视频私享"待审核任务单 | 需新建 VIDEO_PRIVACY 任务 | **需创建** |
| **AMS-VTD-008** | **PASS** | 已完成任务 + 执行队列 | V2603300001 + dispatcher 3条completed | **可用** |
| **AMS-TER-001** | 待人工验证 | 分销商 + 未解约作品 | HELLO BEAR (510个活跃作品) | **可用** |
| **JLB-VM-001** | BLOCKED | 剧老板同步数据 | 需分销商来源任务走完 MQ 同步 | **需前置** |
| **JLB-VM-002** | BLOCKED | 同上 | 同上 | **需前置** |
| **AMS-E2E-001** | - | 全链路数据 | 需 VTD-002 走完后验证 | **需前置** |

---

## 7. 数据缺口与解决方案

### 7.1 "分销商名称" 数据（AMS-VTD-002, AMS-TER-001）— 已解决

**原问题**：数据库中未找到独立的分销商列表表。

**解决（2026-03-30 重新查询）**：
从 `composition_allocate` JOIN `composition_allocate_detail` 获取到 7 个分销商：

> **表结构变更说明**：`composition_allocate_detail` 表不再包含 `team_name`/`team_id` 列，分销商信息需通过 `allocate_id` 关联 `composition_allocate` 父表获取。

| 分销商名称 | team_id | 未解约作品数 | 备注 |
|-----------|---------|:----------:|------|
| 境外--YUJA--002 | 1988137461068951552 | 582 | |
| 马小强 | 1983420712272539648 | 579 | |
| **HELLO BEAR** | **1988839584685428736** | **510** | **JLB登录账号对应团队** |
| 境外--YUJA--001 | 1985522863929118720 | 506 | |
| 茶萃礼 | 1988526061061218304 | 500 | |
| 我的运气爆棚 | 1988520080772243456 | 479 | |
| 德鲁特家族 | 1983425590982094848 | 7 | |

**推荐使用**：**HELLO BEAR**（VTD-002 分销商来源 + TER-001 解约单分销商），原因：
- 该团队对应 JLB 登录账号 Yancz-cool@outlook.com
- 创建分销商来源任务单后 MQ 会同步到 JLB，支撑 JLB-VM-001/002 和 E2E-001

**HELLO BEAR 已分配作品（前10条，共510条活跃）**：

| 作品ID | 作品名称 |
|--------|---------|
| 16425 | 版权采买作品001 |
| 20004 | 我叫阮甜甜 |
| 20006 | 麻辣婆媳逗 |
| 77353 | 整个娱乐圈都在等我们离婚 |
| 77360 | 被离婚后我成为了千亿总裁 |
| 77369 | 我的合约老婆 |
| 77581 | 流浪之家 |
| 86439 | 山之影落烟火圆 |
| 86444 | 植物大战僵尸战棋 |

> **注意**：亚历山大moto**未分配给任何分销商**，不能用于分销商来源任务单。

### 7.2 "审核拒绝"任务单（AMS-VTD-006）— 新增替代方案

**问题**：当前环境中不存在"审核拒绝"状态的任务单。V2603300001 已完成，V2603300002 为 CREATE_FAILED。

**解决方案**（两个选项）：
- **方案A**（复用现有数据）：V2603300002 状态为 CREATE_FAILED，PRD §3.1.5 说明"创建失败编辑流程与审核拒绝相同"，可直接用于 VTD-006 编辑+重新提交验证
- **方案B**（产出审核拒绝数据）：先执行 AMS-VTD-001 创建新任务单 → 等待异步变为"待审核" → 审核"不通过" → 产出"审核拒绝"任务单
- **推荐**：**方案A**（减少前置步骤，V2603300002 已存在且状态符合）

### 7.3 Excel导入模板（AMS-VTD-002）— 需更新视频ID

**问题**：需要构造包含合法视频ID的 Excel 文件。原使用的 380Ns7AJ0O4 已被 V2603300001 视频删除处理，V2603300002 用该 ID 创建时失败（"无权限或未找到发布通道"）。

**解决方案**：
- 执行步骤中先点击"下载导入模板"获取模板格式
- 需要从 HELLO BEAR 分配的作品中找到一个有真实 YouTube 视频的作品，获取其视频ID
- **候选作品**：版权采买作品001 (id=16425), 我叫阮甜甜 (id=20004), 麻辣婆媳逗 (id=20006) 等
- **备选方案**：若无法提前确认视频ID，可在 AMS 前端搜索 HELLO BEAR 下的作品，查看其绑定的海外频道和视频列表

### 7.4 剧老板端同步数据（JLB-VM-001/002, AMS-E2E-001）

**问题**：需确认已完成的任务单数据是否已通过 MQ 同步到剧老板。

**当前状态（2026-03-30 16:30）**：
- V2603300001 已完成但**非分销商来源**（task_source=null），不会触发 MQ 同步到剧老板
- V2603300002 创建失败，未进入审核/执行流程
- dispatcher 队列有 3 条已完成记录（均来自 V2603300001，非分销商来源）
- 剧老板端大概率**无视频下架数据**

**解决方案**：
- 需通过 AMS-VTD-002 重新创建一条分销商来源（HELLO BEAR）的任务单（使用新的视频ID）
- 走完审核流程后，通过 RocketMQ 同步到剧老板
- 然后再执行 JLB-VM-001/002 和 AMS-E2E-001

### 7.5 剧老板前端nginx配置（已修复）

**问题**：`distribute.test.xiaowutw.com` 的 nginx 配置缺少 `/appApi/` 和 `/gateway/` 代理规则，导致前端无法调用后端 API（返回 405）。

**根因**：204 服务器上 nginx 的 `frontend-distribute` 配置仅有 SPA 静态文件服务，缺少反向代理规则。前端 JS 代码使用相对路径 `/appApi/*` 和 `/gateway/*` 发起请求。

**修复（2026-03-27）**：
- 在 `/etc/nginx/sites-enabled/frontend-distribute` 中添加：
  - `location /appApi/` -> `proxy_pass http://127.0.0.1:10251/appApi/;`（JLB 后端）
  - `location /gateway/` -> `proxy_pass http://172.16.24.200:8011/;`（网关）
- 原始配置已备份至 `/tmp/frontend-distribute.bak`
- nginx reload 后验证通过：登录 API 返回 200 + JWT token

### 7.6 亚历山大moto作品复用限制（AMS-VTD-001）— 已解决

**问题（2026-03-30 更新）**：V2603300001 已使用 亚历山大moto（composition_id=19584）创建并**已完成**。该作品下的 3 个视频（380Ns7AJ0O4, 8osKZ-x8QXE, _ivssajl8C0）均已被 VIDEO_DELETE 处理完成。

**数据库验证结果**：
- 亚历山大moto关联的 4 个频道中，仅 UClDJc5bJntyxdJoHB94GVgg (@林) 频道有已上传视频
- 其他 3 个频道（604292219431376/哈哈哈历险、UC3OASOStqIRqtk7awPoOkEw/新开频道、UCtrVMtqUt5ICmjZeYsoafxA/@@@杨宇月@@@）均 **0 个已上传视频**
- @林 频道总共有 **56 个不同的 YouTube 视频**，其中 3 个已被下架，仍有 **53 个可用**
- V2603300001 已完成（COMPLETED），**亚历山大moto不再有"未完成任务单"的重复创建限制**

**结论**：**亚历山大moto + @林 频道可直接复用**。V2603300001 已完成不会阻塞新任务单创建，@林 频道上还有 53 个未被下架的视频可供系统自动发现。

### 7.7 VTD-002 视频ID数据问题 — 已解决

**问题（2026-03-30 新增）**：V2603300002 使用 380Ns7AJ0O4 按视频ID创建，状态为 CREATE_FAILED，失败原因"无权限或未找到发布通道"。该视频已在 V2603300001 中被删除。

**根因分析**：
- 380Ns7AJ0O4 在 V2603300001 中以 VIDEO_DELETE 方式处理完成（14:10:47），视频已从 YouTube 删除
- V2603300002 (15:34:45) 尝试用 VIDEO_PRIVACY 处理该视频时，YouTube 上已找不到该视频

**解决方案**（已从数据库验证）：
从 `dispatcher.video_order` 表中查到 @林 频道 (UClDJc5bJntyxdJoHB94GVgg, team=HELLO BEAR) 上有 **20+ 个可用的 YouTube 视频ID**（publish_status=finished，已排除 3 个被下架的视频）。

**VTD-002 推荐使用的视频ID（前5个）**：

| 序号 | YouTube 视频ID | 频道 | 发布状态 |
|:---:|---------------|------|---------|
| 1 | **zdNh8rzITgA** | UClDJc5bJntyxdJoHB94GVgg (@林) | publish_success |
| 2 | MwmEP7ls_rA | UClDJc5bJntyxdJoHB94GVgg (@林) | publish_success |
| 3 | jxnPH08ktSQ | UClDJc5bJntyxdJoHB94GVgg (@林) | publish_success |
| 4 | 4tunT7cwLHE | UClDJc5bJntyxdJoHB94GVgg (@林) | publish_success |
| 5 | oPgr_VArnzk | UClDJc5bJntyxdJoHB94GVgg (@林) | publish_success |

> **VTD-002 Excel 模板填写**：视频ID=`zdNh8rzITgA`（或上述任一），海外频道ID=`UClDJc5bJntyxdJoHB94GVgg`。作品名称和CP名称由系统在"创建中"异步展开时自动匹配（source_type=local_upload，无预设 content_source）。

---

## 8. 推荐执行顺序（2026-03-31 第三次更新）

> **冒烟测试已完成**（7 PASS / 0 FAIL / 4 BLOCKED / 1 待人工验证）。以下为后续功能测试的推荐执行顺序。
>
> **当前环境**：
> - 8 条任务单：3条 COMPLETED + 4条 PENDING_REVIEW + 1条 CREATE_FAILED
> - dispatcher 队列：3条 completed + 6条 filtered
> - 分销商：HELLO BEAR（510个活跃作品）
> - **可用作品**：6个可用作品（10个可用视频ID），详见 §10

| 序号 | 步骤 | 推荐数据 | 说明 |
|:---:|------|---------|------|
| 1 | **AMS-VTD-001** 按作品创建-视频删除 | 蓝天上的流云(215579)，3个全新视频 | 可立即执行 |
| 2 | [等待] 异步展开 ~30s | - | 等待状态变为"待审核" |
| 3 | **AMS-VTD-003** 审核通过（新产出的任务单） | 步骤1产出的任务单 | 审核流程验证 |
| 4 | **AMS-VTD-002** 按视频ID创建-视频私享 | HELLO BEAR + zdNh8rzITgA | 分销商来源任务 |
| 5 | [等待] 异步展开 ~30s | - | 等待状态变为"待审核" |
| 6 | **AMS-VTD-007** 审核视频私享任务 | 步骤4产出的任务单 | 视频私享差异化流转 |
| 7 | **AMS-TER-001** 创建解约单联动 | HELLO BEAR + 任意未解约作品 | 解约单联动验证 |
| 8 | [等待] MQ同步到剧老板 | - | 视频私享任务完成后同步 |
| 9 | **JLB-VM-001** 剧老板列表查看 | JLB: Yancz-cool@outlook.com | 数据同步验证 |
| 10 | **JLB-VM-002** 剧老板进度查看 | 同上 | 详情验证 |
| 11 | **AMS-E2E-001** 跨系统端到端 | AMS + JLB 联合验证 | 全链路验证 |

> **已完成用例**（冒烟测试中已通过，可用现有数据直接回归）：
> - VTD-004: V2603300001/V2603300005/V2603300007（已完成任务详情）
> - VTD-005: 8条任务单覆盖3种状态（列表搜索筛选）
> - VTD-006: V2603300003 已重测通过（编辑+重提交）
> - VTD-008: V2603300001 + dispatcher 3条completed（执行队列）

---

## 9. 数据库表结构参考

> 第二次查询过程中发现的实际列名与文档记载不一致之处，记录供后续参考。

### 9.1 silverdawn_ams.video_takedown_task

关键列：`id, code, status, takedown_reason, takedown_description, process_method, deadline_date, create_source, create_type, task_source, team_id, team_name, terminate_id, auditor_id, audit_opinion, audit_time, create_fail_reason, retry_count, created_at, updated_at`

> 注意：列名为 `code`（非 `task_code`）、`created_at`（非 `create_time`）、`takedown_description`（非 `takedown_desc`）

### 9.2 silverdawn_ams.video_takedown_task_composition

关键列：`id, task_id, composition_id, composition_name, cp_name, register_channel_ids, expand_status, fail_reason, video_count, created_at, updated_at`

### 9.3 silverdawn_ams.video_takedown_task_detail

关键列：`id, task_id, video_id, video_title, pipeline_id, composition_id, composition_name, cp_id, cp_name, register_channel_id, operation_type, operation_team, process_method, video_status, status_detail, execute_time, complete_time, created_at, updated_at`

### 9.4 silverdawn_ams.composition_terminate

关键列：`id, code, terminate_date, terminate_type, reason, team_id, team_name, created_at, updated_at, created_user_id, updated_user_id, need_takedown, takedown_reason, takedown_description, process_method, takedown_deadline_date, takedown_task_code`

> 注意：列名为 `code`（非 `terminate_code`），无 `deleted` 列

### 9.5 silverdawn_ams.composition_allocate_detail

关键列中 `terminate_status`（非 `is_terminate` 或 `deleted`）用于标记解约状态（0=未解约，1=已解约）

---

*更新时间：2026-03-31（第五次更新：限定双频道数据，橙汁+@林，10作品19视频）*

---

## 10. 已验证可用作品数据链（视频下架测试）

> **数据来源**: 通过数据库交叉验证 `ams_publish_channel` + `dispatcher.video_order` 确认  
> **验证时间**: 2026-03-31（第五次更新：限定双频道数据）  
> **核心发现**: `ams_publish_channel.sign_channel_name` = 作品名称（composition name），这是作品关联到频道/pipeline/视频的关键纽带

> **重要约束**: 后续所有测试套件（冒烟/功能/回归/集成）**只能**使用以下两个 YT 频道对应的数据：
> 1. `UClDJc5bJntyxdJoHB94GVgg` — **@林**
> 2. `UCA17JOb1Bo5YQdggQwJN20Q` — **橙汁的测试频道-0627-02**
>
> 不在这两个频道上的作品/视频，即使数据链完整，也**不应**用于测试。

### 10.1 频道 A：@林 (`UClDJc5bJntyxdJoHB94GVgg`)

**可用作品 — 6个，13个可用视频：**

| 作品名称 | composition_id | pipeline_id | YouTube视频ID | 分配分销商 | 备注 |
|---------|:-----------:|-------------|--------------|-----------|------|
| 我要娶的不是你 | 88781 | 9e35af9750ac40308549ce0e68071b8a | avuifVWuW3o | HELLO BEAR, 境外--YUJA--001, 境外--YUJA--002, 我的运气爆棚, 茶萃礼, 马小强 | 6个视频，多分销商 |
| 我要娶的不是你 | 88781 | 9e35af9750ac40308549ce0e68071b8a | CMTVfxaXlnI | 同上 | |
| 我要娶的不是你 | 88781 | 9e35af9750ac40308549ce0e68071b8a | PDtHvdP__fA | 同上 | |
| 我要娶的不是你 | 88781 | 9e35af9750ac40308549ce0e68071b8a | vYMrouQX_P8 | 同上 | |
| 我要娶的不是你 | 88781 | 9e35af9750ac40308549ce0e68071b8a | YUU8ZjcTYX8 | 同上 | |
| 我要娶的不是你 | 88781 | 9e35af9750ac40308549ce0e68071b8a | YYYFyc0LP6H | 同上 | |
| 蓝天上的流云 | 215579 | c8eddbc2934b45c39cf3f5a92521aa2d | yLCvR_OZFyA | HELLO BEAR | 3个视频 |
| 蓝天上的流云 | 215579 | 52d62e19f7ea421e864bb23dcb17c5a8 | fIFvE-W5Azc | HELLO BEAR | |
| 蓝天上的流云 | 215579 | f11f77f9d0b341608a69086d65c0f1ba | QhBuiHHEkr4 | HELLO BEAR | |
| 方方^ | 99351 | cd36d4d68584431c99edb8da099a0084 | 4tunT7cwLHE | HELLO BEAR | 特殊字符作品名 |
| 庄皓文 | 99352 | 816986667254417386ca62e8960e64cf | oPgr_VArnzk | HELLO BEAR | |
| 素什锦 | 99353 | fbc9ae71f03a49cbb526ab2fff95a12e | _q6n4G_khkI | HELLO BEAR | |
| 亚历山大moto | 99354 | 65f6516120834e2f9dfa12db856bfec1 | mTpLgFgLlV8 | HELLO BEAR | |

**不可用作品（视频已全部下架）：**

| 作品名称 | composition_id | YouTube视频ID | 下架任务单 | 说明 |
|---------|:-----------:|--------------|-----------|------|
| 神医探案 | 88641 | ~~zdNh8rzITgA~~ | V2603310003 | 3个视频全被 VIDEO_PRIVACY |
| 神医探案 | 88641 | ~~MwmEP7ls_rA~~ | V2603310003 | |
| 神医探案 | 88641 | ~~jxnPH08ktSQ~~ | V2603310003 | |
| D的气泡水 | 19584 | ~~380Ns7AJ0O4~~ | V2603300001/05/07 | 被 VIDEO_DELETE 多次处理 |

### 10.2 频道 B：橙汁的测试频道-0627-02 (`UCA17JOb1Bo5YQdggQwJN20Q`)

**可用作品 — 6个，6个可用视频：**

| 作品名称 | composition_id | pipeline_id | YouTube视频ID | 分配分销商 | 备注 |
|---------|:-----------:|-------------|--------------|-----------|------|
| 庄皓文 | 99352 | 0f85fb890af94747af8b8ffda09e18ea | DWx-MYvnJ9c | HELLO BEAR | 同时在@林有1个视频 |
| 素什锦 | 99353 | 99b4559576c749c181c5acaf22813c68 | dNiVyRtec1A | HELLO BEAR | 同时在@林有1个视频 |
| 周可可很可以 | 100960 | 100e2b156e55414381d981f313d450a7 | v72tBaFp-Ho | HELLO BEAR | 仅此频道 |
| 福喆木艺 | 100959 | be15012f2220481292cc8305f7af9993 | KbkyzTzm-1o | HELLO BEAR | 仅此频道 |
| 视听：乡村阿泰 | 215595 | 6f789f23f26c4303b253e3fb35d6f47a | 9gmorQqG4b8 | 境外--YUJA--001 | 仅此频道 |
| 视听：吾乃肆玖 | 215587 | 475acc60fd3b4217b5eb8dbdc98cc629 | QD0C9KgeALc | 境外--YUJA--001 | 仅此频道 |

### 10.3 按作品汇总（快速查阅）

| 作品名称 | composition_id | 所在频道 | 可用视频数 | 视频ID列表 | 推荐用途 |
|---------|:-----------:|---------|:-------:|-----------|---------|
| **我要娶的不是你** | 88781 | @林 | 6 | avuifVWuW3o, CMTVfxaXlnI, PDtHvdP__fA, vYMrouQX_P8, YUU8ZjcTYX8, YYYFyc0LP6H | VTD-002 按视频ID创建（视频丰富，多分销商） |
| **蓝天上的流云** | 215579 | @林 | 3 | yLCvR_OZFyA, fIFvE-W5Azc, QhBuiHHEkr4 | VTD-001 按作品创建（视频较多） |
| **庄皓文** | 99352 | @林 + 橙汁 | 2 | oPgr_VArnzk(@林), DWx-MYvnJ9c(橙汁) | 跨频道作品测试 |
| **素什锦** | 99353 | @林 + 橙汁 | 2 | _q6n4G_khkI(@林), dNiVyRtec1A(橙汁) | 跨频道作品测试 |
| **方方^** | 99351 | @林 | 1 | 4tunT7cwLHE | 特殊字符作品名测试 |
| **亚历山大moto** | 99354 | @林 | 1 | mTpLgFgLlV8 | 单视频作品测试 |
| **周可可很可以** | 100960 | 橙汁 | 1 | v72tBaFp-Ho | 单视频、仅橙汁频道 |
| **福喆木艺** | 100959 | 橙汁 | 1 | KbkyzTzm-1o | 单视频、仅橙汁频道 |
| **视听：乡村阿泰** | 215595 | 橙汁 | 1 | 9gmorQqG4b8 | 境外--YUJA--001 分销商 |
| **视听：吾乃肆玖** | 215587 | 橙汁 | 1 | QD0C9KgeALc | 境外--YUJA--001 分销商 |

> **总计**: 10 个可用作品，19 个可用视频（@林频道 13个 + 橙汁频道 6个）。  
> 另有 神医探案(88641) 3个视频 + D的气泡水(19584) 1个视频已下架，不可复用。

### 10.4 数据链路关系说明

```
数据链路：作品 → 发布通道 → 视频

ams_composition.name (作品名)
  ↕ 通过 sign_channel_name 匹配
ams_publish_channel (发布通道)
  ├── sign_channel_name = 作品名
  ├── register_channel_id = YouTube频道ID
  ├── pipeline_id = 管道ID（视频下架核心字段）
  └── status = 1 (有效)
       ↓ 通过 target_channel_id + pipeline_id 关联
dispatcher.video_order (视频订单)
  ├── target_channel_id = register_channel_id
  ├── pipeline_id = pipeline_id
  ├── upload_video_id = YouTube视频ID
  └── publish_status = 'finished' (已发布)
```

### 10.5 用例数据推荐（2026-03-31 第二次更新 — 双频道限定版）

> 以下推荐均限定在 @林 + 橙汁的测试频道-0627-02 两个频道范围内。

| 用例编号 | 推荐作品 | 推荐视频ID | 推荐频道 | 理由 |
|---------|---------|-----------|---------|------|
| **AMS-VTD-001** (按作品创建-视频删除) | **蓝天上的流云** (215579) | 系统自动展开(3个) | @林 | 3个全新视频，HELLO BEAR 分销商 |
| **AMS-VTD-001 备选** | 我要娶的不是你 (88781) | 系统自动展开(6个) | @林 | 视频最多，多分销商验证 |
| **AMS-VTD-002** (按视频ID创建-视频私享) | **我要娶的不是你** (88781) | **avuifVWuW3o** | @林 | HELLO BEAR分销商，6个视频可选 |
| **AMS-VTD-002 备选** | 庄皓文 (99352) | **DWx-MYvnJ9c** | 橙汁 | 橙汁频道备选 |
| **AMS-VTD-003** (审核通过) | - | - | - | 使用已有 V2603300004/V2603300009 |
| **AMS-VTD-004** (查看已完成详情) | - | - | - | 使用已有 V2603300001 |
| **AMS-VTD-005** (列表搜索/筛选) | - | - | - | 全部已有任务单覆盖 |
| **AMS-VTD-006** (编辑重提交) | - | - | - | V2603300006(PENDING) 或 V2603300002(FAILED) |
| **AMS-VTD-007** (审核视频私享) | - | - | - | 依赖 VTD-002 产出 |
| **AMS-VTD-008** (执行队列) | - | - | - | V2603300001 dispatcher 3条completed |
| **AMS-TER-001** (解约单联动) | 方方^/亚历山大moto 等 | - | @林 | HELLO BEAR 分销商 |
| **单视频场景** | 方方^/亚历山大moto/周可可很可以/福喆木艺 | 各1个视频 | 各频道 | 边界测试 |
| **跨频道场景** | 庄皓文/素什锦 | 同一作品两个频道各1个 | @林+橙汁 | 多频道验证 |
| **非HELLO BEAR分销商** | 视听：乡村阿泰/视听：吾乃肆玖 | 各1个视频 | 橙汁 | 境外--YUJA--001 分销商 |

> **注意事项**:
> - 神医探案(88641) 3个视频已被 V2603310003 全部 VIDEO_PRIVACY 下架，不可复用
> - D的气泡水(19584) 视频已被 VIDEO_DELETE 删除，不可复用
> - 我要娶的不是你(88781) 替代神医探案作为 VTD-002 推荐数据（视频更丰富，同样有 HELLO BEAR 分配）

### 10.6 验证SQL（供测试执行时使用）

```sql
-- ==========================================
-- 1. 查询任务单状态（快速）
-- ==========================================
SELECT t.code, t.status, t.process_method, t.task_source, t.takedown_reason
FROM silverdawn_ams.video_takedown_task t
ORDER BY t.code;

-- ==========================================
-- 2. 查询任务单完整信息（含作品+视频数）
-- ==========================================
SELECT t.code, t.status, t.process_method,
       c.composition_name, c.video_count, c.expand_status
FROM silverdawn_ams.video_takedown_task t
LEFT JOIN silverdawn_ams.video_takedown_task_composition c ON t.id = c.task_id
ORDER BY t.code;

-- ==========================================
-- 3. 查询任务单视频明细
-- ==========================================
SELECT t.code, d.video_id, d.video_status, d.process_method, 
       d.composition_name, d.register_channel_id, d.pipeline_id
FROM silverdawn_ams.video_takedown_task t
JOIN silverdawn_ams.video_takedown_task_detail d ON t.id = d.task_id
WHERE t.code = '{TASK_CODE}'
ORDER BY d.video_id;

-- ==========================================
-- 4. 查询两个限定频道的作品发布通道
-- ==========================================
SELECT pc.sign_channel_name AS composition_name,
       pc.register_channel_id, pc.register_channel_name,
       pc.pipeline_id, pc.status
FROM silverdawn_ams.ams_publish_channel pc
WHERE pc.register_channel_id IN ('UClDJc5bJntyxdJoHB94GVgg', 'UCA17JOb1Bo5YQdggQwJN20Q')
  AND pc.status = 1
ORDER BY pc.register_channel_id, pc.sign_channel_name;

-- ==========================================
-- 5. 查询两个限定频道的已发布视频（19个可用）
-- ==========================================
SELECT vo.upload_video_id AS youtube_video_id,
       vo.target_channel_id,
       vo.pipeline_id,
       vo.publish_status
FROM dispatcher.video_order vo
WHERE vo.target_channel_id IN ('UClDJc5bJntyxdJoHB94GVgg', 'UCA17JOb1Bo5YQdggQwJN20Q')
  AND vo.pipeline_id IN (
    -- @林 频道
    '9e35af9750ac40308549ce0e68071b8a',  -- 我要娶的不是你 (6个视频)
    'c8eddbc2934b45c39cf3f5a92521aa2d',  -- 蓝天上的流云
    '52d62e19f7ea421e864bb23dcb17c5a8',  -- 蓝天上的流云
    'f11f77f9d0b341608a69086d65c0f1ba',  -- 蓝天上的流云
    'cd36d4d68584431c99edb8da099a0084',  -- 方方^
    '816986667254417386ca62e8960e64cf',  -- 庄皓文
    'fbc9ae71f03a49cbb526ab2fff95a12e',  -- 素什锦
    '65f6516120834e2f9dfa12db856bfec1',  -- 亚历山大moto
    -- 橙汁频道
    '0f85fb890af94747af8b8ffda09e18ea',  -- 庄皓文
    '99b4559576c749c181c5acaf22813c68',  -- 素什锦
    '100e2b156e55414381d981f313d450a7', -- 周可可很可以
    'be15012f2220481292cc8305f7af9993',  -- 福喆木艺
    '6f789f23f26c4303b253e3fb35d6f47a',  -- 视听：乡村阿泰
    '475acc60fd3b4217b5eb8dbdc98cc629'   -- 视听：吾乃肆玖
  )
  AND vo.publish_status = 'finished';

-- ==========================================
-- 6. 查询某个视频ID是否已被下架
-- ==========================================
SELECT vtd.video_id, vtd.video_status, vtd.process_method, t.code AS task_code
FROM silverdawn_ams.video_takedown_task_detail vtd
JOIN silverdawn_ams.video_takedown_task t ON t.id = vtd.task_id
WHERE vtd.video_id = '{VIDEO_ID}'
ORDER BY t.code;

-- ==========================================
-- 7. 查询下架执行队列状态
-- ==========================================
SELECT q.task_id, q.video_id, q.process_method, q.queue_status,
       q.execute_time, q.complete_time, q.status_detail
FROM dispatcher.video_takedown_queue q
ORDER BY q.id DESC;

-- ==========================================
-- 8. 查询分销商及其作品分配数
-- ==========================================
SELECT ca.team_name, ca.team_id, COUNT(cad.id) AS composition_count
FROM silverdawn_ams.composition_allocate ca
JOIN silverdawn_ams.composition_allocate_detail cad ON ca.id = cad.allocate_id
WHERE cad.terminate_status = 0
GROUP BY ca.team_name, ca.team_id
ORDER BY composition_count DESC;

-- ==========================================
-- 9. 查询解约单（含联动下架标记）
-- ==========================================
SELECT ct.code, ct.terminate_type, ct.team_name, ct.need_takedown,
       ct.takedown_task_code, ct.takedown_reason
FROM silverdawn_ams.composition_terminate ct
ORDER BY ct.created_at DESC
LIMIT 10;
```
