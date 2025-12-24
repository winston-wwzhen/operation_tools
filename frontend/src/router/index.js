import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '热点聚合', public: true }
  },
  {
    path: '/history',
    name: 'History',
    component: () => import('@/views/History.vue'),
    meta: { title: '历史记录', requiresAuth: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', public: true }
  },
  {
    path: '/my-articles',
    name: 'MyArticles',
    component: () => import('@/views/MyArticles.vue'),
    meta: { title: '我的文章', requiresAuth: true }
  },
  {
    path: '/categories',
    name: 'CategoryManagement',
    component: () => import('@/views/CategoryManagement.vue'),
    meta: { title: '分类管理', requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/shared/:token',
    name: 'SharedArticle',
    component: () => import('@/views/SharedArticle.vue'),
    meta: { title: '分享文章', public: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - HotSpotAI` : 'HotSpotAI'

  const authStore = useAuthStore()

  // 已登录用户访问登录页，重定向到首页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Home' })
    return
  }

  // 需要认证的路由
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    ElMessage.warning('请先登录')
    next({
      name: 'Login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // 需要管理员权限的路由
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    ElMessage.error('无权访问')
    next({ name: 'Home' })
    return
  }

  next()
})

// 全局后置钩子
router.afterEach((to, from) => {
  // 可以在这里添加页面访问统计等逻辑
})

export default router
