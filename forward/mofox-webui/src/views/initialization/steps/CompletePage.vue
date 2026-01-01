<template>
  <div class="complete-page">
    <!-- 全屏彩带效果 -->
    <div class="confetti-container" ref="confettiContainer">
      <div 
        v-for="piece in confettiPieces" 
        :key="piece.id" 
        class="confetti-piece"
        :style="piece.style"
      ></div>
    </div>
    
    <div class="card m3-card">
      <div class="complete-content">
        <!-- 成功图标 -->
        <div class="success-icon">
          <div class="icon-circle">
            <span class="material-symbols-rounded">check_circle</span>
          </div>
        </div>
        
        <!-- 标题和描述 -->
        <div class="text-content">
          <h2 class="title">🎉 配置完成！</h2>
          <p class="subtitle">MoFox Bot 已准备就绪</p>
        </div>
        
        <!-- 摘要信息 -->
        <div class="summary">
          <div class="summary-item">
            <span class="material-symbols-rounded">smart_toy</span>
            <span>机器人配置已保存</span>
            <span class="material-symbols-rounded check">done</span>
          </div>
          <div class="summary-item">
            <span class="material-symbols-rounded">psychology</span>
            <span>AI 模型已配置</span>
            <span class="material-symbols-rounded check">done</span>
          </div>
          <div class="summary-item">
            <span class="material-symbols-rounded">deployed_code</span>
            <span>Git 已配置</span>
            <span class="material-symbols-rounded check">done</span>
          </div>
        </div>
        
        <!-- 提示信息 -->
        <div class="tips">
          <h3>💡 接下来可以做什么？</h3>
          <ul>
            <li>在<strong>主控台</strong>查看机器人运行状态</li>
            <li>在<strong>配置管理</strong>中调整更多高级设置</li>
            <li>在<strong>插件市场</strong>安装更多功能插件</li>
            <li>查看<strong>日志</strong>了解机器人运行详情</li>
          </ul>
        </div>
        
        <!-- 进入主页按钮 -->
        <button class="m3-button filled large" @click="$emit('next')">
          <span>进入主控台</span>
          <span class="material-symbols-rounded">arrow_forward</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'

defineEmits<{
  next: []
}>()

// 彩带数据
interface ConfettiPiece {
  id: number
  style: Record<string, string>
}

const confettiPieces = ref<ConfettiPiece[]>([])
const confettiContainer = ref<HTMLElement | null>(null)

// 彩带颜色
const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#DDA0DD', '#87CEEB']

// 播放音效
function playPopSound() {
  try {
    // 使用 Web Audio API 生成简单的"砰"声
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)()
    
    // 创建振荡器
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    // 设置音调 - 低沉的砰声
    oscillator.frequency.setValueAtTime(150, audioContext.currentTime)
    oscillator.frequency.exponentialRampToValueAtTime(50, audioContext.currentTime + 0.1)
    
    // 设置音量包络 - 快速衰减
    gainNode.gain.setValueAtTime(0.5, audioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2)
    
    oscillator.type = 'sine'
    oscillator.start(audioContext.currentTime)
    oscillator.stop(audioContext.currentTime + 0.2)
    
    // 添加第二个音调增加层次感
    setTimeout(() => {
      const osc2 = audioContext.createOscillator()
      const gain2 = audioContext.createGain()
      
      osc2.connect(gain2)
      gain2.connect(audioContext.destination)
      
      osc2.frequency.setValueAtTime(200, audioContext.currentTime)
      osc2.frequency.exponentialRampToValueAtTime(80, audioContext.currentTime + 0.08)
      
      gain2.gain.setValueAtTime(0.3, audioContext.currentTime)
      gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15)
      
      osc2.type = 'sine'
      osc2.start(audioContext.currentTime)
      osc2.stop(audioContext.currentTime + 0.15)
    }, 50)
  } catch (e) {
    console.log('Audio not supported')
  }
}

// 生成从两侧喷出的彩带
function createConfetti() {
  const pieces: ConfettiPiece[] = []
  const totalPieces = 60
  
  for (let i = 0; i < totalPieces; i++) {
    // 决定从左侧还是右侧喷出
    const fromLeft = i < totalPieces / 2
    
    // 起始位置
    const startX = fromLeft ? -20 : window.innerWidth + 20
    const startY = window.innerHeight * (0.3 + Math.random() * 0.4) // 从中间偏上的位置喷出
    
    // 目标位置 - 向对侧喷射并下落
    const endX = fromLeft 
      ? 100 + Math.random() * (window.innerWidth * 0.6)
      : window.innerWidth - 100 - Math.random() * (window.innerWidth * 0.6)
    const endY = window.innerHeight + 100
    
    // 随机属性
    const color = colors[Math.floor(Math.random() * colors.length)]
    const size = 8 + Math.random() * 8
    const duration = 2 + Math.random() * 1.5
    const delay = Math.random() * 0.3
    const rotation = Math.random() * 1080 - 540
    
    // 形状变化
    const isRectangle = Math.random() > 0.5
    const width = isRectangle ? size : size * 0.6
    const height = isRectangle ? size * 0.6 : size
    
    pieces.push({
      id: i,
      style: {
        '--start-x': `${startX}px`,
        '--start-y': `${startY}px`,
        '--end-x': `${endX}px`,
        '--end-y': `${endY}px`,
        '--color': color!,
        '--width': `${width}px`,
        '--height': `${height}px`,
        '--duration': `${duration}s`,
        '--delay': `${delay}s`,
        '--rotation': `${rotation}deg`,
        '--mid-x': `${(startX + endX) / 2 + (Math.random() - 0.5) * 200}px`,
        '--mid-y': `${Math.min(startY, endY) - 100 - Math.random() * 150}px`
      }
    })
  }
  
  confettiPieces.value = pieces
}

