/**
 * 表情包管理 Store
 */

import { defineStore } from 'pinia'
import type { EmojiItem, GetEmojiListParams } from '@/api/emoji'
import * as emojiApi from '@/api/emoji'

export interface EmojiState {
  items: EmojiItem[]
  total: number
  page: number
  pageSize: number
  totalPages: number
  loading: boolean
  selectedItems: Set<string>
  searchQuery: string
  sortBy: string
  sortOrder: 'asc' | 'desc'
  isRegisteredFilter: boolean | null
  isBannedFilter: boolean | null
}

export const useEmojiStore = defineStore('emoji', {
  state: (): EmojiState => ({
    items: [],
    total: 0,
    page: 1,
    pageSize: 50,
    totalPages: 0,
    loading: false,
    selectedItems: new Set(),
    searchQuery: '',
    sortBy: 'record_time',
    sortOrder: 'desc',
    isRegisteredFilter: null,
    isBannedFilter: null
  }),

  getters: {
    /**
     * 是否有选中的表情包
     */
    hasSelection: (state) => state.selectedItems.size > 0,

    /**
     * 选中的表情包数量
     */
    selectionCount: (state) => state.selectedItems.size,

    /**
     * 是否全部选中
     */
    isAllSelected: (state) => {
      if (state.items.length === 0) return false
      return state.items.every(item => state.selectedItems.has(item.hash))
    },

    /**
     * 获取当前筛选参数
     */
    currentParams: (state): GetEmojiListParams => ({
      page: state.page,
      page_size: state.pageSize,
      search: state.searchQuery || undefined,
      sort_by: state.sortBy,
      sort_order: state.sortOrder,
      is_registered: state.isRegisteredFilter ?? undefined,
      is_banned: state.isBannedFilter ?? undefined
    })
  },

  actions: {
    /**
     * 获取表情包列表
     */
    async fetchEmojiList() {
      this.loading = true
      console.log('[EmojiStore] 准备请求列表, searchQuery:', this.searchQuery)
      console.log('[EmojiStore] 请求参数:', this.currentParams)
      try {
        const response = await emojiApi.getEmojiList(this.currentParams)
        
        if (response?.success) {
          const { items, total, page, page_size, total_pages } = response.data
          this.items = items
          this.total = total
          this.page = page
          this.pageSize = page_size
          this.totalPages = total_pages
        }
      } catch (error) {
        console.error('获取表情包列表失败:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    /**
     * 获取表情包详情
     */
    async getEmojiDetail(hash: string) {
      try {
        const response = await emojiApi.getEmojiDetail(hash)
        return response?.success ? response.data : null
      } catch (error) {
        console.error('获取表情包详情失败:', error)
        throw error
      }
    },

    /**
     * 上传表情包
     */
    async uploadEmojis(files: File[]) {
      try {
        const response = await emojiApi.uploadEmojis(files)
        if (response?.success) {
          await this.fetchEmojiList()
          return response.data
        }
        throw new Error('上传失败')
      } catch (error) {
        console.error('上传表情包失败:', error)
        throw error
      }
    },

    /**
     * 删除表情包
     */
    async deleteEmoji(hash: string) {
      try {
        const response = await emojiApi.deleteEmoji(hash)
        if (response?.success) {
          await this.fetchEmojiList()
          this.selectedItems.delete(hash)
          return true
        }
        return false
      } catch (error) {
        console.error('删除表情包失败:', error)
        throw error
      }
    },

    /**
     * 更新表情包
     */
    async updateEmoji(hash: string, data: { description?: string; is_banned?: boolean }) {
      try {
        const response = await emojiApi.updateEmoji(hash, data)
        if (response?.success) {
          await this.fetchEmojiList()
          return response.data
        }
        throw new Error('更新失败')
      } catch (error) {
        console.error('更新表情包失败:', error)
        throw error
      }
    },

    /**
     * 批量删除表情包
     */
    async batchDelete(hashes: string[]) {
      try {
        const response = await emojiApi.batchOperationEmojis('delete', hashes)
        if (response?.success) {
          await this.fetchEmojiList()
          hashes.forEach(hash => this.selectedItems.delete(hash))
          return response.data
        }
        throw new Error('批量删除失败')
      } catch (error) {
        console.error('批量删除失败:', error)
        throw error
      }
    },

    /**
     * 批量禁用表情包
     */
    async batchBan(hashes: string[]) {
      try {
        const response = await emojiApi.batchOperationEmojis('ban', hashes)
        if (response?.success) {
          await this.fetchEmojiList()
          return response.data
        }
        throw new Error('批量禁用失败')
      } catch (error) {
        console.error('批量禁用失败:', error)
        throw error
      }
    },

    /**
     * 批量启用表情包
     */
    async batchUnban(hashes: string[]) {
      try {
        const response = await emojiApi.batchOperationEmojis('unban', hashes)
        if (response?.success) {
          await this.fetchEmojiList()
          return response.data
        }
        throw new Error('批量启用失败')
      } catch (error) {
        console.error('批量启用失败:', error)
        throw error
      }
    },

    /**
     * 获取统计信息
     */
    async getStats() {
      try {
        const response = await emojiApi.getEmojiStats()
        return response?.success ? response.data : null
      } catch (error) {
        console.error('获取统计信息失败:', error)
        return null
      }
    },

    /**
     * 切换选中状态
     */
    toggleSelection(hash: string) {
      if (this.selectedItems.has(hash)) {
        this.selectedItems.delete(hash)
      } else {
        this.selectedItems.add(hash)
      }
    },

    /**
     * 全选/取消全选
     */
    toggleSelectAll() {
      if (this.isAllSelected) {
        this.clearSelection()
      } else {
        this.items.forEach(item => this.selectedItems.add(item.hash))
      }
    },

    /**
     * 清空选中
     */
    clearSelection() {
      this.selectedItems.clear()
    },

    /**
     * 设置搜索关键词
     */
    setSearchQuery(query: string) {
      console.log('[EmojiStore] setSearchQuery 被调用, 参数:', query)
      this.searchQuery = query
      this.page = 1
      console.log('[EmojiStore] searchQuery 已设置为:', this.searchQuery)
    },

    /**
     * 设置排序
     */
    setSorting(sortBy: string, sortOrder: 'asc' | 'desc') {
      this.sortBy = sortBy
      this.sortOrder = sortOrder
      this.page = 1
    },

    /**
     * 设置页码
     */
    setPage(page: number) {
      this.page = page
    },

    /**
     * 设置每页数量
     */
    setPageSize(pageSize: number) {
      this.pageSize = pageSize
      this.page = 1
    },

    /**
     * 重置筛选条件
     */
    resetFilters() {
      this.searchQuery = ''
      this.isRegisteredFilter = null
      this.isBannedFilter = null
      this.sortBy = 'record_time'
      this.sortOrder = 'desc'
      this.page = 1
    }
  }
})
