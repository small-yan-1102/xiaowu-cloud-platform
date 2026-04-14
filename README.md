# 小五云平台 - 项目管理根目录

> 双维度结构：系统维度（持久化知识沉淀）+ 迭代维度（项目管理推进）

---

## 目录结构

```
小五云平台/
|
+-- systems/                              # 维度一：系统（持久化，跨迭代沉淀）
|   +-- AMS/knowledge/                    #   AMS 资产管理系统
|   +-- 剧老板/knowledge/                  #   剧老板系统
|   +-- CRM/knowledge/                    #   CRM 系统
|   +-- 总控系统/knowledge/                #   总控系统（额度管理）
|   +-- 结算系统/knowledge/                #   结算系统
|   +-- _shared/                          #   跨系统共享知识
|       +-- 系统关系图.md                  #     系统间数据流+调用关系
|       +-- 枚举值字典.md                  #     全局统一枚举定义
|       +-- 代码仓库管理.md                #     仓库总索引+管理规范
|
+-- iterations/                           # 维度二：迭代（项目管理，按时间推进）
|   +-- 2026-Q1_AMS-V2.0.0_视频下架/     #   迭代示例
|       +-- README.md                     #     迭代概览卡片
|       +-- input/prd/                    #     需求输入
|       +-- review/                       #     反审/评审
|       +-- testcase/                     #     测试用例
|       +-- report/                       #     测试报告
|
+-- templates/                            # 模板（复用）
|   +-- iteration_readme.md               #   迭代概览卡片模板
|   +-- changelog.md                      #   系统变更记录模板
|   +-- system_knowledge.md               #   系统功能清单模板
|
+-- README.md                             # 本文件：根目录索引
+-- 目录结构说明.md                         # 详细的目录结构使用说明
```

---

## 快速指南

### 新建迭代

1. 在 `iterations/` 下创建目录，命名：`{年份}-{季度}_{系统}-{版本}_{主题}`
2. 复制 `templates/iteration_readme.md` 为 `README.md`
3. 填写涉及系统、数据流、产出物索引
4. 在每个涉及系统的 `knowledge/changelog.md` 中追加变更记录

### 查找系统知识

- 进入 `systems/{系统名}/knowledge/` 查看功能清单、权限模型、已知问题
- 通过 `changelog.md` 反查该系统被哪些迭代改过

### 查找跨系统信息

- `systems/_shared/枚举值字典.md`：统一枚举定义
- `systems/_shared/系统关系图.md`：系统间调用关系
- `.claude/rules/test-environment-config.md`：测试环境地址和账号（密码见 `.claude/secrets/credentials.md`）

---

> 详细使用说明见 [目录结构说明.md](./目录结构说明.md)
