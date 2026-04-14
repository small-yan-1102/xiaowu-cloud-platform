# 版权服务器架构设计文档

## 1. 整体架构概述

### 1.1 架构模式
本项目采用**六边形架构**（Hexagonal Architecture）也称为端口适配器架构，结合**领域驱动设计**（DDD）理念构建。

### 1.2 核心设计原则
- **关注点分离**：各层职责明确，低耦合高内聚
- **领域驱动**：以业务领域为核心，技术为业务服务
- **事件驱动**：通过领域事件实现松耦合通信
- **最终一致性**：接受短暂的数据不一致，通过补偿机制保证最终一致

### 1.3 模块划分

```
copyright-server/
├── copyright-server-start/          # 启动模块（入口层）
├── copyright-server-domain/         # 领域层（核心业务逻辑）
├── copyright-server-application/    # 应用层（业务编排）
├── copyright-server-adapter/        # 适配器层（外部集成）
└── copyright-server-share/          # 共享层（公共组件）
```

## 2. 领域层设计 (Domain Layer)

### 2.1 核心概念实现

#### 聚合根 (Aggregate Root)
```java
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
    // 聚合根标识
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    // 业务字段...
    
    // 领域行为
    public void start() {
        publisher().attachEvent(CopyrightOrderStartEvent.builder().copyrightOrder(this).build());
    }
    
    public void uploadSuccess(String submitResult) {
        // 业务逻辑处理
        this.submitStatus = CopyrightOrderSubmitStatusEnum.SUCCEED.getCode();
        // 发布领域事件
        publisher().attachEvent(CopyrightOrderUploadSuccessEvent.builder().copyrightOrder(this).build());
    }
}
```

#### 实体基类
```java
public abstract class BaseEntity {
    private DomainEventPublisher domainEventPublisher;
    
    public DomainEventPublisher publisher() {
        if (domainEventPublisher == null) {
            domainEventPublisher = DomainEventPublisher.Factory.create(this);
        }
        return domainEventPublisher;
    }
}
```

#### 值对象
通过普通Java类实现，强调不可变性和值相等性。

### 2.2 领域事件机制

#### 事件定义
```java
@DomainEvent  // 内部事件
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CopyrightOrderConfirmSuccessEvent {
    private CopyrightOrder copyrightOrder;
}

@DomainEvent("copyright.order.confirm.success")  // 集成事件（带topic）
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CopyrightOrderConfirmSuccessIntegrationEvent {
    private CopyrightOrder copyrightOrder;
}
```

#### 事件发布器
```java
public interface DomainEventPublisher {
    void attachEvent(Object event);    // 添加事件
    void detachEvent(Object event);    // 移除事件
    void reset();                      // 重置事件列表
    
    static boolean isIntergrationEvent(Object event) {
        DomainEvent domainEvent = event.getClass().getAnnotation(DomainEvent.class);
        return StringUtils.isNotBlank(domainEvent.value());
    }
}
```

### 2.3 规范验证 (Specification)

```java
@Service
@Slf4j
public class AccountSpec implements Specification<Account> {
    @Override
    public Class<Account> entityClass() {
        return Account.class;
    }
    
    @Override
    public boolean inTransaction() {
        return false;  // 是否在事务中验证
    }
    
    @Override
    public Result valid(Object entity) {
        Account account = (Account) entity;
        if (account.getBalance() < 0) {
            return Result.failed("账户余额不能为负数");
        }
        return Result.passed();
    }
}
```

## 3. 应用层设计 (Application Layer)

### 3.1 命令模式

#### 基础命令接口
```java
public interface Command<PARAM, RESULT> {
    RESULT exec(PARAM param) throws Exception;
}

// 无参数命令
public interface CommandNoneParam<RESULT> extends Command<Void, RESULT> {
    default RESULT exec(Void param) throws Exception {
        return exec();
    }
    RESULT exec() throws Exception;
}

// 无参数无返回值命令
public interface CommandNoneParamAndResult extends Command<Void, Void> {
    default Void exec(Void param) throws Exception {
        exec();
        return null;
    }
    void exec() throws Exception;
}
```

