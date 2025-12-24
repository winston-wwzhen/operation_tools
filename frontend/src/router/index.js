import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

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
    meta: { title: '历史记录', public: true }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录/注册', public: true }
  },
  {
    path: '/my-articles',
    name: 'MyArticles',
    component: () => import('@/views/MyArticles.vue'),
    meta: { title: '我的文章', requiresAuth: true }
  },
  {
    path: '/share/:shareToken',
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

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - HotSpotAI` : 'HotSpotAI'

  // 认证守卫
  if (to.meta.requiresAuth) {
    const { isAuthenticated } = useAuth()
    if (!isAuthenticated.value) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }
  }

  next()
})

export default router
