<template>
  <div class="flex-grow flex flex-col min-h-screen bg-gray-50">
    <!-- 头部导航 -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div class="max-w-full mx-auto px-3 sm:px-4 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center space-x-2 sm:space-x-3 cursor-pointer" @click="scrollToTop">
          <div class="w-8 h-8 sm:w-9 sm:h-9 bg-indigo-600 rounded-lg flex items-center justify-center">
            <el-icon class="text-white text-base sm:text-lg"><Data-Analysis /></el-icon>
          </div>
          <div>
            <h1 class="text-base sm:text-lg font-bold text-gray-900">HotSpotAI</h1>
          </div>
        </div>

        <div class="flex items-center space-x-1 sm:space-x-2">
          <!-- 状态和刷新按钮（仅管理员可见） -->
          <template v-if="isAdmin">
            <!-- 桌面端：状态指示器 + 圆形刷新按钮 -->
            <div class="hidden md:flex items-center space-x-2 mr-2 px-3 py-1.5 bg-gray-100 rounded-full">
              <span class="relative flex h-2 w-2">
                <span v-if="state.isRunning" class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span class="relative inline-flex rounded-full h-2 w-2" :class="state.isRunning ? 'bg-green-500' : 'bg-gray-400'"></span>
              </span>
              <span v-if="currentRunningStage" class="text-xs font-medium text-gray-700">
                {{ currentRunningStage.icon }} {{ currentRunningStage.name }}
              </span>
              <span v-else class="text-xs font-medium text-gray-500">
                空闲
              </span>
            </div>
            <el-button type="primary" :loading="state.isRunning" @click="handleRefresh" circle title="刷新热点" class="hidden md:flex">
              <el-icon><Refresh /></el-icon>
            </el-button>
            <!-- 移动端：文字刷新按钮 -->
            <el-button type="primary" :loading="state.isRunning" @click="handleRefresh" size="small" class="md:hidden">
              <el-icon class="mr-1"><Refresh /></el-icon>
              <span class="text-xs">刷新</span>
            </el-button>
          </template>

          <!-- 历史记录按钮 -->
          <el-button @click="goToHistory" circle title="历史记录" class="hidden sm:flex">
            <el-icon><Clock /></el-icon>
          </el-button>

          <!-- 我的文章按钮 -->
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
                <template v-if="isAdmin">
                  <el-dropdown-item command="refresh">
                    <el-icon><Refresh /></el-icon>刷新热点
                  </el-dropdown-item>
                  <el-dropdown-item command="categories">
                    <el-icon><Menu /></el-icon>分类管理
                  </el-dropdown-item>
                  <el-dropdown-item command="logs">
                    <el-icon><Document /></el-icon>系统日志
                  </el-dropdown-item>
                  <el-dropdown-item divided></el-dropdown-item>
                </template>
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

    <!-- 主内容区 - 左右分栏布局 -->
    <main class="flex-grow flex flex-col lg:flex-row gap-0 lg:gap-6">
      <!-- 左侧：热点内容区 -->
      <section class="flex-grow lg:w-3/5 xl:w-2/3 px-4 sm:px-6 lg:px-8 py-6">
        <!-- Tab 切换 -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 mb-4 overflow-hidden">
          <el-tabs v-model="activeTab" class="px-4">
            <!-- 热点排行榜 Tab -->
            <el-tab-pane label="热点排行榜" name="rankings">
              <template #label>
                <div class="flex items-center space-x-2">
                  <el-icon class="text-orange-500"><Trophy /></el-icon>
                  <span class="font-semibold">热点排行榜</span>
                </div>
              </template>

              <!-- 排行榜头部信息 -->
              <div class="flex items-center justify-between py-3">
                <div class="flex items-center space-x-3">
                  <div class="w-10 h-10 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg flex items-center justify-center">
                    <el-icon class="text-white"><Trophy /></el-icon>
                  </div>
                  <div>
                    <h2 class="text-base font-bold text-gray-900">全网热点聚合</h2>
                    <p class="text-xs text-gray-500">{{ state.lastRunTime ? formatDate(state.lastRunTime) : '暂无更新' }}</p>
                  </div>
                </div>
                <span class="text-xs font-medium text-gray-500 bg-gray-100 px-3 py-1.5 rounded-full">
                  {{ state.hot_topics.length }} 条
                </span>
              </div>

              <!-- 筛选器 - 只保留平台和标签筛选 -->
              <div class="bg-gray-50 rounded-lg p-3 mb-4 space-y-3">
                <!-- 平台筛选 -->
                <div class="flex flex-col sm:flex-row sm:items-center gap-2">
                  <span class="text-xs font-medium text-gray-600 w-12">平台:</span>
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
                  <span class="text-xs font-medium text-gray-600 w-12">标签:</span>
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
                  <el-button size="small" @click="clearRankingFilters" :icon="Delete">清除筛选</el-button>
                </div>
              </div>

              <!-- 热点列表 -->
              <div v-if="loading" class="py-16 text-center">
                <el-icon class="is-loading text-4xl text-indigo-500 mb-3"><Loading /></el-icon>
                <p class="text-sm text-gray-500">数据加载中...</p>
              </div>

              <div v-else-if="state.hot_topics.length === 0" class="py-16 text-center">
                <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-xl flex items-center justify-center">
                  <el-icon class="text-3xl text-gray-400"><Trophy /></el-icon>
                </div>
                <h3 class="text-base font-semibold text-gray-700 mb-2">暂无热点数据</h3>
                <p class="text-sm text-gray-400 mb-4">点击右上角刷新按钮获取最新热点</p>
                <el-button v-if="isAdmin" type="primary" @click="handleRefresh" :icon="Refresh">
                  刷新热点
                </el-button>
              </div>

              <div v-else class="space-y-3">
                <div v-if="filteredRankingTopics.length === 0" class="py-8 text-center">
                  <p class="text-sm text-gray-500">没有符合筛选条件的热点</p>
                  <el-button size="small" @click="clearRankingFilters" class="mt-2">清除筛选</el-button>
                </div>
                <TopicCard
                  v-else
                  v-for="(topic, index) in filteredRankingTopics"
                  :key="index"
                  :topic="topic"
                  :index="index"
                  @generate="openGenerateDialog"
                />
              </div>
            </el-tab-pane>

            <!-- 分类新闻 Tab -->
            <el-tab-pane label="分类新闻" name="categories">
              <template #label>
                <div class="flex items-center space-x-2">
                  <el-icon class="text-indigo-500"><Grid /></el-icon>
                  <span class="font-semibold">分类新闻</span>
                </div>
              </template>

              <div class="py-3">
                <div class="flex items-center justify-between mb-4">
                  <p class="text-sm text-gray-500">按分类浏览各领域的最新热点资讯</p>
                  <el-button
                    v-if="isAdmin"
                    type="primary"
                    size="small"
                    @click="handleRefreshCategories"
                    :loading="isRefreshingCategories"
                    :icon="Refresh"
                  >
                    刷新分类热点
                  </el-button>
                </div>

                <!-- 分类卡片网格 -->
                <div v-if="categoriesList.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div
                    v-for="category in categoriesList"
                    :key="category.id"
                    class="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                    @click="selectCategory(category)"
                  >
                    <!-- 分类头部 -->
                    <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between" :style="{ backgroundColor: category.color + '15' }">
                      <div class="flex items-center space-x-2">
                        <span v-if="category.icon" class="text-2xl">{{ category.icon }}</span>
                        <h3 class="font-bold text-gray-900">{{ category.name }}</h3>
                      </div>
                      <el-icon class="text-gray-400"><Arrow-Right /></el-icon>
                    </div>

                    <!-- 分类内容预览 -->
                    <div class="p-4">
                      <div class="flex items-center justify-between mb-3">
                        <div class="flex flex-wrap gap-1">
                          <el-tag
                            v-for="keyword in category.keywords?.slice(0, 3)"
                            :key="keyword.id"
                            size="small"
                            type="info"
                          >{{ keyword.keyword }}</el-tag>
                          <span v-if="category.keywords?.length > 3" class="text-xs text-gray-400">+{{ category.keywords.length - 3 }}</span>
                        </div>
                      </div>

                      <!-- 该分类的热点数量 -->
                      <div class="flex items-center justify-between text-sm">
                        <span class="text-gray-500">相关热点</span>
                        <span class="font-medium text-gray-900">{{ getCategoryTopicCount(category.id) }} 条</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 空状态 -->
                <div v-else class="py-16 text-center">
                  <div class="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-xl flex items-center justify-center">
                    <el-icon class="text-3xl text-gray-400"><Grid /></el-icon>
                  </div>
                  <h3 class="text-base font-semibold text-gray-700 mb-2">暂无分类数据</h3>
                  <p class="text-sm text-gray-400 mb-4">请联系管理员初始化分类</p>
                </div>
              </div>

              <!-- 分类详情展开区域 -->
              <div v-if="selectedCategoryForDetail" class="mt-6 pt-6 border-t border-gray-200">
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center space-x-3">
                    <span v-if="selectedCategoryForDetail.icon" class="text-3xl">{{ selectedCategoryForDetail.icon }}</span>
                    <div>
                      <h3 class="text-lg font-bold text-gray-900">{{ selectedCategoryForDetail.name }}</h3>
                      <p class="text-xs text-gray-500">{{ selectedCategoryForDetail.description || '' }}</p>
                    </div>
                  </div>
                  <el-button size="small" @click="selectedCategoryForDetail = null" :icon="Close">关闭</el-button>
                </div>

                <!-- 该分类的热点列表 -->
                <div v-if="getCategoryTopics(selectedCategoryForDetail.id).length > 0" class="space-y-3">
                  <TopicCard
                    v-for="(topic, index) in getCategoryTopics(selectedCategoryForDetail.id)"
                    :key="index"
                    :topic="topic"
                    :index="index"
                    @generate="openGenerateDialog"
                  />
                </div>
                <div v-else class="py-8 text-center bg-gray-50 rounded-lg">
                  <p class="text-sm text-gray-500">该分类暂无热点数据</p>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </section>

      <!-- 右侧：AI 文案编辑器（桌面端固定，移动端在底部） -->
      <aside id="preview-section" class="lg:w-2/5 xl:w-1/3 lg:border-l lg:border-gray-200 lg:bg-gray-50">
        <div class="lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] lg:overflow-y-auto">
          <div class="p-4 lg:p-6">
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

              <!-- 内容区域 -->
              <div v-if="generatedContent" class="flex-1 overflow-hidden min-h-0">
                <!-- 预览模式 -->
                <div v-if="!isEditing" class="h-full overflow-y-auto p-3 sm:p-4 bg-gray-50" style="max-height: 50vh;">
                  <div v-html="parsedContent" class="prose prose-sm max-w-none prose-headings:font-bold prose-a:text-indigo-600"></div>
                </div>

                <!-- 编辑模式 -->
                <textarea
                  v-else
                  v-model="generatedContent"
                  class="h-full w-full p-3 sm:p-4 bg-white text-sm font-mono leading-relaxed resize-none focus:outline-none"
                  style="max-height: 50vh;"
                  placeholder="在此编辑文案内容..."
                ></textarea>
              </div>

              <!-- 加载状态 -->
              <div v-else-if="isGenerating" class="flex flex-col items-center justify-center py-12 sm:py-16 px-4 sm:px-6 flex-shrink-0 bg-gradient-to-b from-indigo-50 to-white" style="min-height: 320px;">
                <div class="relative mb-5 sm:mb-6">
                  <div class="w-16 h-16 sm:w-20 sm:h-20 bg-indigo-100 rounded-2xl flex items-center justify-center">
                    <el-icon class="text-indigo-600 text-3xl sm:text-4xl animate-pulse"><Magic-Stick /></el-icon>
                  </div>
                  <div class="absolute -top-1 -right-1 w-4 h-4 bg-indigo-400 rounded-full animate-bounce"></div>
                  <div class="absolute -bottom-1 -left-1 w-3 h-3 bg-indigo-300 rounded-full animate-bounce" style="animation-delay: 0.2s;"></div>
                </div>

                <el-tag size="small" type="primary" class="mb-3">{{ getPlatformLabel(generatingPlatform) }}</el-tag>

                <h3 class="text-base sm:text-lg font-semibold text-gray-800 mb-2">AI 正在创作中</h3>
                <p class="text-xs sm:text-sm text-gray-500 text-center mb-4">{{ currentLoadingStep }}</p>

                <div class="w-48 sm:w-56 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full animate-pulse" style="width: 70%;"></div>
                </div>

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

              <!-- 底部操作栏 -->
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
            <div v-if="isAdmin" class="bg-gray-900 rounded-xl overflow-hidden mt-4">
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

            <!-- 任务统计（仅管理员可见） -->
            <div v-if="isAdmin" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden mt-4">
              <div class="flex items-center justify-between px-4 py-2.5 bg-gray-50 border-b border-gray-200">
                <div class="flex items-center space-x-2">
                  <el-icon class="text-indigo-500 text-sm"><Data-Analysis /></el-icon>
                  <h3 class="text-xs font-semibold text-gray-700">任务统计</h3>
                </div>
                <span class="text-[10px] text-gray-500">实时数据</span>
              </div>
              <div class="p-3">
                <!-- 三阶段任务统计 -->
                <div class="grid grid-cols-3 gap-3 mb-3">
                  <!-- 爬虫统计 -->
                  <div class="text-center p-2 bg-blue-50 rounded-lg">
                    <div class="text-lg font-bold text-blue-600">{{ state.last_scraper_count }}</div>
                    <div class="text-[10px] text-gray-500">上次爬取</div>
                  </div>
                  <!-- 分析统计 -->
                  <div class="text-center p-2 bg-purple-50 rounded-lg">
                    <div class="text-lg font-bold text-purple-600">{{ state.last_analyzer_count }}</div>
                    <div class="text-[10px] text-gray-500">上次分析</div>
                  </div>
                  <!-- 精选统计 -->
                  <div class="text-center p-2 bg-orange-50 rounded-lg">
                    <div class="text-lg font-bold text-orange-600">{{ state.last_selector_count }}</div>
                    <div class="text-[10px] text-gray-500">上次精选</div>
                  </div>
                </div>
                <!-- 爬取详情 -->
                <div class="grid grid-cols-2 gap-3 pt-3 border-t border-gray-100">
                  <div class="text-center p-2 bg-rose-50 rounded-lg">
                    <div class="text-base font-bold text-rose-600">{{ state.last_hot_ranking_count || 0 }}</div>
                    <div class="text-[10px] text-gray-500">热榜新闻</div>
                  </div>
                  <div class="text-center p-2 bg-teal-50 rounded-lg">
                    <div class="text-base font-bold text-teal-600">{{ state.last_category_count || 0 }}</div>
                    <div class="text-[10px] text-gray-500">分类新闻</div>
                  </div>
                </div>
                <div v-if="task_stats && Object.keys(task_stats).length > 0" class="mt-3 pt-3 border-t border-gray-100">
                  <div class="flex justify-between text-xs">
                    <span class="text-gray-500">待分析新闻</span>
                    <span class="font-medium text-gray-900">{{ pendingAnalysisCount }} 条</span>
                  </div>
                  <div class="flex justify-between text-xs mt-1">
                    <span class="text-gray-500">今日爬取</span>
                    <span class="font-medium text-gray-900">{{ todayScrapedCount }} 条</span>
                  </div>
                </div>
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

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Edit, View, CopyDocument, Delete, MagicStick, EditPen, Monitor, Iphone, Refresh, Document, Clock, DataAnalysis, ArrowDown, Trophy, Loading, User, SwitchButton, FullScreen, Menu, Grid, ArrowRight, Close } from '@element-plus/icons-vue'
import { status, content, categories } from '@/api'
import { useAuth } from '@/composables/useAuth'
import { useSSE } from '@/composables/useSSE'
import TopicCard from '@/components/TopicCard.vue'
import GenerateDialog from '@/components/GenerateDialog.vue'
import { marked } from 'marked'

