<template>
  <div class="main-content">
    <div class="content-card">
      <h2 class="card-title">
        <Icon icon="material-symbols:trending-up" class="title-icon" />
        API调用趋势
      </h2>
      <div class="chart-container">
        <v-chart class="chart" :option="chartOption" :theme="themeStore.theme" autoresize />
      </div>
    </div>
    
    <div class="content-card">
      <h2 class="card-title">
        <Icon icon="material-symbols:data-usage" class="title-icon" />
        Token消耗详情
      </h2>
      <div class="token-details">
        <div class="detail-item">
          <span class="detail-label">GPT-4</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: 45%"></div>
          </div>
          <span class="detail-value">45%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Claude 3.5</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: 30%; background-color: #F39C12"></div>
          </div>
          <span class="detail-value">30%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Gemini Pro</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: 15%; background-color: #2ECC71"></div>
          </div>
          <span class="detail-value">15%</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Local Model</span>
          <div class="progress-bar">
            <div class="progress-fill" style="width: 10%; background-color: #9B59B6"></div>
          </div>
          <span class="detail-value">10%</span>
        </div>
        
        <div class="total-cost">
          <span class="cost-label">今日预估花费</span>
          <span class="cost-value">$2.45</span>
        </div>
      </div>
    </div>

    <div class="content-card full-width">
      <h2 class="card-title">
        <Icon icon="material-symbols:speed-outline" class="title-icon" />
        消息流量监控
      </h2>
      <div class="chart-container">
        <v-chart class="chart" :option="performanceOption" :theme="themeStore.theme" autoresize />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Icon } from '@iconify/vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { useThemeStore } from '@/stores/theme'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
])

const themeStore = useThemeStore()

const chartOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['请求数', 'Token消耗']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '请求数',
      type: 'line',
      smooth: true,
      data: [120, 132, 101, 134, 90, 230, 210],
      itemStyle: {
        color: '#4A90E2'
      }
    },
    {
      name: 'Token消耗',
      type: 'line',
      smooth: true,
      data: [220, 182, 191, 234, 290, 330, 310],
      itemStyle: {
        color: '#F39C12'
      }
    }
  ]
})

const performanceOption = ref({
  tooltip: {
    trigger: 'axis'
  },
  legend: {
    data: ['接收消息', '发送消息']
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    boundaryGap: false,
    data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
  },
  yAxis: {
    type: 'value'
  },
  series: [
    {
      name: '接收消息',
      type: 'line',
      smooth: true,
      data: [150, 230, 224, 218, 135, 147, 260],
      itemStyle: {
        color: '#2ECC71'
      },
      areaStyle: {
        opacity: 0.1
      }
    },
    {
      name: '发送消息',
      type: 'line',
      smooth: true,
      data: [140, 210, 200, 200, 120, 130, 240],
      itemStyle: {
        color: '#3498DB'
      },
      areaStyle: {
        opacity: 0.1
      }
    }
  ]
})
</script>

<style scoped>
.main-content {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.full-width {
  grid-column: 1 / -1;
}

.content-card {
  background: var(--bg-white);
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--shadow);
  display: flex;
  flex-direction: column;
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

.chart-container {
  height: 300px;
  width: 100%;
}

.chart {
  height: 100%;
  width: 100%;
}

.token-details {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 10px;
}

.detail-label {
  width: 80px;
  color: var(--text-dark);
}

.progress-bar {
  flex: 1;
  height: 8px;
  background-color: var(--bg-light);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-blue);
  border-radius: 4px;
}

.detail-value {
  width: 40px;
  text-align: right;
  color: var(--text-gray);
}

.total-cost {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid var(--lighter-blue);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cost-label {
  font-size: 10px;
  color: var(--text-dark);
}

.cost-value {
  font-size: 16px;
  font-weight: bold;
  color: var(--primary-blue);
  font-family: 'Press Start 2P', cursive;
}

@media (max-width: 768px) {
  .main-content {
    grid-template-columns: 1fr;
  }
}
</style>
