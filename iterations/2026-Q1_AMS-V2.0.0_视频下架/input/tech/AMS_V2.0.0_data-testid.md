# AMS V2.0.0 data-testid 映射清单

**版本**：V2.0.0  
**创建日期**：2026-03-23  
**状态**：待添加

---

## 模块编号定义

| 编号 | 模块 | 路径 |
| ---- | ---- | ---- |
| 01 | 视频下架 | src/views/video-manage/video-shelves |
| 02 | 内容解约单 | src/views/content-assets/content-termination |

---

## 命名规范

`data-testid` 格式：`{模块编号}_{场景编号}_{序号}`

| 部分 | 说明 | 示例 |
| ---- | ---- | ---- |
| 模块编号 | 两位数字，与功能模块对应 | `01`、`02` |
| 场景编号 | `layout`（布局）或 `S{N}-{M:02d}`（场景N第M步） | `layout`、`S1-01`、`S2-01` |
| 序号 | 两位数字，同一场景内从 01 递增 | `01`、`02`、`03` |

---

## 一、视频下架模块（01）

### 1.1 Quest 1-2: 列表页 (list.vue)

**文件路径**：`src/views/video-manage/video-shelves/list.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 页面根容器 | `01_layout_01` | `[data-testid="01_layout_01"]` |
| Tab 区域 | `01_layout_02` | `[data-testid="01_layout_02"]` |
| 搜索表单 | `01_layout_03` | `[data-testid="01_layout_03"]` |
| 创建任务单按钮 | `01_S1-01_01` | `[data-testid="01_S1-01_01"]` |
| 按作品创建菜单项 | `01_S1-01_02` | `[data-testid="01_S1-01_02"]` |
| 按视频ID创建菜单项 | `01_S1-01_03` | `[data-testid="01_S1-01_03"]` |
| 数据表格 | `01_S1-01_04` | `[data-testid="01_S1-01_04"]` |
| 任务单编号链接 | `01_S1-01_05` | `[data-testid="01_S1-01_05"]` |
| 分页组件 | `01_layout_04` | `[data-testid="01_layout_04"]` |
| 排序提示文案 | `01_S2-01_01` | `[data-testid="01_S2-01_01"]` |
| 排序说明图标 | `01_S2-01_02` | `[data-testid="01_S2-01_02"]` |

---

### 1.2 Quest 3-4: 创建任务单抽屉 (CreateTaskDrawer.vue)

**文件路径**：`src/views/video-manage/video-shelves/components/CreateTaskDrawer.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 抽屉容器 | `01_S3-01_01` | `[data-testid="01_S3-01_01"]` |
| 下架原因下拉框 | `01_S3-01_02` | `[data-testid="01_S3-01_02"]` |
| 下架说明输入框 | `01_S3-01_03` | `[data-testid="01_S3-01_03"]` |
| 处理方式单选组 | `01_S3-01_04` | `[data-testid="01_S3-01_04"]` |
| 截止执行日期选择器 | `01_S3-01_05` | `[data-testid="01_S3-01_05"]` |
| 新增作品按钮 | `01_S3-01_06` | `[data-testid="01_S3-01_06"]` |
| 批量导入按钮 | `01_S3-01_07` | `[data-testid="01_S3-01_07"]` |
| 已选作品表格 | `01_S3-01_08` | `[data-testid="01_S3-01_08"]` |
| 取消按钮 | `01_S3-01_09` | `[data-testid="01_S3-01_09"]` |
| 提交审批按钮 | `01_S3-01_10` | `[data-testid="01_S3-01_10"]` |
| 任务来源下拉框（按视频ID创建） | `01_S4-01_01` | `[data-testid="01_S4-01_01"]` |
| 分销商名称下拉框（按视频ID创建） | `01_S4-01_02` | `[data-testid="01_S4-01_02"]` |
| 运营团队下拉框（按视频ID创建） | `01_S4-01_03` | `[data-testid="01_S4-01_03"]` |
| 海外频道ID可点击单元格 | `01_S3-01_26` | `[data-testid="01_S3-01_26"]` |
| 删除作品图标 | `01_S3-01_27` | `[data-testid="01_S3-01_27"]` |