onMounted(() => {
  // 延迟一点播放，让页面先渲染
  setTimeout(() => {
    playPopSound()
    createConfetti()
  }, 300)
})
</script>

<style scoped>
.complete-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 500px;
  animation: fadeIn 0.5s ease-out;
  position: relative;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 全屏彩带容器 */
.confetti-container {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 1000;
  overflow: hidden;
}

.confetti-piece {
  position: absolute;
  width: var(--width);
  height: var(--height);
  background: var(--color);
  border-radius: 2px;
  left: var(--start-x);
  top: var(--start-y);
  animation: confettiShoot var(--duration) cubic-bezier(0.25, 0.46, 0.45, 0.94) var(--delay) forwards;
  opacity: 0;
}

@keyframes confettiShoot {
  0% {
    opacity: 1;
    left: var(--start-x);
    top: var(--start-y);
    transform: rotate(0deg) scale(1);
  }
  30% {
    opacity: 1;
    left: var(--mid-x);
    top: var(--mid-y);
    transform: rotate(calc(var(--rotation) * 0.3)) scale(1.2);
  }
  100% {
    opacity: 0;
    left: var(--end-x);
    top: var(--end-y);
    transform: rotate(var(--rotation)) scale(0.5);
  }
}

.card {
  width: 100%;
  max-width: 600px;
  padding: 48px;
  background: var(--md-sys-color-surface);
  border-radius: 28px;
  box-shadow: var(--md-sys-elevation-3);
  position: relative;
  z-index: 1;
}

.complete-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
}

/* 成功图标 */
.success-icon {
  position: relative;
  width: 120px;
  height: 120px;
}

.icon-circle {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--md-sys-color-tertiary-container);
  border-radius: 50%;
  animation: scaleIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes scaleIn {
  from {
    transform: scale(0);
  }
  to {
    transform: scale(1);
  }
}

.icon-circle .material-symbols-rounded {
  font-size: 72px;
  color: var(--md-sys-color-tertiary);
  animation: checkIn 0.6s ease-out 0.3s backwards;
}

@keyframes checkIn {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 文本内容 */
.text-content {
  text-align: center;
}

.title {
  font-size: 32px;
  font-weight: 600;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 18px;
  color: var(--md-sys-color-on-surface-variant);
  margin: 0;
}

/* 摘要 */
.summary {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--md-sys-color-surface-variant);
  border-radius: 12px;
  animation: slideIn 0.5s ease-out backwards;
}

.summary-item:nth-child(1) { animation-delay: 0.6s; }
.summary-item:nth-child(2) { animation-delay: 0.7s; }
.summary-item:nth-child(3) { animation-delay: 0.8s; }

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.summary-item > .material-symbols-rounded:first-child {
  font-size: 24px;
  color: var(--md-sys-color-primary);
}

.summary-item > span:nth-child(2) {
  flex: 1;
  font-size: 14px;
  color: var(--md-sys-color-on-surface);
}

.summary-item .check {
  font-size: 20px;
  color: var(--md-sys-color-tertiary);
}

/* 提示 */
.tips {
  width: 100%;
  padding: 20px;
  background: var(--md-sys-color-primary-container);
  border-radius: 16px;
  animation: fadeIn 0.5s ease-out 0.9s backwards;
}

.tips h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--md-sys-color-on-primary-container);
  margin: 0 0 12px 0;
}

.tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tips li {
  font-size: 14px;
  line-height: 1.6;
  color: var(--md-sys-color-on-primary-container);
  padding-left: 20px;
  position: relative;
}

.tips li::before {
  content: '•';
  position: absolute;
  left: 8px;
  color: var(--md-sys-color-primary);
}

.tips strong {
  font-weight: 600;
  color: var(--md-sys-color-primary);
}

/* 按钮 */
.m3-button {
  padding: 14px 32px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 100px;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  animation: fadeIn 0.5s ease-out 1s backwards;
}

.m3-button.filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  box-shadow: var(--md-sys-elevation-1);
}

.m3-button.filled:hover {
  box-shadow: var(--md-sys-elevation-3);
  transform: scale(1.05);
}

.m3-button.filled:active {
  transform: scale(0.98);
}

.m3-button.large {
  padding: 16px 40px;
  font-size: 18px;
}

.m3-button .material-symbols-rounded {
  font-size: 24px;
}

/* 响应式 */
@media (max-width: 768px) {
  .card {
    padding: 32px 24px;
  }
  
  .success-icon {
    width: 100px;
    height: 100px;
  }
  
  .icon-circle .material-symbols-rounded {
    font-size: 60px;
  }
  
  .title {
    font-size: 28px;
  }
  
  .subtitle {
    font-size: 16px;
  }
}
</style>
