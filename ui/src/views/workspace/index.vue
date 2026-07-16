<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import { useMessage, NUpload } from 'naive-ui';
import { Icon } from '@iconify/vue';
import request from '../../utils/request';
import MonacoEditor from '../../components/MonacoEditor.vue';
import { useAuthStore } from '../../store/auth';

const message = useMessage();
const authStore = useAuthStore();

// SQL 语句校验
const validateSql = (sql: string): string | null => {
  const trimmed = sql.trim();
  if (!trimmed) return 'SQL 内容不能为空。';

  // 检查是否包含 SQL 关键字
  if (!/\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|TRUNCATE)\b/i.test(trimmed)) {
    return '输入内容不是有效的 SQL 语句，请检查后重试。';
  }

  // 提取 CREATE TABLE 中定义的表名（忽略 IF NOT EXISTS 和 schema 前缀）
  const createTableRegex = /CREATE\s+(?:TEMPORARY\s+)?TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:`?\w+`?\.)?`?(\w+)`?/gi;
  const createdTables = new Set<string>();
  let match;
  while ((match = createTableRegex.exec(trimmed)) !== null) {
    createdTables.add(match[1].toLowerCase());
  }

  // 如果有 CREATE TABLE，视为有表结构
  if (createdTables.size > 0) return null;

  // 没有 CREATE TABLE，检查是否有 DML 操作
  const hasDml = /\bINSERT\s+(?:IGNORE\s+)?INTO\b|\bUPDATE\b|\bDELETE\s+FROM\b/i.test(trimmed);
  const hasOtherDdl = /\bALTER\s+TABLE\b|\bCREATE\s+(?:INDEX|VIEW|SEQUENCE|SCHEMA|DATABASE)\b/i.test(trimmed);

  if (hasDml && !hasOtherDdl) {
    return '转换需要表结构定义（CREATE TABLE），仅有 INSERT/UPDATE/DELETE 语句无法完成转换。';
  }
  if (!hasDml && !hasOtherDdl && !/\bSELECT\b/i.test(trimmed)) {
    return '未检测到 CREATE TABLE 等表结构定义语句，无法进行方言转换。';
  }
  return null;
};

// SQL 默认值
const defaultSource = '-- 请在此处黏贴源 SQL 或通过上传文件进行转换';
const defaultTarget = '-- 转换后的 SQL 结果将在此处展示';

// SQL 状态
const sourceSql = ref(defaultSource);
const targetSql = ref(defaultTarget);
const sourceMode = ref('Auto-Sniff');
const targetMode = ref('pgsql');

// 方言选项
const sourceDialects = ref<Array<{ label: string; value: string }>>([
  { label: '自动识别 (Auto-Sniff)', value: 'Auto-Sniff' }
]);

const targetDialects = ref<Array<{ label: string; value: string }>>([]);

// 任务状态
const logs = ref<string[]>([]);
const activeTaskId = ref('');
const converting = ref(false);

// WebSocket 引用
let ws: WebSocket | null = null;
let pollTimer: any = null;
let wsReconnectAttempts = 0;
let wsMaxReconnect = 5;
// WebSocket 连接状态指示: 'connecting' | 'connected' | 'disconnected'
const wsStatus = ref<'connecting' | 'connected' | 'disconnected'>('disconnected');

