/**
 * ��֤��ص����ʽ����
 */
import { computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { STORAGE_KEYS, ROUTES } from "@/constants"

export function useAuth() {
  const router = useRouter()
  const authStore = useAuthStore()

  // ��������
  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const user = computed(() => authStore.user)
  const token = computed(() => authStore.token)
  const isAdmin = computed(() => authStore.isAdmin)
  const username = computed(() => user.value?.username || '')

  /**
   * ��¼
   */
  const login = async (credentials) => {
    try {
      await authStore.login(credentials)
      return true
    } catch (error) {
      console.error("��¼ʧ��:", error)
      throw error
    }
  }

  /**
   * �ǳ�
   */
  const logout = () => {
    authStore.logout()
    router.push(ROUTES.LOGIN)
  }

  /**
   * ���Ȩ��
   */
  const hasPermission = (permission) => {
    if (!isAuthenticated.value) return false
    if (permission === "admin") return isAdmin.value
    return true
  }

  return {
    isAuthenticated,
    user,
    token,
    isAdmin,
    username,
    login,
    logout,
    hasPermission
  }
}
