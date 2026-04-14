# AMS 系统功能清单

> 系统名称：AMS（资产管理系统，silverdawn-ams）
> 梳理版本：当前代码基线（AMS_V1.5.0 前）
> 梳理范围：AMS 后端（silverdawn-ams-server）+ AMS 前端（silverdawn-ams-web）
> 梳理方法：Controller 源码 + 前端路由 + Views 目录结构

---

## 一、系统基础信息

| 项目 | 内容 |
|------|------|
| 系统名称 | AMS（资产管理系统）|
| 后端框架 | Spring Boot 3.x / Gradle / MyBatis-Plus |
| 前端框架 | Vue 2.x / Vuetify / Vue Router（动态路由，后端下发）|
| 认证方式 | Sa-Token SSO + JWT（Bearer Token）|
| 权限模型 | 基于路由权限 + 按钮权限（后端动态下发菜单路由树）|
| 数据权限 | 运营组别/部门维度过滤 |

---

## 二、菜单模块树形结构

```
AMS
├── 首页（Home）
├── 通道管理（Thoroughfare）
│   ├── 发布通道（Release Channel）[Tab: 签约频道 | 视听作品]
│   └── 申请审核（Application Review）[Tab: YouTube | Facebook]
├── 资产账户（Asset Account）
│   ├── 频道/主页（Channel & Homepage）[Tab: YouTube | YouTube-分销]
│   └── 签约频道（Contract Channel）
├── 内容资产（Content Assets）
│   ├── 签约内容（Contract Content / 内容领用）[Tab: 视听作品 | 影视作品 | 图文作品 | 音乐作品 | 频道]
│   ├── 内容分配（Content Distribute）
│   ├── 内容解约（Content Termination）
│   └── 发布内容（Publishing Content）
├── 线索审核 / 作品审核 [Tab: 频道 | 视听作品 | 影视作品 | 图文作品 | 音乐作品] ⚠️ 线索审核已下架
├── 版权授权管理（Auth）
│   ├── 版权审核（Copyright Auth）[Tab: 版权审核 | 同名纠纷处理]
│   └── CID 纠纷处理（Dispute Auth）
├── 异常监控（Abnormal Monitoring）
│   └── 视频异常（Video Abnormality）
├── 视频管理（Video Management）✨ 本期新增
│   └── 视频下架（Video Takedown）✨ 本期新增
└── 系统设置（System Settings）
    └── 垂类配置（Vertical Category）
```

---

## 三、各模块功能详情

---

### 3.1 首页（Home）

**后端接口**：`GET /statistics/*`

| 功能点 | 接口 | 说明 |
|--------|------|------|
| 首部统计 | GET /statistics/head | 签约频道数、签约视频数、发布视频数等核心数据 |
| 签约频道总数 | GET /statistics/contractChannel | 按时间维度统计签约频道数 |
| 国外频道总数 | GET /statistics/overseaChannel | 海外频道注册数汇总 |
| 签约视频总数 | GET /statistics/contractVideo | 签约视频总量统计 |
| 发布视频总数 | GET /statistics/publishVideo | 已发布视频总量统计 |
| 签约视频时长 | GET /statistics/contractVideoDuration | 签约视频总时长统计 |
| 发布视频时长 | GET /statistics/publishVideoDuration | 发布视频总时长统计 |
| 异常报错数 | GET /statistics/errorCount | 视频异常/报错数量汇总 |

---

### 3.2 通道管理 - 发布通道（Release Channel）

**后端接口**：`POST/GET /publishChannel/*`
**前端路由**：`/views/thoroughfare/release-channel/`

**Tab 页签**：

| Tab 名称 | name 值 | 说明 |
|---------|---------|------|
| 签约频道 | `0` | 签约频道列表（默认）|
| 视听作品 | `1` | 视听作品列表 |

