<template>
  <!-- 机器人配置步骤容器 -->
  <div class="bot-config-step">
    <!-- 主卡片容器，使用 Material Design 3 样式 -->
    <div class="card m3-card">
      <!-- 步骤头部：标题和描述 -->
      <div class="step-header">
        <h2 class="step-title">
          <!-- Material Symbols 图标：机器人 -->
          <span class="material-symbols-rounded">smart_toy</span>
          机器人配置
        </h2>
        <p class="step-description">设置您的机器人的基本信息和人格特质</p>
      </div>
      
      <!-- 
        配置表单
        @submit.prevent: 阻止表单默认提交行为，使用自定义的 handleSubmit 方法
      -->
      <form class="config-form" :class="{ 'form-loading': isLoadingConfig }" @submit.prevent="handleSubmit">
        <!-- ========== 昵称输入框 ========== -->
        <div class="form-field">
          <label class="field-label">
            <span class="material-symbols-rounded">person</span>
            昵称
          </label>
          <!-- 
            v-model: 双向绑定昵称数据
            @input: 监听输入事件，用于实时验证和提示
          -->
          <input
            v-model="formData.nickname"
            @input="handleNicknameInput"
            type="text"
            class="m3-input"
            placeholder="例如：墨狐"
            :disabled="isLoadingConfig"
            required
          />
          <span class="field-hint">机器人的主要称呼</span>
        </div>
        
        <!-- ========== 别名配置（可选） ========== -->
        <div class="form-field">
          <StringArrayEditor
            :value="formData.alias_names"
            title="别名（可选）"
            description="其他可以称呼机器人的名字"
            placeholder="例如：狐狐"
            emptyText="暂无别名"
            addButtonText="添加别名"
            @update="formData.alias_names = $event"
          />
        </div>
        
        <!-- ========== 人格核心输入框 ========== -->
        <div class="form-field">
          <label class="field-label">
            <span class="material-symbols-rounded">psychology</span>
            人格核心
          </label>
          <!-- 
            textarea: 多行文本输入
            @input: 监听输入事件，检查长度并给出建议
            rows="2": 默认显示2行
            建议不超过50字
          -->
          <textarea
            v-model="formData.personality_core"
            @input="handlePersonalityInput"
            class="m3-textarea"
            placeholder="例如：是一个积极向上的女大学生"
            rows="2"
            :disabled="isLoadingConfig"
            required
          ></textarea>
          <span class="field-hint">用一句话描述机器人的核心人格特质（建议50字以内）</span>
        </div>
        
        <!-- ========== 身份设定输入框 ========== -->
        <div class="form-field">
          <label class="field-label">
            <span class="material-symbols-rounded">fingerprint</span>
            身份设定
          </label>
          <!-- 
            用于描述机器人的外貌、年龄、性别、职业等基本信息
            rows="2": 默认显示2行
          -->
          <textarea
            v-model="formData.identity"
            class="m3-textarea"
            placeholder="例如：年龄为19岁，是女孩子，身高为160cm，有黑色的短发"
            rows="2"
            :disabled="isLoadingConfig"
            required
          ></textarea>
          <span class="field-hint">描述外貌、年龄、性别、职业等</span>
        </div>
        
        <!-- ========== 回复风格输入框 ========== -->
        <div class="form-field">
          <label class="field-label">
            <span class="material-symbols-rounded">chat</span>
            回复风格
          </label>
          <!-- 
            用于描述机器人的说话方式和表达习惯
            rows="3": 默认显示3行（这个字段可能需要更多说明）
          -->
          <textarea
            v-model="formData.reply_style"
            class="m3-textarea"
            placeholder="例如：回复可以简短一些，语气轻松自然"
            rows="3"
            :disabled="isLoadingConfig"
            required
          ></textarea>
          <span class="field-hint">描述机器人的说话方式和表达习惯</span>
        </div>
        
        <!-- ========== 主人用户配置（可选） ========== -->
        <div class="form-field">
          <OwnerListEditor
            :value="formData.owner_list"
            @update="formData.owner_list = $event"
          />
        </div>
        
        <!-- ========== 按钮组 ========== -->
        <div class="button-group">
          <!-- 跳过按钮：使用 outlined 样式 -->
          <button type="button" class="m3-button outlined" @click="$emit('skip')" :disabled="loading || isLoadingConfig">
            <span>跳过此步</span>
          </button>
          <!-- 
            提交按钮：使用 filled 样式
            type="submit": 触发表单提交事件
            :disabled: 提交中或加载配置时禁用按钮
            v-if/v-else: 根据加载状态显示不同文本
          -->
          <button type="submit" class="m3-button filled" :disabled="loading || isLoadingConfig">
            <span v-if="isLoadingConfig">加载中...</span>
            <span v-else-if="!loading">保存并继续</span>
            <span v-else>保存中...</span>
            <span class="material-symbols-rounded">arrow_forward</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * 机器人配置步骤组件
 * 
 * 功能说明：
 * 该组件是初始化向导的第二步，负责收集和保存机器人的基本信息。
 * 用户可以在此设置机器人的个性化参数，这些参数将影响机器人的行为和回复风格。
 * 
 * 配置项包括：
 * - QQ账号：机器人使用的QQ号码（必填）
 * - 昵称：机器人的主要称呼（必填）
 * - 别名：其他可以称呼机器人的名字（可选，支持多个，用逗号分隔）
 * - 人格核心：用一句话描述机器人的核心人格特质（必填，建议50字以内）
 * - 身份设定：描述外貌、年龄、性别、职业等信息（必填）
 * - 回复风格：描述机器人的说话方式和表达习惯（必填）
 * 
 * 特性：
 * - 支持跳过此步骤
 * - 自动加载已有配置
 * - 输入验证和友好提示
 * - 保存前的数据处理（如别名解析）
 */

