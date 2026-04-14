# AI Coding 编码规范（架构层）

> 本文档在领域建模、架构设计时加载，包含 DDD 规范、API 设计、安全规范。

---

## 1. API 路径规范

| 接口类型 | 类命名后缀 | 路径前缀 | 调用方 | 登录要求 |
|---------|-----------|---------|-------|---------|
| 面向前端 | `Controller` | `/appApi/` | 前端应用（Web、App等） | **必须添加 `@NeedLogin` 注解** |
| 面向服务 | `CloudController` | `/cloudApi/` | 其他微服务内部调用 | 视场景而定 |

### 1.1 登录注解规范

**路径前缀为 `/appApi/` 的 Controller，每个方法都必须添加 `@NeedLogin` 注解**。

```java
// ✅ 正确：面向前端接口，所有方法都添加 @NeedLogin
@RestController
@RequestMapping("/appApi/order")
public class OrderController {
    
    @NeedLogin
    @GetMapping("/list")
    public ApiResponse<PageResult<OrderVo>> list(OrderQuery query) {
        // 需要登录才能访问
    }
    
    @NeedLogin
    @GetMapping("/detail/{id}")
    public ApiResponse<OrderVo> detail(@PathVariable String id) {
        // 需要登录才能访问
    }
    
    @NeedLogin(required = false)  // 公开接口
    @GetMapping("/public/info")
    public ApiResponse<PublicInfoVo> getPublicInfo() {
        // 无需登录即可访问
    }
}
```

### 1.2 自定义注解

#### @NeedLogin 注解

```java
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface NeedLogin {
    /**
     * 是否需要登录，默认 true
     */
    boolean required() default true;
}
```

#### @OperateLog 注解

```java
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface OperateLog {
    /**
     * 操作描述
     */
    String value() default "";
    
    /**
     * 操作类型
     */
    OperateType type() default OperateType.OTHER;
}

// 使用示例
@OperateLog(value = "创建订单", type = OperateType.CREATE)
@PostMapping("/create")
public ApiResponse<String> create(@RequestBody CreateOrderDto dto) {
    // 会自动记录操作日志
}
```

---

## 2. 安全规范

### 2.1 越权问题防范

**查询类接口必须考虑越权问题**。

```java
// ❌ 禁止：未校验数据归属
@GetMapping("/order/{orderId}")
public ApiResponse<OrderVo> getOrder(@PathVariable String orderId) {
    Order order = orderRepository.findByOrderId(orderId)
        .orElseThrow(() -> new WarnException("订单不存在"));
    return ApiResponse.success(convertToVo(order));  // 任何用户都能查看任何订单
}

// ✅ 正确：校验数据归属
@NeedLogin
@GetMapping("/order/{orderId}")
public ApiResponse<OrderVo> getOrder(@PathVariable String orderId) {
    String currentUserId = SecurityContextHolder.getCurrentUserId();
    
    Order order = orderRepository.findByOrderId(orderId)
        .orElseThrow(() -> new WarnException("订单不存在"));
    
    if (!order.getUserId().equals(currentUserId)) {
        throw new WarnException("无权查看该订单");
    }
    
    return ApiResponse.success(convertToVo(order));
}

// ✅ 更推荐：在 Repository 层直接限制
@NeedLogin
@GetMapping("/order/{orderId}")
public ApiResponse<OrderVo> getOrder(@PathVariable String orderId) {
    String currentUserId = SecurityContextHolder.getCurrentUserId();
    
    // Repository 层查询时直接带上用户ID条件
    Order order = orderRepository.findByOrderIdAndUserId(orderId, currentUserId)
        .orElseThrow(() -> new WarnException("订单不存在或无权查看"));
    
    return ApiResponse.success(convertToVo(order));
}
```

---

## 3. 公共组件优先使用规范

**涉及以下场景时，必须优先使用团队公共组件**。

### 3.1 场景速查表

| 场景分类 | 推荐组件 | 说明 |
|---------|---------|-----|
| **DDD架构支撑** | `@AggregateRoot` `@DomainEvent` `@SagaProcess` | 实现领域驱动设计的基础设施 |
| **用户认证鉴权** | `@NeedLogin` `JwtUtils` `RequestUtils` | 统一的登录校验和Token管理 |
| **数据转换** | `MapperUtil` | 各层之间的对象转换（DTO/VO/Entity） |
| **缓存操作** | `RedisUtils` | 缓存读写、分布式锁、计数器等 |
| **文件存储** | `StorageUtils` | 多云存储统一接口（MinIO/阿里OSS/联通云OSS） |
| **任务重试** | `RetryUtil` `RetryTimeCalculator` | 失败任务的重试调度 |
| **API安全** | `SignUtil` | 接口签名认证 |
| **分布式协调** | `LockerService` | 定时任务防重、资源互斥 |
| **接口限流** | `@RateLimit` | 基于Redis的接口限流保护 |
| **操作日志** | `@OperateLog` | 记录用户操作日志 |
| **埋点统计** | `@NeedUserOperationBuriedPoint` | 用户行为埋点采集 |

