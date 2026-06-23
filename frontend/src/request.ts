import axios from 'axios'
import { message } from 'ant-design-vue'
import { API_BASE_URL } from '@/config/env'
import { REQUEST_TIMEOUT, UNAUTHORIZED_CODE } from '@/constants'

const LOGIN_PATH = '/user/login'
const LOGIN_STATUS_PATH = 'user/get/login'

function isLoginStatusRequest(url?: string) {
  return url?.includes(LOGIN_STATUS_PATH) ?? false
}

function handleUnauthorized(url?: string) {
  if (isLoginStatusRequest(url) || window.location.pathname.includes(LOGIN_PATH)) {
    return
  }

  message.warning('请先登录')
  window.location.href = `${LOGIN_PATH}?redirect=${window.location.href}`
}

// 创建 Axios 实例
const myAxios = axios.create({
  baseURL: API_BASE_URL,
  timeout: REQUEST_TIMEOUT,
  withCredentials: true,
})

// 全局请求拦截器
myAxios.interceptors.request.use(
  function (config) {
    // Do something before request is sent
    return config
  },
  function (error) {
    // Do something with request error
    return Promise.reject(error)
  },
)

// 全局响应拦截器
myAxios.interceptors.response.use(
  function (response) {
    const { data } = response
    // 未登录
    if (data.code === UNAUTHORIZED_CODE) {
      handleUnauthorized(response.request?.responseURL ?? response.config?.url)
    }
    return response
  },
  function (error) {
    // Any status codes that falls outside the range of 2xx cause this function to trigger
    // Do something with response error
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      handleUnauthorized(error.response.request?.responseURL ?? error.config?.url)
    }
    return Promise.reject(error)
  },
)

export default myAxios
