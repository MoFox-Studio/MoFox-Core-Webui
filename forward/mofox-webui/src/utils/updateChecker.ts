import { ref } from 'vue'
import { checkUpdates } from '@/api/git_update'
import type { UpdateCheck } from '@/api/git_update'

// 全局更新信息
export const globalUpdateInfo = ref<UpdateCheck | null>(null)
export const hasNewUpdate = ref(false)

// 更新检查定时器
let updateCheckTimer: ReturnType<typeof setInterval> | null = null
const CHECK_INTERVAL = 5 * 60 * 1000 // 5分钟

// Toast 回调函数
let toastCallback: ((message: string, type: 'success' | 'error') => void) | null = null

// 设置 Toast 回调
export function setToastCallback(callback: (message: string, type: 'success' | 'error') => void) {
  toastCallback = callback
}

// 静默检查更新
async function silentCheckUpdate() {
  try {
    const response = await checkUpdates()
    if (response.success && response.data && response.data.success) {
      const hadUpdate = hasNewUpdate.value
      
      if (response.data.has_update) {
        globalUpdateInfo.value = response.data
        
        // 只在首次发现新版本时显示通知
        if (!hadUpdate) {
          hasNewUpdate.value = true
          if (toastCallback) {
            toastCallback('发现新版本，建议立即更新！', 'success')
          }
        }
      } else {
        // 如果之前有更新，现在没有了，重置状态
        if (hadUpdate) {
          hasNewUpdate.value = false
          globalUpdateInfo.value = null
        }
      }
    }
  } catch (error) {
    console.error('自动检查更新失败:', error)
  }
}

// 启动更新检查器
export function startUpdateChecker() {
  if (updateCheckTimer) {
    return // 已经启动，避免重复
  }

  // 立即执行一次检查
  silentCheckUpdate()

  // 启动定时检查
  updateCheckTimer = setInterval(() => {
    silentCheckUpdate()
  }, CHECK_INTERVAL)

  console.log('更新检查器已启动，每5分钟检查一次')
}

// 停止更新检查器
export function stopUpdateChecker() {
  if (updateCheckTimer) {
    clearInterval(updateCheckTimer)
    updateCheckTimer = null
    console.log('更新检查器已停止')
  }
}

// 手动触发一次检查
export async function manualCheckUpdate() {
  await silentCheckUpdate()
}

// 清除更新状态（用户查看更新后）
export function clearUpdateStatus() {
  // 不清除 globalUpdateInfo，只标记用户已知晓
  hasNewUpdate.value = false
}
