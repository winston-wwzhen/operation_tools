<template>
  <div class="flex-grow flex flex-col min-h-screen bg-gray-50">
    <!-- 头部导航 -->
    <header class="bg-white shadow-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center space-x-2 sm:space-x-3">
          <el-button @click="goBack" circle size="small" class="!w-8 !h-8">
            <el-icon><Arrow-Left /></el-icon>
          </el-button>
          <div class="flex items-center space-x-2 sm:space-x-3">
            <el-icon class="text-indigo-600 text-xl sm:text-2xl"><Data-Analysis /></el-icon>
            <h1 class="text-lg sm:text-xl font-bold text-gray-900">分类管理</h1>
          </div>
        </div>
        <div class="flex items-center space-x-2">
          <el-button type="success" @click="handleInitDefaults" :loading="initializing">
            <el-icon class="mr-1"><Refresh /></el-icon>
            初始化默认分类
          </el-button>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon class="mr-1"><Plus /></el-icon>
            添加分类
          </el-button>
        </div>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
      <!-- 加载状态 -->
      <div v-if="loading" class="py-12 text-center text-gray-400">
        <el-icon class="is-loading text-3xl mb-2"><Loading /></el-icon>
        <p class="text-sm">加载中...</p>
      </div>

      <!-- 分类卡片列表 -->
      <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="category in categories"
          :key="category.id"
          class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
        >
          <!-- 分类头部 -->
          <div class="px-4 py-3 border-b border-gray-100 flex items-center justify-between" :style="{ backgroundColor: category.color + '10' }">
            <div class="flex items-center space-x-2">
              <span v-if="category.icon" class="text-2xl">{{ category.icon }}</span>
              <div>
                <h3 class="font-bold text-gray-900">{{ category.name }}</h3>
                <p class="text-xs text-gray-500">{{ category.description || '无描述' }}</p>
              </div>
            </div>
            <el-tag :type="category.is_active ? 'success' : 'info'" size="small">
              {{ category.is_active ? '启用' : '禁用' }}
            </el-tag>
          </div>

          <!-- 分类内容 -->
          <div class="p-4 space-y-3">
            <!-- 关键词 -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-gray-600">关键词</span>
                <el-button size="small" text @click="editKeywords(category)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </div>
              <div class="flex flex-wrap gap-1">
                <el-tag v-if="category.keywords && category.keywords.length > 0" size="small" type="info">
                  {{ category.keywords.slice(0, 3).map(k => k.keyword).join(', ') }}
                  <span v-if="category.keywords.length > 3">等{{ category.keywords.length }}个</span>
                </el-tag>
                <span v-else class="text-xs text-gray-400">暂无关键词</span>
              </div>
            </div>

            <!-- 平台配置 -->
            <div>
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium text-gray-600">平台配置</span>
                <el-button size="small" text @click="editPlatforms(category)">
                  <el-icon><Edit /></el-icon>
                </el-button>
              </div>
              <div class="flex flex-wrap gap-1">
                <el-tag
                  v-for="platform in category.platforms"
                  :key="platform.platform"
                  size="small"
                  :type="platform.is_enabled ? 'success' : 'info'"
                >
                  {{ getPlatformLabel(platform.platform) }}
                </el-tag>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="flex items-center justify-between pt-2 border-t border-gray-100">
              <el-button size="small" @click="editCategory(category)">
                <el-icon class="mr-1"><Edit /></el-icon>编辑
              </el-button>
              <el-button size="small" type="danger" text @click="confirmDelete(category)">
                <el-icon class="mr-1"><Delete /></el-icon>删除
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 创建/编辑分类对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingCategory ? '编辑分类' : '添加分类'"
      width="500px"
      destroy-on-close
    >
      <el-form :model="categoryForm" label-width="100px">
        <el-form-item label="分类名称" required>
          <el-input v-model="categoryForm.name" placeholder="例如：AI科技" />
        </el-form-item>
        <el-form-item label="标识" required>
          <el-input v-model="categoryForm.slug" placeholder="例如：ai-tech" />
          <div class="text-xs text-gray-500 mt-1">URL友好的唯一标识</div>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="categoryForm.description" type="textarea" rows="2" placeholder="分类描述" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="categoryForm.icon" placeholder="例如：🤖" maxlength="2" />
          <div class="text-xs text-gray-500 mt-1">推荐使用 emoji 图标</div>
        </el-form-item>
        <el-form-item label="主题色">
          <el-input v-model="categoryForm.color" placeholder="例如：#6366f1" />
          <div class="text-xs text-gray-500 mt-1">十六进制颜色值</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="categoryForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="categoryForm.sort_order" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveCategory" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 关键词编辑对话框 -->
    <el-dialog
      v-model="showKeywordsDialog"
      title="编辑关键词"
      width="500px"
      destroy-on-close
    >
      <div v-if="currentCategory">
        <p class="text-sm text-gray-600 mb-3">当前分类: <strong>{{ currentCategory.name }}</strong></p>
        <el-form label-width="80px">
          <el-form-item label="关键词">
            <el-select
              v-model="tempKeywords"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入关键词后按回车添加"
              class="w-full"
            >
              <el-option
                v-for="keyword in tempKeywords"
                :key="keyword"
                :label="keyword"
                :value="keyword"
              />
            </el-select>
            <div class="text-xs text-gray-500 mt-1">
              输入关键词后按回车添加，可添加多个关键词
            </div>
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showKeywordsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveKeywords" :loading="saving">确定</el-button>
      </template>
    </el-dialog>

    <!-- 平台配置对话框 -->
    <el-dialog
      v-model="showPlatformsDialog"
      title="配置平台"
      width="400px"
      destroy-on-close
    >
      <div v-if="currentCategory">
        <p class="text-sm text-gray-600 mb-3">当前分类: <strong>{{ currentCategory.name }}</strong></p>
        <div class="space-y-2">
          <el-checkbox
            v-for="platform in allPlatforms"
            :key="platform.value"
            v-model="tempPlatforms[platform.value]"
            :label="platform.label"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="showPlatformsDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSavePlatforms" :loading="saving">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, Plus, Edit, Delete, Loading, Refresh, DataAnalysis
} from '@element-plus/icons-vue'
import { categories as categoriesApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const saving = ref(false)
const initializing = ref(false)
const categoriesList = ref([])

const showCreateDialog = ref(false)
const showKeywordsDialog = ref(false)
const showPlatformsDialog = ref(false)
const editingCategory = ref(null)
const currentCategory = ref(null)

const categoryForm = reactive({
  name: '',
  slug: '',
  description: '',
  icon: '',
  color: '',
  is_active: true,
  sort_order: 0
})

const tempKeywords = ref([])
const tempPlatforms = ref({})

const allPlatforms = [
  { value: 'weibo', label: '微博' },
  { value: 'zhihu', label: '知乎' },
  { value: 'douyin', label: '抖音' },
  { value: 'xiaohongshu', label: '小红书' },
  { value: 'toutiao', label: '头条' }
]

const categories = computed(() => {
  return categoriesList.value.map(cat => ({
    ...cat,
    keywords: cat.keywords || [],
    platforms: cat.platforms || allPlatforms.map(p => ({
      platform: p.value,
      is_enabled: true
    }))
  }))
})

// 获取分类列表
const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await categoriesApi.getCategories({ include_inactive: true })
    const cats = res.categories || []
    // 获取每个分类的详情（包含关键词和平台）
    const detailPromises = cats.map(cat => categoriesApi.getCategory(cat.id))
    const details = await Promise.all(detailPromises)
    categoriesList.value = details
  } catch (e) {
    ElMessage.error('加载失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 初始化默认分类
const handleInitDefaults = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要初始化默认分类吗？已存在的分类将被跳过。',
      '确认操作',
      { type: 'warning' }
    )
    initializing.value = true
    await categoriesApi.initDefaultCategories()
    ElMessage.success('初始化成功')
    await fetchCategories()
  } catch (e) {
    if (e !== 'cancel') {
      ElMessage.error('初始化失败')
    }
  } finally {
    initializing.value = false
  }
}

