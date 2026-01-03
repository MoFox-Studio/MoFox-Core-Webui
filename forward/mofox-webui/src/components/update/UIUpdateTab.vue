<!--
  @file UIUpdateTab.vue
  @description UI 更新标签页组件
  
  功能说明：
  1. 显示当前 UI 版本信息
  2. 检查 UI 更新
  3. 执行 UI 更新
  4. 管理 UI 备份和回滚
  
  注意：
  - 只有在 webui-dist 分支上才能更新
  - 非 Git 仓库时更新功能被禁用
-->
<template>
  <div class="ui-update-tab">
    <!-- 更新禁用提示 -->
    <div v-if="updateDisabled" class="m3-card disabled-card">
      <div class="disabled-content">
        <span class="material-symbols-rounded icon-warning">info</span>
        <div class="disabled-text">
          <h4>更新功能已禁用</h4>
          <p>{{ disabledReason }}</p>
        </div>
      </div>
    </div>

    <!-- 当前版本信息 (仅在更新未禁用时显示) -->
    <div v-if="!updateDisabled" class="m3-card version-card">
      <div class="card-header">
        <span class="material-symbols-rounded">web</span>
        <h3>当前版本</h3>
      </div>
      <div class="version-info" v-if="currentVersion">
        <div class="info-row">
          <span class="info-label">版本号:</span>
          <span class="info-value version">v{{ currentVersion.version }}</span>
        </div>
        <div class="info-row" v-if="currentVersion.build_time">
          <span class="info-label">构建时间:</span>
          <span class="info-value">{{ formatTime(currentVersion.build_time) }}</span>
        </div>
        <div class="info-row" v-if="currentVersion.branch">
          <span class="info-label">分支:</span>
          <span class="info-value branch">{{ currentVersion.branch }}</span>
        </div>
        <div class="info-row" v-if="currentVersion.commit">
          <span class="info-label">Commit:</span>
          <code class="info-value commit">{{ currentVersion.commit.substring(0, 8) }}</code>
        </div>
      </div>
      <div class="version-info" v-else>
        <p class="no-version">未检测到版本信息</p>
      </div>
    </div>

    <!-- 检查更新 (仅在更新未禁用时显示) -->
    <div v-if="!updateDisabled" class="m3-card update-check-card">
      <div class="card-header">
        <span class="material-symbols-rounded">sync</span>
        <h3>检查更新</h3>
        <button 
          class="m3-button tonal" 
          @click="handleCheckUpdate"
          :disabled="checking || updateDisabled"
        >
          <span class="material-symbols-rounded" :class="{ spinning: checking }">
            {{ checking ? 'progress_activity' : 'refresh' }}
          </span>
          <span>{{ checking ? '检查中...' : '检查更新' }}</span>
        </button>
      </div>

      <!-- 更新检查结果 -->
      <div v-if="statusInfo && !updateDisabled" class="update-result">
        <!-- 有更新 -->
        <div v-if="statusInfo.has_update" class="has-update">
          <div class="update-badge">
            <span class="material-symbols-rounded">auto_awesome</span>
            <span>发现新版本 v{{ statusInfo.latest_version }}</span>
          </div>
          
          <div class="changelog" v-if="statusInfo.changelog?.length">
            <h4>更新内容:</h4>
            <ul>
              <li v-for="(log, index) in statusInfo.changelog.slice(0, 10)" :key="index">
                {{ log }}
              </li>
            </ul>
          </div>
          
          <div class="update-actions">
            <button 
              class="m3-button filled"
              @click="handleUpdate"
              :disabled="updating"
            >
              <span class="material-symbols-rounded" :class="{ spinning: updating }">
                {{ updating ? 'progress_activity' : 'download' }}
              </span>
              <span>{{ updating ? '更新中...' : '立即更新' }}</span>
            </button>
          </div>
        </div>

        <!-- 已是最新 -->
        <div v-else class="up-to-date">
          <span class="material-symbols-rounded icon-success">check_circle</span>
          <span>已是最新版本</span>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="error" class="error-message">
        <span class="material-symbols-rounded">error</span>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- 历史版本管理 (仅在更新未禁用时显示) -->
    <div v-if="!updateDisabled" class="m3-card backup-card">
      <div class="card-header">
        <span class="material-symbols-rounded">history</span>
        <h3>历史版本</h3>
        <button class="m3-icon-button" @click="loadBackups" :disabled="loadingBackups">
          <span class="material-symbols-rounded" :class="{ spinning: loadingBackups }">refresh</span>
        </button>
      </div>

      <div class="backup-list" v-if="backups.length">
        <div 
          v-for="backup in backups" 
          :key="backup.commit"
          class="backup-item"
          :class="{ 'is-current': backup.is_current }"
        >
          <div class="backup-info">
            <div class="backup-header">
              <code class="backup-commit">{{ backup.commit_short }}</code>
              <span v-if="backup.version" class="backup-version">v{{ backup.version }}</span>
              <span v-if="backup.is_current" class="current-badge">当前</span>
            </div>
            <span class="backup-message">{{ backup.message }}</span>
            <span class="backup-meta">{{ formatTime(backup.timestamp) }}</span>
          </div>
          <div class="backup-actions">
            <button 
              class="m3-button text"
              @click="handleShowDetail(backup.commit)"
              :disabled="loadingDetail"
            >
              <span class="material-symbols-rounded">info</span>
              <span>详情</span>
            </button>
            <button 
              class="m3-button text" 
              @click="handleRollback(backup.commit)"
              :disabled="rolling || backup.is_current"
            >
              <span class="material-symbols-rounded">restore</span>
              <span>回滚</span>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="no-backups">
        <span class="material-symbols-rounded">history_toggle_off</span>
        <span>暂无历史版本</span>
      </div>
    </div>

    <!-- 提交详情弹窗 -->
    <Teleport to="body">
      <div v-if="showDetailDialog" class="detail-dialog-overlay" @click.self="showDetailDialog = false">
        <div class="detail-dialog">
          <div class="detail-header">
            <h3>版本详情</h3>
            <button class="m3-icon-button" @click="showDetailDialog = false">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
          <div class="detail-content" v-if="commitDetail">
            <div class="detail-section">
              <div class="detail-row">
                <span class="detail-label">Commit:</span>
                <code class="detail-value">{{ commitDetail.commit_short }}</code>
              </div>
              <div class="detail-row" v-if="commitDetail.version">
                <span class="detail-label">版本:</span>
                <span class="detail-value version-tag">v{{ commitDetail.version }}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">时间:</span>
                <span class="detail-value">{{ formatTime(commitDetail.timestamp) }}</span>
              </div>
              <div class="detail-row" v-if="commitDetail.author">
                <span class="detail-label">作者:</span>
                <span class="detail-value">{{ commitDetail.author }}</span>
              </div>
            </div>
            
            <div class="detail-section" v-if="commitDetail.message">
              <h4>提交消息</h4>
              <p class="commit-message">{{ commitDetail.message }}</p>
            </div>
            
            <div class="detail-section" v-if="commitDetail.body">
              <h4>更新内容</h4>
              <pre class="commit-body">{{ commitDetail.body }}</pre>
            </div>
            
            <div class="detail-section" v-if="commitDetail.files_changed?.length">
              <h4>修改文件 ({{ commitDetail.files_changed.length }})</h4>
              <div class="files-list">
                <div 
                  v-for="(file, index) in commitDetail.files_changed.slice(0, 20)" 
                  :key="index"
                  class="file-item"
                >
                  <span class="file-status" :class="getStatusClass(file.status)">{{ file.status }}</span>
                  <span class="file-path">{{ file.path }}</span>
                </div>
                <div v-if="commitDetail.files_changed.length > 20" class="files-more">
                  ... 及其他 {{ commitDetail.files_changed.length - 20 }} 个文件
                </div>
              </div>
            </div>
          </div>
          <div class="detail-content loading" v-else-if="loadingDetail">
            <span class="material-symbols-rounded spinning">progress_activity</span>
            <span>加载中...</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { 
  getUIStatus, 
  updateUI, 
  getUIBackups, 
  rollbackUI,
  getCommitDetail,
  type UIStatusResult,
  type UIBackupInfo,
  type UICommitDetail
} from '@/api/ui_update'
import { showSuccess, showError, showConfirm } from '@/utils/dialog'

