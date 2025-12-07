<template>
  <div class="git-update-view">
    <!-- 头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-icon">
          <Icon icon="lucide:package" />
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
        <Icon :icon="gitStatus.update_mode === 'git' ? 'lucide:git-branch' : 'lucide:package'" />
        <span>{{ gitStatus.update_mode === 'git' ? 'Git 模式' : 'Release 模式' }}</span>
      </div>
      <div v-if="gitStatus.update_mode === 'git'" class="info-item">
        <Icon :icon="gitStatus.git_available ? 'lucide:check-circle-2' : 'lucide:alert-circle'" 
              :class="gitStatus.git_available ? 'icon-success' : 'icon-warning'" />
        <span>{{ gitStatus.git_available ? 'Git 可用' : 'Git 未安装' }}</span>
      </div>
      <div class="info-item">
        <Icon icon="lucide:monitor" />
        <span>{{ gitStatus.system_os }}</span>
      </div>
    </div>

    <!-- Git 未安装警告 -->
    <div v-if="gitStatus && gitStatus.update_mode === 'git' && !gitStatus.git_available" class="alert alert-warning">
      <Icon icon="lucide:alert-triangle" />
      <div class="alert-content">
        <strong>需要安装 Git</strong>
        <p>当前为 Git 仓库模式，需要安装 Git 才能进行更新操作</p>
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
              <code>{{ updateInfo.update_mode === 'git' ? updateInfo.current_commit?.substring(0, 8) : updateInfo.current_version || '未知' }}</code>
            </div>
            <Icon icon="lucide:arrow-right" class="arrow-icon" />
            <div class="version-box version-latest">
              <span class="version-tag">最新</span>
              <code>{{ updateInfo.update_mode === 'git' ? updateInfo.remote_commit?.substring(0, 8) : updateInfo.latest_version }}</code>
            </div>
          </div>

          <!-- 提交信息 (Git模式) -->
          <div v-if="updateInfo.update_mode === 'git' && updateInfo.commits_behind" class="commits-badge">
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
            <template v-if="updateInfo.update_mode === 'git'">
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
            </template>
            <template v-else>
              <label class="option-item">
                <input type="checkbox" v-model="updateOptions.createBackup" />
                <div class="option-text">
                  <span class="option-label">创建备份</span>
                  <span class="option-desc">建议在更新前备份</span>
                </div>
              </label>
            </template>
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
            {{ updateInfo.update_mode === 'git' ? updateInfo.current_commit?.substring(0, 8) : updateInfo.current_version || updateInfo.latest_version }}
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { getGitStatus, installGit, checkUpdates, updateMainProgram, rollbackVersion } from '@/api/git_update'
import type { GitStatus, UpdateCheck, UpdateResult } from '@/api/git_update'
import { globalUpdateInfo, clearUpdateStatus } from '@/utils/updateChecker'

const loading = ref(true)
const checking = ref(false)
const installing = ref(false)
const updating = ref(false)

const gitStatus = ref<GitStatus | null>(null)
const updateInfo = ref<UpdateCheck | null>(null)
const updateError = ref<string | null>(null)
const lastUpdateResult = ref<UpdateResult | null>(null)
const showInstallGuide = ref(false)
const showSuccessModal = ref(false)

const updateOptions = ref({
  force: false,
  stashLocal: true,
  createBackup: true
})