#### 命令实现示例
```java
@Component
public class CreateCopyrightOrderCmd {
    @Service
    @RequiredArgsConstructor
    public static class Handler implements Command<CreateCopyrightOrderCmd, String> {
        private final CopyrightOrderRepository copyrightOrderRepository;
        private final CopyrightInfoRepository copyrightInfoRepository;
        
        @Override
        @Transactional(rollbackFor = Exception.class)
        public String exec(CreateCopyrightOrderCmd cmd) throws Exception {
            // 1. 查询版权信息
            CopyrightInfo copyrightInfo = copyrightInfoRepository.findById(cmd.getCopyrightId())
                .orElseThrow(() -> new KnownException("版权信息不存在"));
            
            // 2. 创建版权订单
            CopyrightOrder copyrightOrder = CopyrightOrder.create(
                cmd.getUnionOrderId(), 
                cmd.getCopyrightOrderId(), 
                copyrightInfo
            );
            
            // 3. 保存并触发领域事件
            copyrightOrderRepository.save(copyrightOrder);
            
            return copyrightOrder.getId().toString();
        }
    }
}
```

### 3.2 查询模式

```java
public interface Query<PARAM, RESULT> {
    RESULT query(PARAM param);
}

public interface PageQuery<PARAM, RESULT> {
    PageData<RESULT> queryPage(PARAM param);
}
```

### 3.3 Saga分布式事务

#### Saga状态机定义
```java
@Service
@Slf4j
public static class Handler extends SagaStateMachine<DemoAnnotationSaga> {
    @Override
    protected String getBizType() {
        return "demo_saga";
    }
    
    @Override
    protected Class<DemoAnnotationSaga> getContextClass() {
        return DemoAnnotationSaga.class;
    }
    
    @SagaProcess(code = 10)
    public void step1(DemoAnnotationSaga context) {
        context.output += "step1 finished!";
    }
    
    @SagaProcess(parent = "step1", code = 20)
    public void step1_1(DemoAnnotationSaga context) {
        context.output += "step1_1 finished!";
    }
    
    @SagaProcess(preview = "step1", code = 30)
    public void step2(DemoAnnotationSaga context) {
        context.output += "step2 finished!";
    }
}
```

#### Saga状态定义
```java
@AllArgsConstructor
public enum SagaState {
    INIT(0, "init"),              // 初始状态
    RUNNING(-1, "running"),       // 执行中
    CANCEL(-2, "cancel"),         // 业务主动取消
    EXPIRED(-3, "expired"),       // 过期
    FAILED(-4, "failed"),         // 失败
    ROLLBACKING(-5, "rollbacking"), // 回滚中
    ROLLBACKED(-6, "rollbacked"),   // 已回滚
    DONE(1, "done");              // 已完成
}
```

#### Saga调度服务
```java
@Service
@RequiredArgsConstructor
@Slf4j
public class SagaScheduleService {
    @Scheduled(cron = "*/10 * * * * ?")
    public void compensation() {
        // 补偿未完成的Saga事务
        Page<Saga> sagas = sagaRepository.findAll((root, cq, cb) -> {
            cq.where(cb.or(
                cb.and(
                    cb.equal(root.get("sagaState"), Saga.SagaState.INIT),
                    cb.lessThan(root.get("nextTryTime"), now),
                    root.get("bizType").in(sagaSupervisor.getSupportedBizTypes())
                )
            ));
            return null;
        }, PageRequest.of(0, 10, Sort.by(Sort.Direction.ASC, "createAt")));
        
        for (Saga saga : sagas.toList()) {
            sagaSupervisor.resume(saga);
        }
    }
    
    @Scheduled(cron = "0 0 2 * * ?")
    public void archiving() {
        // 归档已完成的Saga事务
        List<ArchivedSaga> archivedSagas = sagas.stream()
            .map(s -> ArchivedSaga.builder()/* 映射逻辑 */.build())
            .collect(Collectors.toList());
        UnitOfWork.saveEntities(archivedSagas, sagas.toList());
    }
}
```

### 3.4 工作单元模式 (Unit of Work)

