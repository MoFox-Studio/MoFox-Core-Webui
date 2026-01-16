<template>
  <div class="daily-quote-card m3-card">
    <div class="quote-content">
      <span class="material-symbols-rounded quote-icon">format_quote</span>
      <p class="quote-text">{{ quoteData?.quote || '加载中...' }}</p>
    </div>
    <div class="quote-footer">
      <div class="author-info">
        <span class="author-name">— {{ quoteData?.author || '...' }}</span>
        <span class="quote-category" v-if="quoteData?.category">{{ quoteData.category }}</span>
      </div>
      <button class="m3-icon-button refresh-btn" @click="refreshQuote" :disabled="loading">
        <span class="material-symbols-rounded" :class="{ spinning: loading }">refresh</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getDailyQuote, type DailyQuoteResponse } from '@/api/dashboard'

const quoteData = ref<DailyQuoteResponse | null>(null)
const loading = ref(false)

async function fetchQuote() {
  loading.value = true
  const startTime = Date.now()
  try {
    const res = await getDailyQuote()
    if (res.success && res.data) {
      quoteData.value = res.data
    }
  } catch (error) {
    console.error('获取每日名言失败:', error)
  } finally {
    // 确保至少显示 800ms 的加载动画
    const elapsed = Date.now() - startTime
    const minDelay = 800
    if (elapsed < minDelay) {
      await new Promise(resolve => setTimeout(resolve, minDelay - elapsed))
    }
    loading.value = false
  }
}

async function refreshQuote() {
  await fetchQuote()
}

onMounted(() => {
  fetchQuote()
})
</script>

<style scoped>
.daily-quote-card {
  background: linear-gradient(135deg, var(--md-sys-color-primary-container) 0%, var(--md-sys-color-tertiary-container) 100%);
  padding: 32px 40px;
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
  animation: slideIn 0.6s cubic-bezier(0.2, 0, 0, 1);
}

.daily-quote-card::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
  border-radius: 50%;
  pointer-events: none;
}

.quote-content {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
}

.quote-icon {
  font-size: 36px;
  color: var(--md-sys-color-primary);
  opacity: 0.6;
  flex-shrink: 0;
}

.quote-text {
  font-size: 24px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--md-sys-color-on-primary-container);
  margin: 0;
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0.2px;
}

.quote-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-name {
  font-size: 16px;
  font-weight: 500;
  color: var(--md-sys-color-on-primary-container);
  opacity: 0.8;
  font-style: italic;
}

.quote-category {
  font-size: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  background: var(--md-sys-color-surface-container-highest);
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.refresh-btn {
  color: var(--md-sys-color-on-primary-container);
}

.refresh-btn:hover {
  background: var(--md-sys-color-surface-container);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinning {
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式 */
@media (max-width: 768px) {
  .daily-quote-card {
    padding: 24px 20px;
  }

  .quote-text {
    font-size: 18px;
  }

  .quote-icon {
    font-size: 28px;
  }
}
</style>
