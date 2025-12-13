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
          <span v-else class="button-content">
            <Icon icon="lucide:log-in" />
            登录
          </span>
        </button>
      </form>

      <!-- 底部信息 -->
      <!-- <div class="footer-info">
        <p>© 2024 MoFox Bot · 安全登录</p>
      </div> -->
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
  background: #FDFBF7; /* Cream background */
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
  opacity: 0.6;
}

.orb-1 {
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, rgba(249, 115, 22, 0.2) 0%, rgba(251, 146, 60, 0.2) 100%);
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.orb-2 {
  width: 400px;
  height: 400px;
  background: linear-gradient(135deg, rgba(253, 186, 116, 0.2) 0%, rgba(254, 215, 170, 0.2) 100%);
  bottom: -100px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

.orb-3 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, rgba(255, 237, 213, 0.4) 0%, rgba(249, 115, 22, 0.1) 100%);
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
    opacity: 0.4;
  }
  50% {
    transform: translate(-50%, -50%) scale(1.1);
    opacity: 0.6;
  }
}

/* 主题切换按钮 */
.theme-toggle {
  position: fixed;
  top: 24px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0,0,0,0.05);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 100;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.theme-toggle:hover {
  background: white;
  transform: rotate(15deg);
  box-shadow: 0 8px 24px rgba(0,0,0,0.1);
  color: var(--primary);
}

/* 登录卡片 */
.login-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 24px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
  width: 100%;
  max-width: 420px;
  padding: 48px 40px;
  position: relative;
  z-index: 1;
  border: 1px solid rgba(255, 255, 255, 0.8);
  animation: slideUp 0.5s ease-out;
}

[data-theme="dark"] .login-card {
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.1);
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
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--primary) 0%, #ea580c 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  font-size: 40px;
  color: white;
  box-shadow: 0 12px 24px rgba(249, 115, 22, 0.3);
  transform: rotate(-5deg);
  transition: transform 0.3s ease;
}

.login-card:hover .logo-icon {
  transform: rotate(0deg) scale(1.05);
}

.logo-title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.logo-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  font-weight: 500;
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
  font-weight: 600;
  color: var(--text-primary);
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
  padding: 16px 48px 16px 20px;
  border: 2px solid transparent;
  border-radius: 12px;
  font-size: 16px;
  background: #f8fafc;
  color: var(--text-primary);
  transition: all 0.3s ease;
}

.form-input:focus {
  background: white;
  border-color: var(--primary);
  box-shadow: 0 0 0 4px rgba(249, 115, 22, 0.1);
}

.form-input::placeholder {
  color: #94a3b8;
}

.password-toggle {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s ease;
}

.password-toggle:hover {
  color: var(--primary);
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
  width: 22px;
  height: 22px;
  border: 2px solid #e2e8f0;
  border-radius: 6px;
  position: relative;
  transition: all 0.2s ease;
  background: white;
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
  width: 6px;
  height: 12px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.checkbox-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* 错误消息 */
.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fee2e2;
  border-radius: 12px;
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
}

@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0); }
  20%, 80% { transform: translate3d(2px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0); }
  40%, 60% { transform: translate3d(4px, 0, 0); }
}

/* 登录按钮 */
.login-button {
  width: 100%;
  padding: 16px 24px;
  background: linear-gradient(135deg, var(--primary) 0%, #ea580c 100%);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 20px -10px rgba(249, 115, 22, 0.5);
}

.button-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px -10px rgba(249, 115, 22, 0.6);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  box-shadow: none;
  filter: grayscale(0.5);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.3);
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
    border-radius: 20px;
  }
  
  .logo-icon {
    width: 64px;
    height: 64px;
    font-size: 32px;
  }
  
  .logo-title {
    font-size: 28px;
  }
}
</style>
