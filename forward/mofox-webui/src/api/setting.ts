import { api, getPluginBaseUrl } from './index'

/**
 * 上传壁纸
 * @param file 壁纸文件
 */
export async function uploadWallpaper(file: File): Promise<{ success: boolean; url: string; type: string; message?: string }> {
  const formData = new FormData()
  formData.append('file', file)

  const result = await api.request<{ url: string; type: string; message?: string }>('setting/wallpaper', {
    method: 'POST',
    body: formData
  })

  if (result.success && result.data) {
    return {
      success: true,
      url: result.data.url,
      type: result.data.type,
      message: result.data.message
    }
  } else {
    throw new Error(result.error || '上传失败')
  }
}

/**
 * 删除壁纸
 */
export async function deleteWallpaper(): Promise<{ success: boolean; message?: string }> {
  const result = await api.delete<{ message?: string }>('setting/wallpaper')
  
  if (result.success && result.data) {
    return {
      success: true,
      message: result.data.message
    }
  } else {
    throw new Error(result.error || '删除失败')
  }
}

/**
 * 获取壁纸图片URL
 * 注意：这只是构建URL，不发送请求
 */
export async function getWallpaperUrl(): Promise<string> {
  try {
    const baseUrl = await getPluginBaseUrl()
    // 添加时间戳防止缓存
    return `${baseUrl}/setting/wallpaper/image?t=${Date.now()}`
  } catch (error) {
    console.error('获取壁纸URL出错:', error)
    return ''
  }
}
