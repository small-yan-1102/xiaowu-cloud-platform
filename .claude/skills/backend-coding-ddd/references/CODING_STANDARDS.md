# AI Coding 编码规范（核心层）

> **必读规范**：本文档包含强制遵守的核心规范，Skill 默认加载。
> 详细规范请查阅 CODING_STANDARDS_FULL.md

---

## 1. 强制红线规范

以下规范**必须严格遵守**，违反会导致 Bug 或严重性能问题。

### 1.1 控制流语句必须使用大括号

| 规范 | 正确写法 | 错误写法 |
|-----|---------|---------|
| if 语句 | `if (a) { return b; }` | `if (a) return b;` |
| for 循环 | `for (x : list) { process(x); }` | `for (x : list) process(x);` |
| while 循环 | `while (condition) { doSomething(); }` | `while (condition) doSomething();` |

### 1.2 字符串判空规范

**必须使用 `StrUtil.isBlank()` / `StrUtil.isNotBlank()`**

```java
// ✅ 正确
if (StrUtil.isBlank(str)) {
    throw new WarnException("参数不能为空");
}

// ❌ 禁止：只判断 null
if (str == null) { ... }
```

### 1.3 对象判等规范

**必须使用 `Objects.equals()`**

```java
// ✅ 正确
if (Objects.equals(order.getStatus(), OrderStatusEnum.PENDING.getCode())) {
    // ...
}

// ❌ 禁止：直接使用 == 或 .equals()
if (order.getStatus() == 1) { ... }
if (order.getStatus().equals(expected)) { ... }  // 可能NPE
```

### 1.4 集合非空判断规范

**List 必须使用 `CollectionUtils.isEmpty()`**

```java
import org.springframework.util.CollectionUtils;

// ✅ 正确
if (CollectionUtils.isEmpty(list)) {
    return Collections.emptyList();
}

if (CollectionUtils.isNotEmpty(list)) {
    String first = list.get(0);
}
```

### 1.5 禁止循环内数据库查询（N+1问题）

```java
// ❌ 禁止：循环内查询
for (Order order : orders) {
    User user = userRepository.findById(order.getUserId());  // N次查询！
}

// ✅ 正确：批量查询 + Map组装
Set<String> userIds = orders.stream().map(Order::getUserId).collect(Collectors.toSet());
Map<String, User> userMap = userRepository.findByUserIdIn(userIds)
    .stream().collect(Collectors.toMap(User::getUserId, Function.identity()));
```

### 1.6 禁止直接使用魔法值

```java
// ❌ 禁止
if (order.getStatus() == 1) { ... }
if ("PENDING".equals(status)) { ... }

// ✅ 正确：使用枚举或常量
if (OrderStatusEnum.PENDING.getCode().equals(order.getStatus())) { ... }
```

### 1.7 禁止吞掉异常

```java
// ❌ 禁止：只打日志不处理
try {
    doSomething();
} catch (Exception e) {
    log.error(e);  // 异常被吞掉！
}

// ✅ 正确：必须有处理逻辑
try {
    doSomething();
} catch (Exception e) {
    log.error("操作失败", e);
    throw new ErrorException("操作失败: " + e.getMessage());
}
```

### 1.8 禁止直接使用 JdbcTemplate

**统一使用 Spring Data JPA 或 MyBatis**

```java
// ❌ 禁止
@Autowired
private JdbcTemplate jdbcTemplate;

// ✅ 正确
@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {
    List<Order> findByStatus(Integer status);
}
```

### 1.9 禁止方法返回值使用 Map

**方法返回值必须使用具体的 POJO 类，禁止使用 Map 传递数据**。

```java
// ❌ 禁止：返回 Map，类型不安全，可读性差
public Map<String, Object> getOrderInfo(String orderId) {
    Map<String, Object> result = new HashMap<>();
    result.put("orderId", orderId);
    result.put("status", 1);
    result.put("amount", new BigDecimal("100.00"));
    return result;
}

// ✅ 正确：返回具体的 POJO
@Data
public class OrderInfo {
    private String orderId;
    private Integer status;
    private BigDecimal amount;
}

public OrderInfo getOrderInfo(String orderId) {
    OrderInfo info = new OrderInfo();
    info.setOrderId(orderId);
    info.setStatus(1);
    info.setAmount(new BigDecimal("100.00"));
    return info;
}
```

---

## 2. 高频错误防范

### 2.1 集合操作安全

```java
// ❌ 禁止：直接获取首元素
String first = list.get(0);  // 可能 IndexOutOfBoundsException

// ✅ 正确：先校验
if (CollectionUtils.isNotEmpty(list)) {
    String first = list.get(0);
}
```

### 2.2 字符串拼接规范

```java
// ❌ 禁止：使用 + 号拼接
String msg = "用户" + userId + "的订单" + orderId + "创建成功";

// ✅ 正确：使用 String.format()
String msg = String.format("用户%s的订单%s创建成功", userId, orderId);
```

### 2.3 日志输出规范

```java
@Slf4j
@Service
public class OrderService {
    
    public void createOrder(CreateOrderDto dto) {
        log.info("开始创建订单, dto: {}", dto);  // 方法开始日志
        
        try {
            // 业务逻辑...
            log.info("创建订单成功, orderId: {}", orderId);  // 成功日志
        } catch (Exception e) {
            log.error("创建订单异常, dto: {}", dto, e);  // 异常日志
            throw new ErrorException("创建订单失败");
        }
    }
}
```

---

## 3. 快速参考表

| 场景 | 推荐用法 | 禁止用法 |
|-----|---------|---------|
| 字符串判空 | `StrUtil.isBlank(str)` | `str == null` |
| 对象判等 | `Objects.equals(a, b)` | `a == b`, `a.equals(b)` |
| List判空 | `CollectionUtils.isEmpty(list)` | `list == \|\| list.isEmpty()` |
| 字符串拼接 | `String.format()` | `+` 号拼接 |
| 数据库访问 | JPA / MyBatis | JdbcTemplate |
| JSON解析 | POJO | JSONObject |
| 方法返回值 | POJO | Map<String, Object> |
| 工具库 | Hutool | Apache Commons, Guava |

---

## 4. 分层加载说明

根据任务类型，Skill 会自动加载对应层级的规范：

| 层级 | 文件 | 触发场景 |
|-----|------|---------|
| L1 核心 | CODING_STANDARDS.md | **必载** |
| L2 代码 | CODING_STANDARDS_CODE.md | 编写业务代码 |
| L3 数据 | CODING_STANDARDS_DATA.md | 涉及数据库操作 |
| L4 架构 | CODING_STANDARDS_ARCH.md | 领域建模/架构设计 |

> 完整规范请查阅：[CODING_STANDARDS_FULL.md](./CODING_STANDARDS_FULL.md)
