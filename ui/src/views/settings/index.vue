<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useMessage, useDialog, NTabs, NTabPane, NModal, NCard, NSelect, NTooltip } from 'naive-ui';
import { Icon } from '@iconify/vue';
import request from '../../utils/request';

const message = useMessage();
const dialog = useDialog();

// ── 全局选项 ──
const userRoleOptions = [
  { label: '是', value: 1 },
  { label: '否', value: 0 }
];

const lockoutStatusOptions = [
  { label: '全部状态', value: -1 },
  { label: '已锁定', value: 1 },
  { label: '正常', value: 0 }
];

const pageSize = 10;

// ── Tab 1: IP 白名单 ──
const whitelistEnabled = ref(false);
const whitelistItems = ref<any[]>([]);
const loadingWhitelist = ref(false);
const searchWhitelistIp = ref('');
const whitelistPage = ref(1);

const totalWhitelistPages = computed(() => Math.max(1, Math.ceil(whitelistItems.value.length / pageSize)));
const pagedWhitelist = computed(() => {
  const start = (whitelistPage.value - 1) * pageSize;
  return whitelistItems.value.slice(start, start + pageSize);
});

const showAddWhitelistModal = ref(false);
const showEditWhitelistModal = ref(false);
const formWhitelistIp = ref('');
const oldWhitelistIp = ref('');

const fetchWhitelist = async () => {
  loadingWhitelist.value = true;
  try {
    const params: any = {};
    if (searchWhitelistIp.value.trim()) {
      params.ip = searchWhitelistIp.value.trim();
    }
    const res: any = await request.get('/api/settings/whitelist', { params });
    whitelistEnabled.value = res.enabled || false;
    whitelistItems.value = Array.isArray(res.whitelist) ? res.whitelist : [];
  } catch (error: any) {
    message.error(error.response?.data?.detail || '获取白名单失败', { duration: 3000 });
  } finally {
    loadingWhitelist.value = false;
  }
};

const handleAddWhitelist = async () => {
  if (!formWhitelistIp.value.trim()) {
    message.warning('请输入 IP 地址', { duration: 3000 });
    return;
  }
  try {
    await request.post('/api/settings/whitelist', { ip: formWhitelistIp.value.trim() });
    message.success('添加成功', { duration: 3000 });
    showAddWhitelistModal.value = false;
    formWhitelistIp.value = '';
    fetchWhitelist();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '添加失败', { duration: 3000 });
  }
};

const openEditWhitelist = (ip: string) => {
  oldWhitelistIp.value = ip;
  formWhitelistIp.value = ip;
  showEditWhitelistModal.value = true;
};

const handleEditWhitelist = async () => {
  if (!formWhitelistIp.value.trim()) {
    message.warning('请输入新 IP 地址', { duration: 3000 });
    return;
  }
  try {
    await request.put('/api/settings/whitelist', {
      old_ip: oldWhitelistIp.value,
      new_ip: formWhitelistIp.value.trim()
    });
    message.success('修改成功', { duration: 3000 });
    showEditWhitelistModal.value = false;
    fetchWhitelist();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '修改失败', { duration: 3000 });
  }
};

const handleDeleteWhitelist = (ip: string) => {
  dialog.warning({
    title: '移除白名单',
    content: `确定要从白名单中移除 IP "${ip}" 吗？该 IP 可能因此失去访问权限。`,
    positiveText: '确认移除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.delete(`/api/settings/whitelist/${ip}`);
        message.success('移除成功', { duration: 3000 });
        fetchWhitelist();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '移除失败', { duration: 3000 });
      }
    }
  });
};

// ── Tab 2: 用户账号锁定监控 ──
const userLockoutItems = ref<any[]>([]);
const loadingUserLockout = ref(false);
const searchUserLockoutName = ref('');
const filterUserLockoutStatus = ref<number>(-1);
const userLockoutPage = ref(1);

const totalUserLockoutPages = computed(() => Math.max(1, Math.ceil(userLockoutItems.value.length / pageSize)));
const pagedUserLockouts = computed(() => {
  const start = (userLockoutPage.value - 1) * pageSize;
  return userLockoutItems.value.slice(start, start + pageSize);
});

const showAddUserLockoutModal = ref(false);
const showEditUserLockoutModal = ref(false);
const formLockUsername = ref('');
const formLockFailCount = ref(0);
const formLockCount = ref(0);
const formLockIsPermanent = ref(0);
const formLockTime = ref('');
const editingLockUser = ref<string>('');

