# 架构与命名规范

> 本文档为 Tool Wrapper 模式资源，在 Phase 2-3 设计阶段及 Phase 4 编写领域层/适配层时加载。

---

## 项目架构概览

本项目采用**六边形架构**（端口适配器架构）结合**领域驱动设计**（DDD）。

### 模块划分

```
[module]-server/
├── [module]-server-start/        # 启动模块（Spring Boot 入口）
├── [module]-server-domain/       # 领域层（核心业务逻辑，零基础设施依赖）
├── [module]-server-application/  # 应用层（业务编排，Command/Query）
├── [module]-server-adapter/      # 适配器层（Controller、Repository 实现、Client 实现）
└── [module]-server-share/        # 共享层（公共组件、枚举、常量）
```

### 包结构约定

```
com.xw.[模块].[层级].[聚合根功能]/
```

示例：

```
com.xw.copyright.domain.order/         # 版权订单领域层
com.xw.copyright.application.order/    # 版权订单用例层
com.xw.copyright.adapter.order/        # 版权订单适配层
```

---

## 命名规范速查

| 类型 | 命名格式 | 示例 |
|------|---------|------|
| 聚合根 | `[业务名称]`（无后缀） | `CopyrightOrder` |
| 实体 | `[业务名称]`（无后缀） | `OrderItem` |
| 值对象 | `[业务名称]`（无后缀） | `Money`、`OrderStatus` |
| 领域事件 | `[业务名称][动作]Event` | `CopyrightOrderConfirmSuccessEvent` |
| Repository 接口 | `[聚合根名称]Repository` | `CopyrightOrderRepository` |
| Repository 实现 | `[聚合根名称]RepositoryImpl` | `CopyrightOrderRepositoryImpl` |
| JPA Repository | `[聚合根名称]JpaRepository` | `CopyrightOrderJpaRepository` |
| 命令类 | `[业务动作][聚合根]Cmd` | `CreateCopyrightOrderCmd` |
| 查询类 | `[聚合根名称]Query` | `CopyrightOrderQuery`、`ListCopyrightOrderQuery` |
| DTO（入参） | `[业务动作][聚合根]Dto` | `CreateCopyrightOrderDto` |
| VO（出参） | `[聚合根名称]Vo` | `CopyrightOrderVo` |
| Feign 接口 | `[聚合根名称]Rest` | `CopyrightOrderRest` |
| 外部 Client 接口 | `[业务名称]ExternalClient` | `CopyrightOrderExternalClient` |
| Client 实现 | `[聚合根名称]ClientImpl` | `CopyrightOrderClientImpl` |
| 前端 Controller | `[聚合根名称]Controller` | `CopyrightOrderController` |
| 云端 Controller | `[聚合根名称]CloudController` | `CopyrightOrderCloudController` |
| 事件监听器 | `[事件名称]Listener` | `CopyrightOrderCreatedEventListener` |

---

## Controller 路径规范

| 类型 | 路径前缀 | 鉴权注解 | 用途 |
|------|---------|---------|------|
| Controller（前端） | `/appApi/` | `@NeedLogin`（**强制**） | 前端 App 调用 |
| CloudController（微服务） | `/cloudApi/` | 无需 | 微服务间内部调用 |

**示例**：

```java
// ✅ 前端接口
@RestController
@RequestMapping("/appApi/copyright/order")
public class CopyrightOrderController {
    @NeedLogin   // ← 必须
    @PostMapping("/create")
    public Result<String> create(...) { ... }
}

// ✅ 微服务接口
@RestController
@RequestMapping("/cloudApi/copyright/order")
public class CopyrightOrderCloudController {
    @PostMapping("/create")
    public Result<String> create(...) { ... }
}
```

---

## DDD 核心规则

### 聚合根创建

```java
// ✅ 必须使用静态工厂方法
public static CopyrightOrder create(String unionOrderId, String userId) {
    CopyrightOrder order = new CopyrightOrder();
    order.setId(IdGenerator.generate());
    order.setStatus(OrderStatus.PENDING);
    order.publisher().attachEvent(new CopyrightOrderCreatedEvent(order.getId()));
    return order;
}

// ❌ 禁止直接 new
CopyrightOrder order = new CopyrightOrder();
order.setId(...);
order.setStatus(...);
```

### 业务行为封装

```java
// ✅ 业务行为在聚合根内
public void confirmSuccess(String approveUserId) {
    if (!ConfirmStatusEnum.PENDING.getCode().equals(this.confirmStatus)) {
        throw new WarnException("当前状态不允许确认");
    }
    this.confirmStatus = ConfirmStatusEnum.SUCCEED.getCode();
    this.approveUserId = approveUserId;
    this.publisher().attachEvent(new CopyrightOrderConfirmSuccessEvent(this.getId()));
}

// ❌ 禁止在 Service/Handler 中直接操作聚合根字段
order.setConfirmStatus(ConfirmStatusEnum.SUCCEED.getCode());
```

### 领域事件发布

```java
// ✅ 在聚合根业务方法内发布
this.publisher().attachEvent(new XxxCreatedEvent(this.getId()));

// ❌ 禁止在 Handler/Service 中发布领域事件
eventPublisher.publishEvent(new XxxCreatedEvent(order.getId()));
```

### Repository 依赖方向

- **领域层**定义 Repository **接口**（端口）
- **适配层**实现 Repository（实现类）
- 领域层/应用层只依赖接口，**绝不直接依赖** JPA/MyBatis

```java
// domain 层
public interface CopyrightOrderRepository {
    Optional<CopyrightOrder> findById(String id);
    void save(CopyrightOrder order);
}

// adapter 层
@Component
public class CopyrightOrderRepositoryImpl implements CopyrightOrderRepository {
    @Autowired
    private CopyrightOrderJpaRepository jpaRepository;
    // ...
}
```

---

## 常用公共组件

| 组件 | 用途 | 禁止的替代方案 |
|------|------|-------------|
| `IdGenerator.generate()` | 生成全局唯一 ID | UUID、雪花算法直接调用 |
| `LockerService` | 分布式锁 | 自行实现 RedisLock |
| `RetryUtil` | 重试机制 | 手写 while 循环重试 |
| `MapperUtil` | 对象转换（Bean Copy） | 手写 get/set 转换 |
| `StrUtil.isBlank()` | 字符串判空 | `== null` 或 `"".equals()` |
| `CollectionUtils.isEmpty()` | 集合判空 | `== null` 或 `.size() == 0` |
| `WarnException` | 业务警告异常（前端提示） | RuntimeException |
| `ErrorException` | 系统错误异常（内部错误） | Exception |
