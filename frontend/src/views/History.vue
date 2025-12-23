<template>
  <div class="flex-grow flex flex-col">
    <!-- 头部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center space-x-2 sm:space-x-3 cursor-pointer" @click="goHome">
          <el-icon class="text-indigo-600 text-xl sm:text-2xl"><Data-Analysis /></el-icon>
          <h1 class="text-lg sm:text-xl font-bold text-gray-900">
            HotSpotAI <span class="text-xs font-normal text-gray-500 ml-2">历史记录</span>
          </h1>
        </div>
        <div class="flex items-center space-x-2">
          <el-button @click="goHome" circle size="default">
            <el-icon><Back /></el-icon>
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-grow max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8 w-full">
      <!-- 筛选器 -->
      <div class="bg-white rounded-lg shadow-sm p-3 sm:p-4 mb-4">
        <div class="flex flex-wrap gap-3 items-end">
          <!-- 日期范围选择 -->
          <div class="flex-1 min-w-[200px]">
            <label class="block text-xs text-gray-500 mb-1">日期范围</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
              size="default"
              class="w-full"
              @change="handleDateChange"
            />
          </div>

          <!-- 快速日期选择 -->
          <div class="flex gap-2">
            <el-button
              v-for="quick in quickDates"
              :key="quick.key"
              :type="activeQuickDate === quick.key ? 'primary' : 'default'"
              size="default"
              @click="selectQuickDate(quick.key)"
            >
              {{ quick.label }}
            </el-button>
          </div>

          <!-- 数据源筛选 -->
          <div class="w-32">
            <label class="block text-xs text-gray-500 mb-1">数据源</label>
            <el-select v-model="selectedSource" placeholder="全部" clearable size="default" class="w-full" @change="fetchHistory">
              <el-option label="全部" value=""></el-option>
              <el-option label="微博" value="weibo"></el-option>
              <el-option label="百度" value="baidu"></el-option>
              <el-option label="知乎" value="zhihu"></el-option>
              <el-option label="抖音" value="douyin"></el-option>
              <el-option label="小红书" value="xiaohongshu"></el-option>
              <el-option label="头条" value="toutiao"></el-option>
            </el-select>
          </div>

          <!-- 搜索按钮 -->
          <el-button type="primary" :loading="loading" @click="fetchHistory">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <!-- 统计信息 -->
        <div v-if="stats" class="mt-3 pt-3 border-t border-gray-100 flex flex-wrap gap-4 text-xs text-gray-500">
          <span>总记录数: <strong class="text-gray-900">{{ stats.total_topics }}</strong></span>
          <span v-if="pagination.total">当前筛选: <strong class="text-gray-900">{{ pagination.total }}</strong> 条</span>
          <span v-if="stats.latest_update">最新更新: <strong class="text-gray-900">{{ stats.latest_update }}</strong></span>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading && topics.length === 0" class="py-12 text-center text-gray-400">
        <el-icon class="is-loading text-3xl mb-2"><Loading /></el-icon>
        <p class="text-sm">数据加载中...</p>
      </div>

      <!-- 空数据状态 -->
      <div v-else-if="topics.length === 0" class="bg-white rounded-lg shadow-sm p-8 text-center">
        <el-empty description="暂无历史数据"></el-empty>
      </div>

      <!-- 热点列表 -->
      <div v-else>
        <div class="space-y-3 sm:space-y-4">
          <div
            v-for="topic in topics"
            :key="topic.id"
            class="bg-white rounded-lg shadow-sm p-3 sm:p-4 hover:shadow-md transition-shadow"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="flex-grow min-w-0">
                <!-- 标题和热度 -->
                <div class="flex items-center gap-2 mb-2">
                  <el-tag :type="getSourceTagType(topic.source)" size="small">{{ getSourceLabel(topic.source) }}</el-tag>
                  <span class="text-xs text-gray-400">{{ topic.created_at }}</span>
                  <el-tag v-if="topic.heat" size="small" :type="getHeatType(topic.heat)">
                    🔥 {{ topic.heat }}
                  </el-tag>
                </div>

                <!-- 标题 -->
                <h3 class="text-sm sm:text-base font-medium text-gray-900 mb-2 line-clamp-2">
                  <a :href="topic.link" target="_blank" class="hover:text-indigo-600 transition-colors">
                    {{ topic.title }}
                  </a>
                </h3>

                <!-- 标签 -->
                <div v-if="topic.tags && topic.tags.length" class="flex flex-wrap gap-1.5 mb-2">
                  <el-tag
                    v-for="tag in topic.tags.slice(0, 5)"
                    :key="tag"
                    size="small"
                    type="info"
                    effect="plain"
                  >
                    {{ tag }}
                  </el-tag>
                </div>

                <!-- AI 点评 -->
                <p v-if="topic.comment" class="text-xs text-gray-500 italic line-clamp-2">
                  "{{ topic.comment }}"
                </p>
              </div>

              <!-- 生成按钮 -->
              <el-button
                type="primary"
                size="small"
                @click="openGenerateDialog(topic)"
                class="flex-shrink-0"
              >
                <el-icon><Edit-Pen /></el-icon>
                生成
              </el-button>
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

    <!-- 生成对话框 -->
    <GenerateDialog
      v-model="showGenerateDialog"
      :topic="selectedTopic"
      :generating="isGenerating"
      @confirm="confirmGenerate"
    />
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { history } from '@/api'
import GenerateDialog from '@/components/GenerateDialog.vue'
import { marked } from 'marked'