| 功能点 | 接口 | 校验规则 |
|--------|------|----------|
| 签约频道分页列表 | POST /signChannel/page | — |
| 数据同步（来自 CRM）| POST /signChannel/syn | voList 不能为空 |
| 同步授权延长数据 | POST /signChannel/synDelayAuth | — |
| 根据名称及平台获取列表 | GET /signChannel/list | — |
| 运营-签约频道列表 | GET /signChannel/operation/list | — |
| 全量签约频道列表 | GET /signChannel/listAll | — |
| 设置垂类 | POST /signChannel/setCategory | @RepeatSubmit 防重 |
| 签约频道分配 | POST /signChannel/allocate | — |
| 签约频道分页导出 | POST /signChannel/export | — |
| 导入签约频道/视听作品 | POST /signChannel/import | type=0 签约频道；type=1 视听作品 |
| 查询分配信息 | POST /signChannel/queryAllocationInformation | 需登录 |
| 查询国内频道详情 | GET /signChannel/queryDomesticChannelDetail | id 必填 |
| 查询国内频道详情（更多）| GET /signChannel/queryDomesticChannelDetailMore | id 必填 |
| 推送解约频道 | POST /signChannel/pushTerminationChannel | — |
| 同步三级垂类到 CRM | GET /signChannel/syncCrmCategory | @RepeatSubmit 防重 |

---

### 3.3 通道管理 - 申请审核（Application Review）

**后端接口**：`GET/POST /content/application/audit*`（复用领用申请接口）
**前端路由**：`/views/thoroughfare/application-review/`

**Tab 页签**：

| Tab 名称 | name 值 | 说明 |
|---------|---------|------|
| YouTube | `0` | YouTube 平台申请审核（默认）|
| Facebook | `1` | Facebook 平台申请审核 |

| 功能点 | 接口 | 校验规则 |
|--------|------|----------|
| 申请审核分页列表 | GET /content/application/queryPage（审核视角）| 审核人维度查询 |
| 审核申请单 | POST /content/application/audit | — |
| 导出审核列表 | POST /content/application/export | 需登录 |

---

### 3.4 资产账户 - 频道/主页（Channel & Homepage）

**后端接口**：`POST/GET /channel/*`
**前端路由**：`/views/asset-account/channel-page/`

**Tab 页签**：

| Tab 名称 | name 值 | 说明 |
|---------|---------|------|
| YouTube | `0` | YouTube 频道列表（默认）|
| YouTube-分销 | `2` | YouTube 分销频道列表 |

> 注：Facebook 主页 Tab（`name='1'`）已在代码中注释掉，暂未启用

#### 3.4.1 频道列表

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 分页列表 | POST /channel/page | — |
| YouTube 分销频道列表 | POST /channel/ytDistributionPage | 仅展示分销频道 |
| 全量频道数据 | GET /channel/all | 按 type 区分 YT/FB |
| 简单列表 | GET /channel/list | 仅返回简要字段 |
| 全量列表 | GET /channel/listAll | 无分页全量返回 |
| 根据频道名查ID | GET /channel/channelId | channelName 不能为空 |
| 根据频道ID查询（批量，最多200条）| POST /channel/getByChannelId | channelIds 不能为空 |
| 根据频道ID单条查询（对外）| GET /channel/getOneByChannelId | channelId 不能为空 |
| 根据多个频道ID查询（对外）| POST /channel/getChannelInfo | — |
| 根据频道名称模糊查询（对外）| GET /channel/search | name 不能为空，长度 ≥ 2 |
| 根据ID集合获取绑定关系 | POST /channel/findByIdList | — |
| 根据频道获取发布通道 | POST /channel/getPipelineByChannelIds | — |
| 根据条件查询频道ID列表 | POST /channel/getChannelIdsByCondition | — |

