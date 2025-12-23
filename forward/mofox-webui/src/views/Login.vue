<template>
  <div class="login-wrapper" :class="{ 'dark-mode': themeStore.theme === 'dark' }">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>
    
    <!-- 顶部操作栏 -->
    <div class="top-actions">
      <a href="https://github.com/MoFox-Studio/MoFox-Core" target="_blank" class="m3-icon-button github-link" title="GitHub">
        <svg viewBox="0 0 24 24" width="24" height="24" class="github-icon">
          <path fill="currentColor" d="M12 2A10 10 0 0 0 2 12c0 4.42 2.87 8.17 6.84 9.5c.5.08.66-.23.66-.5v-1.69c-2.77.6-3.36-1.34-3.36-1.34c-.46-1.16-1.11-1.47-1.11-1.47c-.91-.62.07-.6.07-.6c1 .07 1.53 1.03 1.53 1.03c.87 1.52 2.34 1.07 2.91.83c.09-.65.35-1.09.63-1.34c-2.22-.25-4.55-1.11-4.55-4.92c0-1.11.38-2 1.03-2.71c-.1-.25-.45-1.29.1-2.64c0 0 .84-.27 2.75 1.02c.79-.22 1.65-.33 2.5-.33c.85 0 1.71.11 2.5.33c1.91-1.29 2.75-1.02 2.75-1.02c.55 1.35.2 2.39.1 2.64c.65.71 1.03 1.6 1.03 2.71c0 3.82-2.34 4.66-4.57 4.91c.36.31.69.92.69 1.85V21c0 .27.16.59.67.5C19.14 20.16 22 16.42 22 12A10 10 0 0 0 12 2z"/>
        </svg>
      </a>
      <button class="m3-icon-button theme-toggle" @click="themeStore.toggleTheme" title="切换主题">
        <span class="material-symbols-rounded">
          {{ themeStore.theme === 'light' ? 'dark_mode' : 'light_mode' }}
        </span>
      </button>
    </div>

    <!-- 登录卡片 -->
    <div class="m3-card login-card">
      <!-- Logo区域 -->
      <div class="logo-section">
        <div class="logo-icon">
          <span class="material-symbols-rounded">smart_toy</span>
        </div>
        <h1 class="logo-title">MoFox</h1>
        <p class="logo-subtitle">智能机器人管理控制台</p>
      </div>
      
      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="m3-label">
            <span class="material-symbols-rounded label-icon">key</span>
            访问密钥
          </label>
          <div class="input-wrapper">
            <input 
              v-model="loginForm.password"
              :type="showPassword ? 'text' : 'password'"
              class="m3-input" 
              placeholder="请输入访问密钥"
              required
            >
            <button 
              type="button" 
              class="m3-icon-button password-toggle"
              @click="showPassword = !showPassword"
            >
              <span class="material-symbols-rounded">
                {{ showPassword ? 'visibility_off' : 'visibility' }}
              </span>
            </button>
          </div>
        </div>
        
        <div class="form-options">
          <label class="m3-checkbox-wrapper">
            <input v-model="loginForm.remember" type="checkbox">
            <span class="checkmark"></span>
            <span class="checkbox-label">记住登录状态</span>
          </label>
        </div>

        <div v-if="errorMessage" class="error-message">
          <span class="material-symbols-rounded">error</span>
          <span>{{ errorMessage }}</span>
        </div>
        
        <button type="submit" class="m3-button filled login-button" :disabled="loading">
          <span v-if="loading" class="material-symbols-rounded spinning">progress_activity</span>
          <span v-else class="button-content">
            <span class="material-symbols-rounded">login</span>
            登录
          </span>
        </button>
      </form>


    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { api, API_ENDPOINTS } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const themeStore = useThemeStore()
const loading = ref(false)
const errorMessage = ref('')
const showPassword = ref(false)

const loginForm = reactive({
  password: '',
  remember: false
})

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  
  try {
    // 先设置 token 用于请求
    api.setToken(loginForm.password)
    
    // 调用登录 API
    const result = await api.get<{ success: boolean; error?: string }>(API_ENDPOINTS.AUTH.LOGIN)

    if (result.success && result.data?.success) {
      // 登录成功，保存到 store
      userStore.login(loginForm.password)
      router.push('/dashboard')
    } else if (result.status === 401 || result.status === 403) {
      // 清除无效的 token
      api.setToken(null)
      errorMessage.value = '密钥错误，请检查后重试'
    } else {
      api.setToken(null)
      errorMessage.value = result.error || '登录失败'
    }
  } catch (error) {
    console.error('Login error:', error)
    api.setToken(null)
    errorMessage.value = '连接服务器失败，请确保Bot已启动且插件正常运行'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
  background: var(--md-sys-color-background);
}

/* 背景装饰 */
.bg-decoration {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.gradient-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, var(--md-sys-color-primary) 0%, var(--md-sys-color-primary-container) 100%);
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, var(--md-sys-color-secondary) 0%, var(--md-sys-color-tertiary) 100%);
  bottom: -100px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, var(--md-sys-color-tertiary) 0%, var(--md-sys-color-primary) 100%);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: pulse 10s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-30px) rotate(5deg);
  }
}

@keyframes pulse {
  0%, 100% {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.3;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.5;
  }
}

/* 顶部操作栏 */
.top-actions {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 100;
  display: flex;
  gap: 12px;
}

.top-actions .m3-icon-button {
  background: var(--md-sys-color-surface-container-high);
  box-shadow: var(--md-sys-elevation-2);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  cursor: pointer;
  color: var(--md-sys-color-on-surface-variant);
  transition: all 0.2s;
}

.top-actions .m3-icon-button:hover {
  background: var(--md-sys-color-surface-container-highest);
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-3);
}

.github-link {
  text-decoration: none;
}

/* 登录卡片 */
.login-card {
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  position: relative;
  z-index: 1;
  animation: slideUp 0.5s ease-out;
  background: var(--md-sys-color-surface-container);
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

/* Logo区域 */
.logo-section {
  text-align: center;
  margin-bottom: 40px;
}

.logo-icon {
  width: 72px;
  height: 72px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  box-shadow: var(--md-sys-elevation-3);
}

.logo-icon .material-symbols-rounded {
  font-size: 40px;
}

.logo-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.logo-subtitle {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  font-weight: 400;
}

/* 表单样式 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.m3-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-on-surface-variant);
}

.label-icon {
  font-size: 18px;
  color: var(--md-sys-color-primary);
}

.input-wrapper {
  position: relative;
}

.m3-input {
  width: 100%;
  padding-right: 48px;
}

.password-toggle {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--md-sys-color-on-surface-variant);
}

/* 表单选项 */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.m3-checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
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
  top: -1px;
  width: 4px;
  height: 10px;
  border: solid var(--md-sys-color-on-primary);
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label {
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--md-sys-color-error-container);
  border-radius: 12px;
  color: var(--md-sys-color-on-error-container);
  font-size: 14px;
}

.error-message .material-symbols-rounded {
  font-size: 20px;
}

/* 登录按钮 */
.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.button-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 底部信息 */
.footer-info {
  margin-top: 32px;
  text-align: center;
}

.footer-info p {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }
  
  .logo-icon {
    width: 60px;
    height: 60px;
  }
  
  .logo-icon .material-symbols-rounded {
    font-size: 32px;
  }
  
  .logo-title {
    font-size: 24px;
  }
}
</style>
