<template>
  <div class="flex-grow flex flex-col">
    <!-- 头部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-50 transition-shadow duration-300">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center space-x-2 sm:space-x-3 cursor-pointer" @click="scrollToTop">
          <el-icon class="text-indigo-600 text-xl sm:text-2xl"><Data-Analysis /></el-icon>
          <h1 class="text-lg sm:text-xl font-bold text-gray-900 truncate max-w-[150px] sm:max-w-none">
            AutoMediaBot <span class="hidden sm:inline text-xs font-normal text-gray-500 ml-2">Pro</span>
          </h1>
        </div>
        <div class="flex items-center space-x-2 sm:space-x-4">
          <span class="text-xs text-gray-500 hidden md:inline-block">
            <span v-if="state.isRunning" class="text-green-600 flex items-center">
              <span class="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75 mr-1"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500 mr-2"></span>
              运行中
            </span>
            <span v-else class="flex items-center">
              <span class="h-2 w-2 rounded-full bg-gray-400 mr-2"></span>
              空闲
            </span>
          </span>
          <el-button type="primary" :loading="state.isRunning" @click="handleRefresh" circle size="default">
            <el-icon><Refresh /></el-icon>
          </el-button>
          <el-button @click="goToHistory" circle size="default" title="历史记录">
            <el-icon><Clock /></el-icon>
          </el-button>
          <el-button @click="showLogDrawer = true" circle size="default">
            <el-icon><Document /></el-icon>
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-grow max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-8 w-full flex flex-col lg:flex-row gap-4 sm:gap-6">
      <!-- 左侧：热点聚合 -->
      <section class="flex-grow lg:w-2/3 order-1">
        <div class="flex items-center justify-between mb-3 px-1">
          <h2 class="text-base sm:text-lg font-medium text-gray-900 flex items-center">
            <el-icon class="mr-1.5 text-red-500"><Trophy /></el-icon>
            热点聚合
            <span class="ml-2 text-xs text-gray-400 font-normal bg-gray-100 px-2 py-0.5 rounded-full" v-if="state.hot_topics.length">
              {{ state.hot_topics.length }}
            </span>
          </h2>
          <span class="text-xs text-gray-400 scale-90 origin-right sm:scale-100">
            {{ state.lastRunTime ? state.lastRunTime.split(' ')[1] + ' 更新' : '' }}
          </span>
        </div>

        <div v-if="loading" class="py-12 text-center text-gray-400">
          <el-icon class="is-loading text-3xl mb-2"><Loading /></el-icon>
          <p class="text-sm">数据加载中...</p>
        </div>

        <div v-else-if="state.hot_topics.length === 0" class="bg-white rounded-lg shadow-sm p-8 text-center">
          <el-empty description="暂无数据，请点击刷新" :image-size="80"></el-empty>
        </div>

        <div v-else class="space-y-3 sm:space-y-4">
          <TopicCard
            v-for="(topic, index) in state.hot_topics"
            :key="index"
            :topic="topic"
            @generate="openGenerateDialog"
          />
        </div>
      </section>

      <!-- 右侧：预览和日志 -->
      <aside id="preview-section" class="lg:w-1/3 order-2 flex flex-col gap-4 sm:gap-6">
        <!-- 文案预览 -->
        <div class="bg-white rounded-lg shadow-sm p-3 sm:p-4 flex flex-col h-[500px] sm:h-[600px] transition-all duration-500"
             :class="{'ring-2 ring-indigo-500': justGenerated}">
          <h3 class="text-sm sm:text-md font-medium text-gray-900 mb-2 sm:mb-3 flex items-center justify-between">
            <span class="flex items-center">
              <el-icon class="mr-1.5 text-indigo-600"><Edit-Pen /></el-icon>
              文案预览
            </span>
            <el-tag v-if="generatedContent" size="small" type="success" effect="dark">完成</el-tag>
          </h3>

          <div v-if="generatedContent" class="flex-grow overflow-y-auto bg-gray-50 p-3 sm:p-4 rounded border border-gray-200">
            <div v-html="parsedContent" class="prose prose-sm max-w-none break-words"></div>
          </div>

          <div v-else class="flex-grow flex items-center justify-center text-gray-400 bg-gray-50 rounded border border-dashed border-gray-300">
            <div class="text-center p-4">
              <el-icon class="text-3xl sm:text-4xl mb-2 sm:mb-3 text-gray-300"><Magic-Stick /></el-icon>
              <p class="text-xs sm:text-sm">点击左侧 "生成" 按钮<br>AI 将为您撰写爆款文案</p>
            </div>
          </div>

          <div class="mt-3 flex justify-end gap-2" v-if="generatedContent">
            <el-button size="small" @click="copyContent" class="flex-1 sm:flex-none">复制全文</el-button>
            <el-button size="small" type="danger" plain @click="clearContent" class="flex-1 sm:flex-none">清空</el-button>
          </div>
        </div>

        <!-- 系统日志 -->
        <div class="bg-gray-900 rounded-lg shadow-sm p-3 sm:p-4 text-gray-300 h-48 sm:h-64 overflow-hidden flex flex-col">
          <div class="flex justify-between items-center mb-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-gray-500">System Logs</h3>
            <span class="h-1.5 w-1.5 rounded-full" :class="state.isRunning ? 'bg-green-500 animate-pulse' : 'bg-gray-600'"></span>
          </div>
          <div class="flex-grow overflow-y-auto log-container space-y-1 scroll-smooth" ref="logContainer">
            <div v-for="log in state.logs" :key="log.id" class="break-all">
              <span class="text-gray-500 opacity-70">[{{ log.time }}]</span>
              <span :class="getLogLevelClass(log.level)" class="ml-1 font-bold text-[10px]">{{ log.level.toUpperCase() }}</span>
              <span class="ml-1 opacity-90">{{ log.message }}</span>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <!-- 日志抽屉 -->
    <el-drawer v-model="showLogDrawer" title="系统日志" :size="drawerSize" direction="rtl">
      <div class="h-full overflow-y-auto bg-gray-50 p-3 sm:p-4 font-mono text-xs sm:text-sm">
        <div v-for="log in state.logs" :key="log.id" class="mb-1.5 pb-1.5 border-b border-gray-100 last:border-0 break-words">
          <span class="text-gray-400">[{{ log.time }}]</span>
          <span :class="getLogLevelClass(log.level)" class="mx-1 font-bold">[{{ log.level.toUpperCase() }}]</span>
          <span class="text-gray-700">{{ log.message }}</span>
        </div>
      </div>
    </el-drawer>

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
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElLoading } from 'element-plus'
import { status, content } from '@/api'
import TopicCard from '@/components/TopicCard.vue'
import GenerateDialog from '@/components/GenerateDialog.vue'
import { marked } from 'marked'

