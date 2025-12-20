<template>
  <div class="git-update-view">
    <!-- 非 Git 仓库错误提示 -->
    <div v-if="gitStatus && !gitStatus.is_git_repo" class="not-git-repo-error">
      <div class="error-icon">
        <span class="material-symbols-rounded">error</span>
      </div>
      <h2>无法使用更新功能</h2>
      <p>主程序目录不是 Git 仓库，无法使用自动更新功能。</p>
      <p class="hint">如需使用此功能，请通过 Git 克隆项目仓库。</p>
      <button class="m3-button tonal" @click="$router.back()">
        <span class="material-symbols-rounded">arrow_back</span>
        <span>返回</span>
      </button>
    </div>

    <!-- Git 仓库正常界面 -->
    <template v-else>
      <!-- 头部 -->
      <div class="page-header">
        <div class="header-content">
          <div class="header-icon">
            <span class="material-symbols-rounded">fork_right</span>
          </div>
          <div class="header-text">
            <h1>MoFox-Bot主程序更新</h1>
            <p>管理和更新您的MoFox-Bot</p>
          </div>
        </div>
        <button class="m3-icon-button" @click="handleRefresh" :disabled="checking || loading">
          <span class="material-symbols-rounded" :class="{ spinning: checking || loading }">refresh</span>
        </button>
      </div>

      <!-- 系统信息条 -->
      <div v-if="gitStatus" class="m3-card info-bar">
        <div class="info-item">
          <span class="material-symbols-rounded">fork_right</span>
          <span>Git 仓库</span>
        </div>
        <div class="info-item">
          <span class="material-symbols-rounded" :class="gitStatus.git_available ? 'icon-success' : 'icon-warning'">
            {{ gitStatus.git_available ? 'check_circle' : 'error' }}
          </span>
          <span>{{ gitStatus.git_available ? 'Git 可用' : 'Git 未安装' }}</span>
        </div>
        <div v-if="gitStatus.current_branch" class="info-item">
          <span class="material-symbols-rounded">fork_right</span>
          <span>分支: {{ gitStatus.current_branch }}</span>
        </div>
        <div class="info-item">
          <span class="material-symbols-rounded">desktop_windows</span>
          <span>{{ gitStatus.system_os }}</span>
        </div>
      </div>

      <!-- 分支切换区域 -->
      <div v-if="gitStatus && gitStatus.git_available && gitStatus.available_branches.length > 0" class="m3-card branch-section">
        <div class="branch-header">
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
              <span class="material-symbols-rounded select-arrow" :class="{ 'rotated': showBranchDropdown }">arrow_drop_down</span>
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

      <!-- Git 路径管理 -->
      <div v-if="gitStatus && gitStatus.git_available" class="m3-card git-path-info">
        <div class="path-header">
          <span class="material-symbols-rounded">folder</span>
          <h3>Git 路径</h3>
        </div>
        <div class="path-content">
          <div class="path-display">
            <span class="path-label">当前路径:</span>
            <code class="path-value">{{ gitStatus.git_path || '未知' }}</code>
            <span class="m3-badge" :class="`source-${gitStatus.git_source}`">
              {{ gitStatus.git_source === 'custom' ? '自定义' : 
                 gitStatus.git_source === 'portable' ? '便携版' : 
                 gitStatus.git_source === 'system' ? '系统' : '未知' }}
            </span>
          </div>
          <div class="path-actions">
            <button class="m3-button tonal small" @click="openSetPathModal">
              <span class="material-symbols-rounded">edit</span>
              设置路径
            </button>
            <button v-if="gitStatus.git_source === 'custom'" 
                    class="m3-button text error small" 
                    @click="handleClearGitPath">
              <span class="material-symbols-rounded">close</span>
              清除自定义
            </button>
          </div>
        </div>
      </div>

      <!-- Git 未安装警告 -->
      <div v-if="gitStatus && !gitStatus.git_available" class="m3-card alert alert-warning">
        <span class="material-symbols-rounded alert-icon">warning</span>
        <div class="alert-content">
          <strong>需要安装 Git</strong>
          <p>需要安装 Git 才能进行更新操作</p>
        </div>
        <button 
          v-if="gitStatus.system_os === 'Windows'" 
          class="m3-button filled warning"
          @click="installGitAuto"
          :disabled="installing"
        >
          {{ installing ? '安装中...' : '立即安装' }}
        </button>
        <button v-else class="m3-button filled warning" @click="showInstallGuide = true">
          安装指南
        </button>
      </div>

    <!-- 主卡片 -->
    <div v-if="canCheckUpdate" class="m3-card main-card">
      <!-- 加载状态 -->
      <div v-if="checking" class="checking-state">
        <span class="material-symbols-rounded spinning spinner-large">progress_activity</span>
        <p>正在检查更新...</p>
      </div>

      <!-- 更新信息 -->
      <div v-else-if="updateInfo" class="update-content">
        <!-- 有更新 -->
        <div v-if="updateInfo.has_update" class="has-update">
          <div class="update-header">
            <div class="update-icon">
              <span class="material-symbols-rounded">auto_awesome</span>
            </div>
            <div class="update-title">
              <h2>发现新版本</h2>
              <p>有可用的更新等待安装</p>
            </div>
          </div>

          <!-- 版本信息 -->
          <div class="version-compare">
            <div class="version-box version-current">
              <span class="version-tag">当前</span>
              <code>{{ updateInfo.current_commit?.substring(0, 8) || '未知' }}</code>
            </div>
            <span class="material-symbols-rounded arrow-icon">arrow_forward</span>
            <div class="version-box version-latest">
              <span class="version-tag">最新</span>
              <code>{{ updateInfo.remote_commit?.substring(0, 8) || '未知' }}</code>
            </div>
          </div>

          <!-- 提交信息 -->
          <div v-if="updateInfo.commits_behind" class="commits-badge">
            <span class="material-symbols-rounded">commit</span>
            <span>{{ updateInfo.commits_behind }} 个新提交</span>
            <span v-if="updateInfo.branch" class="branch-badge">
              <span class="material-symbols-rounded">fork_right</span>
              {{ updateInfo.branch }}
            </span>
          </div>

          <!-- 更新日志 -->
          <div v-if="updateInfo.update_logs && updateInfo.update_logs.length > 0" class="changelog">
            <div class="changelog-header">
              <span class="material-symbols-rounded">list</span>
              <h3>更新内容</h3>
            </div>
            <ul class="changelog-list">
              <li v-for="(log, index) in updateInfo.update_logs" :key="index">
                <span class="material-symbols-rounded bullet">circle</span>
                <span>{{ log }}</span>
              </li>
            </ul>
          </div>

          <!-- 更新选项 -->
          <div class="update-options">
            <label class="m3-checkbox-wrapper option-item">
              <input type="checkbox" v-model="updateOptions.stashLocal" />
              <span class="checkmark"></span>
              <div class="option-text">
                <span class="option-label">暂存本地修改</span>
                <span class="option-desc">保护您的本地更改</span>
              </div>
            </label>
            <label class="m3-checkbox-wrapper option-item">
              <input type="checkbox" v-model="updateOptions.createBackup" />
              <span class="checkmark"></span>
              <div class="option-text">
                <span class="option-label">创建备份点</span>
                <span class="option-desc">可随时回滚</span>
              </div>
            </label>
            <label class="m3-checkbox-wrapper option-item">
              <input type="checkbox" v-model="updateOptions.force" />
              <span class="checkmark"></span>
              <div class="option-text">
                <span class="option-label">强制更新</span>
                <span class="option-desc">覆盖所有本地修改</span>
              </div>
            </label>
          </div>

          <!-- 更新按钮 -->
          <button 
            class="m3-button filled large btn-update"
            @click="performUpdate"
            :disabled="updating"
          >
            <span class="material-symbols-rounded" :class="{ spinning: updating }">
              {{ updating ? 'progress_activity' : 'download' }}
            </span>
            <span>{{ updating ? '正在更新...' : '立即更新' }}</span>
          </button>
        </div>

        <!-- 无更新 -->
        <div v-else class="no-update">
          <div class="no-update-icon">
            <span class="material-symbols-rounded">check_circle</span>
          </div>
          <h2>已是最新版本</h2>
          <p>您的MoFox-Bot已经是最新版本</p>
          <code class="current-version">
            {{ updateInfo.current_commit?.substring(0, 8) || '未知' }}
          </code>
          
          <!-- 最近更新信息 -->
          <div v-if="lastUpdateResult && lastUpdateResult.success" class="last-update-info">
            <div class="update-time">
              <span class="material-symbols-rounded">schedule</span>
              <span>上次更新成功</span>
            </div>
            <button v-if="lastUpdateResult.backup_commit" class="m3-button tonal" @click="rollback(lastUpdateResult.backup_commit!)">
              <span class="material-symbols-rounded">undo</span>
              <span>回滚到上一版本</span>
            </button>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="updateError" class="error-message">
          <span class="material-symbols-rounded">error</span>
          <p>{{ updateError }}</p>
        </div>
      </div>

      <!-- 初始状态 -->
      <div v-else class="initial-state">
        <div class="initial-icon">
          <span class="material-symbols-rounded">search</span>
        </div>
        <h2>检查更新</h2>
        <p>点击按钮检查是否有可用的更新</p>
        <button class="m3-button filled" @click="checkForUpdates">
          <span class="material-symbols-rounded">search</span>
          <span>检查更新</span>
        </button>
      </div>
    </div>

    <!-- 成功弹窗 -->
    <Transition name="dialog">
      <div v-if="showSuccessModal" class="m3-dialog-overlay" @click.self="showSuccessModal = false">
        <div class="m3-dialog success-modal">
          <div class="success-icon-wrapper">
            <span class="material-symbols-rounded success-icon">check_circle</span>
          </div>
          <h2>更新成功</h2>
          <p>{{ lastUpdateResult?.message || 'MoFox-Bot已成功更新到最新版本' }}</p>
          
          <div v-if="lastUpdateResult?.updated_files && lastUpdateResult.updated_files.length > 0" class="updated-summary">
            <span class="material-symbols-rounded">file_present</span>
            <span>已更新 {{ lastUpdateResult.updated_files.length }} 个文件</span>
          </div>

          <div class="modal-actions">
            <button class="m3-button filled" @click="closeSuccessModal">
              <span class="material-symbols-rounded">check</span>
              <span>确定</span>
            </button>
            <button v-if="lastUpdateResult?.backup_commit" class="m3-button tonal" @click="rollbackFromModal">
              <span class="material-symbols-rounded">undo</span>
              <span>回滚</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Git 安装指南弹窗 -->
    <Transition name="dialog">
      <div v-if="showInstallGuide" class="m3-dialog-overlay" @click.self="showInstallGuide = false">
        <div class="m3-dialog guide-modal">
          <div class="dialog-header">
            <h3>Git 安装指南</h3>
            <button class="m3-icon-button" @click="showInstallGuide = false">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
          <div class="dialog-body center-content">
            <div class="guide-icon">
              <span class="material-symbols-rounded">menu_book</span>
            </div>
            <p>请访问 Git 官网下载并安装适合您系统的版本</p>
            <a href="https://git-scm.com/downloads" target="_blank" class="m3-button filled guide-link">
              <span class="material-symbols-rounded">open_in_new</span>
              <span>git-scm.com/downloads</span>
            </a>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 设置 Git 路径弹窗 -->
    <Transition name="dialog">
      <div v-if="showSetPathModal" class="m3-dialog-overlay" @click.self="closeSetPathModal">
        <div class="m3-dialog path-modal">
          <div class="dialog-header">
            <h3>设置 Git 路径</h3>
            <button class="m3-icon-button" @click="closeSetPathModal">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
          <div class="dialog-body">
            <div class="modal-icon">
              <span class="material-symbols-rounded">folder</span>
            </div>
            <p class="modal-desc">请输入 Git 可执行文件的完整路径，或者选择自动下载安装</p>
            
            <div class="path-input-group">
              <label class="m3-label" for="git-path-input">Git 可执行文件路径</label>
              <input 
                id="git-path-input"
                v-model="customGitPath" 
                type="text" 
                class="m3-input"
                placeholder="例如: C:\Program Files\Git\bin\git.exe"
                :disabled="settingPath"
                @keyup.enter="handleSetGitPath"
              />
              <span class="input-hint">
                Windows: git.exe | Linux/macOS: git
              </span>
            </div>

            <div v-if="updateError" class="error-message">
              <span class="material-symbols-rounded">error</span>
              <p>{{ updateError }}</p>
            </div>
          </div>
          <div class="dialog-actions">
            <button class="m3-button text" @click="closeSetPathModal">
              取消
            </button>
            <button 
              class="m3-button tonal" 
              @click="handleAutoDetectGit"
              :disabled="installing"
            >
              <span class="material-symbols-rounded" :class="{ spinning: installing }">
                {{ installing ? 'progress_activity' : 'search' }}
              </span>
              {{ installing ? '处理中...' : '自动识别' }}
            </button>
            <button 
              class="m3-button filled" 
              @click="handleSetGitPath"
              :disabled="!customGitPath.trim() || settingPath"
            >
              <span class="material-symbols-rounded" :class="{ spinning: settingPath }">
                {{ settingPath ? 'progress_activity' : 'check' }}
              </span>
              {{ settingPath ? '验证中...' : '确认设置' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast 通知 -->
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div 
          v-for="toast in toasts" 
          :key="toast.id" 
          class="m3-snackbar"
          :class="toast.type"
        >
          <span class="material-symbols-rounded">
            {{ toast.type === 'success' ? 'check_circle' : 
               toast.type === 'error' ? 'error' : 
               toast.type === 'warning' ? 'warning' : 'info' }}
          </span>
          <span>{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { getGitStatus, installGit, checkUpdates, updateMainProgram, rollbackVersion, switchBranch, setGitPath, clearGitPath } from '@/api/git_update'
import type { GitStatus, UpdateCheck, UpdateResult } from '@/api/git_update'
import { globalUpdateInfo, clearUpdateStatus } from '@/utils/updateChecker'
import { showConfirm } from '@/utils/dialog'

const loading = ref(true)
const checking = ref(false)
const installing = ref(false)
const updating = ref(false)
const switching = ref(false)

const gitStatus = ref<GitStatus | null>(null)
const updateInfo = ref<UpdateCheck | null>(null)
const updateError = ref<string | null>(null)
const lastUpdateResult = ref<UpdateResult | null>(null)
const showInstallGuide = ref(false)
const showSuccessModal = ref(false)
const showSetPathModal = ref(false)
const selectedBranch = ref<string>('')
const customGitPath = ref<string>('')
const settingPath = ref(false)
const showBranchDropdown = ref(false)
const branchSelectWrapper = ref<HTMLElement | null>(null)

// Toast 通知
interface Toast {
  id: number
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  duration: number
}

const toasts = ref<Toast[]>([])
let toastId = 0

function showToast(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info', duration = 3000) {
  const id = toastId++
  toasts.value.push({ id, type, message, duration })
  
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, duration)
}

function toggleBranchDropdown() {
  if (switching.value) return
  showBranchDropdown.value = !showBranchDropdown.value
}

function selectBranch(branch: string) {
  if (branch === selectedBranch.value) {
    showBranchDropdown.value = false
    return
  }
  selectedBranch.value = branch
  showBranchDropdown.value = false
  handleBranchChange()
}

function handleClickOutside(event: MouseEvent) {
  if (branchSelectWrapper.value && !branchSelectWrapper.value.contains(event.target as Node)) {
    showBranchDropdown.value = false
  }
}

const updateOptions = ref({
  force: false,
  stashLocal: true,
  createBackup: true
})

// 监听 gitStatus 变化，更新选中的分支
watch(() => gitStatus.value?.current_branch, (newBranch) => {
  if (newBranch) {
    selectedBranch.value = newBranch
  }
}, { immediate: true })

// 计算属性：是否可以检查更新
const canCheckUpdate = computed(() => {
  if (!gitStatus.value) return false
  // 必须是 Git 仓库且 Git 可用
  return gitStatus.value.is_git_repo && gitStatus.value.git_available
})

async function refreshGitStatus() {
  loading.value = true
  try {
    const response = await getGitStatus()
    if (response.success && response.data) {
      gitStatus.value = response.data
    }
  } catch (error) {
    console.error('获取 Git 状态失败:', error)
  } finally {
    loading.value = false
  }
}

async function installGitAuto() {
  installing.value = true
  try {
    const response = await installGit()
    if (response.success && response.data) {
      showSuccessModal.value = true
      await refreshGitStatus()
    } else {
      updateError.value = response.error || 'Git 安装失败'
    }
  } catch (error) {
    updateError.value = 'Git 安装失败'
    console.error(error)
  } finally {
    installing.value = false
  }
}

async function checkForUpdates() {
  checking.value = true
  updateError.value = null
  try {
    const response = await checkUpdates()
    if (response.success && response.data) {
      updateInfo.value = response.data
      if (!response.data.success) {
        updateError.value = response.data.error || '检查更新失败'
      }
    } else {
      updateError.value = response.error || '检查更新失败'
    }
  } catch (error) {
    updateError.value = '检查更新失败'
    console.error(error)
  } finally {
    checking.value = false
  }
}

async function performUpdate() {
  updating.value = true
  updateError.value = null
  try {
    const response = await updateMainProgram(
      updateOptions.value.force,
      updateOptions.value.stashLocal,
      updateOptions.value.createBackup
    )
    
    if (response.success && response.data && response.data.success) {
      lastUpdateResult.value = response.data
      updateInfo.value = null
      showSuccessModal.value = true
      // 重新检查状态
      await refreshGitStatus()
    } else {
      updateError.value = response.error || response.data?.error || '更新失败'
    }
  } catch (error) {
    updateError.value = '更新失败'
    console.error(error)
  } finally {
    updating.value = false
  }
}

async function rollback(commitHash: string) {
  const confirmed = await showConfirm({
    title: '回滚版本',
    message: `确定要回滚到版本 ${commitHash.substring(0, 8)} 吗？`,
    type: 'warning',
    confirmText: '确定回滚',
    cancelText: '取消'
  })
  
  if (!confirmed) {
    return
  }
  
  try {
    const response = await rollbackVersion(commitHash)
    if (response.success && response.data && response.data.success) {
      lastUpdateResult.value = null
      showSuccessModal.value = true
      await refreshGitStatus()
      await checkForUpdates()
    } else {
      updateError.value = response.error || response.data?.error || '回滚失败'
    }
  } catch (error) {
    updateError.value = '回滚失败'
    console.error(error)
  }
}

function closeSuccessModal() {
  showSuccessModal.value = false
  checkForUpdates()
}

function rollbackFromModal() {
  showSuccessModal.value = false
  if (lastUpdateResult.value?.backup_commit) {
    rollback(lastUpdateResult.value.backup_commit)
  }
}

// 切换分支
async function handleBranchChange() {
  if (!selectedBranch.value || selectedBranch.value === gitStatus.value?.current_branch) {
    return
  }

  const confirmed = await showConfirm({
    title: '切换分支',
    message: `确定要切换到分支 ${selectedBranch.value} 吗？\n\n切换分支后将拉取最新代码。`,
    type: 'warning',
    confirmText: '确定切换',
    cancelText: '取消'
  })
  
  if (!confirmed) {
    // 用户取消，恢复选择
    selectedBranch.value = gitStatus.value?.current_branch || ''
    return
  }

  switching.value = true
  updateError.value = null
  
  try {
    const response = await switchBranch(selectedBranch.value)
    if (response.success && response.data && response.data.success) {
      showSuccessModal.value = true
      lastUpdateResult.value = {
        success: true,
        message: response.data.message
      }
      // 刷新状态
      await refreshGitStatus()
      // 检查新分支的更新
      await checkForUpdates()
    } else {
      updateError.value = response.error || response.data?.error || '切换分支失败'
      // 恢复选择
      selectedBranch.value = gitStatus.value?.current_branch || ''
    }
  } catch (error) {
    updateError.value = '切换分支失败'
    console.error(error)
    // 恢复选择
    selectedBranch.value = gitStatus.value?.current_branch || ''
  } finally {
    switching.value = false
  }
}

// 刷新按钮 - 同时刷新状态和检查更新
async function handleRefresh() {
  await refreshGitStatus()
  if (canCheckUpdate.value) {
    await checkForUpdates()
  }
}

// 打开设置路径弹窗
function openSetPathModal() {
  showSetPathModal.value = true
  customGitPath.value = gitStatus.value?.git_path || ''
}

// 关闭设置路径弹窗
function closeSetPathModal() {
  showSetPathModal.value = false
  customGitPath.value = ''
  updateError.value = null
}

// 设置自定义 Git 路径
async function handleSetGitPath() {
  if (!customGitPath.value.trim()) {
    updateError.value = '请输入 Git 可执行文件路径'
    return
  }

  settingPath.value = true
  updateError.value = null

  try {
    const response = await setGitPath(customGitPath.value)
    if (response.success && response.data) {
      closeSetPathModal()
      await refreshGitStatus()
      showToast(`Git 路径设置成功！版本: ${response.data.git_version}`, 'success')
    } else {
      updateError.value = response.data?.error || '设置失败'
    }
  } catch (error: any) {
    updateError.value = error?.message || '设置失败'
    console.error(error)
  } finally {
    settingPath.value = false
  }
}

// 清除自定义路径
async function handleClearGitPath() {
  const confirmed = await showConfirm({
    title: '清除自定义路径',
    message: '确定要清除自定义 Git 路径吗？\n\n系统将重新自动检测 Git。',
    type: 'warning',
    confirmText: '确定清除',
    cancelText: '取消'
  })
  
  if (!confirmed) {
    return
  }

  try {
    const response = await clearGitPath()
    if (response.success) {
      await refreshGitStatus()
      showToast('已清除自定义 Git 路径', 'success')
    }
  } catch (error: any) {
    showToast(`清除失败: ${error?.message || '未知错误'}`, 'error')
    console.error(error)
  }
}

// 自动识别 Git
async function handleAutoDetectGit() {
  installing.value = true
  updateError.value = null

  try {
    // 先清除现有的自定义路径
    await clearGitPath()
    
    // 刷新状态，让后端重新检测
    await refreshGitStatus()

    if (gitStatus.value?.git_available) {
      // 检测到 Git，关闭弹窗
      closeSetPathModal()
      const source = gitStatus.value.git_source === 'portable' ? '便携版' : 
                     gitStatus.value.git_source === 'system' ? '系统环境变量' : '未知来源'
      showToast(`已自动识别到 Git！来源: ${source}`, 'success', 4000)
    } else {
      // 没有检测到，询问是否下载
      if (gitStatus.value?.system_os === 'Windows') {
        const confirmed = await showConfirm({
          title: 'Git 未检测到',
          message: '未检测到可用的 Git。\n\n是否立即下载安装便携版 Git？',
          type: 'info',
          confirmText: '立即安装',
          cancelText: '取消'
        })
        
        if (confirmed) {
          await installGitAuto()
          closeSetPathModal()
        } else {
          updateError.value = '未检测到 Git，请手动输入路径或下载安装'
        }
      } else {
        updateError.value = '未检测到 Git，请手动安装或输入路径'
        showInstallGuide.value = true
      }
    }
  } catch (error: any) {
    updateError.value = error?.message || '自动识别失败'
    console.error(error)
  } finally {
    installing.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', handleClickOutside)
  await refreshGitStatus()
  
  // 如果全局已经有更新信息，使用它
  if (globalUpdateInfo.value) {
    updateInfo.value = globalUpdateInfo.value
    // 清除"新更新"标记（用户已进入更新页面）
    clearUpdateStatus()
  }
  
  // 如果 Git 不可用，自动弹出设置路径对话框
  if (gitStatus.value && !gitStatus.value.git_available) {
    showSetPathModal.value = true
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.git-update-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.spinning {
  animation: spin 1s linear infinite;
}

/* 非 Git 仓库错误页面 */
.not-git-repo-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 60px 40px;
}

.error-icon {
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-error-container);
  border-radius: 50%;
  color: var(--md-sys-color-on-error-container);
  margin-bottom: 32px;
}

.error-icon .material-symbols-rounded {
  font-size: 48px;
}

.not-git-repo-error h2 {
  margin: 0 0 16px 0;
  font-size: 32px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
}

.not-git-repo-error p {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.6;
}

.not-git-repo-error .hint {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  border-radius: 16px;
  color: var(--md-sys-color-on-primary-container);
}

.header-icon .material-symbols-rounded {
  font-size: 28px;
}

.header-text h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
  line-height: 1.2;
}

.header-text p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 信息条 */
.info-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.info-item .material-symbols-rounded {
  font-size: 20px;
}

.icon-success {
  color: var(--md-sys-color-primary);
}

.icon-warning {
  color: var(--md-sys-color-error);
}

/* 分支选择区域 */
.branch-section {
  padding: 20px 24px;
  position: relative;
  z-index: 5;
}

.branch-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.branch-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.branch-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.select-wrapper {
  position: relative;
  min-width: 240px;
}

.m3-select-trigger {
  width: 100%;
  height: 40px;
  padding: 0 16px;
  border-radius: 8px;
  background: transparent;
  border: 1px solid var(--md-sys-color-outline);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.m3-select-trigger:hover {
  background: var(--md-sys-color-surface-container-highest);
  border-color: var(--md-sys-color-on-surface-variant);
}

.m3-select-trigger.active {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-highest);
}

.m3-select-trigger.disabled {
  opacity: 0.38;
  cursor: not-allowed;
  pointer-events: none;
}

.selected-value {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.select-arrow {
  color: var(--md-sys-color-on-surface-variant);
  transition: transform 0.2s;
}

.select-arrow.rotated {
  transform: rotate(180deg);
}

.m3-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  padding: 4px;
  z-index: 100;
  box-shadow: var(--md-sys-elevation-2);
  display: flex;
  flex-direction: column;
  gap: 2px;
  /* 强制禁用动画 */
  animation: none !important;
  transition: none !important;
  transform: none !important;
}

.m3-select-option {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  transition: background 0.2s;
}

.m3-select-option:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.m3-select-option.selected {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  font-weight: 500;
}

.check-icon {
  font-size: 18px;
}

.switching-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-sys-color-primary);
}

