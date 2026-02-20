import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      'vue-demi': 'vue-demi/lib/v3/index.mjs',
    },
  },
  server: {
    port: 11451,
    host: 'localhost',
    proxy: {
      // 将 WebSocket 请求代理到发现服务器（开发环境）
      '/ws': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true, // 启用 WebSocket 代理
      },
      // 将 API 请求代理到 Neo-MoFox（开发环境）
      '/webui': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true, // 启用 WebSocket 代理
      },
    },
  },
})
