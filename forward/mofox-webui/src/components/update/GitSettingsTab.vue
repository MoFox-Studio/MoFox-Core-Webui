<!--
  @file GitSettingsTab.vue
  @description 更新/Git 设置标签页组件
  
  功能说明：
  1. 显示 Git 环境状态
  2. 设置自定义 Git 路径
  3. 一键安装 Git（Windows）
  4. 自动更新检查配置
-->
<template>
  <div class="git-settings-tab">
    <!-- Git 环境状态 -->
    <div class="m3-card status-card">
      <div class="card-header">
        <span class="material-symbols-rounded">terminal</span>
        <h3>Git 环境状态</h3>
        <button class="m3-icon-button" @click="loadGitStatus" :disabled="loading">
          <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
        </button>
      </div>
      
      <div class="status-grid" v-if="gitStatus">
        <div class="status-item">
          <span class="status-label">状态</span>
          <span class="status-value" :class="gitStatus.git_available ? 'success' : 'error'">
            <span class="material-symbols-rounded">
              {{ gitStatus.git_available ? 'check_circle' : 'cancel' }}
            </span>
            {{ gitStatus.git_available ? '可用' : '不可用' }}
          </span>
        </div>
        
        <div class="status-item" v-if="gitStatus.git_version">
          <span class="status-label">版本</span>
          <span class="status-value">{{ gitStatus.git_version }}</span>
        </div>
        
        <div class="status-item">
          <span class="status-label">来源</span>
          <span class="status-value">
            <span class="m3-badge" :class="`source-${gitStatus.git_source}`">
              {{ getSourceLabel(gitStatus.git_source) }}
            </span>
          </span>
        </div>
        
        <div class="status-item">
          <span class="status-label">操作系统</span>
          <span class="status-value">{{ gitStatus.system_os }}</span>
        </div>
      </div>
    </div>

    <!-- Git 路径管理 -->
    <div class="m3-card path-card" v-if="gitStatus">
      <div class="card-header">
        <span class="material-symbols-rounded">folder</span>
        <h3>Git 路径</h3>
      </div>
      
      <div class="path-content">
        <div class="path-display">
          <span class="path-label">当前路径:</span>
          <code class="path-value">{{ gitStatus.git_path || '未检测到' }}</code>
        </div>
        
        <div class="path-actions">
          <!-- 自动寻找 Git -->
          <button 
            class="m3-button tonal"
            @click="handleAutoDetect"
            :disabled="autoDetecting"
          >
            <span class="material-symbols-rounded" :class="{ spinning: autoDetecting }">
              {{ autoDetecting ? 'progress_activity' : 'search' }}
            </span>
            <span>{{ autoDetecting ? '检测中...' : '自动寻找' }}</span>
          </button>
          
          <button class="m3-button tonal" @click="showSetPathModal = true">
            <span class="material-symbols-rounded">edit</span>
            <span>设置路径</span>
          </button>
          
          <!-- 安装 Git（全平台支持） -->
          <button 
            class="m3-button" 
            :class="gitStatus.git_available ? 'tonal' : 'filled'"
            @click="handleInstallGit"
            :disabled="installing"
          >
            <span class="material-symbols-rounded" :class="{ spinning: installing }">
              {{ installing ? 'progress_activity' : 'download' }}
            </span>
            <span>{{ installing ? '安装中...' : getInstallButtonText() }}</span>
          </button>
          


        </div>
  


        
        <!-- 未检测到 Git 提示 -->
        <div class="portable-tip" v-if="!gitStatus.git_available">
          <span class="material-symbols-rounded">info</span>
          <span>{{ getInstallTipText() }}</span>
        </div>
      </div>
    </div>
    <!-- 自动更新配置 -->
    <div class="m3-card update-config-card">
      <div class="card-header">
        <span class="material-symbols-rounded">update</span>
        <h3>自动更新检查</h3>
      </div>
      
      <div class="config-content">
        <div class="config-item">
          <div class="config-info">
            <span class="config-label">启用自动更新检查</span>
            <span class="config-desc">定期检查是否有新版本可用（每5分钟）</span>
          </div>
          <label class="m3-switch">
            <input 
              type="checkbox" 
              v-model="autoUpdateEnabled"
              @change="handleAutoUpdateToggle"
            />
            <span class="slider"></span>
          </label>
        </div>
        
        <div class="config-tip" v-if="!autoUpdateEnabled">
          <span class="material-symbols-rounded">info</span>
          <span>关闭后将不会自动检查更新，您可以在更新页面手动检查</span>
        </div>
      </div>
    </div>
    <!-- Git 安装（仅 Windows 未安装时显示） -->
    <div 
      class="m3-card install-card" 
      v-if="false"
    >
      <div class="card-header">
        <span class="material-symbols-rounded">download</span>
        <h3>安装 Git</h3>
      </div>
      
      <div class="install-content">
        <p class="install-desc">
          检测到系统未安装 Git，点击下方按钮自动下载并安装便携版 Git。
        </p>
        
        <button 
          class="m3-button filled"
          @click="handleInstallGit"
          :disabled="installing"
        >
          <span class="material-symbols-rounded" :class="{ spinning: installing }">
            {{ installing ? 'progress_activity' : 'download' }}
          </span>
          <span>{{ installing ? '安装中...' : '一键安装 Git' }}</span>
        </button>
      </div>
    </div>

    <!-- 非 Windows 安装指南 -->
    <div 
      class="m3-card guide-card" 
      v-if="gitStatus && !gitStatus.git_available && gitStatus.system_os !== 'Windows'"
    >
      <div class="card-header">
        <span class="material-symbols-rounded">help</span>
        <h3>安装指南</h3>
      </div>
      
      <div class="guide-content" v-if="installGuide">
        <p>{{ installGuide.description }}</p>
        
        <div class="guide-commands" v-if="installGuide.manual_commands">
          <div 
            v-for="(cmd, name) in installGuide.manual_commands" 
            :key="name"
            class="command-item"
          >
            <span class="command-name">{{ name }}:</span>
            <code class="command-value">{{ cmd }}</code>
          </div>
        </div>
        
        <a 
          v-if="installGuide.manual_url" 
          :href="installGuide.manual_url" 
          target="_blank"
          class="m3-button tonal"
        >
          <span class="material-symbols-rounded">open_in_new</span>
          <span>官方下载</span>
        </a>
      </div>
    </div>

    <!-- 设置路径弹窗 -->
    <Teleport to="body">
      <div v-if="showSetPathModal" class="modal-overlay" @click.self="showSetPathModal = false">
        <div class="modal-content m3-card">
          <div class="modal-header">
            <h3>设置 Git 路径</h3>
            <button class="m3-icon-button" @click="showSetPathModal = false">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
          
          <div class="modal-body">
            <p>请输入 Git 可执行文件的完整路径</p>
            <div class="input-wrapper">
              <input 
                type="text" 
                v-model="customPath"
                placeholder="例如: C:\Program Files\Git\bin\git.exe"
                class="m3-input"
              />
            </div>
          </div>
          
          <div class="modal-footer">
            <button class="m3-button text" @click="showSetPathModal = false">取消</button>
            <button 
              class="m3-button filled" 
              @click="handleSetPath"
              :disabled="!customPath || settingPath"
            >
              {{ settingPath ? '设置中...' : '确定' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  getGitEnvStatus, 
  installGit, 
  setGitPath, 
  autoDetectGit,
  getGitInstallGuide,
  type GitEnvStatus,
  type GitInstallGuide
} from '@/api/git_env'
import { showToast } from '@/utils/updateChecker'
import { showSuccess, showError, showConfirm } from '@/utils/dialog'
import { startUpdateChecker, stopUpdateChecker } from '@/utils/updateChecker'

// State
const gitStatus = ref<GitEnvStatus | null>(null)
const installGuide = ref<GitInstallGuide | null>(null)
const loading = ref(false)
const installing = ref(false)
const settingPath = ref(false)
const autoDetecting = ref(false)
const showSetPathModal = ref(false)
const customPath = ref('')
const autoUpdateEnabled = ref(true) // 默认启用自动更新

// 获取来源标签
function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    custom: '自定义',
    portable: '便携版',
    system: '系统',
    unknown: '未知'
  }
  return labels[source] || source
}

