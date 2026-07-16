import { defineStore } from 'pinia';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // 统一变更为 localStorage，废弃 sessionStorage
    token: localStorage.getItem('session_token') || '',
    username: localStorage.getItem('username') || '',
    isAdmin: localStorage.getItem('is_admin') === 'true',
    avatar: localStorage.getItem('avatar') || '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    setToken(token: string, username: string) {
      this.token = token;
      this.username = username;
      // 统一持久化存入 localStorage
      localStorage.setItem('session_token', token);
      localStorage.setItem('username', username);
    },
    setAvatar(avatar: string) {
      this.avatar = avatar;
      localStorage.setItem('avatar', avatar);
    },
    clearToken() {
      this.token = '';
      this.username = '';
      this.isAdmin = false;
      this.avatar = '';
      localStorage.removeItem('session_token');
      localStorage.removeItem('username');
      localStorage.removeItem('is_admin');
      localStorage.removeItem('avatar');
      
      // 清理会话 Cookie 防止残留
      document.cookie = 'session_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
      document.cookie = 'session_token_js=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    },
    /** 启动时从后端获取当前用户的管理员状态与头像（兼容已登录但本地没有缓存的情况） */
    async fetchUserInfo() {
      if (!this.token) return;
      try {
        const resp = await fetch('/api/me', {
          headers: { 'Authorization': `Bearer ${this.token}` }
        });
        if (resp.ok) {
          const data = await resp.json();
          if (data.username) {
            this.username = data.username;
            this.isAdmin = data.is_admin || false;
            this.avatar = data.avatar || '';
            localStorage.setItem('username', data.username);
            localStorage.setItem('is_admin', String(this.isAdmin));
            localStorage.setItem('avatar', this.avatar);
          }
        }
      } catch {
        // 网络错误时静默失败，使用已有的 localStorage 值
      }
    }
  }
});