#### 3.4.2 频道设置/操作

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 新建频道/主页 | POST /channel/create | 使用 @RepeatSubmit 防重 |
| 频道详情 | POST /channel/detail | id 必填 |
| 单开/合集设置 | POST /channel/setChannel | 设为单开时：当前频道绑定发布通道 ≤ 1 条才允许 |
| 子集查询 | POST /channel/subSet | — |
| 频道配置 | POST /channel/config | 后端校验配置合法性 |
| 批量设置（已废弃）| POST /channel/batchConfig | @Deprecated |
| 同步频道信息 | POST /channel/syncChannelMessage | channelIds 不能为空 |
| 同步所有频道扩展信息 | POST /channel/syncAllChannelExt | — |
| 更新 CMS | POST /channel/updateCms | ids 不能为空 |
| 频道加入回收站 | GET /channel/recycleOverseaChannel | id 不能为空 |
| 查询海外频道详情 | GET /channel/queryOverseaChannel | id 不能为空 |
| 查询再运营中的 YT 频道 | POST /channel/queryOverseaChannelInOperation | — |
| 查询海外频道运营组别 | POST /channel/queryOverseaChannelOperationTeam | overseaChannelIds 不能为空 |
| 根据姓名查询 CP 信息 | GET /channel/queryChannelMemberByName | memberName 不能为空 |

#### 3.4.3 运营类型历史记录

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 保存运营类型历史 | POST /channel/saveOperationTypeHistory | channelId 不能为空 |
| 查询运营类型历史 | GET /channel/getOperationTypeHistory | channelId 不能为空 |
| 根据频道月份查询运营类型 | POST /channel/channelPeriodChannelTypeInfo | — |

#### 3.4.4 导入/导出

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 导出频道列表 | POST /channel/export | type=0 输出 YT 频道，type=1 输出 FB 主页 |
| 分销频道导出 | POST /channel/exportDistribution | — |
| 导出获利状态模板 | GET /channel/exportTemplate | — |
| 导入获利状态 | POST /channel/importProfit | 模板表头校验：「频道ID/主页ID*」「获利*」；获利值仅允许 Yes/No；ID 必须在系统内存在 |
| 导入频道/主页（YT）| POST /channel/ytImportChannel/{type} | type 路径参数区分类型 |
| YouTube 导入分配分销商 | POST /channel/allocateDistribution/importDistribution | — |

---

### 3.5 资产账户 - 签约频道（Contract Channel / Domestic Channel）

**后端接口**：`POST/GET /signChannel/*`
**前端路由**：`/views/asset-account/contract-channel/`

| 功能点 | 接口 | 校验规则 |
|--------|------|----------|
| 签约频道分页列表 | POST /signChannel/page | — |
| 数据同步（来自 CRM）| POST /signChannel/syn | voList 不能为空 |
| 同步授权延长数据 | POST /signChannel/synDelayAuth | — |
| 根据名称及平台获取列表 | GET /signChannel/list | — |
| 运营-签约频道列表 | GET /signChannel/operation/list | — |
| 全量签约频道列表 | GET /signChannel/listAll | — |
| 设置垂类 | POST /signChannel/setCategory | @RepeatSubmit 防重 |
| 签约频道分配 | POST /signChannel/allocate | — |
| 签约频道分页导出 | POST /signChannel/export | — |
| 导入签约频道/视听作品 | POST /signChannel/import | type=0 签约频道；type=1 视听作品 |
| 查询分配信息 | POST /signChannel/queryAllocationInformation | 需登录 |
| 查询国内频道详情 | GET /signChannel/queryDomesticChannelDetail | id 必填 |
| 查询国内频道详情（更多）| GET /signChannel/queryDomesticChannelDetailMore | id 必填 |
| 推送解约频道 | POST /signChannel/pushTerminationChannel | — |
| 同步三级垂类到 CRM | GET /signChannel/syncCrmCategory | @RepeatSubmit 防重 |

---

### 3.6 内容资产 - 内容领用（签约内容 / OpeContent Application）

**后端接口**：`POST/GET /content/application/*`
**前端路由**：`/views/content-assets/contract-content/`

**Tab 页签**：

| Tab 名称 | name 值 | 说明 |
|---------|---------|------|
| 视听作品 | `0` | 视听类作品列表（默认）|
| 影视作品 | `5` | 影视类作品列表 |
| 图文作品 | `1` | 图文类作品列表 |
| 音乐作品 | `2` | 音乐类作品列表 |
| 频道 | `-1` | 签约频道列表，搜索条件和表格与作品 Tab 不同 |