// 获取安装按钮文字
function getInstallButtonText(): string {
  const os = gitStatus.value?.system_os
  switch (os) {
    case 'Windows':
      return '下载便携版'
    case 'Linux':
      return '安装 Git'
    case 'Darwin':
      return '安装 Git'
    default:
      return '安装 Git'
  }
}

// 获取安装提示文字
function getInstallTipText(): string {
  const os = gitStatus.value?.system_os
  switch (os) {
    case 'Windows':
      return '未检测到 Git，可以点击上方"下载便携版"按钮安装'
    case 'Linux':
      return '未检测到 Git，点击"安装 Git"将使用系统包管理器安装'
    case 'Darwin':
      return '未检测到 Git，点击"安装 Git"将使用 Homebrew 或 Xcode 安装'
    default:
      return '未检测到 Git，请手动安装'
  }
}

// 加载 Git 状态
async function loadGitStatus() {
  loading.value = true
  try {
    const result = await getGitEnvStatus()
    console.log('[GitSettingsTab] 加载 Git 状态:', result)
    
    if (result.success && result.data) {
      gitStatus.value = result.data as any
      console.log('[GitSettingsTab] Git 状态已更新:', gitStatus.value)
      
      // 如果不可用，加载安装指南
      if (!result.data.git_available && result.data.system_os !== 'Windows') {
        loadInstallGuide()
      }
    }
  } catch (e) {
    console.error('加载 Git 状态失败:', e)
  } finally {
    loading.value = false
  }
}

