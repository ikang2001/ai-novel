import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import { getLoginUser } from '@/api/userController.ts'
import { DEFAULT_USERNAME } from '@/constants/user'

const defaultLoginUser: API.LoginUserVO = {
  userName: DEFAULT_USERNAME,
}

type FetchLoginUserOptions = {
  force?: boolean
}

/**
 * 登录用户信息
 */
export const useLoginUserStore = defineStore('loginUser', () => {
  // 默认值
  const loginUser = ref<API.LoginUserVO>({ ...defaultLoginUser })
  const hasFetchedLoginUser = ref(false)
  let fetchLoginUserPromise: Promise<API.LoginUserVO> | null = null

  // 获取登录用户信息
  async function fetchLoginUser(options: FetchLoginUserOptions = {}) {
    const { force = false } = options

    if (!force) {
      if (fetchLoginUserPromise) {
        return fetchLoginUserPromise
      }
      if (hasFetchedLoginUser.value) {
        return loginUser.value
      }
    }

    fetchLoginUserPromise = (async () => {
      try {
        const res = await getLoginUser()
        if (res.data.code === 0 && res.data.data) {
          loginUser.value = res.data.data
        } else {
          loginUser.value = { ...defaultLoginUser }
        }
        return loginUser.value
      } catch (error) {
        if (axios.isAxiosError(error) && error.response?.status === 401) {
          loginUser.value = { ...defaultLoginUser }
          return loginUser.value
        }
        throw error
      } finally {
        hasFetchedLoginUser.value = true
        fetchLoginUserPromise = null
      }
    })()

    return fetchLoginUserPromise
  }

  // 更新登录用户信息
  function setLoginUser(newLoginUser: any) {
    loginUser.value = newLoginUser
    hasFetchedLoginUser.value = true
  }

  // 重置登录用户信息
  function resetLoginUser() {
    loginUser.value = { ...defaultLoginUser }
    hasFetchedLoginUser.value = false
    fetchLoginUserPromise = null
  }

  return { loginUser, fetchLoginUser, setLoginUser, resetLoginUser }
})
