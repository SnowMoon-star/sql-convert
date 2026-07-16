<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useMessage, NTag, NSelect, NTooltip, NModal, NCard, NDatePicker } from 'naive-ui';
import { Icon } from '@iconify/vue';
import request from '../../utils/request';

const message = useMessage();

const tasks = ref<any[]>([]);
const loading = ref(false);
const searchQuery = ref('');
const statusFilter = ref<string>('');

// 分页状态
const page = ref(1);
const pageSize = ref(10);
const total = ref(0);

// 详情弹窗状态
const showDetail = ref(false);
const detailTask = ref<any>(null);
const detailLoading = ref(false);

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '成功', value: 'SUCCESS' },
  { label: '失败', value: 'FAILED' },
  { label: '进行中', value: 'RUNNING' },
  { label: '等待中', value: 'PENDING' },
];

// 时间范围
const dateTimeRange = ref<[number, number] | null>(null);

const convertLocalToUtc8Str = (ts: number): string => {
  const d = new Date(ts);
  const utcMs = ts + d.getTimezoneOffset() * 60000;
  const utc8Ms = utcMs + 8 * 3600000;
  const d8 = new Date(utc8Ms);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d8.getFullYear()}-${pad(d8.getMonth() + 1)}-${pad(d8.getDate())} ${pad(d8.getHours())}:${pad(d8.getMinutes())}:${pad(d8.getSeconds())}`;
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

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));

const fetchTasks = async () => {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize.value };
    if (searchQuery.value) params.filename = searchQuery.value;
    if (statusFilter.value) params.status = statusFilter.value;
    if (dateTimeRange.value) {
      params.date_from = convertLocalToUtc8Str(dateTimeRange.value[0]);
      params.date_to = convertLocalToUtc8Str(dateTimeRange.value[1]);
    }
    const res: any = await request.get('/api/tasks', { params });
    tasks.value = Array.isArray(res.data) ? res.data : [];
    total.value = res.total || 0;
  } catch (error: any) {
    message.error('获取历史记录失败');
  } finally {
    loading.value = false;
  }
};

// 仅通过查询/重置按钮触发 API
const handleSearch = () => {
  page.value = 1;
  fetchTasks();
};

const handleReset = () => {
  page.value = 1;
  searchQuery.value = '';
  statusFilter.value = '';
  dateTimeRange.value = null;
  fetchTasks();
};

const goPage = (p: number) => {
  if (p < 1 || p > totalPages.value) return;
  page.value = p;
  fetchTasks();
};

const handleViewReport = (taskId: string) => {
  window.open(`/api/report/${taskId}`, '_blank');
};

const handleDownload = (taskId: string) => {
  const a = document.createElement('a');
  a.href = `/api/download/${taskId}`;
  a.download = '';
  a.click();
};

const handleViewDetail = async (task: any) => {
  showDetail.value = true;
  detailLoading.value = true;
  try {
    const res: any = await request.get(`/api/tasks/${task.task_id}`);
    detailTask.value = res;
  } catch {
    detailTask.value = null;
  } finally {
    detailLoading.value = false;
  }
};

const formatTime = (t: string | null | undefined) => {
  if (!t) return '—';
  const localStr = convertUtc8ToLocalStr(t);
  return localStr.substring(0, 16);
};

const formatTimeFull = (t: string | null | undefined) => {
  if (!t) return '—';
  return convertUtc8ToLocalStr(t);
};

onMounted(() => {
  fetchTasks();
});
</script>

<template>
  <div class="flex flex-col gap-5 h-full">
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h2 class="text-lg font-bold" style="color: var(--text-primary)">转换历史</h2>
        <p class="text-xs mt-0.5" style="color: var(--text-muted)">查看所有 SQL 转换任务的历史记录与成果</p>
      </div>
    </div>

    <!-- 搜索与筛选栏 — 仅收集输入，查询/重置才调 API -->
    <div class="flex items-center gap-3 shrink-0">
      <div class="relative flex-1 max-w-xs">
        <Icon icon="material-symbols:search" class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4" style="color: var(--text-muted)" />
        <input v-model="searchQuery" type="text" placeholder="搜索文件名或任务ID..."
          class="w-full h-[34px] pl-9 pr-3 rounded-lg text-sm outline-none transition-colors duration-200"
          :style="{ background: 'var(--bg-secondary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }" />
      </div>
      <n-select v-model:value="statusFilter" :options="statusOptions" placeholder="全部状态" clearable
        class="!w-[130px]" />
      <n-date-picker v-model:value="dateTimeRange" type="datetimerange" clearable placeholder="选择时间范围"
        class="!w-[280px]" />
      <button @click="handleSearch"
        class="h-[34px] px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all active:scale-[0.98]">
        <Icon icon="material-symbols:search" class="w-4 h-4" />查询
      </button>
      <button @click="handleReset"
        class="h-[34px] px-5 rounded-lg text-xs flex items-center gap-2 transition-all duration-200 border"
        :style="{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
        <Icon icon="material-symbols:refresh" class="w-4 h-4" />重置
      </button>
    </div>

    <!-- 表格 -->
    <div class="flex-1 rounded-xl overflow-hidden flex flex-col min-h-0 border"
      :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)' }">
      <div class="flex items-center justify-between px-5 py-3 border-b text-[11px] font-bold uppercase tracking-wider shrink-0"
        :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-muted)' }">
        <span class="w-[90px] shrink-0 text-left">任务 ID</span>
        <span class="w-[180px] shrink-0 text-center">文件名</span>
        <span class="w-[90px] shrink-0 text-center">原始方言</span>
        <span class="w-[90px] shrink-0 text-center">目标方言</span>
        <span class="w-[105px] shrink-0 text-center">转换类型</span>
        <span class="w-[80px] shrink-0 text-center">状态</span>
        <span class="w-[80px] shrink-0 text-center">耗时</span>
        <span class="w-[140px] shrink-0 text-center">创建时间</span>
        <span class="w-[140px] shrink-0 text-center">完成时间</span>
        <span class="w-[95px] shrink-0 text-right">操作</span>
      </div>
      <div class="flex-1 overflow-y-auto">
        <div v-if="loading" class="p-8 text-center text-sm" style="color: var(--text-muted)">加载中...</div>
        <div v-else-if="tasks.length === 0" class="p-8 text-center text-sm" style="color: var(--text-muted)">暂无历史转换记录</div>
        <div v-for="task in tasks" :key="task.task_id"
          class="flex items-center justify-between px-5 py-3.5 transition-colors duration-150 border-b text-sm"
          :style="{ borderColor: 'var(--border-color)' }">
          
          <div class="w-[90px] shrink-0 font-mono text-sm truncate text-left" style="color: var(--text-primary)" :title="'ID: ' + task.task_id">
            {{ task.task_id.substring(0, 8) }}
          </div>
          
          <div class="w-[180px] shrink-0 text-sm font-medium truncate text-center" style="color: var(--text-primary)" :title="task.filename">
            {{ task.filename }}
          </div>
          
          <div class="w-[90px] shrink-0 font-mono text-sm text-center" style="color: var(--text-primary)">
            {{ task.source_mode }}
          </div>
          
          <div class="w-[90px] shrink-0 font-mono text-sm text-center" style="color: var(--text-primary)">
            {{ task.target_mode }}
          </div>
          
          <div class="w-[105px] shrink-0 text-sm flex items-center justify-center gap-1" style="color: var(--text-primary)">
            <span v-if="task.convert_type === 'online'" class="flex items-center gap-1">
              <Icon icon="material-symbols:edit-note" class="w-4 h-4 text-indigo-400 shrink-0" />
              线上转换
            </span>
            <span v-else class="flex items-center gap-1">
              <Icon icon="material-symbols:cloud-upload" class="w-4 h-4 text-emerald-400 shrink-0" />
              文件解析
            </span>
          </div>
          
          <div class="w-[80px] shrink-0 flex justify-center">
            <n-tag size="small" :type="task.status === 'SUCCESS' ? 'success' : task.status === 'FAILED' ? 'error' : task.status === 'RUNNING' ? 'warning' : 'default'" round>
              <span class="text-[10px] font-semibold">{{ task.status }}</span>
            </n-tag>
          </div>
          
          <div class="w-[80px] shrink-0 font-mono text-sm text-center" style="color: var(--text-primary)">
            {{ task.duration !== undefined ? task.duration + ' ms' : '—' }}
          </div>
          
          <div class="w-[140px] shrink-0 font-mono text-sm text-center" style="color: var(--text-primary)">
            {{ formatTime(task.created_at) }}
          </div>
          
          <div class="w-[140px] shrink-0 font-mono text-sm text-center" style="color: var(--text-primary)">
            {{ task.completed_at ? formatTime(task.completed_at) : '—' }}
          </div>
          
          <div class="w-[95px] shrink-0 flex items-center justify-end gap-1">
            <n-tooltip trigger="hover" placement="top">
              <template #trigger>
                <button @click="handleViewDetail(task)" class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                  <Icon icon="material-symbols:info" class="w-4 h-4 shrink-0" />
                </button>
              </template>查看详情
            </n-tooltip>
            <n-tooltip v-if="task.status === 'SUCCESS'" trigger="hover" placement="top">
              <template #trigger>
                <button @click="handleViewReport(task.task_id)" class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                  <Icon icon="material-symbols:article" class="w-4 h-4 shrink-0" />
                </button>
              </template>查看报告
            </n-tooltip>
            <n-tooltip v-if="task.status === 'SUCCESS'" trigger="hover" placement="top">
              <template #trigger>
                <button @click="handleDownload(task.task_id)" class="w-7 h-7 rounded flex items-center justify-center transition-all duration-200 border"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
                  <Icon icon="material-symbols:download" class="w-4 h-4 shrink-0" />
                </button>
              </template>下载 SQL
            </n-tooltip>
          </div>
        </div>
      </div>
      <div class="flex items-center justify-between px-5 py-2.5 border-t shrink-0"
        :style="{ borderColor: 'var(--border-color)', background: 'var(--bg-hover)' }">
        <span class="text-xs" style="color: var(--text-muted)">第 {{ page }} / {{ totalPages }} 页，共 {{ total }} 条</span>
        <div class="flex items-center gap-1">
          <button :disabled="page <= 1" @click="goPage(page - 1)"
            class="h-7 w-7 rounded text-xs flex items-center justify-center transition-colors border disabled:opacity-30 disabled:cursor-not-allowed"
            :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
            <Icon icon="material-symbols:chevron-left" class="w-4 h-4" />
          </button>
          <template v-for="p in totalPages" :key="p">
            <button v-if="p === 1 || p === totalPages || Math.abs(p - page) <= 1" @click="goPage(p)"
              class="h-7 min-w-[28px] px-1 rounded text-xs font-medium transition-all duration-200 border"
              :style="p === page
                ? { background: '#6366f1', borderColor: '#6366f1', color: '#ffffff' }
                : { background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">{{ p }}</button>
            <span v-else-if="p === page - 2 || p === page + 2" class="text-xs px-1 select-none" style="color: var(--text-muted)">...</span>
          </template>
          <button :disabled="page >= totalPages" @click="goPage(page + 1)"
            class="h-7 w-7 rounded text-xs flex items-center justify-center transition-colors border disabled:opacity-30 disabled:cursor-not-allowed"
            :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
            <Icon icon="material-symbols:chevron-right" class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- 任务详情弹窗 -->
    <n-modal v-model:show="showDetail" transform-origin="center" :mask-closable="true">
      <n-card title="" :bordered="false" size="medium" role="dialog" aria-modal="true"
        style="max-width: 640px; width: 90vw;" class="glass-panel">
        <div class="flex items-center gap-3 mb-4">
          <button @click="showDetail = false"
            class="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 border shrink-0"
            :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
            <Icon icon="material-symbols:arrow-back" class="w-4 h-4" />
          </button>
          <div class="min-w-0 flex-1"><h3 class="text-base font-bold truncate" style="color: var(--text-primary)">任务详情</h3></div>
        </div>
        <div v-if="detailLoading" class="flex items-center justify-center py-16 text-sm" style="color: var(--text-muted)">
          <Icon icon="line-md:loading-twotone-loop" class="w-5 h-5 mr-2" />加载中...
        </div>
        <template v-else-if="detailTask">
          <div class="flex items-start justify-between mb-4">
            <div class="min-w-0 flex-1">
              <p class="text-sm font-bold truncate" style="color: var(--text-primary)">{{ detailTask.filename }}</p>
              <p class="text-xs font-mono mt-1" style="color: var(--text-muted)">{{ detailTask.task_id }}</p>
            </div>
            <span class="shrink-0 ml-3 px-2.5 py-0.5 rounded-full text-[11px] font-bold border"
              :style="{
                background: detailTask.status === 'SUCCESS' ? 'rgba(16,185,129,0.15)' : detailTask.status === 'FAILED' ? 'rgba(239,68,68,0.15)' : detailTask.status === 'RUNNING' ? 'rgba(245,158,11,0.15)' : 'var(--bg-hover)',
                color: detailTask.status === 'SUCCESS' ? '#10b981' : detailTask.status === 'FAILED' ? '#ef4444' : detailTask.status === 'RUNNING' ? '#f59e0b' : 'var(--text-secondary)',
                borderColor: detailTask.status === 'SUCCESS' ? 'rgba(16,185,129,0.3)' : detailTask.status === 'FAILED' ? 'rgba(239,68,68,0.3)' : detailTask.status === 'RUNNING' ? 'rgba(245,158,11,0.3)' : 'var(--border-color)'
              }">{{ detailTask.status }}</span>
          </div>
          <div class="grid grid-cols-2 gap-4 mb-4 text-sm">
            <div><p class="text-xs" style="color: var(--text-muted)">源方言</p><p class="font-semibold mt-0.5" style="color: var(--text-primary)">{{ detailTask.source_mode }}</p></div>
            <div><p class="text-xs" style="color: var(--text-muted)">目标方言</p><p class="font-semibold mt-0.5" style="color: var(--text-primary)">{{ detailTask.target_mode }}</p></div>
            <div><p class="text-xs" style="color: var(--text-muted)">转换类型</p><p class="font-semibold mt-0.5" style="color: var(--text-primary)">{{ detailTask.convert_type === 'online' ? '线上编辑转换' : '本地文件解析' }}</p></div>
            <div><p class="text-xs" style="color: var(--text-muted)">执行耗时</p><p class="font-semibold mt-0.5" style="color: var(--text-primary)">{{ detailTask.duration !== undefined ? detailTask.duration + ' ms' : '—' }}</p></div>
            <div><p class="text-xs" style="color: var(--text-muted)">创建时间</p><p class="font-mono text-xs mt-0.5" style="color: var(--text-primary)">{{ formatTimeFull(detailTask.created_at) }}</p></div>
            <div><p class="text-xs" style="color: var(--text-muted)">完成时间</p><p class="font-mono text-xs mt-0.5" style="color: var(--text-primary)">{{ detailTask.completed_at ? formatTimeFull(detailTask.completed_at) : '—' }}</p></div>
          </div>
          <div v-if="detailTask.progress" class="border-t pt-4" :style="{ borderColor: 'var(--border-color)' }">
            <p class="text-xs font-semibold mb-3" style="color: var(--text-secondary)">转换进度</p>
            <div class="grid grid-cols-3 gap-3">
              <template v-for="(val, key) in (detailTask.progress as Record<string, any>)" :key="key">
                <div v-if="key !== 'status'"
                  class="flex flex-col items-center py-2.5 px-2 rounded-lg border text-center"
                  :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)' }">
                  <span class="text-base font-bold" style="color: var(--text-primary)">{{ val ?? '—' }}</span>
                  <span class="text-[10px] mt-0.5" style="color: var(--text-muted)">{{ key }}</span>
                </div>
              </template>
            </div>
          </div>
          <div v-if="detailTask.error" class="mt-4 p-3 rounded-lg border" :style="{ background: 'rgba(239,68,68,0.05)', borderColor: 'rgba(239,68,68,0.2)' }">
            <div class="flex items-center gap-1.5 mb-1.5"><Icon icon="material-symbols:error" class="w-4 h-4 text-red-500 shrink-0" /><span class="text-xs font-bold text-red-500">错误</span></div>
            <pre class="text-xs whitespace-pre-wrap font-mono leading-relaxed text-red-400">{{ detailTask.error }}</pre>
          </div>
          <div v-if="detailTask.status === 'SUCCESS'" class="flex gap-2 mt-4 pt-4 border-t" :style="{ borderColor: 'var(--border-color)' }">
            <button @click="handleViewReport(detailTask.task_id)" class="h-9 px-4 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all duration-200 border"
              :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }">
              <Icon icon="material-symbols:article" class="w-4 h-4 shrink-0" />查看报告
            </button>
            <button @click="handleDownload(detailTask.task_id)" class="h-9 px-4 rounded-lg text-xs font-semibold flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-500 text-white transition-all duration-200">
              <Icon icon="material-symbols:download" class="w-4 h-4 shrink-0" />下载 SQL
            </button>
          </div>
        </template>
        <div v-else class="flex flex-col items-center justify-center py-16 text-sm" style="color: var(--text-muted)">
          <Icon icon="material-symbols:search-off" class="w-10 h-10 mb-2" style="color: var(--text-muted)" /><p>任务不存在或已被删除</p>
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

:deep(.n-date-picker-range-input) {
  color: var(--text-primary) !important;
}
</style>
