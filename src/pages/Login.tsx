import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface FieldErrors {
  email?: string
  password?: string
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const Login = () => {
  const { login, isProcessing, error: authError, clearError } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const redirectTo = useMemo(() => {
    const value = location.state && typeof location.state === 'object' ? (location.state as { from?: string }).from : undefined
    return value && value.startsWith('/') ? value : '/'
  }, [location.state])

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  useEffect(() => {
    clearError()
    return () => {
      clearError()
    }
  }, [clearError])

  const validate = () => {
    const nextErrors: FieldErrors = {}

    if (!email.trim()) {
      nextErrors.email = 'Please enter the email you used to register.'
    } else if (!emailPattern.test(email.trim())) {
      nextErrors.email = 'That email address does not look quite right.'
    }

    if (!password) {
      nextErrors.password = 'Enter your password to continue.'
    } else if (password.length < 8) {
      nextErrors.password = 'Passwords must be at least 8 characters long.'
    }

    setFieldErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!validate()) {
      return
    }

    setSubmitError(null)
    clearError()

    try {
      await login({ email: email.trim().toLowerCase(), password })
      navigate(redirectTo, { replace: true })
    } catch (error) {
      const message = error instanceof Error && error.message ? error.message : 'We were unable to sign you in.'
      setSubmitError(message)
    }
  }

  const handleEmailChange = (value: string) => {
    setEmail(value)
    if (fieldErrors.email) {
      setFieldErrors((previous) => ({ ...previous, email: undefined }))
    }
    if (submitError) {
      setSubmitError(null)
    }
    clearError()
  }

  const handlePasswordChange = (value: string) => {
    setPassword(value)
    if (fieldErrors.password) {
      setFieldErrors((previous) => ({ ...previous, password: undefined }))
    }
    if (submitError) {
      setSubmitError(null)
    }
    clearError()
  }

  const errorMessage = submitError ?? authError

  return (
    <div className="auth-page" data-testid="login-page">
      <section className="auth-card">
        <header className="auth-card__header">
          <p className="auth-card__eyebrow">Welcome back</p>
          <h1>Sign in to Auragraph</h1>
          <p className="auth-card__subtitle">
            Continue curating your blended playlist experience. Enter your credentials to resume where you left off.
          </p>
        </header>
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <label className="field auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => handleEmailChange(event.target.value)}
              autoComplete="email"
              required
            />
            {fieldErrors.email && <span className="field__error">{fieldErrors.email}</span>}
          </label>
          <label className="field auth-field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => handlePasswordChange(event.target.value)}
              autoComplete="current-password"
              required
            />
            {fieldErrors.password && <span className="field__error">{fieldErrors.password}</span>}
          </label>
          {errorMessage && (
            <div className="auth-form__error" role="alert">
              <p>{errorMessage}</p>
            </div>
          )}
          <button type="submit" className="button auth-submit" disabled={isProcessing}>
            {isProcessing ? 'Signing you in…' : 'Sign in'}
          </button>
        </form>
        <footer className="auth-card__footer">
          <p>
            New to Auragraph?{' '}
            <Link to="/signup" className="auth-link">
              Create an account
            </Link>
            .
          </p>
        </footer>
      </section>
    </div>
  )
}

export default Login
