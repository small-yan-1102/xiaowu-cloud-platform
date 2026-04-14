# 前端组件结构模板

本文件定义了使用 Mock 数据开发前端界面时的标准组件结构和文件组织规范。

## 1. 目录结构模板

```
src/views/{模块名}/
├── index.vue                    # 主页面组件
├── service.js                   # 接口层(Mock + 真实接口)
├── mock/
│   └── data.js                 # Mock 数据
└── components/
    ├── {模块名}Search.vue       # 搜索表单组件
    ├── {模块名}Table.vue        # 数据表格组件
    └── {模块名}Form.vue         # 表单组件(新增/编辑)
```

## 2. service.js 模板

```javascript
// src/views/{模块名}/service.js

// ========== Mock 数据（联调时删除）==========
const MOCK_XXX_LIST = [
  // ≥ 20 条数据用于测试分页
];

// ========== Mock 开关（联调时改为 false）==========
const USE_MOCK = true;

// ========== 模拟延迟 ==========
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// ========== API 接口定义 ==========

/**
 * 获取列表
 */
export async function getXxxList(params) {
  if (USE_MOCK) {
    await delay(500);
    return {
      code: 200,
      data: {
        list: MOCK_XXX_LIST,
        total: MOCK_XXX_LIST.length,
        page: params.page,
        size: params.size
      }
    };
  }
  
  // 真实接口 - 联调时取消注释
  // return request.get('/api/xxx', { params });
}

/**
 * 创建
 */
export async function createXxx(data) {
  if (USE_MOCK) {
    await delay(300);
    return { code: 200, message: '创建成功', data: { id: Date.now(), ...data } };
  }
  
  // return request.post('/api/xxx', data);
}

/**
 * 更新
 */
export async function updateXxx(id, data) {
  if (USE_MOCK) {
    await delay(300);
    return { code: 200, message: '更新成功' };
  }
  
  // return request.put(`/api/xxx/${id}`, data);
}

/**
 * 删除
 */
export async function deleteXxx(id) {
  if (USE_MOCK) {
    await delay(200);
    return { code: 200, message: '删除成功' };
  }
  
  // return request.delete(`/api/xxx/${id}`);
}
```

## 3. 页面组件模板

```vue
<!-- src/views/{模块名}/index.vue -->
<template>
  <div class="{模块名}-container">
    <!-- 搜索表单 -->
    <{模块名}Search @search="handleSearch" @reset="handleReset" />
    
    <!-- 操作按钮 -->
    <div class="action-bar">
      <el-button type="primary" @click="handleAdd">新增</el-button>
    </div>
    
    <!-- 数据表格 -->
    <{模块名}Table 
      :data="tableData" 
      :loading="loading"
      @edit="handleEdit"
      @delete="handleDelete"
    />
    
    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      @current-change="fetchData"
      @size-change="fetchData"
    />
    
    <!-- 新增/编辑弹窗 -->
    <{模块名}Form 
      v-model="formVisible" 
      :form-data="currentForm"
      @submit="handleSubmit"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getXxxList, deleteXxx } from './service.js'
import {Module}Search from './components/{Module}Search.vue'
import {Module}Table from './components/{Module}Table.vue'
import {Module}Form from './components/{Module}Form.vue'

// 状态
const tableData = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const formVisible = ref(false)
const currentForm = ref(null)

// 方法
const fetchData = async () => {
  loading.value = true
  try {
    const res = await getXxxList({
      page: currentPage.value,
      size: pageSize.value
    })
    tableData.value = res.data.list
    total.value = res.data.total
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSearch = (params) => {
  currentPage.value = 1
  fetchData()
}

const handleReset = () => {
  currentPage.value = 1
  fetchData()
}

const handleAdd = () => {
  currentForm.value = null
  formVisible.value = true
}

const handleEdit = (row) => {
  currentForm.value = row
  formVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await deleteXxx(row.id)
    fetchData()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleSubmit = () => {
  formVisible.value = false
  fetchData()
}

// 生命周期
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.{模块名}-container {
  padding: 20px;
}

.action-bar {
  margin-bottom: 16px;
}
</style>
```

## 4. Mock 数据模板

```javascript
// src/views/{模块名}/mock/data.js

export const MOCK_XXX_LIST = [
  {
    id: 1,
    name: '示例数据1',  // ⚠️ 字段名必须与后端接口一致
    status: 1,
    createdAt: '2024-01-01 10:00:00',
    // ... 更多字段
  },
  // ... ≥ 20 条数据
]
```

## 5. 命名规范速查

| 类型 | 规范 | 示例 |
|------|------|------|
| Mock 数据 | MOCK_ + 大写下划线 | `MOCK_USER_LIST` |
| 接口函数 | 动词 + 驼峰 | `getUserList`, `createOrder` |
| 组件变量 | 驼峰 | `userList`, `loading` |
| 组件名 | PascalCase | `UserTable`, `OrderForm` |
| 文件名 | kebab-case | `user-list.vue` |
| CSS 类名 | kebab-case | `.user-container` |

## 6. 联调检查清单

联调时需要修改的内容:

- [ ] 修改 `const USE_MOCK = false`
- [ ] 取消注释所有真实接口代码
- [ ] 删除 `const MOCK_XXX_LIST = [...]`
- [ ] 删除 `const delay = (ms) => ...`
- [ ] 删除所有 `if (USE_MOCK)` 分支
- [ ] 删除 `mock/` 目录(可选)
