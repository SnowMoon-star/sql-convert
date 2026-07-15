<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useMessage, useDialog, NTooltip, NSelect } from 'naive-ui';
import { Icon } from '@iconify/vue';
import request from '../../utils/request';
import { useAuthStore } from '../../store/auth';

const message = useMessage();
const dialog = useDialog();
const authStore = useAuthStore();

const currentUsername = computed(() => authStore.username);
const sessions = ref<any[]>([]);
const loading = ref(false);

// 分页
const pageSize = 10;
const currentPage = ref(1);
const total = ref(0);
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)));

const pageNumbers = computed(() => {
  const totalP = totalPages.value;
  if (totalP <= 7) return Array.from({ length: totalP }, (_, i) => i + 1);
  const cur = currentPage.value;
  const pages: (number | '...')[] = [1];
  if (cur > 3) pages.push('...');
  for (let i = Math.max(2, cur - 1); i <= Math.min(totalP - 1, cur + 1); i++) pages.push(i);
  if (cur < totalP - 2) pages.push('...');
  pages.push(totalP);
  return pages;
});

const searchUsername = ref('');
const searchIp = ref('');
const searchRole = ref<number | null>(null);

const roleOptions: any[] = [
  { label: '全部身份', value: null },
  { label: '管理员', value: 1 },
  { label: '普通用户', value: 0 }
];

const fetchSessions = async () => {
  loading.value = true;
  try {
    const params: any = {
      page: currentPage.value,
      size: pageSize,
    };
    if (searchUsername.value.trim()) params.username = searchUsername.value.trim();
    if (searchIp.value.trim()) params.ip = searchIp.value.trim();
    if (searchRole.value !== null) params.is_admin = searchRole.value;

    const res: any = await request.get('/api/active-users', { params });
    sessions.value = res && Array.isArray(res.items) ? res.items : [];
    total.value = res && typeof res.total === 'number' ? res.total : 0;
  } catch (error: any) {
    message.error(error.response?.data?.detail || '获取活跃用户列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchSessions();
};

const handleReset = () => {
  searchUsername.value = '';
  searchIp.value = '';
  searchRole.value = null;
  currentPage.value = 1;
  fetchSessions();
};

const canKick = (session: any) => {
  // 不能踢自己
  if (session.username === currentUsername.value) return false;
  // 超管可以踢任何人
  if (currentUsername.value === 'admin') return true;
  // 普通管理员不能踢管理员
  if (session.is_admin) return false;
  return true;
};

const getKickTooltip = (session: any) => {
  if (session.username === currentUsername.value) {
    return '不能踢出当前登录会话';
  }
  if (currentUsername.value !== 'admin' && session.is_admin) {
    return '无权踢出其他管理员';
  }
  return '强行下线';
};

const handleKick = (session: any) => {
  dialog.warning({
    title: '强制下线',
    content: `确定要强制将用户 "${session.username}" 的会话踢下线吗？被踢出的用户将无法再发起任何请求。`,
    positiveText: '确认踢出',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.post('/api/active-users/kick', {
          session_token: session.session_token
        });
        message.success('会话踢出成功');
        fetchSessions();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '踢出会话失败');
      }
    }
  });
};

