<template>
  <div
    class="topic-card bg-white rounded-lg shadow-sm p-3 sm:p-5 border-l-4 relative overflow-hidden"
    :class="getHeatColorClass(topic.heat)"
  >
    <div class="flex flex-col sm:flex-row justify-between items-start gap-2 sm:gap-4">
      <div class="flex-grow min-w-0 w-full">
        <div class="flex items-start gap-2 mb-1">
          <span :class="getSourceClass(topic.source)" class="source-tag mt-0.5 shrink-0">
            {{ topic.source }}
          </span>
          <h3
            class="text-base sm:text-lg font-bold text-gray-800 leading-snug cursor-pointer active:text-indigo-600 sm:hover:text-indigo-600 line-clamp-2"
            @click="openLink"
          >
            {{ topic.title }}
          </h3>
        </div>

        <div class="flex flex-wrap gap-1.5 mt-2 px-1" v-if="topic.tags && topic.tags.length">
          <span
            v-for="tag in topic.tags"
            :key="tag"
            class="text-[10px] sm:text-xs text-gray-500 bg-gray-50 border border-gray-100 px-1.5 py-0.5 rounded"
          >
            #{{ tag }}
          </span>
        </div>

        <div v-if="topic.comment" class="topic-comment">
          <span class="font-bold text-indigo-500 mr-1 text-xs">AI:</span>
          {{ topic.comment }}
        </div>
      </div>

      <div class="flex sm:flex-col items-center justify-between sm:justify-start w-full sm:w-auto mt-2 sm:mt-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-gray-50 sm:border-none gap-2">
        <div class="flex items-center sm:block text-left sm:text-center">
          <span class="text-xs text-gray-400 mr-1 sm:mr-0 sm:block">热度</span>
          <span class="text-sm sm:text-xl font-black text-gray-700 font-mono">{{ topic.heat }}</span>
        </div>
        <el-button type="primary" size="small" plain class="!px-4 !h-8" @click="$emit('generate', topic)">
          <el-icon class="mr-1"><Edit /></el-icon> 生成
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TopicCard',
  props: {
    topic: {
      type: Object,
      required: true
    }
  },
  emits: ['generate'],
  methods: {
    openLink() {
      if (this.topic.link) window.open(this.topic.link, '_blank')
    },
    getHeatColorClass(heat) {
      if (heat >= 90) return 'border-l-red-500'
      if (heat >= 80) return 'border-l-orange-500'
      if (heat >= 60) return 'border-l-yellow-500'
      return 'border-l-blue-500'
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
