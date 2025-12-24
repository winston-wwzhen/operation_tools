<template>
  <div class="flex-grow flex flex-col">
    <!-- 头部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center space-x-2 sm:space-x-3">
          <el-button @click="goHome" circle size="small" class="!w-8 !h-8">
            <el-icon><Arrow-Left /></el-icon>
          </el-button>
          <div class="flex items-center space-x-2 sm:space-x-3 cursor-pointer" @click="goHome">
            <el-icon class="text-indigo-600 text-xl sm:text-2xl"><Data-Analysis /></el-icon>
            <h1 class="text-lg sm:text-xl font-bold text-gray-900">
              HotSpotAI <span class="text-xs font-normal text-gray-500 ml-2">我的文章</span>
            </h1>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-sm text-gray-600 hidden sm:inline">{{ auth.username }}</span>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-grow max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8 w-full">
      <!-- 加载状态 -->
      <div v-if="loading" class="py-12 text-center text-gray-400">
        <el-icon class="is-loading text-3xl mb-2"><Loading /></el-icon>
        <p class="text-sm">加载中...</p>
      </div>

      <!-- 空数据状态 -->
      <div v-else-if="articles.length === 0" class="bg-white rounded-lg shadow-sm p-8 text-center">
        <el-empty description="暂无文章，快去生成第一篇吧"></el-empty>
        <el-button type="primary" @click="goHome" class="mt-4">去生成文章</el-button>
      </div>

      <!-- 文章列表 -->
      <div v-else>
        <div class="space-y-3 sm:space-y-4">
          <div
            v-for="article in articles"
            :key="article.id"
            class="bg-white rounded-lg shadow-sm p-3 sm:p-4 hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-grow min-w-0">
                <!-- 标签和日期 -->
                <div class="flex items-center gap-2 mb-2 flex-wrap">
                  <!-- 发布平台 -->
                  <el-tag :type="getPlatformTagType(article.platform)" size="small">
                    {{ getPlatformLabel(article.platform) }}
                  </el-tag>
                  <!-- 热点来源 -->
                  <span v-if="article.topic_source" :class="getSourceTagClass(article.topic_source)" class="text-[10px] px-2 py-0.5 rounded text-white">
                    {{ article.topic_source }}
                  </span>
                  <span class="text-xs text-gray-400">{{ formatDate(article.created_at) }}</span>
                  <el-tag v-if="article.is_public" size="small" type="success">公开</el-tag>
                  <el-tag v-else size="small" type="info">私有</el-tag>
                </div>

                <!-- 标题 -->
                <div class="mb-2">
                  <h3 class="text-sm sm:text-base font-medium text-gray-900 line-clamp-2">
                    {{ article.topic_title }}
                  </h3>
                  <a
                    v-if="article.topic_link"
                    :href="article.topic_link"
                    target="_blank"
                    class="text-xs text-indigo-600 hover:text-indigo-800 hover:underline mt-1 inline-block"
                  >
                    查看原热点 →
                  </a>
                </div>

                <!-- 操作按钮 -->
                <div class="flex gap-2">
                  <el-button size="small" @click="viewArticle(article)">查看</el-button>
                  <el-button
                    v-if="article.is_public"
                    size="small"
                    @click="copyShareLink(article)"
                  >
                    复制链接
                  </el-button>
                  <el-button
                    size="small"
                    :type="article.is_public ? 'warning' : 'success'"
                    @click="toggleVisibility(article)"
                  >
                    {{ article.is_public ? '设为私有' : '设为公开' }}
                  </el-button>
                  <el-button size="small" type="danger" @click="confirmDelete(article)">删除</el-button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="pagination.total > pagination.limit" class="mt-4 flex justify-center">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pagination.limit"
            :total="pagination.total"
            layout="prev, pager, next, total"
            @current-change="handlePageChange"
          />
        </div>
      </div>
    </main>

    <!-- 文章预览弹框 -->
    <el-dialog
      v-model="showArticleDialog"
      :width="previewMode === 'mobile' ? '420px' : '85%'"
      :fullscreen="false"
      destroy-on-close
    >
      <template #header="{ close, titleId, titleClass }">
        <div class="flex items-center justify-between w-full">
          <div class="flex items-center gap-3">
            <span :id="titleId" :class="titleClass">{{ currentArticle?.topic_title || '文章预览' }}</span>
            <el-tag v-if="currentArticle" :type="getPlatformTagType(currentArticle.platform)" size="small">
              {{ getPlatformLabel(currentArticle.platform) }}
            </el-tag>
          </div>
          <el-radio-group v-model="previewMode" size="small">
            <el-radio-button value="desktop">
              <el-icon><Monitor /></el-icon>
              <span class="ml-1">桌面</span>
            </el-radio-button>
            <el-radio-button value="mobile">
              <el-icon><Iphone /></el-icon>
              <span class="ml-1">手机</span>
            </el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 桌面预览 -->
      <div v-if="previewMode === 'desktop'" class="max-h-[65vh] overflow-y-auto p-6 bg-white">
        <div v-html="parsedContent" class="prose prose-lg max-w-4xl mx-auto prose-headings:font-bold prose-a:text-indigo-600 prose-a:no-underline hover:prose-a:underline"></div>
      </div>

      <!-- 手机预览 -->
      <div v-else class="flex justify-center bg-gray-100 p-4 rounded-lg">
        <div class="w-full max-w-[375px] bg-white rounded-xl shadow-2xl overflow-hidden">
          <!-- 手机状态栏 -->
          <div class="bg-gray-900 text-white text-xs px-4 py-2 flex justify-between items-center">
            <span>9:41</span>
            <div class="flex gap-1">
              <span>●●●</span>
              <span>📶</span>
              <span>🔋</span>
            </div>
          </div>
          <!-- 手机内容区 -->
          <div class="h-[55vh] overflow-y-auto p-4 bg-gray-50">
            <article class="bg-white rounded-lg p-4 shadow-sm">
              <div v-html="parsedContent" class="prose prose-sm max-w-none prose-headings:font-bold prose-a:text-indigo-600"></div>
            </article>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-500">{{ currentArticle?.content?.length || 0 }} 字</span>
          <div class="flex gap-2">
            <el-button @click="copyContent" :icon="CopyDocument">复制</el-button>
            <el-button type="primary" @click="showArticleDialog = false">关闭</el-button>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CopyDocument, Monitor, Iphone, ArrowLeft } from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'
