# MoFox WebUI 开发指南

> Vue 3 + TypeScript + Vite 管理面板 | Material Design 3 规范

---

## 🛠 技术栈

**核心**: Vue 3.5+ (Composition API) | TypeScript | Vite 6 | Vue Router 4 | Pinia  
**UI**: Material Design 3 | Material Symbols | ECharts | Monaco Editor

---

## 📁 核心目录结构

```
src/
├── api/          # API 接口（index.ts 统一入口 + mock.ts）
├── components/   # 可复用组件（ConfirmDialog、M3Select、Sidebar 等）
├── views/        # 页面视图
├── router/       # 路由配置
├── stores/       # Pinia 状态管理
├── utils/        # 工具函数（dialog.ts 对话框工具）
└── styles/       # 全局样式（m3-theme.css 设计变量）
```

---

## 🎨 核心可复用组件

### 1. 对话框系统 (`utils/dialog.ts`)

```typescript
import { showConfirm, showSuccess, showError } from '@/utils/dialog'

// 确认对话框
const confirmed = await showConfirm({
  title: '删除确认',
  message: '确定要删除吗？',
  type: 'danger'  // 'info' | 'success' | 'warning' | 'danger'
})

// 快捷提示
showSuccess('操作成功！')
showError('操作失败')
```

### 2. M3 选择器 (`components/M3Select.vue`)

```vue
<M3Select v-model="selected" :options="options" />
```

### 3. 侧边栏 (`components/Sidebar.vue`)

支持嵌套菜单、路由高亮、自定义动作。菜单项结构：

```typescript
interface MenuItem {
  name: string          // 显示名称
  path: string          // 路由路径
  icon: string          // Material Symbol 图标
  key?: string          // 分组标识（有子菜单时）
  children?: MenuItem[] // 子菜单
}
```

---

## 🎨 Material Design 3 规范

### 设计变量 (`styles/m3-theme.css`)

**颜色系统**：
```css
/* 主色调 */
--md-sys-color-primary / --md-sys-color-on-primary
--md-sys-color-primary-container / --md-sys-color-on-primary-container

/* 次要 / 第三 / 错误色 */
--md-sys-color-secondary / --md-sys-color-tertiary / --md-sys-color-error

/* 表面色 */
--md-sys-color-surface / --md-sys-color-surface-container
--md-sys-color-on-surface / --md-sys-color-on-surface-variant

/* 语义化别名 */
--bg-primary / --bg-secondary / --bg-tertiary
--text-primary / --text-secondary
--border-primary / --border-secondary
```

**形状系统**：
```css
--md-sys-shape-corner-medium: 12px        /* 按钮 */
--md-sys-shape-corner-large: 16px         /* 卡片 */
--md-sys-shape-corner-extra-large: 28px   /* 对话框 */
```

**图标**：使用 Material Symbols Rounded
```html
<span class="material-symbols-rounded">settings</span>
```

**主题切换**：通过 `[data-theme="dark"]` 自动切换暗色模式

---

## 📝 开发规范

### TypeScript

```typescript
// ✅ 使用 interface 定义对象，type 定义联合类型
interface User { id: number; name: string }
type Status = 'idle' | 'loading' | 'success' | 'error'

// ✅ Props 定义
const props = withDefaults(defineProps<{ title: string; count?: number }>(), {
  count: 0
})

// ❌ 避免 any（除非必要）
```

### Vue 组件结构

```vue
<template><!-- 模板 --></template>

<script setup lang="ts">
// 1. 导入
import { ref, computed, onMounted } from 'vue'

// 2. 类型 + Props/Emits
interface Props { title: string }
const props = defineProps<Props>()
const emit = defineEmits<{ update: [value: string] }>()

// 3. 响应式数据
const data = ref<Item[]>([])

// 4. 计算属性 + 方法
const count = computed(() => data.value.length)
const handleClick = () => emit('update', 'value')

// 5. 生命周期
onMounted(() => {})
</script>

<style scoped>/* 样式 */</style>
```

### 样式规范

```css
/* ✅ 使用 CSS 变量 */
.button {
  background: var(--md-sys-color-primary);
  border-radius: var(--md-sys-shape-corner-medium);
}

/* ❌ 避免硬编码 */
.button { background: #6750A4; }
```

### 命名规范

- **文件**: 组件 PascalCase (`UserProfile.vue`)，工具 camelCase (`dialog.ts`)
- **变量/函数**: camelCase (`userName`, `handleClick`)
- **常量**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **类型**: PascalCase (`User`, `ApiResponse`)

---

## 🚀 新功能开发流程（必读）

### 完整清单

#### 1️⃣ 需求分析
- [ ] 明确功能需求、页面结构、数据流
- [ ] 确认是否需要新 API

#### 2️⃣ 后端 API（如需要）
- [ ] 实现并测试 API
- [ ] 准备 Mock 数据

#### 3️⃣ **路由配置** ⭐
```typescript
// src/router/index.ts
{
  path: 'new-feature',
  name: 'NewFeature',
  component: () => import('@/views/NewFeatureView.vue'),
  meta: { requiresAuth: true }
}
```

