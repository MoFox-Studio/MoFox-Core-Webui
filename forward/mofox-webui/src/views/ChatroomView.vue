<!--
  @file ChatroomView.vue
  @description UI 聊天室页面
  
  功能说明：
  1. 创建和管理虚拟用户
  2. 与 Bot 进行对话测试
  3. 查看聊天历史
  4. 编辑用户信息和印象
  5. 重置用户关系
  
  布局结构：
  - 左侧：虚拟用户列表
  - 右侧：聊天界面（消息列表 + 输入框）
  
  消息类型：
  - 普通消息：用户/Bot 发送的消息
  - 系统消息：状态通知横幅
  - 引用消息：回复特定消息
  
  用户管理：
  - 创建虚拟用户（昵称、头像、印象）
  - 编辑用户信息
  - 删除用户
-->
<template>
  <div class="chatroom-view">
    <!-- 左侧：虚拟用户列表面板 -->
    <aside class="user-panel m3-card">
      <div class="panel-header">
        <div class="header-content">
          <span class="material-symbols-rounded">people</span>
          <h2>虚拟用户</h2>
        </div>
        <button class="m3-button icon-only" @click="showCreateUserDialog = true" title="创建用户">
          <span class="material-symbols-rounded">person_add</span>
        </button>
      </div>
      
      <div class="user-list">
        <div 
          v-for="user in users" 
          :key="user.user_id"
          class="user-item"
          :class="{ active: selectedUser?.user_id === user.user_id }"
          @click="selectUser(user)"
        >
          <div class="user-avatar">
            <img v-if="user.avatar" :src="user.avatar" :alt="user.nickname" />
            <span v-else class="material-symbols-rounded">account_circle</span>
          </div>
          <div class="user-info">
            <div class="user-name">{{ user.nickname }}</div>
            <div class="user-id">{{ user.user_id }}</div>
          </div>
          <button 
            class="m3-icon-button delete-btn" 
            @click.stop="confirmDeleteUser(user)"
            title="删除用户"
          >
            <span class="material-symbols-rounded">delete</span>
          </button>
        </div>
        
        <div v-if="users.length === 0" class="empty-state">
          <span class="material-symbols-rounded">group_off</span>
          <p>暂无虚拟用户</p>
          <button class="m3-button filled" @click="showCreateUserDialog = true">
            创建第一个用户
          </button>
        </div>
      </div>
    </aside>

    <!-- 右侧：聊天区域 -->
    <main class="chat-panel m3-card">
      <!-- 顶部栏 -->
      <header class="chat-header">
        <div v-if="selectedUser" class="header-content">
          <div class="user-avatar">
            <img v-if="selectedUser.avatar" :src="selectedUser.avatar" :alt="selectedUser.nickname" />
            <span v-else class="material-symbols-rounded">account_circle</span>
          </div>
          <div class="user-info">
            <h2>{{ selectedUser.nickname }}</h2>
            <p v-if="selectedUser.impression">{{ selectedUser.impression }}</p>
          </div>
        </div>
        <div v-else class="header-placeholder">
          <span class="material-symbols-rounded">chat</span>
          <span>UI 聊天室</span>
        </div>
        
        <div class="header-actions">
          <button
            v-if="selectedUser"
            class="m3-button icon-only"
            @click="showResetConfirm = true"
            title="重置关系"
          >
            <span class="material-symbols-rounded">restart_alt</span>
          </button>
          <button
            v-if="selectedUser"
            class="m3-button icon-only"
            @click="showEditUserDialog = true"
            title="编辑用户"
          >
            <span class="material-symbols-rounded">edit</span>
          </button>
          <button
            class="m3-button icon-only"
            @click="loadMessages"
            title="刷新消息"
          >
            <span class="material-symbols-rounded">refresh</span>
          </button>
        </div>
      </header>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="!selectedUser" class="welcome-state">
          <span class="material-symbols-rounded">forum</span>
          <h3>欢迎使用 UI 聊天室</h3>
          <p>选择一个虚拟用户开始对话</p>
        </div>

        <div v-else-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载消息中...</p>
        </div>

        <div v-else class="messages-list">
          <!-- 系统消息使用横幅样式 -->
          <div 
            v-for="msg in messages" 
            :key="msg.message_id"
            :class="{
              'message': msg.user_id !== 'system',
              'system-banner': msg.user_id === 'system',
              'is-bot': msg.user_id === 'mofox_bot',
              'is-user': msg.user_id !== 'mofox_bot' && msg.user_id !== 'system'
            }"
          >
            <!-- 系统消息横幅 -->
            <template v-if="msg.user_id === 'system'">
              <div class="banner-icon">
                <span class="material-symbols-rounded">info</span>
              </div>
              <div class="banner-content">
                <span class="banner-text">{{ msg.content }}</span>
              </div>
            </template>

            <!-- 普通消息 -->
            <template v-else>
              <div class="message-avatar">
                <span class="material-symbols-rounded">
                  {{ msg.user_id === 'mofox_bot' ? 'smart_toy' : 'account_circle' }}
                </span>
              </div>
              <div class="message-content">
                <div class="message-header">
                  <span class="message-sender">{{ msg.nickname }}</span>
                  <span class="message-time">{{ formatTime(msg.timestamp) }}</span>
                </div>
                
                <!-- 引用消息 -->
                <div v-if="msg.reply_to && getQuotedMessage(msg.reply_to)" class="message-quote">
                  <div class="quote-line"></div>
                  <div class="quote-content">
                    <span class="quote-author">{{ getQuotedMessage(msg.reply_to)?.nickname }}</span>
                    <span class="quote-text">{{ getQuotedMessage(msg.reply_to)?.content }}</span>
                  </div>
                </div>
                
                <!-- 文本内容 -->
                <div v-if="msg.content" class="message-text">{{ msg.content }}</div>
                
                <!-- 表情包显示 -->
                <div v-if="msg.emojis && msg.emojis.length > 0" class="message-emojis">
                  <img 
                    v-for="(emoji, idx) in msg.emojis" 
                    :key="idx"
                    :src="`data:image/png;base64,${emoji}`"
                    class="emoji-image"
                    alt="emoji"
                  />
                </div>
              </div>
            </template>
          </div>
          
          <div v-if="messages.length === 0" class="empty-messages">
            <span class="material-symbols-rounded">chat_bubble_outline</span>
            <p>还没有消息，发送第一条消息开始对话吧！</p>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <footer class="input-area">
        <div class="input-container">
          <div class="input-wrapper" :class="{ focused: isInputFocused }">
            <textarea
              v-model="inputMessage"
              class="message-input"
              placeholder="输入消息..."
              rows="1"
              :disabled="!selectedUser || sending"
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResize"
              @focus="isInputFocused = true"
              @blur="isInputFocused = false"
              ref="messageInput"
            ></textarea>
          </div>
          <button 
            class="m3-button fab" 
            :disabled="!inputMessage.trim() || !selectedUser || sending"
            @click="sendMessage"
            title="发送 (Enter)"
          >
            <span class="material-symbols-rounded">{{ sending ? 'hourglass_empty' : 'send' }}</span>
          </button>
        </div>
      </footer>
    </main>

    <!-- 创建用户对话框 -->
    <Teleport to="body">
      <Transition name="dialog">
        <div v-if="showCreateUserDialog" class="dialog-overlay" @click.self="showCreateUserDialog = false">
          <div class="m3-dialog">
            <div class="dialog-header">
              <h3>创建虚拟用户</h3>
              <button class="m3-icon-button" @click="showCreateUserDialog = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            
            <div class="dialog-content">
              <!-- 复制用户区域 -->
              <div class="copy-user-section">
                <div class="section-title">从现有用户复制</div>
                <div class="input-row">
                  <div class="input-group half">
                    <label>平台</label>
                    <div 
                      class="custom-select-container"
                      :class="{ 'is-open': isPlatformDropdownOpen }"
                    >
                      <div 
                        class="custom-select-trigger"
                        @click="togglePlatformDropdown"
                      >
                        <span>{{ copyPlatform || '全部平台' }}</span>
                        <span class="material-symbols-rounded select-arrow">expand_more</span>
                      </div>
                      
                      <Transition name="select-fade">
                        <div v-if="isPlatformDropdownOpen" class="custom-select-dropdown">
                          <div 
                            class="custom-select-option"
                            :class="{ 'is-selected': copyPlatform === '' }"
                            @click="selectPlatform('')"
                          >
                            全部平台
                            <span v-if="copyPlatform === ''" class="material-symbols-rounded check-icon">check</span>
                          </div>
                          <div 
                            v-for="p in platforms" 
                            :key="p" 
                            class="custom-select-option"
                            :class="{ 'is-selected': copyPlatform === p }"
                            @click="selectPlatform(p)"
                          >
                            {{ p }}
                            <span v-if="copyPlatform === p" class="material-symbols-rounded check-icon">check</span>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                  
                  <div class="input-group half">
                    <label>选择用户</label>
                    <div 
                      class="custom-select-container"
                      :class="{ 'is-open': isUserDropdownOpen }"
                    >
                      <div 
                        class="custom-select-trigger"
                        @click="toggleUserDropdown"
                      >
                        <span>{{ selectedCopyUser ? `${selectedCopyUser.nickname} (${selectedCopyUser.platform})` : '不复制' }}</span>
                        <span class="material-symbols-rounded select-arrow">expand_more</span>
                      </div>
                      
                      <Transition name="select-fade">
                        <div v-if="isUserDropdownOpen" class="custom-select-dropdown">
                          <div 
                            class="custom-select-option"
                            :class="{ 'is-selected': selectedCopyUser === null }"
                            @click="selectCopyUser(null)"
                          >
                            不复制
                            <span v-if="selectedCopyUser === null" class="material-symbols-rounded check-icon">check</span>
                          </div>
                          <div 
                            v-for="user in filteredCopyableUsers" 
                            :key="user.person_id" 
                            class="custom-select-option"
                            :class="{ 'is-selected': selectedCopyUser?.person_id === user.person_id }"
                            @click="selectCopyUser(user)"
                          >
                            {{ user.nickname }} ({{ user.platform }})
                            <span v-if="selectedCopyUser?.person_id === user.person_id" class="material-symbols-rounded check-icon">check</span>
                          </div>
                        </div>
                      </Transition>
                    </div>
                  </div>
                </div>
              </div>
              
              <div class="divider"></div>

              <div class="input-group">
                <label>用户ID * <span class="hint">(仅限数字)</span></label>
                <div class="input-with-action">
                  <input v-model="newUser.user_id" type="text" class="m3-input" placeholder="例如: 10001" pattern="[0-9]+" />
                  <button class="m3-icon-button" @click="generateRandomId" title="随机生成">
                    <span class="material-symbols-rounded">refresh</span>
                  </button>
                </div>
              </div>
              
              <div class="input-group">
                <label>昵称 *</label>
                <input v-model="newUser.nickname" type="text" class="m3-input" placeholder="例如: 小明" />
              </div>
              
              <div class="input-group">
                <label>详细印象/性格描述</label>
                <textarea 
                  v-model="newUser.impression" 
                  class="m3-input" 
                  rows="3"
                  placeholder="例如: 活泼开朗，喜欢聊天，经常分享生活趣事..."
                ></textarea>
              </div>
              
              <div class="input-group">
                <label>简短印象</label>
                <input v-model="newUser.short_impression" type="text" class="m3-input" placeholder="例如: 活泼开朗" />
              </div>

              <div class="input-group">
                <div class="label-row">
                  <label>记忆点</label>
                  <button class="m3-button text small" @click="addMemoryPoint(newUser.memory_points)">
                    <span class="material-symbols-rounded">add</span>
                    添加
                  </button>
                </div>
                <div class="memory-points-list">
                  <div v-for="(point, index) in newUser.memory_points" :key="index" class="memory-point-item">
                    <div class="point-header">
                      <span class="point-label">记忆点 #{{ index + 1 }}</span>
                      <button class="m3-icon-button small" @click="removeMemoryPoint(newUser.memory_points, index)">
                        <span class="material-symbols-rounded">delete</span>
                      </button>
                    </div>
                    <div class="point-content">
                      <textarea 
                        v-model="point.content" 
                        class="m3-input" 
                        rows="2"
                        placeholder="输入记忆内容..."
                      ></textarea>
                    </div>
                    <div class="point-weight">
                      <label>重要度: {{ point.weight }}</label>
                      <input 
                        v-model.number="point.weight" 
                        type="range" 
                        min="0.1" 
                        max="2.0" 
                        step="0.1" 
                        class="m3-slider"
                      />
                    </div>
                  </div>
                  <div v-if="newUser.memory_points.length === 0" class="empty-points">
                    暂无记忆点
                  </div>
                </div>
              </div>
              
              <div class="input-group">
                <label>态度值 (-100 到 100)</label>
                <input v-model.number="newUser.attitude" type="number" class="m3-input" min="-100" max="100" placeholder="0" />
              </div>
              
              <div class="input-group">
                <label>头像URL (可选)</label>
                <input v-model="newUser.avatar" type="text" class="m3-input" placeholder="https://..." />
              </div>
            </div>
            
            <div class="dialog-actions">
              <button class="m3-button text" @click="showCreateUserDialog = false">取消</button>
              <button 
                class="m3-button filled" 
                :disabled="!newUser.user_id || !newUser.nickname || creating"
                @click="createUser"
              >
                {{ creating ? '创建中...' : '创建' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 编辑用户对话框 -->
    <Teleport to="body">
      <Transition name="dialog">
        <div v-if="showEditUserDialog" class="dialog-overlay" @click.self="showEditUserDialog = false">
          <div class="m3-dialog">
            <div class="dialog-header">
              <h3>编辑用户</h3>
              <button class="m3-icon-button" @click="showEditUserDialog = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            
            <div class="dialog-content">
              <div class="input-group">
                <label>昵称</label>
                <input v-model="editUser.nickname" type="text" class="m3-input" />
              </div>
              
              <div class="input-group">
                <label>详细印象/性格描述</label>
                <textarea 
                  v-model="editUser.impression" 
                  class="m3-input" 
                  rows="3"
                  placeholder="详细描述用户的印象和性格特点..."
                ></textarea>
              </div>
              
              <div class="input-group">
                <label>简短印象</label>
                <input v-model="editUser.short_impression" type="text" class="m3-input" placeholder="用简短词语概括" />
              </div>

              <div class="input-group">
                <div class="label-row">
                  <label>记忆点</label>
                  <button class="m3-button text small" @click="addMemoryPoint(editUser.memory_points)">
                    <span class="material-symbols-rounded">add</span>
                    添加
                  </button>
                </div>
                <div class="memory-points-list">
                  <div v-for="(point, index) in editUser.memory_points" :key="index" class="memory-point-item">
                    <div class="point-header">
                      <span class="point-label">记忆点 #{{ index + 1 }}</span>
                      <button class="m3-icon-button small" @click="removeMemoryPoint(editUser.memory_points, index)">
                        <span class="material-symbols-rounded">delete</span>
                      </button>
                    </div>
                    <div class="point-content">
                      <textarea 
                        v-model="point.content" 
                        class="m3-input" 
                        rows="2"
                        placeholder="输入记忆内容..."
                      ></textarea>
                    </div>
                    <div class="point-weight">
                      <label>重要度: {{ point.weight }}</label>
                      <input 
                        v-model.number="point.weight" 
                        type="range" 
                        min="0.1" 
                        max="2.0" 
                        step="0.1" 
                        class="m3-slider"
                      />
                    </div>
                  </div>
                  <div v-if="editUser.memory_points.length === 0" class="empty-points">
                    暂无记忆点
                  </div>
                </div>
              </div>
              
              <div class="input-group">
                <label>态度值 (-100 到 100)</label>
                <input v-model.number="editUser.attitude" type="number" class="m3-input" min="-100" max="100" placeholder="数值化的态度评分" />
              </div>
              
              <div class="input-group">
                <label>头像URL</label>
                <input v-model="editUser.avatar" type="text" class="m3-input" placeholder="https://..." />
              </div>
            </div>
            
            <div class="dialog-actions">
              <button class="m3-button text" @click="showEditUserDialog = false">取消</button>
              <button 
                class="m3-button filled" 
                :disabled="updating"
                @click="updateUser"
              >
                {{ updating ? '保存中...' : '保存' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 确认删除对话框 -->
    <Teleport to="body">
      <Transition name="dialog">
        <div v-if="showDeleteConfirm" class="dialog-overlay" @click.self="showDeleteConfirm = false">
          <div class="m3-dialog small">
            <div class="dialog-header">
              <h3>确认删除</h3>
              <button class="m3-icon-button" @click="showDeleteConfirm = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            
            <div class="dialog-content">
              <p>确定要删除用户 "{{ userToDelete?.nickname }}" 吗？</p>
              <p class="warning-text">此操作不可撤销</p>
            </div>
            
            <div class="dialog-actions">
              <button class="m3-button text" @click="showDeleteConfirm = false">取消</button>
              <button 
                class="m3-button filled error" 
                :disabled="deleting"
                @click="deleteUser"
              >
                {{ deleting ? '删除中...' : '删除' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- 确认重置对话框 -->
    <Teleport to="body">
      <Transition name="dialog">
        <div v-if="showResetConfirm" class="dialog-overlay" @click.self="showResetConfirm = false">
          <div class="m3-dialog small">
            <div class="dialog-header">
              <h3>确认重置</h3>
              <button class="m3-icon-button" @click="showResetConfirm = false">
                <span class="material-symbols-rounded">close</span>
              </button>
            </div>
            
            <div class="dialog-content">
              <p>确定要重置与用户 "{{ selectedUser?.nickname }}" 的关系吗？</p>
              <p class="warning-text">这将清除 Bot 对该用户的记忆和关系进展，恢复到初始设定。</p>
            </div>
            
            <div class="dialog-actions">
              <button class="m3-button text" @click="showResetConfirm = false">取消</button>
              <button 
                class="m3-button filled error" 
                :disabled="resetting"
                @click="resetUser"
              >
                {{ resetting ? '重置中...' : '重置' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { api } from '@/api'
import type { Ref } from 'vue'

// ========== 数据类型定义 ==========

interface MemoryPoint {
  content: string
  weight: number
}

interface User {
  user_id: string
  nickname: string
  impression: string
  short_impression?: string
  avatar: string
  attitude?: number | null
  person_id?: string
  memory_points?: MemoryPoint[]
  created_at: number
  updated_at: number
}

interface CopyableUser {
  person_id: string
  nickname: string
  platform: string
  user_id: string
  impression: string
  short_impression: string
  attitude: number | null
  memory_points?: MemoryPoint[]
}

interface Message {
  message_id: string
  user_id: string
  nickname: string
  content: string
  timestamp: number
  message_type: string
  reply_to?: string  // 引用的消息ID
  emojis?: string[]  // 表情包图片列表（base64）
}

// ========== 状态 ==========

const users: Ref<User[]> = ref([])
const selectedUser: Ref<User | null> = ref(null)
const messages: Ref<Message[]> = ref([])
const inputMessage = ref('')
const loading = ref(false)
const sending = ref(false)
const isInputFocused = ref(false)

// 轮询定时器
let pollTimer: number | null = null
const pollInterval = 1000  // 1秒轮询一次

// 引用消息缓存
const quotedMessagesCache: Ref<Map<string, Message>> = ref(new Map())

// 对话框状态
const showCreateUserDialog = ref(false)
const showEditUserDialog = ref(false)
const showDeleteConfirm = ref(false)
const showResetConfirm = ref(false)
const userToDelete: Ref<User | null> = ref(null)

// 复制用户状态
const copyableUsers: Ref<CopyableUser[]> = ref([])
const filteredCopyableUsers: Ref<CopyableUser[]> = ref([])
const platforms: Ref<string[]> = ref([])
const copyPlatform = ref('')
const selectedCopyUser: Ref<CopyableUser | null> = ref(null)
const isPlatformDropdownOpen = ref(false)
const isUserDropdownOpen = ref(false)

// 表单数据
const newUser = ref({
  user_id: '',
  nickname: '',
  impression: '',
  short_impression: '',
  avatar: '',
  attitude: null as number | null,
  memory_points: [] as MemoryPoint[]
})

const editUser = ref({
  nickname: '',
  impression: '',
  short_impression: '',
  avatar: '',
  attitude: null as number | null,
  memory_points: [] as MemoryPoint[]
})

// 操作状态
const creating = ref(false)
const updating = ref(false)
const deleting = ref(false)
const resetting = ref(false)

// Refs
const messagesContainer = ref<HTMLElement | null>(null)
const messageInput = ref<HTMLTextAreaElement | null>(null)

// ========== 生命周期 ==========

onMounted(async () => {
  await loadUsers()
  // 启动轮询
  startPolling()
  // 添加点击外部关闭下拉框的监听
  window.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  // 停止轮询
  stopPolling()
  window.removeEventListener('click', handleClickOutside)
})

// ========== 监听 ==========

watch(selectedUser, async (newUser, oldUser) => {
  if (newUser) {
    await loadMessages()
    // 切换用户时重启轮询
    if (oldUser?.user_id !== newUser.user_id) {
      stopPolling()
      startPolling()
    }
  } else {
    messages.value = []
    stopPolling()
  }
})

watch(showCreateUserDialog, (newVal) => {
  if (newVal) {
    // 打开对话框时，加载可复制用户，并生成随机ID
    loadCopyableUsers()
    generateRandomId()
    // 重置复制选项
    copyPlatform.value = ''
    selectedCopyUser.value = null
  }
})

// ========== 方法 ==========

async function loadUsers() {
  try {
    const response = await api.get<{ users: User[] }>('chatroom/users')
    
    if (response.success && response.data) {
      users.value = response.data.users || []
    } else {
      showToast('加载用户列表失败: ' + (response.error || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('加载用户列表失败:', error)
    showToast('加载用户列表失败', 'error')
  }
}

async function loadMessages() {
  if (!selectedUser.value) return
  
  loading.value = true
  try {
    const response = await api.get<{ messages: Message[] }>('chatroom/messages?limit=100')
    
    if (response.success && response.data) {
      messages.value = response.data.messages || []
      
      // 加载所有引用的消息
      for (const msg of messages.value) {
        if (msg.reply_to) {
          await loadQuotedMessage(msg.reply_to)
        }
      }
      
      await nextTick()
      scrollToBottom()
    } else {
      showToast('加载消息失败: ' + (response.error || '未知错误'), 'error')
    }
  } catch (error) {
    console.error('加载消息失败:', error)
    showToast('加载消息失败', 'error')
  } finally {
    loading.value = false
  }
}

function selectUser(user: User) {
  selectedUser.value = user
  // 同步编辑表单数据
  editUser.value = {
    nickname: user.nickname,
    impression: user.impression,
    short_impression: user.short_impression || '',
    avatar: user.avatar,
    attitude: user.attitude ?? null,
    memory_points: user.memory_points ? JSON.parse(JSON.stringify(user.memory_points)) : []
  }
}

async function createUser() {
  if (!newUser.value.user_id || !newUser.value.nickname) {
    showToast('请填写必填字段', 'error')
    return
  }
  
  // 验证用户ID只能是数字
  if (!/^\d+$/.test(newUser.value.user_id)) {
    showToast('用户ID只能包含数字', 'error')
    return
  }
  
  // 过滤空记忆点
  newUser.value.memory_points = newUser.value.memory_points.filter(p => p.content.trim())

  creating.value = true
  try {
    const response = await api.post('chatroom/users', newUser.value)
    
    if (response.success) {
      showToast('创建用户成功', 'success')
      showCreateUserDialog.value = false
      // 重置表单
      newUser.value = {
        user_id: '',
        nickname: '',
        impression: '',
        short_impression: '',
        avatar: '',
        attitude: null,
        memory_points: []
      }
      await loadUsers()
    } else {
      showToast(response.error || '创建用户失败', 'error')
    }
  } catch (error: any) {
    console.error('创建用户失败:', error)
    showToast(error.message || '创建用户失败', 'error')
  } finally {
    creating.value = false
  }
}

async function updateUser() {
  if (!selectedUser.value) return
  
  // 过滤空记忆点
  editUser.value.memory_points = editUser.value.memory_points.filter(p => p.content.trim())

  updating.value = true
  try {
    const response = await api.put<{ user: User }>(`chatroom/users/${selectedUser.value.user_id}`, editUser.value)
    
    if (response.success) {
      showToast('更新用户成功', 'success')
      showEditUserDialog.value = false
      await loadUsers()
      // 更新当前选中的用户信息
      if (response.data?.user) {
        selectedUser.value = response.data.user
      }
    } else {
      showToast(response.error || '更新用户失败', 'error')
    }
  } catch (error: any) {
    console.error('更新用户失败:', error)
    showToast(error.message || '更新用户失败', 'error')
  } finally {
    updating.value = false
  }
}

function confirmDeleteUser(user: User) {
  userToDelete.value = user
  showDeleteConfirm.value = true
}

async function deleteUser() {
  if (!userToDelete.value) return
  
  deleting.value = true
  try {
    const response = await api.delete(`chatroom/users/${userToDelete.value.user_id}`)
    
    if (response.success) {
      showToast('删除用户成功', 'success')
      showDeleteConfirm.value = false
      
      // 如果删除的是当前选中的用户，清空选择
      if (selectedUser.value?.user_id === userToDelete.value.user_id) {
        selectedUser.value = null
      }
      
      userToDelete.value = null
      await loadUsers()
    } else {
      showToast(response.error || '删除用户失败', 'error')
    }
  } catch (error: any) {
    console.error('删除用户失败:', error)
    showToast(error.message || '删除用户失败', 'error')
  } finally {
    deleting.value = false
  }
}

async function resetUser() {
  if (!selectedUser.value) return
  
  resetting.value = true
  try {
    const response = await api.post(`chatroom/users/${selectedUser.value.user_id}/reset`)
    
    if (response.success) {
      showToast('用户关系已重置', 'success')
      showResetConfirm.value = false
      
      // 刷新消息和用户信息
      await loadMessages()
      // 重新加载用户列表以更新可能变化的信息（如印象）
      await loadUsers()
      // 重新获取当前用户信息
      const updatedUser = users.value.find(u => u.user_id === selectedUser.value?.user_id)
      if (updatedUser) {
        selectedUser.value = updatedUser
      }
    } else {
      showToast(response.error || '重置失败', 'error')
    }
  } catch (error: any) {
    console.error('重置用户失败:', error)
    showToast(error.message || '重置失败', 'error')
  } finally {
    resetting.value = false
  }
}

async function loadCopyableUsers() {
  try {
    const response = await api.get<{ users: CopyableUser[] }>('chatroom/copyable_users')
    if (response.success && response.data) {
      copyableUsers.value = response.data.users || []
      
      // 提取平台列表
      const platformSet = new Set(copyableUsers.value.map(u => u.platform))
      platforms.value = Array.from(platformSet).sort()
      
      // 初始化筛选列表
      filterCopyableUsers()
    }
  } catch (error) {
    console.error('加载可复制用户失败:', error)
  }
}

function filterCopyableUsers() {
  if (!copyPlatform.value) {
    filteredCopyableUsers.value = copyableUsers.value
  } else {
    filteredCopyableUsers.value = copyableUsers.value.filter(u => u.platform === copyPlatform.value)
  }
  // 如果当前选中的用户不在筛选结果中，清空选择
  if (selectedCopyUser.value && !filteredCopyableUsers.value.find(u => u.person_id === selectedCopyUser.value?.person_id)) {
    selectedCopyUser.value = null
  }
}

// 下拉框相关方法
function togglePlatformDropdown(event: Event) {
  event.stopPropagation() // 防止触发 window click
  isPlatformDropdownOpen.value = !isPlatformDropdownOpen.value
  isUserDropdownOpen.value = false // 关闭另一个
}

function selectPlatform(platform: string) {
  copyPlatform.value = platform
  filterCopyableUsers()
  isPlatformDropdownOpen.value = false
}

function toggleUserDropdown(event: Event) {
  event.stopPropagation() // 防止触发 window click
  isUserDropdownOpen.value = !isUserDropdownOpen.value
  isPlatformDropdownOpen.value = false // 关闭另一个
}

function selectCopyUser(user: CopyableUser | null) {
  selectedCopyUser.value = user
  onCopyUserSelect()
  isUserDropdownOpen.value = false
}

function handleClickOutside(event: MouseEvent) {
  // 如果点击的不是下拉框内部，则关闭所有下拉框
  const target = event.target as HTMLElement
  if (!target.closest('.custom-select-container')) {
    isPlatformDropdownOpen.value = false
    isUserDropdownOpen.value = false
  }
}

function onCopyUserSelect() {
  if (selectedCopyUser.value) {
    const user = selectedCopyUser.value
    newUser.value.nickname = user.nickname
    newUser.value.impression = user.impression || ''
    newUser.value.short_impression = user.short_impression || ''
    newUser.value.attitude = user.attitude
    newUser.value.memory_points = user.memory_points ? JSON.parse(JSON.stringify(user.memory_points)) : []
    // 头像暂时不复制，因为PersonInfo里可能没有avatar字段，或者格式不一样
  }
}

function generateRandomId() {
  // 生成 100000 到 999999 之间的随机数
  const randomId = Math.floor(Math.random() * 900000 + 100000).toString()
  newUser.value.user_id = randomId
}

async function sendMessage() {
  if (!inputMessage.value.trim() || !selectedUser.value || sending.value) return
  
  sending.value = true
  try {
    const response = await api.post<{ request_message?: Message }>('chatroom/send', {
      user_id: selectedUser.value.user_id,
      content: inputMessage.value.trim(),
      message_type: 'text'
    })
    
    if (response.success && response.data) {
      // 添加用户消息
      if (response.data.request_message) {
        messages.value.push(response.data.request_message)
      }
      
      // 清空输入
      inputMessage.value = ''
      
      // 重置输入框高度
      if (messageInput.value) {
        messageInput.value.style.height = 'auto'
      }
      
      // 滚动到底部
      await nextTick()
      scrollToBottom()
    } else {
      showToast(response.error || '发送消息失败', 'error')
    }
  } catch (error: any) {
    console.error('发送消息失败:', error)
    showToast(error.message || '发送消息失败', 'error')
  } finally {
    sending.value = false
  }
}

function autoResize(event: Event) {
  const target = event.target as HTMLTextAreaElement
  target.style.height = 'auto'
  target.style.height = Math.min(target.scrollHeight, 120) + 'px'
}

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// ========== 轮询相关 ==========

function startPolling() {
  if (!pollTimer && selectedUser.value) {
    pollMessages()  // 立即执行一次
    pollTimer = window.setInterval(pollMessages, pollInterval)
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function pollMessages() {
  if (!selectedUser.value) {
    stopPolling()
    return
  }

  try {
    const response = await api.get<{ messages: Message[] }>('chatroom/poll')
    
    if (response.success && response.data?.messages && response.data.messages.length > 0) {
      // 添加新消息
      for (const msg of response.data.messages) {
        // 避免重复添加
        if (!messages.value.find(m => m.message_id === msg.message_id)) {
          messages.value.push(msg)
          
          // 如果消息有引用，加载引用的消息
          if (msg.reply_to) {
            await loadQuotedMessage(msg.reply_to)
          }
        }
      }
      
      // 滚动到底部
      await nextTick()
      scrollToBottom()
    }
  } catch (error) {
    console.error('轮询消息失败:', error)
    // 静默失败，不打扰用户
  }
}

async function loadQuotedMessage(messageId: string) {
  // 如果已经缓存，直接返回
  if (quotedMessagesCache.value.has(messageId)) {
    return
  }

  try {
    const response = await api.get<{ message: Message }>(`chatroom/messages/${messageId}`)
    
    if (response.success && response.data?.message) {
      quotedMessagesCache.value.set(messageId, response.data.message)
    }
  } catch (error) {
    console.error('加载引用消息失败:', error)
  }
}

function getQuotedMessage(messageId: string): Message | null {
  return quotedMessagesCache.value.get(messageId) || null
}

function formatTime(timestamp: number): string {
  const date = new Date(timestamp * 1000)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 今天
  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  // 昨天
  if (diff < 172800000 && date.getDate() === now.getDate() - 1) {
    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  
  // 其他
  return date.toLocaleDateString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

function addMemoryPoint(list: MemoryPoint[]) {
  list.push({ content: '', weight: 1.0 })
}

function removeMemoryPoint(list: MemoryPoint[], index: number) {
  list.splice(index, 1)
}

// Toast 提示函数
function showToast(message: string, type: 'success' | 'error' = 'success') {
  // 创建 toast 元素
  const toast = document.createElement('div')
  toast.className = `toast toast-${type}`
  toast.textContent = message
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 12px 20px;
    background: ${type === 'success' ? 'var(--md-sys-color-primary)' : 'var(--md-sys-color-error)'};
    color: ${type === 'success' ? 'var(--md-sys-color-on-primary)' : 'var(--md-sys-color-on-error)'};
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    animation: slideIn 0.3s ease;
  `
  
  document.body.appendChild(toast)
  
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease'
    setTimeout(() => {
      document.body.removeChild(toast)
    }, 300)
  }, 3000)
}
</script>

<style scoped>
.chatroom-view {
  display: flex;
  gap: 16px;
  height: 100%;
  padding: 16px;
  overflow: hidden;
}

/* ========== 用户面板 ========== */

.user-panel {
  width: 300px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.panel-header .header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.panel-header .material-symbols-rounded {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.panel-header h2 {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
}

.user-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.user-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  position: relative;
}

.user-item:hover {
  background-color: var(--md-sys-color-surface-container-high);
}

.user-item.active {
  background-color: var(--md-sys-color-secondary-container);
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  background-color: var(--md-sys-color-surface-container-highest);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-avatar .material-symbols-rounded {
  font-size: 32px;
  color: var(--md-sys-color-on-surface-variant);
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-id {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.delete-btn {
  opacity: 0;
  transition: opacity 0.2s, background-color 0.2s, color 0.2s;
}

.delete-btn:hover {
  background-color: var(--md-sys-color-error-container) !important;
  color: var(--md-sys-color-on-error-container) !important;
}

.user-item:hover .delete-btn {
  opacity: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
  color: var(--md-sys-color-on-surface-variant);
}

.empty-state .material-symbols-rounded {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin-bottom: 20px;
}

/* ========== 聊天面板 ========== */

.chat-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
  flex-shrink: 0;
}

.chat-header .header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header .user-avatar {
  width: 48px;
  height: 48px;
}

.chat-header .user-info h2 {
  font-size: 18px;
  font-weight: 500;
  margin: 0;
}

.chat-header .user-info p {
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 4px 0 0;
}

.header-placeholder {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--md-sys-color-on-surface-variant);
}

.header-actions {
  display: flex;
  gap: 8px;
}

/* ========== 消息区域 ========== */

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: var(--md-sys-color-surface-container-low);
  border-top: none;
  border-bottom: none;
}

.welcome-state,
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--md-sys-color-on-surface-variant);
  text-align: center;
}

.welcome-state .material-symbols-rounded {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.3;
}

.welcome-state h3 {
  margin: 0 0 8px;
  font-size: 24px;
}

.welcome-state p {
  margin: 0;
  font-size: 16px;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--md-sys-color-outline-variant);
  border-top-color: var(--md-sys-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 70%;
}

.message.is-user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.is-bot {
  align-self: flex-start;
}

/* 系统消息横幅 */
.system-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 8px 0;
  background: linear-gradient(90deg, 
    var(--md-sys-color-secondary-container) 0%, 
    var(--md-sys-color-tertiary-container) 100%);
  border-radius: 12px;
  border-left: 4px solid var(--md-sys-color-secondary);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.banner-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: var(--md-sys-color-secondary);
  flex-shrink: 0;
}

.banner-icon .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-on-secondary);
}

.banner-content {
  flex: 1;
  min-width: 0;
}

.banner-text {
  font-size: 14px;
  color: var(--md-sys-color-on-secondary-container);
  line-height: 1.5;
  word-wrap: break-word;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  background-color: var(--md-sys-color-surface-container-highest);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-avatar .material-symbols-rounded {
  font-size: 24px;
}

.is-bot .message-avatar {
  background-color: var(--md-sys-color-primary-container);
}

.is-bot .message-avatar .material-symbols-rounded {
  color: var(--md-sys-color-on-primary-container);
}

.is-user .message-avatar {
  background-color: var(--md-sys-color-tertiary-container);
}

.is-user .message-avatar .material-symbols-rounded {
  color: var(--md-sys-color-on-tertiary-container);
}

.message-content {
  flex: 1;
  min-width: 0;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.message-sender {
  font-weight: 500;
  font-size: 14px;
}

.message-time {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.message-quote {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px 12px;
  background-color: var(--md-sys-color-surface-container);
  border-radius: 8px;
  opacity: 0.8;
}

.quote-line {
  width: 3px;
  background-color: var(--md-sys-color-primary);
  border-radius: 2px;
  flex-shrink: 0;
}

.quote-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.quote-author {
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-primary);
}

.quote-text {
  font-size: 13px;
  color: var(--md-sys-color-on-surface-variant);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.message-text {
  padding: 12px 16px;
  border-radius: 16px;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.is-bot .message-text {
  background-color: var(--md-sys-color-surface-container-highest);
  border-top-left-radius: 4px;
}

.is-user .message-text {
  background-color: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  border-top-right-radius: 4px;
}

/* 表情包样式 */
.message-emojis {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.emoji-image {
  max-width: 120px;
  max-height: 120px;
  border-radius: 8px;
  object-fit: contain;
  background-color: var(--md-sys-color-surface-container);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.emoji-image:hover {
  transform: scale(1.05);
}

.empty-messages {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: var(--md-sys-color-on-surface-variant);
  text-align: center;
}

.empty-messages .material-symbols-rounded {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.3;
}

/* ========== 输入区域 ========== */

.input-area {
  padding: 16px 20px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
  flex-shrink: 0;
  background-color: var(--md-sys-color-surface);
  border-radius: 0 0 16px 16px;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper {
  flex: 1;
  display: flex;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 24px;
  background-color: var(--md-sys-color-surface-container-highest);
  transition: border-color 0.2s;
  overflow: hidden;
}

.input-wrapper.focused {
  border-color: var(--md-sys-color-primary);
}

.message-input {
  flex: 1;
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: transparent;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  color: var(--md-sys-color-on-surface);
  min-height: 42px;
  max-height: 120px;
}

.message-input:focus {
  outline: none;
}

.message-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.m3-button.fab {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.m3-button.fab .material-symbols-rounded {
  font-size: 24px;
}

/* ========== 对话框样式 ========== */

.dialog-overlay {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.m3-dialog {
  background-color: var(--md-sys-color-surface-container-high);
  border-radius: 28px;
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.m3-dialog.small {
  max-width: 400px;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 16px;
}

.dialog-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.dialog-content {
  flex: 1;
  padding: 0 24px 24px;
  overflow-y: auto;
}

.input-group {
  margin-bottom: 20px;
}

.input-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.input-group label .hint {
  font-weight: 400;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  opacity: 0.7;
}

.m3-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  background-color: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  transition: border-color 0.2s;
}

.m3-input:focus {
  outline: none;
  border-color: var(--md-sys-color-primary);
}

textarea.m3-input {
  resize: vertical;
  font-family: inherit;
}

.copy-user-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--md-sys-color-primary);
  margin-bottom: 12px;
}

.input-row {
  display: flex;
  gap: 16px;
}

.input-group.half {
  flex: 1;
  margin-bottom: 0;
}

.divider {
  height: 1px;
  background-color: var(--md-sys-color-outline-variant);
  margin: 20px 0;
}

.input-with-action {
  display: flex;
  gap: 8px;
  align-items: center;
}

.input-with-action .m3-input {
  flex: 1;
}

.dialog-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  padding: 16px 24px;
  border-top: 1px solid var(--md-sys-color-outline-variant);
}

/* Custom Select Styles */
.custom-select-container {
  position: relative;
  width: 100%;
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background-color: var(--md-sys-color-surface-container-highest);
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.custom-select-trigger:hover {
  border-color: var(--md-sys-color-primary);
  background-color: var(--md-sys-color-surface-container-high);
}

.custom-select-container.is-open .custom-select-trigger {
  border-color: var(--md-sys-color-primary);
  box-shadow: 0 0 0 2px var(--md-sys-color-secondary-container);
}

.custom-select-container.is-disabled .custom-select-trigger {
  opacity: 0.6;
  cursor: not-allowed;
  background-color: var(--md-sys-color-surface-container);
}

.select-arrow {
  color: var(--md-sys-color-on-surface-variant);
  transition: transform 0.2s ease;
  font-size: 20px;
}

.custom-select-container.is-open .select-arrow {
  transform: rotate(180deg);
  color: var(--md-sys-color-primary);
}

.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  width: 100%;
  background-color: var(--md-sys-color-surface-container-high);
  border: 1px solid var(--md-sys-color-outline);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
  padding: 4px;
}

.custom-select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.15s ease;
  color: var(--md-sys-color-on-surface);
  font-size: 14px;
}

.custom-select-option:hover {
  background-color: var(--md-sys-color-surface-container-highest);
}

.custom-select-option.is-selected {
  background-color: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  font-weight: 500;
}

.check-icon {
  font-size: 18px;
  color: var(--md-sys-color-primary);
}

.select-fade-enter-active,
.select-fade-leave-active {
  transition: all 0.2s ease;
}

.select-fade-enter-from,
.select-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.warning-text {
  color: var(--md-sys-color-error);
  font-size: 14px;
  margin-top: 8px;
}

.m3-button.error {
  background-color: var(--md-sys-color-error);
  color: var(--md-sys-color-on-error);
}

.m3-button.error:hover {
  background-color: var(--md-sys-color-error);
  filter: brightness(1.1);
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.m3-button.small {
  height: 32px;
  padding: 0 12px;
  font-size: 13px;
}

.m3-icon-button.small {
  width: 32px;
  height: 32px;
}

.m3-icon-button.small .material-symbols-rounded {
  font-size: 18px;
}

.memory-points-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.memory-point-item {
  background-color: var(--md-sys-color-surface-container);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.point-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--md-sys-color-primary);
}

.point-content {
  margin-bottom: 8px;
}

.point-weight {
  display: flex;
  align-items: center;
  gap: 12px;
}

.point-weight label {
  margin: 0;
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  min-width: 80px;
}

.m3-slider {
  flex: 1;
  height: 4px;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 2px;
  outline: none;
  -webkit-appearance: none;
}

.m3-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  cursor: pointer;
  transition: transform 0.1s;
}

.m3-slider::-webkit-slider-thumb:hover {
  transform: scale(1.2);
}

.empty-points {
  text-align: center;
  padding: 20px;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
  background-color: var(--md-sys-color-surface-container-highest);
  border-radius: 12px;
  border: 1px dashed var(--md-sys-color-outline);
}

/* ========== 动画 ========== */

.dialog-enter-active,
.dialog-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .m3-dialog,
.dialog-leave-to .m3-dialog {
  transform: scale(0.9);
}

/* ========== 响应式 ========== */

@media (max-width: 768px) {
  .chatroom-view {
    flex-direction: column;
    padding: 8px;
  }
  
  .user-panel {
    width: 100%;
    max-height: 200px;
  }
  
  .message {
    max-width: 85%;
  }
}
</style>
