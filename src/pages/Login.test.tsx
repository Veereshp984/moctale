import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Login from './Login'
import { useAuth, type AuthContextValue } from '../context/AuthContext'

vi.mock('../context/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const useAuthMock = useAuth as unknown as Mock<[], AuthContextValue>

describe('Login page', () => {
  beforeEach(() => {
    useAuthMock.mockReset()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('validates required fields', async () => {
    useAuthMock.mockReturnValue({
      login: vi.fn(),
      isProcessing: false,
      error: null,
      clearError: vi.fn(),
    })

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.click(screen.getByRole('button', { name: /sign in/i }))

    expect(screen.getByText(/enter your password/i)).toBeInTheDocument()
    expect(screen.getByText(/please enter the email/i)).toBeInTheDocument()
  })

  it('surfaces API errors when login fails', async () => {
    const loginMock = vi.fn().mockRejectedValueOnce(new Error('Invalid credentials'))

    useAuthMock.mockReturnValue({
      login: loginMock,
      isProcessing: false,
      error: null,
      clearError: vi.fn(),
    })

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
        </Routes>
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/email/i), 'invalid@example.com')
    await user.type(screen.getByLabelText(/password/i), 'Password1')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('logs the user in and redirects to the dashboard', async () => {
    const loginMock = vi.fn().mockResolvedValueOnce({})

    useAuthMock.mockReturnValue({
      login: loginMock,
      isProcessing: false,
      error: null,
      clearError: vi.fn(),
    })

    const user = userEvent.setup()

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div data-testid="home">Home</div>} />
        </Routes>
      </MemoryRouter>,
    )

    await user.type(screen.getByLabelText(/email/i), 'User@Example.com')
    await user.type(screen.getByLabelText(/password/i), 'Password1')
    await user.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByTestId('home')).toBeInTheDocument()
    })

    expect(loginMock).toHaveBeenCalledWith({ email: 'user@example.com', password: 'Password1' })
  })
})
