# CRM 交接单 - API 接口设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 所属模块 | CRM 交接单 |
| 关联设计文档 | `02-CRM交接单-详细设计.md` |

---

## 一、全局约定

### 1.1 基础信息

| 项目 | 值 |
|------|---|
| **Base URL** | `/api/v1` |
| **Content-Type** | `application/json` |
| **字符编码** | UTF-8 |

### 1.2 统一响应格式

**成功响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误响应**：

```json
{
  "code": 10001,
  "message": "参数校验失败",
  "details": { "field": "error message" }
}
```

### 1.3 认证方式

| 项目 | 值 |
|------|---|
| **认证方式** | Bearer Token |
| **Header 名称** | `Authorization` |
| **格式** | `Bearer {token}` |

### 1.4 错误码定义

| 错误码 | HTTP 状态码 | 说明 | 触发场景 |
|--------|-----------|------|----------|
| `0` | 200 | 成功 | - |
| `10001` | 400 | 参数校验失败 | 必填参数为空、格式错误 |
| `10002` | 401 | 未认证 | Token 过期或无效 |
| `10004` | 404 | 资源不存在 | 合约/交接单不存在 |
| `50000` | 500 | 系统内部错误 | 服务异常 |

---

## 二、接口详细设计

### 2.1 交接单管理接口

> 资源路径：`/api/v1/contract`
> Controller：`ContractLibraryController`
> 代码位置：`src/main/java/cn/oyss/crm/application/controller/ContractLibraryController.java`

**接口总览**：

| # | 接口方法 | HTTP 方法 | 路径 | 说明 | 认证 |
|---|----------|----------|------|------|------|
| 1 | `addOrUpdateDeliveryReceipt` | `POST` | `/contract/addOrUpdateDeliveryReceipt` | 创建/编辑交接单 `[修改]` | 需认证 |
| 2 | `deliveryReceiptGetDetail` | `GET` | `/contract/deliveryReceiptGetDetail` | 获取交接单详情 `[修改]` | 需认证 |

---

#### 2.1.1 创建/编辑交接单 `需认证` `[修改]`

| 项目 | 内容 |
|------|------|
| **接口方法** | `addOrUpdateDeliveryReceipt` |
| **HTTP 方法** | `POST` |
| **完整路径** | `/api/v1/contract/addOrUpdateDeliveryReceipt` |
| **Service 方法** | `DeliveryReceiptServiceImpl.addOrUpdateDeliveryReceipt()` |
| **认证要求** | 需认证 |
| **权限标识** | 无 |

**Request Body**：

| 字段名 | 类型 | 必选 | 校验规则 | 说明 |
|--------|------|------|----------|------|
| `contractId` | `Long` | Y | 不能为空 | 合约ID |
| `channelList` | `List<Object>` | Y | 不能为空 | 频道列表 |
| `channelList[].channelId` | `String` | Y | - | 频道ID |
| `channelList[].channelName` | `String` | N | - | 频道名称 |
| `channelList[].channelLabel` | `Integer` | N | 0/1/2/3 | 频道标签 |
| `channelList[].collectionType` | `String` | N | 0/1 | 合集类型 |
| `channelList[].firstReleaseTime` | `String` | N | ISO 8601格式 | 首发时间 |
| `channelList[].publishLanguage` | `String` | N | - | 首发语种 |
| `compositionList` | `List<Object>` | N | - | 作品配置列表 `[新增]` |
| `compositionList[].compositionId` | `Long` | Y | 不能为空 | 作品ID |
| `compositionList[].compositionName` | `String` | N | 长度≤500 | 作品名称 |
| `compositionList[].internalPublish` | `Boolean` | Y | 不能为空 | 内部可发布 |
| `compositionList[].firstPublishTimeType` | `String` | N | ANYTIME/CUSTOM/WAITING | 首发时间类型 |
| `compositionList[].firstPublishTime` | `String` | N | ISO 8601格式 | 首发时间 |
| `compositionList[].channelLimit` | `String` | N | UNLIMITED/CP_ONLY | 频道发布限制 |
| `compositionList[].subtitleLangConfig` | `Object` | N | - | 字幕语种配置 |
| `compositionList[].subtitleLangConfig.allow` | `List<String>` | N | - | 字幕可发语种 |
| `compositionList[].subtitleLangConfig.deny` | `List<String>` | N | - | 字幕禁发语种 |
| `compositionList[].dubbingLangConfig` | `Object` | N | - | 配音语种配置 |
| `compositionList[].dubbingLangConfig.allow` | `List<String>` | N | - | 配音可发语种 |
| `compositionList[].dubbingLangConfig.deny` | `List<String>` | N | - | 配音禁发语种 |
| `status` | `Integer` | Y | 0/1 | 状态：0未提交，1已交接 |

