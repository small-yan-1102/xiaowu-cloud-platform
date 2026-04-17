# 逾期结算处理 - API 接口设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 所属模块 | 逾期结算处理（VideoCompositionOverdue） |
| 关联域设计文档 | [02-逾期结算处理-详细设计.md](./02-逾期结算处理-详细设计.md) |
| 迭代版本 | V4.5 |
| 说明 | 仅包含本次迭代变更涉及的接口，未变更接口不重复描述 |

---

## 一、全局约定

### 1.1 基础信息

| 项目 | 值 |
|------|---|
| **Base Path** | `/videoCompositionOverdue` |
| **Content-Type** | `application/json` |
| **字符编码** | UTF-8 |

### 1.2 统一响应格式

**成功响应**：

```json
{
  "status": 200,
  "message": "success",
  "data": {}
}
```

**错误响应**：

```json
{
  "status": 400,
  "message": "错误说明"
}
```

**分页响应（data 部分）**：

```json
{
  "records": [],
  "total": 100,
  "size": 20,
  "current": 1
}
```

### 1.3 认证方式

| 项目 | 值 |
|------|---|
| **认证方式** | Sa-Token（内部系统）/ JWT accessToken（外部系统调用 `checkSplitStatus`）|
| **Header 名称** | `Authorization` / `accessToken` |

### 1.4 错误码说明

| HTTP 状态码 | 说明 | 典型场景 |
|------------|------|---------|
| `200` | 请求处理成功 | - |
| `400` | 业务异常（BizException） | 参数错误、业务规则不满足 |
| `500` | 系统异常 | 数据库异常、外部服务调用失败 |

---

## 二、接口详细设计

### 2.1 逾期结算处理接口（VideoCompositionOverdueController）

> 资源路径：`/videoCompositionOverdue`
> Controller：`VideoCompositionOverdueController`
> 代码位置：`finance-service/src/main/java/cn/oyss/finance/application/controller/VideoCompositionOverdueController.java`

**本次迭代接口变更总览**：

| # | 接口方法 | HTTP 方法 | 路径 | 变更类型 | 说明 |
|---|----------|----------|------|---------|------|
| 1 | `page` | `POST` | `/videoCompositionOverdue/page` | `[修改]` | VO 新增 `originalStatus`、`videoTag` 字段；支持 status=3 |
| 2 | `batchSplit` | `POST` | `/videoCompositionOverdue/batchSplit` | `[修改]` | 入参从 `List<Long>` 改为 `BatchSplitRequest`（含 status 参数）|
| 3 | `exportAsync` | `POST` | `/videoCompositionOverdue/export/async` | `[修改]` | 导出对象新增 `originalStatus`、`videoTag` 字段 |
| 4 | `checkSplitStatus` | `GET` | `/videoCompositionOverdue/checkSplitStatus` | `[修改]` | status=3 纳入"未拆分"判断 |

---

#### 2.1.1 分页查询逾期结算列表 `[修改]`

| 项目 | 内容 |
|------|------|
| **接口方法** | `page` |
| **HTTP 方法** | `POST` |
| **完整路径** | `/videoCompositionOverdue/page` |
| **认证要求** | Sa-Token（内部系统，菜单级权限控制）|
| **变更说明** | VO 新增 `originalStatus`、`videoTag`（视频标签）字段；status=3 Tab 通过现有 `status` 参数传值即可支持 |

**Request Body**（`VideoCompositionOverdueQuery`）：

| 字段名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `page` | `Integer` | N | 页码，默认 1 |
| `pageSize` | `Integer` | N | 每页大小，默认 20 |
| `status` | `Integer` | N | Tab 状态：0=未登记, 1=逾期登记未拆分, 2=已拆分, **3=跨期正常未拆分（新增）** |
| `receiptedMonthStart` | `String` | N | 到账月份起，格式 yyyy-MM |
| `receiptedMonthEnd` | `String` | N | 到账月份止，格式 yyyy-MM |
| `channelId` | `String` | N | 频道ID |
| `channelName` | `String` | N | 频道名称，模糊匹配 |
| `videoId` | `String` | N | 视频ID |
| `cpName` | `String` | N | CP名称，模糊匹配 |
| `signChannelName` | `String` | N | 子集名称，模糊匹配 |
| `teamName` | `String` | N | 分销商名称，模糊匹配 |
| `cms` | `String` | N | 收款系统 |

**请求示例**：

