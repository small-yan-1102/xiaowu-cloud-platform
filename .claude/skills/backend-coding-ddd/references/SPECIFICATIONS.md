# 版权服务器开发规范文档

## 1. 命名约定和代码风格

### 1.1 包命名规范
```
com.xw.[模块].[层级].[功能]
```

### 1.2 类命名规范

#### 领域层类命名
- 聚合根：`[业务名称]` (如：CopyrightOrder, UserAccount)
- 实体：`[业务名称]` (如：CopyrightInfo, UserProfile)
- 值对象：`[业务名称]` (如：Price, Address)

#### 应用层类命名
- 命令类：`[业务名称] + Cmd` (如：CreateCopyrightOrderCmd)
- 查询类：`[业务名称] + Query` (如：CopyrightOrderQuery)

#### 适配器层类命名
- 客户端实现：`[业务名称] + ClientImpl` (如：CopyrightOrderClientImpl)
- Feign接口：`[业务名称] + Rest` (如：CopyrightOrderRest, UserAccountRest)
- 消息消费者：`[业务名称] + Consumer` (如：CopyrightOrderProcessConsumer)
- 面向服务Controller接口：`[业务名称] + CloudController` (如：CopyrightOrderCloudController, UserAccountCloudController)
- 面向前端Controller接口：`[业务名称] + Controller` (如：CopyrightOrderController, UserAccountController)

#### 适配器层Controller接口路径规范

##### 面向服务的Controller接口（CloudController）
面向服务的Controller接口用于微服务之间的内部调用，所有接口路径必须以 `/cloudApi/` 为前缀。

**命名规则：**
- 类名以 `CloudController` 结尾
- 类级别 `@RequestMapping` 路径格式：`/cloudApi/[业务模块]`
- 方法级别路径按照 RESTful 风格定义

**代码示例：**
```java
@RestController
@RequestMapping("/cloudApi/copyrightOrder")
@RequiredArgsConstructor
public class CopyrightOrderCloudController {

    @PostMapping("/confirm")
    public ApiResponse<Void> confirm(@RequestBody ConfirmCopyrightOrderDto dto) {
        // ...
    }

    @GetMapping("/detail/{copyrightOrderId}")
    public ApiResponse<CopyrightOrderVo> detail(@PathVariable String copyrightOrderId) {
        // ...
    }
}
```

##### 面向前端的Controller接口（Controller）
面向前端的Controller接口用于提供给前端应用（Web、App等）调用，所有接口路径必须以 `/appApi/` 为前缀。

**命名规则：**
- 类名以 `Controller` 结尾（不带 `Cloud` 前缀）
- 类级别 `@RequestMapping` 路径格式：`/appApi/[业务模块]`
- 方法级别路径按照 RESTful 风格定义

**代码示例：**
```java
@RestController
@RequestMapping("/appApi/copyrightOrder")
@RequiredArgsConstructor
public class CopyrightOrderController {

    @PostMapping("/create")
    public ApiResponse<String> create(@RequestBody CreateCopyrightOrderDto dto) {
        // ...
    }

    @GetMapping("/list")
    public ApiResponse<PageResult<CopyrightOrderVo>> list(CopyrightOrderQuery query) {
        // ...
    }
}
```

##### 路径规范总结
| 接口类型 | 类命名后缀 | 路径前缀 | 调用方 |
|---------|-----------|---------|-------|
| 面向服务 | `CloudController` | `/cloudApi/` | 其他微服务 |
| 面向前端 | `Controller` | `/appApi/` | 前端应用（Web、App等） |

#### 共享层类命名
- DTO：`[业务名称] + Dto` (如：CreateCopyrightOrderDto)
- VO：`[业务名称] + Vo` (如：CopyrightOrderVo)
- 异常：仅使用WarnException和ErrorException两种类型

