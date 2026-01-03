<!--
  @file MainUpdateTab.vue
  @description 主程序更新标签页组件
  
  功能说明：
  1. 分支管理（切换分支）
  2. 检查主程序更新
  3. 执行更新操作
  4. 历史版本管理与回退
-->
<template>
  <div class="main-update-tab">
    <!-- 分支管理 -->
    <div class="m3-card branch-card">
      <div class="card-header">
        <span class="material-symbols-rounded">fork_right</span>
        <h3>分支管理</h3>
      </div>
      <!-- 加载中 -->
      <div v-if="initialLoading" class="loading-placeholder">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        <span>加载中...</span>
      </div>
      <!-- Git 不可用或没有分支 -->
      <div v-else-if="!gitEnvStatus?.git_available || (repoStatus?.available_branches?.length ?? 0) === 0" class="card-disabled-hint">
        <span class="material-symbols-rounded">info</span>
        <span>{{ !gitEnvStatus?.git_available ? 'Git 环境不可用' : '无可用分支' }}</span>
      </div>
      <div v-else class="branch-selector">
        <label class="m3-label">当前分支:</label>
        <div class="select-wrapper" ref="branchSelectWrapper">
          <div 
            class="m3-select-trigger" 
            :class="{ 'disabled': switching, 'active': showBranchDropdown }"
            @click="toggleBranchDropdown"
          >
            <span class="selected-value">{{ selectedBranch }}</span>
            <span class="material-symbols-rounded select-arrow" :class="{ 'rotated': showBranchDropdown }">
              arrow_drop_down
            </span>
          </div>
          
          <div v-if="showBranchDropdown" class="m3-select-dropdown m3-card">
            <div 
              v-for="branch in repoStatus?.available_branches ?? []" 
              :key="branch" 
              class="m3-select-option"
              :class="{ 'selected': branch === selectedBranch }"
              @click="selectBranch(branch)"
            >
              <span>{{ branch }}</span>
              <span v-if="branch === selectedBranch" class="material-symbols-rounded check-icon">check</span>
            </div>
          </div>
        </div>
        <span v-if="switching" class="switching-indicator">
          <span class="material-symbols-rounded spinning">progress_activity</span>
          切换中...
        </span>
      </div>
    </div>

    <!-- 更新检测 -->
    <div class="m3-card update-card">
      <div class="card-header">
        <span class="material-symbols-rounded">sync</span>
        <h3>更新检测</h3>
        <button 
          class="m3-button tonal" 
          @click="handleCheckUpdate"
          :disabled="initialLoading || checking || !gitEnvStatus?.git_available"
        >
          <span class="material-symbols-rounded" :class="{ spinning: checking }">
            {{ checking ? 'progress_activity' : 'refresh' }}
          </span>
          <span>{{ checking ? '检查中...' : '检查更新' }}</span>
        </button>
      </div>

      <!-- 加载中 -->
      <div v-if="initialLoading || checking" class="loading-placeholder">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        <span>{{ initialLoading ? '加载中...' : '检查更新中...' }}</span>
      </div>

      <!-- Git 不可用警告 -->
      <div v-else-if="gitEnvStatus && !gitEnvStatus.git_available" class="alert alert-warning">
        <span class="material-symbols-rounded">warning</span>
        <span>Git 不可用，请先在"Git 设置"中配置 Git 环境</span>
      </div>

      <!-- 非 Git 仓库警告 -->
      <div v-else-if="repoStatus && !repoStatus.is_git_repo" class="alert alert-warning">
        <span class="material-symbols-rounded">warning</span>
        <span>主程序目录不是 Git 仓库，无法使用自动更新功能</span>
      </div>

      <!-- 更新检查结果 -->
      <div v-else-if="updateInfo" class="update-result">
        <!-- 有更新 -->
        <div v-if="updateInfo.has_update" class="has-update">
          <div class="update-header">
            <div class="update-icon">
              <span class="material-symbols-rounded">auto_awesome</span>
            </div>
            <div class="update-title">
              <h4>发现新版本</h4>
              <p>有 {{ updateInfo.commits_behind }} 个新提交等待更新</p>
            </div>
          </div>

          <!-- 版本对比 -->
          <div class="version-compare">
            <div class="version-box version-current">
              <span class="version-tag">当前</span>
              <code>{{ updateInfo.current_commit || '未知' }}</code>
            </div>
            <span class="material-symbols-rounded arrow-icon">arrow_forward</span>
            <div class="version-box version-latest">
              <span class="version-tag">最新</span>
              <code>{{ updateInfo.remote_commit || '未知' }}</code>
            </div>
          </div>

          <!-- 更新日志 -->
          <div class="changelog" v-if="updateInfo.update_logs?.length">
            <h4>更新内容:</h4>
            <ul>
              <li v-for="(log, index) in updateInfo.update_logs.slice(0, 5)" :key="index">
                {{ log }}
              </li>
            </ul>
          </div>

          <!-- 更新按钮 -->
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
          <div class="up-to-date-info">
            <span>已是最新版本</span>
            <code v-if="updateInfo.current_commit">{{ updateInfo.current_commit }}</code>
          </div>
        </div>
      </div>

      <!-- 错误信息 -->
      <div v-if="error" class="error-message">
        <span class="material-symbols-rounded">error</span>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- 历史版本管理 -->
    <div class="m3-card backup-card">
      <div class="card-header">
        <span class="material-symbols-rounded">history</span>
        <h3>历史版本</h3>
        <button class="m3-icon-button" @click="loadBackups" :disabled="initialLoading || loadingBackups || !gitEnvStatus?.git_available">
          <span class="material-symbols-rounded" :class="{ spinning: loadingBackups }">refresh</span>
        </button>
      </div>

      <!-- 加载中 -->
      <div v-if="initialLoading || loadingBackups" class="loading-placeholder">
        <span class="material-symbols-rounded spinning">progress_activity</span>
        <span>加载中...</span>
      </div>
      <!-- Git 不可用或非仓库 -->
      <div v-else-if="!gitEnvStatus?.git_available || !repoStatus?.is_git_repo" class="card-disabled-hint">
        <span class="material-symbols-rounded">info</span>
        <span>{{ !gitEnvStatus?.git_available ? 'Git 环境不可用' : '当前目录非 Git 仓库' }}</span>
      </div>
      <div v-else-if="backups.length" class="backup-list">
        <div 
          v-for="backup in backups" 
          :key="backup.commit"
          class="backup-item"
          :class="{ 'is-current': backup.is_current }"
        >
          <div class="backup-info">
            <div class="backup-header">
              <code class="backup-commit">{{ backup.commit_short }}</code>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  getRepoStatus, 
  checkUpdates, 
  updateMainProgram, 
  switchBranch,
  rollbackVersion,
  getMainBackups,
  getMainCommitDetail,
  type RepoStatus,
  type UpdateCheck,
  type MainBackupInfo,
  type MainCommitDetail
} from '@/api/git_update'
import { getGitEnvStatus, type GitEnvStatus } from '@/api/git_env'
import { showSuccess, showError, showConfirm } from '@/utils/dialog'

