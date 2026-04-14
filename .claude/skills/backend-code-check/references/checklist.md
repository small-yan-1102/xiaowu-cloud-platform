# 代码规约检查清单

> 本文档为 Reviewer 模式资源。SKILL.md Step 2 确定代码类型后，加载对应章节进行检查。
> 
> **权威规范文档**（本清单为索引，检查时以规范文档为最终依据）：
> 
> | 层级 | 规范文档 | 适用场景 |
> |-----|---------|---------|
> | L1 核心 | [CODING_STANDARDS.md](CODING_STANDARDS.md) | 所有 Java 代码必载 |
> | L2 代码 | [CODING_STANDARDS_CODE.md](CODING_STANDARDS_CODE.md) | Service / 业务逻辑 |
> | L3 数据 | [CODING_STANDARDS_DATA.md](CODING_STANDARDS_DATA.md) | Repository / 数据操作 |
> | L4 架构 | [CODING_STANDARDS_ARCH.md](CODING_STANDARDS_ARCH.md) | Controller / 领域模型 |

---

## L1 强制红线（所有 Java 代码必查）

> **权威来源**：[CODING_STANDARDS.md](CODING_STANDARDS.md)
> 
> 以下问题直接影响代码正确性或可维护性，**发现即为严重问题，必须修复后才能提交**。

| # | 检查项 | 违规示例 | 合规示例 |
|---|-------|---------|---------|
| 1 | **控制流必须使用大括号** | `if (x) return;` | `if (x) { return; }` |
| 2 | **字符串判空用 StrUtil** | `str == null \|\| str.isEmpty()` | `StrUtil.isBlank(str)` |
| 3 | **对象判等用 Objects.equals** | `a.equals(b)` | `Objects.equals(a, b)` |
| 4 | **集合判空用 CollectionUtils** | `list == null \|\| list.size() == 0` | `CollectionUtils.isEmpty(list)` |
| 5 | **禁止循环内数据库查询（N+1）** | `for(id : ids) { repo.findById(id); }` | 批量查询后内存匹配 |
| 6 | **禁止魔法值** | `if (status == 1)` | 使用枚举或常量 |
| 7 | **禁止吞掉异常** | `catch (Exception e) {}` | 至少记录日志或重新抛出 |
| 8 | **禁止使用 JdbcTemplate** | `jdbcTemplate.query(...)` | 使用 JPA 或 MyBatis |
| 9 | **方法返回值禁止用 Map** | `Map<String, Object> getInfo()` | 定义 POJO/VO 返回 |
| 10 | **禁止使用 JSONObject 解析** | `JSONObject.parseObject(str)` | 定义 POJO，用 JSON 工具反序列化 |
| 11 | **禁止直接取集合首元素** | `list.get(0)` | 先校验 `!CollectionUtils.isEmpty(list)` |
| 12 | **异常类型规范** | `throw new RuntimeException(...)` | `throw new WarnException(...)` 或 `ErrorException` |

---

## L2 代码层（Service / 业务逻辑类）

> **权威来源**：[CODING_STANDARDS_CODE.md](CODING_STANDARDS_CODE.md)
> 
> 发现即为**警告问题**，建议修复以提升可维护性。

| # | 检查项 | 说明 |
|---|-------|------|
| 1 | **单一职责** | 一个业务逻辑对应一个 private 方法，单方法不超过 80 行 |
| 2 | **卫语句优先** | 优先提前返回/抛异常，减少嵌套层级（嵌套不超过 3 层） |
| 3 | **ID 生成封装** | ID 生成逻辑必须封装为独立方法，禁止 inline UUID |
| 4 | **异常场景覆盖** | 每个业务逻辑都要考虑：参数非法、数据不存在、外部调用失败 |
| 5 | **枚举判断封装** | 多枚举值判断逻辑封装到枚举类静态方法中，禁止散落在 Service |
| 6 | **状态分组封装** | 多状态判断（如"活跃状态包含 A/B/C"）必须封装为枚举静态方法 |
| 7 | **分布式锁范式** | 使用 `LockerService`，禁止手写 Redis SETNX |
| 8 | **代码抽象复用** | 识别 3 处以上相同逻辑，提取为 private 方法或工具类 |
| 9 | **日志规范** | 方法入口有入参日志，关键分支有日志，异常有 error 日志；敏感信息脱敏 |
| 10 | **圈复杂度** | 单方法圈复杂度不超过 10 |

---

## L3 数据层（Repository / DAO / 数据操作类）

> **权威来源**：[CODING_STANDARDS_DATA.md](CODING_STANDARDS_DATA.md)
> 
> 发现即为**警告问题**（N+1 问题升级为**严重问题**）。

| # | 检查项 | 说明 |
|---|-------|------|
| 1 | **避免 SELECT *** | 明确指定查询字段，减少数据传输 |
| 2 | **禁止内存分页** | 必须使用数据库 LIMIT/OFFSET 分页，禁止查全量后截取 |
| 3 | **深度分页优化** | 超过 10 万条时推荐游标分页（WHERE id > lastId LIMIT N） |
| 4 | **禁止内存过滤** | 禁止查全量数据后在 Java 中 filter，过滤条件下推到 SQL |
| 5 | **大批量分批处理** | 批量操作超过 500 条须分批，每批不超过 200 条 |
| 6 | **缓存使用** | 频繁读取且低频变更的数据应使用缓存，更新时同步失效 |
| 7 | **禁止循环内远程调用** | 同 L1 N+1，远程 HTTP/RPC 调用也适用 |
| 8 | **索引命名规范** | 唯一索引 `uk_`，普通索引 `idx_`，全文索引 `ft_` |

---

## L4 架构层（Controller / API 接口 / 领域模型 / Entity）

> **权威来源**：[CODING_STANDARDS_ARCH.md](CODING_STANDARDS_ARCH.md)
> 
> 发现即为**警告问题**（`@NeedLogin` 缺失升级为**严重问题**）。

| # | 检查项 | 说明 |
|---|-------|------|
| 1 | **API 路径规范** | 前端接口用 `/appApi/`，微服务间接口用 `/cloudApi/` |
| 2 | **@NeedLogin 注解** | `/appApi/` 下所有接口必须加 `@NeedLogin`，缺失为严重问题 |
| 3 | **越权检查** | 查询/操作接口必须校验数据归属（用户只能访问自己的数据） |
| 4 | **公共组件优先** | 优先使用 `MapperUtil`、`LockerService`、`RetryUtil` 等团队组件 |
| 5 | **Maven 版本管理** | 依赖版本号必须在根 pom 统一管理，子模块不写版本号 |
| 6 | **DDD 依赖方向** | 领域层不得依赖适配层/基础设施；应用层不得直接操作数据库 |
| 7 | **聚合根创建** | 必须通过静态工厂方法创建，禁止 new 后直接 set |
| 8 | **领域事件发布** | 通过 `publisher().attachEvent()` 在聚合根内发布，禁止在 Handler 外部发布 |

---

## 严重程度说明

| 级别 | 含义 | 处理要求 |
|-----|------|---------|
| 🚨 严重 | 违反强制红线或关键架构约束 | **必须修复后提交** |
| ⚠️ 警告 | 代码质量/可维护性问题 | 建议修复，可酌情处理 |
| ✅ 通过 | 符合规约或有优秀实践 | 记录表扬 |
