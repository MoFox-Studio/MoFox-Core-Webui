<template>
  <div class="theme-config-view">
    <div class="page-header">
      <div class="header-content">
        <h1>风格与壁纸</h1>
        <p class="subtitle">自定义 WebUI 的外观和配色方案</p>
      </div>
    </div>

    <div class="config-content">
      <!-- 预览区域 -->
      <div class="preview-section">
        <div class="preview-card">
          <div class="preview-header">
            <div class="preview-title">预览</div>
          </div>
          <div class="preview-body">
            <div class="mock-ui">
              <div class="mock-sidebar">
                <div class="mock-icon active"></div>
                <div class="mock-icon"></div>
                <div class="mock-icon"></div>
              </div>
              <div class="mock-content">
                <div class="mock-card primary">
                  <div class="mock-line title"></div>
                  <div class="mock-line"></div>
                </div>
                <div class="mock-row">
                  <div class="mock-card secondary"></div>
                  <div class="mock-card tertiary"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 颜色选择 -->
      <div class="config-section">
        <h2>基本颜色</h2>
        <div class="color-presets">
          <button
            v-for="preset in presetPreviews"
            :key="preset.source"
            class="preset-item"
            :class="{ active: themeStore.sourceColor.toLowerCase() === preset.source.toLowerCase() }"
            @click="themeStore.setSourceColor(preset.source)"
            :title="preset.source"
          >
            <div class="preset-circle" :style="getPresetStyle(preset)">
              <span v-if="themeStore.sourceColor.toLowerCase() === preset.source.toLowerCase()" class="material-symbols-rounded check-icon">check</span>
            </div>
            <span class="preset-label">{{ getPresetName(preset.source) }}</span>
          </button>
          
          <!-- 自定义颜色 -->
          <button 
            class="preset-item custom-picker"
            :class="{ active: !isPreset(themeStore.sourceColor) }"
            @click="openCustomColorModal"
            title="自定义颜色"
          >
            <div class="preset-circle custom-circle" :style="!isPreset(themeStore.sourceColor) ? { background: themeStore.sourceColor } : {}">
              <span class="material-symbols-rounded more-icon" :style="{ color: !isPreset(themeStore.sourceColor) ? '#fff' : '' }">palette</span>
            </div>
            <span class="preset-label">自定义</span>
          </button>
        </div>
      </div>

      <!-- 深色模式 -->
      <div class="config-section">
        <h2>深色主题</h2>
        <div class="mode-toggles">
          <button 
            class="mode-card"
            :class="{ active: themeStore.theme === 'light' }"
            @click="setTheme('light')"
          >
            <div class="mode-preview light">
              <span class="material-symbols-rounded">light_mode</span>
            </div>
            <span class="mode-label">浅色模式</span>
            <div class="radio-indicator">
              <div class="radio-inner"></div>
            </div>
          </button>
          
          <button 
            class="mode-card"
            :class="{ active: themeStore.theme === 'dark' }"
            @click="setTheme('dark')"
          >
            <div class="mode-preview dark">
              <span class="material-symbols-rounded">dark_mode</span>
            </div>
            <span class="mode-label">深色模式</span>
            <div class="radio-indicator">
              <div class="radio-inner"></div>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- 自定义颜色弹窗 -->
    <Transition name="fade">
      <div v-if="showColorModal" class="modal-overlay" @click="closeColorModal">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>自定义主题色</h3>
            <button class="close-btn" @click="closeColorModal">
              <span class="material-symbols-rounded">close</span>
            </button>
          </div>
          
          <div class="modal-body">
            <!-- HSV Color Picker -->
            <div class="hsv-picker">
              <div 
                class="saturation-area" 
                ref="saturationArea"
                :style="{ backgroundColor: `hsl(${hsv.h}, 100%, 50%)` }"
                @mousedown="startDragSaturation"
                @touchstart.prevent="startDragSaturation"
              >
                <div class="saturation-white"></div>
                <div class="saturation-black"></div>
                <div 
                  class="saturation-cursor" 
                  :style="{ 
                    left: `${hsv.s}%`, 
                    top: `${100 - hsv.v}%`,
                    backgroundColor: tempColor
                  }"
                ></div>
              </div>
              <div 
                class="hue-slider" 
                ref="hueSlider"
                @mousedown="startDragHue"
                @touchstart.prevent="startDragHue"
              >
                <div 
                  class="hue-cursor" 
                  :style="{ left: `${(hsv.h / 360) * 100}%` }"
                ></div>
              </div>
            </div>
            
            <div class="color-controls">
              <!-- Hex 输入 -->
              <div class="hex-input-wrapper">
                <span class="hex-prefix">#</span>
                <input 
                  type="text" 
                  v-model="tempHex" 
                  @input="handleHexInput"
                  class="hex-input"
                  maxlength="6"
                />
              </div>

              <!-- RGB 滑块 -->
              <div class="sliders-container">
                <div class="slider-row">
                  <span class="slider-label red">R</span>
                  <input 
                    type="range" 
                    min="0" 
                    max="255" 
                    v-model.number="tempRgb.r"
                    @input="handleRgbInput"
                    class="color-slider red-slider"
                  />
                  <span class="slider-value">{{ tempRgb.r }}</span>
                </div>
                <div class="slider-row">
                  <span class="slider-label green">G</span>
                  <input 
                    type="range" 
                    min="0" 
                    max="255" 
                    v-model.number="tempRgb.g"
                    @input="handleRgbInput"
                    class="color-slider green-slider"
                  />
                  <span class="slider-value">{{ tempRgb.g }}</span>
                </div>
                <div class="slider-row">
                  <span class="slider-label blue">B</span>
                  <input 
                    type="range" 
                    min="0" 
                    max="255" 
                    v-model.number="tempRgb.b"
                    @input="handleRgbInput"
                    class="color-slider blue-slider"
                  />
                  <span class="slider-value">{{ tempRgb.b }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-text" @click="closeColorModal">取消</button>
            <button class="btn-filled" @click="applyCustomColor">应用</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useThemeStore } from '@/stores/theme'
