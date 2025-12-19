<template>
  <div class="expression-view">
    <!-- 顶部操作栏 -->
    <header class="page-header">
      <div class="header-content">
        <div class="title-group">
          <div class="header-icon-container">
            <span class="material-symbols-rounded header-icon">psychology</span>
          </div>
          <div class="header-text">
            <h1 class="page-title">表达方式管理</h1>
            <p class="page-description">管理Bot的语言风格和表达习惯</p>
          </div>
        </div>
        <div class="header-actions">
          <button class="m3-button tonal" @click="showStatisticsDialog = true">
            <span class="material-symbols-rounded">bar_chart</span>
            统计信息
          </button>
          <button class="m3-button filled" @click="openCreateDialog">
            <span class="material-symbols-rounded">add</span>
            新建表达
          </button>
        </div>
      </div>
    </header>

    <!-- 搜索和筛选栏 -->
    <div class="m3-card toolbar-card">
      <div class="toolbar-content">
        <div class="search-container">
          <div class="search-wrapper" :class="{ focused: isSearchFocused }">
            <span class="material-symbols-rounded search-icon">search</span>
            <input
              v-model="searchQuery"
              type="text"
              class="search-input"
              placeholder="搜索情境或表达风格..."
              @focus="isSearchFocused = true"
              @blur="isSearchFocused = false"
              @keyup.enter="handleSearch"
            />
            <button v-if="searchQuery" class="icon-button clear-btn" @click="clearSearch">
              <span class="material-symbols-rounded">cancel</span>
            </button>
          </div>
        </div>
        
        <div class="filters-group">
          <!-- Type Filter -->
          <div class="custom-select" :class="{ active: showTypeDropdown }">
            <div class="select-trigger" @click="showTypeDropdown = !showTypeDropdown; showSortDropdown = false">
              <span>{{ getFilterTypeLabel(filterType) }}</span>
              <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
            </div>
            <Transition name="scale-y">
              <div v-if="showTypeDropdown" class="select-options m3-card">
                <div 
                  class="select-option" 
                  :class="{ selected: filterType === '' }"
                  @click="filterType = ''; loadExpressionList(); showTypeDropdown = false"
                >
                  全部类型
                </div>
                <div 
                  class="select-option" 
                  :class="{ selected: filterType === 'style' }"
                  @click="filterType = 'style'; loadExpressionList(); showTypeDropdown = false"
                >
                  语言风格
                </div>
                <div 
                  class="select-option" 
                  :class="{ selected: filterType === 'grammar' }"
                  @click="filterType = 'grammar'; loadExpressionList(); showTypeDropdown = false"
                >
                  句法特点
                </div>
              </div>
            </Transition>
            <div v-if="showTypeDropdown" class="dropdown-overlay" @click="showTypeDropdown = false"></div>
          </div>
          
          <!-- Sort Filter -->
          <div class="custom-select" :class="{ active: showSortDropdown }">
            <div class="select-trigger" @click="showSortDropdown = !showSortDropdown; showTypeDropdown = false">
              <span>{{ getSortByLabel(sortBy) }}</span>
              <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
            </div>
            <Transition name="scale-y">
              <div v-if="showSortDropdown" class="select-options m3-card">
                <div 
                  class="select-option" 
                  :class="{ selected: sortBy === 'last_active_time' }"
                  @click="sortBy = 'last_active_time'; loadExpressionList(); showSortDropdown = false"
                >
                  最后使用
                </div>
                <div 
                  class="select-option" 
                  :class="{ selected: sortBy === 'count' }"
                  @click="sortBy = 'count'; loadExpressionList(); showSortDropdown = false"
                >
                  使用次数
                </div>
                <div 
                  class="select-option" 
                  :class="{ selected: sortBy === 'create_date' }"
                  @click="sortBy = 'create_date'; loadExpressionList(); showSortDropdown = false"
                >
                  创建时间
                </div>
              </div>
            </Transition>
            <div v-if="showSortDropdown" class="dropdown-overlay" @click="showSortDropdown = false"></div>
          </div>
          
          <button 
            class="m3-icon-button" 
            @click="toggleSortOrder"
            :title="sortOrder === 'desc' ? '降序' : '升序'"
          >
            <span class="material-symbols-rounded">
              {{ sortOrder === 'desc' ? 'arrow_downward' : 'arrow_upward' }}
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-state">
        <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
        <p>加载中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="error-state">
        <span class="material-symbols-rounded error-icon">error</span>
        <h3>加载失败</h3>
        <p>{{ error }}</p>
        <button class="m3-button tonal" @click="loadExpressionList">
          <span class="material-symbols-rounded">refresh</span>
          重试
        </button>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!expressionList || expressionList.length === 0" class="empty-state">
        <span class="material-symbols-rounded empty-icon">inbox</span>
        <h3>暂无表达方式</h3>
        <p>{{ searchQuery ? '没有找到匹配的表达方式' : '还没有创建任何表达方式' }}</p>
      </div>

      <!-- 表达方式网格 -->
      <div v-else class="expression-grid">
        <div
          v-for="expr in expressionList"
          :key="expr.id"
          class="m3-card expression-card"
          @click="viewExpressionDetail(expr.id)"
        >
          <div class="card-header">
            <div class="badges">
              <span class="m3-badge" :class="expr.type === 'style' ? 'primary' : 'tertiary'">
                {{ expr.type === 'style' ? '风格' : '句法' }}
              </span>
              <span class="m3-badge secondary count-badge">
                <span class="material-symbols-rounded badge-icon">local_fire_department</span>
                {{ expr.count.toFixed(1) }}
              </span>
            </div>
            <span class="last-use-time">{{ formatRelativeTime(expr.last_active_time) }}</span>
          </div>
          
          <div class="card-body">
            <div class="info-row">
              <span class="label">情境</span>
              <p class="text situation">{{ expr.situation }}</p>
            </div>
            <div class="info-row">
              <span class="label">表达</span>
              <p class="text style">{{ expr.style }}</p>
            </div>
          </div>
          
          <div class="card-footer">
            <div class="chat-info" :title="`${expr.chat_id_display || expr.chat_id}\n哈希: ${expr.chat_id}`">
              <span class="material-symbols-rounded footer-icon">chat</span>
              <span class="chat-name">{{ expr.chat_id_display || expr.chat_name || expr.chat_id.substring(0, 8) + '...' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="totalPages > 1" class="pagination">
      <button
        class="m3-icon-button"
        :disabled="currentPage === 1"
        @click="changePage(currentPage - 1)"
      >
        <span class="material-symbols-rounded">chevron_left</span>
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
        class="m3-icon-button"
        :disabled="currentPage === totalPages"
        @click="changePage(currentPage + 1)"
      >
        <span class="material-symbols-rounded">chevron_right</span>
      </button>
    </div>

    <!-- 详情对话框 -->
    <div class="m3-dialog-overlay" v-if="showDetailDialog" @click="showDetailDialog = false">
      <div class="m3-dialog detail-dialog" @click.stop>
        <div class="dialog-header">
          <h3>表达方式详情</h3>
          <button class="m3-icon-button" @click="showDetailDialog = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        
        <div v-if="expressionDetail" class="dialog-content">
          <div class="detail-header">
            <span class="m3-badge large" :class="expressionDetail.type === 'style' ? 'primary' : 'tertiary'">
              <span class="material-symbols-rounded badge-icon">
                {{ expressionDetail.type === 'style' ? 'format_quote' : 'rule' }}
              </span>
              {{ expressionDetail.type === 'style' ? '语言风格' : '句法特点' }}
            </span>
          </div>

          <div class="detail-section">
            <div class="detail-item">
              <label>情境描述</label>
              <div class="detail-value">{{ expressionDetail.situation }}</div>
            </div>

            <div class="detail-item">
              <label>表达风格</label>
              <div class="detail-value highlight">{{ expressionDetail.style }}</div>
            </div>

            <div class="detail-item">
              <label>权重评分</label>
              <div class="weight-display">
                <div class="weight-bar-bg">
                  <div class="weight-bar-fill" :style="{ width: `${(expressionDetail.count / 5) * 100}%` }"></div>
                </div>
                <span class="weight-text">{{ expressionDetail.count.toFixed(2)}} / 5.0</span>
              </div>
            </div>

            <div class="detail-item">
              <label>所属聊天流</label>
              <div class="chat-detail-card">
                <span class="material-symbols-rounded chat-icon">forum</span>
                <div class="chat-detail-info">
                  <span class="chat-detail-name">{{ expressionDetail.chat_name }}</span>
                  <span class="chat-detail-id">{{ expressionDetail.chat_id_display }}</span>
                </div>
              </div>
            </div>

            <div class="stats-grid-mini">
              <div class="mini-stat">
                <span class="material-symbols-rounded">calendar_today</span>
                <div class="mini-stat-content">
                  <span class="label">创建于</span>
                  <span class="value">{{ formatDate(expressionDetail.create_date) }}</span>
                </div>
              </div>
              <div class="mini-stat">
                <span class="material-symbols-rounded">update</span>
                <div class="mini-stat-content">
                  <span class="label">最后使用</span>
                  <span class="value">{{ formatDate(expressionDetail.last_active_time) }}</span>
                </div>
              </div>
              <div class="mini-stat">
                <span class="material-symbols-rounded">history</span>
                <div class="mini-stat-content">
                  <span class="label">已创建</span>
                  <span class="value">{{ expressionDetail.usage_stats.days_since_create }} 天</span>
                </div>
              </div>
              <div class="mini-stat">
                <span class="material-symbols-rounded">trending_up</span>
                <div class="mini-stat-content">
                  <span class="label">使用频率</span>
                  <span class="value">{{ expressionDetail.usage_stats.usage_frequency.toFixed(3) }} /天</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="dialog-actions">
          <button class="m3-button text error" @click="deleteExpressionConfirm(expressionDetail!.id)">
            <span class="material-symbols-rounded">delete</span>
            删除
          </button>
          <div class="spacer"></div>
          <button class="m3-button text" @click="showDetailDialog = false">关闭</button>
          <button class="m3-button filled" @click="editExpression(expressionDetail!)">
            <span class="material-symbols-rounded">edit</span>
            编辑
          </button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑对话框 -->
    <div class="m3-dialog-overlay" v-if="showEditDialog" @click="showEditDialog = false">
      <div class="m3-dialog edit-dialog" @click.stop>
        <div class="dialog-header">
          <h3>{{ editMode === 'create' ? '创建表达方式' : '编辑表达方式' }}</h3>
          <button class="m3-icon-button" @click="showEditDialog = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        
        <div class="dialog-content">
          <div class="form-group">
            <label>类型</label>
            <div class="select-wrapper full-width">
              <select v-model="editForm.type" class="m3-input">
                <option value="style">语言风格</option>
                <option value="grammar">句法特点</option>
              </select>
              <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
            </div>
          </div>

          <div class="form-group">
            <label>情境描述</label>
            <input
              v-model="editForm.situation"
              type="text"
              class="m3-input"
              placeholder="如：对某件事表示十分惊叹，有些意外"
              maxlength="200"
            />
          </div>

          <div class="form-group">
            <label>表达风格</label>
            <textarea
              v-model="editForm.style"
              class="m3-input textarea"
              placeholder="如：我嘞个xxxx"
              rows="3"
              maxlength="200"
            ></textarea>
          </div>

          <div class="form-group">
            <label>权重 ({{ editForm.count.toFixed(1) }})</label>
            <input
              v-model.number="editForm.count"
              type="range"
              min="0"
              max="5"
              step="0.1"
              class="m3-range"
            />
          </div>

          <div v-if="editMode === 'create'" class="form-group">
            <div class="label-row">
              <label>聊天流</label>
              <button class="m3-button text small" @click="inputType = inputType === 'select' ? 'manual' : 'select'">
                {{ inputType === 'select' ? '切换手动输入' : '切换列表选择' }}
              </button>
            </div>
            
            <div v-if="inputType === 'select'" class="select-wrapper full-width">
              <select v-model="editForm.chat_id" :disabled="loadingChats" class="m3-input">
                <option value="" disabled>请选择聊天流</option>
                <option v-for="chat in chatList" :key="chat.id" :value="chat.id">
                  {{ chat.name }} ({{ chat.platform }})
                </option>
              </select>
              <span class="material-symbols-rounded select-arrow">arrow_drop_down</span>
              <div v-if="loadingChats" class="helper-text">加载中...</div>
              <div v-else-if="chatList.length === 0" class="helper-text warning">未找到活跃的聊天流，请尝试手动输入</div>
            </div>

            <div v-else>
              <input
                v-model="editForm.chat_id"
                type="text"
                class="m3-input"
                placeholder="格式: platform:id:type 或哈希值"
              />
              <div class="helper-text">
                支持格式：platform:raw_id:type (如: QQ:12345:group) 或 哈希值
              </div>
            </div>
          </div>
        </div>
        
        <div class="dialog-actions">
          <button class="m3-button text" @click="showEditDialog = false">取消</button>
          <button class="m3-button filled" :disabled="!canSubmitEdit" @click="submitEdit">
            {{ editMode === 'create' ? '创建' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 统计信息对话框 -->
    <div class="m3-dialog-overlay" v-if="showStatisticsDialog" @click="showStatisticsDialog = false">
      <div class="m3-dialog stats-dialog" @click.stop>
        <div class="dialog-header">
          <h3>统计信息</h3>
          <button class="m3-icon-button" @click="showStatisticsDialog = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        
        <div v-if="statistics" class="dialog-content">
          <div class="stats-overview-cards">
            <div class="m3-card stat-overview-card">
              <div class="stat-icon-bg primary">
                <span class="material-symbols-rounded">database</span>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ statistics.total_count }}</span>
                <span class="stat-label">总数</span>
              </div>
            </div>
            <div class="m3-card stat-overview-card">
              <div class="stat-icon-bg secondary">
                <span class="material-symbols-rounded">format_quote</span>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ statistics.style_count }}</span>
                <span class="stat-label">语言风格</span>
              </div>
            </div>
            <div class="m3-card stat-overview-card">
              <div class="stat-icon-bg tertiary">
                <span class="material-symbols-rounded">rule</span>
              </div>
              <div class="stat-info">
                <span class="stat-value">{{ statistics.grammar_count }}</span>
                <span class="stat-label">句法特点</span>
              </div>
            </div>
          </div>

          <div class="top-list-section">
            <h4>最常用表达方式 Top 10</h4>
            <div class="top-list">
              <div v-for="(expr, idx) in statistics.top_used" :key="expr.id" class="top-item">
                <div class="rank-badge">{{ idx + 1 }}</div>
                <div class="top-content">
                  <div class="top-situation">{{ expr.situation }}</div>
                  <div class="top-style">{{ expr.style }}</div>
                </div>
                <div class="top-count">
                  <span class="material-symbols-rounded">local_fire_department</span>
                  {{ expr.count.toFixed(1) }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="dialog-actions">
          <button class="m3-button text" @click="showStatisticsDialog = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import {
  getExpressionList,
  getExpressionDetail,
  createExpression,
  updateExpression,
  deleteExpression,
  getStatistics,
  getChatList,
  type Expression,
  type ExpressionDetail,
  type ExpressionStatistics,
  type ExpressionType,
  type SortByField,
  type ChatInfo
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

// 聊天流列表
const chatList = ref<ChatInfo[]>([])
const loadingChats = ref(false)
const inputType = ref<'select' | 'manual'>('select')

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

// 监听编辑对话框打开
watch(showEditDialog, (newVal) => {
  if (newVal && editMode.value === 'create') {
    loadChatList()
  }
})

async function loadChatList() {
  loadingChats.value = true
  try {
    const res = await getChatList()
    chatList.value = res.data || []
  } catch (e) {
    console.error('Failed to load chat list', e)
  } finally {
    loadingChats.value = false
  }
}

// 监听筛选条件变化，自动刷新列表
watch([filterType, sortBy, sortOrder], () => {
  currentPage.value = 1 // 重置到第一页
  loadExpressionList()
})

// 切换排序顺序
const toggleSortOrder = () => {
  sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
}

// UI State
const isSearchFocused = ref(false)
const showTypeDropdown = ref(false)
const showSortDropdown = ref(false)

const getFilterTypeLabel = (type: string | undefined) => {
  const map: Record<string, string> = {
    '': '全部类型',
    'style': '语言风格',
    'grammar': '句法特点'
  }
  return map[type || ''] || '全部类型'
}

const getSortByLabel = (sort: string) => {
  const map: Record<string, string> = {
    'last_active_time': '最后使用',
    'count': '使用次数',
    'create_date': '创建时间'
  }
  return map[sort] || '最后使用'
}

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
  handleSearch()
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
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 页面标题 */
.page-header {
  padding: 0 8px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-container {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-icon {
  font-size: 24px;
}

.page-title {
  font-size: 22px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 4px;
}

.page-description {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 工具栏 */
.toolbar-card {
  padding: 16px;
  border-radius: 16px;
  background: var(--md-sys-color-surface-container);
}

.toolbar-content {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.search-container {
  flex: 1;
  min-width: 280px;
}

.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  height: 40px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 20px;
  padding: 0 12px;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.search-wrapper.focused {
  background: var(--md-sys-color-surface);
  border-color: var(--md-sys-color-primary);
}

.search-icon {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 20px;
  margin-right: 8px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  outline: none;
  padding: 0;
  height: 100%;
}

.clear-btn {
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px;
  margin-left: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  cursor: pointer;
  border: none;
  background: transparent;
}

.clear-btn:hover {
  background: var(--md-sys-color-surface-variant);
  color: var(--md-sys-color-on-surface);
}

.filters-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Custom Select */
.custom-select {
  position: relative;
  min-width: 140px;
  height: 40px;
}

.select-trigger {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px 0 16px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
}

.custom-select.active .select-trigger {
  background: var(--md-sys-color-surface);
  border-color: var(--md-sys-color-primary);
}

.select-arrow {
  color: var(--md-sys-color-on-surface-variant);
  transition: transform 0.2s;
}

.custom-select.active .select-arrow {
  transform: rotate(180deg);
  color: var(--md-sys-color-primary);
}

.select-options {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  padding: 4px;
  z-index: 100;
  box-shadow: var(--md-sys-elevation-2);
  transform-origin: top center;
}

.select-option {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  transition: background 0.2s;
}

.select-option:hover {
  background: var(--md-sys-color-surface-variant);
}

.select-option.selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.dropdown-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
}

/* Transitions */
.scale-y-enter-active,
.scale-y-leave-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.scale-y-enter-from,
.scale-y-leave-to {
  opacity: 0;
  transform: scaleY(0.8);
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 4px;
}

.expression-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.expression-card {
  background: var(--md-sys-color-surface-container-low);
  border-radius: 16px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 12px;
  border: 1px solid transparent;
}

.expression-card:hover {
  background: var(--md-sys-color-surface-container-high);
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
  border-color: var(--md-sys-color-outline-variant);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.badges {
  display: flex;
  gap: 8px;
}

.m3-badge {
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 8px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.m3-badge.primary {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.m3-badge.secondary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-badge.tertiary {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.badge-icon {
  font-size: 14px;
}

.last-use-time {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.label {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
}

.text {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.text.style {
  font-weight: 500;
}

.card-footer {
  padding-top: 12px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.chat-info {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 12px;
}

.footer-icon {
  font-size: 16px;
}

.chat-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 0;
}

.page-numbers {
  display: flex;
  gap: 4px;
}

.page-number {
  min-width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.page-number:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.page-number.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

/* 状态提示 */
.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--md-sys-color-on-surface-variant);
  gap: 16px;
  height: 100%;
}

.loading-icon,
.error-icon,
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 弹窗样式 */
.m3-dialog-overlay {
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
  backdrop-filter: blur(4px);
}

.m3-dialog {
  background: var(--md-sys-color-surface-container);
  width: 90%;
  max-width: 500px;
  max-height: 85vh;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-3);
  animation: dialogIn 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.detail-dialog {
  max-width: 600px;
}

.stats-dialog {
  max-width: 700px;
}

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.dialog-header {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-header h3 {
  margin: 0;
  font-size: 22px;
  color: var(--md-sys-color-on-surface);
}

.dialog-content {
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dialog-actions {
  padding: 16px 24px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.spacer {
  flex: 1;
}

/* 详情内容 */
.detail-header {
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.m3-badge.large {
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 16px;
}

.detail-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 500;
}

.detail-value {
  font-size: 15px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.5;
}

.detail-value.highlight {
  background: var(--md-sys-color-surface-container-high);
  padding: 12px;
  border-radius: 12px;
  font-family: 'JetBrains Mono', monospace;
}

.weight-display {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-bar-bg {
  flex: 1;
  height: 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 4px;
  overflow: hidden;
}

.weight-bar-fill {
  height: 100%;
  background: var(--md-sys-color-primary);
  border-radius: 4px;
}

.weight-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.chat-detail-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 12px;
}

.chat-icon {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.chat-detail-info {
  display: flex;
  flex-direction: column;
}

.chat-detail-name {
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.chat-detail-id {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.stats-grid-mini {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.mini-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
}

.mini-stat .material-symbols-rounded {
  color: var(--md-sys-color-primary);
  font-size: 20px;
}

.mini-stat-content {
  display: flex;
  flex-direction: column;
}

.mini-stat-content .label {
  font-size: 11px;
  color: var(--md-sys-color-on-surface-variant);
}

.mini-stat-content .value {
  font-size: 13px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

/* 编辑表单 */
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.select-wrapper.full-width {
  width: 100%;
}

.select-wrapper.full-width select {
  width: 100%;
}

.textarea {
  resize: vertical;
  min-height: 80px;
}

.m3-range {
  width: 100%;
  accent-color: var(--md-sys-color-primary);
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.helper-text {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 4px;
}

.helper-text.warning {
  color: var(--md-sys-color-error);
}

/* 统计概览 */
.stats-overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.stat-overview-card {
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon-bg {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon-bg.primary {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.stat-icon-bg.secondary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.stat-icon-bg.tertiary {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.stat-label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.top-list-section h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: var(--md-sys-color-on-surface);
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
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
}

.rank-badge {
  width: 24px;
  height: 24px;
  border-radius: 12px;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.top-content {
  flex: 1;
  min-width: 0;
}

.top-situation {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-style {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--md-sys-color-tertiary);
}

.top-count .material-symbols-rounded {
  font-size: 16px;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .toolbar-content {
    flex-direction: column;
  }
  
  .search-box {
    width: 100%;
  }
  
  .filters-group {
    width: 100%;
    justify-content: space-between;
  }
  
  .select-wrapper {
    flex: 1;
  }
  
  .filter-select {
    width: 100%;
  }
  
  .stats-grid-mini {
    grid-template-columns: 1fr;
  }
}
</style>