// 编辑分类
const editCategory = (category) => {
  editingCategory.value = category
  Object.assign(categoryForm, {
    name: category.name,
    slug: category.slug,
    description: category.description || '',
    icon: category.icon || '',
    color: category.color || '',
    is_active: category.is_active,
    sort_order: category.sort_order || 0
  })
  showCreateDialog.value = true
}

// 保存分类
const handleSaveCategory = async () => {
  if (!categoryForm.name || !categoryForm.slug) {
    ElMessage.warning('请填写分类名称和标识')
    return
  }

  saving.value = true
  try {
    if (editingCategory.value) {
      await categoriesApi.updateCategory(editingCategory.value.id, categoryForm)
      ElMessage.success('更新成功')
    } else {
      await categoriesApi.createCategory(categoryForm)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    editingCategory.value = null
    resetCategoryForm()
    await fetchCategories()
  } catch (e) {
    ElMessage.error('保存失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 编辑关键词
const editKeywords = (category) => {
  currentCategory.value = category
  tempKeywords.value = category.keywords.map(k => k.keyword)
  showKeywordsDialog.value = true
}

// 保存关键词
const handleSaveKeywords = async () => {
  if (!currentCategory.value) return

  saving.value = true
  try {
    await categoriesApi.updateKeywords(currentCategory.value.id, tempKeywords.value)
    ElMessage.success('更新成功')
    showKeywordsDialog.value = false
    await fetchCategories()
  } catch (e) {
    ElMessage.error('更新失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 编辑平台配置
const editPlatforms = (category) => {
  currentCategory.value = category
  tempPlatforms.value = {}
  allPlatforms.forEach(p => {
    const platform = category.platforms.find(pl => pl.platform === p.value)
    tempPlatforms.value[p.value] = platform ? platform.is_enabled : false
  })
  showPlatformsDialog.value = true
}

// 保存平台配置
const handleSavePlatforms = async () => {
  if (!currentCategory.value) return

  saving.value = true
  try {
    const enabledPlatforms = allPlatforms
      .filter(p => tempPlatforms.value[p.value])
      .map(p => p.value)
    await categoriesApi.updatePlatformConfig(currentCategory.value.id, enabledPlatforms)
    ElMessage.success('更新成功')
    showPlatformsDialog.value = false
    await fetchCategories()
  } catch (e) {
    ElMessage.error('更新失败: ' + (e.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 删除分类
const confirmDelete = (category) => {
  ElMessageBox.confirm(
    `确定要删除分类"${category.name}"吗？此操作不可撤销。`,
    '确认删除',
    { type: 'warning' }
  ).then(async () => {
    try {
      await categoriesApi.deleteCategory(category.id)
      ElMessage.success('删除成功')
      await fetchCategories()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 重置表单
const resetCategoryForm = () => {
  Object.assign(categoryForm, {
    name: '',
    slug: '',
    description: '',
    icon: '',
    color: '',
    is_active: true,
    sort_order: 0
  })
}

// 获取平台标签
const getPlatformLabel = (platform) => {
  const found = allPlatforms.find(p => p.value === platform)
  return found ? found.label : platform
}

// 返回首页
const goBack = () => {
  router.push('/')
}

onMounted(fetchCategories)
</script>

<style scoped>
:deep(.el-checkbox__label) {
  color: var(--el-text-color-regular);
}
</style>
