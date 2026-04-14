# AI Coding 编码规范（代码层）

> 本文档在编写业务代码时加载，包含代码风格、设计原则、实现规范。

---

## 1. 方法返回值规范

### 1.1 禁止使用 Map 作为返回值

**方法返回值必须使用具体的 POJO 类，禁止使用 Map 传递数据**。

#### 问题说明

使用 Map 作为返回值存在以下问题：
1. **类型不安全**：编译期无法检查类型，运行时可能出现 ClassCastException
2. **可读性差**：调用方无法直观知道返回哪些字段
3. **维护困难**：字段变更容易遗漏，重构成本高
4. **无法利用 IDE 提示**：没有代码补全和跳转

```java
// ❌ 禁止：返回 Map，类型不安全，可读性差
public Map<String, Object> getOrderInfo(String orderId) {
    Map<String, Object> result = new HashMap<>();
    result.put("orderId", orderId);
    result.put("status", 1);
    result.put("amount", new BigDecimal("100.00"));
    result.put("createTime", LocalDateTime.now());
    return result;
}

// 调用方使用时容易出错
Map<String, Object> orderInfo = getOrderInfo("123");
String orderId = (String) orderInfo.get("orderId");  // 需要强制类型转换
Integer status = (Integer) orderInfo.get("status");  // 可能 NullPointerException
// 拼写错误也不会被发现
Object amount = orderInfo.get("amout");  // 返回 null，难以排查
```

```java
// ✅ 正确：返回具体的 POJO
@Data
public class OrderInfo {
    private String orderId;
    private Integer status;
    private BigDecimal amount;
    private LocalDateTime createTime;
}

public OrderInfo getOrderInfo(String orderId) {
    OrderInfo info = new OrderInfo();
    info.setOrderId(orderId);
    info.setStatus(1);
    info.setAmount(new BigDecimal("100.00"));
    info.setCreateTime(LocalDateTime.now());
    return info;
}

// 调用方使用时有类型安全保证
OrderInfo orderInfo = getOrderInfo("123");
String orderId = orderInfo.getOrderId();  // 类型安全，有代码补全
Integer status = orderInfo.getStatus();   // 无需强制转换
```

#### 特殊情况

以下情况可以使用 Map：
- **动态配置/元数据**：如 `Map<String, ConfigValue>` 表示配置项
- **第三方接口适配**：与外部系统交互时的临时转换
- **框架底层实现**：如 MyBatis 参数传递

---

## 2. 单一职责原则

**一个业务逻辑对应一个 private 方法**，保持方法职责单一。

```java
// ❌ 禁止：方法职责不单一
public void createOrder(CreateOrderDto dto) {
    // 1. 参数校验
    if (StrUtil.isBlank(dto.getUserId())) { ... }
    // 2. 查询用户
    User user = userRepository.findById(dto.getUserId()).orElseThrow(...);
    // 3. 查询产品
    Product product = productRepository.findById(dto.getProductId()).orElseThrow(...);
    // 4. 创建订单
    Order order = Order.create(...);
    orderRepository.save(order);
    // 5. 发送通知
    notificationService.sendOrderCreatedNotification(order);
}

// ✅ 正确：每个业务逻辑封装为独立方法
public void createOrder(CreateOrderDto dto) {
    log.info("开始创建订单, dto: {}", dto);
    
    validateCreateOrderParams(dto);
    User user = validateAndGetUser(dto.getUserId());
    Product product = getProduct(dto.getProductId());
    BigDecimal totalPrice = calculateTotalPrice(product, dto.getQuantity());
    Order order = createAndSaveOrder(user.getId(), product.getId(), dto.getQuantity(), totalPrice);
    sendOrderNotification(order);
    
    log.info("创建订单完成, orderId: {}", order.getId());
}

private void validateCreateOrderParams(CreateOrderDto dto) { ... }
private User validateAndGetUser(String userId) { ... }
private Product getProduct(String productId) { ... }
private BigDecimal calculateTotalPrice(Product product, Integer quantity) { ... }
private Order createAndSaveOrder(String userId, String productId, Integer quantity, BigDecimal price) { ... }
private void sendOrderNotification(Order order) { ... }
```

### 2.1 使用卫语句减少嵌套层级

**优先使用「卫语句」（Guard Clause）提前返回，避免条件判断包裹大段代码**。

当 `if` 条件内部是方法的主要逻辑时，应将条件反转并提前返回，让主要逻辑保持在方法的最外层。

