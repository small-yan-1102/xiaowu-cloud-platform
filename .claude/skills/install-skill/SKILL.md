---
name: install-skill
description: 将 harness-engineering 仓库中的技能安装到目标项目或全局目录，支持 Claude Code、Qoder、Codex 三种工具环境。
version: 2.0.0
triggers:
  - "安装技能"
  - "install skill"
  - "把技能安装到项目"
  - "帮我安装技能"
  - "技能安装"
  - "deploy skill"
dependencies: []
---

# 技能安装工具

## 角色定位

你是一个技能安装助手，负责将 harness-engineering 仓库中的技能（Skill）复制到目标目录，使其可以在目标项目或全局环境中被 Claude Code / Qoder / Codex 调用。

---

## 核心工作流

```
Task Progress:
- [ ] Phase 1: 扫描可用技能
- [ ] Phase 2: 收集安装参数
- [ ] Phase 3: 执行安装
- [ ] Phase 4: 验证安装结果
```

---

### Phase 1: 扫描可用技能

**目标**：从 harness-engineering 仓库的 `skills/iteration/` 目录扫描所有可安装的技能。

**步骤**：

1. **定位仓库根目录**：
   - 确定 harness-engineering 仓库路径（即本 SKILL.md 所在路径向上三级的目录）
   - 仓库根目录 = 本 SKILL.md 路径中 `skills/iteration/install-skill/SKILL.md` 前的部分

2. **扫描所有技能**：
   - 遍历 `<仓库根目录>/skills/iteration/` 下的每个子分类目录
   - 在每个分类目录下找到包含 `SKILL.md` 的子目录，每个这样的目录即为一个可安装技能
   - 读取每个技能的 `SKILL.md` frontmatter，提取 `name` 和 `description`
   - **排除** `install-skill` 本身（不需要安装安装工具自身）

3. **展示可用技能列表**：

   ```
   ┌─────────────────────────────────────────────┐
   │        harness-engineering 可用技能列表        │
   ├─────────────────────────────────────────────┤
   │ 分类: prd-review                              │
   │  [1] backend-prd-review  - 后端开发视角审阅PRD │
   │  [2] frontend-prd-review - 前端开发视角审阅PRD │
   │  [3] test-prd-review     - 测试视角审阅PRD     │
   │                                              │
   │ 分类: technical-solution                      │
   │  [4] backend-tech-design-mvc - MVC架构技术方案  │
   └─────────────────────────────────────────────┘
   ```

**本阶段输出**：可安装技能列表（编号、名称、分类、描述摘要）

---

### Phase 2: 收集安装参数

**目标**：收集用户要安装哪些技能、使用什么工具、安装到什么位置。

**步骤**：

1. **选择目标工具平台**：

   使用 AskUserQuestion 询问用户在哪个工具中使用这些技能：

   | 选项 | 工具 | 技能目录名 |
   |------|------|-----------|
   | A. Claude Code | Anthropic Claude Code CLI | `.claude/skills/` |
   | B. Qoder | Qoder AI 编程工具 | `.qoder/skills/` |
   | C. Codex | OpenAI Codex CLI | `.codex/skills/` |
   | D. 全部 | 同时安装到以上三个工具的目录 | 依次安装到三个目录 |

   > 若用户选择 D（全部），则后续安装步骤对 Claude Code、Qoder、Codex 三个目标路径各执行一次，安装结果汇总时分工具展示。

2. **选择要安装的技能**：
   - 使用 AskUserQuestion 让用户选择：
     - 选项 A：安装全部技能
     - 选项 B：按分类安装（指定分类名）
     - 选项 C：安装指定技能（输入技能编号或名称，多个用逗号分隔）

3. **选择安装目标**：
   - 使用 AskUserQuestion 让用户选择安装位置：

   根据所选工具平台，`<skills-dir>` 替换为对应工具目录名：

   | 选项 | 目标路径 | 说明 |
   |------|---------|------|
   | A. 当前项目 | `<当前工作目录>/.<tool>/skills/` | 安装到当前工作目录的项目中 |
   | B. 指定项目 | `<用户输入路径>/.<tool>/skills/` | 安装到用户指定的项目目录中 |
   | C. 全局（当前用户） | `~/.<tool>/skills/` | 安装到用户主目录，对所有项目可用 |

   > 若用户选择 B，追问：请输入目标项目的根目录绝对路径

4. **确认安装计划**：

   向用户展示即将执行的操作，等待确认：

   ```
   即将执行以下安装：

   工具平台：Claude Code（或 Qoder / Codex）
   源仓库：<仓库根目录>/skills/iteration/
   目标位置：<目标路径>

   待安装技能：
   - backend-prd-review      → <目标路径>/backend-prd-review/
   - backend-tech-design-mvc → <目标路径>/backend-tech-design-mvc/

   包含文件：
   - SKILL.md（技能入口）
   - assets/（资产文件）
   - references/（参考规范）

   是否继续？[y/N]
   ```

   > ⛔ **DO NOT** 开始复制文件，直到用户明确确认。