#### 事件类命名
- 领域事件：`[业务名称] + [动作] + Event` (如：CopyrightOrderConfirmSuccessEvent)
- 集成事件：`[业务名称] + [动作] + IntegrationEvent` (如：CopyrightOrderConfirmSuccessIntegrationEvent)

### 1.3 实体方法命名规范

#### 1.3.1 创建行为规范
创建行为用于实例化新的领域对象或实体，应遵循以下规范：

**命名原则：**
- 使用静态工厂方法模式
- 方法名以`create`作为开头
- 参数应包含创建对象所需的必要信息
- 返回新创建的对象实例

**代码示例：**
```java
// 聚合根创建
public static CopyrightOrder create(String unionOrderId, String copyrightOrderId, CopyrightInfo copyrightInfo) {
    CopyrightOrder order = new CopyrightOrder();
    order.unionOrderId = unionOrderId;
    order.copyrightOrderId = copyrightOrderId;
    order.copyrightInfo = copyrightInfo;
    order.status = OrderStatus.PENDING;
    order.createdAt = LocalDateTime.now();
    return order;
}

// 实体创建
public static CopyrightInfo create(String title, String author, String content) {
    CopyrightInfo info = new CopyrightInfo();
    info.title = title;
    info.author = author;
    info.content = content;
    info.createdAt = LocalDateTime.now();
    return info;
}

// 值对象创建
public static Price create(BigDecimal amount, String currency) {
    return new Price(amount, currency);
}

// 带验证的创建方法
public static CopyrightOrder createWithValidation(CreateCopyrightOrderRequest request) {
    // 参数验证
    if (StringUtils.isBlank(request.getUnionOrderId())) {
        throw new WarnException("统一订单ID不能为空");
    }
    
    if (request.getCopyrightInfo() == null) {
        throw new WarnException("版权信息不能为空");
    }
    
    // 创建对象
    CopyrightOrder order = create(
        request.getUnionOrderId(), 
        request.getCopyrightOrderId(), 
        request.getCopyrightInfo()
    );
    
    // 初始化业务状态
    order.initializeBusinessState();
    return order;
}
```

#### 1.3.2 业务行为规范
业务行为表示领域对象的核心业务逻辑和状态变更，应遵循以下规范：

**命名原则：**
- 采用动词+名词的格式
- 动词表示具体的操作或状态变化
- 名词表示操作的对象或结果
- 方法名应能清晰表达业务意图

**常用动词前缀：**
- `upload` - 上传相关操作
- `confirm` - 确认相关操作
- `process` - 处理相关操作
- `submit` - 提交相关操作
- `cancel` - 取消相关操作
- `complete` - 完成相关操作
- `fail` - 失败相关操作
- `retry` - 重试相关操作

**代码示例：**
```java
// 上传成功处理
public void uploadSuccess(String result) {
    this.submitStatus = CopyrightOrderSubmitStatusEnum.SUCCEED.getCode();
    this.submitResult = result;
    this.submittedAt = LocalDateTime.now();
    
    // 发布领域事件
    publisher().attachEvent(CopyrightOrderUploadSuccessEvent.builder()
        .copyrightOrder(this)
        .build());
}

// 确认失败处理
public void confirmFail(String errorMessage) {
    this.confirmStatus = CopyrightOrderConfirmStatusEnum.FAILED.getCode();
    this.confirmResult = errorMessage;
    this.confirmedAt = LocalDateTime.now();
    
    // 发布确认失败事件
    publisher().attachEvent(CopyrightOrderConfirmFailEvent.builder()
        .copyrightOrder(this)
        .errorMessage(errorMessage)
        .build());
}

// 处理支付
public void processPayment(PaymentInfo paymentInfo) {
    if (this.paymentStatus == PaymentStatus.PAID) {
        throw new WarnException("订单已支付，无需重复处理");
    }
    
    // 验证支付信息
    if (!paymentInfo.isValid()) {
        throw new WarnException("支付信息无效");
    }
    
    // 更新支付状态
    this.paymentStatus = PaymentStatus.PAID;
    this.paidAmount = paymentInfo.getAmount();
    this.paidAt = LocalDateTime.now();
    
    // 发布支付成功事件
    publisher().attachEvent(PaymentProcessedEvent.builder()
        .orderId(this.id)
        .amount(paymentInfo.getAmount())
        .build());
}

// 取消订单
public void cancel(String reason) {
    if (this.status == OrderStatus.COMPLETED) {
        throw new WarnException("已完成订单无法取消");
    }
    
    this.status = OrderStatus.CANCELLED;
    this.cancelledAt = LocalDateTime.now();
    this.cancelReason = reason;
    
    // 发布取消事件
    publisher().attachEvent(OrderCancelledEvent.builder()
        .orderId(this.id)
        .reason(reason)
        .build());
}


```


