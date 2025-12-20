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
    <div v-else class="search-bar-container">
      <div class="search-wrapper" :class="{ focused: isSearchFocused }">
        <span class="material-symbols-rounded search-icon">search</span>
        <input 
          v-model="searchQuery" 
          type="text" 
          class="search-input" 
          placeholder="搜索用户名..."
          @focus="isSearchFocused = true"
          @blur="isSearchFocused = false"
          @keyup.enter="handleSearch"
        />
        <button 
          v-if="searchQuery" 
          class="icon-button clear-btn" 
          @click="clearSearch"
        >
          <span class="material-symbols-rounded">cancel</span>
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

      <!-- 平台筛选 -->
      <div class="platform-filter">
        <div class="filter-label">
          <span class="material-symbols-rounded">filter_list</span>
          <span>按平台筛选</span>
        </div>
        <div class="platform-chips">
          <button 
            class="platform-chip" 
            :class="{ active: selectedPlatform === '' }"
            @click="selectedPlatform = ''; handlePlatformChange()"
          >
            <span>全部</span>
            <span class="chip-count">{{ platforms.reduce((sum, p) => sum + p.count, 0) }}</span>
          </button>
          <button 
            v-for="platform in platforms" 
            :key="platform.platform"
            class="platform-chip" 
            :class="{ active: selectedPlatform === platform.platform }"
            @click="selectedPlatform = platform.platform; handlePlatformChange()"
          >
            <span>{{ platform.platform }}</span>
            <span class="chip-count">{{ platform.count }}</span>
          </button>
        </div>
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
    <Transition name="dialog-fade">
      <div class="m3-dialog-overlay" v-if="showEditRelationshipDialog" @click="showEditRelationshipDialog = false">
        <Transition name="dialog-scale">
          <div class="m3-dialog modern" @click.stop v-if="showEditRelationshipDialog">
            <div class="dialog-header">
              <div class="header-icon-wrapper">
                <span class="material-symbols-rounded header-icon">favorite</span>
              </div>
              <div class="header-content">
                <h3>编辑关系信息</h3>
                <p class="header-subtitle">调整与用户的关系描述</p>
              </div>
              <button class="m3-icon-button" @click="showEditRelationshipDialog = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            <div class="dialog-content">
              <div class="form-section">
                <div class="form-group">
                  <label class="m3-label">
                    <span class="material-symbols-rounded label-icon">favorite</span>
                    <span>关系分数</span>
                  </label>
                  <div class="score-input-container">
                    <input 
                      v-model.number="editForm.score" 
                      type="range" 
                      min="0" 
                      max="100" 
                      class="m3-slider"
                    />
                    <div class="score-value-display">
                      <span class="score-number">{{ editForm.score }}</span>
                      <span class="score-unit">分</span>
                    </div>
                  </div>
                  <div class="score-preview">
                    <div 
                      class="score-fill" 
                      :style="{ width: editForm.score + '%' }"
                    ></div>
                  </div>
                  <div class="score-hint">
                    <span>{{ getScoreDescription(editForm.score) }}</span>
                  </div>
                </div>
                <div class="form-group">
                  <label class="m3-label">
                    <span class="material-symbols-rounded label-icon">description</span>
                    <span>关系描述</span>
                  </label>
                  <textarea 
                    v-model="editForm.text" 
                    class="m3-textarea"
                    rows="4"
                    placeholder="描述你与这个用户的关系..."
                  ></textarea>
                  <div class="char-count" :class="{ warning: editForm.text.length > 200 }">
                    {{ editForm.text.length }} / 200
                  </div>
                </div>
              </div>
            </div>
            <div class="dialog-actions">
              <button class="m3-button text" @click="showEditRelationshipDialog = false">
                <span class="material-symbols-rounded">close</span>
                <span>取消</span>
              </button>
              <button class="m3-button filled" @click="saveRelationship" :disabled="saving">
                <span class="material-symbols-rounded">{{ saving ? 'progress_activity' : 'check' }}</span>
                <span>{{ saving ? '保存中...' : '保存' }}</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- 编辑印象对话框 -->
    <Transition name="dialog-fade">
      <div class="m3-dialog-overlay" v-if="showEditImpressionDialog" @click="showEditImpressionDialog = false">
        <Transition name="dialog-scale">
          <div class="m3-dialog modern large" @click.stop v-if="showEditImpressionDialog">
            <div class="dialog-header">
              <div class="header-icon-wrapper">
                <span class="material-symbols-rounded header-icon">psychology</span>
              </div>
              <div class="header-content">
                <h3>编辑印象</h3>
                <p class="header-subtitle">记录你对用户的印象和感受</p>
              </div>
              <button class="m3-icon-button" @click="showEditImpressionDialog = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            <div class="dialog-content">
              <div class="form-section">
                <div class="form-group">
                  <label class="m3-label">
                    <span class="material-symbols-rounded label-icon">article</span>
                    <span>详细印象</span>
                  </label>
                  <textarea 
                    v-model="editForm.impression" 
                    class="m3-textarea"
                    rows="6"
                    placeholder="详细描述你对这个用户的印象..."
                  ></textarea>
                  <div class="char-count">
                    {{ editForm.impression.length }} 字符
                  </div>
                </div>
                <div class="form-group">
                  <label class="m3-label">
                    <span class="material-symbols-rounded label-icon">sentiment_satisfied</span>
                    <span>简短印象</span>
                  </label>
                  <textarea 
                    v-model="editForm.shortImpression" 
                    class="m3-textarea short"
                    rows="3"
                    placeholder="用简短的话概括你的印象..."
                  ></textarea>
                  <div class="char-count" :class="{ warning: editForm.shortImpression.length > 100 }">
                    {{ editForm.shortImpression.length }} / 100
                  </div>
                </div>
              </div>
            </div>
            <div class="dialog-actions">
              <button class="m3-button text" @click="showEditImpressionDialog = false">
                <span class="material-symbols-rounded">close</span>
                <span>取消</span>
              </button>
              <button class="m3-button filled" @click="saveImpression" :disabled="saving">
                <span class="material-symbols-rounded">{{ saving ? 'progress_activity' : 'check' }}</span>
                <span>{{ saving ? '保存中...' : '保存' }}</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>

    <!-- 编辑记忆点对话框 -->
    <Transition name="dialog-fade">
      <div class="m3-dialog-overlay" v-if="showEditMemoryPointsDialog" @click="showEditMemoryPointsDialog = false">
        <Transition name="dialog-scale">
          <div class="m3-dialog modern extra-large" @click.stop v-if="showEditMemoryPointsDialog">
            <div class="dialog-header">
              <div class="header-icon-wrapper">
                <span class="material-symbols-rounded header-icon">bookmark</span>
              </div>
              <div class="header-content">
                <h3>编辑记忆点</h3>
                <p class="header-subtitle">管理与用户相关的重要记忆</p>
              </div>
              <button class="m3-icon-button" @click="showEditMemoryPointsDialog = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            <div class="dialog-content scrollable">
              <div class="form-section">
                <div class="section-header">
                  <div class="section-title">
                    <span class="material-symbols-rounded">collections_bookmark</span>
                    <h4>记忆点列表</h4>
                    <span class="m3-badge">{{ editForm.memoryPoints.length }}</span>
                  </div>
                  <button class="m3-button filled-tonal" @click="addMemoryPoint" type="button">
                    <span class="material-symbols-rounded">add</span>
                    <span>添加</span>
                  </button>
                </div>
                <div v-if="editForm.memoryPoints.length === 0" class="empty-hint modern">
                  <span class="material-symbols-rounded empty-icon">bookmark_border</span>
                  <p>暂无记忆点，点击「添加」按钮创建新记忆点</p>
                </div>
                <TransitionGroup name="list" tag="div" v-else class="memory-points-edit-list">
                  <div 
                    v-for="(point, index) in editForm.memoryPoints" 
                    :key="index"
                    class="memory-point-edit"
                  >
                    <div class="point-edit-header">
                      <div class="point-index">
                        <span class="material-symbols-rounded">bookmark</span>
                        <span>记忆点 #{{ index + 1 }}</span>
                      </div>
                      <div class="point-weight-control">
                        <label class="weight-label">重要度</label>
                        <div class="weight-slider-wrapper">
                          <input 
                            v-model.number="point.weight" 
                            type="range" 
                            min="0" 
                            max="1" 
                            step="0.1" 
                            class="m3-slider small"
                          />
                          <span class="weight-value">{{ (point.weight * 100).toFixed(0) }}%</span>
                        </div>
                      </div>
                      <button class="m3-icon-button error" @click="deleteMemoryPoint(index)" type="button" title="删除">
                        <span class="material-symbols-rounded">delete</span>
                      </button>
                    </div>
                    <div class="point-edit-body">
                      <label class="m3-label">
                        <span class="material-symbols-rounded label-icon">edit_note</span>
                        <span>记忆内容</span>
                      </label>
                      <textarea 
                        v-model="point.content" 
                        class="m3-textarea"
                        rows="4"
                        placeholder="输入这个记忆点的详细内容..."
                      ></textarea>
                      <div class="point-timestamp">
                        <span class="material-symbols-rounded">schedule</span>
                        <span>{{ formatDate(point.timestamp) }}</span>
                      </div>
                    </div>
                  </div>
                </TransitionGroup>
              </div>
            </div>
            <div class="dialog-actions">
              <button class="m3-button text" @click="showEditMemoryPointsDialog = false">
                <span class="material-symbols-rounded">close</span>
                <span>取消</span>
              </button>
              <button class="m3-button filled" @click="saveMemoryPoints" :disabled="saving">
                <span class="material-symbols-rounded">{{ saving ? 'progress_activity' : 'check' }}</span>
                <span>{{ saving ? '保存中...' : '保存' }}</span>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { 
  getPersonList,
  getPersonDetail, 
  updatePersonRelationship, 
  searchPerson,
  getPlatforms,
  type PersonDetail,
  type PersonCard,
  type PlatformInfo 
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

// 平台筛选相关
const platforms = ref<PlatformInfo[]>([])
const selectedPlatform = ref<string>('')
const platformsLoading = ref(false)

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
    const result = await getPersonList(currentPage.value, pageSize.value, selectedPlatform.value || undefined)
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

// 加载平台列表
const loadPlatforms = async () => {
  platformsLoading.value = true
  try {
    const result = await getPlatforms()
    if (result.success && result.data) {
      platforms.value = result.data.platforms
    }
  } catch (err) {
    console.error('加载平台列表失败:', err)
  } finally {
    platformsLoading.value = false
  }
}

// 平台变化时重新加载列表
const handlePlatformChange = async () => {
  currentPage.value = 1
  await loadPersonList()
}

// 页面加载时获取用户列表和平台列表
onMounted(() => {
  loadPersonList()
  loadPlatforms()
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

  console.log('[RelationshipView] 开始加载用户详情, personId:', currentPersonId.value)
  loading.value = true
  error.value = ''

  try {
    const result = await getPersonDetail(currentPersonId.value)
    console.log('[RelationshipView] 获取用户详情结果:', result)
    if (result.success && result.data) {
      console.log('[RelationshipView] 更新 personDetail.value:', result.data)
      console.log('[RelationshipView] 详细印象值:', result.data.impression)
      console.log('[RelationshipView] 简短印象值:', result.data.short_impression)
      console.log('[RelationshipView] 记忆点数量:', result.data.memory_points?.length)
      
      // 强制创建新对象以触发响应式更新
      personDetail.value = {
        basic_info: { ...result.data.basic_info },
        relationship: { ...result.data.relationship },
        impression: result.data.impression,
        short_impression: result.data.short_impression,
        memory_points: [...(result.data.memory_points || [])]
      }
      
      // 初始化编辑表单
      editForm.score = result.data.relationship.relationship_score * 100
      editForm.text = result.data.relationship.relationship_text || ''
      console.log('[RelationshipView] personDetail 已更新, 新值:', personDetail.value)
    } else {
      console.error('[RelationshipView] 加载用户详情失败:', result.error)
      error.value = result.error || '加载用户详情失败'
    }
  } catch (err) {
    console.error('[RelationshipView] 加载用户详情异常:', err)
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

  console.log('[RelationshipView] 开始保存关系信息, personId:', currentPersonId.value)
  console.log('[RelationshipView] 提交数据:', {
    relationship_score: editForm.score / 100,
    relationship_text: editForm.text
  })
  saving.value = true

  try {
    // 更新关系信息
    const result = await updatePersonRelationship(currentPersonId.value, {
      relationship_score: editForm.score / 100,
      relationship_text: editForm.text
    })

    console.log('[RelationshipView] 保存关系信息响应:', result)

    if (!result.success) {
      throw new Error(result.error || '更新关系信息失败')
    }

    // 检查返回的数据中的 success 字段
    if (result.data && !result.data.success) {
      throw new Error(result.data.message || '更新关系信息失败')
    }

    console.log('[RelationshipView] 关系信息保存成功，准备重新加载详情')
    await showSuccess('关系信息已更新')
    showEditRelationshipDialog.value = false
    
    console.log('[RelationshipView] 开始重新加载用户详情')
    await loadPersonDetail()
    console.log('[RelationshipView] 用户详情重新加载完成')
  } catch (err) {
    console.error('[RelationshipView] 保存关系信息失败:', err)
    await showError(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

// 保存印象
const saveImpression = async () => {
  if (!currentPersonId.value) return

  console.log('[RelationshipView] 开始保存印象, personId:', currentPersonId.value)
  console.log('[RelationshipView] 提交数据:', {
    impression: editForm.impression,
    short_impression: editForm.shortImpression
  })
  saving.value = true

  try {
    // 更新印象信息
    const { updatePersonImpression } = await import('@/api/relationship')
    
    const result = await updatePersonImpression(
      currentPersonId.value,
      editForm.impression,
      editForm.shortImpression
    )

    console.log('[RelationshipView] 保存印象响应:', result)

    if (!result.success) {
      throw new Error(result.error || '更新印象失败')
    }

    // 检查返回的数据中的 success 字段
    if (result.data && !result.data.success) {
      throw new Error(result.data.message || '更新印象失败')
    }

    console.log('[RelationshipView] 印象保存成功，准备重新加载详情')
    await showSuccess('印象已更新')
    showEditImpressionDialog.value = false
    
    console.log('[RelationshipView] 开始重新加载用户详情')
    await loadPersonDetail()
    console.log('[RelationshipView] 用户详情重新加载完成')
  } catch (err) {
    console.error('[RelationshipView] 保存印象失败:', err)
    await showError(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

// 保存记忆点
const saveMemoryPoints = async () => {
  if (!currentPersonId.value) return

  console.log('[RelationshipView] 开始保存记忆点, personId:', currentPersonId.value)
  console.log('[RelationshipView] 提交数据:', editForm.memoryPoints)
  saving.value = true

  try {
    // 更新记忆点
    const { updatePersonPoints } = await import('@/api/relationship')
    
    const result = await updatePersonPoints(
      currentPersonId.value,
      editForm.memoryPoints
    )

    console.log('[RelationshipView] 保存记忆点响应:', result)

    if (!result.success) {
      throw new Error(result.error || '更新记忆点失败')
    }

    // 检查返回的数据中的 success 字段
    if (result.data && !result.data.success) {
      throw new Error(result.data.message || '更新记忆点失败')
    }

    console.log('[RelationshipView] 记忆点保存成功，准备重新加载详情')
    await showSuccess('记忆点已更新')
    showEditMemoryPointsDialog.value = false
    
    console.log('[RelationshipView] 开始重新加载用户详情')
    await loadPersonDetail()
    console.log('[RelationshipView] 用户详情重新加载完成')
  } catch (err) {
    console.error('[RelationshipView] 保存记忆点失败:', err)
    await showError(err instanceof Error ? err.message : '更新失败')
  } finally {
    saving.value = false
  }
}

const formatDate = (dateStr?: string | number) => {
  if (!dateStr) return '未知'
  try {
    let date: Date
    // 如果是字符串类型的数字时间戳，先转换为数字
    if (typeof dateStr === 'string' && !isNaN(Number(dateStr))) {
      date = new Date(Number(dateStr) * 1000)  // Unix 时间戳（秒）转为毫秒
    } else if (typeof dateStr === 'number') {
      date = new Date(dateStr * 1000)  // Unix 时间戳（秒）转为毫秒
    } else {
      date = new Date(dateStr)
    }
    
    // 检查日期是否有效
    if (isNaN(date.getTime())) {
      return '未知'
    }
    
    return date.toLocaleString('zh-CN')
  } catch {
    return '未知'
  }
}

// 根据分数获取描述
const getScoreDescription = (score: number) => {
  if (score >= 90) return '🌟 亲密无间'
  if (score >= 80) return '💖 非常亲密'
  if (score >= 70) return '😊 关系良好'
  if (score >= 60) return '👍 比较熟悉'
  if (score >= 50) return '🙂 一般熟悉'
  if (score >= 40) return '😐 略有了解'
  if (score >= 30) return '🤔 初步认识'
  if (score >= 20) return '👋 刚刚见面'
  return '❓ 陌生人'
}

const isSearchFocused = ref(false)
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

/* 弹窗基础样式 */
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
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.24);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.dialog-header {
  padding: 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.dialog-content {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

.dialog-actions {
  padding: 16px 24px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 弹窗动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-scale-enter-active,
.dialog-scale-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dialog-scale-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

.dialog-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 列表动画 */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-leave-active {
  position: absolute;
  width: 100%;
}

/* 现代化弹窗样式 */
.m3-dialog.modern {
  max-width: 600px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-radius: 28px;
  overflow: hidden;
}

.m3-dialog.modern.large {
  max-width: 700px;
}

.m3-dialog.modern.extra-large {
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.m3-dialog.modern .dialog-header {
  background: linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-secondary-container) 100%);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: none;
}

.header-icon-wrapper {
  width: 56px;
  height: 56px;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.header-icon-wrapper .header-icon {
  font-size: 32px;
  color: var(--md-sys-color-primary);
}

.header-content {
  flex: 1;
}

.header-content h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--md-sys-color-on-primary-container);
}

.header-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.8;
}

.m3-dialog.modern .dialog-header .m3-icon-button {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
}

.dialog-content.scrollable {
  max-height: calc(90vh - 200px);
  overflow-y: auto;
}

.dialog-content.scrollable::-webkit-scrollbar {
  width: 8px;
}

.dialog-content.scrollable::-webkit-scrollbar-track {
  background: transparent;
}

.dialog-content.scrollable::-webkit-scrollbar-thumb {
  background: var(--md-sys-color-outline-variant);
  border-radius: 4px;
}

.dialog-content.scrollable::-webkit-scrollbar-thumb:hover {
  background: var(--md-sys-color-outline);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.m3-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.m3-label .label-icon {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

/* 滑块样式 */
.m3-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--md-sys-color-surface-container-highest);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.m3-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.m3-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.m3-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.m3-slider::-moz-range-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.m3-slider.small {
  height: 4px;
}

.m3-slider.small::-webkit-slider-thumb {
  width: 16px;
  height: 16px;
}

.m3-slider.small::-moz-range-thumb {
  width: 16px;
  height: 16px;
}

/* 分数输入容器 */
.score-input-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
}

.score-value-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  min-width: 80px;
  padding: 8px 16px;
  background: var(--md-sys-color-primary-container);
  border-radius: 12px;
  justify-content: center;
}

.score-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--md-sys-color-on-primary-container);
}

.score-unit {
  font-size: 14px;
  color: var(--md-sys-color-on-primary-container);
  opacity: 0.8;
}

.score-preview {
  height: 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.score-preview .score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--md-sys-color-tertiary) 0%, var(--md-sys-color-primary) 100%);
  border-radius: 6px;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.score-preview .score-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.score-hint {
  text-align: center;
  padding: 8px 16px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

/* 文本域样式 */
.m3-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.6;
  resize: vertical;
  transition: all 0.2s;
  outline: none;
}

.m3-textarea:focus {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container);
  box-shadow: 0 0 0 4px var(--md-sys-color-primary-container);
}

.m3-textarea::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.6;
}

.m3-textarea.short {
  min-height: 80px;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 0 4px;
}

.char-count.warning {
  color: var(--md-sys-color-error);
  font-weight: 600;
}

/* 记忆点部分样式 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title .material-symbols-rounded {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.section-title h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.empty-hint.modern {
  padding: 48px 24px;
  text-align: center;
  background: var(--md-sys-color-surface-container-low);
  border: 2px dashed var(--md-sys-color-outline-variant);
  border-radius: 16px;
}

.empty-hint.modern .empty-icon {
  font-size: 64px;
  color: var(--md-sys-color-outline);
  margin-bottom: 16px;
  display: block;
}

.empty-hint.modern p {
  margin: 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

.memory-points-edit-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

.memory-point-edit {
  padding: 20px;
  background: var(--md-sys-color-surface-container);
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  transition: all 0.2s;
}

.memory-point-edit:hover {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.point-edit-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.point-index {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.point-index .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.point-weight-control {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.weight-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.weight-slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-value {
  min-width: 48px;
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--md-sys-color-primary);
  padding: 4px 8px;
  background: var(--md-sys-color-primary-container);
  border-radius: 8px;
}

.point-edit-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 顶部栏 */
.top-bar {
  margin-bottom: 24px;
}

/* 搜索栏 */
.search-bar-container {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
}

.search-wrapper {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
  height: 48px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 24px;
  padding: 0 16px;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.search-wrapper.focused {
  background: var(--md-sys-color-surface);
  border-color: var(--md-sys-color-primary);
}

.search-icon {
  color: var(--md-sys-color-on-surface-variant);
  font-size: 24px;
  margin-right: 12px;
}

.search-input {
  flex: 1;
  border: none;
  background: transparent;
  color: var(--md-sys-color-on-surface);
  font-size: 16px;
  outline: none;
  padding: 0;
  height: 100%;
}

.clear-btn {
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px;
  margin-left: 8px;
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

/* 平台筛选 */
.platform-filter {
  margin-bottom: 24px;
  padding: 20px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 16px;
}

.filter-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-label .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.platform-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.platform-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--md-sys-color-surface-container-high);
  border: 2px solid transparent;
  border-radius: 20px;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.platform-chip:hover {
  background: var(--md-sys-color-surface-container-highest);
  border-color: var(--md-sys-color-outline);
}

.platform-chip.active {
  background: var(--md-sys-color-primary-container);
  border-color: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary-container);
}

.chip-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 8px;
  background: var(--md-sys-color-surface);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 700;
}

.platform-chip.active .chip-count {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
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

/* 弹窗动画 */
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-scale-enter-active,
.dialog-scale-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dialog-scale-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(20px);
}

.dialog-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 列表动画 */
.list-move,
.list-enter-active,
.list-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.list-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.list-leave-active {
  position: absolute;
  width: 100%;
}

/* 现代化弹窗样式 */
.m3-dialog.modern {
  max-width: 600px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  border-radius: 28px;
  overflow: hidden;
}

.m3-dialog.modern.large {
  max-width: 700px;
}

.m3-dialog.modern.extra-large {
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

.m3-dialog.modern .dialog-header {
  background: linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-secondary-container) 100%);
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  border: none;
}

