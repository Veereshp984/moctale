import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getPlaylistById } from '../services/api'
import type { Playlist } from '../types'
import { formatDuration } from '../utils/format'

const PublicPlaylist = () => {
  const { playlistId } = useParams<{ playlistId: string }>()
  const [playlist, setPlaylist] = useState<Playlist | null>(null)
  const [status, setStatus] = useState<'loading' | 'ready' | 'not-found' | 'error'>('loading')

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      if (!playlistId) {
        setStatus('not-found')
        return
      }

      try {
        const result = await getPlaylistById(playlistId)
        if (cancelled) {
          return
        }

        if (!result || !result.isPublic) {
          setStatus('not-found')
          return
        }

        setPlaylist(result)
        setStatus('ready')
      } catch (error) {
        console.error('Failed to load public playlist', error)
        if (!cancelled) {
          setStatus('error')
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [playlistId])

  if (status === 'loading') {
    return (
      <div className="public-playlist" data-testid="public-playlist">
        <div className="panel">
          <div className="panel__body panel__body--centered" role="status">
            <div className="spinner" />
            <p>Loading playlist…</p>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'not-found') {
    return (
      <div className="public-playlist" data-testid="public-playlist">
        <div className="panel">
          <div className="panel__body panel__body--centered" role="alert">
            <h2>Playlist unavailable</h2>
            <p>This playlist either does not exist or is no longer shared publicly.</p>
            <Link className="button" to="/">
              Back to discovery
            </Link>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'error' || !playlist) {
    return (
      <div className="public-playlist" data-testid="public-playlist">
        <div className="panel">
          <div className="panel__body panel__body--centered" role="alert">
            <h2>We ran into an issue</h2>
            <p>Something went wrong while loading this playlist. Please try again later.</p>
            <Link className="button" to="/">
              Back to discovery
            </Link>
          </div>
        </div>
      </div>
    )
  }

  const totalMinutes = playlist.items.reduce((acc, item) => acc + (item.durationMinutes ?? 0), 0)

  return (
    <div className="public-playlist" data-testid="public-playlist">
      <section className="panel">
        <header className="panel__header">
          <div>
            <p className="panel__eyebrow">Shared playlist</p>
            <h1>{playlist.name}</h1>
            <p className="panel__subtitle">{playlist.description}</p>
          </div>
        </header>
        <div className="panel__body">
          <div className="public-playlist__summary">
            <p>
              Curated with <strong>{playlist.items.length}</strong> selections · {formatDuration(totalMinutes)} of combined playtime
            </p>
            <p>Updated {new Date(playlist.updatedAt).toLocaleString()}</p>
          </div>
          <ol className="playlist-list playlist-list--public">
            {playlist.items.map((item, index) => (
              <li key={item.playlistItemId ?? `${item.type}-${item.id}-${index}`}
                className="playlist-item"
              >
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
              </li>
            ))}
          </ol>
          <div className="public-playlist__cta">
            <p>Like what you hear? Build your own blend back in discovery.</p>
            <Link className="button" to="/">
              Build your playlist
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

export default PublicPlaylist