### 1.4 变量命名规范
- 使用驼峰命名法
- 布尔类型变量应使用过去完成时进行表达，避免使用`is`前缀
- 集合类型使用复数形式（如：`orders`, `users`）
- 常量使用全大写加下划线（如：`MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`）

**布尔变量命名示例：**
- 删除状态：`deleted` 而不是 `isDeleted`
- 启用状态：`enabled` 而不是 `isEnabled`  
- 激活状态：`activated` 而不是 `isActive`
- 完成状态：`completed` 而不是 `isCompleted`
- 锁定状态：`locked` 而不是 `isLocked`

## 2. 异常处理和日志规范

### 2.1 异常层次结构

#### 基础异常类型
```java
// 警告级别异常
@Data
@Slf4j
public class WarnException extends RuntimeException {
    private Integer code;
    private String msg;
    
    public WarnException(String msg) {
        super(msg);
        this.code = 400;
        this.msg = msg;
    }
    
    public WarnException(Integer code, String msg) {
        super(msg);
        this.code = code;
        this.msg = msg;
    }
}

// 错误级别异常
@Data
@Slf4j
public class ErrorException extends RuntimeException {
    private Integer code;
    private String msg;
    
    public ErrorException(String msg) {
        super(msg);
        this.code = 500;
        this.msg = msg;
    }
    
    public ErrorException(Integer code, String msg) {
        super(msg);
        this.code = code;
        this.msg = msg;
    }
}
```

### 2.2 异常处理规范

#### 异常使用原则
```java
// 业务警告异常
throw new WarnException("参数校验失败");

// 业务特定警告
throw new WarnException(400, "版权信息不存在");

// 系统错误异常
throw new ErrorException("数据库连接失败");

// 系统特定错误
throw new ErrorException(500, "系统内部错误");
```

#### 全局异常处理器
```java
@RestControllerAdvice
@Slf4j
public class CommonExceptionHandler {
    @ExceptionHandler(value = WarnException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ApiResponse<Object> handleWarnException(WarnException e) {
        log.warn("业务警告: {}", e.getMsg());
        return ApiResponse.fail(e.getCode(), e.getMsg());
    }
    
    @ExceptionHandler(value = ErrorException.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse<Object> handleErrorException(ErrorException e) {
        log.error("系统错误: {}", e.getMsg(), e);
        return ApiResponse.fail(e.getCode(), e.getMsg());
    }
    
    @ExceptionHandler(Throwable.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ApiResponse<Object> handleError(HttpServletRequest request, Throwable e) {
        log.error(String.format("发生未知异常:%s request:%s", e.getMessage(), getRequestInfo(request)), e);
        return ApiResponse.fail(500, "系统内部错误");
    }
}
```

### 2.3 日志规范

#### 日志级别使用
```java
// INFO级别 - 业务流程关键节点
log.info("创建版权订单成功, orderId: {}, copyrightId: {}", orderId, copyrightId);

// WARN级别 - 业务警告信息
log.warn("版权订单处理超时, orderId: {}, elapsed: {}ms", orderId, elapsedTime);

// ERROR级别 - 系统错误
log.error("处理版权订单失败, orderId: {}", orderId, exception);

// DEBUG级别 - 调试信息
if (log.isDebugEnabled()) {
    log.debug("版权订单详细信息: {}", JSON.toJSONString(order));
}
```