/* Git 路径信息 */
.git-path-info {
  padding: 20px 24px;
}

.path-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.path-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.path-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.path-display {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.path-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.path-value {
  flex: 1;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--md-sys-color-on-surface);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.m3-badge {
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

.source-custom {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.source-portable {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.source-system {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.source-unknown {
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface-variant);
}

.path-actions {
  display: flex;
  gap: 8px;
}

/* 警告提示 */
.alert {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}

.alert-warning {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.alert-icon {
  font-size: 24px;
}

.alert-content {
  flex: 1;
}

.alert-content strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.alert-content p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

/* 主卡片 */
.main-card {
  padding: 40px;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 检查状态 */
.checking-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  text-align: center;
}

.spinner-large {
  font-size: 48px;
  color: var(--md-sys-color-primary);
}

.checking-state p {
  margin: 0;
  font-size: 16px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 更新内容 */
.update-content {
  width: 100%;
}

.has-update {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.update-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.update-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  border-radius: 16px;
  color: var(--md-sys-color-on-primary-container);
}

.update-icon .material-symbols-rounded {
  font-size: 32px;
}

.update-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.update-title p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 版本对比 */
.version-compare {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 24px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
}

.version-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.version-tag {
  font-size: 12px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--md-sys-color-on-surface-variant);
}

.version-box code {
  padding: 10px 20px;
  background: var(--md-sys-color-surface);
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  font-family: 'Roboto Mono', monospace;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.version-latest code {
  border-color: var(--md-sys-color-primary);
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.arrow-icon {
  font-size: 24px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 提交徽章 */
.commits-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--md-sys-color-secondary-container);
  border-radius: 10px;
  font-size: 14px;
  color: var(--md-sys-color-on-secondary-container);
  width: fit-content;
}

.branch-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: var(--md-sys-color-surface);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

/* 更新日志 */
.changelog {
  padding: 20px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
}

.changelog-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.changelog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.changelog-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.changelog-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--md-sys-color-on-surface-variant);
}

.changelog-list .bullet {
  font-size: 8px;
  margin-top: 6px;
  flex-shrink: 0;
  color: var(--md-sys-color-primary);
}

/* 更新选项 */
.update-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.m3-checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.m3-checkbox-wrapper input {
  display: none;
}

.checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid var(--md-sys-color-outline);
  border-radius: 2px;
  position: relative;
  transition: all 0.2s;
}

.m3-checkbox-wrapper input:checked + .checkmark {
  background: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
}

.m3-checkbox-wrapper input:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 1px;
  width: 4px;
  height: 10px;
  border: solid var(--md-sys-color-on-primary);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.option-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.option-desc {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 更新按钮 */
.btn-update {
  width: 100%;
  height: 56px;
  font-size: 16px;
}

/* 无更新状态 */
.no-update {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 60px 40px;
  text-align: center;
}

.no-update-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  border-radius: 50%;
  color: var(--md-sys-color-on-primary-container);
}

.no-update-icon .material-symbols-rounded {
  font-size: 40px;
}

.no-update h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.no-update p {
  margin: 0;
  font-size: 15px;
  color: var(--md-sys-color-on-surface-variant);
}

.current-version {
  padding: 10px 20px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.last-update-info {
  margin-top: 20px;
  padding: 20px;
  background: var(--md-sys-color-surface-container-low);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.update-time {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 初始状态 */
.initial-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
  padding: 60px 40px;
  text-align: center;
}

.initial-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 50%;
  color: var(--md-sys-color-on-surface-variant);
}

.initial-icon .material-symbols-rounded {
  font-size: 40px;
}

.initial-state h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.initial-state p {
  margin: 0;
  font-size: 15px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: var(--md-sys-color-error-container);
  border-radius: 12px;
  color: var(--md-sys-color-on-error-container);
  margin-top: 16px;
}

.error-message p {
  margin: 0;
  font-size: 14px;
}

/* 弹窗 */
.m3-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}

.m3-dialog {
  background: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  padding: 24px;
  width: 90%;
  max-width: 480px;
  box-shadow: var(--md-sys-elevation-3);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
}

.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.dialog-body.center-content {
  align-items: center;
  text-align: center;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* 成功弹窗 */
.success-modal {
  align-items: center;
  text-align: center;
}

.success-icon-wrapper {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-primary-container);
  border-radius: 50%;
  color: var(--md-sys-color-on-primary-container);
  margin-bottom: 16px;
}

.success-icon {
  font-size: 40px;
}

.success-modal h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.success-modal > p {
  margin: 0 0 24px 0;
  font-size: 15px;
  color: var(--md-sys-color-on-surface-variant);
  line-height: 1.6;
}

.updated-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 10px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 24px;
  width: 100%;
}

.modal-actions {
  width: 100%;
  justify-content: center;
}

/* 指南弹窗 */
.guide-icon,
.modal-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-tertiary-container);
  border-radius: 50%;
  color: var(--md-sys-color-on-tertiary-container);
  margin-bottom: 16px;
}