```java
// ❌ 不推荐：条件包裹大段代码，嵌套层级深
private void retriggerAsyncExpand(Long taskId, VideoTakedownTask task, List<CompositionItemVO> compositions) {
    videoTakedownTaskDetailService.deleteByTaskId(taskId);
    String createType = task.getCreateType();
    if (Objects.equals(TakedownTaskCreateModeEnum.BY_COMPOSITION.getCode(), createType)
            || Objects.equals(TakedownTaskCreateModeEnum.BY_VIDEO_ID.getCode(), createType)) {
        if (CollectionUtils.isEmpty(compositions)) {
            throw new IllegalArgumentException("创建失败任务编辑时必须提供compositions作品列表");
        }
        deleteAndSaveInputData(taskId, createType, compositions);
        triggerAsyncExpand(taskId, task, compositions);
    }
}
```

```java
// ✅ 推荐：使用卫语句提前返回，主要逻辑保持在最外层
private void retriggerAsyncExpand(Long taskId, VideoTakedownTask task, List<CompositionItemVO> compositions) {
    videoTakedownTaskDetailService.deleteByTaskId(taskId);
    String createType = task.getCreateType();
    
    // 卫语句：不满足条件时提前返回
    if (!Objects.equals(TakedownTaskCreateModeEnum.BY_COMPOSITION.getCode(), createType)
            && !Objects.equals(TakedownTaskCreateModeEnum.BY_VIDEO_ID.getCode(), createType)) {
        return;
    }
    
    // 主要逻辑保持在方法最外层，可读性更好
    if (CollectionUtils.isEmpty(compositions)) {
        throw new IllegalArgumentException("创建失败任务编辑时必须提供compositions作品列表");
    }
    deleteAndSaveInputData(taskId, createType, compositions);
    triggerAsyncExpand(taskId, task, compositions);
}
```

#### 使用场景

| 场景 | 卫语句写法 |
|------|------------|
| 参数校验 | `if (param == null) { return; }` |
| 状态检查 | `if (!isValidStatus()) { return; }` |
| 权限校验 | `if (!hasPermission()) { throw new WarnException(...); }` |
| 空集合处理 | `if (CollectionUtils.isEmpty(list)) { return Collections.emptyList(); }` |

#### 优势

1. **减少嵌套**：代码结构更扁平，可读性更高
2. **逻辑清晰**：异常情况先处理，主要逻辑更突出
3. **便于维护**：新增条件时只需添加新的卫语句

---

## 3. ID 生成规范

**ID 生成必须是单独一个方法**，便于维护和替换生成策略。

```java
@Service
@RequiredArgsConstructor
public class OrderService {
    
    private final IdGenerator idGenerator;
    
    public void createOrder(CreateOrderDto dto) {
        String orderId = generateOrderId();  // 独立方法
        // ...
    }
    
    private String generateOrderId() {
        return idGenerator.generate("ORD", 6);
    }
}

// 统一 ID 生成工具
@Component
public class IdGenerator {
    public String generate(String prefix, int randomLength) {
        return prefix + System.currentTimeMillis() + RandomUtil.randomNumbers(randomLength);
    }
    
    public String generateUuid() {
        return IdUtil.simpleUUID();
    }
    
    public Long generateSnowflakeId() {
        return IdUtil.getSnowflakeNextId();
    }
}
```

---

## 4. 异常处理规范

### 3.1 业务逻辑异常考虑

每个业务逻辑都要考虑异常情况：
- 参数校验失败
- 数据不存在
- 状态不正确
- 权限不足
- 业务规则不满足

```java
public Order getOrderDetail(String orderId, String userId) {
    // 参数校验
    if (StrUtil.isBlank(orderId)) {
        throw new WarnException("订单ID不能为空");
    }
    
    // 查询订单
    Order order = orderRepository.findByOrderId(orderId)
        .orElseThrow(() -> new WarnException("订单不存在"));
    
    // 权限校验
    if (!order.getUserId().equals(userId)) {
        throw new WarnException("无权查看该订单");
    }
    
    // 状态校验
    if (OrderStatusEnum.DELETED.getCode().equals(order.getStatus())) {
        throw new WarnException("订单已被删除");
    }
    
    return order;
}
```

### 3.2 外部接口调用规范

涉及外部接口或服务时，**必须考虑超时和异常情况**。

```java
@Slf4j
@Component
@RequiredArgsConstructor
public class ThirdPartyServiceClient {
    
    private final RestTemplate restTemplate;
    private static final int DEFAULT_TIMEOUT_MS = 5000;
    
    public ThirdPartyResponse callExternalService(ThirdPartyRequest request) {
        log.info("开始调用外部服务, request: {}", request);
        
        try {
            ResponseEntity<ThirdPartyResponse> response = restTemplate.exchange(
                externalServiceUrl, HttpMethod.POST, entity, ThirdPartyResponse.class);
            log.info("调用外部服务成功");
            return response.getBody();
            
        } catch (ResourceAccessException e) {
            log.error("调用外部服务超时", e);
            throw new ErrorException("外部服务响应超时，请稍后重试");
        } catch (HttpClientErrorException e) {
            log.error("调用外部服务客户端错误, status: {}", e.getStatusCode(), e);
            throw new WarnException("请求参数错误");
        } catch (HttpServerErrorException e) {
            log.error("调用外部服务服务端错误", e);
            throw new ErrorException("外部服务异常，请稍后重试");
        } catch (Exception e) {
            log.error("调用外部服务未知异常", e);
            throw new ErrorException("调用外部服务失败");
        }
    }
}
```

