---
skill: backend-tech-design-presentation
based_on: harness@1.0.0
he_path: linscode/skills/iteration/technical-solution/backend-tech-design-presentation
override_count: 3
last_updated: 2026-04-15
---

# backend-tech-design-presentation 项目定制

## 覆盖 1：Phase 0 文档自动检测 + 下游说明

**HE 原文位置**：Phase 0 信息收集
**HE 原文摘要**：直接 AskUserQuestion 收集文档来源
**定制为**：首先自动检测上下文中是否已有设计文档，有则跳过问询。补充路径解析规则和下游说明（本 Skill 产出不被下游 AI Skill 消费）。

## 覆盖 2：影响粒度判定

**HE 原文位置**：Phase 1.3 → 影响粒度表
**HE 原文摘要**：4 行表格（服务级/模块级/功能级/类级）
**定制为**：替换为决策树——变更涉及 >1 个微服务？→ 服务级；单服务内 >2 模块？→ 模块级；涉及实体变更？→ 类级；否则 → 功能级

## 新增 1：Phase 3 状态管理

**HE 原文位置**：Phase 3 预览确认 → 用户选择 2/3/4 后
**HE 原文摘要**：执行操作后重新进入检查点（无状态管理说明）
**定制为**：循环中保留所有已完成章节内容，仅重新生成用户指定修改的部分