## 3. DDD实现规范

### 3.1 聚合根规范

#### 聚合根定义
```java
/**
 * 版权订单聚合根
 * @author lambert
 * @since 2024-01-01
 */
@AggregateRoot
@Entity
@Table(name = "`copyright_order`")
@DynamicInsert
@DynamicUpdate
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Data
@Where(clause = "deleted = 0")
public class CopyrightOrder extends BaseEntity {
    /**
     * 主键ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "`id`")
    private Long id;
    
    /**
     * 版权订单ID
     * 业务唯一标识
     */
    @Column(name = "`copyright_order_id`", nullable = false, length = 64)
    private String copyrightOrderId;
    
    // 包含业务行为的方法
    public void uploadSuccess(String result) {
        this.submitStatus = CopyrightOrderSubmitStatusEnum.SUCCEED.getCode();
        this.submitResult = result;
        publisher().attachEvent(CopyrightOrderUploadSuccessEvent.builder()
            .copyrightOrder(this).build());
    }
}
```

#### 聚合根设计原则
1. 聚合根是聚合的唯一入口点
2. 聚合内部的一致性由聚合根保证
3. 聚合之间通过ID引用，避免直接持有其他聚合根的引用
4. 聚合根包含业务逻辑和领域行为

### 3.2 实体规范

#### 实体定义
```java
@Entity
@Table(name = "`copyright_info`")
@DynamicInsert
@DynamicUpdate
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Where(clause = "deleted = 0")
public class CopyrightInfo extends BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "`title`", nullable = false, length = 255)
    private String title;
    
    @Column(name = "`author`", length = 100)
    private String author;
    
    // 实体可以有自己的业务方法
    public boolean isValid() {
        return StringUtils.isNotBlank(title) && StringUtils.isNotBlank(author);
    }
}
```

### 3.3 值对象规范

#### 值对象实现
```java
// 值对象应该具备不可变性
@Value
@Builder
public class PriceVO {
    private BigDecimal amount;
    private String currency;
    
    // 值相等性比较
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        PriceVO priceVO = (PriceVO) o;
        return Objects.equals(amount, priceVO.amount) && 
               Objects.equals(currency, priceVO.currency);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(amount, currency);
    }
}
```

### 3.4 领域服务规范

#### 领域服务定义
```java
@Service
@RequiredArgsConstructor
public class CopyrightValidationService {
    
    public ValidationResult validateCopyright(CopyrightInfo copyrightInfo) {
        // 领域服务处理跨聚合的业务逻辑
        if (!isValidTitle(copyrightInfo.getTitle())) {
            return ValidationResult.invalid("标题格式不正确");
        }
        
        if (!isValidAuthor(copyrightInfo.getAuthor())) {
            return ValidationResult.invalid("作者信息不完整");
        }
        
        return ValidationResult.valid();
    }
    
    private boolean isValidTitle(String title) {
        return StringUtils.isNotBlank(title) && title.length() <= 255;
    }
    
    private boolean isValidAuthor(String author) {
        return StringUtils.isNotBlank(author) && author.length() <= 100;
    }
}
```

### 3.4 领域事件规范

#### 事件定义规范
```java
// 内部事件 - 同一进程内处理
@DomainEvent
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CopyrightOrderCreatedEvent {
    private CopyrightOrder copyrightOrder;
}

// 集成事件 - 跨服务处理
@DomainEvent("copyright.order.created")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CopyrightOrderCreatedIntegrationEvent {
    private String copyrightOrderId;
    private String unionOrderId;
    private Long copyrightId;
}
```

