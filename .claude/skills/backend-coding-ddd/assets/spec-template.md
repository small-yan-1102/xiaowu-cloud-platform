# [聚合根名称] 代码规格说明

> 生成时间：[日期时间]
> 基于技术方案：[技术方案文档路径]

---

## 1. 领域层 (Domain)

### 1.1 聚合根

- **类名**：XxxAggregateRoot
- **包路径**：com.xw.[模块].domain.[功能]
- **属性**：
  - id: String
  - status: XxxStatus（枚举）
  - [其他属性...]
- **静态工厂方法**：
  - `create(...)`: XxxAggregateRoot — 创建聚合根实例
- **业务行为方法**：
  - `updateStatus(...)`: void — [描述业务语义]
  - [其他方法...]
- **领域事件发布**：
  - `publisher().attachEvent(new XxxCreatedEvent(...))` — 在 create() 内发布

### 1.2 实体

- **类名**：XxxEntity
- **包路径**：com.xw.[模块].domain.[功能]
- **属性**：[属性列表]
- **业务行为**：[方法列表]

### 1.3 值对象

- **类名**：XxxValueObject
- **特性**：不可变（所有字段 final）
- **属性**：[属性列表]

### 1.4 领域事件

| 事件类名 | 触发时机 | 事件数据 |
|---------|---------|---------|
| XxxCreatedEvent | 聚合根创建时 | id, [其他关键字段] |
| XxxStatusChangedEvent | 状态变更时 | id, oldStatus, newStatus |

### 1.5 Repository 接口

- **接口名**：XxxRepository
- **包路径**：com.xw.[模块].domain.[功能]
- **方法**：
  - `findById(String id)`: Optional\<XxxAggregateRoot\>
  - `save(XxxAggregateRoot aggregateRoot)`: void
  - `findByXxx(...)`: List\<XxxAggregateRoot\> — [查询条件描述]

---

## 2. Client 层

### 2.1 外部服务 Client

- **接口名**：XxxExternalClient
- **包路径**：com.xw.[模块].domain.[功能].client
- **方法**：
  - `callXxx(...)`: XxxResult — [描述调用的外部服务]

### 2.2 Feign 接口

- **接口名**：XxxRest
- **路径前缀**：/cloudApi/
- **方法**：[接口方法列表]

### 2.3 中间件 Client

- **接口名**：XxxRedisClient / XxxMqClient
- **方法**：[封装的中间件操作]

---

## 3. 用例层 (Application)

### 3.1 Command（写操作）

| 命令类 | Handler 类 | 输入 | 输出 | 业务逻辑摘要 |
|-------|-----------|------|------|------------|
| CreateXxxCmd | CreateXxxCmd.Handler | CreateXxxCmd | String (id) | 创建聚合根，发布事件 |
| UpdateXxxCmd | UpdateXxxCmd.Handler | UpdateXxxCmd | void | 更新状态/属性 |

### 3.2 Query（读操作）

| 查询类 | 输入 | 输出 | 查询逻辑摘要 |
|-------|------|------|------------|
| GetXxxQuery | id: String | XxxVo | 按 ID 查询单条 |
| ListXxxQuery | ListXxxQuery | Page\<XxxVo\> | 分页查询列表 |

---

## 4. 适配层 (Adapter)

### 4.1 Controller

| Controller 类 | 路径前缀 | 用途 |
|-------------|---------|------|
| XxxController | /appApi/ | 前端调用，需加 @NeedLogin |
| XxxCloudController | /cloudApi/ | 微服务间调用 |

**API 清单**：

| HTTP 方法 | 路径 | 请求 DTO | 响应 VO | 描述 |
|---------|------|---------|---------|------|
| POST | /appApi/xxx/create | CreateXxxDto | String | 创建 Xxx |
| GET | /appApi/xxx/{id} | - | XxxVo | 查询 Xxx |

### 4.2 Repository 实现

- **类名**：XxxRepositoryImpl
- **实现接口**：XxxRepository
- **依赖**：XxxJpaRepository（JPA）或 XxxMapper（MyBatis）
- **关键方法实现**：[描述 ORM 映射逻辑]

### 4.3 Client 实现

- **类名**：XxxExternalClientImpl / XxxClientImpl
- **实现接口**：XxxExternalClient
- **依赖**：XxxRest（Feign）
- **关键逻辑**：[描述外部调用方式和错误处理]

### 4.4 事件监听器

| 监听器类 | 监听事件 | 处理逻辑 |
|---------|---------|---------|
| XxxCreatedEventListener | XxxCreatedEvent | [处理逻辑描述] |

---

## 更新记录

| 时间 | 阶段 | 更新内容 | 更新人 |
|------|------|---------|-------|
| [时间] | Phase 2 | 初始 Spec 生成 | AI |
