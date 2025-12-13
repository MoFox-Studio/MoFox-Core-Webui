<template>
  <div class="expression-view">
    <!-- 顶部操作栏 -->
    <div class="top-bar">
      <div class="title-section">
        <h1>表达方式管理</h1>
        <span class="subtitle">管理Bot的语言风格和表达习惯</span>
      </div>
      <div class="action-buttons">
        <button class="action-btn statistics-btn" @click="showStatisticsDialog = true">
          <Icon icon="mdi:chart-box" />
          统计信息
        </button>
        <button class="action-btn create-btn" @click="openCreateDialog">
          <Icon icon="mdi:plus-circle" />
          新建表达
        </button>
      </div>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="search-bar">
      <div class="search-input-wrapper">
        <Icon class="search-icon" icon="mdi:magnify" />
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索情境或表达风格..."
          @keyup.enter="handleSearch"
        />
        <button v-if="searchQuery" class="clear-button" @click="clearSearch">
          <Icon icon="mdi:close" />
        </button>
      </div>
      <button class="search-button" @click="handleSearch">
        <Icon icon="mdi:magnify" />
        搜索
      </button>
    </div>

    <!-- 筛选器 -->
    <div class="filters">
      <div class="filter-group">
        <label>类型：</label>
        <select v-model="filterType" @change="loadExpressionList">
          <option value="">全部</option>
          <option value="style">语言风格</option>
          <option value="grammar">句法特点</option>
        </select>
      </div>
      <div class="filter-group">
        <label>排序：</label>
        <select v-model="sortBy" @change="loadExpressionList">
          <option value="last_active_time">最后使用</option>
          <option value="count">使用次数</option>
          <option value="create_date">创建时间</option>
        </select>
      </div>
      <div class="filter-group">
        <label>顺序：</label>
        <select v-model="sortOrder" @change="loadExpressionList">
          <option value="desc">降序</option>
          <option value="asc">升序</option>
        </select>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <Icon class="error-icon" icon="mdi:alert-circle" />
      <h3>加载失败</h3>
      <p>{{ error }}</p>
      <button class="retry-button" @click="loadExpressionList">
        <Icon icon="mdi:refresh" />
        重试
      </button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!expressionList || expressionList.length === 0" class="empty-state">
      <Icon class="empty-icon" icon="mdi:folder-open-outline" />
      <h3>暂无表达方式</h3>
      <p>{{ searchQuery ? '没有找到匹配的表达方式' : '还没有创建任何表达方式' }}</p>
    </div>

    <!-- 表达方式网格 -->
    <div v-else class="expression-grid">
      <div
        v-for="expr in expressionList"
        :key="expr.id"
        class="expression-card"
        @click="viewExpressionDetail(expr.id)"
      >
        <div class="card-header">
          <div class="type-badge" :class="`type-${expr.type}`">
            <Icon :icon="expr.type === 'style' ? 'mdi:comment-text' : 'mdi:text-box'" />
            {{ expr.type === 'style' ? '风格' : '句法' }}
          </div>
          <div class="count-badge">
            <Icon icon="mdi:fire" />
            {{ expr.count.toFixed(1) }}
          </div>
        </div>
        <div class="card-body">
          <div class="situation-section">
            <label>情境：</label>
            <p class="situation-text">{{ expr.situation }}</p>
          </div>
          <div class="style-section">
            <label>表达：</label>
            <p class="style-text">{{ expr.style }}</p>
          </div>
        </div>
        <div class="card-footer">
          <span class="chat-name" :title="`${expr.chat_id_display || expr.chat_id}\n哈希: ${expr.chat_id}`">
            <Icon icon="mdi:chat" />
            {{ expr.chat_id_display || expr.chat_name || expr.chat_id.substring(0, 8) + '...' }}
          </span>
          <span class="last-use">
            <Icon icon="mdi:clock-outline" />
            {{ formatRelativeTime(expr.last_active_time) }}
          </span>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        class="page-button"
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        <Icon icon="mdi:chevron-left" />
        上一页
      </button>
      <div class="page-numbers">
        <button
          v-for="page in visiblePages"
          :key="page"
          class="page-number"
          :class="{ active: page === currentPage }"
          @click="changePage(page)"
        >
          {{ page }}
        </button>
      </div>
      <button
        class="page-button"
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        下一页
        <Icon icon="mdi:chevron-right" />
      </button>
    </div>

    <!-- 详情对话框 -->
    <Teleport to="body">
      <Transition name="dialog-fade">
        <div v-if="showDetailDialog" class="dialog-overlay" @click.self="showDetailDialog = false">
          <div class="dialog detail-dialog">
            <div class="dialog-header">
              <h3>表达方式详情</h3>
              <button class="close-button" @click="showDetailDialog = false">
                <Icon icon="mdi:close" />
              </button>
            </div>
            <div v-if="expressionDetail" class="dialog-body">
              <div class="detail-section">
                <div class="type-badge-large" :class="`type-${expressionDetail.type}`">
                  <Icon :icon="expressionDetail.type === 'style' ? 'mdi:comment-text' : 'mdi:text-box'" />
                  {{ expressionDetail.type === 'style' ? '语言风格' : '句法特点' }}
                </div>
                
                <div class="detail-item">
                  <label>情境描述</label>
                  <div class="detail-value">{{ expressionDetail.situation }}</div>
                </div>

                <div class="detail-item">
                  <label>表达风格</label>
                  <div class="detail-value">{{ expressionDetail.style }}</div>
                </div>

                <div class="detail-item">
                  <label>权重</label>
                  <div class="weight-display">
                    <div class="weight-bar">
                      <div class="weight-fill" :style="{ width: `${(expressionDetail.count / 5) * 100}%` }"></div>
                    </div>
                    <span>{{ expressionDetail.count.toFixed(2)}} / 5.0</span>
                  </div>
                </div>

                <div class="detail-item">
                  <label>所属聊天流</label>
                  <div class="detail-value" :title="`平台: ${expressionDetail.chat_platform}\nID: ${expressionDetail.chat_raw_id}\n类型: ${expressionDetail.chat_type}\n\n完整ID: ${expressionDetail.chat_id_display}\n哈希: ${expressionDetail.chat_id}`">
                    <Icon icon="mdi:chat" />
                    {{ expressionDetail.chat_name }} ({{ expressionDetail.chat_id_display }})
                  </div>
                </div>

                <div class="stats-grid">
                  <div class="stat-card">
                    <Icon icon="mdi:calendar-plus" />
                    <span class="stat-label">创建于</span>
                    <span class="stat-value">{{ formatDate(expressionDetail.create_date) }}</span>
                  </div>
                  <div class="stat-card">
                    <Icon icon="mdi:clock-check" />
                    <span class="stat-label">最后使用</span>
                    <span class="stat-value">{{ formatDate(expressionDetail.last_active_time) }}</span>
                  </div>
                  <div class="stat-card">
                    <Icon icon="mdi:timer-sand" />
                    <span class="stat-label">已创建天数</span>
                    <span class="stat-value">{{ expressionDetail.usage_stats.days_since_create }} 天</span>
                  </div>
                  <div class="stat-card">
                    <Icon icon="mdi:chart-line" />
                    <span class="stat-label">使用频率</span>
                    <span class="stat-value">{{ expressionDetail.usage_stats.usage_frequency.toFixed(3) }} /天</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="dialog-footer">
              <button class="cancel-button" @click="showDetailDialog = false">关闭</button>
              <button class="action-button edit-btn" @click="editExpression(expressionDetail!)">
                <Icon icon="mdi:pencil" />
                编辑
              </button>
              <button class="action-button delete-btn" @click="deleteExpressionConfirm(expressionDetail!.id)">
                <Icon icon="mdi:delete" />
                删除
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 创建/编辑对话框 -->
    <Teleport to="body">
      <Transition name="dialog-fade">
        <div v-if="showEditDialog" class="dialog-overlay" @click.self="showEditDialog = false">
          <div class="dialog edit-dialog">
            <div class="dialog-header">
              <h3>{{ editMode === 'create' ? '创建表达方式' : '编辑表达方式' }}</h3>
              <button class="close-button" @click="showEditDialog = false">
                <Icon icon="mdi:close" />
              </button>
            </div>
            <div class="dialog-body">
              <div class="form-group">
                <label>类型</label>
                <select v-model="editForm.type">
                  <option value="style">语言风格</option>
                  <option value="grammar">句法特点</option>
                </select>
              </div>

              <div class="form-group">
                <label>情境描述</label>
                <input
                  v-model="editForm.situation"
                  type="text"
                  class="form-input"
                  placeholder="如：对某件事表示十分惊叹，有些意外"
                  maxlength="200"
                />
              </div>

              <div class="form-group">
                <label>表达风格</label>
                <input
                  v-model="editForm.style"
                  type="text"
                  class="form-input"
                  placeholder="如：我嘞个xxxx"
                  maxlength="200"
                />
              </div>

              <div class="form-group">
                <label>权重 ({{ editForm.count.toFixed(1) }})</label>
                <input
                  v-model.number="editForm.count"
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  class="form-range"
                />
              </div>

              <div v-if="editMode === 'create'" class="form-group">
                <label>聊天流ID</label>
                <input
                  v-model="editForm.chat_id"
                  type="text"
                  class="form-input"
                  placeholder="格式: platform:id:type (如 QQ:12345:group) 或哈希值"
                />
                <small style="color: var(--text-tertiary); font-size: 12px; margin-top: 4px; display: block;">
                  支持格式：<br>
                  • platform:raw_id:type (如: QQ:12345:group 或 QQ:67890:private)<br>
                  • 哈希值 (如: abc123def456...)
                </small>
              </div>
            </div>
            <div class="dialog-footer">
              <button class="cancel-button" @click="showEditDialog = false">取消</button>
              <button class="confirm-button" :disabled="!canSubmitEdit" @click="submitEdit">
                {{ editMode === 'create' ? '创建' : '保存' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 统计信息对话框 -->
    <Teleport to="body">
      <Transition name="dialog-fade">
        <div v-if="showStatisticsDialog" class="dialog-overlay" @click.self="showStatisticsDialog = false">
          <div class="dialog statistics-dialog">
            <div class="dialog-header">
              <h3>统计信息</h3>
              <button class="close-button" @click="showStatisticsDialog = false">
                <Icon icon="mdi:close" />
              </button>
            </div>
            <div v-if="statistics" class="dialog-body">
              <div class="stats-overview">
                <div class="stat-box">
                  <Icon icon="mdi:database" />
                  <div class="stat-content">
                    <span class="stat-number">{{ statistics.total_count }}</span>
                    <span class="stat-label">总数</span>
                  </div>
                </div>
                <div class="stat-box">
                  <Icon icon="mdi:comment-text" />
                  <div class="stat-content">
                    <span class="stat-number">{{ statistics.style_count }}</span>
                    <span class="stat-label">语言风格</span>
                  </div>
                </div>
                <div class="stat-box">
                  <Icon icon="mdi:text-box" />
                  <div class="stat-content">
                    <span class="stat-number">{{ statistics.grammar_count }}</span>
                    <span class="stat-label">句法特点</span>
                  </div>
                </div>
              </div>

              <div class="top-used-section">
                <h4>最常用表达方式 Top 10</h4>
                <div class="top-list">
                  <div v-for="(expr, idx) in statistics.top_used" :key="expr.id" class="top-item">
                    <span class="rank">{{ idx + 1 }}</span>
                    <div class="top-content">
                      <div class="top-situation">{{ expr.situation }}</div>
                      <div class="top-style">{{ expr.style }}</div>
                    </div>
                    <span class="top-count">{{ expr.count.toFixed(1) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div class="dialog-footer">
              <button class="cancel-button" @click="showStatisticsDialog = false">关闭</button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'
import {
  getExpressionList,
  getExpressionDetail,
  createExpression,
  updateExpression,
  deleteExpression,
  getStatistics,
  type Expression,
  type ExpressionDetail,
  type ExpressionStatistics,
  type ExpressionType,
  type SortByField
} from '@/api/expression'
import { showSuccess, showError, showConfirm } from '@/utils/dialog'

// 列表相关状态
const expressionList = ref<Expression[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = ref(0)
const totalCount = ref(0)
const loading = ref(false)
const error = ref('')

// 搜索和筛选
const searchQuery = ref('')
const filterType = ref<ExpressionType | ''>('')
const sortBy = ref<SortByField>('last_active_time')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 对话框状态
const showDetailDialog = ref(false)
const showEditDialog = ref(false)
const showStatisticsDialog = ref(false)

// 详情和编辑
const expressionDetail = ref<ExpressionDetail | null>(null)
const editMode = ref<'create' | 'edit'>('create')
const editForm = reactive({
  id: 0,
  situation: '',
  style: '',
  count: 1.0,
  type: 'style' as ExpressionType,
  chat_id: ''
})

// 统计信息
const statistics = ref<ExpressionStatistics | null>(null)

// 监听统计对话框打开
watch(showStatisticsDialog, (newVal) => {
  if (newVal && !statistics.value) {
    loadStatistics()
  }
})

// 监听筛选条件变化，自动刷新列表
watch([filterType, sortBy, sortOrder], () => {
  currentPage.value = 1 // 重置到第一页
  loadExpressionList()
})

// 加载表达方式列表
const loadExpressionList = async () => {
  loading.value = true
  error.value = ''

  try {
    const result = await getExpressionList(
      currentPage.value,
      pageSize.value,
      undefined, // chatId 参数，目前不需要按聊天筛选
      filterType.value as ExpressionType | undefined,
      sortBy.value,
      sortOrder.value
    )

    if (result.success && result.data) {
      expressionList.value = result.data.expressions
      totalPages.value = result.data.total_pages
      totalCount.value = result.data.total
    } else {
      error.value = result.error || '加载失败'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

// 页面加载时获取列表
onMounted(() => {
  loadExpressionList()
})

// 计算可见的页码
const visiblePages = computed(() => {
  const pages: number[] = []
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  let end = Math.min(totalPages.value, start + maxVisible - 1)

  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1)
  }

  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  return pages
})

const clearSearch = () => {
  searchQuery.value = ''
}

const changePage = async (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  await loadExpressionList()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleSearch = async () => {
  // 实现搜索功能（简化版本，直接重新加载）
  currentPage.value = 1
  await loadExpressionList()
}

// 查看详情
const viewExpressionDetail = async (expressionId: number) => {
  try {
    const result = await getExpressionDetail(expressionId)
    if (result.success && result.data) {
      expressionDetail.value = result.data
      showDetailDialog.value = true
    } else {
      await showError(result.error || '加载详情失败')
    }
  } catch (err) {
    await showError(err instanceof Error ? err.message : '加载详情失败')
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  editMode.value = 'create'
  editForm.id = 0
  editForm.situation = ''
  editForm.style = ''
  editForm.count = 1.0
  editForm.type = 'style'
  editForm.chat_id = ''
  showEditDialog.value = true
}

// 编辑表达方式
const editExpression = (expr: ExpressionDetail) => {
  editMode.value = 'edit'
  editForm.id = expr.id
  editForm.situation = expr.situation
  editForm.style = expr.style
  editForm.count = expr.count
  editForm.type = expr.type
  editForm.chat_id = expr.chat_id
  showDetailDialog.value = false
  showEditDialog.value = true
}

// 检查是否可以提交编辑
const canSubmitEdit = computed(() => {
  if (!editForm.situation.trim() || !editForm.style.trim()) return false
  if (editMode.value === 'create' && !editForm.chat_id.trim()) return false
  return true
})

// 提交编辑
const submitEdit = async () => {
  try {
    let result
    if (editMode.value === 'create') {
      result = await createExpression({
        situation: editForm.situation,
        style: editForm.style,
        chat_id: editForm.chat_id,
        type: editForm.type,
        count: editForm.count
      })
      if (result.success) {
        await showSuccess('创建成功')
      } else {
        await showError(result.error || '创建失败')
        return
      }
    } else {
      result = await updateExpression(editForm.id, {
        situation: editForm.situation,
        style: editForm.style,
        count: editForm.count,
        type: editForm.type
      })
      if (result.success) {
        await showSuccess('更新成功')
      } else {
        await showError(result.error || '更新失败')
        return
      }
    }
    showEditDialog.value = false
    await loadExpressionList()
  } catch (err) {
    await showError(err instanceof Error ? err.message : '操作失败')
  }
}

// 删除确认
const deleteExpressionConfirm = async (expressionId: number) => {
  const confirmed = await showConfirm({
    message: '确定要删除这个表达方式吗？',
    type: 'danger'
  })
  if (confirmed) {
    try {
      const result = await deleteExpression(expressionId)
      if (result.success) {
        await showSuccess('删除成功')
        showDetailDialog.value = false
        await loadExpressionList()
      } else {
        await showError(result.error || '删除失败')
      }
    } catch (err) {
      await showError(err instanceof Error ? err.message : '删除失败')
    }
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const result = await getStatistics()
    if (result.success && result.data) {
      statistics.value = result.data
    } else {
      await showError(result.error || '加载统计信息失败')
    }
  } catch (err) {
    await showError(err instanceof Error ? err.message : '加载统计信息失败')
  }
}

// 格式化相对时间
const formatRelativeTime = (timestamp: number) => {
  const now = Date.now() / 1000
  const diff = now - timestamp
  
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  if (diff < 2592000) return `${Math.floor(diff / 86400)}天前`
  return formatDate(timestamp)
}

// 格式化日期
const formatDate = (timestamp: number) => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.expression-view {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}

/* 顶部栏 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.title-section h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.subtitle {
  color: var(--text-tertiary);
  font-size: 14px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.statistics-btn {
  background: var(--info-bg);
  color: var(--info);
}

.create-btn {
  background: var(--primary);
  color: white;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 14px;
  font-size: 20px;
  color: var(--text-tertiary);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 44px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 15px;
  transition: all var(--transition);
}

.search-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.clear-button {
  position: absolute;
  right: 8px;
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition);
}

.clear-button:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.search-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: var(--primary);
  border: none;
  border-radius: var(--radius);
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.search-button:hover {
  background: var(--primary-dark);
  transform: translateY(-1px);
}

/* 筛选器 */
.filters {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.filter-group select {
  padding: 6px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
}

/* 表达方式网格 */
.expression-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
}

.expression-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  cursor: pointer;
  transition: all var(--transition);
}

.expression-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.type-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
}

.type-style {
  background: var(--primary-bg);
  color: var(--primary);
}

.type-grammar {
  background: var(--success-bg);
  color: var(--success);
}

.count-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--warning-bg);
  color: var(--warning);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 700;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.situation-section,
.style-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.situation-section label,
.style-section label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.situation-text,
.style-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--text-primary);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
  font-size: 12px;
  color: var(--text-tertiary);
}

.chat-name,
.last-use {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
}

.page-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.page-button:hover:not(:disabled) {
  border-color: var(--primary);
  color: var(--primary);
}

.page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number {
  min-width: 40px;
  height: 40px;
  padding: 0 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
}

.page-number:hover {
  border-color: var(--primary);
  color: var(--primary);
}

.page-number.active {
  background: var(--primary);
  border-color: var(--primary);
  color: white;
}

/* 加载和错误状态 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--border-color);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.error-icon,
.empty-icon {
  font-size: 64px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
  opacity: 0.5;
}

.retry-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  margin-top: 16px;
  background: var(--primary);
  border: none;
  border-radius: var(--radius);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.retry-button:hover {
  background: var(--primary-dark);
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.dialog {
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.statistics-dialog {
  max-width: 800px;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

.dialog-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-button {
  padding: 6px;
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition);
}

.close-button:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.dialog-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border-color);
}

.cancel-button,
.confirm-button {
  padding: 10px 20px;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.cancel-button {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.confirm-button {
  background: var(--primary);
  color: white;
}

.confirm-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 详情对话框特定样式 */
.detail-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.type-badge-large {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
  width: fit-content;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
}

.detail-value {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.6;
}

.weight-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-bar {
  flex: 1;
  height: 24px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.weight-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary) 0%, var(--success) 100%);
  transition: width 0.3s ease;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  text-align: center;
}

.stat-card svg {
  font-size: 24px;
  color: var(--primary);
}

.stat-label {
  font-size: 12px;
  color: var(--text-tertiary);
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

/* 表单样式 */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-input,
.form-range,
.form-group select {
  padding: 10px 14px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 15px;
  transition: all var(--transition);
}

.form-input:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 统计对话框样式 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-box {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.stat-box svg {
  font-size: 32px;
  color: var(--primary);
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.top-used-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.top-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.top-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
}

.rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--primary);
  color: white;
  border-radius: 50%;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}

.top-content {
  flex: 1;
  min-width: 0;
}

.top-situation {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-style {
  font-size: 13px;
  color: var(--text-tertiary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-count {
  padding: 4px 12px;
  background: var(--warning-bg);
  color: var(--warning);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.edit-btn {
  background: var(--info-bg);
  color: var(--info);
}

.delete-btn {
  background: var(--danger-bg);
  color: var(--danger);
}

.action-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 对话框过渡动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s ease;
}

.dialog-fade-enter-active .dialog,
.dialog-fade-leave-active .dialog {
  transition: transform 0.3s ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-from .dialog,
.dialog-fade-leave-to .dialog {
  transform: scale(0.9);
}

/* 响应式 */
@media (max-width: 768px) {
  .expression-grid {
    grid-template-columns: 1fr;
  }

  .stats-overview {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .action-buttons {
    flex-direction: column;
  }

  .filters {
    flex-direction: column;
  }
}
</style>