#### 事件发布规范
```java
// 在聚合根中发布事件
public class CopyrightOrder extends BaseEntity {
    public void create() {
        // 业务逻辑处理...
        this.status = OrderStatus.CREATED;
        
        // 发布领域事件
        publisher().attachEvent(CopyrightOrderCreatedEvent.builder()
            .copyrightOrder(this)
            .build());
    }
}
```

## 4. 各层职责划分和交互规范

### 4.1 领域层职责
- 包含核心业务逻辑
- 定义聚合根、实体、值对象
- 实现领域事件机制
- 提供规范验证服务

### 4.2 应用层职责
- 协调领域对象完成业务用例
- 实现命令和查询模式
- 提供工作单元事务管理

### 4.3 适配器层职责
- 提供外部接口（REST API、消息队列等）
- 实现外部服务客户端
- 处理数据持久化
- 集成第三方中间件
- **中间件的唯一引入层**：所有中间件（Redis、MQ、Elasticsearch、OSS 等）的依赖引入和直接使用仅限于适配器层，其他任何层（领域层、应用层、共享层）禁止直接引入或使用中间件相关的类和依赖

### 4.4 共享层职责
- 提供通用的DTO、VO
- 定义异常体系
- 实现工具类和常量
- 提供基础组件

### 4.5 层间交互规范
```
适配器层 → 应用层 → 领域层
    ↓          ↓         ↓
共享层 ← 共享层 ← 共享层
```

### 4.6 应用层中间件隔离规范

#### 核心原则
应用层**禁止直接使用任何中间件**（如 Redis、MQ、Elasticsearch 等），所有对中间件的依赖必须通过封装的 Client 接口进行间接调用。Client 接口的定义**不应暴露底层中间件实现细节**，而应根据业务语义进行命名和设计。

#### 规范要求
1. **应用层不允许直接注入中间件客户端**：如 `RedissonClient`、`StringRedisTemplate`、`RabbitTemplate`、`KafkaTemplate` 等中间件原生客户端不得出现在应用层代码中。
2. **封装业务语义化的 Client 接口**：在共享层或领域层定义接口，在适配器层实现，接口命名和方法签名应体现业务含义而非技术实现。
3. **Client 接口不体现中间件**：接口名称和方法不应包含 `Redis`、`MQ`、`Kafka`、`Cache` 等中间件关键词，而应使用业务术语。

#### 反面示例（禁止）
```java
// ❌ 应用层直接使用 Redis
@Service
@RequiredArgsConstructor
public class OrderCmd {
    private final RedissonClient redissonClient;
    
    public void exec(String orderId) {
        RLock lock = redissonClient.getLock("order-lock:" + orderId);
        // ...
    }
}

// ❌ Client接口暴露中间件细节
public interface OrderRedisClient {
    void setOrderCache(String key, String value);
    String getOrderCache(String key);
}
```

#### 正面示例（推荐）
```java
// ✅ 定义业务语义化的 Client 接口（共享层/领域层）
public interface OrderLockClient {
    /**
     * 尝试获取订单操作锁
     */
    boolean tryLock(String orderId, long timeout, TimeUnit unit);
    
    /**
     * 释放订单操作锁
     */
    void unlock(String orderId);
}

public interface OrderSnapshotClient {
    /**
     * 保存订单快照
     */
    void saveSnapshot(String orderId, OrderSnapshot snapshot);
    
    /**
     * 获取订单快照
     */
    OrderSnapshot getSnapshot(String orderId);
}

// ✅ 适配器层实现（内部使用中间件）
@Component
@RequiredArgsConstructor
public class OrderLockClientImpl implements OrderLockClient {
    private final RedissonClient redissonClient;
    
    @Override
    public boolean tryLock(String orderId, long timeout, TimeUnit unit) {
        RLock lock = redissonClient.getLock("order-lock:" + orderId);
        try {
            return lock.tryLock(timeout, unit);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }
    
    @Override
    public void unlock(String orderId) {
        RLock lock = redissonClient.getLock("order-lock:" + orderId);
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}

// ✅ 应用层通过 Client 接口调用
@Service
@RequiredArgsConstructor
public class OrderCmd {
    private final OrderLockClient orderLockClient;
    
    public void exec(String orderId) {
        if (orderLockClient.tryLock(orderId, 3, TimeUnit.SECONDS)) {
            try {
                // 业务逻辑
            } finally {
                orderLockClient.unlock(orderId);
            }
        }
    }
}
```