---

### 1.3 Quest 3: 选择作品弹窗 (SelectWorksModal.vue)

**文件路径**：`src/views/video-manage/video-shelves/components/SelectWorksModal.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 弹窗容器 | `01_S3-01_11` | `[data-testid="01_S3-01_11"]` |
| 作品名称搜索框 | `01_S3-01_12` | `[data-testid="01_S3-01_12"]` |
| CP名称搜索框 | `01_S3-01_13` | `[data-testid="01_S3-01_13"]` |
| 查询按钮 | `01_S3-01_14` | `[data-testid="01_S3-01_14"]` |
| 重置按钮 | `01_S3-01_15` | `[data-testid="01_S3-01_15"]` |
| 作品选择表格 | `01_S3-01_16` | `[data-testid="01_S3-01_16"]` |
| 确认按钮 | `01_S3-01_17` | `[data-testid="01_S3-01_17"]` |
| 已选择数量文本 | `01_S3-01_28` | `[data-testid="01_S3-01_28"]` |

---

### 1.4 Quest 3-4: 选择海外频道弹窗 (SelectDialog.vue)

**文件路径**：`src/views/video-manage/video-shelves/components/SelectDialog.vue`

| 元素描述 | data-testid | 选择器示例 | 状态 |
| -------- | ----------- | ---------- | ---- |
| 弹窗容器 | `01_S3-01_18` | `[data-testid="01_S3-01_18"]` | ✅ 已添加 |
| 海外频道名称搜索框 | `01_S3-01_19` | `[data-testid="01_S3-01_19"]` | ✅ 已添加 |
| 查询按钮 | `01_S3-01_20` | `[data-testid="01_S3-01_20"]` | ✅ 已添加 |
| 重置按钮 | `01_S3-01_21` | `[data-testid="01_S3-01_21"]` | ✅ 已添加 |
| 频道选择表格 | `01_S3-01_22` | `[data-testid="01_S3-01_22"]` | ✅ 已添加 |
| 已选频道列表 | `01_S3-01_23` | `[data-testid="01_S3-01_23"]` | ✅ 已添加 |
| 取消按钮 | `01_S3-01_24` | `[data-testid="01_S3-01_24"]` | ✅ 已添加 |
| 保存按钮 | `01_S3-01_25` | `[data-testid="01_S3-01_25"]` | ✅ 已添加 |
| 单个删除图标 | `01_S3-01_29` | `[data-testid="01_S3-01_29"]` | ✅ 已添加 |
| 全部清空图标 | `01_S3-01_30` | `[data-testid="01_S3-01_30"]` | ✅ 已添加 |

---

### 1.5 Quest 5: 详情抽屉 (DetailDrawer.vue)

**文件路径**：`src/views/video-manage/video-shelves/components/DetailDrawer.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 抽屉容器 | `01_S5-01_01` | `[data-testid="01_S5-01_01"]` |
| 基础信息区块 | `01_S5-01_02` | `[data-testid="01_S5-01_02"]` |
| 整体完成进度区块 | `01_S5-01_03` | `[data-testid="01_S5-01_03"]` |
| 作品处理进度区块 | `01_S5-01_04` | `[data-testid="01_S5-01_04"]` |
| 导出全部文件按钮 | `01_S5-01_05` | `[data-testid="01_S5-01_05"]` |
| 导出失败文件按钮 | `01_S5-01_06` | `[data-testid="01_S5-01_06"]` |
| 搜索表单 | `01_S5-01_07` | `[data-testid="01_S5-01_07"]` |
| 作品列表 | `01_S5-01_08` | `[data-testid="01_S5-01_08"]` |

---

### 1.6 Quest 5: 视频明细面板 (WorkItemPanel.vue)