// Props
const emit = defineEmits<{
  (e: 'update-complete', needsRestart: boolean): void
}>()

// State
const statusInfo = ref<UIStatusResult | null>(null)
const backups = ref<UIBackupInfo[]>([])
const checking = ref(false)
const updating = ref(false)
const rolling = ref(false)
const loadingBackups = ref(false)
const error = ref('')

// 详情弹窗状态
const showDetailDialog = ref(false)
const loadingDetail = ref(false)
const commitDetail = ref<UICommitDetail | null>(null)

// 计算当前版本（用于显示）
const currentVersion = computed(() => {
  if (!statusInfo.value) return null
  return {
    version: statusInfo.value.current_version || '未安装',
    build_time: null, // 从 changelog 或其他地方获取
    branch: statusInfo.value.current_branch,
    commit: statusInfo.value.current_commit
  }
})

// 计算是否禁用更新
const updateDisabled = computed(() => {
  if (statusInfo.value) {
    return statusInfo.value.update_enabled === false
  }
  return false
})

// 计算禁用原因
const disabledReason = computed(() => {
  if (!statusInfo.value) return ''
  
  // 优先使用后端返回的 message
  if (statusInfo.value.message) {
    return statusInfo.value.message
  }
  
  // 如果没有 message，根据 update_enabled 状态生成提示
  if (statusInfo.value.update_enabled === false) {
    const branch = statusInfo.value.current_branch || '未知'
    return `当前分支为 "${branch}"，更新功能已禁用。仅 webui-dist 分支支持自动更新。`
  }
  
  return ''
})

