<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useMessage } from 'naive-ui';
import { Icon } from '@iconify/vue';
import { useAuthStore } from '../../store/auth';
import request from '../../utils/request';

const message = useMessage();
const authStore = useAuthStore();

// ── 头像管理 ──
const avatarUrl = ref('');
const avatarFile = ref<File | null>(null);
const avatarPreview = ref('');
const savingAvatar = ref(false);
const isZoomed = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

/** 从 /me 接口加载头像（以数据库为准） */
const loadAvatar = async () => {
  try {
    const res: any = await request.get('/api/me');
    if (res.avatar) {
      avatarUrl.value = res.avatar;
    }
  } catch {
    // 加载失败静默忽略
  }
};

const handleCircleClick = () => {
  // 仅在非预览状态下点击圆形区域触发上传
  if (!avatarPreview.value) {
    fileInputRef.value?.click();
  }
};

const handleAvatarChange = (e: Event) => {
  const target = e.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  const file = target.files[0];
  if (file.size > 2 * 1024 * 1024) {
    message.warning('头像图片不能超过 2MB', { duration: 3000 });
    target.value = '';
    return;
  }
  const reader = new FileReader();
  reader.onload = (ev) => {
    avatarPreview.value = ev.target?.result as string;
  };
  reader.readAsDataURL(file);
  avatarFile.value = file;
};

/** 上传头像到后端，成功后以服务端返回的 Data URI 为准 */
const saveAvatar = async () => {
  if (!avatarFile.value) return;
  savingAvatar.value = true;
  try {
    const form = new FormData();
    form.append('file', avatarFile.value);
    await request.put('/api/me/avatar', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    await loadAvatar();
    authStore.setAvatar(avatarUrl.value);
    avatarPreview.value = '';
    avatarFile.value = null;
    message.success('头像更新成功！', { duration: 3000 });
  } catch (err: any) {
    const detail = err.response?.data?.detail || '头像上传失败';
    message.error(detail, { duration: 3000 });
  } finally {
    savingAvatar.value = false;
  }
};

const cancelAvatar = () => {
  avatarPreview.value = '';
  avatarFile.value = null;
  if (fileInputRef.value) {
    fileInputRef.value.value = '';
  }
};

// ── 修改密码 ──
const oldPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const changingPassword = ref(false);

const handleChangePassword = async () => {
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    message.warning('请填写所有密码字段', { duration: 3000 });
    return;
  }
  if (newPassword.value.length < 6) {
    message.warning('新密码长度不能少于6位', { duration: 3000 });
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    message.warning('两次输入的新密码不一致', { duration: 3000 });
    return;
  }
  changingPassword.value = true;
  try {
    const res: any = await request.post('/api/me/password', {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    });
    if (res.status === 'success') {
      message.success(res.message || '密码修改成功', { duration: 3000 });
      oldPassword.value = '';
      newPassword.value = '';
      confirmPassword.value = '';
    }
  } catch (err: any) {
    const detail = err.response?.data?.detail || '密码修改失败';
    message.error(detail, { duration: 3000 });
  } finally {
    changingPassword.value = false;
  }
};