**文件路径**：`src/views/video-manage/video-shelves/components/WorkItemPanel.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 视频明细表格 | `01_S5-01_09` | `[data-testid="01_S5-01_09"]` |
| 分页组件 | `01_S5-01_10` | `[data-testid="01_S5-01_10"]` |

---

### 1.7 审核弹窗 (AuditDialog.vue)

**文件路径**：`src/views/video-manage/video-shelves/components/AuditDialog.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 弹窗容器 | `01_S1-01_06` | `[data-testid="01_S1-01_06"]` |
| 通过选项 | `01_S1-01_07` | `[data-testid="01_S1-01_07"]` |
| 不通过选项 | `01_S1-01_08` | `[data-testid="01_S1-01_08"]` |
| 审核意见输入框 | `01_S1-01_09` | `[data-testid="01_S1-01_09"]` |
| 取消按钮 | `01_S1-01_10` | `[data-testid="01_S1-01_10"]` |
| 确认按钮 | `01_S1-01_11` | `[data-testid="01_S1-01_11"]` |

---

## 二、内容解约单模块（02）

### 2.1 Quest 6: 解约单列表页 (List.vue)

**文件路径**：`src/views/content-assets/content-termination/List.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 页面根容器 | `02_layout_01` | `[data-testid="02_layout_01"]` |
| 搜索表单 | `02_layout_02` | `[data-testid="02_layout_02"]` |
| 创建解约单按钮 | `02_S6-01_01` | `[data-testid="02_S6-01_01"]` |
| 数据表格 | `02_S6-01_02` | `[data-testid="02_S6-01_02"]` |
| 解约单编号链接 | `02_S6-01_03` | `[data-testid="02_S6-01_03"]` |
| 按分销商创建菜单项 | `02_S6-01_04` | `[data-testid="02_S6-01_04"]` |
| 按作品创建菜单项 | `02_S6-01_05` | `[data-testid="02_S6-01_05"]` |
| 分页组件 | `02_layout_03` | `[data-testid="02_layout_03"]` |

---

### 2.2 Quest 7: 创建解约单抽屉 (Add.vue)

**文件路径**：`src/views/content-assets/content-termination/components/Add.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 抽屉容器 | `02_S7-01_01` | `[data-testid="02_S7-01_01"]` |
| 分销商名称下拉框 | `02_S7-01_02` | `[data-testid="02_S7-01_02"]` |
| 解约类型下拉框 | `02_S7-01_03` | `[data-testid="02_S7-01_03"]` |
| 解约原因输入框 | `02_S7-01_04` | `[data-testid="02_S7-01_04"]` |
| 解约日期选择器 | `02_S7-01_05` | `[data-testid="02_S7-01_05"]` |
| 视频是否下架下拉框 | `02_S7-01_06` | `[data-testid="02_S7-01_06"]` |
| 下架原因下拉框（条件显示） | `02_S7-01_07` | `[data-testid="02_S7-01_07"]` |
| 下架说明输入框（条件显示） | `02_S7-01_08` | `[data-testid="02_S7-01_08"]` |
| 处理方式单选组（条件显示） | `02_S7-01_09` | `[data-testid="02_S7-01_09"]` |
| 截止执行日期选择器（条件显示） | `02_S7-01_10` | `[data-testid="02_S7-01_10"]` |
| 已选作品表格 | `02_S7-01_11` | `[data-testid="02_S7-01_11"]` |
| 添加作品按钮 | `02_S7-01_12` | `[data-testid="02_S7-01_12"]` |
| 批量导入按钮 | `02_S7-01_13` | `[data-testid="02_S7-01_13"]` |
| 取消按钮 | `02_S7-01_14` | `[data-testid="02_S7-01_14"]` |
| 解约按钮 | `02_S7-01_15` | `[data-testid="02_S7-01_15"]` |
| 删除作品图标（表格内） | `02_S7-01_29` | `[data-testid="02_S7-01_29"]` |

---

### 2.3 Quest 7-1: 添加作品弹窗 - 按分销商创建 (AddWork.vue)