---

## 5. 枚举判断逻辑封装

**涉及多个枚举类判断时，判断逻辑应封装到枚举类中**。

```java
@Getter
@AllArgsConstructor
public enum OrderStatusEnum {
    PENDING(1, "待处理"),
    PROCESSING(2, "处理中"),
    COMPLETED(3, "已完成"),
    CANCELLED(4, "已取消");
    
    private final Integer code;
    private final String desc;
    
    /** 是否为可处理状态 */
    public boolean isProcessable() {
        return this == PENDING || this == PROCESSING;
    }
    
    /** 是否为终态 */
    public boolean isFinalStatus() {
        return this == COMPLETED || this == CANCELLED;
    }
    
    /** 根据 code 获取枚举 */
    public static OrderStatusEnum fromCode(Integer code) {
        if (code == null) return null;
        for (OrderStatusEnum status : values()) {
            if (status.getCode().equals(code)) return status;
        }
        return null;
    }
    
    /** 判断给定 code 是否为可处理状态 */
    public static boolean isProcessable(Integer code) {
        OrderStatusEnum status = fromCode(code);
        return status != null && status.isProcessable();
    }
}

// 业务代码中使用
public void processOrder(Order order) {
    if (OrderStatusEnum.isProcessable(order.getStatus())) {
        // 可处理状态
    }
}
```

### 5.1 多状态分组判断必须封装为静态方法

**多个状态的组合判断，必须在枚举类中定义状态分组集合和静态判断方法**，禁止在业务代码中出现多个 `Objects.equals()` 的连续判断。

```java
// ❌ 禁止：业务代码中出现冗长的状态判断
public void cancelTask(TakedownTask task) {
    boolean isNonExecutingState = Objects.equals(TakedownTaskStatusEnum.PENDING_REVIEW.getCode(), task.getStatus())
            || Objects.equals(TakedownTaskStatusEnum.REVIEW_REJECTED.getCode(), task.getStatus())
            || Objects.equals(TakedownTaskStatusEnum.CREATING.getCode(), task.getStatus())
            || Objects.equals(TakedownTaskStatusEnum.CREATE_FAILED.getCode(), task.getStatus());
    
    if (!isNonExecutingState) {
        throw new WarnException("当前状态不允许取消");
    }
    // ...
}
```

```java
// ✅ 正确：在枚举类中定义状态分组和判断方法
@Getter
@AllArgsConstructor
public enum TakedownTaskStatusEnum {
    PENDING_REVIEW(1, "待审核"),
    REVIEW_REJECTED(2, "审核驳回"),
    CREATING(3, "创建中"),
    CREATE_FAILED(4, "创建失败"),
    EXECUTING(5, "执行中"),
    COMPLETED(6, "已完成");
    
    private final Integer code;
    private final String desc;
    
    /** 非执行中状态集合（可取消的状态） */
    private static final List<TakedownTaskStatusEnum> NON_EXECUTING_STATUSES = Lists.newArrayList(
            PENDING_REVIEW, REVIEW_REJECTED, CREATING, CREATE_FAILED
    );
    
    /** 判断是否为非执行中状态 */
    public static boolean isNonExecuting(Integer code) {
        TakedownTaskStatusEnum status = fromCode(code);
        return status != null && NON_EXECUTING_STATUSES.contains(status);
    }
    
    /** 根据 code 获取枚举 */
    public static TakedownTaskStatusEnum fromCode(Integer code) {
        if (code == null) return null;
        for (TakedownTaskStatusEnum status : values()) {
            if (status.getCode().equals(code)) return status;
        }
        return null;
    }
}

// 业务代码简洁明了
public void cancelTask(TakedownTask task) {
    if (!TakedownTaskStatusEnum.isNonExecuting(task.getStatus())) {
        throw new WarnException("当前状态不允许取消");
    }
    // ...
}
```

#### 优势

1. **业务代码简洁**：一行代码完成状态判断
2. **逻辑集中**：状态分组定义在枚举内部，便于维护
3. **可复用**：多处业务逻辑可复用同一判断方法
4. **语义清晰**：方法名明确表达判断意图
5. **易于扩展**：新增状态时只需修改枚举类

---

## 6. 锁的使用规范

