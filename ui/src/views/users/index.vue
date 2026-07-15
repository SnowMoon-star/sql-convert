<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useMessage, useDialog, NModal, NCard, NSelect, NTooltip } from 'naive-ui';
import { Icon } from '@iconify/vue';
import request from '../../utils/request';
import { useAuthStore } from '../../store/auth';

const message = useMessage();
const dialog = useDialog();
const authStore = useAuthStore();

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

const currentUsername = computed(() => authStore.username);
const users = ref<any[]>([]);
const loading = ref(false);

// 分页
const pageSize = 10;
const currentPage = ref(1);
const totalPages = computed(() => Math.max(1, Math.ceil(users.value.length / pageSize)));
const pagedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return users.value.slice(start, start + pageSize);
});
const pageNumbers = computed(() => {
  const total = totalPages.value;
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const cur = currentPage.value;
  const pages: (number | '...')[] = [1];
  if (cur > 3) pages.push('...');
  for (let i = Math.max(2, cur - 1); i <= Math.min(total - 1, cur + 1); i++) pages.push(i);
  if (cur < total - 2) pages.push('...');
  pages.push(total);
  return pages;
});
const showCreateModal = ref(false);
const showEditModal = ref(false);
const editingUser = ref<any>(null);

// 表单
const formUsername = ref('');
const formIsAdmin = ref(0);
const editIsAdmin = ref(0);

const getUserAvatar = (user: any) => {
  return user?.avatar || '';
};

const userRoleOptions: any[] = [
  { label: '管理员', value: 1 },
  { label: '普通用户', value: 0 }
];

const handleResetPassword = (user: any) => {
  dialog.warning({
    title: '重置密码',
    content: `确定要将用户 "${user.username}" 的密码重置为 "123456" 吗？`,
    positiveText: '确认重置',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.put(`/api/users/${user.username}`, {
          password: '123456',
          is_admin: user.is_admin ? 1 : 0
        });
        message.success('密码已成功重置为 123456');
        fetchUsers();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '重置密码失败');
      }
    }
  });
};

const searchUsername = ref('');
const searchRole = ref<number | null>(null);
const searchStatus = ref<number | null>(null);

const roleOptions: any[] = [
  { label: '全部角色', value: null },
  { label: '管理员', value: 1 },
  { label: '普通用户', value: 0 }
];

const statusOptions: any[] = [
  { label: '全部状态', value: null },
  { label: '正常', value: 0 },
  { label: '已锁定', value: 1 }
];

const fetchUsers = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (searchUsername.value.trim()) params.username = searchUsername.value.trim();
    if (searchRole.value !== null) params.is_admin = searchRole.value;
    if (searchStatus.value !== null) params.is_locked = searchStatus.value;

    const res: any = await request.get('/api/users', { params });
    users.value = Array.isArray(res) ? res : [];
  } catch (error: any) {
    message.error(error.response?.data?.detail || '获取用户列表失败');
  } finally {
    loading.value = false;
  }
};

const handleSearch = () => {
  currentPage.value = 1;
  fetchUsers();
};

const handleReset = () => {
  searchUsername.value = '';
  searchRole.value = null;
  searchStatus.value = null;
  currentPage.value = 1;
  fetchUsers();
};

const handleCreate = async () => {
  if (!formUsername.value) {
    message.warning('用户名不能为空');
    return;
  }
  try {
    await request.post('/api/users', {
      username: formUsername.value,
      password: '123456',
      is_admin: formIsAdmin.value,
    });
    message.success('用户创建成功，默认密码为 123456');
    showCreateModal.value = false;
    formUsername.value = '';
    formIsAdmin.value = 0;
    fetchUsers();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '创建失败');
  }
};

const openEdit = (user: any) => {
  editingUser.value = user;
  editIsAdmin.value = user.is_admin ? 1 : 0;
  showEditModal.value = true;
};

const handleEdit = async () => {
  if (!editingUser.value) return;
  try {
    const body: any = {};
    body.is_admin = editIsAdmin.value;
    await request.put(`/api/users/${editingUser.value.username}`, body);
    message.success('用户更新成功');
    showEditModal.value = false;
    fetchUsers();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '更新失败');
  }
};

const handleDelete = (user: any) => {
  dialog.warning({
    title: '删除用户',
    content: `确定要删除用户 "${user.username}" 吗？此操作不可撤销。`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.delete(`/api/users/${user.username}`);
        message.success('用户已删除');
        fetchUsers();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '删除失败');
      }
    }
  });
};

const handleUnlock = (user: any) => {
  dialog.info({
    title: '解锁用户',
    content: `确定要解锁用户 "${user.username}" 吗？`,
    positiveText: '确认解锁',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.post(`/api/users/${user.username}/unlock`);
        message.success('用户已解锁');
        fetchUsers();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '解锁失败');
      }
    }
  });
};

onMounted(() => {
  fetchUsers();
});
</script>