**请求示例**：

```http
POST /api/v1/contract/addOrUpdateDeliveryReceipt
Content-Type: application/json
Authorization: Bearer {token}

{
  "contractId": 12345,
  "channelList": [
    {
      "channelId": "UCxxxxxx",
      "channelName": "测试频道",
      "channelLabel": 0,
      "collectionType": "1",
      "firstReleaseTime": "2026-04-01T00:00:00",
      "publishLanguage": "zh,en"
    }
  ],
  "compositionList": [
    {
      "compositionId": 1001,
      "compositionName": "作品A",
      "internalPublish": true,
      "firstPublishTimeType": "ANYTIME",
      "firstPublishTime": null,
      "channelLimit": "UNLIMITED",
      "subtitleLangConfig": {
        "allow": ["ALL"],
        "deny": []
      },
      "dubbingLangConfig": {
        "allow": ["zh", "en"],
        "deny": ["ko"]
      }
    }
  ],
  "status": 1
}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

**错误响应**：

| 触发场景 | 错误码 | HTTP 状态码 | message |
|----------|--------|-----------|---------|
| 合约ID为空 | `10001` | 400 | "合约ID不能为空" |
| 合约不存在 | `10004` | 404 | "合约不存在" |
| 频道列表为空 | `10001` | 400 | "请选择频道" |

**本次迭代变更说明**：

- `[新增]` 支持 `compositionList` 参数，用于配置作品发布信息
- `[修改]` 已交接状态（`status=1`）的交接单可以编辑并重新推送
- `[新增]` 保存时若 `status=1`，自动触发 MQ 推送至 AMS

---

#### 2.1.2 获取交接单详情 `需认证` `[修改]`

| 项目 | 内容 |
|------|------|
| **接口方法** | `deliveryReceiptGetDetail` |
| **HTTP 方法** | `GET` |
| **完整路径** | `/api/v1/contract/deliveryReceiptGetDetail` |
| **Service 方法** | `DeliveryReceiptServiceImpl.deliveryReceiptGetDetail()` |
| **认证要求** | 需认证 |
| **权限标识** | 无 |

**Query 参数**：

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `num` | `String` | Y | 交接单编号 |

**请求示例**：

```http
GET /api/v1/contract/deliveryReceiptGetDetail?num=ZY2603260001
Authorization: Bearer {token}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "num": "ZY2603260001",
    "contractNum": "HT2603001",
    "contractId": 12345,
    "memberName": "CP名称",
    "status": 1,
    "signTime": "2026-03-26T10:00:00",
    "channelList": [
      {
        "channelId": "UCxxxxxx",
        "channelName": "测试频道",
        "channelLabel": 0,
        "collectionType": "1",
        "firstReleaseTime": "2026-04-01T00:00:00",
        "publishLanguage": "zh,en",
        "disableLanguage": null
      }
    ],
    "compositionList": [
      {
        "compositionId": 1001,
        "compositionName": "作品A",
        "internalPublish": true,
        "firstPublishTimeType": "ANYTIME",
        "firstPublishTime": null,
        "channelLimit": "UNLIMITED",
        "subtitleLangConfig": {
          "allow": ["ALL"],
          "deny": []
        },
        "dubbingLangConfig": {
          "allow": ["zh", "en"],
          "deny": ["ko"]
        }
      }
    ],
    "scopeList": [
      {
        "platform": "YouTube",
        "accountOwnership": "公司",
        "profitStatus": "分成"
      }
    ],
    "notesList": [
      {
        "content": "备注内容",
        "createdAt": "2026-03-26T14:00:00",
        "createdUser": "张三"
      }
    ]
  }
}
```

**成功响应字段说明**：

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data.num` | `String` | 交接单编号 |
| `data.contractNum` | `String` | 合约编号 |
| `data.contractId` | `Long` | 合约ID |
| `data.memberName` | `String` | CP名称 |
| `data.status` | `Integer` | 状态：0未提交，1已交接 |
| `data.signTime` | `String` | 签约时间 |
| `data.channelList` | `Array` | 频道列表 |
| `data.compositionList` | `Array` | 作品配置列表 `[新增]` |
| `data.compositionList[].compositionId` | `Long` | 作品ID |
| `data.compositionList[].compositionName` | `String` | 作品名称 |
| `data.compositionList[].internalPublish` | `Boolean` | 内部可发布 |
| `data.compositionList[].firstPublishTimeType` | `String` | 首发时间类型 |
| `data.compositionList[].firstPublishTime` | `String` | 首发时间 |
| `data.compositionList[].channelLimit` | `String` | 频道发布限制 |
| `data.compositionList[].subtitleLangConfig` | `Object` | 字幕语种配置 |
| `data.compositionList[].dubbingLangConfig` | `Object` | 配音语种配置 |
| `data.scopeList` | `Array` | 合作范围列表 |
| `data.notesList` | `Array` | 备注列表 |