onMounted(() => {
  loadAvatar();
});
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-6">
    <!-- 页面标题 -->
    <div>
      <h2 class="text-xl font-bold" style="color: var(--text-primary)">个人中心</h2>
      <p class="text-sm mt-0.5" style="color: var(--text-muted)">管理您的个人信息和安全设置</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <!-- 左侧：头像与用户信息 -->
      <div class="md:col-span-1">
        <div class="rounded-xl p-6 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
          <!-- 头像 -->
          <div class="flex flex-col items-center">
            <!-- 头像圆形容器 -->
            <div class="relative w-24 h-24 mb-4 group cursor-pointer" @click="handleCircleClick">
              <!-- 头像/占位符 -->
              <div class="w-24 h-24 rounded-full overflow-hidden border-2 border-indigo-500/30 flex items-center justify-center transition-all duration-200"
                   :style="{ background: (avatarPreview || avatarUrl) ? 'transparent' : 'var(--bg-hover)' }">
                <img v-if="avatarPreview || avatarUrl" :src="avatarPreview || avatarUrl"
                     class="w-full h-full object-cover" alt="avatar" />
                <span v-else class="text-3xl font-bold text-indigo-500/80 select-none">
                  {{ authStore.username.substring(0, 2).toUpperCase() }}
                </span>
              </div>

              <!-- 选图前蒙层 (始终显示 + 号，若有头像则悬停显示) -->
              <div v-if="!avatarPreview"
                   class="absolute inset-0 rounded-full flex items-center justify-center transition-opacity duration-200"
                   :class="avatarUrl ? 'opacity-0 group-hover:opacity-100 bg-black/45' : 'border-2 border-dashed border-indigo-500/40 hover:bg-indigo-500/5'">
                <Icon icon="material-symbols:add" class="w-8 h-8 text-indigo-500" />
              </div>

              <!-- 预览态蒙层 (悬停显示：放大 & 删除) -->
              <div v-else
                   class="absolute inset-0 rounded-full flex items-center justify-center gap-3 bg-black/55 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button @click.stop="isZoomed = true"
                        class="p-1.5 rounded-full bg-white/15 hover:bg-white/30 text-white transition-colors"
                        title="放大">
                  <Icon icon="material-symbols:zoom-in" class="w-5 h-5" />
                </button>
                <button @click.stop="cancelAvatar"
                        class="p-1.5 rounded-full bg-red-500/20 hover:bg-red-500/45 text-white transition-colors"
                        title="删除">
                  <Icon icon="material-symbols:delete-outline" class="w-5 h-5" />
                </button>
              </div>
            </div>

            <!-- 隐藏的 file input -->
            <input ref="fileInputRef" type="file" accept=".jpg,.jpeg,.png,.webp" class="hidden" @change="handleAvatarChange" />

            <!-- 按钮展示区（仅预览时显示 保存/取消 按钮） -->
            <div v-if="avatarPreview" class="flex gap-2 mb-2">
              <button @click="saveAvatar" :disabled="savingAvatar"
                      class="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 transition-all duration-200 flex items-center gap-1.5 disabled:opacity-50">
                <Icon v-if="savingAvatar" icon="line-md:loading-twotone-loop" class="w-3.5 h-3.5" />
                保存
              </button>
              <button @click="cancelAvatar" :disabled="savingAvatar"
                      class="px-4 py-2 rounded-lg text-xs font-medium border transition-all duration-200"
                      :style="{ background: 'transparent', borderColor: 'var(--border-color)', color: 'var(--text-muted)' }">
                取消
              </button>
            </div>

            <!-- 限制提示（始终显示） -->
            <div class="text-xs text-center" style="color: var(--text-muted)">
              支持 JPG / PNG / WebP，最大 2MB
            </div>
          </div>

          <!-- 用户信息 -->
          <div class="mt-6 pt-4 border-t" :style="{ borderColor: 'var(--border-color)' }">
            <div class="space-y-3">
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">用户名</p>
                <p class="text-sm font-semibold mt-0.5" style="color: var(--text-primary)">{{ authStore.username }}</p>
              </div>
              <div>
                <p class="text-xs font-medium" style="color: var(--text-muted)">角色</p>
                <span class="inline-block mt-0.5 text-xs px-2 py-0.5 rounded font-semibold"
                      :class="authStore.isAdmin ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/20' : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/20'">
                  {{ authStore.isAdmin ? '管理员' : '普通用户' }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：修改密码 -->
      <div class="md:col-span-2">
        <div class="rounded-xl p-6 border" :style="{ background: 'var(--bg-card)', borderColor: 'var(--border-color)', boxShadow: 'var(--shadow-sm)' }">
          <h3 class="text-base font-semibold mb-1" style="color: var(--text-primary)">修改密码</h3>
          <p class="text-xs mb-6" style="color: var(--text-muted)">定期更换密码有助于提升账户安全性</p>

          <form @submit.prevent="handleChangePassword" class="space-y-5">
            <!-- 旧密码 -->
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">当前密码</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)">
                  <Icon icon="material-symbols:lock-outline" class="w-4 h-4" />
                </span>
                <input
                  v-model="oldPassword"
                  type="password"
                  placeholder="请输入当前密码"
                  class="w-full h-10 pl-10 pr-3 rounded-lg text-sm outline-none transition-all duration-200"
                  :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
                  required
                />
              </div>
            </div>

            <!-- 新密码 -->
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">新密码</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)">
                  <Icon icon="material-symbols:lock" class="w-4 h-4" />
                </span>
                <input
                  v-model="newPassword"
                  type="password"
                  placeholder="请输入新密码（至少6位）"
                  class="w-full h-10 pl-10 pr-3 rounded-lg text-sm outline-none transition-all duration-200"
                  :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
                  required
                />
              </div>
            </div>

            <!-- 确认新密码 -->
            <div class="space-y-1.5">
              <label class="text-xs font-semibold" style="color: var(--text-secondary)">确认新密码</label>
              <div class="relative">
                <span class="absolute left-3 top-1/2 -translate-y-1/2" style="color: var(--text-muted)">
                  <Icon icon="material-symbols:check-circle-outline" class="w-4 h-4" />
                </span>
                <input
                  v-model="confirmPassword"
                  type="password"
                  placeholder="请再次输入新密码"
                  class="w-full h-10 pl-10 pr-3 rounded-lg text-sm outline-none transition-all duration-200"
                  :style="{ background: 'var(--bg-hover)', border: '1px solid var(--border-color)', color: 'var(--text-primary)' }"
                  :class="{ 'border-red-500/50': confirmPassword && newPassword !== confirmPassword }"
                  required
                />
              </div>
              <p v-if="confirmPassword && newPassword !== confirmPassword" class="text-xs text-red-500 mt-1">
                两次输入的密码不一致
              </p>
            </div>

            <!-- 提交按钮 -->
            <button
              type="submit"
              :disabled="changingPassword"
              class="w-full h-10 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:pointer-events-none"
            >
              <Icon v-if="changingPassword" icon="line-md:loading-twotone-loop" class="w-4 h-4" />
              <span>{{ changingPassword ? '修改中...' : '修改密码' }}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>

  <!-- 放大预览的 Lightbox 弹窗 -->
  <div v-if="isZoomed" @click="isZoomed = false"
       class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 cursor-zoom-out backdrop-blur-sm transition-opacity duration-300">
    <div class="relative max-w-[90vw] max-h-[90vh]" @click.stop>
      <img :src="avatarPreview || avatarUrl" class="max-w-full max-h-[80vh] rounded-lg object-contain shadow-2xl" alt="enlarged avatar" />
      <button @click="isZoomed = false"
              class="absolute -top-12 right-0 p-2 rounded-full bg-white/10 text-white hover:bg-white/25 transition-colors">
        <Icon icon="material-symbols:close" class="w-6 h-6" />
      </button>
    </div>
  </div>
</template>

