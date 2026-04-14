---
trigger: always_on
description: 测试环境基础设施配置 - 系统URL、登录路径、data-testid索引（AI执行测试的前置必读信息）。敏感凭证见 .claude/secrets/credentials.md
---

# 测试环境基础设施配置

> **定位**: AI 执行任何测试（冒烟/功能/回归）前的 **必读前置信息**  
> **更新日期**: 2026-04-10  
> **适用范围**: 所有测试迭代共用，非迭代专属数据  
> **凭证信息**: 数据库密码、服务器密码、系统登录密码等敏感信息已分离至 `.claude/secrets/credentials.md`，执行测试时按需读取

---

## 1. 数据库连接

| 项目 | 值 | 说明 |
|------|-----|------|
| Host | 172.16.24.61 | 测试环境 MySQL |
| Port | 3306 | |
| 用户名 | xiaowu_db | |
| 密码 | 见 `.claude/secrets/credentials.md` §1 | |

### 1.1 业务数据库清单

| 数据库名 | 所属系统 | 用途 |
|---------|---------|------|
| silverdawn_ams | AMS 资产管理系统 | 主库：作品、视频下架任务单、解约单等 |
| dispatcher | 分发调度系统 | 视频下架执行队列（video_takedown_queue） |

### 1.2 分发系统关键表

| 数据库 | 表名 | 用途 |
|--------|------|------|
| dispatcher | video_takedown_queue | YouTube 视频下架执行队列，审核通过后进入此队列排队执行 |

---

## 2. 测试服务器

| 服务器 | IP | 账号 | 密码 | 角色 |
|--------|-----|------|------|------|
| 服务器 A | 172.16.24.200 | test | 见 `.claude/secrets/credentials.md` §2 | 前端 + 部分后端服务 |
| 服务器 B | 172.16.24.204 | test | 见 `.claude/secrets/credentials.md` §2 | 后端服务 |
| 服务器 B (root) | 172.16.24.204 | root | 见 `.claude/secrets/credentials.md` §2 | 运维操作时使用 |

---

## 3. Redis

| 项目 | 值 |
|------|-----|
| Host | 172.16.24.200 |
| Port | 6379 |

---

## 4. 系统登录信息

### 4.1 小五云平台（SSO 统一登录）

> 小五云平台是所有内部系统的统一入口，通过 SSO 验证码登录后进入应用中心，再选择目标系统。

| 项目 | 值 |
|------|-----|
| 入口 URL（应用中心） | http://172.16.24.200:7778/MyApps |
| 入口 URL（SSO 登录页） | http://172.16.24.200:7778/ssoLogin |
| 登录方式 | 验证码登录 |
| 固定验证码 | 见 `.claude/secrets/credentials.md` §3.1 |

**账号列表**：

| 账号标识 | 手机号 | 用途 |
|---------|--------|------|
| 主账号 | 15057199668 | 默认测试账号（AMS/剧老板等） |
| 备用账号 | 18202748232 | 杨宇杰账号，分发系统测试 |

**通用登录路径**：
```
1. 访问 http://172.16.24.200:7778/ssoLogin（或 /MyApps 会自动跳转）
2. 选择「验证码登录」Tab
3. 输入手机号，验证码见 credentials.md，点击登录
4. 登录后进入应用中心 http://172.16.24.200:7778/home（可能出现欢迎弹窗，关闭即可）
5. 找到目标系统卡片，鼠标滑入后点击「进入系统」
6. 目标系统在新标签页打开
```

> 截图参考：`systems/_shared/login-screenshots/云平台/`

#### 4.1.1 → AMS 资产管理系统

| 项目 | 值 |
|------|-----|
| 应用中心卡片名称 | 资产管理系统 |
| 打开后 URL | http://172.16.24.200:8024 |
| 推荐账号 | 15057199668 |

#### 4.1.2 → 分发系统（新内容分发系统）