## 5. 数据库表结构设计规范

### 5.1 表命名规范
- 聚合根表：使用业务名称，如 `copyright_order`
- 关联表：使用 `_relation` 后缀，如 `m2m_student_course_relation`
- 系统表：使用双下划线前缀，如 `__event`, `__task_record`

### 5.2 字段设计规范

#### 基础字段
```sql
-- 主键字段
`id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID',

-- 业务字段
`copyright_order_id` varchar(64) NOT NULL COMMENT '版权订单ID',
`title` varchar(255) NOT NULL COMMENT '标题',
`amount` decimal(10,2) DEFAULT NULL COMMENT '金额',

-- 状态字段
`status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '状态',
`deleted` tinyint(1) NOT NULL DEFAULT '0' COMMENT '删除标识',

-- 时间戳字段
`created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
`updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
```

#### 索引设计
```sql
-- 主键索引
PRIMARY KEY (`id`),

-- 唯一索引
UNIQUE KEY `uk_copyright_order_id` (`copyright_order_id`),

-- 普通索引
KEY `idx_status` (`status`),
KEY `idx_created_at` (`created_at`),

-- 复合索引
KEY `idx_status_created` (`status`, `created_at`)
```

### 5.3 软删除规范
```java
// 使用 @Where 注解实现软删除
@Where(clause = "deleted = 0")
public class CopyrightOrder extends BaseEntity {
    @Column(name = "`deleted`", nullable = false, columnDefinition = "TINYINT DEFAULT 0")
    private Boolean deleted = false;
}
```

## 6. 分片策略规范

### 6.1 数据库分片
```java
// Saga表按月分区示例
private void addPartition(String table, Date date) {
    String sql = "alter table `" + table + "` add partition " +
                "(partition p" + DateFormatUtils.format(date, "yyyyMM") + 
                " values less than (to_days('" + 
                DateFormatUtils.format(DateUtils.addMonths(date, 1), "yyyy-MM") + 
                "-01')) ENGINE=InnoDB)";
    jdbcTemplate.execute(sql);
}
```

### 6.2 分片策略选择
- 按时间分片：适用于日志、事件等时间序列数据
- 按业务ID分片：适用于用户、订单等业务数据
- 按哈希分片：适用于需要均匀分布的场景

## 7. 定时任务和异步处理规范

### 7.1 XXL-JOB任务规范

#### 任务处理器定义
```java
@Component
@JobHandler(value = "copyrightOrderConfirmJob")
@Slf4j
public class CopyrightOrderConfirmJobHandler extends IJobHandler {
    @Resource
    private CopyrightOrderConfirmCmd.Handler copyrightOrderConfirmHandler;
    
    @Override
    public ReturnT<String> execute(String param) throws Exception {
        try {
            copyrightOrderConfirmHandler.exec();
            return SUCCESS;
        } catch (Exception e) {
            log.error("版权订单确认任务执行失败", e);
            return FAIL;
        }
    }
}
```

#### 任务配置规范
- 任务名称：使用业务名称 + Job后缀
- 执行频率：根据业务需求合理设置
- 超时时间：设置合理的超时阈值
- 失败重试：配置适当的重试策略

### 7.2 Spring Scheduled任务规范

