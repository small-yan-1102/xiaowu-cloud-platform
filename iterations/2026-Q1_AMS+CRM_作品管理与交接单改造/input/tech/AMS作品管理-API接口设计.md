# AMS 作品管理 - API 接口设计文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 所属模块 | AMS 作品管理 |
| 关联设计文档 | `02-AMS作品管理-详细设计.md` |

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

**分页响应**（data 部分）：

```json
{
  "list": [ ... ],
  "total": 100,
  "pageNum": 1,
  "pageSize": 20
}
```

### 1.3 分页约定

| 参数名 | 类型 | 传参位置 | 说明 | 默认值 |
|--------|------|----------|------|--------|
| `pageNum` | `int` | Query | 当前页码（从 1 开始） | `1` |
| `pageSize` | `int` | Query | 每页条数（最大 100） | `20` |

### 1.4 认证方式

| 项目 | 值 |
|------|---|
| **认证方式** | Bearer Token |
| **Header 名称** | `Authorization` |
| **格式** | `Bearer {token}` |

### 1.5 错误码定义

| 错误码 | HTTP 状态码 | 说明 | 触发场景 |
|--------|-----------|------|----------|
| `0` | 200 | 成功 | - |
| `10001` | 400 | 参数校验失败 | 必填参数为空、格式错误 |
| `10002` | 401 | 未认证 | Token 过期或无效 |
| `10004` | 404 | 资源不存在 | 作品ID不存在 |
| `50000` | 500 | 系统内部错误 | 服务异常 |

---

## 二、接口详细设计

### 2.1 作品管理接口

> 资源路径：`/api/v1/composition`
> Controller：`AmsCompositionController`
> 代码位置：`src/main/java/cn/oyss/ams/controller/AmsCompositionController.java`

**接口总览**：

| # | 接口方法 | HTTP 方法 | 路径 | 说明 | 认证 |
|---|----------|----------|------|------|------|
| 1 | `getDetail` | `GET` | `/composition/detail/{id}` | 获取作品详情 | 需认证 |
| 2 | `getChangeLogList` | `GET` | `/composition/changeLog/{compositionId}` | 获取修改记录 | 需认证 |

> **注意**：作品设置功能复用现有 `POST /assets/setCompositionCategory` 接口（位于 `AssetsController`），仅修改垂类、别名、入库链接 3 个字段。发布配置和语种配置由 CRM 交接单推送修改，AMS 侧只读展示。

---

#### 2.1.1 获取作品详情 `需认证`

| 项目 | 内容 |
|------|------|
| **接口方法** | `getDetail` |
| **HTTP 方法** | `GET` |
| **完整路径** | `/api/v1/composition/detail/{id}` |
| **Service 方法** | `AmsCompositionServiceImpl.getDetail()` |
| **认证要求** | 需认证 |
| **权限标识** | 无 |

**Path 参数**：

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `id` | `Long` | Y | 作品ID |

**请求示例**：

```http
GET /api/v1/composition/detail/12345
Authorization: Bearer {token}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 12345,
    "name": "作品名称",
    "cpName": "CP名称",
    "cpType": 1,
    "deliveryReceiptNum": "ZY2503170001",
    "storageUrl": "https://xxx.com/storage",
    "categoryName": "短剧",
    "aliasList": ["别名1", "别名2"],
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
}
```

**成功响应字段说明**：

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data.id` | `Long` | 作品ID |
| `data.name` | `String` | 作品名称 |
| `data.cpName` | `String` | CP名称 |
| `data.cpType` | `Integer` | CP类型：1公司,2个人,3境外公司,4境外个人 |
| `data.deliveryReceiptNum` | `String` | 交接单编号 |
| `data.storageUrl` | `String` | 入库链接 |
| `data.categoryName` | `String` | 垂类名称 |
| `data.aliasList` | `List<String>` | 别名列表 |
| `data.internalPublish` | `Boolean` | 内部可发布 |
| `data.firstPublishTimeType` | `String` | 首发时间类型：ANYTIME/CUSTOM/WAITING |
| `data.firstPublishTime` | `String` | 首发时间（ISO 8601格式） |
| `data.channelLimit` | `String` | 频道发布限制：UNLIMITED/CP_ONLY |
| `data.subtitleLangConfig` | `Object` | 字幕语种配置 |
| `data.subtitleLangConfig.allow` | `List<String>` | 字幕可发语种，ALL表示全部 |
| `data.subtitleLangConfig.deny` | `List<String>` | 字幕禁发语种 |
| `data.dubbingLangConfig` | `Object` | 配音语种配置 |
| `data.dubbingLangConfig.allow` | `List<String>` | 配音可发语种，ALL表示全部 |
| `data.dubbingLangConfig.deny` | `List<String>` | 配音禁发语种 |

**错误响应**：

| 触发场景 | 错误码 | HTTP 状态码 | message |
|----------|--------|-----------|---------|
| 作品ID为空 | `10001` | 400 | "作品ID不能为空" |
| 作品不存在 | `10004` | 404 | "作品不存在" |

---

#### 2.1.2 获取修改记录列表 `需认证`

| 项目 | 内容 |
|------|------|
| **接口方法** | `getChangeLogList` |
| **HTTP 方法** | `GET` |
| **完整路径** | `/api/v1/composition/changeLog/{compositionId}` |
| **Service 方法** | `CompositionChangeLogServiceImpl.getPageList()` |
| **认证要求** | 需认证 |
| **权限标识** | 无 |

**Path 参数**：

| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| `compositionId` | `Long` | Y | 作品ID |

**Query 参数**：

| 参数名 | 类型 | 必选 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `pageNum` | `Integer` | N | `1` | 页码 |
| `pageSize` | `Integer` | N | `20` | 每页条数 |

**请求示例**：

```http
GET /api/v1/composition/changeLog/12345?pageNum=1&pageSize=20
Authorization: Bearer {token}
```

**成功响应**：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1001,
        "operator": "张三",
        "operateType": "UPDATE",
        "fieldName": "内部是否可发布",
        "oldValue": "不可发布",
        "newValue": "可发布",
        "operateTime": "2026-03-26T14:30:00"
      },
      {
        "id": 1000,
        "operator": "李四",
        "operateType": "CREATE",
        "fieldName": "创建作品",
        "oldValue": null,
        "newValue": null,
        "operateTime": "2026-03-25T10:00:00"
      }
    ],
    "total": 2,
    "pageNum": 1,
    "pageSize": 20
  }
}
```