| 项目 | 值 |
|------|-----|
| 应用中心卡片名称 | 分发系统 |
| 打开后 URL | http://content-1.test.xiaowutw.com/ |
| 推荐账号 | 18202748232 |
| 侧边栏模块 | 资源池、频道运营、译制成品、信息监控、频道管理、字典设置 |

### 4.2 剧老板系统（分销商端）

| 项目 | 值 |
|------|-----|
| 入口 URL | http://distribute.test.xiaowutw.com/login |
| 登录方式 | 邮箱/手机号 + 密码登录 |

**账号列表**：

| 账号标识 | 登录账号 | 密码 | 权限类型 | 所属团队 | 用途 |
|---------|---------|------|---------|---------|------|
| 主分销商 | Yancz-cool@outlook.com | 见 credentials.md §3.2 | ALL（全量数据） | HELLO BEAR (team_id=1988839584685428736) | 冒烟测试主账号，MQ 同步验证 |
| 权限受限 | 15057199668 | 见 credentials.md §3.2 | 部门级（仅本部门） | YUJA-001 (team_id=1985522863929118720) | 权限隔离测试 |
| 空数据 | 18506850780 | 见 credentials.md §3.2 | SCOPE（范围管理） | YUJA-001 | 空列表/无数据场景测试 |
| 第二分销商 | 17835727272 | 见 credentials.md §3.2 | ALL（全量数据） | team_id=1988520080772243456 | 多分销商交叉验证 |

**登录路径**：
```
1. 访问 http://distribute.test.xiaowutw.com/login
2. 在账号输入框输入邮箱或手机号
3. 在密码输入框输入对应密码（见 credentials.md §3.2）
4. 点击「登录」按钮
5. 登录成功后进入系统首页，左侧导航栏可见
```

### 4.3 剧译宝系统

| 项目 | 值 |
|------|-----|
| 入口 URL | http://dubbing-1.test.xiaowutw.com/login |
| 登录方式 | 验证码登录 |

**账号列表**：

| 账号标识 | 手机号 | 验证码 | 用途 |
|---------|--------|--------|------|
| 主账号 | 15139407453 | 见 credentials.md §3.3 | 功能测试主账号 |

**登录路径**：
```
1. 访问 http://dubbing-1.test.xiaowutw.com/login
2. 选择「验证码登录」Tab
3. 输入手机号 15139407453，验证码见 credentials.md §3.3
4. 点击登录，进入首页
5. 左侧导航：首页、视频译制、系统设置
```

> 截图参考：`systems/_shared/login-screenshots/剧译宝/`

### 4.4 SSO API 接口登录

> 用于 AI 测试数据准备场景，通过接口获取 token 后调用业务 API。
> 接口凭证见 `.claude/secrets/credentials.md` §3.4

| 项目 | 值 |
|------|-----|
| 接口地址 | `POST http://172.16.24.200:8011/sso/doLogin` |
| 参数 | `name`=手机号, `pwd`=验证码 |
| 返回 | `token`（用于后续请求头 `accessToken`） |

**注意事项**：
- 登录成功后在后续请求头中携带 `accessToken: {token}`
- 验证码有效期 10 分钟
- 测试环境固定验证码见 credentials.md

---

## 5. AI 执行测试前置检查清单

AI 在开始执行任何测试用例前，**必须**确认以下信息：

- [ ] 已读取本文件获取环境连接信息
- [ ] 已读取 `.claude/secrets/credentials.md` 获取登录凭证
- [ ] 已读取当前迭代的 `smoke_test_data_config.md` 或对应数据配置文件
- [ ] 已确认测试环境 URL 可访问
- [ ] 已确认登录账号与目标系统匹配
- [ ] 已确认数据库中存在用例所需的前置数据（或知道如何创建）
- [ ] 已读取目标系统的 data-testid 映射文件（见§6 索引表）

---

## 6. data-testid 前端元素定位索引

> AI 执行测试时，**必须**根据目标系统读取对应的 data-testid 映射文件，用于前端元素定位。

### 6.1 AMS 资产管理系统

