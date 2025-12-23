<template>
  <div class="model-stats-view">
    <div class="view-header">
      <div class="header-content">
        <h2>模型统计</h2>
        <p class="subtitle">查看各模型的详细使用情况和 Token 消耗</p>
      </div>
      <div class="header-actions">
        <button class="m3-button filled" @click="fetchData" :disabled="loading">
          <span class="material-symbols-rounded icon" :class="{ spinning: loading }">refresh</span>
          刷新数据
        </button>
      </div>
    </div>

    <div class="stats-content">
      <div v-if="loading && !statsData" class="loading-state">
        <span class="material-symbols-rounded spinning">refresh</span>
        加载中...
      </div>
      
      <div v-else-if="statsData && Object.keys(statsData).length > 0" class="stats-grid">
        <div 
          v-for="(stats, model) in statsData" 
          :key="model" 
          class="m3-card model-card"
          @click="openDetail(model, stats)"
        >
          <div class="card-header">
            <div class="model-info">
              <span class="material-symbols-rounded model-icon">psychology</span>
              <h3 class="model-name" :title="model">{{ model }}</h3>
            </div>
          </div>
          
          <div class="card-body">
            <div class="stat-row">
              <div class="stat-item">
                <span class="label">提示词 (Prompt)</span>
                <span class="value">{{ stats.prompt_tokens }}</span>
              </div>
              <div class="stat-item" style="text-align: right;">
                <span class="label">生成 (Completion)</span>
                <span class="value">{{ stats.completion_tokens }}</span>
              </div>
            </div>
            
            <div class="stat-divider"></div>
            
            <div class="stat-row total-row">
              <div class="stat-item">
                <span class="label">总计 Token</span>
                <span class="value highlight">{{ stats.total_tokens }}</span>
              </div>
              <div class="stat-item" style="text-align: right;">
                <span class="label">调用次数</span>
                <span class="value">{{ stats.total_calls }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else class="empty-state">
        <span class="material-symbols-rounded empty-icon">data_usage</span>
        <h3>暂无数据</h3>
        <p>还没有产生任何模型调用记录</p>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div class="m3-dialog-overlay" v-if="selectedModel" @click="closeDetail">
      <div class="m3-dialog" @click.stop>
        <div class="dialog-header">
          <h3>模型详情</h3>
          <button class="m3-icon-button" @click="closeDetail">
            <span class="material-symbols-rounded">close</span>
          </button>
        </div>
        <div class="dialog-content">
          <div class="detail-header">
            <span class="material-symbols-rounded detail-icon">psychology</span>
            <div class="detail-title">
              <div class="detail-name">{{ selectedModel.name }}</div>
              <div class="detail-badge">{{ selectedModel.stats.total_calls }} 次调用</div>
            </div>
          </div>
          
          <div class="detail-grid">
            <div class="detail-card filled">
              <div class="detail-label">总计消耗 (Total)</div>
              <div class="detail-value">{{ selectedModel.stats.total_tokens }}</div>
            </div>
            <div class="detail-card">
              <div class="detail-label">提示词 (Prompt)</div>
              <div class="detail-value">{{ selectedModel.stats.prompt_tokens }}</div>
            </div>
            <div class="detail-card">
              <div class="detail-label">生成 (Completion)</div>
              <div class="detail-value">{{ selectedModel.stats.completion_tokens }}</div>
            </div>
            <div class="detail-card">
              <div class="detail-label">平均消耗 / 次</div>
              <div class="detail-value">{{ Math.round(selectedModel.stats.total_tokens / (selectedModel.stats.total_calls || 1)) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getModelUsageStats } from '@/api'
import { showError } from '@/utils/dialog'

const loading = ref(false)
const statsData = ref<Record<string, Record<string, number>> | null>(null)
const selectedModel = ref<{ name: string; stats: any } | null>(null)

const fetchData = async () => {
  loading.value = true
  try {
    const res = await getModelUsageStats()
    if (res.success && res.data) {
      statsData.value = res.data.stats
    } else {
      showError('获取数据失败: ' + (res.error || '未知错误'))
    }
  } catch (e) {
    showError('网络请求失败: ' + e)
  } finally {
    loading.value = false
  }
}

const openDetail = (model: string, stats: any) => {
  selectedModel.value = { name: model, stats }
}

const closeDetail = () => {
  selectedModel.value = null
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.model-stats-view {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
  box-sizing: border-box;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-content h2 {
  margin: 0;
  font-size: 24px;
  color: var(--md-sys-color-on-surface);
}

.subtitle {
  margin: 4px 0 0;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 14px;
}

.m3-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 24px;
  height: 40px;
  border-radius: 20px;
  border: none;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
}

.m3-button.filled:hover {
  box-shadow: var(--md-sys-elevation-1);
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
}

.m3-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.model-card {
  background: var(--md-sys-color-surface-container);
  border-radius: 24px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}

.model-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--md-sys-elevation-2);
  background: var(--md-sys-color-surface-container-high);
}

.card-header {
  padding: 20px 24px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-info {
  display: flex;
  align-items: center;
  gap: 16px;
  overflow: hidden;
}

.model-icon {
  color: var(--md-sys-color-on-secondary-container);
  background: var(--md-sys-color-secondary-container);
  padding: 12px;
  border-radius: 50%;
  font-size: 24px;
}

.model-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-body {
  padding: 0 24px 24px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.value {
  font-size: 18px;
  font-family: 'Noto Sans SC', sans-serif;
  color: var(--md-sys-color-on-surface);
  font-weight: 500;
}

.stat-divider {
  height: 1px;
  background: var(--md-sys-color-outline-variant);
  margin: 16px 0;
  opacity: 0.5;
}

.total-row .value.highlight {
  color: var(--md-sys-color-primary);
  font-weight: 700;
  font-size: 24px;
}

.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: var(--md-sys-color-on-surface-variant);
  gap: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

/* Dialog Styles */
.m3-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.m3-dialog {
  background: var(--md-sys-color-surface-container);
  width: 90%;
  max-width: 500px;
  border-radius: 28px;
  display: flex;
  flex-direction: column;
  box-shadow: var(--md-sys-elevation-3);
  animation: dialogIn 0.3s cubic-bezier(0.2, 0, 0, 1);
}

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

.dialog-header {
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--md-sys-color-outline-variant);
}

.dialog-header h3 {
  margin: 0;
  font-size: 22px;
  color: var(--md-sys-color-on-surface);
}

.m3-icon-button {
  background: transparent;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.m3-icon-button:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.dialog-content {
  padding: 24px;
}

.detail-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-icon {
  font-size: 32px;
  color: var(--md-sys-color-primary);
  background: var(--md-sys-color-surface-container-high);
  padding: 12px;
  border-radius: 16px;
}

.detail-title {
  flex: 1;
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin-bottom: 8px;
  word-break: break-all;
  line-height: 1.4;
}

.detail-badge {
  display: inline-block;
  padding: 4px 12px;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.detail-card {
  background: var(--md-sys-color-surface-container-low);
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-card.filled {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  grid-column: span 2;
}

.detail-card.filled .detail-label {
  color: var(--md-sys-color-on-primary-container);
  opacity: 0.8;
}

.detail-card.filled .detail-value {
  color: var(--md-sys-color-on-primary-container);
}

.detail-label {
  font-size: 12px;
  color: var(--md-sys-color-on-surface-variant);
}

.detail-value {
  font-size: 20px;
  font-family: 'Noto Sans SC', sans-serif;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
}
</style>
