<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="发布到微信公众号"
    :width="dialogWidth"
    align-center
    class="rounded-lg"
  >
    <div v-if="article" class="mb-4 sm:mb-6">
      <p class="text-xs text-gray-500 mb-1">即将发布</p>
      <div class="bg-gray-50 p-3 rounded text-sm font-medium text-gray-800 border-l-4 border-indigo-500">
        {{ article.title }}
      </div>
    </div>

    <!-- 公众号选择 -->
    <div class="mb-4 sm:mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">选择公众号</label>
      <el-select
        v-model="selectedAccountId"
        placeholder="请选择公众号"
        class="w-full"
        :loading="loadingAccounts"
      >
        <el-option
          v-for="account in accounts"
          :key="account.id"
          :label="account.account_name || account.nickname || account.app_id"
          :value="account.id"
        >
          <div class="flex items-center justify-between w-full">
            <span>{{ account.account_name || account.nickname || account.app_id }}</span>
            <el-tag v-if="!account.is_active" type="info" size="small" class="ml-2">未激活</el-tag>
          </div>
        </el-option>
      </el-select>
      <div v-if="accounts.length === 0" class="mt-2">
        <div class="text-xs text-gray-500 mb-2">暂无绑定公众号</div>
        <el-button size="small" type="primary" @click="showBindDialog = true">
          <el-icon class="mr-1"><Plus /></el-icon>
          绑定公众号
        </el-button>
      </div>
      <div v-else class="flex justify-end mt-2">
        <el-button size="small" text @click="showBindDialog = true">
          <el-icon class="mr-1"><Plus /></el-icon>
          添加公众号
        </el-button>
      </div>
    </div>

    <!-- 发布方式 -->
    <div class="mb-4 sm:mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">发布方式</label>
      <div class="grid grid-cols-1 gap-2">
        <div
          @click="publishType = 'draft'"
          class="border rounded-lg p-3 cursor-pointer transition-colors"
          :class="publishType === 'draft' ? 'border-indigo-500 bg-indigo-50' : 'border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="font-bold text-sm text-gray-800">保存为草稿</div>
              <div class="text-xs text-gray-500">推荐 • 需要在微信公众平台手动发布</div>
            </div>
            <el-radio v-model="publishType" value="draft" class="!m-0"></el-radio>
          </div>
        </div>

        <div
          @click="publishType = 'auto'"
          class="border rounded-lg p-3 cursor-pointer transition-colors"
          :class="publishType === 'auto' ? 'border-red-500 bg-red-50' : 'border-gray-200 hover:bg-gray-50'"
        >
          <div class="flex items-center justify-between">
            <div>
              <div class="font-bold text-sm text-gray-800">自动发布</div>
              <div class="text-xs text-gray-500">谨慎 • 文章将直接推送给关注者</div>
            </div>
            <el-radio v-model="publishType" value="auto" class="!m-0"></el-radio>
          </div>
        </div>
      </div>

      <!-- 发布限制提示 -->
      <div v-if="publishType === 'auto' && limitCheck" class="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded text-xs">
        <div v-if="limitCheck.can_publish" class="text-yellow-700">
          <el-icon class="mr-1"><InfoFilled /></el-icon>
          当前可以发布，距离上次发布已超过限制时间
        </div>
        <div v-else class="text-yellow-700">
          <el-icon class="mr-1"><WarningFilled /></el-icon>
          {{ limitCheck.reason }}
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <template #footer>
      <div class="flex justify-end gap-2">
        <el-button @click="$emit('update:modelValue', false)">取消</el-button>
        <el-button
          type="primary"
          :loading="publishing"
          :disabled="!selectedAccountId || (publishType === 'auto' && limitCheck && !limitCheck.can_publish)"
          @click="handlePublish"
        >
          {{ publishType === 'draft' ? '保存草稿' : '立即发布' }}
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 绑定公众号对话框 -->
  <el-dialog
    v-model="showBindDialog"
    title="绑定微信公众号"
    :width="dialogWidth"
    append-to-body
  >
    <el-form :model="bindForm" label-width="100px" label-position="top">
      <el-form-item label="AppID">
        <el-input
          v-model="bindForm.appId"
          placeholder="请输入微信公众号 AppID"
          clearable
        />
        <div class="text-xs text-gray-500 mt-1">
          在微信公众平台 > 开发 > 基本配置中获取
        </div>
      </el-form-item>

      <el-form-item label="AppSecret">
        <el-input
          v-model="bindForm.secret"
          type="password"
          placeholder="请输入微信公众号 AppSecret"
          show-password
          clearable
        />
        <div class="text-xs text-gray-500 mt-1">
          在微信公众平台 > 开发 > 基本配置中获取
        </div>
      </el-form-item>

      <el-form-item label="备注名称（可选）">
        <el-input
          v-model="bindForm.accountName"
          placeholder="为公众号起一个易识别的名称"
          clearable
        />
      </el-form-item>

      <el-alert
        type="info"
        :closable="false"
        class="mb-4"
      >
        <template #title>
          <div class="text-xs">
            <strong>获取 AppID 和 AppSecret：</strong>
            <ol class="list-decimal list-inside mt-1 space-y-1">
              <li>登录 <a href="https://mp.weixin.qq.com" target="_blank" class="text-indigo-600 hover:underline">微信公众平台</a></li>
              <li>进入 开发 > 基本配置</li>
              <li>获取开发者 ID（AppID）和开发者密码（AppSecret）</li>
            </ol>
          </div>
        </template>
      </el-alert>
    </el-form>

    <template #footer>
      <div class="flex justify-end gap-2">
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" :loading="binding" @click="handleBind">
          绑定
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { InfoFilled, WarningFilled, Plus } from '@element-plus/icons-vue'
import { wechat } from '@/api'

