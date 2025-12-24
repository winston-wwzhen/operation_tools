<template>
  <div class="flex-grow flex flex-col min-h-screen bg-gray-50">
    <!-- 头部导航 - 简洁版 -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center space-x-2 sm:space-x-3 cursor-pointer" @click="scrollToTop">
          <div class="w-8 h-8 sm:w-9 sm:h-9 bg-indigo-600 rounded-lg flex items-center justify-center">
            <el-icon class="text-white text-base sm:text-lg"><Data-Analysis /></el-icon>
          </div>
          <div>
            <h1 class="text-base sm:text-lg font-bold text-gray-900">HotSpotAI</h1>
          </div>
        </div>

        <div class="flex items-center space-x-1 sm:space-x-2">
          <!-- 状态和刷新按钮（仅管理员可见，大屏显示） -->
          <template v-if="isAdmin">
            <div class="hidden md:flex items-center space-x-2 mr-2 px-3 py-1.5 bg-gray-100 rounded-full">
              <span class="relative flex h-2 w-2">
                <span v-if="state.isRunning" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2" :class="state.isRunning ? 'bg-green-500' : 'bg-gray-400'"></span>
              </span>
              <span class="text-xs font-medium" :class="state.isRunning ? 'text-green-600' : 'text-gray-500'">
                {{ state.isRunning ? '运行中' : '空闲' }}
              </span>
            </div>
            <el-button type="primary" :loading="state.isRunning" @click="handleRefresh" circle title="刷新热点" class="hidden md:flex">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </template>

          <!-- 历史记录按钮（大屏显示） -->
          <el-button @click="goToHistory" circle title="历史记录" class="hidden sm:flex">
            <el-icon><Clock /></el-icon>
          </el-button>

          <!-- 我的文章按钮（登录后可见，大屏显示） -->
          <el-button v-if="isAuthenticated" @click="goToMyArticles" circle title="我的文章" class="hidden sm:flex">
            <el-icon><Document /></el-icon>
          </el-button>

          <!-- 用户菜单/登录按钮 -->
          <el-dropdown v-if="isAuthenticated" @command="handleUserCommand">
            <div class="flex items-center space-x-1 sm:space-x-2 px-2 sm:px-3 py-2 rounded-full bg-gray-100 hover:bg-gray-200 cursor-pointer">
              <div class="w-7 h-7 bg-indigo-600 rounded-full flex items-center justify-center text-white text-xs font-bold">
                {{ username?.charAt(0)?.toUpperCase() }}
              </div>
              <span class="text-sm font-medium text-gray-700 hidden sm:block">{{ username }}</span>
              <el-icon class="text-gray-400 text-sm"><Arrow-Down /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <!-- 管理员选项 -->
                <template v-if="isAdmin">
                  <el-dropdown-item command="refresh">
                    <el-icon><Refresh /></el-icon>刷新热点
                  </el-dropdown-item>
                  <el-dropdown-item command="logs">
                    <el-icon><Document /></el-icon>系统日志
                  </el-dropdown-item>
                  <el-dropdown-item divided></el-dropdown-item>
                </template>
                <!-- 常用选项 -->
                <el-dropdown-item command="history">
                  <el-icon><Clock /></el-icon>历史记录
                </el-dropdown-item>
                <el-dropdown-item command="my-articles">
                  <el-icon><Document /></el-icon>我的文章
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button v-else type="primary" @click="goToLogin">
            <el-icon><User /></el-icon>
            <span class="hidden sm:inline ml-1">登录</span>
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full flex flex-col xl:flex-row gap-6">
      <!-- 左侧：热点聚合 -->
      <section class="flex-grow xl:w-3/5 order-1">
        <!-- 头部卡片 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 bg-orange-500 rounded-lg flex items-center justify-center">
                <el-icon class="text-white"><Trophy /></el-icon>
              </div>
              <div>
                <h2 class="text-base font-bold text-gray-900">热点聚合</h2>
                <p class="text-xs text-gray-500">{{ state.lastRunTime ? formatDate(state.lastRunTime) : '暂无更新' }}</p>
              </div>
            </div>
            <span class="text-xs font-medium text-gray-500 bg-gray-100 px-3 py-1.5 rounded-full">
              {{ filteredTopics.length }} 条
            </span>
          </div>
        </div>

        <!-- 筛选器 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-3 sm:p-4 mb-4">
          <div class="space-y-2 sm:space-y-3">
            <!-- 平台筛选 -->
            <div class="flex flex-col sm:flex-row sm:items-center gap-2">
              <span class="text-xs sm:text-sm font-medium text-gray-700">平台:</span>
              <div class="flex flex-wrap gap-1">
                <el-button
                  size="small"
                  :type="selectedSource === null ? 'primary' : ''"
                  @click="selectedSource = null"
                >全部</el-button>
                <el-button
                  v-for="source in uniqueSources"
                  :key="source"
                  size="small"
                  :type="selectedSource === source ? 'primary' : ''"
                  @click="selectedSource = selectedSource === source ? null : source"
                >{{ source }}</el-button>
              </div>
            </div>

            <!-- 标签筛选 -->
            <div v-if="uniqueTags.length > 0" class="flex flex-col sm:flex-row sm:items-center gap-2">
              <span class="text-xs sm:text-sm font-medium text-gray-700">标签:</span>
              <div class="flex flex-wrap gap-1">
                <el-button
                  size="small"
                  :type="selectedTag === null ? 'primary' : ''"
                  @click="selectedTag = null"
                >全部</el-button>
                <el-button
                  v-for="tag in uniqueTags.slice(0, 8)"
                  :key="tag"
                  size="small"
                  :type="selectedTag === tag ? 'primary' : ''"
                  @click="selectedTag = selectedTag === tag ? null : tag"
                >{{ tag }}</el-button>
              </div>
            </div>

            <!-- 清除筛选 -->
            <div v-if="selectedSource || selectedTag" class="flex items-center gap-2">
              <el-button size="small" @click="clearFilters" :icon="Delete">清除筛选</el-button>
            </div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="bg-white rounded-xl p-16 text-center">
          <el-icon class="is-loading text-4xl text-indigo-500 mb-3"><Loading /></el-icon>
          <p class="text-sm text-gray-500">数据加载中...</p>
        </div>

        <!-- 空状态 -->
        <div v-else-if="state.hot_topics.length === 0" class="bg-white rounded-xl p-16 text-center">
          <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-xl flex items-center justify-center">
            <el-icon class="text-3xl text-gray-400"><Trophy /></el-icon>
          </div>
          <h3 class="text-base font-semibold text-gray-700 mb-2">暂无热点数据</h3>
          <p class="text-sm text-gray-400 mb-4">点击右上角刷新按钮获取最新热点</p>
          <el-button v-if="isAdmin" type="primary" @click="handleRefresh" :icon="Refresh">
            刷新热点
          </el-button>
        </div>

        <!-- 热点列表 -->
        <div v-else class="space-y-3">
          <div v-if="filteredTopics.length === 0" class="bg-white rounded-xl p-8 text-center">
            <p class="text-sm text-gray-500">没有符合筛选条件的热点</p>
            <el-button size="small" @click="clearFilters" class="mt-2">清除筛选</el-button>
          </div>
          <TopicCard
            v-else
            v-for="(topic, index) in filteredTopics"
            :key="index"
            :topic="topic"
            :index="index"
            @generate="openGenerateDialog"
          />
        </div>
      </section>

      <!-- 右侧：编辑器和日志 -->
      <aside id="preview-section" class="xl:w-2/5 order-2 flex flex-col gap-4">
        <!-- AI 文案编辑器 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col max-h-[80vh]">
          <!-- 头部工具栏 -->
          <div class="flex items-center justify-between px-3 sm:px-4 py-2.5 sm:py-3 border-b border-gray-200 flex-shrink-0">
            <div class="flex items-center space-x-2">
              <el-icon class="text-indigo-600"><Edit-Pen /></el-icon>
              <span class="font-semibold text-gray-800 text-sm sm:text-base">AI 文案</span>
              <el-tag v-if="generatedContent && !isEditing" size="small" type="success">预览</el-tag>
              <el-tag v-if="isEditing" size="small" type="warning">编辑中</el-tag>
            </div>
            <div v-if="generatedContent">
              <el-button-group size="small">
                <el-button :type="isEditing ? '' : 'primary'" @click="isEditing = false" :icon="View">预览</el-button>
                <el-button :type="isEditing ? 'primary' : ''" @click="isEditing = true" :icon="Edit">编辑</el-button>
              </el-button-group>
            </div>
          </div>

          <!-- 内容区域 - 固定高度可滚动 -->
          <div v-if="generatedContent" class="flex-1 overflow-hidden min-h-0">
            <!-- 预览模式 -->
            <div v-if="!isEditing" class="h-full overflow-y-auto p-3 sm:p-4 bg-gray-50">
              <div v-html="parsedContent" class="prose prose-sm max-w-none prose-headings:font-bold prose-a:text-indigo-600"></div>
            </div>

            <!-- 编辑模式 -->
            <textarea
              v-else
              v-model="generatedContent"
              class="h-full w-full p-3 sm:p-4 bg-white text-sm font-mono leading-relaxed resize-none focus:outline-none"
              placeholder="在此编辑文案内容..."
            ></textarea>
          </div>

          <!-- 加载状态 -->
          <div v-else-if="isGenerating" class="flex flex-col items-center justify-center py-12 sm:py-16 px-4 sm:px-6 flex-shrink-0 bg-gradient-to-b from-indigo-50 to-white" style="min-height: 320px;">
            <!-- 动画图标 -->
            <div class="relative mb-5 sm:mb-6">
              <div class="w-16 h-16 sm:w-20 sm:h-20 bg-indigo-100 rounded-2xl flex items-center justify-center">
                <el-icon class="text-indigo-600 text-3xl sm:text-4xl animate-pulse"><Magic-Stick /></el-icon>
              </div>
              <!-- 装饰圆点 -->
              <div class="absolute -top-1 -right-1 w-4 h-4 bg-indigo-400 rounded-full animate-bounce"></div>
              <div class="absolute -bottom-1 -left-1 w-3 h-3 bg-indigo-300 rounded-full animate-bounce" style="animation-delay: 0.2s;"></div>
            </div>

            <!-- 平台标签 -->
            <el-tag size="small" type="primary" class="mb-3">{{ getPlatformLabel(generatingPlatform) }}</el-tag>

            <!-- 加载文字 -->
            <h3 class="text-base sm:text-lg font-semibold text-gray-800 mb-2">AI 正在创作中</h3>
            <p class="text-xs sm:text-sm text-gray-500 text-center mb-4">{{ currentLoadingStep }}</p>

            <!-- 进度条 -->
            <div class="w-48 sm:w-56 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full animate-pulse" style="width: 70%;"></div>
            </div>

            <!-- 温馨提示 -->
            <p class="text-[10px] sm:text-xs text-gray-400 text-center mt-4">AI 创作需要一些时间，请耐心等待...</p>
          </div>

          <!-- 空状态 -->
          <div v-else class="flex flex-col items-center justify-center py-12 sm:py-16 px-4 sm:px-6 flex-shrink-0" style="min-height: 320px;">
            <div class="w-12 h-12 sm:w-14 sm:h-14 mb-3 sm:mb-4 bg-indigo-100 rounded-xl flex items-center justify-center">
              <el-icon class="text-indigo-500 text-xl sm:text-2xl"><Magic-Stick /></el-icon>
            </div>
            <h3 class="text-sm sm:text-base font-semibold text-gray-800 mb-1">AI 智能创作</h3>
            <p class="text-xs sm:text-sm text-gray-500 text-center">选择热点话题，AI 为您生成平台适配的专业文案</p>
          </div>

          <!-- 底部操作栏 - 始终可见 -->
          <div v-if="generatedContent" class="flex items-center justify-between px-3 sm:px-4 py-2.5 sm:py-3 border-t border-gray-200 flex-shrink-0 bg-white">
            <span class="text-xs text-gray-500">{{ contentLength }} 字</span>
            <div class="flex gap-1.5 sm:gap-2">
              <el-button size="small" @click="openPreviewDialog" :icon="View">全屏</el-button>
              <el-button size="small" @click="copyContent" :icon="CopyDocument">复制</el-button>
              <el-button size="small" type="danger" plain @click="clearContent" :icon="Delete">清空</el-button>
            </div>
          </div>
        </div>

        <!-- 系统日志（仅管理员可见） -->
        <div v-if="isAdmin" class="bg-gray-900 rounded-xl overflow-hidden">
          <div class="flex items-center justify-between px-4 py-2.5 bg-gray-800 border-b border-gray-700">
            <div class="flex items-center space-x-2">
              <el-icon class="text-gray-400 text-sm"><Monitor /></el-icon>
              <h3 class="text-xs font-semibold text-gray-400">系统日志</h3>
            </div>
            <div class="flex items-center gap-2">
              <span class="h-1.5 w-1.5 rounded-full" :class="state.isRunning ? 'bg-green-500' : 'bg-gray-600'"></span>
              <span class="text-[10px] text-gray-500">{{ state.logs.length }}</span>
              <el-button size="small" text class="!text-gray-400 !h-6 !px-2" @click="showLogsDialog = true">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </div>
          </div>
          <div class="h-48 p-3 overflow-y-auto">
            <div class="space-y-1 font-mono text-xs">
              <div v-for="log in reversedLogs.slice(0, 50)" :key="log.id" class="break-all">
                <span class="text-gray-600">[{{ log.time }}]</span>
                <span :class="getLogLevelClass(log.level)" class="ml-1 font-bold text-[10px]">[{{ log.level.toUpperCase() }}]</span>
                <span class="text-gray-300 ml-1">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </main>

    <!-- 日志抽屉 -->
    <el-drawer v-model="showLogDrawer" title="系统日志" :size="drawerSize" direction="rtl">
      <div class="h-full overflow-y-auto bg-gray-900 p-4 font-mono text-xs">
        <div v-for="log in reversedLogs" :key="log.id" class="mb-2 pb-2 border-b border-gray-800 last:border-0 break-words">
          <span class="text-gray-600">[{{ log.time }}]</span>
          <span :class="getLogLevelClass(log.level)" class="mx-1 font-bold">[{{ log.level.toUpperCase() }}]</span>
          <span class="text-gray-300">{{ log.message }}</span>
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

    <!-- 全屏预览弹框 -->
    <el-dialog
      v-model="showPreviewDialog"
      :width="previewMode === 'mobile' ? '420px' : '85%'"
      :fullscreen="false"
      destroy-on-close
    >
      <template #header="{ close, titleId, titleClass }">
        <div class="flex items-center justify-between w-full">
          <span :id="titleId" :class="titleClass">文章预览</span>
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
      <div v-if="previewMode === 'desktop'" class="max-h-[70vh] overflow-y-auto p-6 bg-white">
        <div v-html="parsedContent" class="prose prose-lg max-w-3xl mx-auto prose-headings:font-bold prose-a:text-indigo-600"></div>
      </div>

      <!-- 手机预览 -->
      <div v-else class="flex justify-center bg-gray-100 p-4 rounded-lg">
        <div class="w-full max-w-[375px] bg-white rounded-xl shadow-lg overflow-hidden">
          <div class="bg-gray-900 text-white text-xs px-4 py-2 flex justify-between items-center">
            <span>9:41</span>
            <div class="flex gap-1">
              <span>●●●</span>
              <span>📶</span>
              <span>🔋</span>
            </div>
          </div>
          <div class="h-[60vh] overflow-y-auto p-4 bg-gray-50">
            <article class="bg-white rounded-lg p-4 shadow-sm">
              <div v-html="parsedContent" class="prose prose-sm max-w-none prose-headings:font-bold prose-a:text-indigo-600"></div>
            </article>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-between items-center">
          <span class="text-sm text-gray-500">{{ contentLength }} 字</span>
          <div class="flex gap-2">
            <el-button @click="copyContent" :icon="CopyDocument">复制</el-button>
            <el-button type="primary" @click="showPreviewDialog = false">关闭</el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 系统日志全屏弹框 -->
    <el-dialog
      v-model="showLogsDialog"
      title="系统日志"
      width="80%"
      destroy-on-close
    >
      <div class="h-[70vh] overflow-y-auto bg-gray-900 p-4 font-mono text-xs">
        <div class="space-y-1">
          <div v-for="log in reversedLogs" :key="log.id" class="mb-2 pb-2 border-b border-gray-800 last:border-0 break-all">
            <span class="text-gray-500">[{{ log.time }}]</span>
            <span :class="getLogLevelClass(log.level)" class="mx-1 font-bold text-[10px]">[{{ log.level.toUpperCase() }}]</span>
            <span class="text-gray-300">{{ log.message }}</span>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-between items-center">
          <span class="text-xs text-gray-500">共 {{ state.logs.length }} 条日志</span>
          <el-button type="primary" @click="showLogsDialog = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit, View, CopyDocument, Delete, MagicStick, EditPen, Monitor, Iphone, Refresh, Document, Clock, DataAnalysis, ArrowDown, Trophy, Loading, User, SwitchButton, FullScreen } from '@element-plus/icons-vue'
