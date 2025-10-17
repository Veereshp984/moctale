import type {
  AuthResponse,
  AuthTokens,
  LoginPayload,
  ProfileUpdatePayload,
  SignupPayload,
  UserProfile,
} from '../types'

const API_BASE_URL = ((import.meta.env && import.meta.env.VITE_API_BASE_URL) || '/api').replace(/\/$/, '')

type BodyExpectation = 'json' | 'void'

export class ApiError extends Error {
  status: number
  details?: unknown

  constructor(status: number, message: string, details?: unknown) {
    super(message)
    this.status = status
    this.details = details
  }
}

let tokenCache: AuthTokens | null = null

const buildUrl = (path: string) => {
  if (/^https?:\/\//.test(path)) {
    return path
  }

  if (path.startsWith('/')) {
    return `${API_BASE_URL}${path}`
  }

  return `${API_BASE_URL}/${path}`
}

interface AuthRequestInit extends RequestInit {
  requireAuth?: boolean
  expect?: BodyExpectation
}

const parseBody = async <T>(response: Response, expect: BodyExpectation): Promise<T> => {
  if (expect === 'void' || response.status === 204) {
    return undefined as T
  }

  const text = await response.text()

  if (!text) {
    return undefined as T
  }

  try {
    return JSON.parse(text) as T
  } catch (error) {
    console.warn('Failed to parse JSON response', error)
    return undefined as T
  }
}

const parseError = async (response: Response) => {
  try {
    const data = await response.clone().json()
    const message =
      typeof data === 'object' && data !== null && 'message' in data
        ? String((data as { message?: string }).message ?? 'Request failed')
        : response.statusText || 'Request failed'

    return { message, details: data }
  } catch (error) {
    const fallback = await response.text()
    return {
      message: fallback || response.statusText || 'Request failed',
      details: fallback || null,
    }
  }
}

const request = async <T>(path: string, options: AuthRequestInit = {}): Promise<T> => {
  const { requireAuth = false, expect = 'json', ...init } = options
  const headers = new Headers(init.headers ?? undefined)

  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (requireAuth) {
    const accessToken = tokenCache?.accessToken
    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`)
    }
  }

  const response = await fetch(buildUrl(path), {
    credentials: 'include',
    ...init,
    headers,
  })

  if (!response.ok) {
    const { message, details } = await parseError(response)
    throw new ApiError(response.status, message, details)
  }

  return parseBody<T>(response, expect)
}

const setTokens = (tokens: AuthTokens | null) => {
  tokenCache = tokens
}

export const getAccessToken = () => tokenCache?.accessToken ?? null

export const clearTokens = () => {
  tokenCache = null
}

export const isUnauthorizedError = (error: unknown) => {
  return error instanceof ApiError && (error.status === 401 || error.status === 403)
}

export const signup = async (payload: SignupPayload): Promise<AuthResponse> => {
  const result = await request<AuthResponse>('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

  setTokens(result.tokens)
  return result
}

export const login = async (payload: LoginPayload): Promise<AuthResponse> => {
  const result = await request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  })

  setTokens(result.tokens)
  return result
}

export const refreshSession = async (): Promise<AuthTokens> => {
  const tokens = await request<AuthTokens>('/auth/refresh', {
    method: 'POST',
  })

  setTokens(tokens)
  return tokens
}

export const fetchProfile = async (): Promise<UserProfile> => {
  return request<UserProfile>('/auth/me', {
    method: 'GET',
    requireAuth: true,
  })
}

export const updateProfile = async (updates: ProfileUpdatePayload): Promise<UserProfile> => {
  return request<UserProfile>('/auth/me', {
    method: 'PUT',
    body: JSON.stringify(updates),
    requireAuth: true,
  })
}

export const logout = async (): Promise<void> => {
  await request('/auth/logout', {
    method: 'POST',
    requireAuth: true,
    expect: 'void',
  })

  clearTokens()
}

export const resolveSession = async (): Promise<UserProfile | null> => {
  try {
    return await fetchProfile()
  } catch (error) {
    if (!isUnauthorizedError(error)) {
      console.warn('Unable to fetch profile', error)
      return null
    }
  }

  try {
    await refreshSession()
    return await fetchProfile()
  } catch (error) {
    if (!isUnauthorizedError(error)) {
      throw error
    }

    clearTokens()
    return null
  }
}