import { getMyArticles, deleteArticle, setArticleVisibility, getArticle } from '@/api/modules/articles'
import { marked } from 'marked'

export default {
  name: 'MyArticles',
  setup() {
    const router = useRouter()
    const { logout: authLogout, username: auth } = useAuth()

    const loading = ref(false)
    const articles = ref([])
    const showArticleDialog = ref(false)
    const previewMode = ref('desktop')
    const currentArticle = ref(null)

    const pagination = reactive({
      total: 0,
      limit: 20,
      offset: 0
    })
    const currentPage = ref(1)

    const parsedContent = computed(() => {
      if (!currentArticle.value?.content) return ''
      try { return marked.parse(currentArticle.value.content) }
      catch (e) { return currentArticle.value.content }
    })

    // 格式化日期
    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // 获取文章列表
    const fetchArticles = async () => {
      loading.value = true
      try {
        const result = await getMyArticles({
          offset: pagination.offset,
          limit: pagination.limit
        })
        articles.value = result.articles || []
        pagination.total = result.total || 0
      } catch (e) {
        ElMessage.error('加载失败: ' + (e.message || '未知错误'))
      } finally {
        loading.value = false
      }
    }

    // 分页变化
    const handlePageChange = (page) => {
      currentPage.value = page
      pagination.offset = (page - 1) * pagination.limit
      fetchArticles()
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    // 查看文章
    const viewArticle = async (article) => {
      try {
        const fullArticle = await getArticle(article.id)
        currentArticle.value = fullArticle
        showArticleDialog.value = true
      } catch (e) {
        ElMessage.error('加载文章失败')
      }
    }

    // 复制分享链接
    const copyShareLink = (article) => {
      const url = `${window.location.origin}/share/${article.share_token}`
      navigator.clipboard.writeText(url)
      ElMessage.success('分享链接已复制')
    }

    // 复制文章内容
    const copyContent = () => {
      if (!currentArticle.value?.content) return
      navigator.clipboard.writeText(currentArticle.value.content)
      ElMessage.success('内容已复制')
    }

    // 切换可见性
    const toggleVisibility = async (article) => {
      try {
        await setArticleVisibility(article.id, !article.is_public)
        article.is_public = !article.is_public
        ElMessage.success(article.is_public ? '已设为公开' : '已设为私有')
      } catch (e) {
        ElMessage.error('操作失败')
      }
    }

    // 确认删除
    const confirmDelete = (article) => {
      ElMessageBox.confirm('确定要删除这篇文章吗？', '确认删除', {
        type: 'warning'
      }).then(async () => {
        try {
          await deleteArticle(article.id)
          ElMessage.success('删除成功')
          fetchArticles()
        } catch (e) {
          ElMessage.error('删除失败')
        }
      })
    }

    // 登出
    const handleLogout = async () => {
      await authLogout()
      router.push('/')
    }

    // 返回首页
    const goHome = () => {
      router.push('/')
    }

    // 获取平台标签
    const getPlatformLabel = (platform) => {
      const labels = {
        wechat: '公众号',
        xiaohongshu: '小红书',
        zhihu: '知乎',
        toutiao: '头条'
      }
      return labels[platform] || platform
    }

    // 获取平台标签类型
    const getPlatformTagType = (platform) => {
      const types = {
        wechat: 'success',
        xiaohongshu: 'danger',
        zhihu: 'primary',
        toutiao: 'warning'
      }
      return types[platform] || ''
    }

    // 获取热点来源标签样式
    const getSourceTagClass = (source) => {
      if (source.includes('微博')) return 'bg-[#ff8200]'
      if (source.includes('百度')) return 'bg-[#2932e1]'
      if (source.includes('知乎')) return 'bg-[#0084ff]'
      if (source.includes('抖音')) return 'bg-[#000000]'
      if (source.includes('小红书')) return 'bg-[#ff2442]'
      if (source.includes('头条')) return 'bg-[#f85959]'
      return 'bg-gray-500'
    }

    onMounted(fetchArticles)

    return {
      loading, articles, showArticleDialog, previewMode, currentArticle, pagination, currentPage,
      parsedContent, auth,
      handlePageChange, viewArticle, copyShareLink, copyContent, toggleVisibility,
      confirmDelete, handleLogout, goHome, formatDate, getPlatformLabel, getPlatformTagType, getSourceTagClass,
      CopyDocument, Monitor, Iphone, ArrowLeft
    }
  }
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