**错误响应**：

| 触发场景 | 错误码 | HTTP 状态码 | message |
|----------|--------|-----------|---------|
| 交接单编号为空 | `10001` | 400 | "交接单编号不能为空" |
| 交接单不存在 | `10004` | 404 | "交接单不存在" |

---

## 附录

### A. 接口清单汇总

| # | 模块 | HTTP 方法 | 路径 | 说明 | 认证 | 变更类型 |
|---|------|----------|------|------|------|---------|
| 1 | 交接单管理 | `POST` | `/contract/addOrUpdateDeliveryReceipt` | 创建/编辑交接单 | Y | `[修改]` |
| 2 | 交接单管理 | `GET` | `/contract/deliveryReceiptGetDetail` | 获取交接单详情 | Y | `[修改]` |

### B. DTO 对象汇总

#### LangConfigDTO `[新增]`

> 用途：语种配置嵌套对象

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `allow` | `List<String>` | 可发语种列表，ALL表示全部 |
| `deny` | `List<String>` | 禁发语种列表 |

#### DeliveryPrChannelVo 新增字段 `[修改]`

> 用途：交接单频道信息（含发布配置）

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `internalPublish` | `Boolean` | 内部可发布 `[新增]` |
| `firstPublishTimeType` | `String` | 首发时间类型 `[新增]` |
| `firstPublishTime` | `LocalDateTime` | 首发时间 `[新增]` |
| `channelLimit` | `String` | 频道发布限制 `[新增]` |
| `subtitleLangConfig` | `LangConfigDTO` | 字幕语种配置 `[新增]` |
| `dubbingLangConfig` | `LangConfigDTO` | 配音语种配置 `[新增]` |

### C. 枚举值说明

#### 首发时间类型 (firstPublishTimeType)

| 值 | 说明 |
|----|------|
| `ANYTIME` | 随时可发布 |
| `CUSTOM` | 自定义时间 |
| `WAITING` | 暂不可发布，等待上线通知 |

#### 频道发布限制 (channelLimit)

| 值 | 说明 |
|----|------|
| `UNLIMITED` | 无限制（原「合集」） |
| `CP_ONLY` | 仅CP指定频道（原「单开」） |

#### 交接单状态 (status)

| 值 | 说明 |
|----|------|
| `0` | 未提交（草稿） |
| `1` | 已交接 |