const startPolling = (taskId: string) => {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    if (!converting.value) {
      clearInterval(pollTimer);
      pollTimer = null;
      return;
    }
    try {
      const res: any = await request.get(`/api/tasks/${taskId}`);
      if (res && res.task_id === activeTaskId.value) {
        if (res.status === 'SUCCESS') {
          clearInterval(pollTimer);
          pollTimer = null;
          converting.value = false;
          if (!logs.value.some(l => l.includes('✅ 转换成功'))) {
            logs.value.push(`[${new Date().toLocaleTimeString()}] ✅ 转换成功！`);
          }
          fetchConvertedResult(taskId);
        } else if (res.status === 'FAILED') {
          clearInterval(pollTimer);
          pollTimer = null;
          converting.value = false;
          const errorMsg = res.error || '未知错误';
          if (!logs.value.some(l => l.includes('❌ 转换失败'))) {
            logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ 转换失败: ${errorMsg}`);
          }
          message.error(`转换失败: ${errorMsg}`);
        } else if (res.progress) {
          const step = res.progress.step || '';
          const desc = res.progress.description || '';
          const percent = res.progress.percentage !== undefined ? `${res.progress.percentage}%` : '';
          if (desc) {
            const logMsg = `[${new Date().toLocaleTimeString()}] ${step} ${percent} - ${desc}`;
            const isDup = logs.value.slice(-3).some(l => l.includes(desc));
            if (!isDup) {
              logs.value.push(logMsg);
            }
          }
        }
      }
    } catch {
      // 静默失败
    }
  }, 1000);
};

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
};

const initWebSocket = () => {
  try {
    wsStatus.value = 'connecting';
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const token = localStorage.getItem('session_token') || '';
    // 将 Token 显式拼接至 Query 参数中，绕过对 HttpOnly Cookie 自动传递的依赖
    const wsUrl = `${protocol}//${window.location.host}/api/ws?token=${encodeURIComponent(token)}`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      wsStatus.value = 'connected';
      wsReconnectAttempts = 0;  // 成功建立连接后重置重连计数
      logs.value.push(`[${new Date().toLocaleTimeString()}] 🟢 WebSocket 连接成功。`);
      if (converting.value && activeTaskId.value) {
        // 重连成功，若任务正在进行，立即注销 Polling，无缝切回 WebSocket 推送通道
        stopPolling();
        logs.value.push(`[${new Date().toLocaleTimeString()}] 🔄 已自动将监听通道切回 WebSocket 实时进度推送模式。`);
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'ping') return; // 拦截并忽略心跳探测包
        if (data.task_id === activeTaskId.value) {
          if (data.progress) {
            const step = data.progress.step || '';
            const desc = data.progress.description || '';
            const percent = data.progress.percentage !== undefined ? `${data.progress.percentage}%` : '';
            if (desc) {
              const logMsg = `[${new Date().toLocaleTimeString()}] ${step} ${percent} - ${desc}`;
              const isDup = logs.value.slice(-3).some(l => l.includes(desc));
              if (!isDup) {
                logs.value.push(logMsg);
              }
            }
          }
          if (data.status === 'SUCCESS') {
            converting.value = false;
            stopPolling();
            if (!logs.value.some(l => l.includes('✅ 转换成功'))) {
              logs.value.push(`[${new Date().toLocaleTimeString()}] ✅ 转换成功！`);
            }
            fetchConvertedResult(data.task_id);
          } else if (data.status === 'FAILED') {
            converting.value = false;
            stopPolling();
            const errorMsg = data.error || '未知错误';
            if (!logs.value.some(l => l.includes('❌ 转换失败'))) {
              logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ 转换失败: ${errorMsg}`);
            }
            message.error(`转换失败: ${errorMsg}`);
          }
        }
      } catch {
        // 忽略解析错误
      }
    };

    ws.onclose = (event) => {
      wsStatus.value = 'disconnected';

      // 4001: 认证失效 (Token 错误)，4003: IP 被封禁。此两类情况不进行无谓重连，直接终止循环
      if (event.code === 4001 || event.code === 4003) {
        logs.value.push(`[${new Date().toLocaleTimeString()}] 🔴 WebSocket 连接请求被服务端拒绝 (握手失效, 错误码: ${event.code})。`);
        if (event.code === 4001) {
          message.error("登录凭证已失效，请重新登录。");
          authStore.clearToken();
          window.location.href = '#/login';
        } else if (event.code === 4003) {
          message.error("访问受限：您的 IP 已被封禁或不在白名单内。");
        }
        return;
      }

      wsReconnectAttempts++;
      if (wsReconnectAttempts < wsMaxReconnect) {
        logs.value.push(`[${new Date().toLocaleTimeString()}] 🟡 WebSocket 连接已断开，正在尝试第 ${wsReconnectAttempts} 次重连...`);
        setTimeout(initWebSocket, 3000);
      } else {
        logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ WebSocket 重连尝试已达上限，已彻底放弃重连。`);
      }
      // WebSocket 断开期间，若任务仍在转换中，启动 Polling 轮询保底以防接收不到进度
      if (converting.value && activeTaskId.value) {
        if (!pollTimer) {
          logs.value.push(`[${new Date().toLocaleTimeString()}] ⚠️ 进度监听通道已自动无缝降级为 Polling 短轮询模式。`);
          startPolling(activeTaskId.value);
        }
      }
    };
  } catch {
    wsStatus.value = 'disconnected';
  }
};

const fetchConvertedResult = async (taskId: string) => {
  try {
    const res = await request.get(`/api/download/${taskId}`, { responseType: 'text' });
    targetSql.value = typeof res === 'string' ? res : JSON.stringify(res);
  } catch (error: any) {
    message.error('拉取转换结果失败: ' + (error.message || error));
  }
};

const handleConvert = async () => {
  // SQL 校验
  const validationError = validateSql(sourceSql.value);
  if (validationError) {
    logs.value = [`[${new Date().toLocaleTimeString()}] ❌ ${validationError}`];
    message.error(validationError);
    return;
  }

  if (!sourceSql.value.trim()) {
    message.warning('请输入源 SQL 代码');
    return;
  }
  converting.value = true;
  logs.value = [`[${new Date().toLocaleTimeString()}] 正在创建转换任务...`];
  activeTaskId.value = '';

  try {
    const blob = new Blob([sourceSql.value], { type: 'text/plain' });
    const file = new File([blob], 'online_query.sql', { type: 'text/plain' });
    const formData = new FormData();
    formData.append('source_mode', sourceMode.value);
    formData.append('target_mode', targetMode.value);
    formData.append('file', file);

    const res: any = await request.post('/api/convert', formData);
    if (res && res.task_id) {
      activeTaskId.value = res.task_id;
      logs.value.push(`[${new Date().toLocaleTimeString()}] 任务创建成功 ID: ${res.task_id}`);
      if (res.status === 'SUCCESS') {
        logs.value.push(`[${new Date().toLocaleTimeString()}] ⚡ 命中缓存！`);
        converting.value = false;
        fetchConvertedResult(res.task_id);
      } else {
        // 优先使用 WebSocket，若不可用则触发轮询
        if (ws && ws.readyState === WebSocket.OPEN) {
          logs.value.push(`[${new Date().toLocaleTimeString()}] 任务已入队，正在通过 WebSocket 实时监听进度...`);
        } else {
          logs.value.push(`[${new Date().toLocaleTimeString()}] 任务已入队，通过 Polling 轮询监听进度...`);
          startPolling(res.task_id);
        }
      }
    } else {
      converting.value = false;
      logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ 任务创建失败`);
      message.error('任务创建失败');
    }
  } catch (error: any) {
    converting.value = false;
    const detail = error.response?.data?.detail || error.message || '任务创建失败';
    logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ 任务失败: ${detail}`);
    message.error(detail);
  }
};

const handleFileUpload = async (options: any) => {
  const fileObj = options.file?.file;
  if (!fileObj) {
    message.error('未检测到有效的上传文件');
    return;
  }
  if (converting.value) return;

  converting.value = true;
  logs.value = [`[${new Date().toLocaleTimeString()}] 正在上传并创建大文件转换任务...`];
  activeTaskId.value = '';

  try {
    const formData = new FormData();
    formData.append('source_mode', sourceMode.value);
    formData.append('target_mode', targetMode.value);
    formData.append('file', fileObj);

    const res: any = await request.post('/api/convert', formData);
    if (res && res.task_id) {
      activeTaskId.value = res.task_id;
      logs.value.push(`[${new Date().toLocaleTimeString()}] 任务创建成功 ID: ${res.task_id}`);
      if (res.status === 'SUCCESS') {
        logs.value.push(`[${new Date().toLocaleTimeString()}] ⚡ 命中缓存！`);
        converting.value = false;
        fetchConvertedResult(res.task_id);
      } else {
        // 优先使用 WebSocket，若不可用则触发轮询
        if (ws && ws.readyState === WebSocket.OPEN) {
          logs.value.push(`[${new Date().toLocaleTimeString()}] 任务已入队，正在通过 WebSocket 实时监听进度...`);
        } else {
          logs.value.push(`[${new Date().toLocaleTimeString()}] 任务已入队，通过 Polling 轮询监听进度...`);
          startPolling(res.task_id);
        }
      }
    } else {
      converting.value = false;
      logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ 任务创建失败`);
      message.error('任务创建失败');
    }
  } catch (error: any) {
    converting.value = false;
    const detail = error.response?.data?.detail || error.message || '上传文件转换失败';
    logs.value.push(`[${new Date().toLocaleTimeString()}] ❌ 任务提交失败: ${detail}`);
    message.error(detail);
  }
};

const clearWorkspace = () => {
  sourceSql.value = defaultSource;
  targetSql.value = defaultTarget;
  logs.value = [];
  activeTaskId.value = '';
};

const canClear = computed(() => {
  if (converting.value) return false;
  return (
    sourceSql.value.trim() !== defaultSource.trim() ||
    targetSql.value.trim() !== defaultTarget.trim() ||
    logs.value.length > 0
  );
});

const parseLog = (log: string) => {
  const timeRegex = /^\[\d{2}:\d{2}:\d{2}\]/;
  const match = log.match(timeRegex);
  if (match) {
    const timeStr = match[0];
    const content = log.substring(timeStr.length);
    const isSuccess = content.includes('SUCCESS') || content.includes('✅') || content.includes('成功');
    const isError = content.includes('ERROR') || content.includes('❌') || content.includes('失败') || content.includes('异常');
    const isWarn = content.includes('WARN') || content.includes('警告') || content.includes('重试');
    return {
      time: timeStr,
      content,
      type: isSuccess ? 'success' : isError ? 'error' : isWarn ? 'warning' : 'info'
    };
  }
  return { time: '', content: log, type: 'info' };
};

onMounted(async () => {
  // 获取 WebSocket 重连配置
  try {
    const wsConfig: any = await request.get('/api/ws-config');
    if (wsConfig && wsConfig.max_reconnect_attempts) {
      wsMaxReconnect = wsConfig.max_reconnect_attempts;
    }
  } catch {
    // 使用默认值 5
  }
  initWebSocket();
  try {
    const res = await request.get('/api/dialects');
    if (Array.isArray(res)) {
      sourceDialects.value = [
        { label: '自动识别 (Auto-Sniff)', value: 'Auto-Sniff' },
        ...res
      ];
      targetDialects.value = res;
    }
  } catch (e) {
    console.error('Failed to load dialects:', e);
  }
});

onUnmounted(() => {
  if (ws) ws.close();
  stopPolling();
});
</script>

<template>
  <div class="flex flex-col gap-5 h-full">
    <!-- 页面标题 -->
    <div class="flex items-center justify-between shrink-0">
      <div>
        <h2 class="text-lg font-bold" style="color: var(--text-primary)">转换工作台</h2>
        <p class="text-xs mt-0.5" style="color: var(--text-muted)">输入源 SQL 脚本，选择目标方言，一键完成流式转换</p>
      </div>
    </div>

    <!-- 主编辑区域 — 改为悬浮式的独立双翼卡片结构，去除大外框与中间分隔线 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6 flex-1 min-h-0">
      <!-- 左侧：源 SQL 输入 (悬浮式卡片) -->
      <div class="lg:col-span-5 flex flex-col min-h-0 border rounded-xl overflow-hidden glass-panel"
           :style="{ borderColor: 'var(--border-color)' }">
        <div class="flex items-center justify-between px-4 py-2.5 shrink-0 border-b"
             :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)' }">
          <span class="text-xs font-bold uppercase tracking-wider flex items-center gap-2" style="color: var(--text-secondary)">
            <span class="w-2 h-2 rounded-full bg-indigo-500"></span>
            源 SQL 脚本
          </span>
          <div class="flex items-center gap-2">
            <span class="text-[11px]" style="color: var(--text-muted)">源方言:</span>
            <select
              v-model="sourceMode"
              :disabled="converting"
              class="text-xs rounded-md h-7 px-2 outline-none disabled:opacity-50 disabled:cursor-not-allowed border"
              :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }"
            >
              <option v-for="d in sourceDialects" :key="d.value" :value="d.value">{{ d.label }}</option>
            </select>
          </div>
        </div>
        <div class="flex-1 min-h-[260px]">
          <MonacoEditor v-model:value="sourceSql" language="sql" :readOnly="converting" />
        </div>
      </div>

      <!-- 中部：转换控制桥接区 (无背景、无分割线，完全融入外部) -->
      <div class="lg:col-span-2 flex flex-col items-center justify-center gap-5 py-6 px-2 select-none transition-all duration-300 relative">
        <!-- 方向指示器 -->
        <div class="flex flex-col items-center gap-1.5 text-indigo-500/80 dark:text-indigo-400/80">
          <div class="w-9 h-9 rounded-xl flex items-center justify-center border shadow-sm"
               :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
            <Icon icon="material-symbols:arrow-forward" class="w-5 h-5" />
          </div>
          <span class="text-[9px] font-bold uppercase tracking-[0.2em]" style="color: var(--text-muted)">流式转换</span>
        </div>

        <!-- 一键转换按钮 -->
        <button
          @click="handleConvert"
          :disabled="converting"
          class="relative w-full h-10 rounded-xl bg-gradient-to-br from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-md shadow-indigo-600/10 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
        >
          <Icon v-if="converting" icon="line-md:loading-twotone-loop" class="w-4 h-4" />
          <template v-else>
            <Icon icon="material-symbols:bolt" class="w-4 h-4" />
            <span>一键转换</span>
          </template>
        </button>

        <!-- 文件上传 -->
        <n-upload
          :show-file-list="false"
          :disabled="converting"
          :default-upload="false"
          @change="handleFileUpload"
          class="w-full"
        >
          <button
            :disabled="converting"
            class="group w-full h-10 rounded-xl text-xs font-medium flex items-center justify-center gap-2 transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed upload-dragger-btn"
            :style="{
              background: 'var(--bg-hover)',
              border: '1.5px dashed var(--border-color)',
              color: 'var(--text-secondary)'
            }"
          >
            <Icon icon="material-symbols:cloud-upload-outline" class="w-4 h-4 transition-all duration-200 upload-icon"
                  :style="{ color: 'var(--text-muted)' }" />
            <span>上传文件</span>
          </button>
        </n-upload>

        <!-- 清空 -->
        <button
          @click="clearWorkspace"
          :disabled="!canClear"
          class="group w-full h-10 rounded-xl text-xs font-medium flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed clear-btn"
        >
          <Icon icon="material-symbols:delete-outline" class="w-4 h-4 transition-colors duration-200" />
          <span>清空内容</span>
        </button>
      </div>

      <!-- 右侧：目标 SQL 输出 (悬浮式卡片) -->
      <div class="lg:col-span-5 flex flex-col min-h-0 border rounded-xl overflow-hidden glass-panel"
           :style="{ borderColor: 'var(--border-color)' }">
        <div class="flex items-center justify-between px-4 py-2.5 shrink-0 border-b"
             :style="{ background: 'var(--bg-hover)', borderColor: 'var(--border-color)' }">
          <span class="text-xs font-bold uppercase tracking-wider flex items-center gap-2" style="color: var(--text-secondary)">
            <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
            目标 SQL 成果
          </span>
          <div class="flex items-center gap-2">
            <span class="text-[11px]" style="color: var(--text-muted)">目标方言:</span>
            <select v-model="targetMode" class="text-xs rounded-md h-7 px-2 outline-none border"
                    :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', color: 'var(--text-primary)' }">
              <option v-for="d in targetDialects" :key="d.value" :value="d.value">{{ d.label }}</option>
            </select>
          </div>
        </div>
        <div class="flex-1 min-h-[260px]">
          <MonacoEditor v-model:value="targetSql" language="sql" read-only />
        </div>
      </div>
    </div>

    <!-- 底部：执行日志 -->
    <div class="flex flex-col gap-2 h-[180px] shrink-0">
      <div class="flex items-center gap-2 px-1 w-full justify-between">
        <div class="flex items-center gap-2">
          <Icon icon="material-symbols:terminal" class="w-3.5 h-3.5" style="color: var(--text-muted)" />
          <span class="text-[11px] font-bold uppercase tracking-wider" style="color: var(--text-muted)">执行日志</span>
        </div>
        <!-- WebSocket 状态微缩呼吸灯指示器 -->
        <span class="flex items-center gap-1.5 text-[10px] select-none shrink-0" style="color: var(--text-muted)">
          <span class="w-2 h-2 rounded-full transition-all duration-300" :style="{
            background: wsStatus === 'connected' ? '#10b981' : wsStatus === 'connecting' ? '#f59e0b' : '#ef4444',
            boxShadow: wsStatus === 'connected' ? '0 0 6px #10b981' : wsStatus === 'connecting' ? '0 0 6px #f59e0b' : 'none'
          }" :class="{ 'animate-pulse': wsStatus === 'connected', 'animate-bounce': wsStatus === 'connecting' }"></span>
          <span>
            {{ wsStatus === 'connected' ? 'WebSocket 已联通' : wsStatus === 'connecting' ? 'WebSocket 连接中...' : 'WebSocket 断开 (轮询保底)' }}
          </span>
        </span>
      </div>
      <div class="flex-1 rounded-xl p-4 overflow-y-auto font-mono text-xs leading-relaxed space-y-1.5 border"
           :style="{ background: 'var(--bg-secondary)', borderColor: 'var(--border-color)' }">
        <div v-if="logs.length === 0" class="italic select-none" style="color: var(--text-muted)">暂无执行任务，请在上方输入 SQL 并开始转换。</div>
        <div v-for="(log, idx) in logs" :key="idx" class="whitespace-pre-wrap select-text leading-relaxed py-0.5 flex gap-1.5">
          <template v-if="parseLog(log).time">
            <span class="text-indigo-500/80 dark:text-indigo-400/80 font-semibold shrink-0 select-none">{{ parseLog(log).time }}</span>
            <span :class="{
              'text-emerald-600 dark:text-emerald-400 font-medium': parseLog(log).type === 'success',
              'text-red-600 dark:text-red-400 font-medium': parseLog(log).type === 'error',
              'text-amber-600 dark:text-amber-400 font-medium': parseLog(log).type === 'warning',
              'text-[var(--text-secondary)]': parseLog(log).type === 'info',
            }">{{ parseLog(log).content }}</span>
          </template>
          <template v-else>
            <span class="text-[var(--text-secondary)]">{{ log }}</span>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 文件上传按钮悬停时边框高亮 */
.upload-dragger-btn:hover {
  border-color: #6366f1 !important;
}

/* 清空按钮：默认淡红，悬停变深红 */
.clear-btn {
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: rgba(239, 68, 68, 0.7);
  transition: all 0.2s ease;
}
.clear-btn:hover:not(:disabled) {
  background: #ef4444;
  border-color: #ef4444;
  color: #ffffff;
}
.clear-btn:active:not(:disabled) {
  background: #dc2626;
}
</style>
