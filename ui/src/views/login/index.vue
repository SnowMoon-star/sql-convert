<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../../store/auth';
import request from '../../utils/request';

const router = useRouter();
const message = useMessage();
const authStore = useAuthStore();

const username = ref('');
const password = ref('');
const loading = ref(false);

const handleLogin = async () => {
  if (!username.value || !password.value) {
    message.warning('请输入用户名和密码');
    return;
  }
  loading.value = true;
  try {
    const res: any = await request.post('/api/login', {
      username: username.value,
      password: password.value,
    });
    if (res.status === 'success') {
      authStore.setToken(res.token, res.username);
      message.success('登录成功，欢迎回来！');
      router.push('/workspace');
    } else {
      message.error(res.detail || '登录失败');
    }
  } catch (error: any) {
    const detail = error.response?.data?.detail || error.message || '网络连接异常，登录失败。';
    message.error(detail);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="relative w-full h-full min-h-screen flex items-center justify-center p-4"
       :style="{ background: 'var(--bg-primary)', color: 'var(--text-primary)' }">
    <!-- 背景流光特效 -->
    <div class="absolute w-[400px] h-[400px] rounded-full bg-indigo-500/10 blur-[120px] top-[10%] left-[15%]"></div>
    <div class="absolute w-[400px] h-[400px] rounded-full bg-violet-600/10 blur-[120px] bottom-[15%] right-[15%]"></div>

    <div class="w-full max-w-[420px] glass-panel rounded-2xl p-8 flex flex-col items-center">
      <!-- 头部 logo 与标题 -->
      <div class="flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mb-6">
        <Icon icon="material-symbols:database" class="w-8 h-8" />
      </div>
      
      <h2 class="text-2xl font-bold tracking-wide mb-1" style="color: var(--text-primary)">SQL Convert</h2>
      <p class="text-sm mb-8" style="color: var(--text-secondary)">多方言 SQL 流式转换器可视化工作台</p>

      <form @submit.prevent="handleLogin" class="w-full space-y-5">
        <!-- 用户名 -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold" style="color: var(--text-secondary)">账号</label>
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)">
              <Icon icon="material-symbols:person-outline" class="w-5 h-5" />
            </span>
            <input 
              v-model="username"
              type="text" 
              placeholder="请输入账号"
              class="w-full h-11 pl-10 pr-4 rounded-lg glass-input text-sm outline-none"
              :style="{ color: 'var(--text-primary)' }"
              required
            />
          </div>
        </div>

        <!-- 密码 -->
        <div class="space-y-1.5">
          <label class="text-xs font-semibold" style="color: var(--text-secondary)">密码</label>
          <div class="relative">
            <span class="absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)">
              <Icon icon="material-symbols:lock-outline" class="w-5 h-5" />
            </span>
            <input 
              v-model="password"
              type="password" 
              placeholder="请输入密码"
              class="w-full h-11 pl-10 pr-4 rounded-lg glass-input text-sm outline-none"
              :style="{ color: 'var(--text-primary)' }"
              required
            />
          </div>
        </div>



        <!-- 登录按钮 -->
        <button
          type="submit"
          :disabled="loading"
          class="w-full h-11 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all duration-300 flex items-center justify-center space-x-2 shadow-lg shadow-indigo-600/20 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none"
        >
          <Icon v-if="loading" icon="line-md:loading-twotone-loop" class="w-5 h-5" />
          <span>{{ loading ? '安全验证中...' : '安全登录' }}</span>
        </button>
      </form>
    </div>
  </div>
</template>
