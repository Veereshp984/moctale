import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider, useAuth } from './AuthContext'
import * as authService from '../services/auth'

vi.mock('../services/auth', () => ({
  ApiError: class ApiError extends Error {
    status = 400
  },
  resolveSession: vi.fn(),
  login: vi.fn(),
  signup: vi.fn(),
  logout: vi.fn(),
  updateProfile: vi.fn(),
  fetchProfile: vi.fn(),
  isUnauthorizedError: vi.fn(() => false),
}))

const mockUser = {
  id: 'user-10',
  email: 'creator@example.com',
  displayName: 'Taylor Creator',
  preferences: {
    newsletterOptIn: true,
  },
}

const Consumer = () => {
  const { status, user, login, logout } = useAuth()

  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="user">{user?.displayName ?? 'none'}</span>
      <button
        type="button"
        data-testid="login"
        onClick={() => {
          void login({ email: 'creator@example.com', password: 'Secret123!' })
        }}
      >
        log in
      </button>
      <button
        type="button"
        data-testid="logout"
        onClick={() => {
          void logout()
        }}
      >
        log out
      </button>
    </div>
  )
}

describe('AuthProvider', () => {
  const resolveSessionMock = vi.mocked(authService.resolveSession)
  const loginMock = vi.mocked(authService.login)
  const logoutMock = vi.mocked(authService.logout)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('hydrates the current user on mount', async () => {
    resolveSessionMock.mockResolvedValueOnce(mockUser)

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    )

    expect(screen.getByTestId('status').textContent).toBe('loading')

    await waitFor(() => {
      expect(screen.getByTestId('status').textContent).toBe('authenticated')
    })

    expect(screen.getByTestId('user').textContent).toBe('Taylor Creator')
    expect(resolveSessionMock).toHaveBeenCalled()
  })

  it('authenticates via login and exposes the user in context', async () => {
    resolveSessionMock.mockResolvedValueOnce(null)
    loginMock.mockResolvedValueOnce({ user: mockUser })

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('status').textContent).toBe('unauthenticated')
    })

    const interactions = userEvent.setup()
    await interactions.click(screen.getByTestId('login'))

    await waitFor(() => {
      expect(screen.getByTestId('status').textContent).toBe('authenticated')
    })

    expect(screen.getByTestId('user').textContent).toBe('Taylor Creator')
    expect(loginMock).toHaveBeenCalledWith({ email: 'creator@example.com', password: 'Secret123!' })
  })

  it('clears the session on logout', async () => {
    resolveSessionMock.mockResolvedValueOnce(mockUser)
    logoutMock.mockResolvedValueOnce(undefined)

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    )

    await waitFor(() => {
      expect(screen.getByTestId('status').textContent).toBe('authenticated')
    })

    fireEvent.click(screen.getByTestId('logout'))

    await waitFor(() => {
      expect(screen.getByTestId('status').textContent).toBe('unauthenticated')
    })

    expect(screen.getByTestId('user').textContent).toBe('none')
    expect(logoutMock).toHaveBeenCalled()
  })
})
