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
    host: '127.0.0.1',
    proxy: {
      // 将 API 请求代理到发现服务器（开发环境）
      // 发现服务器会进一步代理到主程序
      '/plugins': {
        target: 'http://localhost:12138',
        changeOrigin: true,
      },
      // 保留原有的 /api 代理（如果需要）
      '/api': {
        target: 'http://localhost:12138',
        changeOrigin: true,
      },
    },
  },
})
