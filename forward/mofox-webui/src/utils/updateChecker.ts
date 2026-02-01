import { ref } from 'vue'
import { checkUpdates } from '@/api/git_update'
import type { UpdateCheck } from '@/api/git_update'
import { getUIStatus } from '@/api/ui_update'
import type { UIStatusResult } from '@/api/ui_update'

// 全局更新信息
export const globalUpdateInfo = ref<UpdateCheck | null>(null)
export const globalUIUpdateInfo = ref<UIStatusResult | null>(null)
export const hasNewUpdate = ref(false)

// 更新检查定时器
let updateCheckTimer: ReturnType<typeof setInterval> | null = null
const CHECK_INTERVAL = 5 * 60 * 1000 // 5分钟
const INITIAL_DELAY = 10 * 1000 // 首次检查延迟10秒，避免阻塞UI加载
const REQUEST_TIMEOUT = 10 * 1000 // 请求超时时间10秒

// 检查状态标志
let isChecking = false

// Toast 回调函数
let toastCallback: ((message: string, type: 'success' | 'error') => void) | null = null

// 设置 Toast 回调
export function setToastCallback(callback: (message: string, type: 'success' | 'error') => void) {
  toastCallback = callback
}

// 显示 Toast 提示（供其他模块调用）
export function showToast(message: string, type: 'success' | 'error' = 'success') {
  if (toastCallback) {
    toastCallback(message, type)
  } else {
    console.warn('Toast callback not set, message:', message)
  }
}

// 静默检查更新（带超时控制）
async function silentCheckUpdate() {
  // 避免并发检查
  if (isChecking) {
    return
  }
  
  isChecking = true
  
  try {
    // 使用 Promise.race 实现超时控制
    const timeoutPromise = new Promise<never>((_, reject) => {
      setTimeout(() => reject(new Error('Request timeout')), REQUEST_TIMEOUT)
    })
    
    // 并发检查主程序和 UI 更新
    const [backendResponse, uiResponse] = await Promise.all([
      Promise.race([checkUpdates(), timeoutPromise]).catch(err => {
        console.warn('主程序更新检查失败:', err)
        return null
      }),
      Promise.race([getUIStatus(), timeoutPromise]).catch(err => {
        console.warn('UI更新检查失败:', err)
        return null
      })
    ])
    
    const hadUpdate = hasNewUpdate.value
    let hasBackendUpdate = false
    let hasUIUpdate = false
    
    // 检查主程序更新
    if (backendResponse?.success && backendResponse.data?.success && backendResponse.data.has_update) {
      globalUpdateInfo.value = backendResponse.data
      hasBackendUpdate = true
    }
    
    // 检查 UI 更新
    if (uiResponse?.success && uiResponse.data?.success && uiResponse.data.has_update) {
      globalUIUpdateInfo.value = uiResponse.data
      hasUIUpdate = true
    }
    
    // 根据更新情况显示不同的通知
    if (hasBackendUpdate || hasUIUpdate) {
      hasNewUpdate.value = true
      
      // 只在首次发现新版本时显示通知
      if (!hadUpdate && toastCallback) {
        let message = ''
        if (hasBackendUpdate && hasUIUpdate) {
          message = '发现MoFox-Bot和UI新版本，建议立即更新！'
        } else if (hasBackendUpdate) {
          message = '发现MoFox-Bot新版本，建议立即更新！'
        } else if (hasUIUpdate) {
          message = '发现UI新版本，建议立即更新！'
        }
        if (message) {
          toastCallback(message, 'success')
        }
      }
    } else {
      // 如果之前有更新，现在没有了，重置状态
      if (hadUpdate) {
        hasNewUpdate.value = false
        globalUpdateInfo.value = null
        globalUIUpdateInfo.value = null
      }
    }
  } catch (error) {
    // 静默处理错误，不影响用户体验
    if (error instanceof Error && error.message === 'Request timeout') {
      console.warn('更新检查超时，可能网络不可达')
    } else {
      console.error('自动检查更新失败:', error)
    }
  } finally {
    isChecking = false
  }
}

// 启动更新检查器
export function startUpdateChecker() {
  if (updateCheckTimer) {
    return // 已经启动，避免重复
  }

  // 延迟首次检查，避免阻塞 UI 加载
  setTimeout(() => {
    silentCheckUpdate().catch(err => {
      console.error('首次更新检查失败:', err)
    })
  }, INITIAL_DELAY)

  // 启动定时检查
  updateCheckTimer = setInterval(() => {
    silentCheckUpdate().catch(err => {
      console.error('定时更新检查失败:', err)
    })
  }, CHECK_INTERVAL)

  console.log(`更新检查器已启动，${INITIAL_DELAY / 1000}秒后首次检查，之后每${CHECK_INTERVAL / 60000}分钟检查一次`)
}

// 检查更新检查器是否正在运行
export function isUpdateCheckerRunning(): boolean {
  return updateCheckTimer !== null
}

// 停止更新检查器
export function stopUpdateChecker() {
  if (updateCheckTimer) {
    clearInterval(updateCheckTimer)
    updateCheckTimer = null
    console.log('更新检查器已停止')
  }
}

// 手动触发一次检查（不受延迟和并发限制）
export async function manualCheckUpdate() {
  // 手动检查时重置状态，允许立即执行
  isChecking = false
  await silentCheckUpdate()
}

// 清除更新状态（用户查看更新后）
export function clearUpdateStatus() {
  // 不清除 globalUpdateInfo 和 globalUIUpdateInfo，只标记用户已知晓
  hasNewUpdate.value = false
}