// Props & Emits
const emit = defineEmits<{
  (e: 'update-complete', needsRestart: boolean): void
}>()

// State
const gitEnvStatus = ref<GitEnvStatus | null>(null)  // Git 环境状态
const repoStatus = ref<RepoStatus | null>(null)  // 仓库状态
const updateInfo = ref<UpdateCheck | null>(null)
const backups = ref<MainBackupInfo[]>([])
const selectedBranch = ref('')
const showBranchDropdown = ref(false)
const initialLoading = ref(true)  // 初始加载状态
const checking = ref(false)
const updating = ref(false)
const switching = ref(false)
const rolling = ref(false)
const loadingBackups = ref(false)
const loadingDetail = ref(false)
const error = ref('')

// 详情弹窗状态
const showDetailDialog = ref(false)
const commitDetail = ref<MainCommitDetail | null>(null)

const branchSelectWrapper = ref<HTMLElement | null>(null)

// 加载状态
async function loadStatus() {
  try {
    // 并行加载环境状态和仓库状态
    const [envResult, repoResult] = await Promise.all([
      getGitEnvStatus(),
      getRepoStatus()
    ])
    
    if (envResult.success && envResult.data) {
      gitEnvStatus.value = envResult.data
    }
    
    if (repoResult.success && repoResult.data) {
      repoStatus.value = repoResult.data
      if (repoResult.data.current_branch) {
        selectedBranch.value = repoResult.data.current_branch
      }
    }
  } catch (e) {
    console.error('加载状态失败:', e)
  }
}