<template>
  <div class="flex flex-col gap-5 h-full">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h2 class="text-lg font-bold" style="color: var(--text-primary)">用户管理</h2>
        <p class="text-xs mt-0.5" style="color: var(--text-muted)">管理系统用户账号、权限与安全状态</p>
      </div>
      <button
        @click="showCreateModal = true"
        class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/10 transition-all duration-200 active:scale-[0.98]"
      >
        <Icon icon="material-symbols:person-add" class="w-4 h-4" />
        新增用户
      </button>
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

      <!-- 角色筛选 -->
      <n-select v-model:value="searchRole" :options="roleOptions"
        placeholder="全部角色" clearable class="shrink-0" :style="{ width: '120px' }" />

      <!-- 状态筛选 -->
      <n-select v-model:value="searchStatus" :options="statusOptions"
        placeholder="全部状态" clearable class="shrink-0" :style="{ width: '120px' }" />

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

    <!-- 用户表格 -->
    <div class="flex-1 rounded-xl overflow-hidden flex flex-col min-h-0 border"
         :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
      <div class="grid grid-cols-12 gap-4 px-5 py-3 border-b text-[11px] font-bold uppercase tracking-wider shrink-0"
           :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-muted)' }">
        <span class="col-span-3">用户名</span>
        <span class="col-span-2">角色</span>
        <span class="col-span-2">状态</span>
        <span class="col-span-2">创建时间</span>
        <span class="col-span-3 text-right">操作</span>
      </div>

      <div class="flex-1 overflow-y-auto">
        <div v-if="loading" class="p-8 text-center text-sm" style="color: var(--text-muted)">加载中...</div>
        <div v-else-if="users.length === 0" class="p-8 text-center text-sm" style="color: var(--text-muted)">暂无用户数据</div>
        <div
          v-for="user in pagedUsers"
          :key="user.username"
          class="grid grid-cols-12 gap-4 px-5 py-3.5 items-center transition-colors duration-150 border-b"
          :style="{ borderColor: 'var(--border-color)' }"
        >
          <div class="col-span-3 flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center text-indigo-400 text-xs font-bold shrink-0"
              :class="getUserAvatar(user) ? '' : 'bg-indigo-600/20 border border-indigo-500/20'">
              <img v-if="getUserAvatar(user)" :src="getUserAvatar(user)" class="w-full h-full object-cover" alt="avatar" />
              <span v-else>{{ user.username.substring(0, 2).toUpperCase() }}</span>
            </div>
            <span class="text-sm font-medium" style="color: var(--text-primary)">{{ user.username }}</span>
          </div>
          <div class="col-span-2">
            <span
              class="text-xs px-2 py-0.5 rounded font-semibold"
              :class="user.is_admin ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/20' : ''"
              :style="user.is_admin ? {} : { background: 'var(--bg-hover)', color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }"
            >
              {{ user.is_admin ? '管理员' : '普通用户' }}
            </span>
          </div>
          <div class="col-span-2">
            <span class="flex items-center gap-1.5 text-xs">
              <span v-if="user.is_locked" class="w-1.5 h-1.5 rounded-full bg-red-500"></span>
              <span v-else class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span :class="user.is_locked ? 'text-red-400' : 'text-emerald-400'">
                {{ user.is_locked ? '已锁定' : '正常' }}
              </span>
            </span>
          </div>
          <div class="col-span-2 text-sm font-mono font-medium" style="color: var(--text-primary)">{{ convertUtc8ToLocalStr(user.created_at) }}</div>
          <div class="col-span-3 flex items-center justify-end gap-1.5">
            <!-- 编辑 -->
            <n-tooltip v-if="currentUsername === 'admin' || !user.is_admin || user.username === currentUsername" trigger="hover" placement="top">
              <template #trigger>
                <button @click="openEdit(user)"
                  class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border shrink-0"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                  <Icon icon="material-symbols:edit-outline" class="w-4 h-4" />
                </button>
              </template>
              编辑角色
            </n-tooltip>

            <!-- 重置密码 -->
            <n-tooltip v-if="currentUsername === 'admin' || !user.is_admin || user.username === currentUsername" trigger="hover" placement="top">
              <template #trigger>
                <button @click="handleResetPassword(user)"
                  class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border shrink-0"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                  <Icon icon="material-symbols:lock-reset" class="w-4 h-4" />
                </button>
              </template>
              重置密码
            </n-tooltip>

            <!-- 解锁 -->
            <n-tooltip v-if="user.is_locked && (currentUsername === 'admin' || !user.is_admin || user.username === currentUsername)" trigger="hover" placement="top">
              <template #trigger>
                <button @click="handleUnlock(user)"
                  class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border border-emerald-500/20 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 shrink-0">
                  <Icon icon="material-symbols:lock-open-outline" class="w-4 h-4" />
                </button>
              </template>
              解锁用户
            </n-tooltip>

            <!-- 删除 -->
            <n-tooltip v-if="user.username !== currentUsername && user.username !== 'admin' && (currentUsername === 'admin' || !user.is_admin)" trigger="hover" placement="top">
              <template #trigger>
                <button @click="handleDelete(user)"
                  class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border border-red-500/20 bg-red-600/10 hover:bg-red-600/20 text-red-400 shrink-0">
                  <Icon icon="material-symbols:delete-outline" class="w-4 h-4" />
                </button>
              </template>
              删除用户
            </n-tooltip>
          </div>
        </div>
      </div>

      <!-- 分页条（固定在表格底部，不随内容滚动） -->
      <div v-if="users.length > 0" class="flex items-center justify-between px-5 py-3 border-t shrink-0"
           :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)' }">
        <span class="text-xs" style="color: var(--text-muted)">
          共 {{ users.length }} 条，第 {{ currentPage }} / {{ totalPages }} 页
        </span>
        <div class="flex items-center gap-1">
          <!-- 上一页 -->
          <button
            @click="currentPage > 1 && (currentPage -= 1)"
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
              @click="currentPage = (p as number)"
              class="w-7 h-7 rounded flex items-center justify-center text-xs font-medium transition-colors border"
              :style="currentPage === p
                ? { background: '#4f46e5', borderColor: '#4f46e5', color: '#fff' }
                : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
            >{{ p }}</button>
          </template>

          <!-- 下一页 -->
          <button
            @click="currentPage < totalPages && (currentPage += 1)"
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

    <!-- 创建用户模态框 -->
    <n-modal v-model:show="showCreateModal">
      <n-card title="新增用户" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">用户名</label>
            <input
              v-model="formUsername"
              type="text"
              placeholder="请输入用户名"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
            />
          </div>

          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">角色</label>
            <n-select
              v-model:value="formIsAdmin"
              :options="userRoleOptions"
              class="w-full"
            />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button
              @click="showCreateModal = false"
              class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
            >
              取消
            </button>
            <button
              @click="handleCreate"
              class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]"
            >
              确认创建
            </button>
          </div>
        </div>
      </n-card>
    </n-modal>

    <!-- 编辑用户模态框 -->
    <n-modal v-model:show="showEditModal">
      <n-card title="编辑用户" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">用户名</label>
            <input
              :value="editingUser?.username"
              disabled
              class="w-full h-10 px-3 rounded-lg text-sm outline-none cursor-not-allowed"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }"
            />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">角色</label>
            <n-select
              v-model:value="editIsAdmin"
              :options="userRoleOptions"
              class="w-full"
            />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button
              @click="showEditModal = false"
              class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }"
            >
              取消
            </button>
            <button
              @click="handleEdit"
              class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]"
            >
              保存修改
            </button>
          </div>
        </div>
      </n-card>
    </n-modal>
  </div>