import { ref, onMounted } from 'vue'
import { saveBotConfig, getBotConfig, type BotConfigRequest } from '@/api/initialization'
import { StringArrayEditor } from '@/components/config/editors'
import OwnerListEditor from '@/components/config/editors/OwnerListEditor.vue'

// === 事件定义 ===
/** 向父组件发送的事件 */
const emit = defineEmits<{
  /** 进入下一步 */
  next: []
  /** 跳过当前步骤 */
  skip: []
  /** 显示提示消息 */
  toast: [message: string]
}>()

// === 状态管理 ===
/** 
 * 是否正在提交数据
 * 用于控制提交按钮的禁用状态和显示加载文本
 */
const loading = ref(false)

/**
 * 是否正在加载配置
 * 用于控制表单输入的禁用状态，确保配置加载完成后才允许用户输入
 */
const isLoadingConfig = ref(true)

/** 
 * 表单数据对象
 * 
 * 类型定义 BotConfigRequest 包含以下字段：
 * @property {number} qq_account - 机器人的QQ账号（必填）
 * @property {string} nickname - 机器人的主要称呼（必填）
 * @property {string[]} alias_names - 机器人的别名列表（可选）
 * @property {string} personality_core - 人格核心描述（必填）
 * @property {string} identity - 身份设定（必填）
 * @property {string} reply_style - 回复风格描述（必填）
 */
const formData = ref<BotConfigRequest>({
  nickname: '',
  alias_names: [],
  personality_core: '',
  identity: '',
  reply_style: '',
  owner_list: []
})

// === 输入验证和提示 ===
/**
 * 处理昵称输入事件
 * 
 * 功能说明：
 * 监听昵称输入框的变化，当用户输入一些常见的AI助手名称时，
 * 给出友好的提示信息，增加趣味性和引导用户创建独特的机器人个性。
 * 
 * @触发时机 昵称输入框的 @input 事件
 * @效果 如果输入了预设的AI名称，通过 toast 事件显示提示消息
 */
function handleNicknameInput() {
  const value = formData.value.nickname
  // 定义常见的AI助手名称列表（不区分大小写）
  const aiNames = ['小冰', '小爱', 'xiaoai', 'xiaobing',"fairy"]
  
  // 如果输入的名称在列表中，显示友好提示
  if (aiNames.includes(value.toLowerCase())) {
    emit('toast', '虽然很像，但 MoFox 有自己独特的个性哦～')
  }
}

/**
 * 处理人格核心输入事件
 * 
 * 功能说明：
 * 监听人格核心输入框的变化，当输入内容过长时给出建议。
 * 人格核心应该简短精炼，过长的描述可能会影响AI的理解和表现。
 * 
 * @触发时机 人格核心输入框的 @input 事件
 * @建议长度 不超过100个字符
 * @效果 如果超过100字符，通过 toast 事件显示建议消息
 */