const router = useRouter()
const { isAuthenticated, isAdmin, username, logout } = useAuth()

// UI 状态
const loading = ref(false)
const showLogDrawer = ref(false)
const showGenerateDialog = ref(false)
const showPreviewDialog = ref(false)
const showLogsDialog = ref(false)
const previewMode = ref('desktop')
const activeTab = ref('rankings')
const isRefreshingCategories = ref(false)

// 筛选状态
const selectedSource = ref(null)
const selectedTag = ref(null)
const selectedCategoryForDetail = ref(null)

// 生成状态
const isGenerating = ref(false)
const generatingPlatform = ref('')
const generatingStep = ref(0)
const stepInterval = ref(null)
const justGenerated = ref(false)
const generatedContent = ref('')
const isEditing = ref(false)
const selectedTopic = ref(null)
const windowWidth = ref(window.innerWidth)

// 数据状态
const categoriesList = ref([])

const state = reactive({
  isRunning: false,
  lastRunTime: '',
  nextRunTime: '',
  hot_topics: [],
  logs: [],
  // 三阶段任务状态
  task_stages: {
    scraper_running: false,
    analyzer_running: false,
    selector_running: false
  },
  // 任务统计
  task_stats: {},
  last_scraper_count: 0,
  last_analyzer_count: 0,
  last_selector_count: 0
})

