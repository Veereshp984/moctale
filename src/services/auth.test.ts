import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  ApiError,
  clearTokens,
  fetchProfile,
  getAccessToken,
  login,
  logout,
  refreshSession,
  resolveSession,
} from './auth'

describe('auth service', () => {
  const createJsonResponse = (body: unknown, init?: ResponseInit) => {
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  }

  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.restoreAllMocks()
    clearTokens()
  })

  it('stores tokens after a successful login', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      createJsonResponse({
        user: { id: 'user-1', email: 'listener@example.com', displayName: 'Listener', preferences: { newsletterOptIn: true } },
        tokens: { accessToken: 'access-token', expiresAt: '2099-01-01T00:00:00.000Z' },
      }),
    )

    const result = await login({ email: 'listener@example.com', password: 'Secret123!' })

    expect(fetchMock).toHaveBeenCalledWith('/api/auth/login', expect.objectContaining({
      method: 'POST',
      credentials: 'include',
    }))
    const init = fetchMock.mock.calls[0][1]
    expect(init?.body).toBe(JSON.stringify({ email: 'listener@example.com', password: 'Secret123!' }))
    expect(getAccessToken()).toBe('access-token')
    expect(result.user.displayName).toBe('Listener')
  })

  it('includes the bearer token when fetching the profile', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')

    fetchMock.mockResolvedValueOnce(
      createJsonResponse({
        user: { id: 'user-2', email: 'viewer@example.com', displayName: 'Viewer', preferences: { newsletterOptIn: true } },
        tokens: { accessToken: 'bearer-token', expiresAt: '2099-01-01T00:00:00.000Z' },
      }),
    )

    fetchMock.mockResolvedValueOnce(
      createJsonResponse({
        id: 'user-2',
        email: 'viewer@example.com',
        displayName: 'Viewer',
        preferences: { newsletterOptIn: true },
      }),
    )

    await login({ email: 'viewer@example.com', password: 'Secret123!' })
    await fetchProfile()

    const init = fetchMock.mock.calls[1][1]
    const headers = new Headers(init?.headers as HeadersInit)
    expect(headers.get('Authorization')).toBe('Bearer bearer-token')
  })

  it('refreshes the session when the existing token is invalid', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    fetchMock.mockResolvedValueOnce(
      createJsonResponse({ accessToken: 'next-token', expiresAt: '2099-01-01T00:00:00.000Z' }),
    )

    fetchMock.mockResolvedValueOnce(
      createJsonResponse({
        id: 'user-3',
        email: 'maker@example.com',
        displayName: 'Maker',
        preferences: { newsletterOptIn: false },
      }),
    )

    const profile = await resolveSession()

    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(profile).toMatchObject({ email: 'maker@example.com' })
    expect(getAccessToken()).toBe('next-token')
  })

  it('clears tokens on logout even if the request fails', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')

    fetchMock.mockResolvedValueOnce(
      createJsonResponse({
        user: { id: 'user-4', email: 'editor@example.com', displayName: 'Editor', preferences: { newsletterOptIn: true } },
        tokens: { accessToken: 'logout-token', expiresAt: '2099-01-01T00:00:00.000Z' },
      }),
    )

    fetchMock.mockResolvedValueOnce(
      new Response(null, {
        status: 204,
      }),
    )

    await login({ email: 'editor@example.com', password: 'Secret123!' })
    expect(getAccessToken()).toBe('logout-token')

    await logout()

    expect(getAccessToken()).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('bubbles non-authentication errors when resolving the session', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Server down' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(resolveSession()).resolves.toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('returns null when refresh fails and exposes the error', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Unauthorized' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Refresh denied' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(resolveSession()).resolves.toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(getAccessToken()).toBeNull()

    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ message: 'Refresh denied' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(refreshSession()).rejects.toBeInstanceOf(ApiError)
  })
})