</template>

<style scoped>
:deep(.n-base-selection) {
  background-color: var(--bg-secondary) !important;
  border-radius: 8px !important;
  height: 34px !important;
  --n-height: 34px !important;
  --n-border: 1px solid var(--border-color) !important;
  --n-border-hover: 1px solid #6366f1 !important;
  --n-border-active: 1px solid #6366f1 !important;
  --n-border-focus: 1px solid #6366f1 !important;
  --n-box-shadow-hover: none !important;
  --n-box-shadow-active: none !important;
  --n-box-shadow-focus: none !important;
  --n-color: var(--bg-secondary) !important;
  --n-color-active: var(--bg-secondary) !important;
  --n-text-color: var(--text-primary) !important;
  --n-caret-color: #6366f1 !important;
  --n-arrow-color: var(--text-muted) !important;
  --n-loading-color: #6366f1 !important;
}

:deep(.n-base-selection-placeholder) {
  color: var(--text-muted) !important;
  line-height: 34px !important;
}

:deep(.n-base-selection-label) {
  line-height: 34px !important;
  color: var(--text-primary) !important;
}

:deep(.n-input) {
  background-color: var(--bg-secondary) !important;
  border-radius: 8px !important;
  height: 34px !important;
  --n-height: 34px !important;
  --n-border: 1px solid var(--border-color) !important;
  --n-border-hover: 1px solid #6366f1 !important;
  --n-border-active: 1px solid #6366f1 !important;
  --n-border-focus: 1px solid #6366f1 !important;
  --n-box-shadow-hover: none !important;
  --n-box-shadow-active: none !important;
  --n-box-shadow-focus: none !important;
  --n-color: var(--bg-secondary) !important;
  --n-color-focus: var(--bg-secondary) !important;
  --n-text-color: var(--text-primary) !important;
  --n-caret-color: #6366f1 !important;
  --n-placeholder-color: var(--text-muted) !important;
}

:deep(.n-input__input) {
  height: 32px !important;
}

:deep(.n-input-wrapper) {
  padding-left: 12px !important;
  padding-right: 12px !important;
}
</style>
