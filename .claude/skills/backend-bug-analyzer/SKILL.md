---
name: backend-bug-analyzer
description: 自动打开 Bug 页面、提取完整信息并生成结构化分析报告，帮助研发快速定位问题根因。只展示 Bug 描述中确定存在的信息，禁止推断猜测。当用户需要分析 Bug、排查问题、获取 Bug 详情时使用此技能。触发关键词：分析 Bug、看一下这个 Bug、帮我排查、Bug 分析。
---

# Bug 分析技能

使用 Chrome DevTools 自动访问 Bug 页面，提取所有确定信息，输出结构化分析报告。

**核心原则**：只展示在 Bug 描述中**明确存在**的信息，禁止使用"应该"、"可能"、"推断"等不确定词汇。

---

## 前置依赖：Chrome DevTools MCP

> ⛔ **本技能强依赖 Chrome DevTools MCP，没有它无法执行任何步骤。**

**启动时必须先检测 Chrome DevTools MCP 是否可用**：调用 `list_pages` 工具，如果调用成功则继续；如果工具不存在或调用失败，立即停止并提示用户安装：

```
❌ 未检测到 Chrome DevTools MCP

本技能需要 Chrome DevTools MCP 才能运行，请按以下步骤安装：

1. 打开 Claude Code 设置（claude.ai/code 或 CLI 配置文件）
2. 在 MCP 插件列表中添加：chrome-devtools-mcp
3. 安装完成后重启 Claude Code
4. 重新执行本技能

安装文档：https://github.com/nicobailon/claude-code-chrome-devtools-mcp
```

> ⛔ **DO NOT** 继续执行任何后续步骤，直到 Chrome DevTools MCP 可用。

---

## 附属资源文件

| 文件 | 路径 | 加载时机 |
|------|------|---------|
| 报告输出模板 | `assets/report-template.md` | Step 6 生成报告前加载 |
| 信息提取与验证规则 | `references/extraction-rules.md` | Step 4 提取接口信息前加载 |

---

## 核心工作流

```
Task Progress:
- [ ] Step 0: 检测 Chrome DevTools MCP 可用性
- [ ] Step 1: 获取 Bug URL（Inversion）
- [ ] Step 2: 打开页面 & 处理登录
- [ ] Step 3: 提取基础信息
- [ ] Step 4: 完整读取描述 & 分析截图
- [ ] Step 5: 识别接口信息（Reviewer）
- [ ] Step 6: 生成分析报告（Generator）
```

---

## Step 1：获取 Bug URL

检查用户是否已提供 Bug 链接，如未提供则询问：

```
请提供需要分析的 Bug 链接。
支持：阿里云云效 / GitHub Issues / Jira / 其他 Web Bug 系统
```

> ⛔ **DO NOT** 执行任何浏览器操作，直到获取到 Bug URL。

---

## Step 2：打开页面 & 处理登录

1. `new_page` 创建新标签页
2. `navigate_page` 导航到 Bug URL
3. `wait_for` 等待页面加载（超时 10 秒）
4. `take_snapshot` 检测是否在登录页面

**登录检测**（URL 含 `login`/`auth`，或页面有账密输入框）：

```
📍 检测到需要登录
请在浏览器窗口中完成登录，Skill 将自动监控页面变化。
⏳ 等待中...
```

使用 `wait_for` 监控登录完成，页面跳转后继续。

---

## Step 3：提取基础信息

使用 `evaluate_script` 从页面 DOM 提取：

| 字段 | 说明 |
|------|------|
| Bug ID / 标题 | 工作项编号和标题文本 |
| 创建人 & 时间 | 创建节点的人名和时间戳 |
| 最后更新人 & 时间 | 更新节点的人名和时间戳 |
| 状态 / 优先级 / 严重程度 | 对应字段值 |
| 负责人 / 验证者 | 对应人员字段 |
| 项目 / 迭代 | 所属项目和迭代信息 |

**仅记录页面中实际存在的字段，无值字段标注"未填写"。**

---

## Step 4：完整读取描述 & 分析截图

1. 找到"描述"/"详情"区域
2. `click` 展开所有"查看更多"/"展开"按钮
3. `evaluate_script` 获取完整描述文本
4. 提取所有图片 URL（`<img>` 标签）
5. 对每张截图使用视觉能力分析：
   - 界面名称和功能区域
   - 表格数据和字段值
   - 错误信息和堆栈跟踪
   - API 请求和响应内容

---

## Step 5：识别接口信息

**加载资源**：读取 `references/extraction-rules.md`

按规则文件中定义的 5 个优先级，从描述文本和截图中搜索接口信息。

**识别到信息时**：记录内容 + 明确标注来源（第几行 / 第几张截图）。

**未识别到接口路径时**：触发交互式补充流程：

```
❌ 在 Bug 描述中未找到明确的接口路径

🔍 已识别的确定信息：
  [列出已确认的技术信息]

❓ 请补充以下至少一项（内容必须来自 Bug 描述或日志）：
1. API 接口路径（如：POST /api/v1/orders/create）
2. 微服务名称（如：order-service）
3. 数据库表名（如：orders）
4. 代码类/方法（如：com.xxx.OrderService.create()）
5. HTTP 方法 + URL 完整组合
```

用户补充后按规则严格验证：信息必须来自 Bug 真实内容，否则拒绝并要求重新输入。

> ⛔ **DO NOT** 推断、猜测或添加 Bug 描述中不存在的信息。

---

## Step 6：生成分析报告

**加载资源**：读取 `assets/report-template.md`

按模板结构逐节填充，输出完整报告：

1. **Bug 基础信息** — Step 3 提取结果
2. **Bug 详细描述** — Step 4 完整文本
3. **截图分析** — 每张截图的分析结果
4. **接口路径识别** — Step 5 确认信息（含来源标注）
5. **Bug 原因分析** — 问题现象、根本原因、影响范围、修复方向
6. **研发排查建议** — 代码检查点、复现步骤、数据库检查

**无法确认的信息**单独列出并标注"未在 Bug 描述中找到"，不做任何推断填充。

---

## 关键约束汇总

| 门控点 | 约束 |
|--------|------|
| Step 1 → Step 2 | 必须获取到 Bug URL |
| Step 2 → Step 3 | 登录检测通过，页面正常加载 |
| Step 5 识别失败 | 必须触发用户补充流程，禁止跳过 |
| Step 5 用户补充 | 信息必须来自 Bug 真实内容，否则拒绝 |
| 整个流程 | 禁止推断、禁止"可能/应该/推断"等词汇 |
