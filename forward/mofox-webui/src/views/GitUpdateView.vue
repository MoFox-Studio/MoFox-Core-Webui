<template>
  <div class="git-update-view">
    <!-- 非 Git 仓库错误提示 -->
    <div v-if="gitStatus && !gitStatus.is_git_repo" class="not-git-repo-error">
      <div class="error-icon">
        <Icon icon="lucide:alert-circle" />
      </div>
      <h2>无法使用更新功能</h2>
      <p>主程序目录不是 Git 仓库，无法使用自动更新功能。</p>
      <p class="hint">如需使用此功能，请通过 Git 克隆项目仓库。</p>
      <button class="btn-back" @click="$router.back()">
        <Icon icon="lucide:arrow-left" />
        <span>返回</span>
      </button>
    </div>

    <!-- Git 仓库正常界面 -->
    <template v-else>
      <!-- 头部 -->
      <div class="page-header">
        <div class="header-content">
          <div class="header-icon">
            <Icon icon="lucide:git-branch" />
          </div>
          <div class="header-text">
            <h1>MoFox-Bot主程序更新</h1>
            <p>管理和更新您的MoFox-Bot</p>
          </div>
        </div>
        <button class="refresh-btn" @click="handleRefresh" :disabled="checking || loading">
          <Icon icon="lucide:refresh-cw" :class="{ rotating: checking || loading }" />
        </button>
      </div>

      <!-- 系统信息条 -->
      <div v-if="gitStatus" class="info-bar">
        <div class="info-item">
          <Icon icon="lucide:git-branch" />
          <span>Git 仓库</span>
        </div>
        <div class="info-item">
          <Icon :icon="gitStatus.git_available ? 'lucide:check-circle-2' : 'lucide:alert-circle'" 
                :class="gitStatus.git_available ? 'icon-success' : 'icon-warning'" />
          <span>{{ gitStatus.git_available ? 'Git 可用' : 'Git 未安装' }}</span>
        </div>
        <div v-if="gitStatus.current_branch" class="info-item">
          <Icon icon="lucide:git-branch" />
          <span>分支: {{ gitStatus.current_branch }}</span>
        </div>
        <div class="info-item">
          <Icon icon="lucide:monitor" />
          <span>{{ gitStatus.system_os }}</span>
        </div>
      </div>

      <!-- 分支切换区域 -->
      <div v-if="gitStatus && gitStatus.git_available && gitStatus.available_branches.length > 0" class="branch-section">
        <div class="branch-header">
          <Icon icon="lucide:git-branch" />
          <h3>分支管理</h3>
        </div>
        <div class="branch-selector">
          <label>当前分支:</label>
          <select v-model="selectedBranch" @change="handleBranchChange" :disabled="switching">
            <option v-for="branch in gitStatus.available_branches" :key="branch" :value="branch">
              {{ branch }}
            </option>
          </select>
          <span v-if="switching" class="switching-indicator">
            <Icon icon="lucide:loader-2" class="rotating" />
            切换中...
          </span>
        </div>
      </div>

      <!-- Git 路径管理 -->
      <div v-if="gitStatus && gitStatus.git_available" class="git-path-info">
        <div class="path-header">
          <Icon icon="lucide:folder-git-2" />
          <h3>Git 路径</h3>
        </div>
        <div class="path-content">
          <div class="path-display">
            <span class="path-label">当前路径:</span>
            <code class="path-value">{{ gitStatus.git_path || '未知' }}</code>
            <span class="path-source" :class="`source-${gitStatus.git_source}`">
              {{ gitStatus.git_source === 'custom' ? '自定义' : 
                 gitStatus.git_source === 'portable' ? '便携版' : 
                 gitStatus.git_source === 'system' ? '系统' : '未知' }}
            </span>
          </div>
          <div class="path-actions">
            <button class="btn-path-action" @click="openSetPathModal">
              <Icon icon="lucide:edit-3" />
              设置路径
            </button>
            <button v-if="gitStatus.git_source === 'custom'" 
                    class="btn-path-action btn-clear" 
                    @click="handleClearGitPath">
              <Icon icon="lucide:x" />
              清除自定义
            </button>
          </div>
        </div>
      </div>

      <!-- Git 未安装警告 -->
      <div v-if="gitStatus && !gitStatus.git_available" class="alert alert-warning">
        <Icon icon="lucide:alert-triangle" />
        <div class="alert-content">
          <strong>需要安装 Git</strong>
          <p>需要安装 Git 才能进行更新操作</p>
        </div>
        <button 
          v-if="gitStatus.system_os === 'Windows'" 
          class="btn-install"
          @click="installGitAuto"
          :disabled="installing"
        >
          {{ installing ? '安装中...' : '立即安装' }}
        </button>
        <button v-else class="btn-install" @click="showInstallGuide = true">
          安装指南
        </button>
      </div>

    <!-- 主卡片 -->
    <div v-if="canCheckUpdate" class="main-card">
      <!-- 加载状态 -->
      <div v-if="checking" class="checking-state">
        <div class="spinner-large"></div>
        <p>正在检查更新...</p>
      </div>

      <!-- 更新信息 -->
      <div v-else-if="updateInfo" class="update-content">
        <!-- 有更新 -->
        <div v-if="updateInfo.has_update" class="has-update">
          <div class="update-header">
            <div class="update-icon">
              <Icon icon="lucide:sparkles" />
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
            <Icon icon="lucide:arrow-right" class="arrow-icon" />
            <div class="version-box version-latest">
              <span class="version-tag">最新</span>
              <code>{{ updateInfo.remote_commit?.substring(0, 8) || '未知' }}</code>
            </div>
          </div>

          <!-- 提交信息 -->
          <div v-if="updateInfo.commits_behind" class="commits-badge">
            <Icon icon="lucide:git-commit" />
            <span>{{ updateInfo.commits_behind }} 个新提交</span>
            <span v-if="updateInfo.branch" class="branch-badge">
              <Icon icon="lucide:git-branch" />
              {{ updateInfo.branch }}
            </span>
          </div>

          <!-- 更新日志 -->
          <div v-if="updateInfo.update_logs && updateInfo.update_logs.length > 0" class="changelog">
            <div class="changelog-header">
              <Icon icon="lucide:list" />
              <h3>更新内容</h3>
            </div>
            <ul class="changelog-list">
              <li v-for="(log, index) in updateInfo.update_logs" :key="index">
                <Icon icon="lucide:circle" class="bullet" />
                <span>{{ log }}</span>
              </li>
            </ul>
          </div>

          <!-- 更新选项 -->
          <div class="update-options">
            <label class="option-item">
              <input type="checkbox" v-model="updateOptions.stashLocal" />
              <div class="option-text">
                <span class="option-label">暂存本地修改</span>
                <span class="option-desc">保护您的本地更改</span>
              </div>
            </label>
            <label class="option-item">
              <input type="checkbox" v-model="updateOptions.createBackup" />
              <div class="option-text">
                <span class="option-label">创建备份点</span>
                <span class="option-desc">可随时回滚</span>
              </div>
            </label>
            <label class="option-item">
              <input type="checkbox" v-model="updateOptions.force" />
              <div class="option-text">
                <span class="option-label">强制更新</span>
                <span class="option-desc">覆盖所有本地修改</span>
              </div>
            </label>
          </div>

          <!-- 更新按钮 -->
          <button 
            class="btn-update"
            @click="performUpdate"
            :disabled="updating"
          >
            <Icon :icon="updating ? 'lucide:loader-2' : 'lucide:download'" :class="{ rotating: updating }" />
            <span>{{ updating ? '正在更新...' : '立即更新' }}</span>
          </button>
        </div>

        <!-- 无更新 -->
        <div v-else class="no-update">
          <div class="no-update-icon">
            <Icon icon="lucide:check-circle-2" />
          </div>
          <h2>已是最新版本</h2>
          <p>您的MoFox-Bot已经是最新版本</p>
          <code class="current-version">
            {{ updateInfo.current_commit?.substring(0, 8) || '未知' }}
          </code>
          
          <!-- 最近更新信息 -->
          <div v-if="lastUpdateResult && lastUpdateResult.success" class="last-update-info">
            <div class="update-time">
              <Icon icon="lucide:clock" />
              <span>上次更新成功</span>
            </div>
            <button v-if="lastUpdateResult.backup_commit" class="btn-rollback" @click="rollback(lastUpdateResult.backup_commit!)">
              <Icon icon="lucide:undo-2" />
              <span>回滚到上一版本</span>
            </button>
          </div>
        </div>

        <!-- 错误信息 -->
        <div v-if="updateError" class="error-message">
          <Icon icon="lucide:alert-circle" />
          <p>{{ updateError }}</p>
        </div>
      </div>

      <!-- 初始状态 -->
      <div v-else class="initial-state">
        <div class="initial-icon">
          <Icon icon="lucide:search" />
        </div>
        <h2>检查更新</h2>
        <p>点击按钮检查是否有可用的更新</p>
        <button class="btn-check" @click="checkForUpdates">
          <Icon icon="lucide:search" />
          <span>检查更新</span>
        </button>
      </div>
    </div>

    <!-- 成功弹窗 -->
    <transition name="modal">
      <div v-if="showSuccessModal" class="modal-overlay" @click.self="showSuccessModal = false">
        <div class="success-modal">
          <div class="success-icon-wrapper">
            <Icon icon="lucide:check-circle-2" class="success-icon" />
          </div>
          <h2>更新成功</h2>
          <p>{{ lastUpdateResult?.message || 'MoFox-Bot已成功更新到最新版本' }}</p>
          
          <div v-if="lastUpdateResult?.updated_files && lastUpdateResult.updated_files.length > 0" class="updated-summary">
            <Icon icon="lucide:file-check" />
            <span>已更新 {{ lastUpdateResult.updated_files.length }} 个文件</span>
          </div>

          <div class="modal-actions">
            <button class="btn-modal-primary" @click="closeSuccessModal">
              <Icon icon="lucide:check" />
              <span>确定</span>
            </button>
            <button v-if="lastUpdateResult?.backup_commit" class="btn-modal-secondary" @click="rollbackFromModal">
              <Icon icon="lucide:undo-2" />
              <span>回滚</span>
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Git 安装指南弹窗 -->
    <transition name="modal">
      <div v-if="showInstallGuide" class="modal-overlay" @click.self="showInstallGuide = false">
        <div class="guide-modal">
          <button class="modal-close" @click="showInstallGuide = false">
            <Icon icon="lucide:x" />
          </button>
          <div class="guide-icon">
            <Icon icon="lucide:book-open" />
          </div>
          <h2>Git 安装指南</h2>
          <p>请访问 Git 官网下载并安装适合您系统的版本</p>
          <a href="https://git-scm.com/downloads" target="_blank" class="guide-link">
            <Icon icon="lucide:external-link" />
            <span>git-scm.com/downloads</span>
          </a>
        </div>
      </div>
    </transition>

    <!-- 设置 Git 路径弹窗 -->
    <transition name="modal">
      <div v-if="showSetPathModal" class="modal-overlay" @click.self="closeSetPathModal">
        <div class="path-modal">
          <button class="modal-close" @click="closeSetPathModal">
            <Icon icon="lucide:x" />
          </button>
          <div class="modal-icon">
            <Icon icon="lucide:folder-git-2" />
          </div>
          <h2>设置 Git 路径</h2>
          <p>请输入 Git 可执行文件的完整路径，或者选择自动下载安装</p>
          
          <div class="path-input-group">
            <label for="git-path-input">Git 可执行文件路径</label>
            <input 
              id="git-path-input"
              v-model="customGitPath" 
              type="text" 
              placeholder="例如: C:\Program Files\Git\bin\git.exe"
              :disabled="settingPath"
              @keyup.enter="handleSetGitPath"
            />
            <span class="input-hint">
              Windows: git.exe | Linux/macOS: git
            </span>
          </div>

          <div v-if="updateError" class="error-message">
            <Icon icon="lucide:alert-circle" />
            <p>{{ updateError }}</p>
          </div>

          <div class="modal-actions">
            <button 
              class="btn-modal-primary" 
              @click="handleSetGitPath"
              :disabled="!customGitPath.trim() || settingPath"
            >
              <Icon :icon="settingPath ? 'lucide:loader-2' : 'lucide:check'" 
                    :class="{ rotating: settingPath }" />
              {{ settingPath ? '验证中...' : '确认设置' }}
            </button>
            <button 
              class="btn-modal-secondary" 
              @click="handleAutoDetectGit"
              :disabled="installing"
            >
              <Icon :icon="installing ? 'lucide:loader-2' : 'lucide:search'" 
                    :class="{ rotating: installing }" />
              {{ installing ? '处理中...' : '自动识别' }}
            </button>
            <button class="btn-modal-secondary" @click="closeSetPathModal">
              取消
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- Toast 通知 -->
    <div class="toast-container">
      <transition-group name="toast">
        <div 
          v-for="toast in toasts" 
          :key="toast.id" 
          class="toast"
          :class="`toast-${toast.type}`"
        >
          <Icon :icon="
            toast.type === 'success' ? 'lucide:check-circle-2' :
            toast.type === 'error' ? 'lucide:alert-circle' :
            toast.type === 'warning' ? 'lucide:alert-triangle' :
            'lucide:info'
          " />
          <span>{{ toast.message }}</span>
        </div>
      </transition-group>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'
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
</script>