function handlePersonalityInput() {
  const value = formData.value.personality_core
  // 检查长度是否超过建议值（100字符）
  if (value.length > 100) {
    emit('toast', '人格核心建议简短精炼，太长可能会让我迷失自我～')
  }
}

// === 配置加载 ===
/**
 * 从后端加载现有的机器人配置
 * 
 * 功能说明：
 * 在组件挂载时调用，尝试从后端获取已保存的机器人配置。
 * 如果存在配置数据，自动填充表单，方便用户编辑现有配置。
 * 
 * 数据结构说明：
 * 后端返回的数据结构为 result.data.data（双层嵌套）
 * - result.success: 请求是否成功
 * - result.data.data: 实际的配置数据对象
 * 
 * 加载逻辑：
 * 1. 调用 getBotConfig() API 获取配置
 * 2. 检查返回数据的有效性
 * 3. 逐个字段检查并填充表单（只填充非空字段）
 * 4. 特殊处理别名字段：将数组转换为逗号分隔的字符串
 * 
 * 错误处理：
 * 如果加载失败，仅在控制台输出错误信息，不影响用户操作
 * （用户可以手动输入新配置）
 */
async function loadExistingConfig() {
  try {
    console.log('[BotConfigStep] 正在加载现有配置...')
    const result = await getBotConfig()
    console.log('[BotConfigStep] API响应:', result)
    
    // 后端返回的数据在 result.data.data 中（双层嵌套）
    const configData = (result.data as any)?.data
    
    if (result.success && configData) {
      console.log('[BotConfigStep] 加载配置数据:', configData)
      
      // 只在有实际数据时才填充表单（避免覆盖默认值）
      if (configData.nickname) {
        formData.value.nickname = configData.nickname
      }
      if (configData.personality_core) {
        formData.value.personality_core = configData.personality_core
      }
      if (configData.identity) {
        formData.value.identity = configData.identity
      }
      if (configData.reply_style) {
        formData.value.reply_style = configData.reply_style
      }
      
      // 加载别名数组
      if (configData.alias_names && Array.isArray(configData.alias_names)) {
        formData.value.alias_names = configData.alias_names
        console.log('[BotConfigStep] 别名已加载:', formData.value.alias_names)
      }
      
      // 加载所有者列表
      if (configData.owner_list && Array.isArray(configData.owner_list)) {
        formData.value.owner_list = configData.owner_list
        console.log('[BotConfigStep] 所有者列表已加载:', formData.value.owner_list)
      }
      
      console.log('[BotConfigStep] 配置加载完成')
    } else {
      console.log('[BotConfigStep] 无现有配置数据')
    }
  } catch (error) {
    console.error('[BotConfigStep] 加载机器人配置失败:', error)
  } finally {
    // 无论成功失败，都允许用户开始输入
    isLoadingConfig.value = false
  }
}

// === 表单提交 ===
/**
 * 处理表单提交
 * 
 * 功能说明：
 * 当用户点击"保存并继续"按钮时触发，处理表单数据并保存到后端。
 * 
 * 处理流程：
 * 1. 设置加载状态，禁用提交按钮
 * 2. 调用 saveBotConfig API 保存配置
 * 3. 根据保存结果执行相应操作：
 *    - 成功：触发 next 事件，进入下一步
 *    - 失败：显示错误提示
 * 4. 无论成功失败，最终都会恢复加载状态
 * 
 * @触发时机 表单提交事件（@submit.prevent）
 * @副作用 修改 loading 状态，可能触发 next 事件
 */
async function handleSubmit() {
  // 设置加载状态，禁用提交按钮
  loading.value = true
  
  try {
    // 调用 API 保存配置（数据已经是正确的格式）
    const result = await saveBotConfig(formData.value)
    
    // 根据保存结果执行相应操作
    if (result.success) {
      // 保存成功，触发 next 事件进入下一步
      emit('next')
    } else {
      // 保存失败，显示错误信息
      alert('保存失败：' + (result.error || '未知错误'))
    }
  } catch (error) {
    // 捕获网络错误或其他异常
    console.error('保存机器人配置失败:', error)
    alert('保存失败，请检查网络连接')
  } finally {
    // 无论成功失败，都恢复加载状态
    loading.value = false
  }
}