```java
@Service
@RequiredArgsConstructor
@Slf4j
public class UnitOfWork {
    @PersistenceContext
    private EntityManager entityManager;
    
    // 保存实体并发布领域事件
    public void save(Collection<?> saveEntities, Collection<?> deleteEntities) {
        // 合并上下文中的实体
        Set<Object> saveEntityList = mergeSaveEntities(saveEntities);
        Set<Object> deleteEntityList = mergeDeleteEntities(deleteEntities);
        
        // 执行持久化操作
        save(() -> {
            persistEntities(saveEntityList);
            removeEntities(deleteEntityList);
            entityManager.flush();  // 刷新到数据库
        });
    }
    
    // 事务执行
    public <T> T save(TransactionHandlerWithOutput<T> transactionHandler) {
        preTransactionSpecifications();  // 事务前规范验证
        T result = transactionHandler.exec();
        inTransactionSpecifications();   // 事务中规范验证
        applicationEventPublisher.publishEvent(new DomainEventFireEvent(this));
        return result;
    }
    
    // 静态方法便捷调用
    public static void saveEntities(Object... entities) {
        instance.save(entities);
    }
    
    public static <T> T saveTransactional(TransactionHandlerWithOutput<T> handler) {
        return instance.save(handler);
    }
}
```

## 4. 适配器层设计 (Adapter Layer)

### 4.1 外部客户端集成

#### REST客户端
```java
@Component
public class CopyrightOrderClientImpl implements CopyrightOrderClient {
    @Resource
    private CopyrightOrderRest copyrightOrderRest;
    
    @Override
    public String createCopyrightOrder(CreateCopyrightOrderDto dto) {
        ApiResponse<String> response = null;
        try {
            response = copyrightOrderRest.createCopyrightOrder(dto);
        } catch (Exception e) {
            log.error("rest createCopyrightOrder fail, message: {}", e.getMessage(), e);
            throw new KnownException("系统异常");
        }
        
        if (response.isSuccess()) {
            return response.getData();
        } else {
            log.error("rest createCopyrightOrder fail, status: {}, message: {}", 
                     response.getStatus(), response.getMessage());
            throw new KnownException("系统异常");
        }
    }
}
```

#### 消息队列消费者
```java
@XwMessageListener(topic = "COPYRIGHT_ORDER_PROCESS", tag = "*", groupId = "copyright_order_group")
@Component
@Slf4j
public class CopyrightOrderProcessConsumer implements MessageConsumer {
    @Override
    public void consume(MessageExt message) {
        try {
            String body = new String(message.getBody(), StandardCharsets.UTF_8);
            CopyrightOrderProcessDto dto = JSON.parseObject(body, CopyrightOrderProcessDto.class);
            
            // 处理业务逻辑
            copyrightOrderProcessCmd.exec(dto);
            
        } catch (Exception e) {
            log.error("处理版权订单消息失败: {}", message.getMsgId(), e);
            throw new RuntimeException("消息处理失败", e);
        }
    }
}
```

### 4.2 数据访问配置

#### 统一事务管理
```java
@Configuration
@EnableTransactionManagement
@EnableJpaRepositories(
    basePackages = {"com.xw"},
    entityManagerFactoryRef = "entityManagerFactory",
    transactionManagerRef = "transactionManager"
)
@MapperScan(basePackages = "com.xw.adapter.domain.mapper", sqlSessionTemplateRef = "sqlSessionTemplate")
public class MainTransactionConfig {
    @Bean
    @Primary
    public LocalContainerEntityManagerFactoryBean entityManagerFactory(
            EntityManagerFactoryBuilder builder, DataSource dataSource) {
        return builder
                .dataSource(dataSource)
                .packages("com.xw")
                .persistenceUnit("primary")
                .properties(jpaProperties())
                .build();
    }
    
    @Bean
    @Primary
    public PlatformTransactionManager transactionManager(
            @Qualifier("entityManagerFactory") EntityManagerFactory entityManagerFactory,
            @Qualifier("dataSource") DataSource dataSource) {
        JpaTransactionManager transactionManager = new JpaTransactionManager();
        transactionManager.setEntityManagerFactory(entityManagerFactory);
        transactionManager.setDataSource(dataSource);
        transactionManager.setDefaultTimeout(300);
        transactionManager.setRollbackOnCommitFailure(true);
        return transactionManager;
    }
}
```

### 4.3 定时任务

#### XXL-JOB任务处理器
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

#### Spring Scheduled任务
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

## 5. 技术栈规范

### 5.1 核心框架版本
- **Java**: 21
- **Spring Boot**: 3.1.6
- **Spring Cloud**: 2022.0.4
- **Spring Cloud Alibaba**: 2022.0.0.0-RC2

