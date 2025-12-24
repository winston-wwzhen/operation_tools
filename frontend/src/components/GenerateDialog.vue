<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="AI 创作设置"
    :width="dialogWidth"
    align-center
    class="rounded-lg"
  >
    <div v-if="topic" class="mb-4 sm:mb-6">
      <p class="text-xs text-gray-500 mb-1">当前选定热点</p>
      <div class="bg-gray-50 p-2.5 sm:p-3 rounded text-sm font-medium text-gray-800 border-l-4 border-indigo-500 line-clamp-2">
        {{ topic.title }}
      </div>
    </div>

    <div class="mb-4 sm:mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">目标平台风格</label>
      <div class="grid grid-cols-1 gap-2 sm:gap-3">
        <div
          @click="selectedPlatform = 'wechat'"
          class="border rounded-lg p-3 cursor-pointer transition-colors flex items-center justify-between"
          :class="selectedPlatform === 'wechat' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-center">
            <span class="text-xl mr-2"></span>
            <div>
              <div class="font-bold text-sm text-gray-800">微信公众号</div>
              <div class="text-xs text-gray-500">深度长文 / HTML排版</div>
            </div>
          </div>
          <el-radio v-model="selectedPlatform" value="wechat" class="!mr-0"></el-radio>
        </div>

        <div
          @click="selectedPlatform = 'xiaohongshu'"
          class="border rounded-lg p-3 cursor-pointer transition-colors flex items-center justify-between"
          :class="selectedPlatform === 'xiaohongshu' ? 'border-pink-500 bg-pink-50' : 'border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-center">
            <span class="text-xl mr-2"></span>
            <div>
              <div class="font-bold text-sm text-gray-800">小红书</div>
              <div class="text-xs text-gray-500">Emoji / 种草 / 标签</div>
            </div>
          </div>
          <el-radio v-model="selectedPlatform" value="xiaohongshu" class="!mr-0"></el-radio>
        </div>

        <div
          @click="selectedPlatform = 'zhihu'"
          class="border rounded-lg p-3 cursor-pointer transition-colors flex items-center justify-between"
          :class="selectedPlatform === 'zhihu' ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-center">
            <span class="text-xl mr-2"></span>
            <div>
              <div class="font-bold text-sm text-gray-800">知乎</div>
              <div class="text-xs text-gray-500">理性客观 / Markdown</div>
            </div>
          </div>
          <el-radio v-model="selectedPlatform" value="zhihu" class="!mr-0"></el-radio>
        </div>

        <div
          @click="selectedPlatform = 'toutiao'"
          class="border rounded-lg p-3 cursor-pointer transition-colors flex items-center justify-between"
          :class="selectedPlatform === 'toutiao' ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-center">
            <span class="text-xl mr-2"></span>
            <div>
              <div class="font-bold text-sm text-gray-800">今日头条</div>
              <div class="text-xs text-gray-500">爆款标题 / 叙事强</div>
            </div>
          </div>
          <el-radio v-model="selectedPlatform" value="toutiao" class="!mr-0"></el-radio>
        </div>
      </div>
    </div>

    <!-- 保存选项 -->
    <div class="mb-4 p-3 bg-indigo-50 rounded-lg border border-indigo-200">
      <div class="flex items-center mb-2">
        <el-icon class="text-indigo-600 mr-1"><Folder-Opened /></el-icon>
        <span class="text-sm font-medium text-indigo-900">保存选项</span>
      </div>
      <el-checkbox v-model="saveArticle">保存到我的文章库</el-checkbox>
      <el-checkbox
        v-if="saveArticle"
        v-model="makePublic"
        class="ml-4"
      >
        生成分享链接（公开文章）
      </el-checkbox>
    </div>

    <!-- 未登录提示 -->
    <div v-if="!isAuthenticated" class="mb-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
      <p class="text-xs text-yellow-800 flex items-center">
        <el-icon class="mr-1"><Warning-Filled /></el-icon>
        生成文章需要先登录，点击"开始创作"后将跳转至登录页面
      </p>
    </div>

    <template #footer>
      <div class="flex gap-2">
        <el-button @click="$emit('update:modelValue', false)" class="flex-1">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="generating" class="flex-1 font-bold">
          开始创作
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { useAuth } from '@/composables/useAuth'

export default {
  name: 'GenerateDialog',
  props: {
    modelValue: Boolean,
    topic: Object,
    generating: Boolean
  },
  emits: ['update:modelValue', 'confirm'],
  setup(props, { emit }) {
    const { isAuthenticated } = useAuth()
    const selectedPlatform = ref('wechat')
    const saveArticle = ref(false)
    const makePublic = ref(false)
    const windowWidth = ref(window.innerWidth)

    const dialogWidth = computed(() => windowWidth.value < 640 ? '90%' : '500px')

    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth
    })

    // 监听对话框打开，重置保存选项
    watch(() => props.modelValue, (newVal) => {
      if (newVal && props.topic) {
        if (props.topic.source.includes('小红书')) selectedPlatform.value = 'xiaohongshu'
        else if (props.topic.source.includes('知乎')) selectedPlatform.value = 'zhihu'
        else if (props.topic.source.includes('头条')) selectedPlatform.value = 'toutiao'
        else selectedPlatform.value = 'wechat'
        // 如果已登录，默认勾选保存
        saveArticle.value = isAuthenticated.value
        makePublic.value = false
      }
    })

    const handleConfirm = () => {
      emit('confirm', selectedPlatform.value, {
        save: saveArticle.value,
        public: makePublic.value
      })
    }

    return {
      selectedPlatform,
      saveArticle,
      makePublic,
      dialogWidth,
      handleConfirm,
      isAuthenticated
    }
  }
}
</script>
