/**
 * 对话框工具
 * 提供统一的对话框API
 */

import { createApp, h } from 'vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

export interface DialogOptions {
  title?: string
  message: string
  type?: 'info' | 'success' | 'warning' | 'danger'
  confirmText?: string
  cancelText?: string
}

/**
 * 显示确认对话框
 */
export function showConfirm(options: DialogOptions): Promise<boolean> {
  return new Promise((resolve) => {
    const container = document.createElement('div')
    document.body.appendChild(container)
    let isDestroyed = false

    const cleanup = () => {
      if (isDestroyed) return
      isDestroyed = true
      app.unmount()
      if (container.parentNode) {
        container.parentNode.removeChild(container)
      }
    }

    const app = createApp({
      data() {
        return {
          visible: true
        }
      },
      methods: {
        handleConfirm() {
          this.visible = false
          setTimeout(() => {
            cleanup()
            resolve(true)
          }, 300)
        },
        handleCancel() {
          this.visible = false
          setTimeout(() => {
            cleanup()
            resolve(false)
          }, 300)
        }
      },
      render() {
        return h(ConfirmDialog, {
          visible: this.visible,
          title: options.title,
          message: options.message,
          type: options.type || 'info',
          showCancel: true,
          confirmText: options.confirmText || '确定',
          cancelText: options.cancelText || '取消',
          onConfirm: this.handleConfirm,
          onCancel: this.handleCancel,
          'onUpdate:visible': (val: boolean) => {
            if (!val) {
              this.handleCancel()
            }
          }
        })
      }
    })

    app.mount(container)
  })
}

/**
 * 显示提示对话框（只有确定按钮）
 */
export function showAlert(options: DialogOptions): Promise<void> {
  return new Promise((resolve) => {
    const container = document.createElement('div')
    document.body.appendChild(container)
    let isDestroyed = false

    const cleanup = () => {
      if (isDestroyed) return
      isDestroyed = true
      app.unmount()
      if (container.parentNode) {
        container.parentNode.removeChild(container)
      }
    }

    const app = createApp({
      data() {
        return {
          visible: true
        }
      },
      methods: {
        handleConfirm() {
          this.visible = false
          setTimeout(() => {
            cleanup()
            resolve()
          }, 300)
        }
      },
      render() {
        return h(ConfirmDialog, {
          visible: this.visible,
          title: options.title,
          message: options.message,
          type: options.type || 'info',
          showCancel: false,
          confirmText: options.confirmText || '确定',
          onConfirm: this.handleConfirm,
          'onUpdate:visible': (val: boolean) => {
            if (!val) {
              this.handleConfirm()
            }
          }
        })
      }
    })

    app.mount(container)
  })
}

/**
 * 显示成功提示
 */
export function showSuccess(message: string, title = '成功'): Promise<void> {
  return showAlert({
    title,
    message,
    type: 'success',
    confirmText: '好的'
  })
}

/**
 * 显示错误提示
 */
export function showError(message: string, title = '错误'): Promise<void> {
  return showAlert({
    title,
    message,
    type: 'danger',
    confirmText: '知道了'
  })
}

/**
 * 显示警告提示
 */
export function showWarning(message: string, title = '警告'): Promise<void> {
  return showAlert({
    title,
    message,
    type: 'warning',
    confirmText: '明白了'
  })
}
