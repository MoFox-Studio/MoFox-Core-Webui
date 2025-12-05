<template>
  <router-view />
</template>

<script setup lang="ts">
import { useThemeStore } from '@/stores/theme'

// 初始化主题
const themeStore = useThemeStore()
</script>

<style scoped>
</style>
