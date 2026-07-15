<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { Icon } from '@iconify/vue';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import VChart from 'vue-echarts';
import { useThemeStore } from '../../store/theme';
import request from '../../utils/request';

// 注册 ECharts 组件
use([CanvasRenderer, LineChart, GridComponent, TooltipComponent, LegendComponent]);

// ── 数据状态 ──
const stats = ref<any>({ tasks: {}, resources: {} });
const history = ref<any[]>([]);
const loading = ref(true);
let timer: ReturnType<typeof setInterval> | null = null;

// ── 统计数据获取 ──
const fetchStats = async () => {
  try {
    const [s, h]: [any, any] = await Promise.all([
      request.get('/api/stats'),
      request.get('/api/stats/history')
    ]);
    stats.value = s || { tasks: {}, resources: {} };
    history.value = h?.history || [];
  } catch {
    // 静默
  } finally {
    loading.value = false;
  }
};

// ── 方言分布排行榜 ──
const dialectRanking = computed(() => {
  const dist = stats.value.tasks?.dialect_distribution || {};
  const entries = Object.entries(dist).map(([name, count]) => ({ name, count: count as number }));
  entries.sort((a, b) => b.count - a.count);
  return entries;
});

const totalTasks = computed(() => stats.value.tasks?.total ?? 0);
const successTasks = computed(() => stats.value.tasks?.success ?? 0);
const failedTasks = computed(() => stats.value.tasks?.failed ?? 0);
const successRate = computed(() => {
  if (!totalTasks.value) return 0;
  return ((successTasks.value / totalTasks.value) * 100).toFixed(1);
});

// ── 折线图配置 ──
const themeStore = useThemeStore();

const chartOption = computed(() => {
  const isDark = themeStore.isDark;
  const textColor = isDark ? '#94a3b8' : '#475569';
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';

  const times = history.value.map((h: any) => {
    const d = new Date(h.time);
    return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  });

  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: isDark ? '#1a2230' : '#ffffff',
      borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
      textStyle: { color: textColor, fontSize: 12 },
    },
    legend: {
      data: ['CPU', '内存', '磁盘'],
      textStyle: { color: textColor, fontSize: 12 },
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '18%',
      top: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: times,
      axisLine: { lineStyle: { color: gridColor } },
      axisLabel: { color: textColor, fontSize: 11 },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { color: textColor, fontSize: 11, formatter: '{value}%' },
      splitLine: { lineStyle: { color: gridColor } },
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(99, 102, 241, 0.3)' },
              { offset: 1, color: 'rgba(99, 102, 241, 0.02)' },
            ],
          },
        },
        itemStyle: { color: '#6366f1' },
        data: history.value.map((h: any) => h.cpu),
      },
      {
        name: '内存',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245, 158, 11, 0.25)' },
              { offset: 1, color: 'rgba(245, 158, 11, 0.02)' },
            ],
          },
        },
        itemStyle: { color: '#f59e0b' },
        data: history.value.map((h: any) => h.memory),
      },
      {
        name: '磁盘',
        type: 'line',
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16, 185, 129, 0.25)' },
              { offset: 1, color: 'rgba(16, 185, 129, 0.02)' },
            ],
          },
        },
        itemStyle: { color: '#10b981' },
        data: history.value.map((h: any) => h.disk),
      },
    ],
  };
});

// ── 生命周期 ──
onMounted(() => {
  fetchStats();
  timer = setInterval(fetchStats, 30000);
});

onUnmounted(() => {
  if (timer) clearInterval(timer);
});
</script>

<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div>
      <h2 class="text-xl font-bold" style="color: var(--text-primary)">仪表盘</h2>
      <p class="text-sm mt-0.5" style="color: var(--text-muted)">系统概览与资源监控</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="rounded-xl p-5 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted)">总任务</p>
            <p class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ totalTasks }}</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center shrink-0">
            <Icon icon="material-symbols:transform" class="w-5 h-5 text-indigo-500" />
          </div>
        </div>
      </div>

      <div class="rounded-xl p-5 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted)">成功</p>
            <p class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ successTasks }}</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
            <Icon icon="material-symbols:check-circle-outline" class="w-5 h-5 text-emerald-500" />
          </div>
        </div>
      </div>

      <div class="rounded-xl p-5 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted)">失败</p>
            <p class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ failedTasks }}</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center shrink-0">
            <Icon icon="material-symbols:error-outline" class="w-5 h-5 text-red-500" />
          </div>
        </div>
      </div>

      <div class="rounded-xl p-5 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs font-medium uppercase tracking-wider" style="color: var(--text-muted)">成功率</p>
            <p class="text-2xl font-bold mt-1" style="color: var(--text-primary)">{{ successRate }}%</p>
          </div>
          <div class="w-11 h-11 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center shrink-0">
            <Icon icon="material-symbols:trending-up" class="w-5 h-5 text-amber-500" />
          </div>
        </div>
      </div>
    </div>

    <!-- 折线图 + 排行榜 -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- 折线图 -->
      <div class="lg:col-span-2 rounded-xl p-5 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
        <h3 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">服务器资源监控</h3>
        <div v-if="history.length === 0" class="flex items-center justify-center h-[300px] text-sm" style="color: var(--text-muted)">
          正在采集数据…
        </div>
        <VChart v-else :option="chartOption" autoresize style="width: 100%; height: 300px" />
      </div>

      <!-- 转换目标排行榜 -->
      <div class="rounded-xl p-5 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
        <h3 class="text-sm font-semibold mb-4" style="color: var(--text-primary)">转换目标排行榜</h3>
        <div v-if="dialectRanking.length === 0" class="flex items-center justify-center h-[300px] text-sm" style="color: var(--text-muted)">
          暂无数据
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(item, index) in dialectRanking"
            :key="item.name"
            class="flex items-center gap-3 py-2.5 px-3 rounded-lg"
            :style="{ background: index % 2 === 0 ? 'var(--bg-hover)' : 'transparent' }"
          >
            <!-- 排行序号 -->
            <div
              class="w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shrink-0"
              :class="{
                'bg-amber-500/20 text-amber-500': index === 0,
                'bg-slate-500/20 text-slate-400': index >= 1
              }"
            >
              {{ index + 1 }}
            </div>

            <!-- 方言名 -->
            <span class="text-sm font-medium flex-1" style="color: var(--text-primary)">
              {{ item.name }}
            </span>

            <!-- 数量 -->
            <div class="flex items-center gap-2">
              <div class="h-1.5 rounded-full bg-indigo-500/20 overflow-hidden w-16">
                <div
                  class="h-full rounded-full bg-indigo-500 transition-all duration-500"
                  :style="{ width: (item.count / (dialectRanking[0]?.count || 1)) * 100 + '%' }"
                />
              </div>
              <span class="text-xs font-semibold tabular-nums" style="color: var(--text-secondary)">
                {{ item.count }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
