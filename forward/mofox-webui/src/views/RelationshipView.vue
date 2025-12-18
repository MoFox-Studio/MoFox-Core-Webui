<template>
  <div class="relationship-view">
    <!-- 返回按钮 (详情页时) -->
    <div v-if="personDetail" class="top-bar">
      <button class="m3-button tonal" @click="backToList">
        <span class="material-symbols-rounded">arrow_back</span>
        <span>返回列表</span>
      </button>
    </div>

    <!-- 搜索栏 (列表页时) -->
    <div v-else class="search-bar">
      <div class="search-input-wrapper">
        <span class="material-symbols-rounded search-icon">search</span>
        <input 
          v-model="searchQuery" 
          type="text" 
          class="m3-input search-input" 
          placeholder="搜索用户名..."
          @keyup.enter="handleSearch"
        />
        <button 
          v-if="searchQuery" 
          class="m3-icon-button clear-button" 
          @click="clearSearch"
        >
          <span class="material-symbols-rounded">close</span>
        </button>
      </div>
      <button class="m3-button filled" @click="handleSearch">
        <span class="material-symbols-rounded">search</span>
        <span>搜索</span>
      </button>
    </div>

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
      <button class="m3-button filled" @click="loadPersonDetail">
        <span class="material-symbols-rounded">refresh</span>
        <span>重试</span>
      </button>
    </div>

    <!-- 用户详情 -->
    <div v-else-if="personDetail" class="person-detail">
      <!-- 基础信息卡片 -->
      <div class="m3-card info-card">
        <div class="card-header">
          <div class="header-title">
            <span class="material-symbols-rounded header-icon">person</span>
            <h2>基础信息</h2>
          </div>
        </div>
        <div class="card-body">
          <div class="info-grid">
            <div class="info-item">
              <label>用户名</label>
              <span class="value">{{ personDetail.basic_info.person_name }}</span>
            </div>
            <div class="info-item">
              <label>昵称</label>
              <span class="value">{{ personDetail.basic_info.nickname || '未设置' }}</span>
            </div>
            <div class="info-item">
              <label>认识次数</label>
              <span class="value">{{ personDetail.basic_info.know_times }}</span>
            </div>
            <div class="info-item">
              <label>态度</label>
              <span class="value">{{ personDetail.basic_info.attitude || '未知' }}</span>
            </div>
            <div class="info-item full-width">
              <label>认识时间</label>
              <span class="value">{{ formatDate(personDetail.basic_info.know_since) }}</span>
            </div>
            <div class="info-item full-width">
              <label>最后见面</label>
              <span class="value">{{ formatDate(personDetail.basic_info.last_know) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 关系信息卡片 -->
      <div class="m3-card info-card">
        <div class="card-header">
          <div class="header-title">
            <span class="material-symbols-rounded header-icon">favorite</span>
            <h2>关系信息</h2>
          </div>
          <button class="m3-button text" @click="openEditRelationshipDialog">
            <span class="material-symbols-rounded">edit</span>
            <span>编辑</span>
          </button>
        </div>
        <div class="card-body">
          <div class="relationship-score">
            <label>关系分数</label>
            <div class="score-bar-container">
              <div class="score-bar">
                <div 
                  class="score-fill" 
                  :style="{ width: `${personDetail.relationship.relationship_score * 100}%` }"
                ></div>
              </div>
              <span class="score-text">{{ (personDetail.relationship.relationship_score * 100).toFixed(1) }}%</span>
            </div>
          </div>
          <div class="relationship-text">
            <label>关系描述</label>
            <p>{{ personDetail.relationship.relationship_text || '暂无描述' }}</p>
          </div>
        </div>
      </div>

      <!-- 印象卡片 -->
      <div class="m3-card info-card">
        <div class="card-header">
          <div class="header-title">
            <span class="material-symbols-rounded header-icon">psychology</span>
            <h2>我的印象</h2>
          </div>
          <button class="m3-button text" @click="openEditImpressionDialog">
            <span class="material-symbols-rounded">edit</span>
            <span>编辑</span>
          </button>
        </div>
        <div class="card-body">
          <div class="impression-section">
            <h3>详细印象</h3>
            <p class="impression-text">{{ personDetail.impression }}</p>
          </div>
          <div class="impression-section">
            <h3>简短印象</h3>
            <p class="impression-text short">{{ personDetail.short_impression }}</p>
          </div>
        </div>
      </div>

      <!-- 记忆点卡片 -->
      <div class="m3-card info-card">
        <div class="card-header">
          <div class="header-title">
            <span class="material-symbols-rounded header-icon">bookmark</span>
            <h2>重要记忆点</h2>
          </div>
          <button class="m3-button text" @click="openEditMemoryPointsDialog">
            <span class="material-symbols-rounded">edit</span>
            <span>编辑</span>
          </button>
        </div>
        <div class="card-body">
          <div v-if="personDetail.memory_points.length === 0" class="empty-state">
            <p>暂无记忆点</p>
          </div>
          <div v-else class="memory-points-list">
            <div 
              v-for="(point, index) in personDetail.memory_points" 
              :key="index"
              class="memory-point"
            >
              <div class="point-header">
                <span class="point-weight">重要性: {{ point.weight.toFixed(2) }}</span>
                <span class="point-time">{{ formatDate(point.timestamp) }}</span>
              </div>
              <p class="point-content">{{ point.content }}</p>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- 用户列表 -->
    <div v-else class="person-list">
      <!-- 列表统计 -->
      <div class="list-header">
        <h2>用户列表</h2>
        <span class="m3-badge secondary">共 {{ totalCount }} 人</span>
      </div>

      <!-- 加载状态 -->
      <div v-if="listLoading" class="loading-state">
        <span class="material-symbols-rounded spinning loading-icon">progress_activity</span>
        <p>加载中...</p>
      </div>

      <!-- 用户卡片网格 -->
      <div v-else-if="personList.length > 0" class="person-grid">
        <div 
          v-for="person in personList" 
          :key="person.person_id"
          class="m3-card person-card clickable"
          @click="viewPersonDetail(person.person_id)"
        >
          <div class="card-header-mini">
            <div class="person-avatar">
              <span class="material-symbols-rounded">person</span>
            </div>
            <div class="person-info">
              <h3 class="person-name">{{ person.person_name }}</h3>
              <p v-if="person.nickname" class="person-nickname">{{ person.nickname }}</p>
            </div>
          </div>

          <div class="card-body-mini">
            <div class="relation-score-mini">
              <label>关系分数</label>
              <div class="score-bar-mini-container">
                <div class="score-bar-mini">
                  <div 
                    class="score-fill-mini" 
                    :style="{ width: `${person.relationship_score * 100}%` }"
                  ></div>
                </div>
                <span class="score-text-mini">{{ (person.relationship_score * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <div v-if="person.relationship_text" class="relation-text-mini">
              <span class="material-symbols-rounded mini-icon">chat_bubble_outline</span>
              <span class="text-truncate">{{ person.relationship_text }}</span>
            </div>

            <div v-if="person.short_impression" class="impression-mini">
              <span class="material-symbols-rounded mini-icon">auto_awesome</span>
              <span class="text-truncate">{{ person.short_impression }}</span>
            </div>

            <div class="card-footer-mini">
              <div class="stat-item">
                <span class="material-symbols-rounded stat-icon">forum</span>
                <span>交互 {{ person.know_times }} 次</span>
              </div>
              <div v-if="person.last_know" class="stat-item">
                <span class="material-symbols-rounded stat-icon">schedule</span>
                <span>{{ formatDate(person.last_know) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <span class="material-symbols-rounded empty-icon">group_off</span>
        <h3>暂无用户</h3>
        <p>还没有认识的用户</p>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="pagination">
        <button 
          class="m3-button tonal" 
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          <span class="material-symbols-rounded">chevron_left</span>
          <span>上一页</span>
        </button>
        
        <div class="page-numbers">
          <button
            v-for="page in visiblePages"
            :key="page"
            class="page-number-btn"
            :class="{ active: page === currentPage }"
            @click="changePage(page)"
          >
            {{ page }}
          </button>
        </div>

        <button 
          class="m3-button tonal" 
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          <span>下一页</span>
          <span class="material-symbols-rounded">chevron_right</span>
        </button>
      </div>
    </div>

    <!-- 编辑关系信息对话框 -->
    <div class="m3-dialog-overlay" v-if="showEditRelationshipDialog" @click="showEditRelationshipDialog = false">
      <div class="m3-dialog" @click.stop>
        <div class="dialog-header">
          <h3>编辑关系信息</h3>
          <button class="m3-icon-button" @click="showEditRelationshipDialog = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div class="form-section">
            <div class="form-group">
              <label class="m3-label">关系分数 (0-100)</label>
              <input 
                v-model.number="editForm.score" 
                type="number" 
                min="0" 
                max="100" 
                step="1"
                class="m3-input"
              />
              <div class="score-preview">
                <div 
                  class="score-fill" 
                  :style="{ width: `${editForm.score}%` }"
                ></div>
              </div>
            </div>
            <div class="form-group">
              <label class="m3-label">关系描述</label>
              <textarea 
                v-model="editForm.text" 
                class="m3-input textarea"
                rows="3"
                placeholder="描述你与该用户的关系..."
              ></textarea>
            </div>
          </div>
        </div>
        <div class="dialog-actions">
          <button class="m3-button text" @click="showEditRelationshipDialog = false">
            取消
          </button>
          <button class="m3-button filled" @click="saveRelationship" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑印象对话框 -->
    <div class="m3-dialog-overlay" v-if="showEditImpressionDialog" @click="showEditImpressionDialog = false">
      <div class="m3-dialog" @click.stop>
        <div class="dialog-header">
          <h3>编辑印象</h3>
          <button class="m3-icon-button" @click="showEditImpressionDialog = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div class="form-section">
            <div class="form-group">
              <label class="m3-label">详细印象</label>
              <textarea 
                v-model="editForm.impression" 
                class="m3-input textarea"
                rows="4"
                placeholder="详细描述你对该用户的印象..."
              ></textarea>
            </div>
            <div class="form-group">
              <label class="m3-label">简短印象</label>
              <textarea 
                v-model="editForm.shortImpression" 
                class="m3-input textarea"
                rows="2"
                placeholder="一句话概括你的印象..."
              ></textarea>
            </div>
          </div>
        </div>
        <div class="dialog-actions">
          <button class="m3-button text" @click="showEditImpressionDialog = false">
            取消
          </button>
          <button class="m3-button filled" @click="saveImpression" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑记忆点对话框 -->
    <div class="m3-dialog-overlay" v-if="showEditMemoryPointsDialog" @click="showEditMemoryPointsDialog = false">
      <div class="m3-dialog large" @click.stop>
        <div class="dialog-header">
          <h3>编辑记忆点</h3>
          <button class="m3-icon-button" @click="showEditMemoryPointsDialog = false">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div class="form-section">
            <div class="section-header">
              <h4><span class="material-symbols-rounded">bookmark</span> 记忆点列表</h4>
              <button class="m3-button tonal small" @click="addMemoryPoint" type="button">
                <span class="material-symbols-rounded">add</span>
                添加
              </button>
            </div>
            <div v-if="editForm.memoryPoints.length === 0" class="empty-hint">
              暂无记忆点，点击"添加"按钮创建新记忆点
            </div>
            <div v-else class="memory-points-edit-list">
              <div 
                v-for="(point, index) in editForm.memoryPoints" 
                :key="index"
                class="memory-point-edit"
              >
                <div class="point-edit-header">
                  <label class="m3-label">重要性 (0-1)</label>
                  <input 
                    v-model.number="point.weight" 
                    type="number" 
                    min="0" 
                    max="1" 
                    step="0.01"
                    class="m3-input weight-input"
                  />
                  <button 
                    class="m3-icon-button error" 
                    @click="deleteMemoryPoint(index)"
                    type="button"
                  >
                    <span class="material-symbols-rounded">delete</span>
                  </button>
                </div>
                <textarea 
                  v-model="point.content" 
                  class="m3-input textarea"
                  rows="2"
                  placeholder="描述这个记忆点..."
                ></textarea>
              </div>
            </div>
          </div>
        </div>
        <div class="dialog-actions">
          <button class="m3-button text" @click="showEditMemoryPointsDialog = false">
            取消
          </button>
          <button class="m3-button filled" @click="saveMemoryPoints" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { 
  getPersonList,
  getPersonDetail, 
  updatePersonRelationship, 
  searchPerson,
  type PersonDetail,
  type PersonCard 
} from '@/api/relationship'
import { showSuccess, showError } from '@/utils/dialog'

const searchQuery = ref('')
const loading = ref(false)
const error = ref('')
const personDetail = ref<PersonDetail | null>(null)
const currentPersonId = ref('')

// 列表相关状态
const personList = ref<PersonCard[]>([])
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = ref(0)
const totalCount = ref(0)
const listLoading = ref(false)

const showEditRelationshipDialog = ref(false)
const showEditImpressionDialog = ref(false)
const showEditMemoryPointsDialog = ref(false)
const saving = ref(false)

const editForm = reactive({
  score: 0,
  text: '',
  impression: '',
  shortImpression: '',
  memoryPoints: [] as Array<{ content: string; weight: number; timestamp: string }>
})

// 加载用户列表
const loadPersonList = async () => {
  listLoading.value = true
  error.value = ''
  
  try {
    const result = await getPersonList(currentPage.value, pageSize.value)
    if (result.success && result.data) {
      personList.value = result.data.persons
      totalPages.value = result.data.total_pages
      totalCount.value = result.data.total
    } else {
      error.value = result.error || '加载用户列表失败'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    listLoading.value = false
  }
}

// 页面加载时获取用户列表
onMounted(() => {
  loadPersonList()
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
  await loadPersonList()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const viewPersonDetail = async (personId: string) => {
  currentPersonId.value = personId
  await loadPersonDetail()
}

const backToList = () => {
  personDetail.value = null
  currentPersonId.value = ''
  searchQuery.value = ''
  loadPersonList()
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    await showError('请输入用户名')
    return
  }

  loading.value = true
  error.value = ''
  personDetail.value = null

  try {
    const result = await searchPerson(searchQuery.value.trim())
    if (result.success && result.data) {
      currentPersonId.value = result.data.person_id
      await loadPersonDetail()
    } else {
      error.value = result.error || '未找到用户'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '搜索失败'
  } finally {
    loading.value = false
  }
}

const loadPersonDetail = async () => {
  if (!currentPersonId.value) return

  loading.value = true
  error.value = ''

  try {
    const result = await getPersonDetail(currentPersonId.value)
    if (result.success && result.data) {
      personDetail.value = result.data
      // 初始化编辑表单
      editForm.score = result.data.relationship.relationship_score * 100
      editForm.text = result.data.relationship.relationship_text || ''
    } else {
      error.value = result.error || '加载用户详情失败'
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '加载失败'
  } finally {
    loading.value = false
  }
}

// 打开编辑关系信息对话框
const openEditRelationshipDialog = () => {
  if (!personDetail.value) return
  
  // 初始化表单数据
  editForm.score = personDetail.value.relationship.relationship_score * 100
  editForm.text = personDetail.value.relationship.relationship_text || ''
  
  showEditRelationshipDialog.value = true
}

// 打开编辑印象对话框
const openEditImpressionDialog = () => {
  if (!personDetail.value) return
  
  // 初始化表单数据
  editForm.impression = personDetail.value.impression || ''
  editForm.shortImpression = personDetail.value.short_impression || ''
  
  showEditImpressionDialog.value = true
}

// 打开编辑记忆点对话框
const openEditMemoryPointsDialog = () => {
  if (!personDetail.value) return
  
  // 初始化表单数据
  editForm.memoryPoints = personDetail.value.memory_points.map(p => ({
    content: p.content,
    weight: p.weight,
    timestamp: p.timestamp
  }))
  
  showEditMemoryPointsDialog.value = true
}

// 添加记忆点
const addMemoryPoint = () => {
  editForm.memoryPoints.push({
    content: '',
    weight: 0.5,
    timestamp: new Date().toISOString()
  })
}

// 删除记忆点
const deleteMemoryPoint = (index: number) => {
  editForm.memoryPoints.splice(index, 1)
}

// 保存关系信息
const saveRelationship = async () => {
  if (!currentPersonId.value) return

  saving.value = true

  try {
    // 更新关系信息
    const result = await updatePersonRelationship(currentPersonId.value, {
      relationship_score: editForm.score / 100,
      relationship_text: editForm.text
    })

    if (!result.success) {
      throw new Error(result.error || '更新关系信息失败')
    }

    // 检查返回的数据中的 success 字段
    if (result.data && !result.data.success) {
      throw new Error(result.data.message || '更新关系信息失败')
    }

    await showSuccess('关系信息已更新')
    showEditRelationshipDialog.value = false
    await loadPersonDetail()
  } catch (err) {
    await showError(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

// 保存印象
const saveImpression = async () => {
  if (!currentPersonId.value) return

  saving.value = true

  try {
    // 更新印象信息
    const { updatePersonImpression } = await import('@/api/relationship')
    
    const result = await updatePersonImpression(
      currentPersonId.value,
      editForm.impression,
      editForm.shortImpression
    )

    if (!result.success) {
      throw new Error(result.error || '更新印象失败')
    }

    // 检查返回的数据中的 success 字段
    if (result.data && !result.data.success) {
      throw new Error(result.data.message || '更新印象失败')
    }

    await showSuccess('印象已更新')
    showEditImpressionDialog.value = false
    await loadPersonDetail()
  } catch (err) {
    await showError(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

// 保存记忆点
const saveMemoryPoints = async () => {
  if (!currentPersonId.value) return

  saving.value = true

  try {
    // 更新记忆点
    const { updatePersonPoints } = await import('@/api/relationship')
    
    const result = await updatePersonPoints(
      currentPersonId.value,
      editForm.memoryPoints
    )

    if (!result.success) {
      throw new Error(result.error || '更新记忆点失败')
    }

    // 检查返回的数据中的 success 字段
    if (result.data && !result.data.success) {
      throw new Error(result.data.message || '更新记忆点失败')
    }

    await showSuccess('记忆点已更新')
    showEditMemoryPointsDialog.value = false
    await loadPersonDetail()
  } catch (err) {
    await showError(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

const formatDate = (dateStr?: string) => {
  if (!dateStr) return '未知'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}
</script>

<style scoped>
.relationship-view {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
  animation: fadeIn 0.4s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 顶部栏 */
.top-bar {
  margin-bottom: 24px;
}

/* 搜索栏 */
.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.search-input-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  font-size: 20px;
  color: var(--md-sys-color-on-surface-variant);
  pointer-events: none;
}

.search-input {
  padding-left: 40px;
  padding-right: 40px;
  width: 100%;
}

.clear-button {
  position: absolute;
  right: 8px;
  width: 32px;
  height: 32px;
}

/* 用户列表 */
.person-list {
  width: 100%;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.list-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

/* 用户卡片网格 */
.person-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.person-card {
  padding: 0;
  overflow: hidden;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.person-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
}

.card-header-mini {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--md-sys-color-surface-container-high);
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.person-avatar {
  width: 48px;
  height: 48px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  flex-shrink: 0;
}

.person-info {
  flex: 1;
  min-width: 0;
}

.person-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.person-nickname {
  margin: 2px 0 0 0;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-body-mini {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.relation-score-mini label {
  display: block;
  margin-bottom: 6px;
  font-size: 11px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.score-bar-mini-container {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-bar-mini {
  flex: 1;
  height: 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 4px;
  overflow: hidden;
}

.score-fill-mini {
  height: 100%;
  background: var(--md-sys-color-primary);
  border-radius: 4px;
}

.score-text-mini {
  font-size: 12px;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  min-width: 32px;
  text-align: right;
}

.relation-text-mini,
.impression-mini {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
}

.mini-icon {
  font-size: 18px;
  color: var(--md-sys-color-primary);
  flex-shrink: 0;
}

.text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer-mini {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.stat-icon {
  font-size: 16px;
}

/* 分页 */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 32px;
}

.page-numbers {
  display: flex;
  gap: 8px;
}

.page-number-btn {
  min-width: 40px;
  height: 40px;
  padding: 0 8px;
  border-radius: 20px;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.page-number-btn:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.page-number-btn.active {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

/* 加载和错误状态 */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
}

.loading-icon,
.error-icon,
.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  color: var(--md-sys-color-primary);
}

.error-icon {
  color: var(--md-sys-color-error);
}

.empty-icon {
  color: var(--md-sys-color-outline);
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 信息卡片 */
.info-card {
  margin-bottom: 20px;
  padding: 0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.card-body {
  padding: 24px;
}

/* 信息网格 */
.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-item label {
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.info-item .value {
  font-size: 16px;
  color: var(--md-sys-color-on-surface);
}

/* 关系分数 */
.relationship-score {
  margin-bottom: 24px;
}

.relationship-score label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.score-bar-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-bar {
  flex: 1;
  height: 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 6px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: var(--md-sys-color-primary);
  border-radius: 6px;
  transition: width 0.3s ease;
}

.score-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  min-width: 48px;
  text-align: right;
}

.relationship-text label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.relationship-text p {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface);
}

/* 印象 */
.impression-section {
  margin-bottom: 24px;
}

.impression-section:last-child {
  margin-bottom: 0;
}

.impression-section h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.impression-text {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface);
  white-space: pre-wrap;
}

.impression-text.short {
  font-style: italic;
  color: var(--md-sys-color-on-surface-variant);
}

/* 记忆点 */
.memory-points-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.memory-point {
  padding: 16px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
  border-left: 4px solid var(--md-sys-color-primary);
}

.point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.point-weight {
  font-weight: 600;
  color: var(--md-sys-color-primary);
}

.point-content {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--md-sys-color-on-surface);
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
}

/* 弹窗内容 */
.m3-dialog.large {
  max-width: 700px;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.m3-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.score-preview {
  margin-top: 8px;
  height: 8px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 4px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.section-header h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.empty-hint {
  padding: 24px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  font-size: 14px;
}

.memory-points-edit-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.memory-point-edit {
  padding: 16px;
  background: var(--md-sys-color-surface-container-low);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
}

.point-edit-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.weight-input {
  width: 100px;
}

.m3-icon-button.error {
  color: var(--md-sys-color-error);
  margin-left: auto;
}

/* 响应式 */
@media (max-width: 768px) {
  .relationship-view {
    padding: 16px;
  }

  .search-bar {
    flex-direction: column;
    gap: 12px;
  }

  .search-input-wrapper {
    width: 100%;
  }

  .person-grid {
    grid-template-columns: 1fr;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style>