**成功响应字段说明**：

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `data.list[].id` | `Long` | 记录ID |
| `data.list[].operator` | `String` | 操作人 |
| `data.list[].operateType` | `String` | 操作类型：CREATE/UPDATE |
| `data.list[].fieldName` | `String` | 字段名（业务名称） |
| `data.list[].oldValue` | `String` | 旧值（CREATE类型时为null） |
| `data.list[].newValue` | `String` | 新值（CREATE类型时为null） |
| `data.list[].operateTime` | `String` | 操作时间（ISO 8601格式） |
| `data.total` | `Long` | 总记录数 |
| `data.pageNum` | `Integer` | 当前页码 |
| `data.pageSize` | `Integer` | 每页条数 |

**错误响应**：

| 触发场景 | 错误码 | HTTP 状态码 | message |
|----------|--------|-----------|---------|
| 作品ID为空 | `10001` | 400 | "作品ID不能为空" |

---

## 附录

### A. 接口清单汇总

| # | 模块 | HTTP 方法 | 路径 | 说明 | 认证 |
|---|------|----------|------|------|------|
| 1 | 作品管理 | `GET` | `/composition/detail/{id}` | 获取作品详情 | Y |
| 2 | 作品管理 | `GET` | `/composition/changeLog/{compositionId}` | 获取修改记录 | Y |
| 3 | 作品管理 | `POST` | `/assets/setCompositionCategory` | 保存作品设置（复用现有） | Y |

### B. DTO 对象汇总

#### ChannelCompositionVO（复用现有）

> 用途：保存作品设置请求体（复用现有 DTO，无新增）

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `id` | `Integer` | 作品ID |
| `categoryId` | `Integer` | 垂类ID |
| `aliasList` | `List<String>` | 别名列表 |
| `storageUrl` | `String` | 入库链接 |

> **注意**：AMS 设置弹窗仅能修改以上 3 个字段（垂类、别名、入库链接）。发布配置和语种配置由 CRM 交接单推送，AMS 侧只读展示。

#### LangConfigDTO

> 用途：语种配置嵌套对象

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `allow` | `List<String>` | 可发语种列表，ALL表示全部 |
| `deny` | `List<String>` | 禁发语种列表 |

#### CompositionDetailVO

> 用途：作品详情响应体

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `id` | `Long` | 作品ID |
| `name` | `String` | 作品名称 |
| `cpName` | `String` | CP名称 |
| `cpType` | `Integer` | CP类型 |
| `deliveryReceiptNum` | `String` | 交接单编号 |
| `storageUrl` | `String` | 入库链接 |
| `categoryName` | `String` | 垂类名称 |
| `aliasList` | `List<String>` | 别名列表 |
| `internalPublish` | `Boolean` | 内部可发布 |
| `firstPublishTimeType` | `String` | 首发时间类型 |
| `firstPublishTime` | `LocalDateTime` | 首发时间 |
| `channelLimit` | `String` | 频道发布限制 |
| `subtitleLangConfig` | `LangConfigDTO` | 字幕语种配置 |
| `dubbingLangConfig` | `LangConfigDTO` | 配音语种配置 |

#### CompositionChangeLogVO

> 用途：修改记录响应体

| 字段名 | Java 类型 | 说明 |
|--------|----------|------|
| `id` | `Long` | 记录ID |
| `operator` | `String` | 操作人 |
| `operateType` | `String` | 操作类型 |
| `fieldName` | `String` | 字段名（业务名称） |
| `oldValue` | `String` | 旧值 |
| `newValue` | `String` | 新值 |
| `operateTime` | `LocalDateTime` | 操作时间 |