| 文件 | 覆盖模块 | 路径 |
|------|---------|------|
| README.md | 索引 + 命名规范 + 模块分配表 | `systems/AMS/knowledge/data-testid/README.md` |
| 01_视频下架.md | 视频下架模块（7组件，55+ 元素） | `systems/AMS/knowledge/data-testid/01_视频下架.md` |
| 02_内容解约单.md | 内容解约单模块（6组件，44 元素） | `systems/AMS/knowledge/data-testid/02_内容解约单.md` |

**业务流程参考文档**（按操作场景顺序映射 data-testid，与上述按组件组织的映射文件互补）：

| 业务场景 | 对应模块 | 路径 |
|---------|---------|------|
| 按作品创建任务单 | 01 视频下架 | `systems/AMS/knowledge/按作品创建_测试流程.md` |
| 创建解约单 | 02 内容解约单 | `systems/AMS/knowledge/创建解约单_测试流程.md` |

### 6.2 剧老板系统

| 文件 | 覆盖模块 | 路径 |
|------|---------|------|
| README.md | 索引 + 模块分配表 | `systems/剧老板/knowledge/data-testid/README.md` |
| 01_YT频道.md | YT频道模块 | `systems/剧老板/knowledge/data-testid/01_YT频道.md` |
| 02_视频管理.md | 视频管理模块（列表页 + ProgressDrawer） | `systems/剧老板/knowledge/data-testid/02_视频管理.md` |
| 03_员工管理.md | 员工管理模块 | `systems/剧老板/knowledge/data-testid/03_员工管理.md` |

### 6.3 财务结算系统

| 文件 | 覆盖模块 | 路径 |
|------|---------|------|
| README.md | 索引 + 语义命名规范 + 模块分配表 | `systems/结算系统/knowledge/data-testid/README.md` |
| 01_YT结算单.md ~ 10_生成记录.md | 10 个语义命名模块（~365 元素） | `systems/结算系统/knowledge/data-testid/` |
| 11_逾期结算处理.md | 逾期结算处理（数字编号命名） | `systems/结算系统/knowledge/data-testid/11_逾期结算处理.md` |

### 6.4 云平台（SSO 登录 + 应用中心）

| 文件 | 覆盖模块 | 路径 |
|------|---------|------|
| README.md | 索引 + 命名规范 + 模块分配表 | `systems/云平台/knowledge/data-testid/README.md` |
| 01_登录与应用中心.md | 登录页（12 元素）+ 应用中心（32 元素） | `systems/云平台/knowledge/data-testid/01_登录与应用中心.md` |

> **说明**：云平台 data-testid 包含两种命名方式——登录页使用标准编号格式 `{模块编号}_{场景编号}_{序号}`，应用中心使用 `{appId}` / `{appId}_click` 格式。

### 6.5 CRM 系统

> **data-testid 尚未创建**。CRM 系统测试用例暂无 data-testid 映射文件，元素定位退回使用可见文本 → aria-label → CSS 选择器顺序。

### 6.6 总控系统

> **data-testid 尚未创建**。总控系统测试用例暂无 data-testid 映射文件，元素定位退回使用可见文本 → aria-label → CSS 选择器顺序。

### 6.7 使用规则

1. **按系统匹配**：执行哪个系统的测试，就读取该系统下的全部 data-testid 文件
2. **元素定位优先级**：`data-testid` > `aria-label` > CSS 选择器 > XPath
3. **testid 命名格式**：`{模块编号}_{场景编号}_{序号}`（如 `01_S3-01_01`）
4. **业务流程参考**：执行特定业务场景的用例时，优先查阅对应的「业务流程参考文档」按操作顺序定位元素，再用「data-testid 映射文件」补充
5. **新增系统**：后续新系统的 data-testid 文件同样添加到本索引中
6. **云平台登录前置**：所有通过云平台 SSO 登录的系统（AMS、分发系统等），在登录阶段需先读取云平台的 data-testid 文件定位登录元素和应用中心卡片

---

*最后更新：2026-04-10*
