# 视频下架任务处理逻辑

---

## 一、按视频ID导入（BY_VIDEO_ID）

### 1.0 接口参数校验（同步，请求入口）

`POST /video-takedown/task/create-by-video-id`，对应 `TakedownCreateByVideoIdVO`：

| 字段 | 注解 | 说明 |
|------|------|------|
| takedownReason | @NotBlank | 下架原因，必填 |
| takedownNote | @Size(max=100) | 下架说明，选填，最多100字符 |
| processMethod | @NotBlank | 处理方式，VIDEO_DELETE / VIDEO_PRIVACY |
| deadlineDate | @NotBlank | 截止执行日期，格式 yyyy-MM-dd |
| taskSource | @NotBlank | 任务来源，DISTRIBUTOR / OPERATION_TEAM |
| teamId | 无注解 | taskSource=DISTRIBUTOR 时由业务逻辑取值 |
| operationTeam | 无注解 | taskSource=OPERATION_TEAM 时由业务逻辑取值 |
| compositions | @NotEmpty | 作品列表，不能为空 |

> **注**：`compositions` 列表元素类型为 `CompositionItemVO`，其内部字段 `compositionName`/`cpName` 标注了 `@NotBlank`，但父 VO 未加 `@Valid`，**Spring 不会级联校验**，这两个注解对该接口无效。

**Service 层同步校验**（`validateDeadlineDate`，VO 校验通过后执行）：
- deadlineDate 格式非 yyyy-MM-dd → 抛出 `IllegalArgumentException`
- deadlineDate 不在当天 ~ 当天+6天范围内 → 抛出 `IllegalArgumentException`

### 1.1 导入阶段（同步校验，拦截后不入库）

`POST /video-takedown/upload`，对应 `VideoTakedownExcelServiceImpl`：

**文件级校验**（优先于行级，任一失败直接返回，resultCode=1）：

| # | 校验项 | 说明 |
|---|--------|------|
| 1 | 文件非空 | 文件为空或 null → 报错 |
| 2 | 文件格式 | 后缀须为 .xlsx 或 .xls |
| 3 | 文件大小 | 不超过 5M |
| 4 | 模板列数 | 第1行须有4个非空列（视频ID/作品名称/CP名称/注册频道ID），列数不符报"导入模板错误" |
| 5 | 有效数据 | 去除空行后若无数据 → 报"文件无有效数据，请填写数据后重新上传" |
| 6 | 条数上限 | 去除空行后超过1000条 → 报"导入失败，单次导入上限1000条" |

**逐行校验**（`validateVideoIdRow`，字段已自动 trim，resultCode=2）：

| # | 校验项 | 触发条件 | 报错提示 |
|---|--------|---------|---------|
| 1 | 视频ID必填 | 视频ID为空 | 【视频ID】不能为空 |
| 2 | 视频ID格式 | 视频ID不为空但长度不等于11位 | 【视频ID】格式错误 |
| 3 | 作品名称必填 | 作品名称为空 | 【作品名称】不能为空 |
| 4 | 海外频道ID必填 | 海外频道ID为空 | 【海外频道ID】不能为空 |
| 5 | 视频ID批内重复 | 同批次内相同视频ID（所有重复行均报，含第一条） | 【视频ID】存在重复行 |
| 6 | 视频ID执行中任务 | 该视频ID已在执行中任务中存在 | 【视频ID】存在执行中的任务单 |
| 7 | 作品存在性 | 系统中不存在该作品名称 | 【作品名称】不存在 |
| 8 | CP名称匹配 | CP名称有值，但与作品不匹配 | 【CP名称】不存在 |
| 9 | 海外频道ID存在性 | 系统中不存在该频道ID | 【海外频道ID】不存在 |
| 10 | 权限校验 | 频道存在但无权限（报错同上，见下） | 【海外频道ID】不存在 |

**权限校验细则**（步骤10，仅在频道存在且 taskSource 非空时触发）：

| taskSource | 校验逻辑 |
|-----------|---------|
| DISTRIBUTOR | 通过 `composition_allocate` 校验该分销商是否有该作品的分配权；compositionId 无法解析时不报错 |
| OPERATION_TEAM | 通过 `sign_channel.operation_team` 校验频道是否归属该运营团队；channelId 为 null 或 SignChannel 不存在时视为**有权限**（容错） |