export default {
  name: 'History',
  components: { GenerateDialog },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const showGenerateDialog = ref(false)
    const isGenerating = ref(false)
    const selectedTopic = ref(null)
    const dateRange = ref([])
    const selectedSource = ref('')
    const activeQuickDate = ref(null)
    const topics = ref([])
    const stats = ref(null)

    const pagination = reactive({
      total: 0,
      limit: 50,
      offset: 0
    })

    const currentPage = ref(1)

    const quickDates = [
      { key: 'today', label: '今天', days: 0 },
      { key: 'week', label: '最近7天', days: 7 },
      { key: 'month', label: '最近30天', days: 30 }
    ]

    // 格式化日期为 YYYY-MM-DD
    const formatDate = (date) => {
      const d = new Date(date)
      return d.toISOString().split('T')[0]
    }

    // 获取今天的日期
    const getToday = () => formatDate(new Date())

    // 获取 N 天前的日期
    const getDateDaysAgo = (days) => {
      const d = new Date()
      d.setDate(d.getDate() - days)
      return formatDate(d)
    }

    const goHome = () => {
      router.push('/')
    }

    const handleDateChange = () => {
      activeQuickDate.value = null
    }

    const selectQuickDate = (key) => {
      const quick = quickDates.find(q => q.key === key)
      if (!quick) return

      activeQuickDate.value = key
      if (key === 'today') {
        dateRange.value = [getToday(), getToday()]
      } else {
        dateRange.value = [getDateDaysAgo(quick.days), getToday()]
      }
      fetchHistory()
    }

    const fetchHistory = async () => {
      loading.value = true
      try {
        const params = {
          offset: pagination.offset,
          limit: pagination.limit
        }

        if (dateRange.value && dateRange.value.length === 2) {
          params.start_date = dateRange.value[0]
          params.end_date = dateRange.value[1]
        }

        if (selectedSource.value) {
          params.source = selectedSource.value
        }

        const result = await history.getHistory(params)
        topics.value = result.topics || []
        pagination.total = result.total || 0
      } catch (e) {
        ElMessage.error('加载失败: ' + (e.message || '未知错误'))
      } finally {
        loading.value = false
      }
    }

    const fetchStats = async () => {
      try {
        const result = await history.getStats()
        stats.value = result
      } catch (e) {
        console.error('获取统计信息失败:', e)
      }
    }

    const handlePageChange = (page) => {
      currentPage.value = page
      pagination.offset = (page - 1) * pagination.limit
      fetchHistory()
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const openGenerateDialog = (topic) => {
      selectedTopic.value = topic
      showGenerateDialog.value = true
    }

    const confirmGenerate = async (platform) => {
      if (!selectedTopic.value) return
      isGenerating.value = true
      showGenerateDialog.value = false

      const loadingInstance = ElLoading.service({
        lock: true,
        text: `AI 正在撰写 [${platform}] 文案...`,
        background: 'rgba(0, 0, 0, 0.7)'
      })

      try {
        // 这里需要调用 content API，暂时先跳转回主页
        ElMessage.info('请返回首页查看生成结果')
        setTimeout(() => {
          router.push('/')
        }, 1000)
      } catch (e) {
        ElMessage.error('生成失败: ' + (e.message || '未知错误'))
      } finally {
        isGenerating.value = false
        loadingInstance.close()
      }
    }

    const getSourceLabel = (source) => {
      const labels = {
        weibo: '微博',
        baidu: '百度',
        zhihu: '知乎',
        douyin: '抖音',
        xiaohongshu: '小红书',
        toutiao: '头条'
      }
      return labels[source] || source
    }

    const getSourceTagType = (source) => {
      const types = {
        weibo: 'danger',
        baidu: 'primary',
        zhihu: 'success',
        douyin: 'warning',
        xiaohongshu: '#ff2442',
        toutiao: 'info'
      }
      return types[source] || ''
    }

    const getHeatType = (heat) => {
      if (heat >= 80) return 'danger'
      if (heat >= 60) return 'warning'
      return 'info'
    }

    onMounted(() => {
      fetchStats()
      // 默认加载最近7天的数据
      selectQuickDate('week')
    })

    return {
      loading, showGenerateDialog, isGenerating, selectedTopic,
      dateRange, selectedSource, activeQuickDate, topics, stats,
      pagination, currentPage, quickDates,
      goHome, handleDateChange, selectQuickDate, fetchHistory,
      handlePageChange, openGenerateDialog, confirmGenerate,
      getSourceLabel, getSourceTagType, getHeatType
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