// 格式化时间
function formatTime(time: string | null): string {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return time
  }
}

// 加载 UI 状态（包含版本信息和更新检查）
async function loadStatus() {
  checking.value = true
  error.value = ''
  
  try {
    const result = await getUIStatus()
    if (result.success && result.data) {
      statusInfo.value = result.data
      if (!result.data.success) {
        error.value = result.data.error || '获取状态失败'
      }
    } else {
      error.value = result.error || '获取状态失败'
    }
  } catch (e: any) {
    error.value = e.message || '获取状态失败'
  } finally {
    checking.value = false
  }
}

// 检查更新（实际上就是重新加载状态）
async function handleCheckUpdate() {
  await loadStatus()
}

// 执行更新
async function handleUpdate() {
  const confirmed = await showConfirm({
    title: '确认更新',
    message: '更新 UI 将刷新页面，是否继续？',
    confirmText: '更新'
  })
  
  if (!confirmed) return
  
  updating.value = true
  error.value = ''
  
  try {
    const result = await updateUI()
    if (result.success && result.data?.success) {
      showSuccess(`更新成功！已更新到 ${result.data.version || '最新版本'}`)
      emit('update-complete', true)
    } else {
      showError(result.data?.error || result.error || '更新失败')
    }
  } catch (e: any) {
    showError(e.message || '更新失败')
  } finally {
    updating.value = false
  }
}

// 加载备份列表
async function loadBackups() {
  loadingBackups.value = true
  try {
    const result = await getUIBackups()
    if (result.success && result.data?.data) {
      backups.value = result.data.data
    }
  } catch (e) {
    console.error('加载备份列表失败:', e)
  } finally {
    loadingBackups.value = false
  }
}

// 回滚到指定提交
async function handleRollback(commitHash: string) {
  const commitShort = commitHash.substring(0, 7)
  const confirmed = await showConfirm({
    title: '确认回滚',
    message: `确定要回滚到版本 "${commitShort}" 吗？此操作将重置到该版本。`,
    confirmText: '回滚'
  })
  
  if (!confirmed) return
  
  rolling.value = true
  
  try {
    const result = await rollbackUI(commitHash)
    if (result.success && result.data?.success) {
      showSuccess(result.data.message || '回滚成功')
      emit('update-complete', true)
    } else {
      showError(result.data?.error || result.error || '回滚失败')
    }
  } catch (e: any) {
    showError(e.message || '回滚失败')
  } finally {
    rolling.value = false
  }
}

// 显示提交详情
async function handleShowDetail(commitHash: string) {
  showDetailDialog.value = true
  loadingDetail.value = true
  commitDetail.value = null
  
  try {
    const result = await getCommitDetail(commitHash)
    if (result.success && result.data) {
      commitDetail.value = result.data
    } else {
      showError(result.error || '获取详情失败')
      showDetailDialog.value = false
    }
  } catch (e: any) {
    showError(e.message || '获取详情失败')
    showDetailDialog.value = false
  } finally {
    loadingDetail.value = false
  }
}