### 1.2 提交阶段（异步执行，结果写入 detail）

触发时机：调用提交接口后异步执行 `asyncExpandByVideoId`。

**遍历每个视频ID，依次执行 `processVideoItem`：**

| # | 处理项 | 通过 | 失败 detail.statusDetail |
|---|--------|------|--------------------------|
| 1 | 作品+CP 系统存在性 | 继续 | `作品不存在` |
| 2 | 发布通道存在性+权限（`findPublishChannelWithPermission`） | 取第一条发布通道记录 | `无权限或未找到发布通道` |
| 2a | — DISTRIBUTOR | 通过 `composition_allocate` 校验分配权 | 无权限 |
| 2b | — OPERATION_TEAM | 通过 `sign_channel.operation_team` 匹配 deptId；channelId 为 null 或 SignChannel 不存在时视为有权限 | 无权限 |
| 3 | 执行中任务 | 无 → 继续 | `视频已有执行中任务` |
| 4 | 已通过删除任务下架 | 未删除 → 继续 | `视频已删除，无法再处理` |
| 5 | 已通过转私任务处理 | 未转私 → 继续 | `视频已转私，无法再处理`（**仅 VIDEO_PRIVACY 时校验**） |

全部通过 → 写入 **PENDING** detail

**任务状态判定（`determineTaskStatus`）：**

| 条件 | 任务状态 |
|------|---------|
| 有 EXPAND_FAILED 占位记录 | CREATING（等待补偿任务重试） |
| 无 PENDING（全部校验失败） | CREATE_FAILED |
| 有 PENDING | PENDING_REVIEW |

---

## 二、按作品导入（BY_COMPOSITION）

### 2.0 接口参数校验（同步，请求入口）

`POST /video-takedown/task/create-by-composition`，对应 `TakedownCreateByCompositionVO`：

| 字段 | 注解 | 说明 |
|------|------|------|
| takedownReason | @NotBlank | 下架原因，必填 |
| takedownNote | @Size(max=100) | 下架说明，选填，最多100字符 |
| processMethod | @NotBlank | 处理方式，VIDEO_DELETE / VIDEO_PRIVACY |
| deadlineDate | @NotBlank | 截止执行日期，格式 yyyy-MM-dd |
| compositions | @NotEmpty | 作品列表，不能为空 |

> **注**：无 taskSource / teamId / operationTeam 字段；`compositions` 元素嵌套校验同一节说明，`@Valid` 未加，不级联。

**Service 层同步校验**（同 1.0，`validateDeadlineDate`）：
- deadlineDate 格式非 yyyy-MM-dd → 抛出 `IllegalArgumentException`
- deadlineDate 不在当天 ~ 当天+6天范围内 → 抛出 `IllegalArgumentException`

### 2.1 导入阶段（同步校验，拦截后不入库）

`POST /video-takedown/upload`，对应 `VideoTakedownExcelServiceImpl`：

**文件级校验**（resultCode=1）：

| # | 校验项 | 说明 |
|---|--------|------|
| 1 | 文件非空 | 文件为空或 null → 报错 |
| 2 | 文件格式 | 后缀须为 .xlsx 或 .xls |
| 3 | 文件大小 | 不超过 5M |
| 4 | 模板列数 | 第1行须有3个非空列（作品名称/CP名称/海外频道ID），列数不符报"导入模板错误" |
| 5 | 有效数据 | 去除空行后若无数据 → 报"文件无有效数据，请填写数据后重新上传" |
| 6 | 条数上限 | 去除空行后超过500条 → 报"导入失败，单次导入上限500条" |

**逐行校验**（`validateCompositionRow`，字段已自动 trim，resultCode=2）：

