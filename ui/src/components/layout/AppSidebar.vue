<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../../store/auth';

interface MenuItem {
  key: string;
  label: string;
  icon: string;
  path: string;
  type?: 'divider';
}

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const collapsed = ref(false);

const menuItems = computed<MenuItem[]>(() => {
  const items: MenuItem[] = [
    { key: 'dashboard', label: '仪表盘', icon: 'material-symbols:dashboard-outline', path: '/dashboard' },
    { key: 'workspace', label: '转换工作台', icon: 'material-symbols:transform', path: '/workspace' },
    { key: 'history', label: '转换历史', icon: 'material-symbols:history', path: '/history' },
  ];

  if (authStore.isAdmin) {
    items.push(
      { key: 'divider', label: '', icon: '', path: '', type: 'divider' },
      { key: 'users', label: '用户管理', icon: 'material-symbols:group', path: '/users' },
      { key: 'active-users', label: '活跃用户', icon: 'material-symbols:person-play-outline', path: '/active-users' },
      { key: 'logs', label: '审计日志', icon: 'material-symbols:article-outline', path: '/logs' },
      { key: 'settings', label: '系统设置', icon: 'material-symbols:settings', path: '/settings' },
    );
  }

  return items;
});

const isActive = (path: string) => {
  return route.path.startsWith(path);
};

const navigate = (path: string) => {
  if (path && path !== route.path) {
    router.push(path);
  }
};
</script>

<template>
  <aside
    class="flex flex-col h-full transition-all duration-300 select-none shrink-0"
    :class="collapsed ? 'w-[60px]' : 'w-[220px]'"
    :style="{ background: 'var(--bg-sidebar)', borderRight: '1px solid var(--border-color)' }"
  >
    <!-- Logo 区域 -->
    <div class="h-16 flex items-center px-4 border-b shrink-0" :style="{ borderColor: 'var(--border-color)' }">
      <router-link to="/dashboard" class="flex items-center gap-3 no-underline overflow-hidden">
        <div class="w-9 h-9 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
          <Icon icon="material-symbols:database" class="w-5 h-5" />
        </div>
        <transition name="fade">
          <div v-if="!collapsed" class="flex flex-col">
            <span class="text-sm font-bold" style="color: #f1f5f9">SQL Convert</span>
            <span class="text-[9px] font-mono" style="color: #94a3b8">CONVERTER PLATFORM</span>
          </div>
        </transition>
      </router-link>
    </div>

    <!-- 导航菜单 -->
    <nav class="flex-1 py-4 px-2 space-y-0.5 overflow-y-auto">
      <template v-for="item in menuItems" :key="item.key">
        <!-- 分隔线 -->
        <div
          v-if="item.type === 'divider'"
          class="mx-3 my-3 border-t"
          style="border-color: rgba(255, 255, 255, 0.12)"
        />

        <!-- 菜单项 -->
        <button
          v-else
          @click="navigate(item.path)"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group"
          :class="isActive(item.path)
            ? 'bg-indigo-600/10 border border-indigo-500/20 text-indigo-400'
            : 'text-gray-400 hover:text-gray-200 hover:bg-white/5 border border-transparent'"
          :title="collapsed ? item.label : ''"
        >
          <Icon :icon="item.icon" class="w-5 h-5 shrink-0" />
          <transition name="fade">
            <span v-if="!collapsed" class="truncate text-left">{{ item.label }}</span>
          </transition>
        </button>
      </template>
    </nav>

    <!-- 底部折叠按钮 -->
    <div class="p-2 border-t shrink-0" :style="{ borderColor: 'var(--border-color)' }">
      <button
        @click="collapsed = !collapsed"
        class="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-gray-500 hover:text-gray-300 hover:bg-white/5 transition-all duration-200 text-xs"
      >
        <Icon
          :icon="collapsed ? 'material-symbols:chevron-right' : 'material-symbols:chevron-left'"
          class="w-5 h-5 transition-transform duration-300"
        />
        <transition name="fade">
          <span v-if="!collapsed">收起菜单</span>
        </transition>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