<style scoped>
.git-update-view {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
}

.error-icon {
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--danger-bg);
  border-radius: 50%;
  color: var(--danger);
  font-size: 48px;
  margin-bottom: 32px;
}

.not-git-repo-error h2 {
  margin: 0 0 16px 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.not-git-repo-error p {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.not-git-repo-error .hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

.btn-back {
  margin-top: 32px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-back:hover {
  background: var(--bg-tertiary);
  transform: translateY(-2px);
}

/* 头部 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid transparent;
  transition: all var(--transition);
}

.page-header:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-light);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-icon {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-bg);
  border-radius: 20px;
  color: var(--primary);
  font-size: 32px;
}

.header-text h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.header-text p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.refresh-btn {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--bg-secondary);
  border-radius: 14px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
  font-size: 20px;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  transform: rotate(180deg);
}

/* 信息条 */
.info-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.info-item svg {
  color: var(--text-tertiary);
}

.info-item .icon-success { color: var(--success); }
.info-item .icon-warning { color: var(--warning); }

/* 分支选择区域 */
.branch-section {
  padding: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.branch-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.branch-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.branch-selector {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.branch-selector label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.branch-selector select {
  flex: 1;
  min-width: 240px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition);
  outline: none;
}

.branch-selector select:hover:not(:disabled) {
  background: var(--bg-tertiary);
}

.branch-selector select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.switching-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--primary);
  font-weight: 500;
}

/* Git 路径信息 */
.git-path-info {
  padding: 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.path-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.path-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.path-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.path-display {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.path-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.path-value {
  flex: 1;
  padding: 10px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  font-family: 'JetBrains Mono', monospace;
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.path-source {
  padding: 4px 12px;
  border-radius: var(--radius-full);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.source-custom { background: var(--primary-bg); color: var(--primary); }
.source-portable { background: rgba(16, 185, 129, 0.1); color: var(--success); }
.source-system { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
.source-unknown { background: var(--bg-tertiary); color: var(--text-tertiary); }

.path-actions {
  display: flex;
  gap: 12px;
}

.btn-path-action {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-path-action:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-path-action.btn-clear:hover {
  background: var(--danger-bg);
  color: var(--danger);
}

/* 主卡片区域 */
.main-card {
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: all var(--transition);
}

.main-card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  padding: 24px;
  border-bottom: 1px solid var(--border-light);
}

.card-header h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.card-header p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.card-body {
  padding: 24px;
}

/* 版本比较 */
.version-compare {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 32px;
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
}

.version-box {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.version-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.version-number {
  font-size: 24px;
  font-weight: 800;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

.version-number.new {
  color: var(--primary);
}

.arrow-icon {
  font-size: 24px;
  color: var(--text-tertiary);
}

/* 提交徽章 */
.commits-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--primary-bg);
  border-radius: var(--radius-full);
  font-size: 13px;
  font-weight: 600;
  color: var(--primary);
  width: fit-content;
}

.branch-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

/* 更新日志 */
.changelog {
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.changelog-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.changelog-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
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
  gap: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.changelog-list .bullet {
  font-size: 6px;
  margin-top: 8px;
  flex-shrink: 0;
  color: var(--primary);
}

/* 更新选项 */
.update-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  margin-bottom: 24px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all var(--transition);
  padding: 8px;
  border-radius: var(--radius);
}

.option-item:hover {
  background: var(--bg-tertiary);
}

.option-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--primary);
  border-radius: 4px;
}

.option-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.option-desc {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 更新按钮 */
.btn-update {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 32px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary);
  color: white;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition);
  box-shadow: var(--shadow-md);
}

.btn-update:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-update:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

/* 无更新状态 */
.no-update {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 60px 40px;
  text-align: center;
}

.no-update-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 50%;
  color: var(--success);
  font-size: 40px;
}

.no-update h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.no-update p {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

.current-version {
  padding: 8px 16px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.last-update-info {
  margin-top: 24px;
  padding: 24px;
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
}

.update-time {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.btn-rollback {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border: 1px solid transparent;
  border-radius: var(--radius-full);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-rollback:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

/* 初始状态 */
.initial-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding: 60px 40px;
  text-align: center;
}

.initial-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-secondary);
  border-radius: 50%;
  color: var(--text-tertiary);
  font-size: 40px;
}

.initial-state h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.initial-state p {
  margin: 0;
  font-size: 15px;
  color: var(--text-secondary);
}

.btn-check {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  border: none;
  border-radius: var(--radius-full);
  background: var(--primary);
  color: white;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition);
  box-shadow: var(--shadow-md);
}

.btn-check:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--danger-bg);
  border-radius: var(--radius-lg);
  color: var(--danger);
  margin-top: 24px;
  font-weight: 500;
}

/* 旋转动画 */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

/* 成功弹窗 */
.success-modal {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  width: 100%;
  max-width: 480px;
  text-align: center;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.success-icon-wrapper {
  margin: 0 auto 24px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 50%;
}

.success-icon {
  font-size: 40px;
  color: var(--success);
  animation: checkmark 0.5s ease 0.2s both;
}

.success-modal h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.success-modal > p {
  margin: 0 0 24px 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.updated-summary {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  background: var(--bg-secondary);
  border-radius: var(--radius);
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 32px;
}

.updated-summary svg {
  color: var(--success);
}

.modal-actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.btn-modal-primary,
.btn-modal-secondary {
  flex: 1;
  min-width: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  border: none;
  border-radius: var(--radius-full);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
}

.btn-modal-primary {
  background: var(--primary);
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn-modal-primary:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-modal-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-modal-secondary:hover {
  background: var(--bg-tertiary);
}

/* 指南弹窗 */
.guide-modal,
.path-modal {
  position: relative;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: 48px 40px;
  width: 100%;
  max-width: 480px;
  text-align: center;
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.modal-close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: var(--bg-secondary);
  border-radius: 10px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition);
  font-size: 18px;
}

.modal-close:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.guide-icon,
.modal-icon {
  margin: 0 auto 24px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-bg);
  border-radius: 50%;
  color: var(--primary);
  font-size: 40px;
}

.guide-modal h2,
.path-modal h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.guide-modal > p,
.path-modal > p {
  margin: 0 0 24px 0;
  font-size: 15px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.guide-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  background: var(--primary);
  color: white;
  text-decoration: none;
  border-radius: var(--radius-full);
  font-size: 15px;
  font-weight: 600;
  transition: all var(--transition);
  box-shadow: var(--shadow-sm);
}

.guide-link:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

/* 路径输入组 */
.path-input-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 24px;
  text-align: left;
}

.path-input-group label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.path-input-group input {
  width: 100%;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius);
  color: var(--text-primary);
  font-size: 14px;
  font-family: 'JetBrains Mono', monospace;
  transition: all var(--transition);
}