**本阶段输出**：已确认的安装计划（工具平台 + 源路径列表 + 目标路径）

---

### Phase 3: 执行安装

**目标**：将选定技能的所有文件复制到目标目录。

**步骤**：

1. **创建目标基础目录**（如不存在）：
   - 使用 Bash 工具执行 `mkdir -p <目标路径>`

2. **逐技能安装**：

   对每个待安装技能，执行以下操作：

   a. **检查是否已存在**：
      - 检查 `<目标路径>/<skill-name>/` 是否已存在
      - 若已存在，提示用户：「技能 <skill-name> 已安装，将覆盖现有版本」
      - 继续执行（覆盖安装）

   b. **创建技能目录结构**：
      ```
      mkdir -p <目标路径>/<skill-name>/assets
      mkdir -p <目标路径>/<skill-name>/references
      ```

   c. **复制文件**：
      - 复制 `SKILL.md`
      - 复制 `assets/` 下的所有文件（如目录存在）
      - 复制 `references/` 下的所有文件（如目录存在）
      - 使用 `cp -r` 保留目录结构

      具体命令示例：
      ```bash
      cp "<源路径>/<skill-name>/SKILL.md" "<目标路径>/<skill-name>/SKILL.md"
      cp -r "<源路径>/<skill-name>/assets/." "<目标路径>/<skill-name>/assets/" 2>/dev/null || true
      cp -r "<源路径>/<skill-name>/references/." "<目标路径>/<skill-name>/references/" 2>/dev/null || true
      ```

   d. **记录安装结果**：
      - 成功：记录 ✅ `<skill-name>` 安装成功
      - 失败：记录 ❌ `<skill-name>` 安装失败 + 错误原因

3. **处理错误**：
   - 权限不足：提示用户检查目标目录写入权限
   - 路径不存在：重新创建目录后重试
   - 单个技能失败：跳过，继续安装其他技能，最终汇总失败列表

**本阶段输出**：安装执行日志

---

### Phase 4: 验证安装结果

**目标**：确认所有技能文件已正确复制到目标位置。

**步骤**：

1. **验证文件完整性**：

   对每个已安装技能，检查：
   - `<目标路径>/<skill-name>/SKILL.md` 是否存在
   - `assets/` 下的文件数量是否与源目录一致
   - `references/` 下的文件数量是否与源目录一致

2. **展示安装汇总**：

   ```
   ┌─────────────────────────────────────────────┐
   │               安装结果汇总                     │
   ├─────────────────────────────────────────────┤
   │ 工具平台：Claude Code                          │
   │ 安装位置：~/.claude/skills/                    │
   │                                              │
   │ ✅ backend-prd-review       已安装（3个文件）   │
   │ ✅ frontend-prd-review      已安装（3个文件）   │
   │ ✅ backend-tech-design-mvc  已安装（11个文件）  │
   │ ❌ test-prd-review          安装失败：权限不足  │
   │                                              │
   │ 成功：3 / 失败：1                              │
   └─────────────────────────────────────────────┘
   ```

3. **提示使用方式**：

   根据工具平台和安装位置给出对应使用提示：

   **Claude Code**：
   ```
   技能已安装到 <目标路径>

   在 Claude Code 中，技能会自动从 .claude/skills/（项目级）
   或 ~/.claude/skills/（全局）加载。
   触发示例：/backend-prd-review 或在对话中说「审阅PRD」
   ```

   **Qoder**：
   ```
   技能已安装到 <目标路径>

   在 Qoder 中，技能会自动从 .qoder/skills/（项目级）
   或 ~/.qoder/skills/（全局）加载。
   触发示例：在 Qoder 对话中说「安装技能」等触发词
   ```

   **Codex**：
   ```
   技能已安装到 <目标路径>

   在 Codex CLI 中，技能会自动从 .codex/skills/（项目级）
   或 ~/.codex/skills/（全局）加载。
   触发示例：在 Codex 对话中使用对应触发词
   ```

**本阶段输出**：安装验证报告 + 使用说明

---

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 目标目录不可写 | 提示检查权限，建议使用 `sudo` 或更换目标路径 |
| 源技能目录不存在 | 提示检查 harness-engineering 仓库是否完整 |
| 用户取消安装 | 输出「安装已取消」，不做任何文件操作 |
| 部分技能安装失败 | 跳过失败项，继续其余技能，最终汇总失败原因 |
| 目标路径已有同名技能 | 覆盖安装，告知用户旧版本已被替换 |

---

## 核心原则

- **幂等性**：重复执行安装结果一致，覆盖旧版本而非追加
- **最小权限**：只操作用户明确指定的目标路径，不修改其他目录
- **确认优先**：在执行任何文件写入前，必须获得用户明确确认
- **透明展示**：安装前展示完整操作计划，安装后展示完整结果汇总
