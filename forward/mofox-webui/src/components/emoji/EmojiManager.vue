<template>
  <div class="emoji-manager">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <!-- 搜索框 -->
        <div class="search-box">
          <span class="material-symbols-rounded">search</span>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索表情包描述..."
            @input="handleSearch"
          />
        </div>

        <!-- 刷新按钮 -->
        <button class="icon-button" title="刷新" @click="handleRefresh">
          <span class="material-symbols-rounded">refresh</span>
        </button>
      </div>

      <div class="toolbar-right">
        <!-- 批量操作 -->
        <button
          v-if="hasSelection"
          class="batch-button delete"
          @click="handleBatchDelete"
        >
          <span class="material-symbols-rounded">delete</span>
          删除选中 ({{ selectionCount }})
        </button>

        <!-- 上传按钮 -->
        <button class="upload-button" @click="showUploadDialog = true">
          <span class="material-symbols-rounded">upload</span>
          上传表情包
        </button>
      </div>
    </div>

    <!-- 统计信息卡片 -->
    <div v-if="stats" class="stats-card">
      <div class="stat-item">
        <span class="material-symbols-rounded icon">inventory_2</span>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_count }}</div>
          <div class="stat-label">总表情包数</div>
        </div>
      </div>

      <div class="stat-item">
        <span class="material-symbols-rounded icon">check_circle</span>
        <div class="stat-content">
          <div class="stat-value">{{ stats.registered_count }}</div>
          <div class="stat-label">已注册</div>
        </div>
      </div>

      <div class="stat-item">
        <span class="material-symbols-rounded icon">block</span>
        <div class="stat-content">
          <div class="stat-value">{{ stats.banned_count }}</div>
          <div class="stat-label">已禁用</div>
        </div>
      </div>

      <div class="stat-item">
        <span class="material-symbols-rounded icon">trending_up</span>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_usage }}</div>
          <div class="stat-label">总使用次数</div>
        </div>
      </div>
    </div>

    <!-- 表情包网格 -->
    <div class="emoji-grid-container">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>

      <!-- 空状态 -->
      <div v-else-if="items.length === 0" class="empty-state">
        <span class="material-symbols-rounded">image_not_supported</span>
        <p>暂无表情包</p>
      </div>

      <!-- 表情包网格 -->
      <div v-else class="grid">
        <EmojiCard
          v-for="item in items"
          :key="item.hash"
          :emoji="item"
          :selected="selectedItems.has(item.hash)"
          @select="toggleSelection(item.hash)"
          @view-detail="handleViewDetail(item.hash)"
          @delete="handleDelete(item.hash)"
        />
      </div>
    </div>

    <!-- 分页器 -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        class="page-button"
        :disabled="page === 1"
        @click="handlePageChange(page - 1)"
      >
        <span class="material-symbols-rounded">chevron_left</span>
      </button>

      <div class="page-numbers">
        <button
          v-for="p in visiblePages"
          :key="p"
          :class="['page-number', { active: p === page }]"
          @click="handlePageChange(p)"
        >
          {{ p }}
        </button>
      </div>

      <button
        class="page-button"
        :disabled="page === totalPages"
        @click="handlePageChange(page + 1)"
      >
        <span class="material-symbols-rounded">chevron_right</span>
      </button>

      <div class="page-info">
        第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条
      </div>
    </div>

    <!-- 详情对话框 -->
    <EmojiDetailDialog
      v-model="showDetailDialog"
      :emoji-hash="selectedEmojiHash"
      @updated="handleRefresh"
      @deleted="handleRefresh"
    />

    <!-- 上传对话框 -->
    <EmojiUploadDialog
      v-model="showUploadDialog"
      @uploaded="handleUploaded"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useEmojiStore } from '@/stores/emojiStore'
import { storeToRefs } from 'pinia'
import EmojiCard from './EmojiCard.vue'
import EmojiDetailDialog from './EmojiDetailDialog.vue'
import EmojiUploadDialog from './EmojiUploadDialog.vue'

const emojiStore = useEmojiStore()
const {
  items,
  total,
  page,
  totalPages,
  loading,
  selectedItems,
  hasSelection,
  selectionCount
} = storeToRefs(emojiStore)