.header-icon-wrapper {
  width: 56px;
  height: 56px;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.header-icon-wrapper .header-icon {
  font-size: 32px;
  color: var(--md-sys-color-primary);
}

.header-content {
  flex: 1;
}

.header-content h3 {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--md-sys-color-on-primary-container);
}

.header-subtitle {
  margin: 0;
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.8;
}

.m3-dialog.modern .dialog-header .m3-icon-button {
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
}

.dialog-content.scrollable {
  max-height: calc(90vh - 200px);
  overflow-y: auto;
}

.dialog-content.scrollable::-webkit-scrollbar {
  width: 8px;
}

.dialog-content.scrollable::-webkit-scrollbar-track {
  background: transparent;
}

.dialog-content.scrollable::-webkit-scrollbar-thumb {
  background: var(--md-sys-color-outline-variant);
  border-radius: 4px;
}

.dialog-content.scrollable::-webkit-scrollbar-thumb:hover {
  background: var(--md-sys-color-outline);
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.m3-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.m3-label .label-icon {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

/* 滑块样式 */
.m3-slider {
  width: 100%;
  height: 6px;
  border-radius: 3px;
  background: var(--md-sys-color-surface-container-highest);
  outline: none;
  -webkit-appearance: none;
  appearance: none;
  cursor: pointer;
}

.m3-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.m3-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.m3-slider::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  cursor: pointer;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.2s;
}

.m3-slider::-moz-range-thumb:hover {
  transform: scale(1.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.m3-slider.small {
  height: 4px;
}

.m3-slider.small::-webkit-slider-thumb {
  width: 16px;
  height: 16px;
}

.m3-slider.small::-moz-range-thumb {
  width: 16px;
  height: 16px;
}

/* 分数输入容器 */
.score-input-container {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 16px;
}

.score-value-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  min-width: 80px;
  padding: 8px 16px;
  background: var(--md-sys-color-primary-container);
  border-radius: 12px;
  justify-content: center;
}

.score-number {
  font-size: 28px;
  font-weight: 700;
  color: var(--md-sys-color-on-primary-container);
}

.score-unit {
  font-size: 14px;
  color: var(--md-sys-color-on-primary-container);
  opacity: 0.8;
}

.score-preview {
  height: 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.score-preview .score-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--md-sys-color-tertiary) 0%, var(--md-sys-color-primary) 100%);
  border-radius: 6px;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.score-preview .score-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.3) 50%, transparent 100%);
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.score-hint {
  text-align: center;
  padding: 8px 16px;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 500;
}

