<template>
  <div class="settings-container">
    <div class="settings-card">
      <h2 class="card-title">
        <Icon icon="material-symbols:settings-account-box-outline" class="title-icon" />
        人设配置 (Personality Config)
      </h2>
      <div class="editor-container">
        <vue-monaco-editor
          v-model:value="code"
          :theme="editorTheme"
          language="json"
          :options="editorOptions"
          @mount="handleMount"
        />
      </div>
      <div class="actions">
        <button class="pixel-button save-btn" @click="saveConfig">保存配置</button>
        <button class="pixel-button reset-btn" @click="resetConfig">重置</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, shallowRef, computed } from 'vue'
import { Icon } from '@iconify/vue'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'
import { useThemeStore } from '@/stores/theme'

const themeStore = useThemeStore()
const editorTheme = computed(() => themeStore.theme === 'dark' ? 'vs-dark' : 'vs-light')

const code = ref(`{
  "name": "MoFox",
  "personality": "cute, helpful, fox-girl",
  "language": "zh-CN",
  "model_config": {
    "temperature": 0.7,
    "max_tokens": 2048
  }
}`)

const editorOptions = {
  automaticLayout: true,
  formatOnType: true,
  formatOnPaste: true,
  minimap: {
    enabled: false
  },
  fontSize: 14,
  fontFamily: "'Fira Code', Consolas, monospace"
}

const editorRef = shallowRef()

const handleMount = (editor: any) => {
  editorRef.value = editor
}

const saveConfig = () => {
  console.log('Config saved:', code.value)
  // TODO: Implement save logic
  alert('配置已保存 (模拟)')
}

const resetConfig = () => {
  // TODO: Implement reset logic
}
</script>

<style scoped>
.settings-container {
  padding: 20px;
  height: 100%;
}

.settings-card {
  background: var(--bg-white);
  padding: 25px;
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--shadow);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 14px;
  color: var(--primary-blue);
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--lighter-blue);
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-icon {
  font-size: 20px;
}

.editor-container {
  flex: 1;
  border: 1px solid var(--lighter-blue);
  border-radius: 4px;
  overflow: hidden;
  min-height: 400px;
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 15px;
  justify-content: flex-end;
}

.pixel-button {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  font-family: 'Press Start 2P', sans-serif;
  font-size: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn {
  background: var(--primary-blue);
  color: white;
}

.save-btn:hover {
  background: var(--light-blue);
  transform: translateY(-2px);
}

.reset-btn {
  background: var(--bg-light);
  color: var(--text-gray);
  border: 1px solid var(--border-color);
}

.reset-btn:hover {
  background: #e0e0e0;
}
</style>
