import { useMemo, useState } from 'react'
import { usePlaylist } from '../context/PlaylistContext'
import { formatDuration } from '../utils/format'
import ShareControls from './ShareControls'

const PlaylistManager = () => {
  const { playlist, isLoading, error, removeItem, moveItem, updateMetadata, save, isSaving } = usePlaylist()
  const [savingState, setSavingState] = useState<'idle' | 'saved'>('idle')

  const totals = useMemo(() => {
    if (!playlist) {
      return { totalMinutes: 0 }
    }

    const totalMinutes = playlist.items.reduce((acc, item) => acc + (item.durationMinutes ?? 0), 0)
    return { totalMinutes }
  }, [playlist])

  if (isLoading) {
    return (
      <section className="panel" id="playlist-manager" data-testid="playlist-manager">
        <header className="panel__header">
          <div>
            <h2>Your playlist</h2>
            <p className="panel__subtitle">We are loading your saved selections…</p>
          </div>
        </header>
        <div className="panel__body panel__body--centered" role="status" aria-live="polite">
          <div className="spinner" />
        </div>
      </section>
    )
  }

  if (!playlist) {
    return (
      <section className="panel" id="playlist-manager" data-testid="playlist-manager">
        <header className="panel__header">
          <div>
            <h2>Your playlist</h2>
            <p className="panel__subtitle">We could not load your playlist right now.</p>
          </div>
        </header>
        <div className="panel__body panel__body--centered" role="alert">
          <p>{error ?? 'Unexpected error.'}</p>
        </div>
      </section>
    )
  }

  const handleSave = async () => {
    setSavingState('idle')
    const success = await save()
    if (success) {
      setSavingState('saved')
      setTimeout(() => setSavingState('idle'), 2200)
    }
  }

  return (
    <section className="panel" id="playlist-manager" data-testid="playlist-manager">
      <header className="panel__header">
        <div>
          <h2>Playlist management</h2>
          <p className="panel__subtitle">
            Arrange your mixed-media playlist, set a vibe, and share it with friends or your community.
          </p>
        </div>
      </header>
      <div className="panel__body">
        <div className="playlist-config">
          <label className="field">
            <span>Title</span>
            <input
              value={playlist.name}
              onChange={(event) => updateMetadata({ name: event.target.value })}
              placeholder="Give your playlist a name"
              data-testid="playlist-name"
            />
          </label>
          <label className="field">
            <span>Description</span>
            <textarea
              value={playlist.description}
              onChange={(event) => updateMetadata({ description: event.target.value })}
              placeholder="Tell listeners what to expect"
              rows={2}
              data-testid="playlist-description"
            />
          </label>
          <label className="switch">
            <input
              type="checkbox"
              checked={playlist.isPublic}
              onChange={(event) => updateMetadata({ isPublic: event.target.checked })}
              data-testid="playlist-public-toggle"
            />
            <span className="switch__label">Make playlist public</span>
          </label>
        </div>
        {playlist.items.length === 0 ? (
          <div className="playlist-empty" role="status">
            <p>Your playlist is empty. Add films or music from discovery to start curating.</p>
          </div>
        ) : (
          <ol className="playlist-list" data-testid="playlist-items">
            {playlist.items.map((item, index) => (
              <li key={item.playlistItemId} className="playlist-item" data-testid="playlist-item">
                <div className="playlist-item__details">
                  <span className={`pill pill--${item.type}`}>{item.type === 'movie' ? 'Film' : 'Track'}</span>
                  <div>
                    <h3>{item.title}</h3>
                    <p>
                      {item.creator} · {item.releaseYear}
                    </p>
                    <p className="playlist-item__meta">
                      {item.genres.join(', ')} · {item.durationMinutes} min
                    </p>
                  </div>
                </div>
                <div className="playlist-item__actions">
                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => moveItem(index, index - 1)}
                    aria-label="Move item up"
                    disabled={index === 0}
                    data-testid="move-item-up"
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    className="icon-button"
                    onClick={() => moveItem(index, index + 1)}
                    aria-label="Move item down"
                    disabled={index === playlist.items.length - 1}
                    data-testid="move-item-down"
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    className="icon-button icon-button--danger"
                    onClick={() => removeItem(item.playlistItemId)}
                    aria-label="Remove from playlist"
                    data-testid="remove-item"
                  >
                    ✕
                  </button>
                </div>
              </li>
            ))}
          </ol>
        )}
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div className="playlist-footer">
          <div className="playlist-summary">
            <p>
              <strong>{playlist.items.length}</strong> items · {formatDuration(totals.totalMinutes)} total playtime
            </p>
            <p className="playlist-summary__updated">Last updated {new Date(playlist.updatedAt).toLocaleString()}</p>
          </div>
          <div className="playlist-actions">
            <button
              type="button"
              className="button"
              onClick={() => void handleSave()}
              disabled={isSaving || playlist.items.length === 0}
              data-testid="save-playlist"
            >
              {isSaving ? 'Saving…' : 'Save playlist'}
            </button>
            {savingState === 'saved' && <span role="status">Saved!</span>}
          </div>
        </div>
      </div>
      {playlist.isPublic && (
        <div className="panel__body panel__body--soft">
          <ShareControls playlistId={playlist.id} playlistName={playlist.name} description={playlist.description} />
        </div>
      )}
    </section>
  )
}

export default PlaylistManager
