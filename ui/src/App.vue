<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { darkTheme, lightTheme, zhCN, dateZhCN, NConfigProvider, NDialogProvider, NMessageProvider } from 'naive-ui';
import { useThemeStore } from './store/theme';
import AppLayout from './components/layout/AppLayout.vue';

const route = useRoute();
const themeStore = useThemeStore();

const isLoginPage = computed(() => route.name === 'Login');

const naiveTheme = computed(() => themeStore.isDark ? darkTheme : lightTheme);

const themeOverrides = computed(() => ({
  common: {
    primaryColor: '#6366f1',
    primaryColorHover: '#4f46e5',
    primaryColorPressed: '#4338ca',
    primaryColorSuppl: '#818cf8',
    borderRadius: '8px',
  },
  Card: {
    borderRadius: '12px',
  },
  Input: {
    borderRadius: '8px',
  },
  Button: {
    borderRadius: '8px',
  }
}));
</script>

<template>
  <n-config-provider
    :theme="naiveTheme"
    :locale="zhCN"
    :date-locale="dateZhCN"
    :theme-overrides="themeOverrides"
  >
    <n-dialog-provider>
      <n-message-provider>
        <!-- 登录页不使用侧边栏布局 -->
        <router-view v-if="isLoginPage" />
        <!-- 其他页面使用带侧边栏的布局 -->
        <AppLayout v-else />
      </n-message-provider>
    </n-dialog-provider>
  </n-config-provider>
</template>

<style>
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}
</style>
