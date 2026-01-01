<!--
  @file MainUpdateTab.vue
  @description 主程序更新标签页组件
  
  功能说明：
  1. 分支管理（切换分支）
  2. 检查主程序更新
  3. 执行更新操作
-->
<template>
  <div class="main-update-tab">
    <!-- 分支管理 -->
    <div v-if="gitStatus?.git_available && gitStatus?.available_branches?.length > 0" class="m3-card branch-card">
      <div class="card-header">
        <span class="material-symbols-rounded">fork_right</span>
        <h3>分支管理</h3>
      </div>
      <div class="branch-selector">
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
              v-for="branch in gitStatus.available_branches" 
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
          :disabled="checking || !gitStatus?.git_available"
        >
          <span class="material-symbols-rounded" :class="{ spinning: checking }">
            {{ checking ? 'progress_activity' : 'refresh' }}
          </span>
          <span>{{ checking ? '检查中...' : '检查更新' }}</span>
        </button>
      </div>

      <!-- Git 不可用警告 -->
      <div v-if="gitStatus && !gitStatus.git_available" class="alert alert-warning">
        <span class="material-symbols-rounded">warning</span>
        <span>Git 不可用，请先在"Git 设置"中配置 Git 环境</span>
      </div>

      <!-- 非 Git 仓库警告 -->
      <div v-else-if="gitStatus && !gitStatus.is_git_repo" class="alert alert-warning">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  getGitStatus, 
  checkUpdates, 
  updateMainProgram, 
  switchBranch,
  type GitStatus,
  type UpdateCheck
} from '@/api/git_update'
import { showSuccess, showError, showConfirm } from '@/utils/dialog'

// Props & Emits
const emit = defineEmits<{
  (e: 'update-complete', needsRestart: boolean): void
}>()

// State
const gitStatus = ref<GitStatus | null>(null)
const updateInfo = ref<UpdateCheck | null>(null)
const selectedBranch = ref('')
const showBranchDropdown = ref(false)
const checking = ref(false)
const updating = ref(false)
const switching = ref(false)
const error = ref('')

const branchSelectWrapper = ref<HTMLElement | null>(null)

// 加载 Git 状态
async function loadGitStatus() {
  try {
    const result = await getGitStatus()
    if (result.success && result.data) {
      gitStatus.value = result.data
      if (result.data.current_branch) {
        selectedBranch.value = result.data.current_branch
      }
    }
  } catch (e) {
    console.error('加载 Git 状态失败:', e)
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
    } else {
      showError(result.data?.error || result.error || '更新失败')
    }
  } catch (e: any) {
    showError(e.message || '更新失败')
  } finally {
    updating.value = false
  }
}

// 点击外部关闭下拉
function handleClickOutside(e: MouseEvent) {
  if (branchSelectWrapper.value && !branchSelectWrapper.value.contains(e.target as Node)) {
    showBranchDropdown.value = false
  }
}

// 初始化
onMounted(() => {
  loadGitStatus()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

// 暴露刷新方法
defineExpose({
  refresh: () => {
    loadGitStatus()
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
</style>