```http
POST /videoCompositionOverdue/page
Content-Type: application/json

{
  "page": 1,
  "pageSize": 20,
  "status": 3,
  "receiptedMonthStart": "2025-10",
  "receiptedMonthEnd": "2025-12"
}
```

**成功响应**：

```json
{
  "status": 200,
  "message": "success",
  "data": [
    {
      "id": 12345,
      "receiptedMonth": "2025-11",
      "channelId": "UCxxxxxx",
      "channelName": "示例频道",
      "videoId": "abcdefg",
      "cms": "XW",
      "revenue": 100.00,
      "usRevenue": 30.00,
      "sgRevenue": 10.00,
      "status": 3,
      "statusName": "跨期正常未拆分",
      "originalStatus": null,
      "videoTag": 1,
      "registrationTime": "2025-12-01 10:00:00",
      "signChannelName": "子集A",
      "cpName": "CP公司"
    }
  ],
  "total": 150,
  "pageSize": 20,
  "page": 1
}
```

**成功响应字段说明（新增字段）**：

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data[].originalStatus` | `Integer` | **[新增]** 拆分前原始状态：1=逾期登记，3=跨期正常；未拆分时为 null，历史已拆分记录也为 null |
| `data[].videoTag` | `Integer` | **[新增]** 视频标签：0=无标签，1=技术漏抓；前端 =1 时展示橙色【技术漏抓】标签 |

**错误响应**：

| 触发场景 | HTTP 状态码 | message |
|----------|-----------|---------|
| 参数格式错误 | `400` | "参数校验失败" |

---

#### 2.1.2 批量拆分结算 `[修改]`

| 项目 | 内容 |
|------|------|
| **接口方法** | `batchSplit` |
| **HTTP 方法** | `POST` |
| **完整路径** | `/videoCompositionOverdue/batchSplit` |
| **认证要求** | Sa-Token（财务人员角色）|
| **变更说明** | 入参从 `List<Long>` 改为对象，新增 `status` 字段以区分操作的 Tab；支持 status=3 记录的拆分；拆分后写入 `originalStatus` |

**Request Body**（`BatchSplitRequest`，新增 DTO）：

| 字段名 | 类型 | 必选 | 校验规则 | 说明 |
|--------|------|------|----------|------|
| `ids` | `List<Long>` | Y | `@NotEmpty` | 用户勾选的记录ID列表 |
| `status` | `Integer` | Y | `@NotNull`，值必须为 1 或 3 | 当前操作Tab状态：1=逾期登记未拆分, 3=跨期正常未拆分 |

**请求示例**（逾期Tab）：

```http
POST /videoCompositionOverdue/batchSplit
Content-Type: application/json

{
  "ids": [101, 102, 103],
  "status": 1
}
```

**请求示例**（跨期正常Tab，新增）：

```http
POST /videoCompositionOverdue/batchSplit
Content-Type: application/json

