import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { LoginPayload, ProfileUpdatePayload, SignupPayload, UserProfile } from '../types'
import {
  ApiError,
  fetchProfile as fetchProfileRequest,
  isUnauthorizedError,
  login as loginRequest,
  logout as logoutRequest,
  resolveSession,
  signup as signupRequest,
  updateProfile as updateProfileRequest,
} from '../services/auth'

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

export interface AuthContextValue {
  user: UserProfile | null
  status: AuthStatus
  isAuthenticated: boolean
  isLoading: boolean
  isProcessing: boolean
  error: string | null
  login: (credentials: LoginPayload) => Promise<UserProfile>
  signup: (payload: SignupPayload) => Promise<UserProfile>
  logout: () => Promise<void>
  updateProfile: (updates: ProfileUpdatePayload) => Promise<UserProfile>
  refreshProfile: () => Promise<UserProfile>
  clearError: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

const resolveErrorMessage = (error: unknown, fallback: string) => {
  if (error instanceof ApiError && error.message) {
    return error.message
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return fallback
}

const normalizeError = (error: unknown, message: string) => {
  if (error instanceof Error) {
    error.message = message
    return error
  }

  return new Error(message)
}

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<UserProfile | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    let cancelled = false

    const hydrate = async () => {
      try {
        const profile = await resolveSession()
        if (cancelled) {
          return
        }

        if (profile) {
          setUser(profile)
          setStatus('authenticated')
        } else {
          setUser(null)
          setStatus('unauthenticated')
        }
      } catch (err) {
        console.error('Unable to resolve auth session', err)
        if (!cancelled) {
          setUser(null)
          setStatus('unauthenticated')
        }
      }
    }

    void hydrate()

    return () => {
      cancelled = true
    }
  }, [])

  const login = useCallback(async (credentials: LoginPayload) => {
    setIsProcessing(true)
    setError(null)
    try {
      const { user: profile } = await loginRequest(credentials)
      setUser(profile)
      setStatus('authenticated')
      return profile
    } catch (err) {
      const fallback = 'We could not sign you in with those details.'
      const message = resolveErrorMessage(err, fallback)
      setError(message)
      setStatus('unauthenticated')
      throw normalizeError(err, message)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const signup = useCallback(async (payload: SignupPayload) => {
    setIsProcessing(true)
    setError(null)
    try {
      const { user: profile } = await signupRequest(payload)
      setUser(profile)
      setStatus('authenticated')
      return profile
    } catch (err) {
      const fallback = 'We were unable to complete your registration.'
      const message = resolveErrorMessage(err, fallback)
      setError(message)
      setStatus('unauthenticated')
      throw normalizeError(err, message)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const logout = useCallback(async () => {
    setIsProcessing(true)
    setError(null)
    try {
      await logoutRequest()
    } catch (err) {
      console.warn('Failed to end session cleanly', err)
    } finally {
      setUser(null)
      setStatus('unauthenticated')
      setIsProcessing(false)
    }
  }, [])

  const updateProfile = useCallback(async (updates: ProfileUpdatePayload) => {
    setIsProcessing(true)
    setError(null)
    try {
      const profile = await updateProfileRequest(updates)
      setUser(profile)
      setStatus('authenticated')
      return profile
    } catch (err) {
      const fallback = 'Unable to update your preferences right now.'
      const message = resolveErrorMessage(err, fallback)
      setError(message)
      throw normalizeError(err, message)
    } finally {
      setIsProcessing(false)
    }
  }, [])

  const refreshProfile = useCallback(async () => {
    try {
      const profile = await fetchProfileRequest()
      setUser(profile)
      setStatus('authenticated')
      return profile
    } catch (err) {
      if (isUnauthorizedError(err)) {
        setUser(null)
        setStatus('unauthenticated')
      }
      const fallback = 'Unable to refresh your profile right now.'
      const message = resolveErrorMessage(err, fallback)
      setError(message)
      throw normalizeError(err, message)
    }
  }, [])

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isLoading: status === 'loading',
      isProcessing,
      error,
      login,
      signup,
      logout,
      updateProfile,
      refreshProfile,
      clearError,
    }),
    [clearError, error, isProcessing, login, logout, refreshProfile, signup, status, updateProfile, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}
