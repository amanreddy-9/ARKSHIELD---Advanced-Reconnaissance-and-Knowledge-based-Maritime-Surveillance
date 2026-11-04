import axios, { AxiosError } from 'axios'

const STORAGE_KEY = 'oatrack_api_base_url'

export function getApiBaseUrl(): string {
  if (typeof window !== 'undefined') {
    const custom = localStorage.getItem(STORAGE_KEY)
    if (custom && custom.trim().length > 0) {
      return custom.trim().replace(/\/$/, '')
    }
  }
  const envUrl = import.meta.env.VITE_API_BASE_URL
  if (envUrl && envUrl.trim().length > 0) {
    return envUrl.trim().replace(/\/$/, '')
  }
  return 'http://127.0.0.1:8000'
}

export function setApiBaseUrl(url: string): void {
  if (typeof window !== 'undefined') {
    const clean = url.trim().replace(/\/$/, '')
    localStorage.setItem(STORAGE_KEY, clean)
    apiClient.defaults.baseURL = clean
  }
}

export function resolveBackendUrl(path?: string | null): string {
  if (!path) return ''
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path
  }
  const base = getApiBaseUrl()
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  return `${base}${cleanPath}`
}

export const apiClient = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 300000, // 5 min for heavy video and 1024px inference
})

// Request interceptor to update baseURL dynamically
apiClient.interceptors.request.use((config) => {
  config.baseURL = getApiBaseUrl()
  return config
})

// Response error handler
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    let message = 'API request failed'
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail
    if (typeof detail === 'string') {
      message = detail
    } else if (error.code === 'ECONNABORTED') {
      message = 'Backend operation timed out during heavy inference.'
    } else if (!error.response) {
      message = 'Backend unavailable (Ensure uvicorn backend.main:app is running at ' + getApiBaseUrl() + ')'
    } else if (error.response.status === 404) {
      message = 'Requested resource or endpoint was not found on backend.'
    } else if (error.response.status === 500) {
      message = 'Backend inference or processing encountered an internal error.'
    } else if (error.code === 'ECONNABORTED') {
      message = 'Backend operation timed out during heavy inference.'
    }
    return Promise.reject(new Error(message))
  }
)