.guide-icon .material-symbols-rounded,
.modal-icon .material-symbols-rounded {
  font-size: 40px;
}

.guide-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
}

/* 路径输入组 */
.path-input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-hint {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

/* Toast 通知 */
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none;
}

.m3-snackbar {
  pointer-events: auto;
  background: var(--md-sys-color-inverse-surface);
  color: var(--md-sys-color-inverse-on-surface);
  padding: 14px 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--md-sys-elevation-3);
  min-width: 300px;
}

.m3-snackbar.success {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.m3-snackbar.error {
  background: var(--md-sys-color-error-container);
  color: var(--md-sys-color-on-error-container);
}

.m3-snackbar.warning {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

/* 动画 */
.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.2, 0, 0, 1);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(0, 20px);
}

/* 响应式 */
@media (max-width: 768px) {
  .git-update-view {
    padding: 16px;
  }

  .header-icon {
    width: 48px;
    height: 48px;
  }

  .header-icon .material-symbols-rounded {
    font-size: 24px;
  }

  .header-text h1 {
    font-size: 24px;
  }

  .main-card {
    padding: 24px;
  }

  .version-compare {
    flex-direction: column;
    gap: 12px;
  }

  .arrow-icon {
    transform: rotate(90deg);
  }

  .modal-actions {
    flex-direction: column;
  }

  .path-display {
    flex-direction: column;
    align-items: flex-start;
  }

  .path-value {
    width: 100%;
  }

  .path-actions {
    width: 100%;
    flex-direction: column;
  }

  .path-actions button {
    width: 100%;
    justify-content: center;
  }
}
</style>