// 计算属性：是否可以检查更新
const canCheckUpdate = computed(() => {
  if (!gitStatus.value) return false
  if (gitStatus.value.update_mode === 'git') {
    return gitStatus.value.git_available
  } else if (gitStatus.value.update_mode === 'release') {
    return true
  }
  return false
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
  if (!confirm(`确定要回滚到版本 ${commitHash.substring(0, 8)} 吗？`)) {
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

// 刷新按钮 - 同时刷新状态和检查更新
async function handleRefresh() {
  await refreshGitStatus()
  if (canCheckUpdate.value) {
    await checkForUpdates()
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
})
</script>

<style scoped>
:root {
  --color-primary: #6366f1;
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
}

.git-update-view {
  max-width: 800px;
  margin: 0 auto;
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-height: 100vh;
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
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 16px;
  color: white;
  font-size: 28px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

.header-text h1 {
  margin: 0;
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.header-text p {
  margin: 4px 0 0 0;
  font-size: 15px;
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
  border-radius: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 20px;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--bg-hover);
  color: var(--text-primary);
  transform: scale(1.05);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 信息条 */
.info-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: var(--bg-secondary);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--text-secondary);
}

.info-item svg {
  font-size: 18px;
}

.icon-success {
  color: var(--color-success);
}

.icon-warning {
  color: var(--color-warning);
}

/* 警告提示 */
.alert {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid;
}

.alert-warning {
  background: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.3);
}

.alert svg:first-child {
  font-size: 24px;
  color: var(--color-warning);
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
}

.alert-content strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.alert-content p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.btn-install {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  background: var(--color-warning);
  color: white;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.btn-install:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-install:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 主卡片 */
.main-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 16px;
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
  width: 64px;
  height: 64px;
  border: 4px solid var(--border-color);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: rotate 0.8s linear infinite;
}

.checking-state p {
  margin: 0;
  font-size: 16px;
  color: var(--text-secondary);
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
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 16px;
  color: white;
  font-size: 32px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

.update-title h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.update-title p {
  margin: 4px 0 0 0;
  font-size: 14px;
  color: var(--text-secondary);
}

/* 版本对比 */
.version-compare {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 24px;
  background: var(--bg-secondary);
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
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-tertiary);
}

.version-box code {
  padding: 10px 20px;
  background: var(--bg-primary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.version-latest code {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.arrow-icon {
  font-size: 24px;
  color: var(--text-tertiary);
}

/* 提交徽章 */
.commits-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  width: fit-content;
}

.commits-badge svg {
  color: var(--color-primary);
}

.branch-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: var(--bg-primary);
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary);
}

/* 更新日志 */
.changelog {
  padding: 20px;
  background: var(--bg-secondary);
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
  font-weight: 600;
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
  gap: 10px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
}

.changelog-list .bullet {
  font-size: 8px;
  margin-top: 6px;
  flex-shrink: 0;
  color: var(--color-primary);
}

/* 更新选项 */
.update-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
  background: var(--bg-secondary);
  border-radius: 12px;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.option-item:hover {
  opacity: 0.8;
}

.option-item input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.option-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.option-desc {
  font-size: 12px;
  color: var(--text-tertiary);
}

/* 更新按钮 */
.btn-update {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 16px 32px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.btn-update:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

.btn-update:active:not(:disabled) {
  transform: translateY(0);
}

.btn-update:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-update svg {
  font-size: 20px;
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  color: white;
  font-size: 40px;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
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
  padding: 10px 20px;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  border-radius: 8px;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.last-update-info {
  margin-top: 20px;
  padding: 20px;
  background: var(--bg-secondary);
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
  color: var(--text-secondary);
}

.btn-rollback {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-rollback:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(99, 102, 241, 0.1);
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
  padding: 14px 32px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
  margin-top: 10px;
}

.btn-check:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  color: var(--color-error);
  margin-top: 16px;
}

.error-message svg {
  font-size: 20px;
  flex-shrink: 0;
}

.error-message p {
  margin: 0;
  font-size: 14px;
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
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

/* 成功弹窗 */
.success-modal {
  background: var(--bg-primary);
  border-radius: 20px;
  padding: 48px 40px;
  width: 100%;
  max-width: 480px;
  text-align: center;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
  animation: modalIn 0.3s ease;
}

.success-icon-wrapper {
  margin: 0 auto 24px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 50%;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.3);
}

.success-icon {
  font-size: 40px;
  color: white;
  animation: checkmark 0.5s ease 0.2s both;
}

.success-modal h2 {
  margin: 0 0 12px 0;
  font-size: 28px;
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
  border-radius: 10px;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 28px;
}

.updated-summary svg {
  color: var(--color-success);
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.btn-modal-primary,
.btn-modal-secondary {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-modal-primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.btn-modal-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}

.btn-modal-secondary {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

.btn-modal-secondary:hover {
  background: var(--bg-hover);
}

/* 指南弹窗 */
.guide-modal {
  position: relative;
  background: var(--bg-primary);
  border-radius: 20px;
  padding: 48px 40px;
  width: 100%;
  max-width: 480px;
  text-align: center;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
  animation: modalIn 0.3s ease;
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
  transition: all 0.2s ease;
  font-size: 18px;
}

.modal-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.guide-icon {
  margin: 0 auto 24px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  border-radius: 50%;
  color: white;
  font-size: 40px;
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.3);
}

.guide-modal h2 {
  margin: 0 0 12px 0;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
}

.guide-modal > p {
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
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: white;
  text-decoration: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.2s ease;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
}

.guide-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
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
.modal-leave-to .success-modal,
.modal-leave-to .guide-modal {
  transform: scale(0.9);
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes checkmark {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
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

  .success-modal,
  .guide-modal {
    padding: 36px 24px;
  }
}
</style>
