import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  // 从 localStorage 恢复主题偏好，默认为 'light'
  const saved = localStorage.getItem('theme') || 'light';
  const isDark = ref(saved === 'dark');

  function toggle() {
    isDark.value = !isDark.value;
  }

  function setTheme(dark: boolean) {
    isDark.value = dark;
  }

  // 持久化到 localStorage 并更新 document 的 class
  watch(isDark, (val) => {
    const theme = val ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
    document.documentElement.setAttribute('data-theme', theme);
  }, { immediate: true });

  return { isDark, toggle, setTheme };
});
