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

export default {
  name: 'GenerateDialog',
  props: {
    modelValue: Boolean,
    topic: Object,
    generating: Boolean
  },
  emits: ['update:modelValue', 'confirm'],
  setup(props, { emit }) {
    const selectedPlatform = ref('wechat')
    const windowWidth = ref(window.innerWidth)

    const dialogWidth = computed(() => windowWidth.value < 640 ? '90%' : '500px')

    window.addEventListener('resize', () => {
      windowWidth.value = window.innerWidth
    })

    watch(() => props.modelValue, (newVal) => {
      if (newVal && props.topic) {
        if (props.topic.source.includes('小红书')) selectedPlatform.value = 'xiaohongshu'
        else if (props.topic.source.includes('知乎')) selectedPlatform.value = 'zhihu'
        else if (props.topic.source.includes('头条')) selectedPlatform.value = 'toutiao'
        else selectedPlatform.value = 'wechat'
      }
    })

    const handleConfirm = () => {
      emit('confirm', selectedPlatform.value)
    }

    return {
      selectedPlatform,
      dialogWidth,
      handleConfirm
    }
  }
}
</script>