const convertUtc8ToLocalStr = (utc8Str: string | null | undefined): string => {
  if (!utc8Str) return '—';
  const formattedStr = utc8Str.replace('T', ' ').split('.')[0];
  const parts = formattedStr.split(' ');
  if (parts.length !== 2) return formattedStr;
  
  const dateParts = parts[0].split('-');
  const timeParts = parts[1].split(':');
  if (dateParts.length !== 3 || timeParts.length < 2) return formattedStr;
  
  const year = parseInt(dateParts[0], 10);
  const month = parseInt(dateParts[1], 10) - 1;
  const date = parseInt(dateParts[2], 10);
  const hour = parseInt(timeParts[0], 10);
  const minute = parseInt(timeParts[1], 10);
  const second = timeParts.length === 3 ? parseInt(timeParts[2], 10) : 0;
  
  const utcMs = Date.UTC(year, month, date, hour, minute, second);
  const utcTimeMs = utcMs - 8 * 3600000;
  const localDate = new Date(utcTimeMs);
  
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${localDate.getFullYear()}-${pad(localDate.getMonth() + 1)}-${pad(localDate.getDate())} ${pad(localDate.getHours())}:${pad(localDate.getMinutes())}:${pad(localDate.getSeconds())}`;
};

const formatDateTime = (val: string) => {
  if (!val) return '—';
  return convertUtc8ToLocalStr(val);
};

const handlePrevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value -= 1;
    fetchSessions();
  }
};

const handleNextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value += 1;
    fetchSessions();
  }
};

const handlePageClick = (p: number) => {
  currentPage.value = p;
  fetchSessions();
};

onMounted(() => {
  fetchSessions();
});
</script>

<template>
  <div class="flex flex-col gap-5 h-full">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h2 class="text-lg font-bold" style="color: var(--text-primary)">活跃用户</h2>
        <p class="text-xs mt-0.5" style="color: var(--text-muted)">监控当前系统在线的所有活跃会话并支持踢出下线</p>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="flex items-center gap-3 shrink-0">
      <!-- 用户名搜索 -->
      <div class="relative flex-1 max-w-xs shrink-0">
        <Icon icon="material-symbols:search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--text-muted)" />
        <input v-model="searchUsername" type="text" placeholder="搜索用户名..."
          class="w-full h-[34px] pl-9 pr-3 rounded-lg text-sm outline-none transition-colors duration-200"
          :style="{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
          @keyup.enter="handleSearch" />
      </div>

      <!-- IP 搜索 -->
      <div class="relative flex-1 max-w-xs shrink-0">
        <Icon icon="material-symbols:search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--text-muted)" />
        <input v-model="searchIp" type="text" placeholder="搜索 IP 地址..."
          class="w-full h-[34px] pl-9 pr-3 rounded-lg text-sm outline-none transition-colors duration-200"
          :style="{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
          @keyup.enter="handleSearch" />
      </div>

      <!-- 身份筛选 -->
      <n-select v-model:value="searchRole" :options="roleOptions"
        placeholder="全部身份" clearable class="shrink-0" :style="{ width: '130px' }" />

      <!-- 查询 -->
      <button @click="handleSearch"
        class="h-[34px] px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shrink-0 transition-all active:scale-[0.98]">
        <Icon icon="material-symbols:search" class="w-4 h-4" />查询
      </button>

      <!-- 重置 -->
      <button @click="handleReset"
        class="h-[34px] px-5 rounded-lg text-xs flex items-center gap-2 transition-all duration-200 border shrink-0"
        :style="{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
        <Icon icon="material-symbols:refresh" class="w-4 h-4" />重置
      </button>
    </div>

    <!-- 活跃会话表格 -->
    <div class="flex-1 rounded-xl overflow-hidden flex flex-col min-h-0 border"
         :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
      <div class="grid grid-cols-12 gap-4 px-5 py-3 border-b text-[11px] font-bold uppercase tracking-wider shrink-0"
           :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-muted)' }">
        <span class="col-span-3">用户名</span>
        <span class="col-span-2">身份</span>
        <span class="col-span-2">登录 IP</span>
        <span class="col-span-3">登录时间</span>
        <span class="col-span-2 text-right">操作</span>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div v-if="loading" class="p-8 text-center text-sm" style="color: var(--text-muted)">加载中...</div>
        <div v-else-if="sessions.length === 0" class="p-8 text-center text-sm" style="color: var(--text-muted)">暂无活跃用户数据</div>
        <div
          v-else
          v-for="session in sessions"
          :key="session.session_token"
          class="grid grid-cols-12 gap-4 px-5 py-3.5 items-center transition-colors duration-150 border-b"
          :style="{ borderColor: 'var(--border-color)' }"
        >
          <div class="col-span-3 flex items-center gap-2.5 min-w-0">
            <div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center text-indigo-400 text-xs font-bold shrink-0"
                 :class="session.avatar ? '' : 'bg-indigo-600/20 border border-indigo-500/20'">
              <img v-if="session.avatar" :src="session.avatar" class="w-full h-full object-cover" alt="avatar" />
              <span v-else>{{ session.username.substring(0, 2).toUpperCase() }}</span>
            </div>
            <div class="flex items-center gap-1.5 min-w-0">
              <span class="text-sm font-medium truncate" style="color: var(--text-primary)">{{ session.username }}</span>
              <span v-if="session.username === currentUsername" class="text-[10px] px-1.5 py-0.5 rounded bg-indigo-600/20 text-indigo-400 border border-indigo-500/20 font-semibold scale-90 shrink-0">
                当前
              </span>
            </div>
          </div>
          <div class="col-span-2">
            <span
              class="text-xs px-2 py-0.5 rounded font-semibold"
              :class="session.is_admin ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/20' : 'bg-white/5 text-gray-400 border border-white/10'"
            >
              {{ session.is_admin ? '管理员' : '普通用户' }}
            </span>
          </div>
          <div class="col-span-2 text-sm font-mono" style="color: var(--text-secondary)">
            {{ session.ip || '—' }}
          </div>
          <div class="col-span-3 text-sm font-mono font-medium" style="color: var(--text-primary)">
            {{ formatDateTime(session.created_at) }}
          </div>
          <div class="col-span-2 flex items-center justify-end gap-1.5">
            <!-- 踢出 -->
            <n-tooltip trigger="hover" placement="top">
              <template #trigger>
                <button 
                  @click="canKick(session) && handleKick(session)"
                  :disabled="!canKick(session)"
                  class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border shrink-0"
                  :class="canKick(session)
                    ? 'border-red-500/20 bg-red-600/10 hover:bg-red-600/20 text-red-400 cursor-pointer'
                    : 'border-white/5 bg-white/5 text-gray-600 cursor-not-allowed'"
                >
                  <Icon icon="material-symbols:logout" class="w-4 h-4" />
                </button>
              </template>
              {{ getKickTooltip(session) }}
            </n-tooltip>
          </div>
        </div>
      </div>

      <!-- 分页条 -->
      <div v-if="sessions.length > 0" class="flex items-center justify-between px-5 py-3 border-t shrink-0"
           :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)' }">
        <span class="text-xs" style="color: var(--text-muted)">
          共 {{ total }} 条，第 {{ currentPage }} / {{ totalPages }} 页
        </span>
        <div class="flex items-center gap-1">
          <!-- 上一页 -->
          <button
            @click="handlePrevPage"
            :disabled="currentPage === 1"
            class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
            :style="currentPage === 1
              ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' }
              : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
          >
            <Icon icon="material-symbols:chevron-left" class="w-4 h-4" />
          </button>

          <!-- 页码 -->
          <template v-for="p in pageNumbers" :key="p">
            <span v-if="p === '...'" class="w-7 h-7 flex items-center justify-center text-xs" style="color: var(--text-muted)">…</span>
            <button v-else
              @click="handlePageClick(p as number)"
              class="w-7 h-7 rounded flex items-center justify-center text-xs font-medium transition-colors border"
              :style="currentPage === p
                ? { background: '#4f46e5', borderColor: '#4f46e5', color: '#fff' }
                : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
            >{{ p }}</button>
          </template>

          <!-- 下一页 -->
          <button
            @click="handleNextPage"
            :disabled="currentPage === totalPages"
            class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
            :style="currentPage === totalPages
              ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' }
              : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
          >
            <Icon icon="material-symbols:chevron-right" class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
