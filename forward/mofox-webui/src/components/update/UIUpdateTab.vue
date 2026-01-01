<!--
  @file UIUpdateTab.vue
  @description UI 更新标签页组件
  
  功能说明：
  1. 显示当前 UI 版本信息
  2. 检查 UI 更新
  3. 执行 UI 更新
  4. 管理 UI 备份和回滚
-->
<template>
  <div class="ui-update-tab">
    <!-- 当前版本信息 -->
    <div class="m3-card version-card">
      <div class="card-header">
        <span class="material-symbols-rounded">web</span>
        <h3>当前版本</h3>
      </div>
      <div class="version-info" v-if="currentVersion">
        <div class="info-row">
          <span class="info-label">版本号:</span>
          <code class="info-value">v{{ currentVersion.version }}</code>
        </div>
        <div class="info-row" v-if="currentVersion.build_time">
          <span class="info-label">构建时间:</span>
          <span class="info-value">{{ formatTime(currentVersion.build_time) }}</span>
        </div>
        <div class="info-row" v-if="currentVersion.branch">
          <span class="info-label">分支:</span>
          <span class="info-value">{{ currentVersion.branch }}</span>
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

    <!-- 检查更新 -->
    <div class="m3-card update-check-card">
      <div class="card-header">
        <span class="material-symbols-rounded">sync</span>
        <h3>检查更新</h3>
        <button 
          class="m3-button tonal" 
          @click="handleCheckUpdate"
          :disabled="checking"
        >
          <span class="material-symbols-rounded" :class="{ spinning: checking }">
            {{ checking ? 'progress_activity' : 'refresh' }}
          </span>
          <span>{{ checking ? '检查中...' : '检查更新' }}</span>
        </button>
      </div>

      <!-- 更新检查结果 -->
      <div v-if="updateInfo" class="update-result">
        <!-- 有更新 -->
        <div v-if="updateInfo.has_update" class="has-update">
          <div class="update-badge">
            <span class="material-symbols-rounded">auto_awesome</span>
            <span>发现新版本 v{{ updateInfo.latest_version }}</span>
          </div>
          
          <div class="changelog" v-if="updateInfo.changelog?.length">
            <h4>更新内容:</h4>
            <ul>
              <li v-for="(log, index) in updateInfo.changelog.slice(0, 5)" :key="index">
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

    <!-- 备份管理 -->
    <div class="m3-card backup-card">
      <div class="card-header">
        <span class="material-symbols-rounded">inventory_2</span>
        <h3>备份管理</h3>
        <button class="m3-icon-button" @click="loadBackups" :disabled="loadingBackups">
          <span class="material-symbols-rounded" :class="{ spinning: loadingBackups }">refresh</span>
        </button>
      </div>

      <div class="backup-list" v-if="backups.length">
        <div 
          v-for="backup in backups" 
          :key="backup.name"
          class="backup-item"
        >
          <div class="backup-info">
            <span class="backup-name">{{ backup.name }}</span>
            <span class="backup-meta">
              {{ formatTime(backup.timestamp) }}
              <span v-if="backup.size"> · {{ formatSize(backup.size) }}</span>
            </span>
          </div>
          <button 
            class="m3-button text" 
            @click="handleRollback(backup.name)"
            :disabled="rolling"
          >
            <span class="material-symbols-rounded">restore</span>
            <span>恢复</span>
          </button>
        </div>
      </div>
      <div v-else class="no-backups">
        <span class="material-symbols-rounded">folder_off</span>
        <span>暂无备份</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  getUIVersion, 
  checkUIUpdate, 
  updateUI, 
  getUIBackups, 
  rollbackUI,
  type UIVersionInfo,
  type UIUpdateCheckResult,
  type UIBackupInfo
} from '@/api/ui_update'
import { showSuccess, showError, showConfirm } from '@/utils/dialog'

// Props
const emit = defineEmits<{
  (e: 'update-complete', needsRestart: boolean): void
}>()

// State
const currentVersion = ref<UIVersionInfo | null>(null)
const updateInfo = ref<UIUpdateCheckResult | null>(null)
const backups = ref<UIBackupInfo[]>([])
const checking = ref(false)
const updating = ref(false)
const rolling = ref(false)
const loadingBackups = ref(false)
const error = ref('')

// 格式化时间
function formatTime(time: string | null): string {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return time
  }
}

// 格式化文件大小
function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 加载当前版本
async function loadCurrentVersion() {
  try {
    const result = await getUIVersion()
    if (result.success && result.data?.data) {
      currentVersion.value = result.data.data
    }
  } catch (e) {
    console.error('加载版本信息失败:', e)
  }
}

// 检查更新
async function handleCheckUpdate() {
  checking.value = true
  error.value = ''
  updateInfo.value = null
  
  try {
    const result = await checkUIUpdate()
    if (result.success && result.data) {
      updateInfo.value = result.data
      if (!result.data.success) {
        error.value = result.data.error || '检查更新失败'
      }
    } else {
      error.value = result.error || '检查更新失败'
    }
  } catch (e: any) {
    error.value = e.message || '检查更新失败'
  } finally {
    checking.value = false
  }
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

// 回滚
async function handleRollback(backupName: string) {
  const confirmed = await showConfirm({
    title: '确认回滚',
    message: `确定要恢复到备份 "${backupName}" 吗？`,
    confirmText: '恢复'
  })
  
  if (!confirmed) return
  
  rolling.value = true
  
  try {
    const result = await rollbackUI(backupName)
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

// 初始化
onMounted(() => {
  loadCurrentVersion()
  loadBackups()
})

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadCurrentVersion()
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

.info-value.commit {
  font-family: monospace;
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
  padding-left: 20px;
}

.changelog li {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 4px;
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

/* 备份列表 */
.backup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
}

.backup-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.backup-name {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
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

/* 动画 */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
