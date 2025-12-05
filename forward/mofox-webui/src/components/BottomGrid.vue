<template>
  <div class="bottom-grid">
    <div class="content-card">
      <h2 class="card-title">
        <Icon icon="material-symbols:smart-toy-outline" class="title-icon" />
        模型使用统计
      </h2>
      <div class="model-stats-container">
        <div class="chart-container">
          <v-chart class="chart" :option="modelChartOption" :theme="themeStore.theme" autoresize />
        </div>
        <table class="model-table">
          <thead>
            <tr>
              <th>模型名称</th>
              <th>请求次数</th>
              <th>平均TPS</th>
              <th>成本</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="model in modelStats" :key="model.name">
              <td>{{ model.name }}</td>
              <td>{{ model.requests }}</td>
              <td>{{ model.tps }}</td>
              <td>¥{{ model.cost }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <div class="content-card">
      <h2 class="card-title">
        <Icon icon="material-symbols:chat-bubble-outline" class="title-icon" />
        Top 5 热闹的聊天流
      </h2>
      <ul class="chat-list">
        <li v-for="(chat, index) in activeChats" :key="chat.id" class="chat-item">
          <div class="chat-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
          <div class="chat-info">
            <div class="chat-name">{{ chat.name }}</div>
            <div class="chat-meta">{{ chat.lastActive }} · {{ chat.msgCount }}条消息</div>
          </div>
          <div class="chat-heat">🔥 {{ chat.heat }}</div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useThemeStore } from '@/stores/theme'

use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
])

const themeStore = useThemeStore()

const modelStats = ref([
  { name: 'Kimi K2 Instruct', requests: 2, tps: '27.5', cost: '0.0228' },
  { name: 'BGE-M3', requests: 15, tps: '37.8', cost: '0.00' },
  { name: 'GPT-4o', requests: 8, tps: '15.2', cost: '0.15' },
  { name: 'Claude 3.5 Sonnet', requests: 12, tps: '45.1', cost: '0.08' }
])

const modelChartOption = ref({
  tooltip: {
    trigger: 'item'
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    top: 'middle'
  },
  series: [
    {
      name: '模型请求分布',
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: {
        show: false,
        position: 'center'
      },
      emphasis: {
        label: {
          show: true,
          fontSize: 20,
          fontWeight: 'bold'
        }
      },
      labelLine: {
        show: false
      },
      data: [
        { value: 2, name: 'Kimi K2' },
        { value: 15, name: 'BGE-M3' },
        { value: 8, name: 'GPT-4o' },
        { value: 12, name: 'Claude 3.5' }
      ]
    }
  ]
})

const activeChats = ref([
  { id: 1, name: '技术交流群', lastActive: '刚刚', msgCount: 1245, heat: 98 },
  { id: 2, name: '摸鱼划水群', lastActive: '1分钟前', msgCount: 856, heat: 85 },
  { id: 3, name: 'Bot测试群', lastActive: '5分钟前', msgCount: 432, heat: 72 },
  { id: 4, name: '二次元同好会', lastActive: '12分钟前', msgCount: 215, heat: 64 },
  { id: 5, name: '反馈建议', lastActive: '30分钟前', msgCount: 89, heat: 45 }
])
</script>

<style scoped>
.bottom-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: 20px;
}

.content-card {
  background: var(--bg-white);
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--shadow);
  overflow: hidden; /* 防止内容溢出 */
}

.card-title {
  font-size: 12px;
  color: var(--primary-blue);
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--lighter-blue);
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-icon {
  font-size: 16px;
}

.model-stats-container {
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap; /* 允许换行，防止穿模 */
}

.chart-container {
  flex: 1;
  height: 200px;
  min-width: 200px; /* 最小宽度 */
}

.chart {
  height: 100%;
  width: 100%;
}

.model-table {
  flex: 1.5;
  border-collapse: collapse;
  font-size: 7px;
  min-width: 250px; /* 最小宽度 */
}

.model-table th {
  background: var(--bg-light);
  padding: 10px;
  text-align: left;
  color: var(--primary-blue);
  border-bottom: 2px solid var(--border-color);
}

.model-table td {
  padding: 10px;
  border-bottom: 1px solid var(--border-color);
}

.model-table tr:hover {
  background: var(--bg-light);
}

.chat-list {
  list-style: none;
}

.chat-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-color);
  transition: background-color 0.2s;
}

.chat-item:hover {
  background-color: var(--bg-light);
}

.chat-item:last-child {
  border-bottom: none;
}

.chat-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--bg-light);
  color: var(--text-gray);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: bold;
  margin-right: 15px;
}

.rank-1 { background: #FFD700; color: white; }
.rank-2 { background: #C0C0C0; color: white; }
.rank-3 { background: #CD7F32; color: white; }

.chat-info {
  flex: 1;
}

.chat-name {
  font-size: 10px;
  color: var(--text-dark);
  margin-bottom: 4px;
  font-weight: bold;
}

.chat-meta {
  font-size: 8px;
  color: var(--text-gray);
}

.chat-heat {
  font-size: 10px;
  color: var(--danger-red);
  font-family: 'Press Start 2P', cursive;
}

@media (max-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
  
  .model-stats-container {
    flex-direction: column;
  }
  
  .chart-container {
    width: 100%;
  }
  
  .model-table {
    width: 100%;
  }
}
</style>