const props = defineProps({
  modelValue: Boolean,
  article: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const dialogWidth = computed(() => window.innerWidth < 640 ? '90%' : '500px')

// 状态
const loadingAccounts = ref(false)
const accounts = ref([])
const selectedAccountId = ref(null)
const publishType = ref('draft') // 'draft' or 'auto'
const publishing = ref(false)
const limitCheck = ref(null)

// 绑定相关状态
const showBindDialog = ref(false)
const binding = ref(false)
const bindForm = ref({
  appId: '',
  secret: '',
  accountName: ''
})

// 加载公众号列表
const loadAccounts = async () => {
  loadingAccounts.value = true
  try {
    const res = await wechat.getWeChatAccounts()
    accounts.value = res.accounts || []
    // 默认选中第一个激活的账号
    if (accounts.value.length > 0) {
      const activeAccount = accounts.value.find(a => a.is_active)
      selectedAccountId.value = activeAccount?.id || accounts.value[0].id
    }
  } catch (error) {
    console.error('加载公众号列表失败:', error)
  } finally {
    loadingAccounts.value = false
  }
}

// 检查发布限制
const checkPublishLimits = async () => {
  if (!props.article || !selectedAccountId.value) return

  try {
    const res = await wechat.checkPublishStatus(
      props.article.id,
      selectedAccountId.value
    )
    limitCheck.value = res
  } catch (error) {
    console.error('检查发布限制失败:', error)
  }
}

// 监听账号变化，重新检查限制
watch(selectedAccountId, () => {
  if (publishType.value === 'auto') {
    checkPublishLimits()
  }
})

// 监听发布方式变化
watch(publishType, () => {
  if (publishType.value === 'auto') {
    checkPublishLimits()
  } else {
    limitCheck.value = null
  }
})

// 处理发布
const handlePublish = async () => {
  if (!selectedAccountId.value) {
    ElMessage.warning('请先选择公众号')
    return
  }

  // 自动发布前二次确认
  if (publishType.value === 'auto') {
    try {
      await ElMessageBox.confirm(
        '自动发布将直接把文章推送给关注者，此操作不可撤销。确定要继续吗？',
        '确认发布',
        {
          confirmButtonText: '确定发布',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    } catch {
      return
    }
  }

  publishing.value = true
  try {
    if (publishType.value === 'draft') {
      const res = await wechat.saveAsDraft(props.article.id, selectedAccountId.value)
      if (res.success) {
        ElMessage.success('草稿保存成功，请在微信公众平台发布')
        emit('success', { type: 'draft', data: res })
        emit('update:modelValue', false)
      }
    } else {
      const res = await wechat.publishToWeChat(props.article.id, selectedAccountId.value)
      if (res.success) {
        ElMessage.success('文章发布成功')
        emit('success', { type: 'auto', data: res })
        emit('update:modelValue', false)
      }
    }
  } catch (error) {
    console.error('发布失败:', error)
  } finally {
    publishing.value = false
  }
}

// 监听对话框打开
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    loadAccounts()
    publishType.value = 'draft'
    limitCheck.value = null
  }
})

// 处理绑定公众号
const handleBind = async () => {
  if (!bindForm.value.appId || !bindForm.value.secret) {
    ElMessage.warning('请填写 AppID 和 AppSecret')
    return
  }

  binding.value = true
  try {
    await wechat.bindWeChatAccount({
      app_id: bindForm.value.appId,
      secret: bindForm.value.secret,
      account_name: bindForm.value.accountName || undefined
    })
    ElMessage.success('绑定成功')
    showBindDialog.value = false
    // 重置表单
    bindForm.value = {
      appId: '',
      secret: '',
      accountName: ''
    }
    // 重新加载公众号列表
    await loadAccounts()
  } catch (error) {
    console.error('绑定失败:', error)
    ElMessage.error(error.message || '绑定失败')
  } finally {
    binding.value = false
  }
}

onMounted(() => {
  if (props.modelValue) {
    loadAccounts()
  }
})
</script>