// 加载安装指南
async function loadInstallGuide() {
  try {
    const result = await getGitInstallGuide()
    if (result.success && result.data?.data) {
      installGuide.value = result.data.data
    }
  } catch (e) {
    console.error('加载安装指南失败:', e)
  }
}

// 自动检测 Git（清除当前设置并重新检测）
async function handleAutoDetect() {
  autoDetecting.value = true
  try {
    const result = await autoDetectGit()
    console.log(result)
    if (result.success && result.data?.success) {
      showSuccess(result.data.message || '已检测到 Git')
      await loadGitStatus()
    } else {
      showError(result.data?.error || result.data?.error || result.error || '未检测到 Git')
    }
  } catch (e: any) {
    showError(e.message || '检测失败')
  } finally {
    autoDetecting.value = false
  }
}

// 安装 Git
async function handleInstallGit() {
  // 如果已经有 Git，先提示用户
  if (gitStatus.value?.git_available) {
    const os = gitStatus.value?.system_os
    let message = '检测到您的电脑已经安装了 Git。\n\n'
    
    if (os === 'Windows') {
      message += '便携版 Git 适用于没有安装 Git 的用户，如果您已经有 Git，通常不需要再下载。'
    } else if (os === 'Linux') {
      message += '系统将尝试使用包管理器重新安装 Git，这可能会覆盖现有版本。'
    } else if (os === 'Darwin') {
      message += '系统将尝试使用 Homebrew 或 Xcode 安装 Git，这可能会覆盖现有版本。'
    }
    
    message += '\n\n确定要继续吗？'
    
    const confirmed = await showConfirm({
      title: '确认安装',
      message,
      type: 'warning',
      confirmText: '继续安装',
      cancelText: '取消'
    })
    if (!confirmed) return
  }
  
  installing.value = true
  try {
    const result = await installGit()
    if (result.success && result.data?.success) {
      showSuccess(result.data.message || 'Git 安装成功')
      // 安装成功后自动检测并设置路径
      await handleAutoDetect()
    } else {
      showError(result.data?.error || result.data?.error || result.error || '安装失败')
    }
  } catch (e: any) {
    showError(e.message || '安装失败')
  } finally {
    installing.value = false
  }
}

// 处理自动更新开关
function handleAutoUpdateToggle() {
  const enabled = autoUpdateEnabled.value
  localStorage.setItem('autoUpdateEnabled', enabled.toString())
  
  if (enabled) {
    startUpdateChecker()
    showToast('已启用自动更新检查')
  } else {
    stopUpdateChecker()
    showToast('已关闭自动更新检查')
  }
}