> 注：切换到「频道」Tab 时，搜索条件变为视频标题/源频道/源平台/视频创建时间；切换到作品类 Tab 时，搜索条件变为作品名/垂类/CP名称/套餐/引进模式/合约状态等；顶部操作栏在「频道」Tab 下隐藏「导入」「导出」按钮

#### 3.6.1 领用申请单

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 分页查询领用申请单 | POST /content/application/queryPage | 需登录；支持按运营组别过滤（含子部门）|
| 新增/保存领用申请 | POST /content/application/saveOrUpdate | 需登录；@RepeatSubmit 防重 |
| 获取申请单详情 | GET /content/application/getById | id 必填 |
| 审核申请单 | POST /content/application/audit | — |
| 更新申请单状态 | GET /content/application/updateStatusById | id、status 必填 |
| 删除申请单 | GET /content/application/delete | 需登录；id 必填 |
| 复用上次申请单 | GET /content/application/reuse | operatingMemberId、operatingMode 不能为空 |
| 获取申请单抬头信息 | GET /content/application/queryApplicationReceiptsTitle | 需登录；authorizePlatform 必填 |
| 获取申请单详情（批量）| GET /content/application/queryOpeContentDetail | applicationIds 必填 |
| 导出 | POST /content/application/export | 需登录 |
| 批量设置 | POST /content/application/batchConfig | @RepeatSubmit 防重；后端校验 |
| 注册 | POST /content/application/register | @RepeatSubmit 防重；后端校验注册合法性 |
| 同步运营数据 | POST /content/application/syn | — |

#### 3.6.2 签约内容管理

**后端接口**：`POST/GET /domestic/content/*`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 签约内容分页查询 | POST /domestic/content/queryPage | 需登录；@Validated 参数校验 |
| 领用记录列表 | GET /domestic/content/getReceiveRecord | 需登录；id 必填 |
| 资源规划退回 | POST /domestic/content/team/sendBack | 需登录；@Validated 校验 |
| 资源分配退回 | POST /domestic/content/dept/sendBack | 需登录；@Validated 校验 |
| 批量分配 | POST /domestic/content/batchAssigner | 需登录；分配冲突时返回 402 |
| 退回（单条）| GET /domestic/content/sendBack | 需登录；id、contentType 必填 |
| 导出签约内容 | POST /domestic/content/export | 需登录；contentType=3 时输出成员视图 |
| 异步导出 | POST /domestic/content/asyncExport | 需登录 |

---

### 3.7 内容资产 - 内容分配（Content Distribute）

**后端接口**：`POST /compositionAllocate/*`
**前端路由**：`/views/content-assets/content-distribute/`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 内容分配分页列表 | POST /compositionAllocate/pageList | @Validated 参数校验 |
| 创建分配单前校验 | POST /compositionAllocate/beforeCreate | @Validated；检测冲突/重复分配 |
| 创建作品分配单 | POST /compositionAllocate/create | @Validated；需先调用 beforeCreate |
| 分配单详情 | POST /compositionAllocate/detail/{id} | id 路径参数必填 |
| 创建页面下拉作品选择 | POST /compositionAllocate/compositionList | @Validated；分页模糊搜索作品 |
| 内容分配冲突检测 | POST /compositionAllocate/checkConflict | teamId、servicePackageList、langList、allocateDetails 必填 |

---

### 3.8 内容资产 - 内容解约（Content Termination）

**后端接口**：`POST /compositionTerminate/*`
**前端路由**：`/views/content-assets/content-termination/`
**前端组件**：`List.vue` + components/ 目录（7个子组件）

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 解约单分页列表 | POST /compositionTerminate/pageList | — |
| 创建解约单 | POST /compositionTerminate/create | @Validated 参数校验 |
| 解约单详情 | POST /compositionTerminate/detail/{id} | id 路径参数必填 |
| 创建页面下拉作品选择 | POST /compositionTerminate/compositionList | — |
| 批量导入添加解约作品 | POST /compositionTerminate/importAdd | key（文件key）必填；teamId 可选 |
| 作品选择（仅作品信息）| POST /compositionTerminate/compositionSimpleList | — |
| 批量创建解约单 | POST /compositionTerminate/batchCreate | — |