export default {
  name: 'Home',
  components: { TopicCard, GenerateDialog },
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const showLogDrawer = ref(false)
    const showGenerateDialog = ref(false)
    const isGenerating = ref(false)
    const justGenerated = ref(false)
    const generatedContent = ref('')
    const selectedTopic = ref(null)
    const logContainer = ref(null)
    const windowWidth = ref(window.innerWidth)

    const state = reactive({
      isRunning: false,
      lastRunTime: '',
      nextRunTime: '',
      hot_topics: [],
      logs: []
    })

    const parsedContent = computed(() => {
      if (!generatedContent.value) return ''
      try { return marked.parse(generatedContent.value) }
      catch (e) { return generatedContent.value }
    })

    const drawerSize = computed(() => windowWidth.value < 768 ? '85%' : '40%')

    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth
    })

    const scrollToTop = () => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const goToHistory = () => {
      router.push('/history')
    }

    const fetchStatus = async () => {
      try {
        const data = await status.getStatus()
        state.isRunning = data.state.isRunning
        state.lastRunTime = data.state.lastRunTime
        state.nextRunTime = data.state.nextRunTime
        if (JSON.stringify(data.state.hot_topics) !== JSON.stringify(state.hot_topics)) {
          state.hot_topics = data.state.hot_topics || []
        }
        if (data.state.logs) state.logs = data.state.logs
      } catch (e) {
        console.error(e)
      }
    }

    // SSE 实时事件处理
    const setupSSE = () => {
      const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000'
      const eventSource = new EventSource(`${baseURL}/api/events`)

      // 连接成功
      eventSource.onopen = () => {
        console.log('SSE 连接已建立')
      }

      // 监听状态更新事件
      eventSource.addEventListener('status', (e) => {
        try {
          const data = JSON.parse(e.data)
          state.isRunning = data.isRunning
          state.lastRunTime = data.lastRunTime
          state.nextRunTime = data.nextRunTime
          // 状态更新时不覆盖 logs 和 hot_topics（由专门事件处理）
        } catch (err) {
          console.error('解析状态事件失败:', err)
        }
      })

      // 监听日志事件
      eventSource.addEventListener('log', (e) => {
        try {
          const log = JSON.parse(e.data)
          state.logs.push(log)
        } catch (err) {
          console.error('解析日志事件失败:', err)
        }
      })

      // 监听热点话题更新事件
      eventSource.addEventListener('topics', (e) => {
        try {
          const topics = JSON.parse(e.data)
          state.hot_topics = topics
        } catch (err) {
          console.error('解析话题事件失败:', err)
        }
      })

      // 连接错误处理
      eventSource.onerror = (err) => {
        console.error('SSE 连接错误:', err)
        // 3秒后尝试重连
        setTimeout(() => {
          eventSource.close()
          setupSSE()
        }, 3000)
      }

      return eventSource
    }

    const handleRefresh = async () => {
      try {
        await content.refreshTopics()
        ElMessage.success('任务已提交')
        fetchStatus()
      } catch (e) {
        ElMessage.error('启动失败')
      }
    }

    const openGenerateDialog = (topic) => {
      selectedTopic.value = topic
      showGenerateDialog.value = true
    }

    const confirmGenerate = async (platform) => {
      if (!selectedTopic.value) return
      isGenerating.value = true
      justGenerated.value = false
      generatedContent.value = ''
      showGenerateDialog.value = false

      const loadingInstance = ElLoading.service({
        target: '#preview-section',
        text: `AI 正在撰写 [${platform}] 文案...`,
        background: 'rgba(255, 255, 255, 0.9)'
      })

      if (windowWidth.value < 1024) {
        nextTick(() => {
          const el = document.getElementById('preview-section')
          if (el) {
            const y = el.getBoundingClientRect().top + window.scrollY - 80
            window.scrollTo({ top: y, behavior: 'smooth' })
          }
        })
      }

      try {
        const result = await content.generateDraft({
          topic: selectedTopic.value,
          platform
        })
        if (result.success && result.content) {
          generatedContent.value = result.content
          justGenerated.value = true
          setTimeout(() => justGenerated.value = false, 2000)
          ElMessage.success('创作完成！')
        } else {
          ElMessage.warning('生成内容为空')
        }
      } catch (e) {
        ElMessage.error('生成失败: ' + (e.message || '未知错误'))
      } finally {
        isGenerating.value = false
        loadingInstance.close()
      }
    }

    const copyContent = () => {
      const el = document.createElement('textarea')
      el.value = generatedContent.value
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
      ElMessage.success('已复制')
    }

    const clearContent = () => { generatedContent.value = '' }

    const getLogLevelClass = (level) => {
      switch (level) {
        case 'error': return 'text-red-400'
        case 'warning': return 'text-yellow-400'
        case 'success': return 'text-green-400'
        default: return 'text-blue-400'
      }
    }

    watch(() => state.logs, () => {
      nextTick(() => {
        if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
      })
    }, { deep: true })

    let eventSource = null

    onMounted(() => {
      // 初始化时获取一次完整状态
      fetchStatus()
      // 建立 SSE 连接
      eventSource = setupSSE()
    })

    // 组件卸载时关闭 SSE 连接
    onUnmounted(() => {
      if (eventSource) {
        eventSource.close()
      }
    })

    return {
      state, loading, showLogDrawer, showGenerateDialog, isGenerating, justGenerated,
      generatedContent, parsedContent, selectedTopic, logContainer, drawerSize,
      handleRefresh, openGenerateDialog, confirmGenerate, copyContent, clearContent, scrollToTop, goToHistory,
      getLogLevelClass
    }
  }
}
</script>