#### 分布式锁保护
```java
@Component
@RequiredArgsConstructor
public class CopyrightOrderTask {
    @Scheduled(cron = "1 * * * * ?")
    public void confirmCopyrightOrderTask() {
        RLock lock = redissonClient.getLock("copyright-order-confirm");
        try {
            if (lock.tryLock(3, TimeUnit.SECONDS)) {
                // 执行业务逻辑
                processPendingOrders();
            }
        } catch (Exception e) {
            log.error("执行版权订单确认任务失败", e);
        } finally {
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
```

#### 任务执行规范
- 使用分布式锁防止重复执行
- 设置合理的执行间隔
- 记录详细的执行日志
- 实现优雅的任务中断

### 7.3 异步处理规范

#### @Async注解使用
```java
@Service
@Async("taskExecutor")
@Slf4j
public class AsyncProcessingService {
    
    public void processCopyrightOrderAsync(String orderId) {
        try {
            // 异步处理逻辑
            processOrder(orderId);
        } catch (Exception e) {
            log.error("异步处理版权订单失败: {}", orderId, e);
        }
    }
}
```

#### 线程池配置
```java
@Configuration
@EnableAsync
public class ThreadPoolExecutorAsyncConfig {
    
    @Bean("taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(200);
        executor.setKeepAliveSeconds(60);
        executor.setThreadNamePrefix("async-task-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }
}
```

## 8. 代码质量要求

### 8.1 注解使用规范
```java
/**
 * 版权订单聚合根
 * @author lambert
 * @since 2024-01-01
 */
@Entity
@Table(name = "`copyright_order`")
@DynamicInsert
@DynamicUpdate
@AllArgsConstructor
@NoArgsConstructor
@Builder
@Data
@Where(clause = "deleted = 0")
public class CopyrightOrder extends BaseEntity {
    /**
     * 主键ID
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "`id`")
    private Long id;
}
```

### 8.2 事务管理规范

#### 事务传播行为
```java
// 默认使用REQUIRED
@Transactional(rollbackFor = Exception.class, propagation = Propagation.REQUIRED)

// 需要新事务时使用REQUIRES_NEW
@Transactional(rollbackFor = Exception.class, propagation = Propagation.REQUIRES_NEW)

// 只读事务
@Transactional(readOnly = true, propagation = Propagation.SUPPORTS)
```

#### 工作单元使用
```java
// 推荐使用UnitOfWork进行事务管理
UnitOfWork.saveTransactional(() -> {
    // 业务逻辑
    copyrightOrderRepository.save(order);
    copyrightInfoRepository.updateStatus(infoId, "PROCESSING");
    return orderId;
});

// 批量操作
UnitOfWork.saveEntities(Arrays.asList(entity1, entity2, entity3));

// 自定义查询
List<CopyrightOrder> orders = UnitOfWork.queryList(
    CopyrightOrder.class, 
    CopyrightOrder.class, 
    (cb, cq, root) -> {
        cq.where(cb.equal(root.get("status"), "PENDING"));
    }
);
```

### 8.3 性能优化规范

#### 查询优化
```java
// 避免N+1查询问题
@Query("SELECT co FROM CopyrightOrder co LEFT JOIN FETCH co.copyrightInfo WHERE co.status = :status")
List<CopyrightOrder> findByStatusWithInfo(@Param("status") String status);

// 使用分页查询
Page<CopyrightOrder> findByStatus(String status, Pageable pageable);
```

#### 缓存使用
```java
@Service
@CacheConfig(cacheNames = "copyright")
public class CopyrightInfoService {
    
    @Cacheable(key = "#id")
    public CopyrightInfo findById(Long id) {
        return copyrightInfoRepository.findById(id)
            .orElseThrow(() -> new WarnException("版权信息不存在"));
    }
    
    @CacheEvict(key = "#result.id")
    public CopyrightInfo save(CopyrightInfo info) {
        return copyrightInfoRepository.save(info);
    }
}
```

---
*文档版本：1.0*
*最后更新：2024年12月*
*适用项目：copyright-server*