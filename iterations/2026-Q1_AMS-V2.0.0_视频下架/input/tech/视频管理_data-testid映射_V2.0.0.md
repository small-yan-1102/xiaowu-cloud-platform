# 视频管理 data-testid 映射文档 - V2.0.0

**版本控制**：V2.0.0 | **状态**：Active | **最后更新**：2026-03-24

---

## 模块编号定义

| 编号 | 模块 | 路由 |
| ---- | ---- | ---- |
| 01 | YT频道 | /resourceManagement/ytChannel/List |
| 02 | 视频管理 | /resourceManagement/videoManage/List |
| 03 | 员工管理 | /systemSetting/employeeManagement/List |

---

## data-testid 命名规范

格式：`{模块编号}_{场景编号}_{序号}`

| 部分     | 说明                                            | 示例                               |
| -------- | ----------------------------------------------- | ---------------------------------- |
| 模块编号 | 两位数字，与路由页面对应                        | `02`（视频管理）                   |
| 场景编号 | `layout`（布局）或 `S{N}-{M:02d}`（场景N第M步） | `layout`、`S1-01`、`S2-01`         |
| 序号     | 两位数字，同一场景内从 01 递增                  | `01`、`02`、`03`                   |

---

## Quest 1: 视频下架列表页

**页面文件**：`src/views/resourceManagement/videoManage/List.vue`

| DOM 元素 | data-testid | 说明 |
|----------|-------------|------|
| 页面根容器 | `02_layout_01` | AppView 根容器 |
| 页面提示信息区 | `02_layout_02` | nav-tip 提示区域 |
| 搜索表单容器 | `02_S1-01_01` | SearchForm 组件 |
| 重置按钮 | `02_S1-01_02` | 搜索表单内的重置按钮 |
| 查询按钮 | `02_S1-01_03` | 搜索表单内的查询按钮 |
| 表格容器 | `02_S1-01_04` | SuperTable 组件 |
| 查看详情按钮 | `02_S1-01_05` | 操作列的查看详情链接（动态，每行一个） |
| 分页组件 | `02_S1-01_06` | vl-pagination 组件 |

---

## Quest 2: 进度查看页

**页面文件**：`src/views/resourceManagement/videoManage/ProgressDrawer.vue`

| DOM 元素 | data-testid | 说明 |
|----------|-------------|------|
| Drawer容器 | `02_S2-01_01` | BasicDrawer 组件 |
| 标题区（含状态标签） | `02_S2-01_02` | drawer-title-wrapper |
| 导出失败文件按钮 | `02_S2-01_03` | 导出按钮 |
| 视频明细表格 | `02_S2-01_04` | SuperTable 组件 |
| 分页组件 | `02_S2-01_05` | vl-pagination 组件 |
| 关闭按钮 | `02_S2-01_06` | 底部关闭按钮 |

---

## 修改文件清单

| 文件 | 修改内容 |
|------|----------|
| `src/views/resourceManagement/videoManage/List.vue` | 添加页面级 data-testid |
| `src/views/resourceManagement/videoManage/ProgressDrawer.vue` | 添加抽屉组件 data-testid |
| `src/components/SearchForm/index.vue` | 新增 `searchBtnTestId`、`resetBtnTestId` props 支持按钮级 testid |

---

## 使用示例

### 测试选择器

```javascript
// 获取页面根容器
cy.get('[data-testid="02_layout_01"]')

// 获取查询按钮
cy.get('[data-testid="02_S1-01_03"]')

// 获取表格
cy.get('[data-testid="02_S1-01_04"]')

// 获取查看详情按钮（第一个）
cy.get('[data-testid="02_S1-01_05"]').first()

// 获取 Drawer
cy.get('[data-testid="02_S2-01_01"]')
```

### SearchForm 组件使用

```vue
<SearchForm
  data-testid="02_S1-01_01"
  :columns="searchConfig"
  :value="searchForm"
  :search="search"
  :reset="reset"
  search-btn-testid="02_S1-01_03"
  reset-btn-testid="02_S1-01_02"
/>
```