| # | 校验项 | 触发条件 | 报错提示 |
|---|--------|---------|---------|
| 1 | 作品名称必填 | 作品名称为空 | 【作品名称】不能为空 |
| 2 | 批内重复 | 作品名称+CP名称+海外频道ID 组合重复（所有重复行均报，含第一条） | 【作品名称】存在重复行 |
| 3 | 作品存在性 | 系统中不存在该作品名称 | 【作品名称】不存在 |
| 4 | CP名称匹配 | CP名称有值，但系统中该作品无此CP | 【CP名称】不存在 |
| 5 | 作品+CP唯一性 | CP名称有值，但 作品+CP 在系统中有多条记录 | 【作品名称+CP】存在多条数据 |
| 6 | 作品唯一性（无CP） | CP名称为空，但系统中该作品有多条记录 | 【作品名称】存在多条数据 |
| 7 | 海外频道ID格式 | 有值时：某个ID不满足 UC开头+24位（支持顿号/中英文逗号分隔多个） | 【海外频道ID】格式错误 |
| 8 | 海外频道ID存在性 | 格式正确但系统中不存在 | 【海外频道ID】不存在：xxx、yyy |
| 9 | 发布通道校验 | **仅前8项全部无错时触发**（见下表） | 详见下表 |

**发布通道校验细则**（步骤9）：

| 场景 | 校验逻辑 | 报错提示 |
|------|---------|---------|
| 海外频道ID为空 | 作品在 publish_channel 中无绑定发布通道（type=COMPOSITION，status=IN_THE_CONTRACT） | 作品无绑定海外频道 |
| 海外频道ID有值 | 对格式+存在性均通过的频道逐个校验；**至少一个频道（有发布通道且配置了 pipelineId）通过则整行通过，全部失败才报错** | 【海外频道ID】未找到发布通道：xxx；或【海外频道ID】发布通道未配置pipelineId：xxx |

### 2.2 提交阶段（异步执行，结果写入 detail）

触发时机：调用提交接口后异步执行 `asyncExpandByComposition`。

**遍历每个作品，依次执行 `processCompositionItem`：**

| # | 处理项 | 通过 | 失败 detail.statusDetail |
|---|--------|------|--------------------------|
| 1 | 作品+CP 系统存在性 | 继续 | `作品不存在` |
| 2 | 绑定海外频道 | 取频道列表（registerChannelIds 为空时查全部绑定频道） | `作品无绑定海外频道` |

**遍历每个海外频道：**

| # | 处理项 | 通过 | 失败 detail.statusDetail |
|---|--------|------|--------------------------|
| 3 | 发布通道存在性 | 取发布通道列表（type=COMPOSITION，status=IN_THE_CONTRACT） | `未找到发布通道` |
| 4 | pipelineId 配置 | 过滤出有 pipelineId 的发布通道 | `发布通道未配置pipelineId` |
| 5 | 获取视频ID | 批量调用结算系统+分发系统（各一次），合并去重 | 网络/系统异常 → 写 **EXPAND_FAILED** 占位记录，等待补偿重试 |
| 5a | — pipeline 无视频 | — | 写 **FAILED**（`发布通道下无视频`），**不跳过** |

**有视频ID时，批量替换 FAILED detail：**

| # | 处理项 | 失败 detail.statusDetail |
|---|--------|----------|
| 6 | 执行中任务 | `视频已有执行中任务` |
| 7 | 已通过删除任务下架 | `视频已删除，无法再处理` |
| 8 | 已通过转私任务处理 | `视频已转私，无法再处理`（**仅 VIDEO_PRIVACY 时校验**） |

**作品展开结果回写（`updateCompositionExpandResult`）：**

| 情况 | expandStatus | videoCount |
|------|-------------|-----------|
| details 为空（兜底，不应发生） | FAILED | 0 |
| 全部 FAILED（无 EXPAND_FAILED） | FAILED | 0 |
| 有 PENDING 且有 FAILED 或 EXPAND_FAILED | PARTIAL_FAILED | PENDING 数量 |
| 全部 PENDING | SUCCESS | PENDING 数量 |

**任务状态判定（`determineTaskStatus`，同 BY_VIDEO_ID）：**

| 条件 | 任务状态 |
|------|---------|
| 有 EXPAND_FAILED 占位记录 | CREATING（等待补偿任务重试） |
| 无 PENDING（全部校验失败） | CREATE_FAILED |
| 有 PENDING | PENDING_REVIEW |

---

## 三、解约联动下架（TERMINATE_CREATE）

### 3.0 接口参数校验（同步，请求入口）

`POST /compositionTerminate/create`（使用 `@Validated`），对应 `CompositionTerminateCreateVO`：