// 设置路径
async function handleSetPath() {
  if (!customPath.value) return
  
  settingPath.value = true
  try {
    const result = await setGitPath(customPath.value)
    if (result.success && result.data?.success) {
      showSuccess(result.data.message || '路径设置成功')
      showSetPathModal.value = false
      customPath.value = ''
      await loadGitStatus()
    } else {
      showError(result.data?.error || result.data?.error || result.error || '设置失败')
    }
  } catch (e: any) {
    showError(e.message || '设置失败')
  } finally {
    settingPath.value = false
  }
}

// 初始化
onMounted(() => {
  loadGitStatus()
  
  // 读取自动更新配置
  const savedConfig = localStorage.getItem('autoUpdateEnabled')
  if (savedConfig !== null) {
    autoUpdateEnabled.value = savedConfig === 'true'
  }
})

// 暴露刷新方法
defineExpose({
  refresh: loadGitStatus
})
</script>

<style scoped>
.git-settings-tab {
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

/* 自动更新配置 */
.update-config-card .config-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.config-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.config-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.config-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
}

.config-desc {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.config-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.config-tip .material-symbols-rounded {
  font-size: 18px;
  color: var(--md-sys-color-primary);
}

/* M3 开关样式 */
.m3-switch {
  position: relative;
  display: inline-block;
  width: 52px;
  height: 32px;
  flex-shrink: 0;
}

.m3-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.m3-switch .slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--md-sys-color-surface-container-highest);
  border: 2px solid var(--md-sys-color-outline);
  transition: 0.3s;
  border-radius: 16px;
}

.m3-switch .slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 6px;
  bottom: 6px;
  background-color: var(--md-sys-color-outline);
  transition: 0.3s;
  border-radius: 50%;
}

.m3-switch input:checked + .slider {
  background-color: var(--md-sys-color-primary);
  border-color: var(--md-sys-color-primary);
}

.m3-switch input:checked + .slider:before {
  transform: translateX(20px);
  background-color: var(--md-sys-color-on-primary);
}

.m3-switch input:focus + .slider {
  box-shadow: 0 0 1px var(--md-sys-color-primary);
}

/* 状态网格 */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.status-value {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.status-value.success {
  color: var(--md-sys-color-primary);
}

.status-value.error {
  color: var(--md-sys-color-error);
}

.status-value .material-symbols-rounded {
  font-size: 18px;
}

/* 徽章 */
.m3-badge {
  display: inline-flex;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  background: var(--md-sys-color-surface-container);
}

.m3-badge.source-custom {
  background: var(--md-sys-color-tertiary-container);
  color: var(--md-sys-color-on-tertiary-container);
}

.m3-badge.source-portable {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-badge.source-system {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

/* 路径显示 */
.path-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.path-display {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.path-label {
  color: var(--md-sys-color-on-surface-variant);
}

.path-value {
  font-family: 'Noto Sans SC', sans-serif;
  font-size: 14px;
  padding: 4px 8px;
  background: var(--md-sys-color-surface-container);
  border-radius: 4px;
  word-break: break-all;
}

.path-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 提示信息 */
.portable-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  padding: 8px 12px;
  background: var(--md-sys-color-surface-container-high);
  border-radius: 8px;
  margin-top: 4px;
}

.portable-tip .material-symbols-rounded {
  font-size: 18px;
  color: var(--md-sys-color-primary);
}

/* 安装内容 */
.install-content, .guide-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.install-desc {
  margin: 0;
  color: var(--md-sys-color-on-surface-variant);
}

.guide-commands {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
}

.command-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.command-name {
  font-weight: 500;
  min-width: 100px;
}

.command-value {
  font-family: monospace;
  padding: 4px 8px;
  background: var(--md-sys-color-surface);
  border-radius: 4px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 90%;
  max-width: 500px;
  padding: 24px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.modal-body {
  margin-bottom: 24px;
}

.modal-body p {
  margin: 0 0 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.input-wrapper {
  width: 100%;
}

.m3-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 1px solid var(--md-sys-color-outline-variant);
  border-radius: 8px;
  background: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  outline: none;
  transition: border-color 0.2s;
}

.m3-input:focus {
  border-color: var(--md-sys-color-primary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
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
  text-decoration: none;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.tonal {
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
}

.m3-button.text {
  background: transparent;
  color: var(--md-sys-color-primary);
}

.m3-button.text.error {
  color: var(--md-sys-color-error);
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