// 切换分支下拉
function toggleBranchDropdown() {
  if (switching.value) return
  showBranchDropdown.value = !showBranchDropdown.value
}

// 选择分支
async function selectBranch(branch: string) {
  showBranchDropdown.value = false
  
  if (branch === selectedBranch.value) return
  
  const confirmed = await showConfirm({
    title: '切换分支',
    message: `确定要切换到分支 "${branch}" 吗？`,
    confirmText: '切换'
  })
  
  if (!confirmed) return
  
  switching.value = true
  
  try {
    const result = await switchBranch(branch)
    if (result.success && result.data?.success) {
      selectedBranch.value = branch
      showSuccess(result.data.message || '分支切换成功')
      emit('update-complete', true)
    } else {
      showError(result.data?.error || result.error || '切换分支失败')
    }
  } catch (e: any) {
    showError(e.message || '切换分支失败')
  } finally {
    switching.value = false
  }
}

// 检查更新
async function handleCheckUpdate() {
  checking.value = true
  error.value = ''
  updateInfo.value = null
  
  try {
    const result = await checkUpdates()
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
    message: '更新主程序后需要重启才能生效，是否继续？',
    confirmText: '更新'
  })
  
  if (!confirmed) return
  
  updating.value = true
  error.value = ''
  
  try {
    const result = await updateMainProgram(true, true, true)
    if (result.success && result.data?.success) {
      showSuccess(result.data.message || '更新成功')
      emit('update-complete', true)
      // 更新后刷新历史版本列表
      loadBackups()
    } else {
      showError(result.data?.error || result.error || '更新失败')
    }
  } catch (e: any) {
    showError(e.message || '更新失败')
  } finally {
    updating.value = false
  }
}

// 加载历史版本列表
async function loadBackups() {
  loadingBackups.value = true
  try {
    const result = await getMainBackups()
    if (result.success && result.data?.data) {
      backups.value = result.data.data
    }
  } catch (e) {
    console.error('加载历史版本列表失败:', e)
  } finally {
    loadingBackups.value = false
  }
}

// 回滚到指定提交
async function handleRollback(commitHash: string) {
  const commitShort = commitHash.substring(0, 7)
  const confirmed = await showConfirm({
    title: '确认回滚',
    message: `确定要回滚到版本 "${commitShort}" 吗？此操作将重置到该版本，回滚后需要重启程序。`,
    confirmText: '回滚'
  })
  
  if (!confirmed) return
  
  rolling.value = true
  
  try {
    const result = await rollbackVersion(commitHash)
    if (result.success && result.data?.success) {
      showSuccess(result.data.message || '回滚成功')
      emit('update-complete', true)
      // 刷新历史版本列表
      loadBackups()
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
    const result = await getMainCommitDetail(commitHash)
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

// 格式化时间
function formatTime(time: string | null | undefined): string {
  if (!time) return '-'
  try {
    return new Date(time).toLocaleString('zh-CN')
  } catch {
    return time
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

// 点击外部关闭下拉
function handleClickOutside(e: MouseEvent) {
  if (branchSelectWrapper.value && !branchSelectWrapper.value.contains(e.target as Node)) {
    showBranchDropdown.value = false
  }
}

// 初始化
onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  try {
    await loadStatus()
    // 并行加载历史版本
    loadBackups()
    // 加载完成后自动检查更新
    if (gitEnvStatus.value?.git_available && repoStatus.value?.is_git_repo) {
      handleCheckUpdate()
    }
  } finally {
    initialLoading.value = false
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadStatus()
    loadBackups()
    updateInfo.value = null
  }
})
</script>

<style scoped>
.main-update-tab {
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

/* 加载占位符 */
.loading-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 32px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 卡片禁用提示 */
.card-disabled-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

/* 分支选择器 */
.branch-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.m3-label {
  color: var(--md-sys-color-on-surface-variant);
}

.select-wrapper {
  position: relative;
  min-width: 200px;
}

.m3-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--md-sys-color-surface-container);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-select-trigger:hover:not(.disabled) {
  background: var(--md-sys-color-surface-container-high);
}

.m3-select-trigger.active {
  border-color: var(--md-sys-color-primary);
}

.m3-select-trigger.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.select-arrow {
  transition: transform 0.2s;
}

.select-arrow.rotated {
  transform: rotate(180deg);
}

.m3-select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  padding: 8px 0;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  box-shadow: var(--md-sys-elevation-2);
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
}

.m3-select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.m3-select-option:hover {
  background: var(--md-sys-color-surface-container-high);
}

.m3-select-option.selected {
  background: var(--md-sys-color-secondary-container);
}

.check-icon {
  font-size: 18px;
  color: var(--md-sys-color-primary);
}

.switching-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-primary);
  font-size: 14px;
}

