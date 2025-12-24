<template>
  <div class="min-h-screen bg-gray-100">
    <!-- 头部导航 -->
    <header class="bg-white shadow-sm">
      <div class="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
        <div class="flex items-center space-x-2 cursor-pointer" @click="goHome">
          <el-icon class="text-indigo-600 text-xl"><Data-Analysis /></el-icon>
          <h1 class="text-lg font-bold text-gray-900">HotSpotAI</h1>
        </div>
        <el-button @click="goHome" size="small">返回首页</el-button>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="max-w-4xl mx-auto px-4 py-8">
      <!-- 加载状态 -->
      <div v-if="loading" class="py-12 text-center text-gray-400">
        <el-icon class="is-loading text-3xl mb-2"><Loading /></el-icon>
        <p class="text-sm">加载中...</p>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="bg-white rounded-lg shadow-sm p-8 text-center">
        <el-result icon="error" title="文章不存在" sub-title="该分享链接可能已失效或文章已被设为私有">
          <template #extra>
            <el-button type="primary" @click="goHome">返回首页</el-button>
          </template>
        </el-result>
      </div>

      <!-- 文章内容 -->
      <article v-else class="bg-white rounded-lg shadow-sm p-6 sm:p-8">
        <!-- 文章头部 -->
        <div class="mb-6 pb-6 border-b">
          <el-tag :type="getPlatformTagType(article.platform)" size="small" class="mb-2">
            {{ getPlatformLabel(article.platform) }}
          </el-tag>
          <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">{{ article.title }}</h1>
          <p class="text-sm text-gray-500">
            基于《{{ article.topic_title }}》生成
            <span v-if="article.topic_link" class="ml-2">
              <a :href="article.topic_link" target="_blank" class="text-indigo-600 hover:underline">查看原文</a>
            </span>
          </p>
          <p class="text-xs text-gray-400 mt-2">生成于 {{ formatDate(article.created_at) }}</p>
        </div>

        <!-- 文章正文 -->
        <div v-html="parsedContent" class="prose prose-lg max-w-none"></div>

        <!-- 底部操作 -->
        <div class="mt-8 pt-6 border-t flex gap-3">
          <el-button type="primary" @click="copyContent">复制全文</el-button>
          <el-button @click="goHome">我也想生成</el-button>
        </div>
      </article>
    </main>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getSharedArticle } from '@/api/modules/articles'
import { marked } from 'marked'

export default {
  name: 'SharedArticle',
  setup() {
    const router = useRouter()
    const route = useRoute()

    const loading = ref(true)
    const error = ref(false)
    const article = ref(null)

    const parsedContent = computed(() => {
      if (!article.value?.content) return ''
      try { return marked.parse(article.value.content) }
      catch (e) { return article.value.content }
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

    // 获取文章
    const fetchArticle = async () => {
      const shareToken = route.params.shareToken
      if (!shareToken) {
        error.value = true
        loading.value = false
        return
      }

      try {
        const data = await getSharedArticle(shareToken)
        article.value = data
      } catch (e) {
        error.value = true
      } finally {
        loading.value = false
      }
    }

    // 复制内容
    const copyContent = () => {
      navigator.clipboard.writeText(article.value.content)
      ElMessage.success('已复制到剪贴板')
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

    onMounted(fetchArticle)

    return {
      loading, error, article, parsedContent, formatDate, copyContent, goHome,
      getPlatformLabel, getPlatformTagType
    }
  }
}
</script>
