import { useEffect, useMemo, useState } from 'react'
import { availableMoods, availableMovieGenres, availableMusicGenres } from '../data/mockData'
import { useAuth } from '../context/AuthContext'

const Profile = () => {
  const { user, updateProfile, isProcessing, error: authError, clearError } = useAuth()

  const [displayName, setDisplayName] = useState(user?.displayName ?? '')
  const [bio, setBio] = useState(user?.bio ?? '')
  const [primaryGenre, setPrimaryGenre] = useState(user?.preferences.primaryGenre ?? '')
  const [primaryMood, setPrimaryMood] = useState(user?.preferences.primaryMood ?? '')
  const [newsletterOptIn, setNewsletterOptIn] = useState<boolean>(user?.preferences.newsletterOptIn ?? true)
  const [submitMessage, setSubmitMessage] = useState<string | null>(null)

  const genreOptions = useMemo(() => {
    const combined = new Set([...availableMovieGenres, ...availableMusicGenres])
    return [...combined.values()].sort()
  }, [])

  useEffect(() => {
    setDisplayName(user?.displayName ?? '')
    setBio(user?.bio ?? '')
    setPrimaryGenre(user?.preferences.primaryGenre ?? '')
    setPrimaryMood(user?.preferences.primaryMood ?? '')
    setNewsletterOptIn(user?.preferences.newsletterOptIn ?? true)
  }, [user?.bio, user?.displayName, user?.preferences.newsletterOptIn, user?.preferences.primaryGenre, user?.preferences.primaryMood])

  useEffect(() => {
    clearError()
    return () => {
      clearError()
    }
  }, [clearError])

  const isDirty = useMemo(() => {
    if (!user) {
      return false
    }

    return (
      displayName.trim() !== (user.displayName ?? '') ||
      (bio ?? '').trim() !== (user.bio ?? '') ||
      (primaryGenre || '') !== (user.preferences.primaryGenre || '') ||
      (primaryMood || '') !== (user.preferences.primaryMood || '') ||
      newsletterOptIn !== user.preferences.newsletterOptIn
    )
  }, [bio, displayName, newsletterOptIn, primaryGenre, primaryMood, user])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!user || !displayName.trim()) {
      return
    }

    setSubmitMessage(null)
    clearError()

    try {
      await updateProfile({
        displayName: displayName.trim(),
        bio: bio.trim() ? bio.trim() : undefined,
        preferences: {
          primaryGenre: primaryGenre || undefined,
          primaryMood: primaryMood || undefined,
          newsletterOptIn,
        },
      })
      setSubmitMessage('Your preferences are saved.')
    } catch (error) {
      const message = error instanceof Error && error.message ? error.message : 'We could not update your profile.'
      setSubmitMessage(message)
    }
  }

  const feedback = submitMessage ?? authError

  if (!user) {
    return (
      <div className="guard guard--loading" role="status" aria-live="polite">
        <div className="spinner" />
        <p>Loading your profile…</p>
      </div>
    )
  }

  return (
    <div className="profile-page" data-testid="profile-page">
      <section className="panel profile-panel">
        <header className="panel__header">
          <div>
            <p className="panel__eyebrow">Account</p>
            <h1>Your profile</h1>
            <p className="panel__subtitle">
              Fine-tune how Auragraph recognises your tastes. These preferences feed into the recommendations you see
              across discovery.
            </p>
          </div>
          {user && (
            <div className="profile-summary" aria-live="polite">
              <p>
                Signed in as <strong>{user.email}</strong>
              </p>
            </div>
          )}
        </header>
        <form className="panel__body profile-form" onSubmit={handleSubmit} noValidate>
          <div className="profile-form__grid">
            <label className="field profile-field">
              <span>Display name</span>
              <input
                type="text"
                value={displayName}
                onChange={(event) => {
                  setDisplayName(event.target.value)
                  setSubmitMessage(null)
                  clearError()
                }}
                required
              />
            </label>
            <label className="field profile-field">
              <span>About you</span>
              <textarea
                value={bio}
                onChange={(event) => {
                  setBio(event.target.value)
                  setSubmitMessage(null)
                  clearError()
                }}
                rows={4}
                placeholder="Share what inspires your mixes, collaborators, or projects."
              />
            </label>
            <label className="field profile-field">
              <span>Preferred genre</span>
              <select
                value={primaryGenre}
                onChange={(event) => {
                  setPrimaryGenre(event.target.value)
                  setSubmitMessage(null)
                  clearError()
                }}
              >
                <option value="">Open to anything</option>
                {genreOptions.map((genre) => (
                  <option key={genre} value={genre}>
                    {genre}
                  </option>
                ))}
              </select>
            </label>
            <label className="field profile-field">
              <span>Preferred mood</span>
              <select
                value={primaryMood}
                onChange={(event) => {
                  setPrimaryMood(event.target.value)
                  setSubmitMessage(null)
                  clearError()
                }}
              >
                <option value="">Let the atmosphere evolve</option>
                {availableMoods.map((mood) => (
                  <option key={mood} value={mood}>
                    {mood}
                  </option>
                ))}
              </select>
            </label>
            <label className="field field--inline profile-field">
              <span>Creative pulses</span>
              <span className="switch">
                <input
                  type="checkbox"
                  checked={newsletterOptIn}
                  onChange={(event) => {
                    setNewsletterOptIn(event.target.checked)
                    setSubmitMessage(null)
                    clearError()
                  }}
                />
                <span className="switch__label">Email me blend-friendly drops, curators, and tonal studies.</span>
              </span>
            </label>
          </div>
          {feedback && (
            <div className={`auth-form__${submitMessage && !authError ? 'success' : 'error'}`} role="status">
              <p>{feedback}</p>
            </div>
          )}
          <div className="profile-form__actions">
            <button type="submit" className="button" disabled={isProcessing || !isDirty}>
              {isProcessing ? 'Saving changes…' : 'Save preferences'}
            </button>
          </div>
        </form>
      </section>
      <section className="panel profile-recommendations">
        <header className="panel__header">
          <div>
            <h2>Recommended for you</h2>
            <p className="panel__subtitle">
              We’re tuning selections to match your playlists. Fresh picks will appear here once we have more to go on.
            </p>
          </div>
        </header>
        <div className="panel__body panel__body--centered profile-recommendations__body" role="status">
          <div className="profile-recommendations__placeholder">
            <p>Keep exploring and saving items. We’ll surface bespoke film & sound combinations tailored to your vibe.</p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default Profile
