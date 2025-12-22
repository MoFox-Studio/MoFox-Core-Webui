import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUIStore = defineStore('ui', () => {
  const isDocOpen = ref(false)

  function toggleDoc() {
    isDocOpen.value = !isDocOpen.value
  }

  function openDoc() {
    isDocOpen.value = true
  }

  function closeDoc() {
    isDocOpen.value = false
  }

  return {
    isDocOpen,
    toggleDoc,
    openDoc,
    closeDoc
  }
})