const fetchUserLockouts = async () => {
  loadingUserLockout.value = true;
  try {
    const params: any = {};
    if (searchUserLockoutName.value.trim()) {
      params.username = searchUserLockoutName.value.trim();
    }
    if (filterUserLockoutStatus.value !== -1) {
      params.is_locked = filterUserLockoutStatus.value;
    }
    const res: any = await request.get('/api/settings/user-lockouts', { params });
    userLockoutItems.value = Array.isArray(res) ? res : [];
  } catch (error: any) {
    message.error(error.response?.data?.detail || '获取账号锁定记录失败', { duration: 3000 });
  } finally {
    loadingUserLockout.value = false;
  }
};

const handleCreateUserLockout = async () => {
  if (!formLockUsername.value.trim()) {
    message.warning('请输入用户名', { duration: 3000 });
    return;
  }
  try {
    await request.post('/api/settings/user-lockouts', {
      username: formLockUsername.value.trim(),
      fail_count: formLockFailCount.value,
      lock_count: formLockCount.value,
      is_permanent_lock: formLockIsPermanent.value,
      lock_time: formLockIsPermanent.value === 1 ? null : (formLockTime.value || null)
    });
    message.success('锁定记录创建成功', { duration: 3000 });
    showAddUserLockoutModal.value = false;
    formLockUsername.value = '';
    formLockFailCount.value = 0;
    formLockCount.value = 0;
    formLockIsPermanent.value = 0;
    formLockTime.value = '';
    fetchUserLockouts();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '创建失败', { duration: 3000 });
  }
};

const openEditUserLockout = (item: any) => {
  editingLockUser.value = item.username;
  formLockFailCount.value = item.fail_count;
  formLockCount.value = item.lock_count;
  formLockIsPermanent.value = item.is_permanent_lock ? 1 : 0;
  formLockTime.value = item.lock_time || '';
  showEditUserLockoutModal.value = true;
};

const handleEditUserLockout = async () => {
  try {
    await request.put(`/api/settings/user-lockouts/${editingLockUser.value}`, {
      fail_count: formLockFailCount.value,
      lock_count: formLockCount.value,
      is_permanent_lock: formLockIsPermanent.value,
      lock_time: formLockIsPermanent.value === 1 ? null : (formLockTime.value || null)
    });
    message.success('更新监控记录成功', { duration: 3000 });
    showEditUserLockoutModal.value = false;
    fetchUserLockouts();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '更新失败', { duration: 3000 });
  }
};

const handleDeleteUserLockout = (username: string) => {
  dialog.warning({
    title: '清除锁定状态',
    content: `确定要清除并解锁用户 "${username}" 的登录失败监控记录吗？`,
    positiveText: '确认解锁',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.delete(`/api/settings/user-lockouts/${username}`);
        message.success('解锁监控已清除', { duration: 3000 });
        fetchUserLockouts();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '解锁失败', { duration: 3000 });
      }
    }
  });
};

// ── Tab 3: IP 锁定封禁监控 ──
const ipLockoutItems = ref<any[]>([]);
const loadingIpLockout = ref(false);
const searchIpLockoutVal = ref('');
const filterIpLockoutStatus = ref<number>(-1);
const ipLockoutPage = ref(1);

const totalIpLockoutPages = computed(() => Math.max(1, Math.ceil(ipLockoutItems.value.length / pageSize)));
const pagedIpLockouts = computed(() => {
  const start = (ipLockoutPage.value - 1) * pageSize;
  return ipLockoutItems.value.slice(start, start + pageSize);
});

const showAddIpLockoutModal = ref(false);
const showEditIpLockoutModal = ref(false);
const formLockIpVal = ref('');
const formLockIpFailCount = ref(0);
const formLockIpIsPermanent = ref(0);
const formLockIpTime = ref('');
const editingLockIpVal = ref<string>('');

const fetchIpLockouts = async () => {
  loadingIpLockout.value = true;
  try {
    const params: any = {};
    if (searchIpLockoutVal.value.trim()) {
      params.ip = searchIpLockoutVal.value.trim();
    }
    if (filterIpLockoutStatus.value !== -1) {
      params.is_locked = filterIpLockoutStatus.value;
    }
    const res: any = await request.get('/api/settings/ip-lockouts', { params });
    ipLockoutItems.value = Array.isArray(res) ? res : [];
  } catch (error: any) {
    message.error(error.response?.data?.detail || '获取 IP 封禁记录失败', { duration: 3000 });
  } finally {
    loadingIpLockout.value = false;
  }
};

const handleCreateIpLockout = async () => {
  if (!formLockIpVal.value.trim()) {
    message.warning('请输入 IP 地址', { duration: 3000 });
    return;
  }
  try {
    await request.post('/api/settings/ip-lockouts', {
      ip: formLockIpVal.value.trim(),
      fail_count: formLockIpFailCount.value,
      is_permanent_lock: formLockIpIsPermanent.value,
      lock_time: formLockIpIsPermanent.value === 1 ? null : (formLockIpTime.value || null)
    });
    message.success('IP 封禁记录创建成功', { duration: 3000 });
    showAddIpLockoutModal.value = false;
    formLockIpVal.value = '';
    formLockIpFailCount.value = 0;
    formLockIpIsPermanent.value = 0;
    formLockIpTime.value = '';
    fetchIpLockouts();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '创建失败', { duration: 3000 });
  }
};