{
  "ids": [201, 202],
  "status": 3
}
```

**成功响应**：

```json
{
  "status": 200,
  "message": "success"
}
```

> 说明：成功提示文案为"操作成功"（V4.5 规定），不返回处理数量。

**错误响应**：

| 触发场景 | HTTP 状态码 | message |
|----------|-----------|---------|
| ids 为空 | `400` | "请选择要拆分的记录" |
| status 不合法（非1或3）| `400` | "不合法的操作Tab状态" |
| 无有效记录（状态不匹配）| `400` | "没有可拆分的记录" |
| pipelineId 为空 | `400` | "视频ID={videoId} 的pipelineId为空，无法拆分" |
| 未找到冲销表记录 | `400` | "未找到对应的冲销表记录: {month}-{channelId}-{cms}" |
| 冲销表记录未到账 | `400` | "冲销表记录未到账，不允许拆分子集: {month}-{channelId}-{cms}" |

---

#### 2.1.3 异步导出 `[修改]`

| 项目 | 内容 |
|------|------|
| **接口方法** | `exportAsync` |
| **HTTP 方法** | `POST` |
| **完整路径** | `/videoCompositionOverdue/export/async` |
| **认证要求** | Sa-Token |
| **变更说明** | 导出对象新增 `videoTag`（视频标签，所有Tab）和 `originalStatus`（已拆分Tab）字段 |

**Request Body**（`VideoCompositionOverdueAsyncQuery`）：

| 字段名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `page` | `Integer` | Y | 页码 |
| `pageSize` | `Integer` | Y | 每页大小 |
| `offset` | `Long` | N | 游标偏移（上一页最后一条ID），首次请求传 0 |
| `status` | `Integer` | N | Tab 状态（0/1/2/3）|
| `receiptedMonthStart` | `String` | N | 到账月份起 |
| `receiptedMonthEnd` | `String` | N | 到账月份止 |

**成功响应**（新增字段）：

```json
{
  "status": 200,
  "data": {
    "records": [
      {
        "receiptedMonth": "2025-11",
        "channelId": "UCxxxxxx",
        "videoId": "abcdefg",
        "revenue": 100.00,
        "usRevenue": 30.00,
        "sgRevenue": 10.00,
        "videoTag": 1,
        "originalStatus": 3,
        "operatorName": "张三",
        "operateTime": "2025-12-10 15:30:00"
      }
    ],
    "total": 500,
    "size": 100,
    "current": 1
  }
}
```

**新增字段说明**：

| 字段路径 | 类型 | 导出列名 | Tab 范围 | 说明 |
|---------|------|---------|---------|------|
| `records[].videoTag` | `Integer` | 视频标签 | 所有Tab | 0=无标签，1=技术漏抓 |
| `records[].originalStatus` | `Integer` | 原状态 | 仅 status=2（已拆分Tab）| 1=逾期登记，3=跨期正常；历史记录为 null |

---

#### 2.1.4 查询视频拆分状态（外部系统调用）`[修改]`

| 项目 | 内容 |
|------|------|
| **接口方法** | `checkSplitStatus` |
| **HTTP 方法** | `GET` |
| **完整路径** | `/videoCompositionOverdue/checkSplitStatus` |
| **认证要求** | JWT accessToken（`@NeedLogin`，外部系统调用）|
| **变更说明** | 将 status=3（跨期正常未拆分）纳入"未拆分"判断，确保 isSplit=false |

**Query 参数**：

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `videoId` | `String` | Y | 视频ID |

**请求示例**：

```http
GET /videoCompositionOverdue/checkSplitStatus?videoId=abcdefg
accessToken: {jwt_token}
```

**成功响应**：

```json
{
  "status": 200,
  "data": {
    "videoId": "abcdefg",
    "isSplit": false
  }
}
```

**isSplit 判断规则（变更后）**：

| 条件 | isSplit |
|------|---------|
| 无记录 | `false` |
| 存在 status=0（未登记）| `false` |
| 存在 status=1（逾期未拆分）| `false` |
| 存在 status=3（跨期正常未拆分）**[新增]** | `false` |
| 全部为 status=2（已拆分）| `true` |

---

## 附录

### A. 接口清单汇总

| # | HTTP 方法 | 路径 | 变更类型 | 说明 |
|---|----------|------|---------|------|
| 1 | `POST` | `/videoCompositionOverdue/page` | `[修改]` | VO 新增 2 字段 |
| 2 | `POST` | `/videoCompositionOverdue/batchSplit` | `[修改]` | 入参结构变更，新增 status 字段 |
| 3 | `POST` | `/videoCompositionOverdue/export/async` | `[修改]` | 导出对象新增 2 字段 |
| 4 | `GET` | `/videoCompositionOverdue/checkSplitStatus` | `[修改]` | status=3 纳入未拆分判断 |
| 5 | `POST` | `/videoCompositionOverdue/import/async` | `[修改]` | 触发新的 R1-R6 导入校验（接口签名不变）|

### B. DTO 对象汇总

#### BatchSplitRequest（新增）

> 用途：批量拆分请求体，替代原 `List<Long>` 直传方式

| 字段名 | Java 类型 | 必填 | 说明 |
|--------|----------|------|------|
| `ids` | `List<Long>` | Y | 勾选的记录ID列表 |
| `status` | `Integer` | Y | 操作Tab状态：1 或 3 |

#### VideoCompositionOverdueVO（新增字段）

> 用途：分页列表响应 VO

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `originalStatus` | `Integer` | **[新增]** 拆分前原始状态，null=未拆分或历史记录 |
| `videoTag` | `Integer` | **[新增]** 视频标签：0=无标签，1=技术漏抓 |

#### VideoCompositionOverdueExport（新增字段）

> 用途：EasyExcel 导出映射对象

| 字段名 | Java 类型 | 导出列名 | 说明 |
|--------|----------|---------|------|
| `originalStatus` | `Integer` | 原状态 | **[新增]** 仅已拆分Tab有值 |
| `videoTag` | `Integer` | 视频标签 | **[新增]** 所有Tab均有值；0=无标签，1=技术漏抓 |
