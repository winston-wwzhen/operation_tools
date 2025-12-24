<template>
  <div class="topic-card bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
    <div class="flex items-stretch">
      <!-- 排名徽章 -->
      <div class="flex-shrink-0 w-11 flex items-center justify-center py-3" :class="getRankBgClass()">
        <span class="text-base font-bold" :class="getRankTextClass()">{{ displayIndex }}</span>
      </div>

      <!-- 内容区 -->
      <div class="flex-grow p-3 min-w-0">
        <div class="flex flex-col sm:flex-row justify-between items-start gap-3">
          <div class="flex-grow min-w-0">
            <!-- 来源和标题 -->
            <div class="flex items-start gap-2 mb-2">
              <span :class="getSourceClass(topic.source)" class="source-tag shrink-0 text-[10px] px-2 py-0.5 rounded font-medium">
                {{ topic.source }}
              </span>
              <h3
                class="text-sm font-semibold text-gray-800 leading-snug cursor-pointer hover:text-indigo-600 transition-colors line-clamp-2"
                @click="openLink"
              >
                {{ topic.title }}
              </h3>
            </div>

            <!-- 标签 -->
            <div class="flex flex-wrap gap-1.5 mb-2" v-if="topic.tags && topic.tags.length">
              <span
                v-for="tag in topic.tags.slice(0, 5)"
                :key="tag"
                class="text-[10px] text-gray-600 bg-gray-100 px-2 py-0.5 rounded"
              >
                #{{ tag }}
              </span>
            </div>

            <!-- AI 点评 -->
            <div v-if="topic.ai_comment" class="flex items-start gap-2 bg-amber-50 rounded-lg p-2">
              <el-icon class="text-amber-500 text-sm mt-0.5"><MagicStick /></el-icon>
              <p class="text-xs text-gray-700 leading-relaxed">{{ topic.ai_comment }}</p>
            </div>
          </div>

          <!-- 右侧操作区 -->
          <div class="flex sm:flex-col items-center justify-between gap-2 pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-100 sm:border-none w-full sm:w-auto">
            <!-- AI 评分 -->
            <div v-if="topic.ai_score" class="flex items-center gap-1.5 px-2.5 py-1 bg-indigo-100 rounded-full">
              <el-icon class="text-indigo-500 text-sm"><Trophy /></el-icon>
              <span class="text-sm font-semibold text-indigo-700">{{ topic.ai_score }}</span>
            </div>

            <!-- 生成按钮 -->
            <el-button type="primary" size="small" @click="$emit('generate', topic)">
              <el-icon><EditPen /></el-icon>
              <span class="hidden sm:inline ml-1">生成</span>
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Trophy, MagicStick, EditPen } from '@element-plus/icons-vue'

export default {
  name: 'TopicCard',
  components: { Trophy, MagicStick, EditPen },
  props: {
    topic: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      default: 0
    }
  },
  emits: ['generate'],
  computed: {
    displayIndex() {
      return this.index + 1
    }
  },
  methods: {
    openLink() {
      if (this.topic.link) window.open(this.topic.link, '_blank')
    },
    getRankBgClass() {
      const idx = this.index
      if (idx === 0) return 'bg-yellow-100'
      if (idx === 1) return 'bg-gray-200'
      if (idx === 2) return 'bg-orange-100'
      return 'bg-gray-100'
    },
    getRankTextClass() {
      const idx = this.index
      if (idx === 0) return 'text-yellow-700'
      if (idx === 1) return 'text-gray-700'
      if (idx === 2) return 'text-orange-700'
      return 'text-gray-600'
    },
    getSourceClass(source) {
      if (!source) return 'bg-gray-100 text-gray-600'
      if (source.includes('微博')) return 'source-weibo'
      if (source.includes('百度')) return 'source-baidu'
      if (source.includes('知乎')) return 'source-zhihu'
      if (source.includes('抖音')) return 'source-douyin'
      if (source.includes('小红书')) return 'source-xiaohongshu'
      if (source.includes('头条')) return 'source-toutiao'
      return 'bg-gray-100 text-gray-600'
    }
  }
}
</script>

<style scoped>
.topic-card {
  position: relative;
}

.source-weibo {
  background: #ff8200;
  color: white;
}

.source-baidu {
  background: #2932e1;
  color: white;
}

.source-zhihu {
  background: #0084ff;
  color: white;
}

.source-douyin {
  background: #000000;
  color: white;
}

.source-xiaohongshu {
  background: #ff2442;
  color: white;
}

.source-toutiao {
  background: #f85959;
  color: white;
}

.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