const openEditIpLockout = (item: any) => {
  editingLockIpVal.value = item.ip;
  formLockIpFailCount.value = item.fail_count;
  formLockIpIsPermanent.value = item.is_permanent_lock ? 1 : 0;
  formLockIpTime.value = item.lock_time || '';
  showEditIpLockoutModal.value = true;
};

const handleEditIpLockout = async () => {
  try {
    await request.put(`/api/settings/ip-lockouts/${editingLockIpVal.value}`, {
      fail_count: formLockIpFailCount.value,
      is_permanent_lock: formLockIpIsPermanent.value,
      lock_time: formLockIpIsPermanent.value === 1 ? null : (formLockIpTime.value || null)
    });
    message.success('更新 IP 监控成功', { duration: 3000 });
    showEditIpLockoutModal.value = false;
    fetchIpLockouts();
  } catch (error: any) {
    message.error(error.response?.data?.detail || '更新失败', { duration: 3000 });
  }
};

const handleDeleteIpLockout = (ip: string) => {
  dialog.warning({
    title: '解除 IP 封禁',
    content: `确定要解除对 IP "${ip}" 的锁定封禁状态吗？`,
    positiveText: '确认解封',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await request.delete(`/api/settings/ip-lockouts/${ip}`);
        message.success('IP 封禁已解除', { duration: 3000 });
        fetchIpLockouts();
      } catch (error: any) {
        message.error(error.response?.data?.detail || '解封失败', { duration: 3000 });
      }
    }
  });
};


// ── Tab 4: 运行参数与关于 ──
const maxUploadSize = ref(500);
const historyRetentionDays = ref(30);
const maxWorkers = ref(4);

// const saveConfig = () => {
//   message.info('运行参数修改需通过后端 config.yml 文件进行。', { duration: 3000 });
// };

// ── 初始化 ──
onMounted(() => {
  fetchWhitelist();
  fetchUserLockouts();
  fetchIpLockouts();
});
</script>

