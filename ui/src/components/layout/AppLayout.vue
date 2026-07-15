<script setup lang="ts">
import { onMounted } from 'vue';
import { useAuthStore } from '../../store/auth';
import AppSidebar from './AppSidebar.vue';
import AppTopBar from './AppTopBar.vue';

const authStore = useAuthStore();

onMounted(() => {
  // 启动时从后端恢复用户信息（兼容已有会话未存储 is_admin 的情况）
  authStore.fetchUserInfo();
});
</script>

<template>
  <div class="flex h-screen w-full overflow-hidden theme-transition relative"
       :style="{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }">
    <!-- 背景流光特效 -->
    <div class="bg-glow-bubble-1"></div>
    <div class="bg-glow-bubble-2"></div>

    <!-- 侧边栏 -->
    <AppSidebar class="z-10" />

    <!-- 主内容区 -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <!-- 顶部栏 -->
      <AppTopBar />

      <!-- 页面内容 -->
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>