import { 
  argbFromHex, 
  themeFromSourceColor, 
  hexFromArgb 
} from '@material/material-color-utilities'

const themeStore = useThemeStore()

// Custom Color Modal Logic
const showColorModal = ref(false)
const tempColor = ref('#6750A4')
const tempHex = ref('6750A4')
const tempRgb = reactive({ r: 103, g: 80, b: 164 })
const hsv = reactive({ h: 266, s: 51, v: 64 })

const saturationArea = ref<HTMLElement | null>(null)
const hueSlider = ref<HTMLElement | null>(null)
const isDraggingSaturation = ref(false)
const isDraggingHue = ref(false)

const hexToRgb = (hex: string) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1]!, 16),
    g: parseInt(result[2]!, 16),
    b: parseInt(result[3]!, 16)
  } : { r: 0, g: 0, b: 0 }
}

const rgbToHex = (r: number, g: number, b: number) => {
  return "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase()
}

const rgbToHsv = (r: number, g: number, b: number) => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s, v = max;
  const d = max - min;
  s = max === 0 ? 0 : d / max;

  if (max === min) {
    h = 0; 
  } else {
    switch (max) {
      case r: h = (g - b) / d + (g < b ? 6 : 0); break;
      case g: h = (b - r) / d + 2; break;
      case b: h = (r - g) / d + 4; break;
    }
    h /= 6;
  }
  return { h: Math.round(h * 360), s: Math.round(s * 100), v: Math.round(v * 100) };
}

const hsvToRgb = (h: number, s: number, v: number) => {
  let r, g, b;
  const i = Math.floor(h / 60);
  const f = h / 60 - i;
  const p = v * (1 - s / 100);
  const q = v * (1 - f * s / 100);
  const t = v * (1 - (1 - f) * s / 100);
  
  switch (i % 6) {
    case 0: r = v, g = t, b = p; break;
    case 1: r = q, g = v, b = p; break;
    case 2: r = p, g = v, b = t; break;
    case 3: r = p, g = q, b = v; break;
    case 4: r = t, g = p, b = v; break;
    case 5: r = v, g = p, b = q; break;
    default: r = 0, g = 0, b = 0;
  }
  return { 
    r: Math.round(r * 2.55), 
    g: Math.round(g * 2.55), 
    b: Math.round(b * 2.55) 
  };
}

const updateColorFromHsv = () => {
  const rgb = hsvToRgb(hsv.h, hsv.s, hsv.v)
  tempRgb.r = rgb.r
  tempRgb.g = rgb.g
  tempRgb.b = rgb.b
  const hex = rgbToHex(rgb.r, rgb.g, rgb.b)
  tempColor.value = hex
  tempHex.value = hex.replace('#', '')
}

