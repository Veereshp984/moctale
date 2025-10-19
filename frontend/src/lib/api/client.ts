import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

const DEFAULT_TIMEOUT = 10_000

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'https://api.soundwave.local',
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface ApiErrorShape {
  message: string
  status?: number
  code?: string
  details?: unknown
}

export const toApiError = (error: unknown): ApiErrorShape => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ message?: string; code?: string; details?: unknown }>
    return {
      message:
        axiosError.response?.data?.message ?? axiosError.message ?? 'Something went wrong while contacting the API',
      status: axiosError.response?.status,
      code: axiosError.response?.data?.code,
      details: axiosError.response?.data?.details,
    }
  }

  if (error instanceof Error) {
    return { message: error.message }
  }

  return { message: 'Unknown error' }
}

const unwrap = <T>(promise: Promise<{ data: T }>) => promise.then((response) => response.data)

export const http = {
  get: async <T>(url: string, config?: AxiosRequestConfig) => unwrap<T>(apiClient.get<T>(url, config)),
  post: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    unwrap<T>(apiClient.post<T>(url, data, config)),
  put: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    unwrap<T>(apiClient.put<T>(url, data, config)),
  patch: async <T>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    unwrap<T>(apiClient.patch<T>(url, data, config)),
  delete: async <T>(url: string, config?: AxiosRequestConfig) => unwrap<T>(apiClient.delete<T>(url, config)),
}

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => Promise.reject(toApiError(error)),
)