> **本期改造重点（AMS_V1.5.0）**：
> - 创建解约单表单新增「视频是否下架」字段及联动逻辑（在现有 Add.vue 组件中改造）
> - 解约类型=版权方解约/分销商解约 → 「视频是否下架」默认「是」且不可编辑
> - 解约类型=双方协商一致 → 默认「是」可编辑
> - 视频是否下架=是 → 展示「下架原因」「处理方式」「截止执行日期」等下架信息子模块
> - 提交时弹出二次确认弹窗，确认后同时创建视频下架任务单

---

### 3.9 内容资产 - 发布内容（Publishing Content）

**后端接口**：`GET /assets/publish/list`
**前端路由**：`/views/content-assets/publishing-content/`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 发布内容分页列表 | GET /assets/publish/list | — |

---

### 3.10 线索审核（Clue Review）⚠️ 已下架

> **此功能已下架，前端入口不再展示，后端接口保留但不对用户开放。**

**后端接口**：`GET/POST /clue/*`
**前端路由**：`/views/clue-review/`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 线索审核分页列表 | GET /clue/page | — |
| 审核线索 | POST /clue/audit | @RepeatSubmit 防重 |
| 保存线索（暂存）| POST /clue/save | @RepeatSubmit 防重 |
| 线索明细 | POST /clue/detail | — |
| Tag 数据量统计 | POST /clue/tagShowCount | 返回各 Tab 计数 |
| 同步数据 | POST /clue/sync | — |
| 导出线索 | POST /clue/export | 使用模板导出 |
| 导入线索 | POST /clue/import | Excel 导入，headRowNumber=2 |
| 导出失败文件 | GET /clue/exportFailure | fileId 必填 |

---

### 3.11 作品审核（Composition Review / Clue Review）

> 注：前端「线索审核」页面（`/views/clue-review/`）与「作品审核」共用同一套 Tab 切换逻辑，实为同一页面分Tab展示。

**后端接口**：`GET/POST /composition/*` 、`GET/POST /clue/*`
**前端路由**：`/views/clue-review/`

**Tab 页签**：

| Tab 名称 | name 值 | 说明 |
|---------|---------|------|
| 频道 | `channel` | 频道审核列表（默认）|
| 视听作品 | `0` | 视听类作品审核 |
| 影视作品 | `5` | 影视类作品审核 |
| 图文作品 | `1` | 图文类作品审核 |
| 音乐作品 | `2` | 音乐类作品审核 |

> 注：「频道」Tab 与作品类 Tab 的搜索条件不同；频道 Tab 下显示频道名称/平台/MCN/来源等筛选项，作品 Tab 下显示作品名/评级等筛选项

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 作品审核分页列表 | GET /composition/page | — |
| 审核作品 | POST /composition/audit | — |
| 保存（暂存）| POST /composition/save | @RepeatSubmit 防重 |
| 同步数据 | POST /composition/sync | — |
| 领域数据 | POST /composition/field | — |
| 导出作品 | POST /composition/export | 使用 Excel 模板输出 |
| 导入作品 | POST /composition/import | Excel 导入，headRowNumber=2 |
| 导出失败文件 | GET /composition/exportFailure | fileId 必填 |

---

### 3.12 内容资产 - 内容资产概览（Assets）

**后端接口**：`GET /assets/*`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 频道内容页面 | GET /assets/channel/list | 按 registerPlatform 过滤 |
| 视听/图文/音乐分页 | GET /assets/composition/list/{type} | type 路径参数 1/2/3 |
| AMS 作品综合查询（对外）| POST /assets/amsCpWorkList | — |
| 60天内即将到期作品数 | GET /assets/composition/expiringSoonCount/{type} | type 路径参数 |
| 签约内容时间线 | GET /assets/video/timeline | videoId 必填 |
| 设置视频垂类 | GET /assets/setCategory | videoId、categoryId、parentCategoryId 必填 |
| 设置作品垂类 | POST /assets/setCompositionCategory | — |
| 获取组别列表 | GET /assets/departmentList | corpId 可选 |
| 获取新大陆员工列表 | GET /assets/xdl/user | — |
| 签约作品分页列表导出 | GET /assets/export/{type} | type 路径参数 |