<template>
  <div class="flex flex-col gap-5 h-full">
    <!-- 页面标题 -->
    <div class="shrink-0">
      <h2 class="text-lg font-bold" style="color: var(--text-primary)">系统设置</h2>
      <p class="text-xs mt-0.5" style="color: var(--text-muted)">集中配置白名单准入、登录防爆锁定与系统运行参数</p>
    </div>

    <!-- 主面板 -->
    <div class="flex-1 min-h-0 flex flex-col">
      <n-tabs type="line" animated class="flex-1 flex flex-col min-h-0">
        <!-- 1. IP 白名单管理 -->
        <n-tab-pane name="whitelist" class="flex flex-col h-full min-h-0 pt-4">
          <template #tab>
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:shield-outline" class="w-4 h-4 shrink-0" />
              <span>IP 白名单</span>
            </div>
          </template>
          <div class="flex flex-col gap-4 flex-1 min-h-0">
            <!-- 头部操作与筛选 -->
            <div class="flex items-center justify-between shrink-0">
              <div class="flex items-center gap-3">
                <div class="relative max-w-xs shrink-0">
                  <Icon icon="material-symbols:search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--text-muted)" />
                  <input v-model="searchWhitelistIp" type="text" placeholder="搜索白名单 IP..."
                    class="w-64 h-[34px] pl-9 pr-3 rounded-lg text-sm outline-none transition-colors duration-200"
                    :style="{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
                    @keyup.enter="fetchWhitelist" />
                </div>
                <button @click="fetchWhitelist"
                  class="h-[34px] px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all active:scale-[0.98]">
                  <Icon icon="material-symbols:search" class="w-4 h-4" />查询
                </button>
              </div>
              <button @click="showAddWhitelistModal = true"
                class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/10 transition-all duration-200 active:scale-[0.98]">
                <Icon icon="material-symbols:add" class="w-4 h-4" />
                新增 IP
              </button>
            </div>

            <!-- 数据表格 -->
            <div class="flex-1 rounded-xl overflow-hidden flex flex-col min-h-0 border"
                 :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
              <div class="grid grid-cols-12 gap-4 px-5 py-3 border-b text-[11px] font-bold uppercase tracking-wider shrink-0"
                   :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-muted)' }">
                <span class="col-span-5">IP 地址</span>
                <span class="col-span-4">加入时间</span>
                <span class="col-span-3 text-right">操作</span>
              </div>

              <div class="flex-1 overflow-y-auto">
                <div v-if="loadingWhitelist" class="p-8 text-center text-sm" style="color: var(--text-muted)">加载中...</div>
                <div v-else-if="whitelistItems.length === 0" class="p-8 text-center text-sm" style="color: var(--text-muted)">暂无白名单数据</div>
                <div v-else
                  v-for="item in pagedWhitelist"
                  :key="item.ip"
                  class="grid grid-cols-12 gap-4 px-5 py-3.5 items-center transition-colors duration-150 border-b text-sm"
                  :style="{ borderColor: 'var(--border-color)' }"
                >
                  <div class="col-span-5 font-mono font-medium flex items-center gap-2" style="color: var(--text-primary)">
                    <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                    {{ item.ip }}
                  </div>
                  <div class="col-span-4 font-mono text-sm" style="color: var(--text-primary)">{{ item.created_at || '—' }}</div>
                  <div class="col-span-3 flex items-center justify-end gap-1.5">
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <button @click="openEditWhitelist(item.ip)"
                          class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border shrink-0"
                          :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                          <Icon icon="material-symbols:edit-outline" class="w-4 h-4" />
                        </button>
                      </template>
                      修改 IP
                    </n-tooltip>
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <button @click="handleDeleteWhitelist(item.ip)"
                          class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border border-red-500/20 bg-red-600/10 hover:bg-red-600/20 text-red-400 shrink-0">
                          <Icon icon="material-symbols:delete-outline" class="w-4 h-4" />
                        </button>
                      </template>
                      移除白名单
                    </n-tooltip>
                  </div>
                </div>
              </div>

              <!-- 分页条 -->
              <div v-if="whitelistItems.length > 0" class="flex items-center justify-between px-5 py-3 border-t shrink-0"
                   :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)' }">
                <span class="text-xs" style="color: var(--text-muted)">
                  共 {{ whitelistItems.length }} 条，第 {{ whitelistPage }} / {{ totalWhitelistPages }} 页
                </span>
                <div class="flex items-center gap-1">
                  <button @click="whitelistPage > 1 && (whitelistPage -= 1)" :disabled="whitelistPage === 1"
                    class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
                    :style="whitelistPage === 1 ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' } : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                    <Icon icon="material-symbols:chevron-left" class="w-4 h-4" />
                  </button>
                  <button @click="whitelistPage < totalWhitelistPages && (whitelistPage += 1)" :disabled="whitelistPage === totalWhitelistPages"
                    class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
                    :style="whitelistPage === totalWhitelistPages ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' } : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                    <Icon icon="material-symbols:chevron-right" class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 2. 用户账号锁定管理 -->
        <n-tab-pane name="user-lockouts" class="flex flex-col h-full min-h-0 pt-4">
          <template #tab>
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:person-off-outline" class="w-4 h-4 shrink-0" />
              <span>用户账号锁定</span>
            </div>
          </template>
          <div class="flex flex-col gap-4 flex-1 min-h-0">
            <!-- 筛选栏 -->
            <div class="flex items-center justify-between shrink-0">
              <div class="flex items-center gap-3">
                <div class="relative max-w-xs shrink-0">
                  <Icon icon="material-symbols:search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--text-muted)" />
                  <input v-model="searchUserLockoutName" type="text" placeholder="搜索用户名..."
                    class="w-48 h-[34px] pl-9 pr-3 rounded-lg text-sm outline-none transition-colors duration-200"
                    :style="{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
                    @keyup.enter="fetchUserLockouts" />
                </div>
                <n-select v-model:value="filterUserLockoutStatus" :options="lockoutStatusOptions"
                  placeholder="状态过滤" class="shrink-0" :style="{ width: '120px' }" />
                <button @click="fetchUserLockouts"
                  class="h-[34px] px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all active:scale-[0.98]">
                  <Icon icon="material-symbols:search" class="w-4 h-4" />查询
                </button>
              </div>
              <button @click="showAddUserLockoutModal = true"
                class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/10 transition-all duration-200 active:scale-[0.98]">
                <Icon icon="material-symbols:person-off-outline" class="w-4 h-4" />
                添加监控
              </button>
            </div>

            <!-- 数据列表 -->
            <div class="flex-1 rounded-xl overflow-hidden flex flex-col min-h-0 border"
                 :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
              <div class="grid grid-cols-12 gap-4 px-5 py-3 border-b text-[11px] font-bold uppercase tracking-wider shrink-0"
                   :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-muted)' }">
                <span class="col-span-3">用户名</span>
                <span class="col-span-2">失败次数</span>
                <span class="col-span-2">锁定次数</span>
                <span class="col-span-2">锁定状态</span>
                <span class="col-span-2">惩罚截止时间</span>
                <span class="col-span-1 text-right">操作</span>
              </div>

              <div class="flex-1 overflow-y-auto">
                <div v-if="loadingUserLockout" class="p-8 text-center text-sm" style="color: var(--text-muted)">加载中...</div>
                <div v-else-if="userLockoutItems.length === 0" class="p-8 text-center text-sm" style="color: var(--text-muted)">暂无锁定记录</div>
                <div v-else
                  v-for="item in pagedUserLockouts"
                  :key="item.username"
                  class="grid grid-cols-12 gap-4 px-5 py-3.5 items-center transition-colors duration-150 border-b text-sm"
                  :style="{ borderColor: 'var(--border-color)' }"
                >
                  <div class="col-span-3 font-semibold" style="color: var(--text-primary)">{{ item.username }}</div>
                  <div class="col-span-2 font-mono font-medium" style="color: var(--text-primary)">{{ item.fail_count }} / 5</div>
                  <div class="col-span-2 font-mono font-medium" style="color: var(--text-primary)">{{ item.lock_count }} / 3</div>
                  <div class="col-span-2">
                    <span class="flex items-center gap-1.5 text-sm">
                      <span v-if="item.is_locked" class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                      <span v-else class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span :class="item.is_locked ? 'text-red-400' : 'text-emerald-400'">
                        {{ item.is_permanent_lock ? '永久锁定' : (item.is_locked ? '临时惩罚中' : '正常') }}
                      </span>
                    </span>
                  </div>
                  <div class="col-span-2 font-mono text-sm" style="color: var(--text-primary)">{{ item.lock_time || '—' }}</div>
                  <div class="col-span-1 flex items-center justify-end gap-1.5">
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <button @click="openEditUserLockout(item)"
                          class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border shrink-0"
                          :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                          <Icon icon="material-symbols:edit-outline" class="w-4 h-4" />
                        </button>
                      </template>
                      编辑参数
                    </n-tooltip>
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <button @click="handleDeleteUserLockout(item.username)"
                          class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border border-emerald-500/20 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 shrink-0">
                          <Icon icon="material-symbols:lock-open-outline" class="w-4 h-4" />
                        </button>
                      </template>
                      解封并清除
                    </n-tooltip>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="userLockoutItems.length > 0" class="flex items-center justify-between px-5 py-3 border-t shrink-0"
                   :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)' }">
                <span class="text-xs" style="color: var(--text-muted)">
                  共 {{ userLockoutItems.length }} 条，第 {{ userLockoutPage }} / {{ totalUserLockoutPages }} 页
                </span>
                <div class="flex items-center gap-1">
                  <button @click="userLockoutPage > 1 && (userLockoutPage -= 1)" :disabled="userLockoutPage === 1"
                    class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
                    :style="userLockoutPage === 1 ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' } : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                    <Icon icon="material-symbols:chevron-left" class="w-4 h-4" />
                  </button>
                  <button @click="userLockoutPage < totalUserLockoutPages && (userLockoutPage += 1)" :disabled="userLockoutPage === totalUserLockoutPages"
                    class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
                    :style="userLockoutPage === totalUserLockoutPages ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' } : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                    <Icon icon="material-symbols:chevron-right" class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 3. IP 封禁锁定管理 -->
        <n-tab-pane name="ip-lockouts" class="flex flex-col h-full min-h-0 pt-4">
          <template #tab>
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:block-outline" class="w-4 h-4 shrink-0" />
              <span>IP 封禁锁定</span>
            </div>
          </template>
          <div class="flex flex-col gap-4 flex-1 min-h-0">
            <!-- 筛选栏 -->
            <div class="flex items-center justify-between shrink-0">
              <div class="flex items-center gap-3">
                <div class="relative max-w-xs shrink-0">
                  <Icon icon="material-symbols:search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--text-muted)" />
                  <input v-model="searchIpLockoutVal" type="text" placeholder="搜索 IP 地址..."
                    class="w-48 h-[34px] pl-9 pr-3 rounded-lg text-sm outline-none transition-colors duration-200"
                    :style="{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
                    @keyup.enter="fetchIpLockouts" />
                </div>
                <n-select v-model:value="filterIpLockoutStatus" :options="lockoutStatusOptions"
                  placeholder="状态过滤" class="shrink-0" :style="{ width: '120px' }" />
                <button @click="fetchIpLockouts"
                  class="h-[34px] px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all active:scale-[0.98]">
                  <Icon icon="material-symbols:search" class="w-4 h-4" />查询
                </button>
              </div>
              <button @click="showAddIpLockoutModal = true"
                class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 shadow-lg shadow-indigo-600/10 transition-all duration-200 active:scale-[0.98]">
                <Icon icon="material-symbols:gpp-bad-outline" class="w-4 h-4" />
                封禁新 IP
              </button>
            </div>

            <!-- 数据表格 -->
            <div class="flex-1 rounded-xl overflow-hidden flex flex-col min-h-0 border"
                 :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
              <div class="grid grid-cols-12 gap-4 px-5 py-3 border-b text-[11px] font-bold uppercase tracking-wider shrink-0"
                   :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-muted)' }">
                <span class="col-span-4">IP 地址</span>
                <span class="col-span-2">失败次数</span>
                <span class="col-span-3">封禁状态</span>
                <span class="col-span-2">临时封禁截止</span>
                <span class="col-span-1 text-right">操作</span>
              </div>

              <div class="flex-1 overflow-y-auto">
                <div v-if="loadingIpLockout" class="p-8 text-center text-sm" style="color: var(--text-muted)">加载中...</div>
                <div v-else-if="ipLockoutItems.length === 0" class="p-8 text-center text-sm" style="color: var(--text-muted)">暂无封禁记录</div>
                <div v-else
                  v-for="item in pagedIpLockouts"
                  :key="item.ip"
                  class="grid grid-cols-12 gap-4 px-5 py-3.5 items-center transition-colors duration-150 border-b text-sm"
                  :style="{ borderColor: 'var(--border-color)' }"
                >
                  <div class="col-span-4 font-mono font-medium" style="color: var(--text-primary)">{{ item.ip }}</div>
                  <div class="col-span-2 font-mono font-medium" style="color: var(--text-primary)">{{ item.fail_count }} / 10</div>
                  <div class="col-span-3">
                    <span class="flex items-center gap-1.5 text-sm">
                      <span v-if="item.is_locked" class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                      <span v-else class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                      <span :class="item.is_locked ? 'text-red-400' : 'text-emerald-400'">
                        {{ item.is_permanent_lock ? '永久封禁' : (item.is_locked ? '临时封禁中' : '正常') }}
                      </span>
                    </span>
                  </div>
                  <div class="col-span-2 font-mono text-sm" style="color: var(--text-primary)">{{ item.lock_time || '—' }}</div>
                  <div class="col-span-1 flex items-center justify-end gap-1.5">
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <button @click="openEditIpLockout(item)"
                          class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border shrink-0"
                          :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                          <Icon icon="material-symbols:edit-outline" class="w-4 h-4" />
                        </button>
                      </template>
                      编辑参数
                    </n-tooltip>
                    <n-tooltip trigger="hover" placement="top">
                      <template #trigger>
                        <button @click="handleDeleteIpLockout(item.ip)"
                          class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border border-emerald-500/20 bg-emerald-600/10 hover:bg-emerald-600/20 text-emerald-400 shrink-0">
                          <Icon icon="material-symbols:lock-open-outline" class="w-4 h-4" />
                        </button>
                      </template>
                      解封并清除
                    </n-tooltip>
                  </div>
                </div>
              </div>

              <!-- 分页 -->
              <div v-if="ipLockoutItems.length > 0" class="flex items-center justify-between px-5 py-3 border-t shrink-0"
                   :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)' }">
                <span class="text-xs" style="color: var(--text-muted)">
                  共 {{ ipLockoutItems.length }} 条，第 {{ ipLockoutPage }} / {{ totalIpLockoutPages }} 页
                </span>
                <div class="flex items-center gap-1">
                  <button @click="ipLockoutPage > 1 && (ipLockoutPage -= 1)" :disabled="ipLockoutPage === 1"
                    class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
                    :style="ipLockoutPage === 1 ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' } : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                    <Icon icon="material-symbols:chevron-left" class="w-4 h-4" />
                  </button>
                  <button @click="ipLockoutPage < totalIpLockoutPages && (ipLockoutPage += 1)" :disabled="ipLockoutPage === totalIpLockoutPages"
                    class="w-7 h-7 rounded flex items-center justify-center text-xs transition-colors border"
                    :style="ipLockoutPage === totalIpLockoutPages ? { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-muted)', cursor: 'not-allowed' } : { background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                    <Icon icon="material-symbols:chevron-right" class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </n-tab-pane>

        <!-- 4. 系统运行参数与信息 -->
        <n-tab-pane name="system" class="pt-4">
          <template #tab>
            <div class="flex items-center gap-2">
              <Icon icon="material-symbols:info-outline" class="w-4 h-4 shrink-0" />
              <span>系统信息</span>
            </div>
          </template>
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 运行配置 -->
            <div class="rounded-xl p-5 flex flex-col gap-4 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-sm font-bold" style="color: var(--text-primary)">运行配置参数</h3>
                  <p class="text-xs mt-0.5" style="color: var(--text-muted)">以下参数为当前后端加载值，修改请编辑 config.yml</p>
                </div>
                <Icon icon="material-symbols:tune" class="w-6 h-6 text-indigo-400" />
              </div>
              <div class="space-y-4">
                <div class="space-y-1.5">
                  <label class="text-xs font-semibold" style="color: var(--text-secondary)">最大上传文件大小 (MB)</label>
                  <input :value="maxUploadSize" disabled class="w-full h-10 px-3 rounded-lg text-sm cursor-not-allowed outline-none"
                    :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-xs font-semibold" style="color: var(--text-secondary)">历史记录保留天数</label>
                  <input :value="historyRetentionDays" disabled class="w-full h-10 px-3 rounded-lg text-sm cursor-not-allowed outline-none"
                    :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-xs font-semibold" style="color: var(--text-secondary)">最大并发工作线程数</label>
                  <input :value="maxWorkers" disabled class="w-full h-10 px-3 rounded-lg text-sm cursor-not-allowed outline-none"
                    :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }" />
                </div>
              </div>
              <!-- <div class="pt-1">
                <button @click="saveConfig" class="h-9 px-4 rounded-lg text-xs transition-all duration-200 border"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                  <Icon icon="material-symbols:info-outline" class="w-4 h-4 inline mr-1.5" />
                  修改提示
                </button>
              </div> -->
            </div>

            <!-- 关于系统 -->
            <div class="rounded-xl p-5 border flex flex-col gap-4" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
              <h3 class="text-sm font-bold" style="color: var(--text-primary)">关于 SQL Convert</h3>
              <div class="space-y-4 text-xs">
                <div class="p-3.5 rounded-lg border flex flex-col gap-2" :style="{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }">
                  <div class="flex justify-between">
                    <span style="color: var(--text-muted)">版本号</span>
                    <span class="font-mono font-semibold" style="color: var(--text-primary)">v2.0.0</span>
                  </div>
                  <div class="flex justify-between">
                    <span style="color: var(--text-muted)">后端服务</span>
                    <span class="font-mono font-semibold" style="color: var(--text-primary)">FastAPI + Uvicorn</span>
                  </div>
                  <div class="flex justify-between">
                    <span style="color: var(--text-muted)">前端框架</span>
                    <span class="font-mono font-semibold" style="color: var(--text-primary)">Vue 3 + Vite + Naive UI</span>
                  </div>
                  <div class="flex justify-between">
                    <span style="color: var(--text-muted)">数据库</span>
                    <span class="font-mono font-semibold" style="color: var(--text-primary)">SQLite (国密 SM3)</span>
                  </div>
                </div>
                <p style="color: var(--text-muted)" class="leading-relaxed">
                  本系统专注大容量 SQL 备份文件（GB级）跨库流式高性能转换。内置账号多次尝试锁定、安全审计与 IP 动态防入侵拦截等安全能力。
                </p>
              </div>
            </div>
          </div>
        </n-tab-pane>
      </n-tabs>
    </div>

    <!-- ── 模态框组 ── -->

    <!-- Tab 1: 新增白名单 -->
    <n-modal v-model:show="showAddWhitelistModal">
      <n-card title="新增 IP 白名单" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">IP 地址</label>
            <input v-model="formWhitelistIp" type="text" placeholder="输入 IP 地址 (如 192.168.1.100)"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button @click="showAddWhitelistModal = false" class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">取消</button>
            <button @click="handleAddWhitelist" class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]">确认添加</button>
          </div>
        </div>
      </n-card>
    </n-modal>

    <!-- Tab 1: 修改白名单 -->
    <n-modal v-model:show="showEditWhitelistModal">
      <n-card title="修改 IP 白名单" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">旧 IP 地址</label>
            <input :value="oldWhitelistIp" disabled class="w-full h-10 px-3 rounded-lg text-sm cursor-not-allowed outline-none"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }" />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">新 IP 地址</label>
            <input v-model="formWhitelistIp" type="text" placeholder="输入新 IP 地址"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button @click="showEditWhitelistModal = false" class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">取消</button>
            <button @click="handleEditWhitelist" class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]">保存修改</button>
          </div>
        </div>
      </n-card>
    </n-modal>

    <!-- Tab 2: 新增用户锁定监控 -->
    <n-modal v-model:show="showAddUserLockoutModal">
      <n-card title="添加账号登录锁定监控" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">被监控账号用户名</label>
            <input v-model="formLockUsername" type="text" placeholder="输入已存在的用户名"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">失败尝试次数</label>
              <input v-model.number="formLockFailCount" type="number" min="0" max="5" class="w-full h-10 px-3 rounded-lg text-sm outline-none"
                :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">累计锁定次数</label>
              <input v-model.number="formLockCount" type="number" min="0" max="3" class="w-full h-10 px-3 rounded-lg text-sm outline-none"
                :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
            </div>
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">永久锁定状态</label>
            <n-select v-model:value="formLockIsPermanent" :options="userRoleOptions" />
          </div>
          <div v-if="formLockIsPermanent !== 1" class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">锁惩期限截止时间 (可选)</label>
            <input v-model="formLockTime" type="text" placeholder="格式如: 2026-07-15 12:00:00"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button @click="showAddUserLockoutModal = false" class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">取消</button>
            <button @click="handleCreateUserLockout" class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]">确认创建</button>
          </div>
        </div>
      </n-card>
    </n-modal>

    <!-- Tab 2: 编辑用户锁定监控 -->
    <n-modal v-model:show="showEditUserLockoutModal">
      <n-card title="编辑账号锁定属性" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">用户名</label>
            <input :value="editingLockUser" disabled class="w-full h-10 px-3 rounded-lg text-sm cursor-not-allowed outline-none"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }" />
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">失败尝试次数 (上限5次)</label>
              <input v-model.number="formLockFailCount" type="number" min="0" max="5" class="w-full h-10 px-3 rounded-lg text-sm outline-none"
                :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">累计锁定次数 (上限3次)</label>
              <input v-model.number="formLockCount" type="number" min="0" max="3" class="w-full h-10 px-3 rounded-lg text-sm outline-none"
                :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
            </div>
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">永久锁定状态</label>
            <n-select v-model:value="formLockIsPermanent" :options="userRoleOptions" />
          </div>
          <div v-if="formLockIsPermanent !== 1" class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">锁惩截止时间</label>
            <input v-model="formLockTime" type="text" placeholder="YYYY-MM-DD HH:MM:SS"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button @click="showEditUserLockoutModal = false" class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">取消</button>
            <button @click="handleEditUserLockout" class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]">保存修改</button>
          </div>
        </div>
      </n-card>
    </n-modal>

    <!-- Tab 3: 新增 IP 封禁记录 -->
    <n-modal v-model:show="showAddIpLockoutModal">
      <n-card title="添加 IP 封禁锁定记录" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">封禁 IP 地址</label>
            <input v-model="formLockIpVal" type="text" placeholder="输入 IP 地址"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">失败尝试次数 (上限10次)</label>
            <input v-model.number="formLockIpFailCount" type="number" min="0" max="10" class="w-full h-10 px-3 rounded-lg text-sm outline-none"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">永久封禁状态</label>
            <n-select v-model:value="formLockIpIsPermanent" :options="userRoleOptions" />
          </div>
          <div v-if="formLockIpIsPermanent !== 1" class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">临时锁定截止时间 (可选)</label>
            <input v-model="formLockIpTime" type="text" placeholder="如: 2026-07-15 12:00:00"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button @click="showAddIpLockoutModal = false" class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">取消</button>
            <button @click="handleCreateIpLockout" class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]">确认创建</button>
          </div>
        </div>
      </n-card>
    </n-modal>

    <!-- Tab 3: 编辑 IP 封禁记录 -->
    <n-modal v-model:show="showEditIpLockoutModal">
      <n-card title="编辑 IP 封禁参数" :bordered="false" size="medium" role="dialog" aria-modal="true" class="glass-panel max-w-[420px]">
        <div class="space-y-4">
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">IP 地址</label>
            <input :value="editingLockIpVal" disabled class="w-full h-10 px-3 rounded-lg text-sm cursor-not-allowed outline-none"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }" />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">失败尝试次数 (上限10次)</label>
            <input v-model.number="formLockIpFailCount" type="number" min="0" max="10" class="w-full h-10 px-3 rounded-lg text-sm outline-none"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">永久封禁状态</label>
            <n-select v-model:value="formLockIpIsPermanent" :options="userRoleOptions" />
          </div>
          <div v-if="formLockIpIsPermanent !== 1" class="space-y-1.5">
            <label class="text-xs font-semibold" style="color: var(--text-secondary)">临时锁定截止时间</label>
            <input v-model="formLockIpTime" type="text" placeholder="YYYY-MM-DD HH:MM:SS"
              class="w-full h-10 px-3 rounded-lg text-sm outline-none transition-colors"
              :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
          </div>
          <div class="flex justify-end gap-2 pt-2">
            <button @click="showEditIpLockoutModal = false" class="h-9 px-4 rounded-lg text-xs transition-colors border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">取消</button>
            <button @click="handleEditIpLockout" class="h-9 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all active:scale-[0.98]">保存修改</button>
          </div>
        </div>
      </n-card>
    </n-modal>
  </div>
</template>

<style scoped>
:deep(.n-tabs) {
  display: flex;
  flex-direction: column;
}

:deep(.n-tabs-pane-wrapper) {
  flex: 1;
  min-height: 0;
}
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
}

:deep(.n-base-selection-placeholder) {
  color: var(--text-muted) !important;
  line-height: 34px !important;
}

:deep(.n-base-selection-label) {
  line-height: 34px !important;
  color: var(--text-primary) !important;
}
</style>