// 获取文件状态样式类
function getStatusClass(status: string): string {
  const statusMap: Record<string, string> = {
    '新增': 'status-add',
    '修改': 'status-modify',
    '删除': 'status-delete',
    '重命名': 'status-rename'
  }
  return statusMap[status] || ''
}

// 初始化
onMounted(() => {
  loadStatus()
  loadBackups()
})

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadStatus()
    loadBackups()
  }
})
</script>

<style scoped>
.ui-update-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.m3-card {
  padding: 20px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 16px;
}

/* 禁用提示卡片 */
.disabled-card {
  background: var(--md-sys-color-tertiary-container);
}

.disabled-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.disabled-content .icon-warning {
  font-size: 28px;
  color: var(--md-sys-color-on-tertiary-container);
  flex-shrink: 0;
}

.disabled-text {
  flex: 1;
}

.disabled-text h4 {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-tertiary-container);
}

.disabled-text p {
  margin: 0;
  font-size: 14px;
  color: var(--md-sys-color-on-tertiary-container);
  opacity: 0.9;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.card-header h3 {
  flex: 1;
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.card-header .material-symbols-rounded {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

/* 版本信息 */
.version-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-label {
  color: var(--md-sys-color-on-surface-variant);
  min-width: 80px;
}

.info-value {
  color: var(--md-sys-color-on-surface);
}

.info-value.version {
  font-family: 'Noto Sans SC', sans-serif;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.info-value.branch {
  font-family: 'Noto Sans SC', sans-serif;
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
  padding: 2px 8px;
  border-radius: 4px;
}

.info-value.commit {
  font-family: 'Noto Sans SC', sans-serif;
  background: var(--md-sys-color-surface-container);
  padding: 2px 8px;
  border-radius: 4px;
}

.no-version {
  color: var(--md-sys-color-on-surface-variant);
  font-style: italic;
}

/* 更新检查结果 */
.update-result {
  margin-top: 16px;
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.has-update .update-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-primary);
  font-weight: 500;
  margin-bottom: 12px;
}

.changelog {
  margin-bottom: 16px;
}

.changelog h4 {
  font-size: 14px;
  margin: 0 0 8px;
  color: var(--md-sys-color-on-surface-variant);
}

.changelog ul {
  margin: 0;
  padding-left: 8px;
  list-style: none;
}

.changelog li {
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 4px;
  line-height: 1.5;
}

.update-actions {
  display: flex;
  justify-content: flex-end;
}

.up-to-date {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-on-surface);
}

.icon-success {
  color: var(--md-sys-color-primary);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
  border-radius: 8px;
}

/* 历史版本列表 */
.backup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  transition: background 0.2s;
}

.backup-item:hover {
  background: var(--md-sys-color-surface-container-high);
}

.backup-item.is-current {
  background: var(--md-sys-color-primary-container);
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.backup-header {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.backup-commit {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  background: var(--md-sys-color-surface-container-highest);
  padding: 2px 6px;
  border-radius: 4px;
  color: var(--md-sys-color-on-surface);
}

.backup-version {
  font-size: 12px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
}

.current-badge {
  font-size: 11px;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}

.backup-message {
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.backup-meta {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.no-backups {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 按钮样式 */
.m3-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover:not(:disabled) {
  box-shadow: var(--md-sys-elevation-1);
}

.m3-button.tonal {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.m3-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.m3-icon-button {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 20px;
  background: transparent;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
}

.m3-icon-button:hover:not(:disabled) {
  background: var(--md-sys-color-surface-container-highest);
}

/* 备份操作按钮组 */
.backup-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

/* 详情弹窗 */
.detail-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.detail-dialog {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { 
    opacity: 0;
    transform: translateY(20px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.detail-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.detail-content {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

.detail-content.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 200px;
  color: var(--md-sys-color-on-surface-variant);
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.detail-label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  min-width: 60px;
}

.detail-value {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.detail-value.version-tag {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  padding: 2px 8px;
  border-radius: 4px;
  font-weight: 500;
}

.commit-message {
  margin: 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.5;
}

.commit-body {
  margin: 0;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 200px;
  overflow-y: auto;
}

.files-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.file-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  font-weight: 500;
  min-width: 40px;
  text-align: center;
}

.file-status.status-add {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.file-status.status-modify {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.file-status.status-delete {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.file-status.status-rename {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.file-path {
  color: var(--md-sys-color-on-surface);
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.files-more {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  padding: 4px 0;
  text-align: center;
}

/* 动画 */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