// === 生命周期钩子 ===
/**
 * 组件挂载后执行
 * 
 * 功能：加载已有的机器人配置（如果存在）
 * 这样用户可以在已有配置的基础上进行修改，而不是每次都重新输入
 */
onMounted(() => {
  loadExistingConfig()
})
</script>

<style scoped>
/* ==================== 容器样式 ==================== */

/* 步骤容器：居中对齐，带淡入动画 */
.bot-config-step {
  display: flex;
  justify-content: center;
  animation: fadeIn 0.5s ease-out;
}

/* 淡入动画：从下方滑入并淡入 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 主卡片：限制最大宽度，圆角，阴影 */
.card {
  width: 100%;
  max-width: 700px;
  padding: 40px;
  background: var(--md-sys-color-surface);
  border-radius: 28px;
  box-shadow: var(--md-sys-elevation-2);
}

/* ==================== 步骤头部样式 ==================== */

.step-header {
  margin-bottom: 32px;
  text-align: center;
}

/* 步骤标题：居中，带图标 */
.step-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 8px 0;
}

/* 标题图标：使用主题色 */
.step-title .material-symbols-rounded {
  font-size: 32px;
  color: var(--md-sys-color-primary);
}

/* 步骤描述文本 */
.step-description {
  font-size: 16px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

/* ==================== 表单样式 ==================== */

.config-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* 加载中的表单禁用交互 */
.config-form.form-loading {
  pointer-events: none;
  opacity: 0.6;
  position: relative;
}

.config-form.form-loading::after {
  content: '加载配置中...';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--md-sys-color-surface);
  padding: 16px 32px;
  border-radius: 12px;
  box-shadow: var(--md-sys-elevation-3);
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-primary);
  z-index: 10;
}

/* 表单字段容器 */
.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 字段标签：带图标 */
.field-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}

/* 标签图标 */
.field-label .material-symbols-rounded {
  font-size: 20px;
  color: var(--md-sys-color-primary);
}

/* 输入框和文本域的通用样式 */
.m3-input,
.m3-textarea {
  width: 100%;
  padding: 14px 16px;
  font-size: 16px;
  font-family: inherit;
  color: var(--md-sys-color-on-surface);
  background: var(--md-sys-color-surface-variant);
  border: 2px solid transparent;
  border-radius: 12px;
  outline: none;
  transition: all 0.2s ease;
}

/* 获得焦点时的样式：显示主题色边框 */
.m3-input:focus,
.m3-textarea:focus {
  border-color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface);
}

/* 文本域特定样式：允许垂直调整大小 */
.m3-textarea {
  resize: vertical;
  min-height: 80px;
}

/* 字段提示文本 */
.field-hint {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
  margin-left: 4px;
}

/* ==================== 按钮样式 ==================== */

/* 按钮组容器：居中排列 */
.button-group {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 16px;
}

/* 按钮通用样式：圆角胶囊形状 */
.m3-button {
  padding: 12px 28px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 100px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}

/* 禁用状态 */
.m3-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Filled 样式按钮：主操作按钮 */
.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: var(--md-sys-elevation-1);
}

/* Filled 按钮悬停效果 */
.m3-button.filled:hover:not(:disabled) {
  box-shadow: var(--md-sys-elevation-2);
  transform: scale(1.02);
}

/* Outlined 样式按钮：次要操作按钮 */
.m3-button.outlined {
  background: transparent;
  color: var(--md-sys-color-primary);
  border: 2px solid var(--md-sys-color-outline);
}

/* Outlined 按钮悬停效果 */
.m3-button.outlined:hover:not(:disabled) {
  background: var(--md-sys-color-surface-variant);
}

/* 按钮图标 */
.m3-button .material-symbols-rounded {
  font-size: 20px;
}

/* ==================== 响应式设计 ==================== */

/* 平板及以下尺寸 */
@media (max-width: 768px) {
  .card {
    padding: 32px 24px;
  }
  
  .step-title {
    font-size: 24px;
  }
  
  /* 按钮垂直排列 */
  .button-group {
    flex-direction: column;
  }
}
</style>
