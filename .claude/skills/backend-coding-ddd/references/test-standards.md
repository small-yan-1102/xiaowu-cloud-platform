# 单元测试规范

> 本文档为 Tool Wrapper 模式资源，在 Phase 4 生成每层代码时同步加载，确保每个主类对应一个测试类。

---

## 核心原则：主类与测试类同步生成

**每个主类生成时，必须同时生成其对应的测试类。禁止只生成主代码而不生成测试。**

---

## 测试类命名规范

| 主类类型 | 测试类命名 | 示例 |
|---------|---------|------|
| 聚合根 | `[聚合根名称]Test` | `CopyrightOrderTest` |
| Command Handler | `[Command名称]Test` | `CreateCopyrightOrderCmdTest` |
| Query | `[Query名称]Test` | `CopyrightOrderQueryTest` |
| Controller | `[Controller名称]Test` | `CopyrightOrderControllerTest` |
| Repository 实现 | `[Repository名称]Test` | `CopyrightOrderRepositoryTest` |
| Client 实现 | `[Client名称]Test` | `CopyrightOrderClientImplTest` |

---

## 测试方法命名格式

采用 `should_[期望结果]_when_[条件]` 格式：

```java
@Test
void should_create_order_successfully_when_valid_input() { ... }

@Test
void should_throw_exception_when_order_not_found() { ... }

@Test
void should_publish_event_when_confirm_success() { ... }
```

---

## 测试结构（AAA 模式）

```java
@Test
void should_change_status_when_confirm_success() {
    // Arrange — 准备测试数据和 Mock
    CopyrightOrder order = CopyrightOrder.create("unionId", "userId");

    // Act — 执行被测方法
    order.confirmSuccess("approveUserId");

    // Assert — 验证结果
    assertThat(order.getConfirmStatus()).isEqualTo(ConfirmStatusEnum.SUCCEED.getCode());
    assertThat(order.getEvents()).hasSize(1);
    assertThat(order.getEvents().get(0)).isInstanceOf(CopyrightOrderConfirmSuccessEvent.class);
}
```

---

## 各层测试注解

### 领域层（纯单元测试，无 Spring 上下文）

```java
@ExtendWith(MockitoExtension.class)
class CopyrightOrderTest {
    // 直接测试聚合根业务行为
}
```

### 应用层 Command/Query（Mock 依赖）

```java
@ExtendWith(MockitoExtension.class)
class CreateCopyrightOrderCmdTest {

    @Mock
    private CopyrightOrderRepository repository;

    @Mock
    private ExternalServiceClient externalClient;

    @InjectMocks
    private CreateCopyrightOrderCmd.Handler handler;

    @Test
    void should_save_order_when_create() {
        // Arrange
        CreateCopyrightOrderCmd cmd = new CreateCopyrightOrderCmd();
        cmd.setUnionOrderId("unionId");
        when(repository.save(any())).thenAnswer(inv -> inv.getArgument(0));

        // Act
        String result = handler.exec(cmd);

        // Assert
        verify(repository).save(any(CopyrightOrder.class));
        assertThat(result).isNotNull();
    }
}
```

### Repository 集成测试

```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE)
class CopyrightOrderRepositoryTest {
    @Autowired
    private CopyrightOrderRepositoryImpl repository;
    // ...
}
```

### Controller 接口测试

```java
@WebMvcTest(CopyrightOrderController.class)
class CopyrightOrderControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private CreateCopyrightOrderCmd.Handler createHandler;
    // ...
}
```

---

## 覆盖率要求

| 层级 | 最低行覆盖率 | 重点覆盖 |
|------|-----------|---------|
| 领域层 | 80% | 业务行为方法、领域事件发布 |
| Client 层 | 70% | 异常处理、边界条件 |
| 用例层 | 80% | 命令执行逻辑、查询逻辑 |
| 适配层 | 70% | API 接口、DTO/VO 转换 |

---

## 执行命令

```bash
# 执行指定测试类
mvn test -f [模块目录]/pom.xml -Dtest=[测试类名]

# 执行指定包下的所有测试
mvn test -f [模块目录]/pom.xml -Dtest="com.xw.[模块].[层级].**"

# 执行全部单元测试
mvn test -f [项目根目录]/pom.xml
```

---

## 测试结果处理

**通过**：

```
✅ 测试通过：[测试类名]
   - 测试用例数：X
   - 执行时间：Xms
```

**失败**：

```
❌ 测试失败：[测试类名]
   - 失败用例：[用例名称]
   - 失败原因：[错误信息]
   - 所在位置：[文件:行号]

修复流程：
1. 分析失败原因（代码问题 or 测试问题）
2. 制定修复方案并告知用户
3. 执行修复
4. 重新运行测试验证
```