.path-input-group input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.path-input-group input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.input-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 动画 */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .success-modal,
.modal-enter-from .guide-modal,
.modal-enter-from .path-modal,
.modal-leave-to .success-modal,
.modal-leave-to .guide-modal,
.modal-leave-to .path-modal {
  transform: scale(0.95) translateY(10px);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes checkmark {
  0% { transform: scale(0); }
  50% { transform: scale(1.2); }
  100% { transform: scale(1); }
}

/* Toast 通知 */
.toast-container {
  position: fixed;
  top: 80px;
  right: 32px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 16px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  font-size: 14px;
  font-weight: 500;
  min-width: 300px;
  max-width: 500px;
  pointer-events: all;
  border: 1px solid transparent;
}

.toast svg {
  font-size: 20px;
  flex-shrink: 0;
}

.toast span {
  flex: 1;
  line-height: 1.5;
}

.toast-success {
  border-left: 4px solid var(--success);
  color: var(--text-primary);
}

.toast-success svg {
  color: var(--success);
}

.toast-error {
  border-left: 4px solid var(--danger);
  color: var(--text-primary);
}

.toast-error svg {
  color: var(--danger);
}

.toast-warning {
  border-left: 4px solid var(--warning);
  color: var(--text-primary);
}

.toast-warning svg {
  color: var(--warning);
}

.toast-info {
  border-left: 4px solid var(--primary);
  color: var(--text-primary);
}

.toast-info svg {
  color: var(--primary);
}

/* Toast 动画 */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(50px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(50px);
}

.toast-move {
  transition: transform 0.4s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .git-update-view {
    padding: 20px 16px;
  }

  .header-icon {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }

  .header-text h1 {
    font-size: 20px;
  }

  .main-card {
    padding: 20px;
  }

  .version-compare {
    flex-direction: column;
    gap: 16px;
  }

  .arrow-icon {
    transform: rotate(90deg);
  }

  .modal-actions {
    flex-direction: column;
  }

  .success-modal,
  .guide-modal,
  .path-modal {
    padding: 32px 24px;
  }

  .git-path-info {
    padding: 20px;
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

  .btn-path-action {
    width: 100%;
    justify-content: center;
  }

  .toast-container {
    top: 60px;
    right: 16px;
    left: 16px;
  }

  .toast {
    min-width: auto;
    max-width: 100%;
  }
}
</style>