---

### 3.13 版权授权管理 - 版权审核（Copyright Auth）

**后端接口**：`GET/POST /copyright/review/*`
**前端路由**：`/views/auth/copyright-auth/`

**Tab 页签**：

| Tab 名称 | name 值 | 说明 |
|---------|---------|------|
| 版权审核 | `copyright` | 版权审核列表（默认）|
| 同名纠纷处理 | `nameDispute` | 同名纠纷处理列表 |

> 注：两个 Tab 共用同一页面，不同 Tab 下搜索条件和表格列不同；「版权审核」Tab 隐藏「评级」「作品名」列；「同名纠纷处理」Tab 隐藏「频道名」「平台」「MCN」「来源」列

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 版权审核分页列表 | GET /copyright/review/page | — |
| 审核操作 | POST /copyright/review/review | @RepeatSubmit 防重 |
| 同名短剧检测 | GET /copyright/review/checkSameName | registrationId 必填 |
| 审核详情 | GET /copyright/review/detail | registrationId 必填 |

#### 数据接收（供剧权宝后端同步）

| 功能点 | 接口 | 说明 |
|--------|------|------|
| 接收版权注册申请 | POST /copyright/receive/registration | 剧权宝同步调用 |
| 接收纠纷提交 | POST /copyright/receive/cidDispute | conflictType: cid_dispute / name_conflict |

---

### 3.14 版权授权管理 - CID 纠纷处理（Dispute Auth）

> 注：此模块仅展示 CID 纠纷（版权侵权），无 Tab 切换；同名纠纷已合并至 3.13「版权审核」页的「同名纠纷处理」Tab 下。

**后端接口**：`GET/POST /copyright/cidDispute/*`
**前端路由**：`/views/auth/dispute-auth/`

#### CID 纠纷处理

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 纠纷处理分页列表 | GET /copyright/cidDispute/page | — |
| 纠纷协调处理（按视频批量）| POST /copyright/cidDispute/process | @Valid 参数校验；@RepeatSubmit 防重 |
| 纠纷详情 | GET /copyright/cidDispute/detail | disputeId 必填 |

#### 同名纠纷处理（归属于 3.13 版权审核页「同名纠纷处理」Tab）

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 同名纠纷分页列表 | GET /copyright/nameDispute/page | — |
| 同名纠纷协调处理 | POST /copyright/nameDispute/process | @Valid 参数校验；@RepeatSubmit 防重 |
| 同名纠纷详情 | GET /copyright/nameDispute/detail | disputeId 必填 |

---

### 3.15 异常监控 - 视频异常（Abnormal Monitoring）

**后端接口**：`GET /abnormal/*`
**前端路由**：`/views/abnormal-monitoring/video-abnormality/`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 视频最新异常列表 | GET /abnormal/current/abnormal/list | 支持频道名（模糊）、获利状态筛选；分页 |
| 视频异常列表导出 | GET /abnormal/current/abnormal/export | 最多导出 10000 条 |

---

### 3.16 系统设置 - 垂类配置（Vertical Category）

**后端接口**：`GET/POST /category/*`
**前端路由**：`/views/system-settings/vertical-configuration/`