import { status, content } from '@/api'
import { useAuth } from '@/composables/useAuth'
import TopicCard from '@/components/TopicCard.vue'
import GenerateDialog from '@/components/GenerateDialog.vue'
import { marked } from 'marked'

export default {
  name: 'Home',
  components: { TopicCard, GenerateDialog },
  setup() {
    const router = useRouter()
    const { isAuthenticated, isAdmin, username, logout } = useAuth()
    const loading = ref(false)
    const showLogDrawer = ref(false)
    const showGenerateDialog = ref(false)
    const showPreviewDialog = ref(false)
    const showLogsDialog = ref(false)
    const previewMode = ref('desktop')
    const isGenerating = ref(false)
    const generatingPlatform = ref('')
    const generatingStep = ref(0)
    const stepInterval = ref(null)
    const justGenerated = ref(false)
    const generatedContent = ref('')
    const isEditing = ref(false)
    const selectedTopic = ref(null)
    const selectedSource = ref(null)
    const selectedTag = ref(null)
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

    const contentLength = computed(() => {
      return generatedContent.value?.length || 0
    })

    const reversedLogs = computed(() => {
      return [...state.logs].reverse()
    })

    const drawerSize = computed(() => windowWidth.value < 768 ? '90%' : '50%')

    const uniqueSources = computed(() => {
      const sources = new Set()
      state.hot_topics.forEach(topic => {
        if (topic.source) sources.add(topic.source)
      })
      return Array.from(sources).sort()
    })

    const uniqueTags = computed(() => {
      const tags = new Set()
      state.hot_topics.forEach(topic => {
        if (topic.tags && Array.isArray(topic.tags)) {
          topic.tags.forEach(tag => tags.add(tag))
        }
      })
      return Array.from(tags).sort()
    })

    const filteredTopics = computed(() => {
      return state.hot_topics.filter(topic => {
        if (selectedSource.value && topic.source !== selectedSource.value) return false
        if (selectedTag.value && (!topic.tags || !topic.tags.includes(selectedTag.value))) return false
        return true
      })
    })

    const loadingSteps = computed(() => [
      '正在分析热点话题...',
      '正在构建内容框架...',
      'AI 正在撰写文案...',
      '正在优化内容...'
    ])

    const currentLoadingStep = computed(() => loadingSteps.value[generatingStep.value] || 'AI 正在创作中...')

    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth
    })

    const scrollToTop = () => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    const goToHistory = () => {
      router.push('/history')
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '暂无更新'
      const date = new Date(dateStr)
      const now = new Date()
      const diff = now - date
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (minutes < 1) return '刚刚更新'
      if (minutes < 60) return `${minutes} 分钟前更新`
      if (hours < 24) return `${hours} 小时前更新`
      if (days < 7) return `${days} 天前更新`
      return dateStr.split(' ')[1] + ' 更新'
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

    const setupSSE = () => {
      const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000'
      const eventSource = new EventSource(`${baseURL}/events`)

      eventSource.onopen = () => {
        console.log('SSE 连接已建立')
      }

      eventSource.addEventListener('status', (e) => {
        try {
          const data = JSON.parse(e.data)
          state.isRunning = data.isRunning
          state.lastRunTime = data.lastRunTime
          state.nextRunTime = data.nextRunTime
        } catch (err) {
          console.error('解析状态事件失败:', err)
        }
      })

      eventSource.addEventListener('log', (e) => {
        try {
          const log = JSON.parse(e.data)
          state.logs.push(log)
        } catch (err) {
          console.error('解析日志事件失败:', err)
        }
      })

      eventSource.addEventListener('topics', (e) => {
        try {
          const topics = JSON.parse(e.data)
          state.hot_topics = topics
        } catch (err) {
          console.error('解析话题事件失败:', err)
        }
      })

      eventSource.onerror = (err) => {
        console.error('SSE 连接错误:', err)
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

    const confirmGenerate = async (platform, options = {}) => {
      if (!selectedTopic.value) return

      if (!isAuthenticated.value) {
        ElMessage.warning('请先登录后再生成文章')
        showGenerateDialog.value = false
        router.push('/login')
        return
      }

      isGenerating.value = true
      justGenerated.value = false
      generatedContent.value = ''
      showGenerateDialog.value = false

      // 生成状态信息
      generatingPlatform.value = platform
      generatingStep.value = 0

      // 自动切换生成步骤
      stepInterval.value = setInterval(() => {
        generatingStep.value = (generatingStep.value + 1) % loadingSteps.value.length
      }, 2500)

      if (windowWidth.value < 1280) {
        nextTick(() => {
          const el = document.getElementById('preview-section')
          if (el) {
            const y = el.getBoundingClientRect().top + window.scrollY - 80
            window.scrollTo({ top: y, behavior: 'smooth' })
          }
        })
      }

      try {
        if (options.save) {
          const { generateAndSave } = await import('@/api/modules/articles')
          const result = await generateAndSave({
            topic: selectedTopic.value,
            platform,
            is_public: options.public || false
          })

          if (result.success && result.content) {
            generatedContent.value = result.content
            justGenerated.value = true
            setTimeout(() => justGenerated.value = false, 2000)

            if (result.share_token && options.public) {
              ElMessage.success({
                message: '创作完成！文章已保存，分享链接已生成',
                duration: 3000
              })
            } else {
              ElMessage.success('创作完成！文章已保存到您的文章库')
            }
          } else if (result.content) {
            generatedContent.value = result.content
            justGenerated.value = true
            setTimeout(() => justGenerated.value = false, 2000)
            ElMessage.warning('文章已生成但保存失败')
          } else {
            ElMessage.warning('生成内容为空')
          }
        } else {
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
        }
      } catch (e) {
        ElMessage.error('生成失败: ' + (e.response?.data?.detail || e.message || '未知错误'))
      } finally {
        isGenerating.value = false
        generatingPlatform.value = ''
        if (stepInterval.value) {
          clearInterval(stepInterval.value)
          stepInterval.value = null
        }
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

    const getPlatformLabel = (platform) => {
      const labels = {
        wechat: '微信公众号',
        xiaohongshu: '小红书',
        zhihu: '知乎',
        toutiao: '今日头条'
      }
      return labels[platform] || platform
    }

    const openPreviewDialog = () => {
      showPreviewDialog.value = true
    }

    const getLogLevelClass = (level) => {
      switch (level) {
        case 'error': return 'text-red-400'
        case 'warning': return 'text-yellow-400'
        case 'success': return 'text-green-400'
        default: return 'text-blue-400'
      }
    }

    const handleUserCommand = (command) => {
      switch (command) {
        case 'refresh':
          handleRefresh()
          break
        case 'logs':
          showLogDrawer.value = true
          break
        case 'history':
          goToHistory()
          break
        case 'my-articles':
          goToMyArticles()
          break
        case 'logout':
          handleLogout()
          break
      }
    }

    const handleLogout = async () => {
      await logout()
    }

    const goToLogin = () => {
      router.push('/login')
    }

    const goToMyArticles = () => {
      router.push('/my-articles')
    }

    const clearFilters = () => {
      selectedSource.value = null
      selectedTag.value = null
    }

    let eventSource = null

    onMounted(() => {
      fetchStatus()
      eventSource = setupSSE()
    })

    onUnmounted(() => {
      if (eventSource) {
        eventSource.close()
      }
    })

    return {
      state, loading, showLogDrawer, showGenerateDialog, showPreviewDialog, showLogsDialog, previewMode,
      isGenerating, generatingPlatform, generatingStep, stepInterval, justGenerated, currentLoadingStep, loadingSteps,
      generatedContent, parsedContent, reversedLogs, selectedTopic, logContainer, drawerSize,
      isEditing, contentLength,
      selectedSource, selectedTag, uniqueSources, uniqueTags, filteredTopics,
      handleRefresh, openGenerateDialog, confirmGenerate, copyContent, clearContent, openPreviewDialog,
      scrollToTop, goToHistory, goToMyArticles, formatDate, clearFilters,
      getLogLevelClass, getPlatformLabel,
      isAuthenticated, isAdmin, username, handleUserCommand, goToLogin,
      Edit, View, CopyDocument, Delete, MagicStick, EditPen, Monitor, Iphone, Refresh,
      Document, Clock, DataAnalysis, ArrowDown, Trophy, Loading, User, SwitchButton, FullScreen
    }
  }
}
</script>