**文件路径**：`src/views/content-assets/content-termination/components/AddWork.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 弹窗容器 | `02_S7-01_16` | `[data-testid="02_S7-01_16"]` |
| 作品下拉选择框 | `02_S7-01_17` | `[data-testid="02_S7-01_17"]` |
| 全选复选框 | `02_S7-01_18` | `[data-testid="02_S7-01_18"]` |
| 确定按钮 | `02_S7-01_19` | `[data-testid="02_S7-01_19"]` |
| 取消按钮 | `02_S7-01_20` | `[data-testid="02_S7-01_20"]` |

---

### 2.4 Quest 7-2: 添加作品弹窗 - 按作品创建 (AddWorkTable.vue)

**文件路径**：`src/views/content-assets/content-termination/components/AddWorkTable.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 弹窗容器 | `02_S7-01_21` | `[data-testid="02_S7-01_21"]` |
| 作品名称搜索框 | `02_S7-01_22` | `[data-testid="02_S7-01_22"]` |
| 左侧作品表格 | `02_S7-01_23` | `[data-testid="02_S7-01_23"]` |
| 右侧已选列表 | `02_S7-01_24` | `[data-testid="02_S7-01_24"]` |
| 单个删除图标 | `02_S7-01_25` | `[data-testid="02_S7-01_25"]` |
| 全部清空图标 | `02_S7-01_26` | `[data-testid="02_S7-01_26"]` |
| 确定按钮 | `02_S7-01_27` | `[data-testid="02_S7-01_27"]` |
| 取消按钮 | `02_S7-01_28` | `[data-testid="02_S7-01_28"]` |

---

### 2.5 Quest 7-3: 选择解约分销商弹窗 (TeamDialog.vue)

**文件路径**：`src/views/content-assets/content-termination/components/TeamDialog.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 弹窗容器 | `02_S7-01_30` | `[data-testid="02_S7-01_30"]` |
| 分销商名称搜索框 | `02_S7-01_31` | `[data-testid="02_S7-01_31"]` |
| 查询按钮 | `02_S7-01_32` | `[data-testid="02_S7-01_32"]` |
| 重置按钮 | `02_S7-01_33` | `[data-testid="02_S7-01_33"]` |
| 分销商表格 | `02_S7-01_34` | `[data-testid="02_S7-01_34"]` |
| 取消按钮 | `02_S7-01_35` | `[data-testid="02_S7-01_35"]` |
| 确定按钮 | `02_S7-01_36` | `[data-testid="02_S7-01_36"]` |

---

### 2.6 Quest 8: 解约单详情 (TerminationDetails.vue)

**文件路径**：`src/views/content-assets/content-termination/components/TerminationDetails.vue`

| 元素描述 | data-testid | 选择器示例 |
| -------- | ----------- | ---------- |
| 抽屉容器 | `02_S8-01_01` | `[data-testid="02_S8-01_01"]` |
| 解约信息区块 | `02_S8-01_02` | `[data-testid="02_S8-01_02"]` |
| 作品信息表格 | `02_S8-01_03` | `[data-testid="02_S8-01_03"]` |

---

## 三、测试用例对照

| Quest | 场景描述 | 涉及文件 | testid 前缀 |
| ----- | -------- | -------- | ----------- |
| Quest 1 | 列表展示与筛选 | list.vue | `01_S1-01_xx` |
| Quest 2 | Tab切换与排序 | list.vue | `01_S2-01_xx` |
| Quest 3 | 按作品创建 | CreateTaskDrawer.vue, SelectWorksModal.vue, SelectDialog.vue | `01_S3-01_xx` |
| Quest 4 | 按视频ID创建 | CreateTaskDrawer.vue, SelectDialog.vue | `01_S4-01_xx` |
| Quest 5 | 详情页 | DetailDrawer.vue, WorkItemPanel.vue | `01_S5-01_xx` |
| Quest 6 | 解约单列表 | List.vue | `02_S6-01_xx` |
| Quest 7 | 创建解约单 | Add.vue, AddWork.vue, AddWorkTable.vue, TeamDialog.vue | `02_S7-01_xx` |
| Quest 8 | 解约单详情 | TerminationDetails.vue | `02_S8-01_xx` |

---

## 四、状态说明

- ✅ 已添加：data-testid 已添加到组件
- ⏳ 待添加：等待开发添加 data-testid
- 🔴 条件显示：仅在特定条件下显示的元素

---

*最后更新：2026-03-31*