#### 4️⃣ **侧边栏导航** ⭐
```typescript
// src/components/Sidebar.vue - menuItems 数组
{ name: '新功能', path: '/dashboard/new-feature', icon: 'star' }

// 或作为子菜单
{
  name: '功能分组',
  icon: 'folder',
  key: 'group',
  children: [
    { name: '新功能', path: '/dashboard/new-feature', icon: 'star' }
  ]
}
```

#### 5️⃣ API 封装
```typescript
// src/api/newFeature.ts
export interface NewFeatureResponse {
  success: boolean
  data?: FeatureData[]
  error?: string
}

export async function getFeature(): Promise<NewFeatureResponse> {
  return apiRequest('/feature', 'GET')
}

// src/api/mock.ts - 添加 Mock 数据
'/feature': { success: true, data: [...] }
```

#### 6️⃣ 状态管理（可选）
```typescript
// src/stores/feature.ts
export const useFeatureStore = defineStore('feature', () => {
  const items = ref<Item[]>([])
  const fetchItems = async () => { /* ... */ }
  return { items, fetchItems }
})
```

#### 7️⃣ 页面开发
```vue
<!-- src/views/NewFeatureView.vue -->
<template>
  <div v-if="isLoading">加载中...</div>
  <div v-else-if="error">错误：{{ error }}</div>
  <div v-else>
    <!-- 内容 -->
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getFeature } from '@/api/newFeature'
import { showSuccess, showError } from '@/utils/dialog'

const isLoading = ref(false)
const error = ref<string | null>(null)
const items = ref([])

const loadData = async () => {
  isLoading.value = true
  try {
    const result = await getFeature()
    if (result.success && result.data) {
      items.value = result.data
    } else {
      error.value = result.error || '加载失败'
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)
</script>
```

#### 8️⃣ 测试
- [ ] 功能测试 + 异常处理
- [ ] Demo 模式（Mock 数据）
- [ ] 亮/暗色主题测试

---

## 🔌 API 规范

### 统一响应格式

```typescript
interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}
```

### 错误处理

```typescript
try {
  const result = await someApi()
  if (result.success && result.data) {
    // 成功处理
  } else {
    showError(result.error || '操作失败')
  }
} catch (error) {
  showError('网络错误: ' + error.message)
}
```

---

## 📦 状态管理 (Pinia)

### Store 模板

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useExampleStore = defineStore('example', () => {
  // State
  const items = ref<Item[]>([])
  
  // Getters
  const count = computed(() => items.value.length)
  
  // Actions
  const fetch = async () => {
    const result = await getItems()
    if (result.success) items.value = result.data
  }
  
  return { items, count, fetch }
})
```

### 使用

```typescript
const store = useExampleStore()
store.fetch()  // 调用 action
console.log(store.count)  // 访问 getter
```

---

## 💡 最佳实践

### 1. 异步处理

```typescript
// ✅ 使用 async/await + 加载状态
const isLoading = ref(false)
const loadData = async () => {
  isLoading.value = true
  try {
    await fetchData()
  } finally {
    isLoading.value = false
  }
}
```

### 2. 组件拆分

单一职责 | 可复用 | 不超过 300 行

### 3. 性能优化

```typescript
// computed 缓存
const filtered = computed(() => items.value.filter(i => i.active))

// v-for 必须加 key
<div v-for="item in items" :key="item.id">

// 大组件懒加载
const Heavy = () => import('@/components/Heavy.vue')

// 防抖
import { debounce } from 'lodash-es'
const search = debounce((q) => {}, 300)
```

### 4. 错误边界

```vue
<div v-if="error">
  <p>{{ error }}</p>
  <button @click="retry">重试</button>
</div>
<div v-else-if="isLoading">加载中...</div>
<div v-else><!-- 内容 --></div>
```

### 5. 代码复用

优先级：**Composables** > **组件** > **工具函数**

```typescript
// composables/useDataFetcher.ts
export function useDataFetcher<T>(fn: () => Promise<T>) {
  const data = ref<T | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  const fetch = async () => {
    loading.value = true
    try {
      data.value = await fn()
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }
  
  return { data, loading, error, fetch }
}
```

---

## 🔍 常见问题

**Q: 如何添加新页面？**  
A: 1) 路由配置 2) 侧边栏菜单 3) 创建页面组件 4) API 封装

**Q: 对话框怎么用？**  
A: `import { showConfirm } from '@/utils/dialog'`

**Q: 全局状态？**  
A: 在 `stores/` 创建 Pinia Store

**Q: 样式变量？**  
A: `styles/m3-theme.css`，使用 `var(--md-sys-color-primary)`

**Q: Mock 数据？**  
A: `api/mock.ts`，Demo 模式自动使用

---

## 📚 参考

[Vue 3](https://vuejs.org/) | [Pinia](https://pinia.vuejs.org/) | [Material Design 3](https://m3.material.io/) | [TypeScript](https://www.typescriptlang.org/)

---

**Happy Coding! 🎉**