| 字段 | 注解 | 说明 |
|------|------|------|
| teamId | @NotBlank | 分销商ID，必填 |
| teamName | @NotBlank | 分销商名称，必填 |
| terminateType | @NotBlank | 解约类型，必填 |
| reason | 无注解 | 解约原因，选填 |
| terminateDate | @NotBlank | 解约日期，格式 yyyy-MM-dd |
| terminateDetails | @NotEmpty | 解约作品列表，不能为空 |
| needTakedown | 无注解 | 是否联动视频下架，Boolean，**前端控制** |
| takedownReason | 无注解 | 下架原因，needTakedown=true 时**前端必传** |
| takedownDescription | 无注解 | 下架说明，选填，最多100字符（**前端控制**） |
| processMethod | 无注解 | 处理方式，needTakedown=true 时**前端必传** |
| takedownDeadlineDate | 无注解 | 截止执行日期，needTakedown=true 时**前端必传** |

> **注**：`terminateDetails` 元素类型 `CompositionTerminateDtCreateVO` 无任何校验注解，`deliveryDate` 字段用于解约日期比较，无格式校验。
> **注**：`batchCreate` 接口（`POST /compositionTerminate/batchCreate`）**未加 `@Validated`**，VO 注解不生效。

### 3.1 Service 层同步校验（`create` 方法）

**解约日期校验**：

遍历所有解约作品，若某条作品的 `deliveryDate != null` 且 `terminateDate < deliveryDate`，则将该作品名称收集到错误列表，最终统一抛出：

```
【作品A、作品B】的解约日期不能早于分配日期
```

（常量 `COMPOSITION_TERMINATE_EARLY = "【%s】的解约日期不能早于分配日期"`）

**联动创建下架任务**（`needTakedown=true` 时执行，`createTakedownTask`）：

1. 批量查询解约作品的 `cpName`（版权方）
2. 构建 `TakedownCreateByCompositionVO`（takedownReason / processMethod / takedownDeadlineDate / compositions）
3. 调用 `videoTakedownTaskService.createByTerminate(terminateId, vo)`：
   - 内部复用 `doCreateByComposition()`，**包含 deadlineDate 同步校验**（同 2.0）
   - createSource 标记为 `TERMINATE_CREATE`，关联 terminateId
4. 回写 `takedownTaskCode` 到解约单

### 3.2 展开阶段（异步执行）

完全复用**按作品下架**的异步展开逻辑（`processCompositionItem`），无任务来源权限校验，校验项与任务状态判定与第二节完全一致。

---

## 四、三种场景横向对比

| 维度 | 按视频（BY_VIDEO_ID） | 按作品（BY_COMPOSITION） | 内容解约（TERMINATE_CREATE） |
|------|----------------------|------------------------|----------------------------|
| 异步展开模式 | F2（逐视频处理） | F1（逐作品展开） | F1（同按作品） |
| Excel 导入 | 有，上限 1000 条 | 有，上限 500 条 | 无 Excel，直接由解约单触发 |
| 接口权限字段 | taskSource / teamId / operationTeam | 无 | 解约单携带 teamId |
| 权限校验（分销商/运营团队） | **有**（Excel 同步 + 异步阶段均校验） | 无 | 无 |
| 发布通道校验 | 仅异步阶段 | **同步（Excel）+ 异步均有** | 仅异步阶段（同按作品） |
| 视频冲突检查方式 | 逐条查询 | 批量 IN 查询 | 批量 IN 查询 |
| EXPAND_FAILED 补偿重试 | 无 | **有**（最多 3 次，超 2 小时超时） | 有（同按作品） |
| 解约日期合法性校验 | 无 | 无 | **有**（terminateDate ≥ deliveryDate） |
| createSource 标记 | — | — | TERMINATE_CREATE |

---

## 通用说明

| 类型 | detail.videoStatus | 含义 | 是否重试 |
|------|-------------------|------|---------|
| 正常待执行 | PENDING | 校验通过，等待执行 | — |
| 业务校验失败 | FAILED | 参数/权限/状态不符 | 不重试 |
| 系统/网络异常 | EXPAND_FAILED | 远程调用失败，占位记录 | 补偿任务重试 |

- 截止日期校验（当天 ~ 当天+6天）：提交接口入口**同步**校验，不在异步阶段处理
- 任务进度百分比：`(COMPLETED + FAILED) / 总数 * 100%`（两者均为终态）