// 计算属性
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

// 热点排行榜的筛选（不包含分类筛选）
const filteredRankingTopics = computed(() => {
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

// 当前运行阶段
const currentRunningStage = computed(() => {
  if (state.task_stages.scraper_running) return { name: '爬虫中', icon: '🕷️', color: 'blue' }
  if (state.task_stages.analyzer_running) return { name: 'AI 分析中', icon: '🤖', color: 'purple' }
  if (state.task_stages.selector_running) return { name: '精选中', icon: '🎯', color: 'orange' }
  if (state.isRunning) return { name: '运行中', icon: '⚡', color: 'green' }
  return null
})

// 待分析新闻数量
const pendingAnalysisCount = computed(() => {
  return state.task_stats?.pending_count || 0
})

// 今日爬取数量
const todayScrapedCount = computed(() => {
  return state.task_stats?.today_count || 0
})

// 方法
const getCategoryTopicCount = (categoryId) => {
  return state.hot_topics.filter(t => t.category_id === categoryId).length
}

const getCategoryTopics = (categoryId) => {
  return state.hot_topics.filter(t => t.category_id === categoryId)
}

const selectCategory = (category) => {
  selectedCategoryForDetail.value = category
  // 滚动到分类详情
  nextTick(() => {
    const el = document.getElementById('preview-section')
    if (el) {
      const y = el.getBoundingClientRect().top + window.scrollY - 80
      window.scrollTo({ top: y, behavior: 'smooth' })
    }
  })
}

const clearRankingFilters = () => {
  selectedSource.value = null
  selectedTag.value = null
}

const scrollToTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const goToHistory = () => {
  router.push('/history')
}

const goToMyArticles = () => {
  router.push('/my-articles')
}

const formatDate = (dateStr) => {
  if (!dateStr || dateStr === 'undefined' || dateStr === 'None') return '暂无更新'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (isNaN(date.getTime())) return '暂无更新'
  if (minutes < 1) return '刚刚更新'
  if (minutes < 60) return `${minutes} 分钟前更新`
  if (hours < 24) return `${hours} 小时前更新`
  if (days < 7) return `${days} 天前更新`
  return dateStr.split(' ')[1] + ' 更新'
}

const fetchStatus = async () => {
  try {
    // 根据认证状态选择不同的端点
    const data = isAuthenticated.value
      ? await status.getStatus()
      : await status.getPublicStatus()

    if (isAuthenticated.value) {
      // 认证用户获取完整状态
      state.isRunning = data.state.isRunning
      state.lastRunTime = data.state.lastRunTime
      state.nextRunTime = data.state.nextRunTime
      if (JSON.stringify(data.state.hot_topics) !== JSON.stringify(state.hot_topics)) {
        state.hot_topics = data.state.hot_topics || []
      }
      if (data.state.logs) state.logs = data.state.logs
      // 三阶段任务状态
      if (data.state.task_stages) {
        state.task_stages = data.state.task_stages
      }
      // 任务统计
      if (data.state.task_stats) {
        state.task_stats = data.state.task_stats
      }
      state.last_scraper_count = data.state.last_scraper_count || 0
      state.last_analyzer_count = data.state.last_analyzer_count || 0
      state.last_selector_count = data.state.last_selector_count || 0
    } else {
      // 未认证用户只获取公开状态
      state.isRunning = data.isRunning
      state.lastRunTime = data.lastRunTime
      state.hot_topics = data.hot_topics || []
      // 三阶段任务状态（公开）
      if (data.task_stages) {
        state.task_stages = data.task_stages
      }
    }
  } catch (e) {
    console.error(e)
  }
}

// SSE connection
const setupSSE = () => {
  const baseURL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:3000'
  const sse = useSSE()

  // Register event handlers
  sse.on('status', (data) => {
    state.isRunning = data.isRunning
    state.lastRunTime = data.lastRunTime
    state.nextRunTime = data.nextRunTime
    // 三阶段任务状态
    if (data.task_stages) {
      state.task_stages = data.task_stages
    }
    // 任务统计（仅管理员）
    if (data.task_stats) {
      state.task_stats = data.task_stats
    }
    if (data.last_scraper_count !== undefined) {
      state.last_scraper_count = data.last_scraper_count
    }
    if (data.last_analyzer_count !== undefined) {
      state.last_analyzer_count = data.last_analyzer_count
    }
    if (data.last_selector_count !== undefined) {
      state.last_selector_count = data.last_selector_count
    }
    if (data.last_hot_ranking_count !== undefined) {
      state.last_hot_ranking_count = data.last_hot_ranking_count
    }
    if (data.last_category_count !== undefined) {
      state.last_category_count = data.last_category_count
    }
  })

  sse.on('log', (log) => {
    state.logs.push(log)
  })

  sse.on('topics', (topics) => {
    state.hot_topics = topics
  })

  // Connect to SSE endpoint
  sse.connect(`${baseURL}/events`, {
    onOpen: () => {
      console.log('SSE 连接已建立')
    },
    onError: (error) => {
      console.error('SSE 连接错误:', error)
    }
  })

  return sse
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

const handleRefreshCategories = async () => {
  try {
    isRefreshingCategories.value = true
    await categories.refreshCategoryTopics()
    ElMessage.success('分类热点刷新任务已启动')
  } catch (e) {
    ElMessage.error('启动失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    isRefreshingCategories.value = false
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

  generatingPlatform.value = platform
  generatingStep.value = 0

  stepInterval.value = setInterval(() => {
    generatingStep.value = (generatingStep.value + 1) % loadingSteps.value.length
  }, 2500)

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
    case 'categories':
      router.push('/categories')
      break
    case 'logs':
      showLogDrawer.value = true
      break
    case 'history':
      goToHistory()
      break
    case 'my-articles':
      router.push('/my-articles')
      break
    case 'logout':
      logout()
      break
  }
}

const goToLogin = () => {
  router.push('/login')
}

const fetchCategories = async () => {
  try {
    const res = await categories.getCategories()
    categoriesList.value = res.categories || []
  } catch (e) {
    console.error('Failed to fetch categories:', e)
  }
}

// 窗口大小监听
window.addEventListener('resize', () => {
  windowWidth.value = window.innerWidth
})

// 生命周期
let sse = null

onMounted(() => {
  fetchCategories()
  fetchStatus()
  sse = setupSSE()
})

onUnmounted(() => {
  if (sse) {
    sse.disconnect()
  }
})
</script>

<style scoped>
:deep(.el-tabs__header) {
  margin: 0;
}

:deep(.el-tabs__nav-wrap::after) {
  display: none;
}

:deep(.el-tabs__item) {
  padding: 0 20px;
}
</style>