/* 警告提示 */
.alert {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 12px;
}

.alert-warning {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

/* 更新结果 */
.update-result {
  padding: 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
}

.has-update .update-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.update-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  border-radius: 12px;
}

.update-icon .material-symbols-rounded {
  font-size: 28px;
  color: var(--md-sys-color-on-primary-container);
}

.update-title h4 {
  margin: 0 0 4px;
  font-size: 16px;
  color: var(--md-sys-color-on-surface);
}

.update-title p {
  margin: 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 版本对比 */
.version-compare {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--md-sys-color-surface);
  border-radius: 8px;
}

.version-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.version-tag {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.version-box code {
  font-family: monospace;
  font-size: 14px;
  padding: 4px 8px;
  background: var(--md-sys-color-surface-container);
  border-radius: 4px;
}

.arrow-icon {
  color: var(--md-sys-color-primary);
}

/* 更新日志 */
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

/* 已是最新 */
.up-to-date {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-success {
  font-size: 32px;
  color: var(--md-sys-color-primary);
}

.up-to-date-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.up-to-date-info code {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 错误信息 */
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

.m3-button.tonal {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 动画 */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 历史版本卡片 */
.backup-card .card-header {
  margin-bottom: 12px;
}

.m3-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: none;
  border-radius: 20px;
  background: transparent;
  cursor: pointer;
  transition: background 0.2s;
}

.m3-icon-button:hover:not(:disabled) {
  background: var(--md-sys-color-surface-container-high);
}

.m3-icon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.backup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

/* 美化滚动条 */
.backup-list::-webkit-scrollbar {
  width: 6px;
}

.backup-list::-webkit-scrollbar-track {
  background: var(--md-sys-color-surface-container);
  border-radius: 3px;
}

.backup-list::-webkit-scrollbar-thumb {
  background: var(--md-sys-color-outline);
  border-radius: 3px;
}

.backup-list::-webkit-scrollbar-thumb:hover {
  background: var(--md-sys-color-on-surface-variant);
}

.backup-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--md-sys-color-surface-container);
  border-radius: 12px;
  transition: background 0.2s;
}

.backup-item:hover {
  background: var(--md-sys-color-surface-container-high);
}

.backup-item.is-current {
  border: 1px solid var(--md-sys-color-primary);
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
}

.backup-commit {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  padding: 2px 6px;
  background: var(--md-sys-color-surface);
  border-radius: 4px;
}

.current-badge {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border-radius: 10px;
}

.backup-message {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.backup-meta {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.backup-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
  padding: 6px 12px;
}

.m3-button.text:hover:not(:disabled) {
  background: var(--md-sys-color-primary-container);
}

.no-backups {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 32px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 提交详情弹窗 */
.detail-dialog-overlay {
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
}

.detail-dialog {
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
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
  color: var(--md-sys-color-on-surface);
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.detail-row {
  display: flex;
  gap: 12px;
  padding: 6px 0;
}

.detail-label {
  color: var(--md-sys-color-on-surface-variant);
  min-width: 80px;
}

.detail-value {
  color: var(--md-sys-color-on-surface);
}

.detail-value code {
  font-family: 'Noto Sans SC', sans-serif;
  padding: 2px 6px;
  background: var(--md-sys-color-surface-container);
  border-radius: 4px;
}

.commit-message {
  margin: 0;
  color: var(--md-sys-color-on-surface);
}

.commit-body {
  margin: 0;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}

.files-list {
  max-height: 200px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  font-size: 13px;
}

.file-status {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  min-width: 40px;
  text-align: center;
}

.file-status.status-add {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.file-status.status-modify {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.file-status.status-delete {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.file-status.status-rename {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.file-path {
  color: var(--md-sys-color-on-surface);
  font-family: 'Roboto Mono', 'Noto Sans SC', monospace;
  word-break: break-all;
}

.files-more {
  padding: 8px 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 13px;
}
</style>