### 5.1 标准分布式锁使用范式

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderLockService {
    
    private final RedissonClient redissonClient;
    
    public void processWithLock(String orderId, Runnable task) {
        String lockKey = String.format("order:lock:%s", orderId);
        RLock lock = redissonClient.getLock(lockKey);
        
        boolean locked = false;
        try {
            locked = lock.tryLock(3, 30, TimeUnit.SECONDS);
            
            if (!locked) {
                log.warn("获取锁失败, lockKey: {}", lockKey);
                throw new WarnException("系统繁忙，请稍后重试");
            }
            
            log.info("获取锁成功, lockKey: {}", lockKey);
            task.run();
            
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("获取锁被中断, lockKey: {}", lockKey, e);
            throw new ErrorException("系统异常，请稍后重试");
        } finally {
            if (locked && lock.isHeldByCurrentThread()) {
                lock.unlock();
                log.info("释放锁成功, lockKey: {}", lockKey);
            }
        }
    }
}
```

---

## 7. 代码抽象与封装规范

**识别多个方法的相同点，进行抽象和封装**。

```java
// ❌ 禁止：重复代码散落在多个方法中
public OrderVo getOrder(String orderId) {
    Order order = orderRepository.findByOrderId(orderId)
        .orElseThrow(() -> new WarnException("订单不存在"));
    OrderVo vo = new OrderVo();
    vo.setOrderId(order.getOrderId());
    vo.setStatus(order.getStatus());
    vo.setStatusDesc(OrderStatusEnum.fromCode(order.getStatus()).getDesc());
    vo.setAmount(order.getAmount());
    vo.setCreatedAt(order.getCreatedAt());
    return vo;
}

// ✅ 正确：抽象公共转换逻辑
public OrderVo getOrder(String orderId) {
    Order order = orderRepository.findByOrderId(orderId)
        .orElseThrow(() -> new WarnException("订单不存在"));
    return convertToVo(order);
}

public List<OrderVo> getOrders(List<String> orderIds) {
    List<Order> orders = orderRepository.findByOrderIdIn(orderIds);
    return orders.stream().map(this::convertToVo).collect(Collectors.toList());
}

private OrderVo convertToVo(Order order) {
    OrderVo vo = new OrderVo();
    vo.setOrderId(order.getOrderId());
    vo.setStatus(order.getStatus());
    vo.setStatusDesc(OrderStatusEnum.fromCode(order.getStatus()).getDesc());
    vo.setAmount(order.getAmount());
    vo.setCreatedAt(order.getCreatedAt());
    return vo;
}
```

---

## 8. JSON 解析规范

**禁止使用 JSONObject 解析 JSON 内容，必须使用 POJO**。

```java
// ❌ 禁止：使用 JSONObject
String jsonStr = "{\"orderId\":\"123\",\"status\":1}";
JSONObject json = JSON.parseObject(jsonStr);
String orderId = json.getString("orderId");  // 类型不安全

// ✅ 正确：使用 POJO
@Data
public class OrderInfo {
    private String orderId;
    private Integer status;
}

String jsonStr = "{\"orderId\":\"123\",\"status\":1}";
OrderInfo orderInfo = JSON.parseObject(jsonStr, OrderInfo.class);
String orderId = orderInfo.getOrderId();  // 类型安全
```

---

## 9. 函数式编程抽象规范

适当使用 `Consumer`/`Function`/`Supplier` 等函数式接口对代码进行抽象。

### 8.1 条件分支调用不同方法

```java
// ❌ 不推荐：相同的调用逻辑重复出现
public void processConfirmResult(CopyrightOrder order, ConfirmResponse res) {
    if (CodeEnum.SUCCESS.getCode().equals(res.getStatus())) {
        order.confirmSuccess(res.getMessage());
    } else {
        order.confirmNotSuccess(res.getMessage());
    }
}

// ✅ 推荐：使用 Consumer 抽象
public void processConfirmResult(CopyrightOrder order, ConfirmResponse res) {
    Consumer<String> handler = CodeEnum.SUCCESS.getCode().equals(res.getStatus())
        ? order::confirmSuccess
        : order::confirmNotSuccess;
    handler.accept(res.getMessage());
}
```

### 8.2 多分支复杂逻辑抽象

```java
// ✅ 多分支场景使用 Function 抽象
public OrderResult processOrder(Order order, ProcessType type) {
    Function<Order, OrderResult> processor = switch (type) {
        case CREATE -> this::handleCreate;
        case UPDATE -> this::handleUpdate;
        case CANCEL -> this::handleCancel;
        default -> throw new WarnException("不支持的处理类型");
    };
    
    log.info("开始处理订单, orderId: {}, type: {}", order.getOrderId(), type);
    validateOrder(order);
    OrderResult result = processor.apply(order);
    log.info("处理订单完成, orderId: {}, result: {}", order.getOrderId(), result);
    return result;
}
```
