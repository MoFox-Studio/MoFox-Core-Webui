import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'
import { 
  argbFromHex, 
  themeFromSourceColor, 
  hexFromArgb,
  type Theme
} from '@material/material-color-utilities'

export const useThemeStore = defineStore('theme', () => {
  const theme = ref(localStorage.getItem('theme') || 'light')
  const sourceColor = ref(localStorage.getItem('sourceColor') || '#6750A4')

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }

  const setSourceColor = (color: string) => {
    sourceColor.value = color
  }

  const updateTheme = () => {
    try {
      // Generate theme from source color
      const argb = argbFromHex(sourceColor.value)
      const m3Theme = themeFromSourceColor(argb)
      
      const isDark = theme.value === 'dark'
      const scheme = isDark ? m3Theme.schemes.dark : m3Theme.schemes.light

      const root = document.documentElement

      // Helper to set CSS variable
      const setVar = (name: string, value: number) => {
        root.style.setProperty(`--md-sys-color-${name}`, hexFromArgb(value))
      }

      // Manually apply all scheme colors to ensure everything updates
      // Core colors
      setVar('primary', scheme.primary)
      setVar('on-primary', scheme.onPrimary)
      setVar('primary-container', scheme.primaryContainer)
      setVar('on-primary-container', scheme.onPrimaryContainer)

      setVar('secondary', scheme.secondary)
      setVar('on-secondary', scheme.onSecondary)
      setVar('secondary-container', scheme.secondaryContainer)
      setVar('on-secondary-container', scheme.onSecondaryContainer)

      setVar('tertiary', scheme.tertiary)
      setVar('on-tertiary', scheme.onTertiary)
      setVar('tertiary-container', scheme.tertiaryContainer)
      setVar('on-tertiary-container', scheme.onTertiaryContainer)

      setVar('error', scheme.error)
      setVar('on-error', scheme.onError)
      setVar('error-container', scheme.errorContainer)
      setVar('on-error-container', scheme.onErrorContainer)

      // Surfaces
      setVar('background', scheme.background)
      setVar('on-background', scheme.onBackground)
      
      setVar('surface', scheme.surface)
      setVar('on-surface', scheme.onSurface)
      setVar('surface-variant', scheme.surfaceVariant)
      setVar('on-surface-variant', scheme.onSurfaceVariant)

      // Surface Containers (New in M3)
      // Check if these exist on the scheme object (they should in newer versions)
      // If not, fallback to surface or mix
      if ('surfaceContainer' in scheme) {
        setVar('surface-container', (scheme as any).surfaceContainer)
        setVar('surface-container-high', (scheme as any).surfaceContainerHigh)
        setVar('surface-container-highest', (scheme as any).surfaceContainerHighest)
        setVar('surface-container-low', (scheme as any).surfaceContainerLow)
        setVar('surface-container-lowest', (scheme as any).surfaceContainerLowest)
      } else {
        // Fallback using Neutral palette if scheme doesn't have container colors
        const neutral = m3Theme.palettes.neutral
        if (isDark) {
            setVar('surface-container', neutral.tone(12))
            setVar('surface-container-high', neutral.tone(17))
            setVar('surface-container-highest', neutral.tone(22))
            setVar('surface-container-low', neutral.tone(10))
            setVar('surface-container-lowest', neutral.tone(4))
        } else {
            setVar('surface-container', neutral.tone(94))
            setVar('surface-container-high', neutral.tone(92))
            setVar('surface-container-highest', neutral.tone(90))
            setVar('surface-container-low', neutral.tone(96))
            setVar('surface-container-lowest', neutral.tone(100))
        }
      }

      setVar('outline', scheme.outline)
      setVar('outline-variant', scheme.outlineVariant)
      setVar('inverse-surface', scheme.inverseSurface)
      setVar('inverse-on-surface', scheme.inverseOnSurface)
      setVar('inverse-primary', scheme.inversePrimary)

      // Update data-theme attribute
      document.documentElement.setAttribute('data-theme', theme.value)
      
      // Persist settings
      localStorage.setItem('theme', theme.value)
      localStorage.setItem('sourceColor', sourceColor.value)
    } catch (e) {
      console.error('Failed to apply theme:', e)
    }
  }

  watch([theme, sourceColor], () => {
    updateTheme()
  }, { immediate: true })

  const isDark = computed(() => theme.value === 'dark')

  return {
    theme,
    sourceColor,
    isDark,
    toggleTheme,
    setSourceColor
  }
})