const openCustomColorModal = () => {
  tempColor.value = themeStore.sourceColor
  tempHex.value = themeStore.sourceColor.replace('#', '')
  const rgb = hexToRgb(themeStore.sourceColor)
  tempRgb.r = rgb.r
  tempRgb.g = rgb.g
  tempRgb.b = rgb.b
  
  const newHsv = rgbToHsv(rgb.r, rgb.g, rgb.b)
  hsv.h = newHsv.h
  hsv.s = newHsv.s
  hsv.v = newHsv.v
  
  showColorModal.value = true
}

const closeColorModal = () => {
  showColorModal.value = false
}

const handleHexInput = () => {
  // Allow only hex chars
  tempHex.value = tempHex.value.replace(/[^0-9A-Fa-f]/g, '').toUpperCase()
  
  if (tempHex.value.length === 6) {
    const hex = '#' + tempHex.value
    tempColor.value = hex
    const rgb = hexToRgb(hex)
    tempRgb.r = rgb.r
    tempRgb.g = rgb.g
    tempRgb.b = rgb.b
    
    const newHsv = rgbToHsv(rgb.r, rgb.g, rgb.b)
    hsv.h = newHsv.h
    hsv.s = newHsv.s
    hsv.v = newHsv.v
  }
}

const handleRgbInput = () => {
  const hex = rgbToHex(tempRgb.r, tempRgb.g, tempRgb.b)
  tempColor.value = hex
  tempHex.value = hex.replace('#', '')
  
  const newHsv = rgbToHsv(tempRgb.r, tempRgb.g, tempRgb.b)
  hsv.h = newHsv.h
  hsv.s = newHsv.s
  hsv.v = newHsv.v
}

// Dragging Logic
const startDragSaturation = (e: MouseEvent | TouchEvent) => {
  isDraggingSaturation.value = true
  handleSaturationDrag(e)
}

const startDragHue = (e: MouseEvent | TouchEvent) => {
  isDraggingHue.value = true
  handleHueDrag(e)
}

const handleSaturationDrag = (e: MouseEvent | TouchEvent) => {
  if (!saturationArea.value) return
  const rect = saturationArea.value.getBoundingClientRect()
  
  let clientX, clientY
  if ('touches' in e) {
    const touch = e.touches[0]
    if (!touch) return
    clientX = touch.clientX
    clientY = touch.clientY
  } else {
    clientX = e.clientX
    clientY = e.clientY
  }
  
  let x = (clientX - rect.left) / rect.width
  let y = (clientY - rect.top) / rect.height
  
  x = Math.max(0, Math.min(1, x))
  y = Math.max(0, Math.min(1, y))
  
  hsv.s = Math.round(x * 100)
  hsv.v = Math.round((1 - y) * 100)
  
  updateColorFromHsv()
}

const handleHueDrag = (e: MouseEvent | TouchEvent) => {
  if (!hueSlider.value) return
  const rect = hueSlider.value.getBoundingClientRect()
  
  let clientX
  if ('touches' in e) {
    const touch = e.touches[0]
    if (!touch) return
    clientX = touch.clientX
  } else {
    clientX = e.clientX
  }
  
  let x = (clientX - rect.left) / rect.width
  x = Math.max(0, Math.min(1, x))
  
  hsv.h = Math.round(x * 360)
  
  updateColorFromHsv()
}

const stopDrag = () => {
  isDraggingSaturation.value = false
  isDraggingHue.value = false
}

const onMouseMove = (e: MouseEvent | TouchEvent) => {
  if (isDraggingSaturation.value) handleSaturationDrag(e)
  if (isDraggingHue.value) handleHueDrag(e)
}

onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', stopDrag)
  window.addEventListener('touchmove', onMouseMove)
  window.addEventListener('touchend', stopDrag)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onMouseMove)
  window.removeEventListener('mouseup', stopDrag)
  window.removeEventListener('touchmove', onMouseMove)
  window.removeEventListener('touchend', stopDrag)
})

const applyCustomColor = () => {
  themeStore.setSourceColor(tempColor.value)
  closeColorModal()
}

const setTheme = (mode: 'light' | 'dark') => {
  if (themeStore.theme !== mode) {
    themeStore.toggleTheme()
  }
}