### 3.2 常用公共组件示例

#### 对象转换使用 MapperUtil

```java
// ❌ 禁止：手动逐字段赋值
UserVO vo = new UserVO();
vo.setId(user.getId());
vo.setName(user.getName());
vo.setPhone(user.getPhone());

// ✅ 正确：使用 MapperUtil
UserVO vo = MapperUtil.map(user, UserVO.class);
List<UserVO> voList = MapperUtil.mapAsList(users, UserVO.class);
```

#### 登录校验使用 @NeedLogin

```java
// ❌ 禁止：手动校验登录状态
@GetMapping("/user/info")
public Result<UserInfo> getUserInfo(HttpServletRequest request) {
    String token = request.getHeader("Authorization");
    if (token == null) {
        throw new WarnException("未登录");
    }
    // ...
}

// ✅ 正确：使用 @NeedLogin 注解
@NeedLogin
@GetMapping("/user/info")
public Result<UserInfo> getUserInfo() {
    // 自动校验登录状态
}
```

#### 分布式锁使用 LockerService

```java
// ✅ 定时任务防重
@Autowired
private LockerService lockerService;

public void scheduledTask() {
    String lockName = "task_sync_data";
    String pwd = RandomStringUtils.random(8, true, true);
    Duration duration = Duration.ofMinutes(5);
    
    if (lockerService.acquire(lockName, pwd, duration)) {
        try {
            // 执行需要互斥的业务逻辑
        } finally {
            lockerService.release(lockName, pwd);
        }
    }
}
```

#### 重试机制使用 RetryUtil

```java
// ✅ 外部服务调用重试
RetryTemplate template = RetryUtil.createExponentialRetryTemplate(
    3,           // 最大重试3次
    1000,        // 初始间隔1秒
    2.0,         // 乘数
    30000,       // 最大间隔30秒
    IOException.class, ResourceAccessException.class
);

String result = RetryUtil.execute(template, () -> {
    return httpClient.call(url);
});
```

---

## 4. Maven 依赖管理规范

### 4.1 版本号统一管理

**所有依赖的版本号必须在根 pom（parent pom）中统一定义**。

```xml
<!-- ✅ 正确：在根 pom 中定义版本号 -->
<properties>
    <hutool.version>5.8.22</hutool.version>
    <guava.version>32.1.2-jre</guava.version>
    <commons-lang3.version>3.12.0</commons-lang3.version>
</properties>

<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>cn.hutool</groupId>
            <artifactId>hutool-all</artifactId>
            <version>${hutool.version}</version>
        </dependency>
    </dependencies>
</dependencyManagement>
```

```xml
<!-- ✅ 正确：子模块只声明依赖，不指定版本号 -->
<dependencies>
    <dependency>
        <groupId>cn.hutool</groupId>
        <artifactId>hutool-all</artifactId>
        <!-- 版本号从 parent 继承 -->
    </dependency>
</dependencies>
```

---

## 5. 编码方式规范

### 5.1 渐进式编码

**采用渐进式编码方式**：开发一个功能，用户确认一次。

#### 流程规范
1. **功能拆分**：将大功能拆分为独立的小功能点
2. **单点开发**：每次只开发一个功能点
3. **及时确认**：每完成一个功能点，提交给用户确认
4. **迭代推进**：确认通过后再开发下一个功能点

#### 优势
- 降低返工风险
- 快速发现问题
- 便于追踪进度
- 提高代码质量

---

## 6. 架构规范速查表

| 场景 | 规范 | 组件/注解 |
|-----|------|----------|
| 前端接口 | 路径 `/appApi/`，类名 `Controller` | `@NeedLogin` |
| 服务接口 | 路径 `/cloudApi/`，类名 `CloudController` | 视场景 |
| 对象转换 | 禁止手动赋值 | `MapperUtil.map()` |
| 登录校验 | 禁止手动校验 | `@NeedLogin` |
| 分布式锁 | 定时任务防重 | `LockerService` |
| 重试机制 | 外部服务调用 | `RetryUtil` |
| 越权防范 | Repository层带用户ID查询 | `findByXxxAndUserId()` |
| 依赖版本 | 根pom统一管理 | `<dependencyManagement>` |
