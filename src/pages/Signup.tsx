import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { availableMoods, availableMovieGenres, availableMusicGenres } from '../data/mockData'
import { useAuth } from '../context/AuthContext'

interface FieldErrors {
  displayName?: string
  email?: string
  password?: string
  confirmPassword?: string
}

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const Signup = () => {
  const { signup, isProcessing, error: authError, clearError } = useAuth()
  const navigate = useNavigate()

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [primaryGenre, setPrimaryGenre] = useState('')
  const [primaryMood, setPrimaryMood] = useState('')
  const [newsletterOptIn, setNewsletterOptIn] = useState(true)

  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)

  const genreOptions = useMemo(() => {
    const combined = new Set([...availableMovieGenres, ...availableMusicGenres])
    return [...combined.values()].sort()
  }, [])

  useEffect(() => {
    clearError()
    return () => {
      clearError()
    }
  }, [clearError])

  const validate = () => {
    const nextErrors: FieldErrors = {}

    if (!displayName.trim()) {
      nextErrors.displayName = 'Tell us what to call you inside Auragraph.'
    }

    if (!email.trim()) {
      nextErrors.email = 'Add the email you want associated with your account.'
    } else if (!emailPattern.test(email.trim())) {
      nextErrors.email = 'This email address does not appear to be valid.'
    }

    if (!password) {
      nextErrors.password = 'Choose a password to secure your account.'
    } else if (password.length < 8) {
      nextErrors.password = 'Passwords need to be at least 8 characters.'
    }

    if (!confirmPassword) {
      nextErrors.confirmPassword = 'Please confirm your password.'
    } else if (confirmPassword !== password) {
      nextErrors.confirmPassword = 'These passwords do not match.'
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
      await signup({
        displayName: displayName.trim(),
        email: email.trim().toLowerCase(),
        password,
        preferences: {
          primaryGenre: primaryGenre || undefined,
          primaryMood: primaryMood || undefined,
          newsletterOptIn,
        },
      })
      navigate('/', { replace: true })
    } catch (error) {
      const message = error instanceof Error && error.message ? error.message : 'We could not complete your registration.'
      setSubmitError(message)
    }
  }

  const clearFieldError = (key: keyof FieldErrors) => {
    if (fieldErrors[key]) {
      setFieldErrors((previous) => ({ ...previous, [key]: undefined }))
    }
    if (submitError) {
      setSubmitError(null)
    }
    clearError()
  }

  const errorMessage = submitError ?? authError

  return (
    <div className="auth-page" data-testid="signup-page">
      <section className="auth-card">
        <header className="auth-card__header">
          <p className="auth-card__eyebrow">Join the community</p>
          <h1>Create your Auragraph account</h1>
          <p className="auth-card__subtitle">
            Sign up to craft playlists that blend cinema and sound. Tell us a little about your taste so we can tailor
            recommendations.
          </p>
        </header>
        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <label className="field auth-field">
            <span>Display name</span>
            <input
              type="text"
              value={displayName}
              onChange={(event) => {
                setDisplayName(event.target.value)
                clearFieldError('displayName')
              }}
              autoComplete="name"
              required
            />
            {fieldErrors.displayName && <span className="field__error">{fieldErrors.displayName}</span>}
          </label>
          <label className="field auth-field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => {
                setEmail(event.target.value)
                clearFieldError('email')
              }}
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
              onChange={(event) => {
                setPassword(event.target.value)
                clearFieldError('password')
              }}
              autoComplete="new-password"
              required
            />
            {fieldErrors.password && <span className="field__error">{fieldErrors.password}</span>}
          </label>
          <label className="field auth-field">
            <span>Confirm password</span>
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) => {
                setConfirmPassword(event.target.value)
                clearFieldError('confirmPassword')
              }}
              autoComplete="new-password"
              required
            />
            {fieldErrors.confirmPassword && <span className="field__error">{fieldErrors.confirmPassword}</span>}
          </label>
          <div className="auth-form__grid">
            <label className="field auth-field">
              <span>Preferred genre</span>
              <select value={primaryGenre} onChange={(event) => setPrimaryGenre(event.target.value)}>
                <option value="">Surprise me</option>
                {genreOptions.map((genre) => (
                  <option key={genre} value={genre}>
                    {genre}
                  </option>
                ))}
              </select>
            </label>
            <label className="field auth-field">
              <span>Preferred mood</span>
              <select value={primaryMood} onChange={(event) => setPrimaryMood(event.target.value)}>
                <option value="">Any vibe</option>
                {availableMoods.map((mood) => (
                  <option key={mood} value={mood}>
                    {mood}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="field field--inline auth-field">
            <span>Stay in the loop</span>
            <span className="switch">
              <input
                type="checkbox"
                checked={newsletterOptIn}
                onChange={(event) => setNewsletterOptIn(event.target.checked)}
              />
              <span className="switch__label">Email me new playlist ideas and curation tips.</span>
            </span>
          </label>
          {errorMessage && (
            <div className="auth-form__error" role="alert">
              <p>{errorMessage}</p>
            </div>
          )}
          <button type="submit" className="button auth-submit" disabled={isProcessing}>
            {isProcessing ? 'Creating your account…' : 'Create account'}
          </button>
        </form>
        <footer className="auth-card__footer">
          <p>
            Already have an account?{' '}
            <Link to="/login" className="auth-link">
              Sign in
            </Link>
            .
          </p>
        </footer>
      </section>
    </div>
  )
}

export default Signup