// Presets
const presets = [
  { color: '#6750A4', name: '深紫' },
  { color: '#386A20', name: '苔绿' },
  { color: '#006874', name: '青色' },
  { color: '#9C4146', name: '砖红' },
  { color: '#7D5260', name: '粉红' },
  { color: '#825500', name: '棕色' },
  { color: '#006D31', name: '翠绿' },
  { color: '#006783', name: '湖蓝' },
]

const presetPreviews = computed(() => presets.map(p => {
  const theme = themeFromSourceColor(argbFromHex(p.color))
  return {
    source: p.color,
    name: p.name,
    c1: hexFromArgb(theme.schemes.light.primary),
    c2: hexFromArgb(theme.schemes.light.secondaryContainer),
    c3: hexFromArgb(theme.schemes.light.tertiaryContainer),
    c4: hexFromArgb(theme.schemes.light.surfaceVariant)
  }
}))

const isPreset = (color: string) => {
  return presets.some(p => p.color.toLowerCase() === color.toLowerCase())
}

const getPresetName = (color: string) => {
  const preset = presets.find(p => p.color.toLowerCase() === color.toLowerCase())
  return preset ? preset.name : '自定义'
}

const getPresetStyle = (preset: any) => {
  return {
    background: `conic-gradient(
      ${preset.c1} 0% 25%, 
      ${preset.c2} 25% 50%, 
      ${preset.c3} 50% 75%, 
      ${preset.c4} 75% 100%
    )`
  }
}
</script>

<style scoped>
.theme-config-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  overflow-y: auto;
}

