import { createRouter, createWebHashHistory } from 'vue-router';
import { useAuthStore } from '../store/auth';

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('../views/login/index.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('../views/dashboard/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/workspace',
      name: 'Workspace',
      component: () => import('../views/workspace/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/history',
      name: 'History',
      component: () => import('../views/history/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/profile/index.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/users',
      name: 'Users',
      component: () => import('../views/users/index.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/active-users',
      name: 'ActiveUsers',
      component: () => import('../views/active-users/index.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/logs',
      name: 'Logs',
      component: () => import('../views/logs/index.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('../views/settings/index.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/workspace'
    }
  ]
});

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore();

  // 登录页：已登录则重定向到仪表盘
  if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' });
    return;
  }

  // 需要认证的页面
  if (to.meta.requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login' });
    return;
  }

  // 需要管理员的页面
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next({ name: 'Workspace' });
    return;
  }

  next();
});

export default router;