### 5.2 数据库技术
- **MySQL**: 8.0+
- **MyBatis Plus**: 3.5.8
- **Hibernate ORM**: 6.2.1
- **Druid**: 1.2.12
- **PageHelper**: 1.4.3

### 5.3 中间件集成
- **RocketMQ**: 2.2.1 (消息队列)
- **Redisson**: 3.21.1 (分布式锁)
- **Nacos**: 2022.0.0.0-RC2 (配置中心/服务发现)
- **Seata**: 1.7.0 (分布式事务)
- **Xxl-Job**: 2.3.1 (分布式任务调度)

### 5.4 开发工具
- **Lombok**: 1.18.30
- **Orika**: 1.4.6 (对象映射)
- **FastJSON**: 1.2.58 (JSON处理)
- **Hutool**: 5.8.35 (工具库)
- **Guava**: 32.1.2-jre

## 6. 数据库设计规范

### 6.1 表命名规范
- 聚合根表：使用业务名称，如 `copyright_order`
- 关联表：使用 `_rel` 后缀，如 `m2m_student_course_rel`
- 系统表：使用双下划线前缀，如 `__saga`, `__event`

### 6.2 字段设计规范
```java
@Entity
@Table(name = "`copyright_order`")
@DynamicInsert
@DynamicUpdate
@Where(clause = "deleted = 0")
public class CopyrightOrder {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "`id`")
    private Long id;
    
    @Column(name = "`copyright_order_id`", nullable = false, length = 64)
    private String copyrightOrderId;
    
    @Column(name = "`deleted`", nullable = false, columnDefinition = "TINYINT DEFAULT 0")
    private Boolean deleted;
    
    @CreationTimestamp
    @Column(name = "`created_at`", updatable = false)
    private LocalDateTime createdAt;
    
    @UpdateTimestamp
    @Column(name = "`updated_at`")
    private LocalDateTime updatedAt;
}
```

### 6.3 分区策略
```java
// Saga表按月分区
private void addPartition(String table, Date date) {
    String sql = "alter table `" + table + "` add partition " +
                "(partition p" + DateFormatUtils.format(date, "yyyyMM") + 
                " values less than (to_days('" + 
                DateFormatUtils.format(DateUtils.addMonths(date, 1), "yyyy-MM") + 
                "-01')) ENGINE=InnoDB)";
    jdbcTemplate.execute(sql);
}
```

## 7. 消息队列和异步处理机制

### 7.1 RocketMQ集成
项目采用RocketMQ作为主要的消息中间件，实现了：
- 异步事件处理
- 服务间解耦通信
- 最终一致性保障
- 消息可靠性投递

### 7.2 事件驱动架构
通过领域事件实现服务间的松耦合通信：
- 内部事件：同一进程内同步处理
- 集成事件：跨服务异步处理，通过消息队列传递

## 8. 事务管理策略

### 8.1 分布式事务
采用Saga模式处理跨服务的分布式事务：
- 通过状态机管理事务流程
- 支持事务补偿和回滚
- 实现最终一致性

### 8.2 本地事务
使用Spring事务管理器配合JPA/Hibernate：
- 声明式事务管理
- 工作单元模式统一事务边界
- 规范验证机制确保数据一致性

## 9. 部署和运维相关配置

### 9.1 环境配置

#### 多环境配置
```
application.yml          # 主配置文件
application-dev.yml      # 开发环境
application-test.yml     # 测试环境
application-prod.yml     # 生产环境
application-sandbox.yml  # 沙箱环境
```

#### 配置文件示例
```yaml
# application.yml
app:
  id: copyright-server
spring:
  application:
    name: ${app.id}
  profiles:
    active: dev

# application-prod.yml
spring:
  config:
    import: optional:nacos:${app.id}.yaml?group=DEFAULT_GROUP&namespace=fcc92a19-72b2-4b67-9396-2b7222ff54aa
  cloud:
    nacos:
      config:
        server-addr: mse-d492bab0-nacos-ans.mse.aliyuncs.com:8848
        group: DEFAULT_GROUP
        file-extension: yaml
```

---
*文档版本：1.0*
*最后更新：2024年12月*
*适用项目：copyright-server*