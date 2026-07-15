<script setup lang="ts">
import { computed, h } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useMessage, NDropdown } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../../store/auth';
import { useThemeStore } from '../../store/theme';
import request from '../../utils/request';

const router = useRouter();
const route = useRoute();
const message = useMessage();
const authStore = useAuthStore();
const themeStore = useThemeStore();

const handleLogout = async () => {
  try {
    await request.post('/api/logout');
  } catch {
    // 忽视报错
  }
  authStore.clearToken();
  message.success('您已安全登出。');
  router.push('/login');
};

// 页面标题映射
const pageTitle = computed(() => {
  const map: Record<string, string> = {
    'Dashboard': '仪表盘',
    'Workspace': '转换工作台',
    'History': '转换历史',
    'Profile': '个人中心',
    'Users': '用户管理',
    'Logs': '审计日志',
    'Settings': '系统设置',
  };
  return map[route.name as string] || 'SQL Convert 管理面板';
});

// 头像显示
const avatarDisplay = computed(() => {
  return authStore.avatar;
});

// 下拉菜单配置
const dropdownOptions = computed(() => [
  {
    label: '个人中心',
    key: 'profile',
    icon: () => h(Icon, { icon: 'material-symbols:person-outline', class: 'w-4 h-4' }),
  },
  { type: 'divider' as const, key: 'divider' },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(Icon, { icon: 'material-symbols:logout', class: 'w-4 h-4' }),
  },
]);

const handleDropdownSelect = (key: string) => {
  if (key === 'profile') {
    router.push('/profile');
  } else if (key === 'logout') {
    handleLogout();
  }
};
</script>

<template>
  <header
    class="h-16 px-6 flex items-center justify-between select-none shrink-0 z-40 border-b"
    :style="{ background: 'var(--bg-topbar)', borderColor: 'var(--border-color)', backdropFilter: 'blur(12px)' }"
  >
    <!-- 左侧：页面标题 -->
    <div class="flex items-center gap-3">
      <div class="text-xs font-bold uppercase tracking-wider" style="color: var(--text-muted)">
        {{ pageTitle }}
      </div>
    </div>

    <!-- 右侧 -->
    <div class="flex items-center gap-3">
      <!-- 主题切换 -->
      <button
        @click="themeStore.toggle()"
        class="w-9 h-9 rounded-lg flex items-center justify-center transition-all duration-200"
        :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }"
        :title="themeStore.isDark ? '切换到亮色模式' : '切换到暗色模式'"
      >
        <Icon :icon="themeStore.isDark ? 'material-symbols:light-mode-outline' : 'material-symbols:dark-mode-outline'" class="w-5 h-5" />
      </button>

      <!-- 头像 + 下拉菜单 -->
      <n-dropdown
        trigger="click"
        placement="bottom-end"
        :options="dropdownOptions"
        @select="handleDropdownSelect"
      >
        <button
          class="flex items-center gap-2.5 transition-all duration-200 rounded-lg px-2 py-1 cursor-pointer"
          :style="{ background: route.name === 'Profile' ? 'var(--bg-hover)' : 'transparent' }"
        >
          <div
            class="w-8 h-8 rounded-full border-2 flex items-center justify-center text-xs font-semibold select-none overflow-hidden shrink-0"
            :style="{ borderColor: themeStore.isDark ? 'rgba(255,255,255,0.1)' : 'rgba(99,102,241,0.3)' }"
          >
            <img v-if="avatarDisplay" :src="avatarDisplay" class="w-full h-full object-cover" alt="avatar" />
            <span v-else class="text-white bg-indigo-600 w-full h-full flex items-center justify-center">
              {{ authStore.username.substring(0, 2).toUpperCase() }}
            </span>
          </div>
          <span class="text-sm font-medium hidden sm:inline" style="color: var(--text-primary)">{{ authStore.username }}</span>
        </button>
      </n-dropdown>
    </div>
  </header>
</template>