.page-header {
  padding: 24px 32px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.header-content h1 {
  font-size: 24px;
  font-weight: 400;
  color: var(--text-primary);
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

.config-content {
  padding: 32px;
  max-width: 1000px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 48px;
}

.config-section h2 {
  font-size: 20px;
  font-weight: 400;
  color: var(--text-primary);
  margin: 0 0 24px 0;
}

/* Preview Section */
.preview-section {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.preview-card {
  width: 300px;
  height: 200px;
  background: var(--md-sys-color-surface);
  border-radius: 16px;
  border: 1px solid var(--border-color);
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
}

.preview-header {
  height: 40px;
  background: var(--md-sys-color-surface-container);
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid var(--border-color);
}

.preview-title {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

.preview-body {
  flex: 1;
  padding: 16px;
  background: var(--md-sys-color-background);
}

.mock-ui {
  display: flex;
  height: 100%;
  gap: 12px;
}

.mock-sidebar {
  width: 40px;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 0;
  gap: 8px;
}

.mock-icon {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  background: var(--md-sys-color-on-surface-variant);
  opacity: 0.2;
}

.mock-icon.active {
  background: var(--md-sys-color-secondary-container);
  opacity: 1;
  color: var(--md-sys-color-on-secondary-container);
}

.mock-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mock-card {
  border-radius: 8px;
  padding: 8px;
}

.mock-card.primary {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-on-primary-container);
  height: 60px;
}

.mock-card.secondary {
  background: var(--md-sys-color-secondary-container);
  flex: 1;
  height: 40px;
}

.mock-card.tertiary {
  background: var(--md-sys-color-tertiary-container);
  flex: 1;
  height: 40px;
}

.mock-row {
  display: flex;
  gap: 8px;
}

.mock-line {
  height: 6px;
  border-radius: 3px;
  background: currentColor;
  opacity: 0.3;
  margin-bottom: 6px;
}

.mock-line.title {
  width: 60%;
  height: 8px;
  opacity: 0.8;
}

/* Color Presets */
.color-presets {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 24px;
}

.preset-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.preset-circle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border-color);
  transition: transform 0.2s;
}

.preset-item:hover .preset-circle {
  transform: scale(1.1);
}

.preset-item.active .preset-circle {
  border: 3px solid var(--md-sys-color-primary);
}

.custom-circle {
  background: var(--md-sys-color-surface-container-high);
}

.check-icon {
  font-size: 24px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
}

.more-icon {
  font-size: 24px;
  color: var(--text-secondary);
}

.preset-label {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.preset-item.active .preset-label {
  color: var(--md-sys-color-primary);
  font-weight: 600;
}

.hidden-color-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}

/* Mode Toggles */
.mode-toggles {
  display: flex;
  gap: 24px;
}

.mode-card {
  flex: 1;
  max-width: 200px;
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 0;
}

.mode-preview {
  width: 100%;
  height: 120px;
  border-radius: 16px;
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.mode-preview.light {
  background: #FEF7FF;
  color: #1D1B20;
}

.mode-preview.dark {
  background: #141218;
  color: #E6E1E5;
}

.mode-preview span {
  font-size: 48px;
}

.mode-card.active .mode-preview {
  border: 3px solid var(--md-sys-color-primary);
}

.mode-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.radio-indicator {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--text-tertiary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mode-card.active .radio-indicator {
  border-color: var(--md-sys-color-primary);
}

.radio-inner {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--md-sys-color-primary);
  opacity: 0;
  transform: scale(0);
  transition: all 0.2s;
}

.mode-card.active .radio-inner {
  opacity: 1;
  transform: scale(1);
}

/* Modal Styles */
.modal-overlay {
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

.modal-content {
  background: var(--md-sys-color-surface);
  border-radius: 28px;
  width: 600px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.15);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 24px 24px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-header h3 {
  margin: 0;
  font-size: 24px;
  font-weight: 400;
  color: var(--md-sys-color-on-surface);
}

.close-btn {
  background: none;
  border: none;
  color: var(--md-sys-color-on-surface-variant);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
}

.close-btn:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.modal-body {
  padding: 0 24px 24px;
  display: flex;
  flex-direction: row;
  gap: 24px;
}

.color-controls {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 240px;
}

.color-preview-large {
  height: 120px;
  border-radius: 16px;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.hex-input-wrapper {
  display: flex;
  align-items: center;
  background: var(--md-sys-color-surface-container);
  border-radius: 8px;
  padding: 0 16px;
  height: 56px;
  border-bottom: 1px solid var(--md-sys-color-outline);
}

.hex-prefix {
  font-size: 16px;
  color: var(--md-sys-color-on-surface-variant);
  margin-right: 8px;
}

.hex-input {
  background: none;
  border: none;
  font-size: 16px;
  color: var(--md-sys-color-on-surface);
  width: 100%;
  outline: none;
  text-transform: uppercase;
  font-family: monospace;
}

.sliders-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.slider-label {
  width: 20px;
  font-size: 14px;
  font-weight: 500;
}

.slider-label.red { color: #B3261E; }
.slider-label.green { color: #386A20; }
.slider-label.blue { color: #006783; }

.color-slider {
  flex: 1;
  height: 4px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--md-sys-color-surface-container-highest);
  border-radius: 2px;
  outline: none;
}

.color-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.red-slider::-webkit-slider-thumb { background: #B3261E; }
.green-slider::-webkit-slider-thumb { background: #386A20; }
.blue-slider::-webkit-slider-thumb { background: #006783; }

.slider-value {
  width: 32px;
  text-align: right;
  font-size: 14px;
  color: var(--md-sys-color-on-surface-variant);
}

.modal-footer {
  padding: 16px 24px 24px;
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.btn-text {
  background: none;
  border: none;
  color: var(--md-sys-color-primary);
  font-weight: 500;
  padding: 10px 24px;
  border-radius: 20px;
  cursor: pointer;
}

.btn-text:hover {
  background: var(--md-sys-color-surface-container-highest);
}

.btn-filled {
  background: var(--md-sys-color-primary);
  color: var(--md-sys-color-on-primary);
  border: none;
  font-weight: 500;
  padding: 10px 24px;
  border-radius: 20px;
  cursor: pointer;
}

.btn-filled:hover {
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  opacity: 0.9;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* HSV Picker */
.hsv-picker {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.saturation-area {
  width: 100%;
  height: 200px;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  cursor: crosshair;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.saturation-white {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to right, #fff, rgba(255,255,255,0));
}

.saturation-black {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to top, #000, rgba(0,0,0,0));
}

.saturation-cursor {
  position: absolute;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 2px rgba(0,0,0,0.5);
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.hue-slider {
  width: 100%;
  height: 24px;
  border-radius: 12px;
  position: relative;
  background: linear-gradient(to right, 
    #f00 0%, #ff0 17%, #0f0 33%, 
    #0ff 50%, #00f 67%, #f0f 83%, #f00 100%);
  cursor: pointer;
  border: 1px solid var(--md-sys-color-outline-variant);
}

.hue-cursor {
  position: absolute;
  top: 50%;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--md-sys-color-outline);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  transform: translate(-50%, -50%);
  pointer-events: none;
}
</style>