/* 文本域样式 */
.m3-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: 12px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
  font-family: inherit;
  line-height: 1.6;
  resize: vertical;
  transition: all 0.2s;
  outline: none;
}

.m3-textarea:focus {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container);
  box-shadow: 0 0 0 4px var(--md-sys-color-primary-container);
}

.m3-textarea::placeholder {
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.6;
}

.m3-textarea.short {
  min-height: 80px;
}

.char-count {
  text-align: right;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 0 4px;
}

.char-count.warning {
  color: var(--md-sys-color-error);
  font-weight: 600;
}

/* 记忆点部分样式 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-title .material-symbols-rounded {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.section-title h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.empty-hint.modern {
  padding: 48px 24px;
  text-align: center;
  background: var(--md-sys-color-surface-container-low);
  border: 2px dashed var(--md-sys-color-outline-variant);
  border-radius: 16px;
}

.empty-hint.modern .empty-icon {
  font-size: 64px;
  color: var(--md-sys-color-outline);
  margin-bottom: 16px;
  display: block;
}

.empty-hint.modern p {
  margin: 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

.memory-points-edit-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

.memory-point-edit {
  padding: 20px;
  background: var(--md-sys-color-surface-container);
  border: 2px solid var(--md-sys-color-outline-variant);
  border-radius: 16px;
  transition: all 0.2s;
}

.memory-point-edit:hover {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.point-edit-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.point-index {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

.point-index .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

.point-weight-control {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.weight-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface-variant);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.weight-slider-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weight-value {
  min-width: 48px;
  text-align: center;
  font-size: 13px;
  font-weight: 700;
  color: var(--md-sys-color-primary);
  padding: 4px 8px;
  background: var(--md-sys-color-primary-container);
  border-radius: 8px;
}

.point-edit-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.point-timestamp {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.point-timestamp .material-symbols-rounded {
  font-size: 16px;
}

.m3-icon-button.error {
  color: var(--md-sys-color-error);
}

.m3-icon-button.error:hover {
  background: var(--md-sys-color-error-container);
}

/* 对话框按钮样式增强 */
.m3-dialog.modern .dialog-actions {
  padding: 20px 24px;
  gap: 12px;
}

.m3-dialog.modern .dialog-actions .m3-button {
  gap: 8px;
}

.m3-dialog.modern .dialog-actions .m3-button .material-symbols-rounded {
  font-size: 20px;
}

.m3-button.filled-tonal {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border: none;
  padding: 10px 24px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.m3-button.filled-tonal:hover {
  background: var(--md-sys-color-secondary-container);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.m3-badge {
  padding: 4px 12px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.m3-badge.secondary {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
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