const searchQuery = ref('')
const stats = ref<any>({
  total_count: 0,
  registered_count: 0,
  banned_count: 0,
  avg_usage: 0
})
const showDetailDialog = ref(false)
const showUploadDialog = ref(false)
const selectedEmojiHash = ref('')

// 计算可见的页码
const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 7
  let start = Math.max(1, page.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

// 防抖搜索
let searchTimeout: ReturnType<typeof setTimeout> | null = null
const handleSearch = () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    emojiStore.setSearchQuery(searchQuery.value)
    emojiStore.fetchEmojiList()
  }, 300)
}

// 刷新
const handleRefresh = async () => {
  await emojiStore.fetchEmojiList()
  const newStats = await emojiStore.getStats()
  if (newStats) {
    stats.value = newStats
  }
}

// 切换选中
const toggleSelection = (hash: string) => {
  emojiStore.toggleSelection(hash)
}

// 查看详情
const handleViewDetail = (hash: string) => {
  selectedEmojiHash.value = hash
  showDetailDialog.value = true
}

// 删除单个
const handleDelete = async (hash: string) => {
  if (!confirm('确定要删除这个表情包吗？')) return

  try {
    await emojiStore.deleteEmoji(hash)
  } catch (error) {
    alert('删除失败')
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!confirm(`确定要删除选中的 ${selectionCount.value} 个表情包吗？`)) return

  try {
    await emojiStore.batchDelete(Array.from(selectedItems.value))
    emojiStore.clearSelection()
  } catch (error) {
    alert('批量删除失败')
  }
}

// 页码变化
const handlePageChange = (newPage: number) => {
  emojiStore.setPage(newPage)
  emojiStore.fetchEmojiList()
}

// 上传完成
const handleUploaded = async () => {
  await handleRefresh()
  showUploadDialog.value = false
}

// 初始化
onMounted(async () => {
  await emojiStore.fetchEmojiList()
  const newStats = await emojiStore.getStats()
  if (newStats) {
    stats.value = newStats
  }
})
</script>

<style scoped>
.emoji-manager {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
}

/* 工具栏 */
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  box-shadow: var(--md-sys-elevation-1);
  margin-bottom: 16px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-left {
  flex: 1;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  flex: 1;
  max-width: 400px;
}

.search-box .material-symbols-rounded {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 20px;
}

.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  outline: none;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.icon-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--md-sys-color-surface-container);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--md-sys-color-on-surface-variant);
}

.icon-button:hover {
  background: var(--md-sys-color-surface-container-high);
}

.upload-button,
.batch-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-button {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.upload-button:hover {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.batch-button.delete {
  background: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
}

.batch-button.delete:hover {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

/* 统计卡片 */
.stats-card {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  box-shadow: var(--md-sys-elevation-1);
}

.stat-item .icon {
  font-size: 40px;
  color: var(--md-sys-color-primary);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 4px;
}

/* 表情包网格 */
.emoji-grid-container {
  min-height: 400px;
  margin-bottom: 24px;
}

.loading-container,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--md-sys-color-on-surface-variant);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid var(--md-sys-color-surface-container-highest);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state .material-symbols-rounded {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
  padding: 8px;
}

/* 分页器 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  box-shadow: var(--md-sys-elevation-1);
}

.page-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--md-sys-color-surface-container);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.2s;
}

.page-button:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-button:not(:disabled):hover {
  background: var(--md-sys-color-primary-container);
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-number {
  min-width: 40px;
  height: 40px;
  padding: 0 12px;
  border: none;
  background: var(--md-sys-color-surface-container);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.page-number.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  font-weight: 500;
}

.page-number:not(.active):hover {
  background: var(--md-sys-color-primary-container);
}

.page-info {
  margin-left: 16px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
  }

  .toolbar-left,
  .toolbar-right {
    width: 100%;
  }

  .search-box {
    max-width: none;
  }

  .stats-card {
    grid-template-columns: repeat(2, 1fr);
  }

  .grid {
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 12px;
  }

  .page-info {
    margin-left: 8px;
    font-size: 12px;
  }
}
</style>
