<template>
  <div class="login-wrapper" :class="{ 'dark-mode': themeStore.theme === 'dark' }">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="gradient-orb orb-1"></div>
      <div class="gradient-orb orb-2"></div>
      <div class="gradient-orb orb-3"></div>
    </div>
    
    <!-- 主题切换按钮 -->
    <button class="theme-toggle" @click="themeStore.toggleTheme" title="切换主题">
      <Icon :icon="themeStore.theme === 'light' ? 'lucide:moon' : 'lucide:sun'" />
    </button>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- Logo区域 -->
      <div class="logo-section">
        <div class="logo-icon">
          <Icon icon="lucide:bot" />
        </div>
        <h1 class="logo-title">MoFox</h1>
        <p class="logo-subtitle">智能机器人管理控制台</p>
      </div>
      
      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label">
            <Icon icon="lucide:key" class="label-icon" />
            访问密钥
          </label>
          <div class="input-wrapper">
            <input 
              v-model="loginForm.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-input" 
              placeholder="请输入访问密钥"
              required
            >
            <button 
              type="button" 
              class="password-toggle"
              @click="showPassword = !showPassword"
            >
              <Icon :icon="showPassword ? 'lucide:eye-off' : 'lucide:eye'" />
            </button>
          </div>
        </div>
        
        <div class="form-options">
          <label class="checkbox-wrapper">
            <input v-model="loginForm.remember" type="checkbox">
            <span class="checkmark"></span>
            <span class="checkbox-label">记住登录状态</span>
          </label>
        </div>

        <div v-if="errorMessage" class="error-message">
          <Icon icon="lucide:alert-circle" />
          <span>{{ errorMessage }}</span>
        </div>
        
        <button type="submit" class="login-button" :disabled="loading">
          <span v-if="loading" class="loading-spinner"></span>
          <span v-else>
            <Icon icon="lucide:log-in" />
            登录
          </span>
        </button>
      </form>

      <!-- 底部信息 -->
      <div class="footer-info">
        <p>© 2024 MoFox Bot · 安全登录</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { Icon } from '@iconify/vue'
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
  background: var(--bg-secondary);
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
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, var(--primary-light) 0%, #8b5cf6 100%);
  bottom: -100px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, #06b6d4 0%, var(--primary) 100%);
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

/* 主题切换按钮 */
.theme-toggle {
  position: fixed;
  top: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  transition: all var(--transition);
  z-index: 100;
  box-shadow: var(--shadow-md);
}

.theme-toggle:hover {
  background: var(--bg-hover);
  transform: rotate(15deg);
}

/* 登录卡片 */
.login-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  position: relative;
  z-index: 1;
  border: 1px solid var(--border-color);
  animation: slideUp 0.5s ease-out;
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
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 36px;
  color: white;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.3);
}

.logo-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.logo-subtitle {
  font-size: 14px;
  color: var(--text-tertiary);
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

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.label-icon {
  font-size: 16px;
  color: var(--primary);
}

.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  padding: 14px 48px 14px 16px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 15px;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.form-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-bg);
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.password-toggle {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-tertiary);
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.password-toggle:hover {
  color: var(--text-secondary);
}

/* 表单选项 */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}

.checkbox-wrapper input {
  display: none;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border-color);
  border-radius: var(--radius-sm);
  position: relative;
  transition: all var(--transition-fast);
}

.checkbox-wrapper input:checked + .checkmark {
  background: var(--primary);
  border-color: var(--primary);
}

.checkbox-wrapper input:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 6px;
  top: 2px;
  width: 5px;
  height: 10px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--danger-bg);
  border: 1px solid var(--danger);
  border-radius: var(--radius);
  color: var(--danger);
  font-size: 14px;
}

/* 登录按钮 */
.login-button {
  width: 100%;
  padding: 14px 24px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.4);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
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
  color: var(--text-tertiary);
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
    border-radius: var(--radius-lg);
  }
  
  .logo-icon {
    width: 60px;
    height: 60px;
    font-size: 30px;
  }
  
  .logo-title {
    font-size: 24px;
  }
}
</style>
