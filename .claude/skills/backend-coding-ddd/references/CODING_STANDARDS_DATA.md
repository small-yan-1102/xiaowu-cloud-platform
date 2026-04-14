# AI Coding 编码规范（数据层）

> 本文档在涉及数据库操作时加载，包含数据库规范、查询优化、缓存使用。

---

## 1. 数据库字段类型规范

### 1.1 JSON 内容字段

**如字段内容是 JSON 格式，数据库字段类型应为 `JSON`**。

```sql
-- ✅ 正确：使用 JSON 类型
CREATE TABLE `order` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `extra_info` JSON COMMENT '扩展信息（JSON格式）',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ❌ 错误：使用 VARCHAR 或 TEXT 存储 JSON
CREATE TABLE `order` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `extra_info` varchar(2000) COMMENT '扩展信息',
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 2. 索引命名规范

| 索引类型 | 命名前缀 | 示例 |
|---------|---------|-----|
| 主键索引 | `pk_` 或默认 | `PRIMARY KEY` |
| 唯一索引 | `uk_` | `uk_order_id` |
| 普通索引 | `idx_` | `idx_status` |
| 复合索引 | `idx_` | `idx_status_created_at` |
| 全文索引 | `ft_` | `ft_content` |

```sql
-- 索引命名示例
CREATE TABLE `order` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `order_id` varchar(64) NOT NULL COMMENT '订单ID',
    `user_id` varchar(64) NOT NULL COMMENT '用户ID',
    `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '状态',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_order_id` (`order_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_status` (`status`),
    KEY `idx_status_created_at` (`status`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 3. 查询优化规范

### 3.1 避免 SELECT *

```java
// ❌ 禁止：查询所有字段
@Query("SELECT o FROM Order o WHERE o.status = :status")
List<Order> findByStatus(@Param("status") Integer status);

// ✅ 正确：只查询需要的字段（使用投影）
@Query("SELECT new com.example.dto.OrderSimpleDto(o.orderId, o.status, o.createdAt) " +
       "FROM Order o WHERE o.status = :status")
List<OrderSimpleDto> findSimpleByStatus(@Param("status") Integer status);
```

### 3.2 合理使用分页

**分页查询必须使用数据库分页，禁止使用内存分页**。

```java
// ❌ 禁止：内存分页
public PageResult<OrderVo> listOrders(OrderQuery query) {
    List<Order> allOrders = orderRepository.findAll();  // 查询所有数据
    int start = (query.getPageNum() - 1) * query.getPageSize();
    List<Order> pageData = allOrders.subList(start, start + query.getPageSize());  // 内存分页
    // ...
}

// ✅ 正确：使用数据库分页
public PageResult<OrderVo> listOrders(OrderQuery query) {
    Pageable pageable = PageRequest.of(
        query.getPageNum() - 1, 
        query.getPageSize(),
        Sort.by(Sort.Direction.DESC, "createdAt")
    );
    
    Page<Order> page = orderRepository.findByCondition(query, pageable);
    
    List<OrderVo> voList = page.getContent().stream()
        .map(this::convertToVo)
        .collect(Collectors.toList());
    
    return PageResult.of(voList, page.getTotalElements(), query.getPageNum(), query.getPageSize());
}
```

### 3.3 避免深度分页

```java
// ❌ 不推荐：深度分页性能差
// SELECT * FROM order LIMIT 1000000, 10  -- 需要扫描100万行

// ✅ 推荐：使用游标分页（基于上一页最后一条记录的ID）
public List<Order> listOrdersByCursor(Long lastId, int pageSize) {
    if (lastId == null) {
        // 第一页
        return orderRepository.findTopNOrderByIdDesc(pageSize);
    }
    // 后续页，基于游标查询
    return orderRepository.findByIdLessThanOrderByIdDesc(lastId, PageRequest.of(0, pageSize));
}
```

### 3.4 查询阶段过滤数据

**严禁先查询全部数据，再在内存中过滤**。

```java
// ❌ 禁止：查询全部数据后再过滤
public List<OrderVo> getPendingOrders() {
    List<Order> allOrders = orderRepository.findAll();  // 查询所有订单
    List<Order> pendingOrders = allOrders.stream()  // 在内存中过滤
        .filter(order -> OrderStatusEnum.PENDING.getCode().equals(order.getStatus()))
        .collect(Collectors.toList());
    // ...
}

// ✅ 正确：在查询阶段过滤数据
public List<OrderVo> getPendingOrders() {
    List<Order> pendingOrders = orderRepository.findByStatus(
        OrderStatusEnum.PENDING.getCode()
    );
    // ...
}
```

---

## 4. 大批量数据分批处理

**处理大批量数据时必须分批处理**，避免内存溢出和长事务。

```java
// ✅ 分批处理大量数据
public void batchProcessOrders(List<String> orderIds) {
    log.info("开始批量处理订单, 总数: {}", orderIds.size());
    
    int batchSize = 100;
    List<List<String>> batches = CollUtil.split(orderIds, batchSize);
    
    int processedCount = 0;
    for (List<String> batch : batches) {
        List<Order> orders = orderRepository.findByOrderIdIn(batch);
        for (Order order : orders) {
            processOrder(order);
        }
        processedCount += batch.size();
        log.info("批量处理进度: {}/{}", processedCount, orderIds.size());
    }
    
    log.info("批量处理订单完成, 总数: {}", orderIds.size());
}
```

---

## 5. 缓存使用规范

### 5.1 缓存基本使用

**对于频繁访问且不经常变化的数据，应使用缓存**。

```java
@Service
@RequiredArgsConstructor
public class ConfigService {
    
    private final ConfigRepository configRepository;
    private final ConfigCacheClient configCacheClient;
    
    /**
     * 获取配置（优先从缓存获取）
     */
    public Config getConfig(String configKey) {
        // 1. 先从缓存获取
        Config config = configCacheClient.get(configKey);
        if (config != null) {
            return config;
        }
        
        // 2. 缓存未命中，查询数据库
        config = configRepository.findByConfigKey(configKey)
            .orElseThrow(() -> new WarnException("配置不存在"));
        
        // 3. 写入缓存
        configCacheClient.set(configKey, config);
        
        return config;
    }
}
```

### 5.2 缓存更新策略

```java
// 更新数据时同步更新缓存
@Transactional
public void updateConfig(String configKey, String configValue) {
    // 1. 更新数据库
    Config config = configRepository.findByConfigKey(configKey)
        .orElseThrow(() -> new WarnException("配置不存在"));
    config.setConfigValue(configValue);
    configRepository.save(config);
    
    // 2. 更新缓存（或删除缓存）
    configCacheClient.set(configKey, config);
    // 或 configCacheClient.delete(configKey);
}
```

---

## 6. 远程调用规范

### 6.1 禁止循环内远程调用

**严禁在循环内进行远程服务调用**（HTTP、RPC等），应批量调用或提供批量接口。

```java
// ❌ 禁止：在循环内调用远程服务
public List<OrderVo> getOrdersWithPayment(List<Order> orders) {
    List<OrderVo> result = new ArrayList<>();
    for (Order order : orders) {
        OrderVo vo = convertToVo(order);
        PaymentInfo payment = paymentClient.getPaymentInfo(order.getPaymentId());  // N次调用！
        vo.setPaymentStatus(payment.getStatus());
        result.add(vo);
    }
    return result;
}

// ✅ 正确：批量调用远程服务
public List<OrderVo> getOrdersWithPayment(List<Order> orders) {
    if (CollectionUtils.isEmpty(orders)) {
        return Collections.emptyList();
    }
    
    // 批量获取支付信息
    List<String> paymentIds = orders.stream()
        .map(Order::getPaymentId)
        .filter(StrUtil::isNotBlank)
        .distinct()
        .collect(Collectors.toList());
    
    // 一次性批量调用
    Map<String, PaymentInfo> paymentMap = paymentClient.batchGetPaymentInfo(paymentIds)
        .stream()
        .collect(Collectors.toMap(PaymentInfo::getPaymentId, Function.identity()));
    
    // 组装结果
    return orders.stream()
        .map(order -> {
            OrderVo vo = convertToVo(order);
            PaymentInfo payment = paymentMap.get(order.getPaymentId());
            if (payment != null) {
                vo.setPaymentStatus(payment.getStatus());
            }
            return vo;
        })
        .collect(Collectors.toList());
}
```

---

## 7. 性能优化速查表

| 问题 | 解决方案 | 关键代码 |
|-----|---------|---------|
| N+1 查询 | 批量查询 + Map 组装 | `findByIdIn()` + `Collectors.toMap()` |
| 内存分页 | 数据库分页 | `PageRequest.of()` + `Pageable` |
| 深度分页 | 游标分页 | `findByIdLessThanOrderByIdDesc()` |
| 循环远程调用 | 批量接口 | `batchGetXXX()` |
| 全表查询 | 索引过滤 | `findByStatus()` |
| 频繁查库 | 缓存 | `CacheClient.get/set()` |
| 大数据量 | 分批处理 | `CollUtil.split(list, batchSize)` |
