# 小五云平台 - 项目管理根目录

> 双维度结构：系统维度（持久化知识沉淀）+ 迭代维度（项目管理推进）

## 📚 权威文档入口

| 想了解什么 | 去哪里看 |
|---|---|
| 完整目录结构 + 使用说明 | [目录结构说明.md](./目录结构说明.md) |
| Claude Code 配置 + 测试工作流 + 规则体系 | [CLAUDE.md](./CLAUDE.md) |
| 测试环境与账号 | `.claude/docs/test-environment-config.md`（密码见 `.claude/secrets/credentials.md`）|
| 跨系统共享知识 | `systems/_shared/`（系统关系图、枚举字典、代码仓库管理）|

## 🚀 快速指南

### 新建迭代

1. 在 `iterations/` 下创建目录，命名：`{年份}-{季度}_{系统}-{版本}_{主题}`
2. 复制 `templates/iteration_readme.md` 为 `README.md`
3. 填写涉及系统、数据流、产出物索引
4. 在每个涉及系统的 `knowledge/changelog.md` 中追加变更记录

### 查找系统知识

- 进入 `systems/{系统名}/knowledge/` 查看功能清单、权限模型、已知问题
- 通过 `changelog.md` 反查该系统被哪些迭代改过

### 调用 Skill / 斜杠命令

完整命令清单见 [CLAUDE.md §可用技能命令](./CLAUDE.md)，或 Claude Code 中输入 `/` 查看。

---

*目录树和详细说明见 [目录结构说明.md](./目录结构说明.md)，避免与本文件重复维护。*