| 功能点 | 接口 | 校验规则 |
|--------|------|---------|
| 垂类树 | GET /category/getTree | — |
| 垂类分页列表 | GET /category/getPage | — |
| 新增垂类 | POST /category/add | @Validated；读取当前登录用户信息作为创建人 |
| 编辑垂类 | POST /category/edit | 读取当前登录用户信息作为更新人 |
| 垂类详情 | GET /category/detail | id 必填 |
| 停用垂类 | POST /category/disable | — |
| 启用垂类 | POST /category/enable | — |
| 初始数据导入 | POST /category/import | file 必填 |
| 更新海外频道垂类 | POST /category/updateOverseaChannelCategory | file 必填 |
| 垂类树（对外）| GET /category/getTreeSelect | fullData 参数，true=过滤未启用节点 |
| 根据ID查询垂类列表（对外）| GET /category/getByIds | ids 列表必填 |
| 获取所有垂类ID→全名映射 | GET /category/allIdToFullNameMap | nodeId、opened 可选 |

---

### 3.17 YouTube 频道字段管理

**后端接口**：`GET /youtubeField/*`

| 功能点 | 接口 | 说明 |
|--------|------|------|
| YouTube 频道字段管理 | （前端不直接使用，供系统内部调用）| 管理 YouTube 频道元数据字段配置 |

---

## 四、权限控制规则

| 权限维度 | 规则说明 |
|---------|---------|
| 路由权限 | 后端动态下发菜单路由树，前端按照路由名称动态注册页面组件 |
| 按钮权限 | 后端在路由树中嵌套按钮类型节点，前端通过 `getButtonAuth` 提取存储，由 `v-auth` 指令控制可见性 |
| 数据权限 | 签约内容/领用模块按运营组别（departmentId 含子部门）过滤数据 |
| 登录校验 | 部分接口使用 `@NeedLogin` 注解，未登录时拦截返回未授权 |
| 防重提交 | 部分写操作使用 `@RepeatSubmit` 注解，同一用户短时间内重复提交时拦截 |

---

## 五、跨系统交互

| 系统 | 交互方向 | 内容 |
|------|---------|------|
| CRM | CRM → AMS | 签约频道数据同步（POST /signChannel/syn）、授权延长同步 |
| 剧权宝 | 剧权宝 → AMS | 版权注册申请同步、CID/同名纠纷提交（POST /copyright/receive/*）|
| 剧老板（distribution-server）| AMS → 剧老板 | 创建发布通道（POST /publishChannel/distribute/publish）|
| 剧老板 | AMS ← 剧老板 | 发布通道数据推送（amsPipelineMessagePage）|
| 用户中心（User Center）| AMS → 用户中心 | 用户信息获取、钉钉部门/用户查询 |
| OSS（阿里云）| AMS ↔ OSS | 文件上传下载（导入模板、导出文件）|

---

## 六、字段校验规则汇总

| 模块 | 字段 | 类型 | 必填 | 校验规则 |
|------|------|------|------|---------|
| 频道/主页导入 | 获利状态 | String | 是 | 只能填 Yes 或 No（不区分大小写）|
| 频道/主页导入 | 频道ID | String | 是 | 必须在系统内已存在 |
| 发布通道 | publishChannelId | Integer | 是（开启/关闭时）| 不能为空 |
| 领用申请 | operatingMemberId | String | 是（复用时）| 不能为空 |
| 领用申请 | authorizePlatform | Integer | 是（获取抬头时）| 不能为空 |
| 内容分配冲突检测 | teamId、servicePackageList、langList | — | 是 | 不能为空 |
| 版权审核 | registrationId | Long | 是（详情/同名检测）| 不能为空 |
| 纠纷处理 | disputeId | Long | 是（详情时）| 不能为空 |
| 垂类 | 名称/父级ID | — | 是（新增时）| @Validated；创建人由系统自动填充 |
| 频道模糊搜索 | name | String | 是 | 长度 ≥ 2 |

---

## 七、本期新增功能（AMS_V1.5.0）

> 以下功能在当前代码基线中**尚未实现**，为本期需求：

| 功能点 | 所属模块 | 说明 |
|--------|---------|------|
| 视频下架管理（新增菜单）| 内容资产 | 全新模块，包含任务单创建/审批/执行全生命周期 |
| 解约单-视频是否下架字段 | 内容解约（改造）| 在现有 Add.vue 组件改造，新增字段+联动+确认弹窗 |

