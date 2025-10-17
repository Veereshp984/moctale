import { useCallback, useEffect, useMemo, useState } from 'react'
import { getMediaFilters, getPopularMedia, searchMedia } from '../services/api'
import type { MediaItem, MediaType } from '../types'
import MediaCard from './MediaCard'

interface DiscoverySectionProps {
  onAddToPlaylist: (item: MediaItem) => void
  isInPlaylist: (item: MediaItem) => boolean
  canMutate?: boolean
  playlistLoading?: boolean
}

type MediaTab = MediaType | 'all'

type FetchState = 'popular' | 'search'

const DiscoverySection = ({
  onAddToPlaylist,
  isInPlaylist,
  canMutate = true,
  playlistLoading = false,
}: DiscoverySectionProps) => {
  const [mediaType, setMediaType] = useState<MediaTab>('all')
  const [genre, setGenre] = useState<string>('all')
  const [mood, setMood] = useState<string>('all')
  const [query, setQuery] = useState('')
  const [activeQuery, setActiveQuery] = useState('')
  const [items, setItems] = useState<MediaItem[]>([])
  const [state, setState] = useState<FetchState>('popular')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const filters = useMemo(() => getMediaFilters(), [])

  const appliedGenre = genre === 'all' ? undefined : genre
  const appliedMood = mood === 'all' ? undefined : mood

  const genreOptions = useMemo(() => {
    if (mediaType === 'movie') {
      return filters.movieGenres
    }

    if (mediaType === 'music') {
      return filters.musicGenres
    }

    const combined = new Set([...filters.movieGenres, ...filters.musicGenres])
    return [...combined.values()]
  }, [filters, mediaType])

  const fetchContent = useCallback(
    async (mode: FetchState, currentQuery?: string) => {
      setLoading(true)
      setError(null)

      try {
        if (mode === 'search' && currentQuery) {
          const results = await searchMedia(currentQuery, mediaType, {
            genre: appliedGenre,
            mood: appliedMood,
          })
          setItems(results)
        } else {
          const results = await getPopularMedia(mediaType, {
            genre: appliedGenre,
            mood: appliedMood,
          })
          setItems(results)
        }
      } catch (err) {
        console.error('Failed to fetch media', err)
        setError('We were unable to load titles. Please refresh or adjust filters.')
      } finally {
        setLoading(false)
      }
    },
    [appliedGenre, appliedMood, mediaType],
  )

  useEffect(() => {
    const mode = activeQuery ? 'search' : 'popular'
    setState(mode)
    void fetchContent(mode, activeQuery)
  }, [activeQuery, fetchContent, mediaType, appliedGenre, appliedMood])

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmed = query.trim()
    setActiveQuery(trimmed)
  }

  const handleClear = () => {
    setQuery('')
    setActiveQuery('')
  }

  return (
    <section className="panel" id="discover" data-testid="discovery-section">
      <header className="panel__header">
        <div>
          <h2>Discover new favourites</h2>
          <p className="panel__subtitle">
            Explore films & tracks from our curated catalogue. Mix both or focus on exactly what you need.
          </p>
        </div>
      </header>
      <div className="discovery-controls">
        <div className="discovery-tabs" role="tablist" aria-label="Media type">
          {(
            [
              { id: 'all', label: 'All' },
              { id: 'movie', label: 'Films' },
              { id: 'music', label: 'Music' },
            ] satisfies { id: MediaTab; label: string }[]
          ).map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={mediaType === tab.id}
              className={`chip ${mediaType === tab.id ? 'chip--active' : ''}`}
              onClick={() => {
                setMediaType(tab.id)
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <form className="discovery-search" onSubmit={handleSubmit} role="search" aria-label="Search media">
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by title, creator, or mood"
            aria-label="Search catalogue"
          />
          <button type="submit" className="button">
            Search
          </button>
          <button type="button" className="button button--ghost" onClick={handleClear} disabled={!activeQuery && !query}>
            Clear
          </button>
        </form>
        <div className="discovery-filters">
          <label className="field">
            <span>Genre</span>
            <select value={genre} onChange={(event) => setGenre(event.target.value)}>
              <option value="all">All genres</option>
              {genreOptions.map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Mood</span>
            <select value={mood} onChange={(event) => setMood(event.target.value)}>
              <option value="all">All moods</option>
              {filters.moods.map((entry) => (
                <option key={entry} value={entry}>
                  {entry}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>
      {!canMutate && playlistLoading && (
        <p className="discovery-hint" role="status">
          Syncing your saved playlist so additions stay in step…
        </p>
      )}
      <div className="discovery-results" data-state={state}>
        {loading ? (
          <div className="discovery-loading" role="status" aria-live="polite">
            <div className="spinner" />
            <p>Loading curated selections…</p>
          </div>
        ) : error ? (
          <div className="discovery-error" role="alert">
            <p>{error}</p>
            <button type="button" className="button button--ghost" onClick={() => void fetchContent(state, activeQuery)}>
              Try again
            </button>
          </div>
        ) : items.length === 0 ? (
          <div className="discovery-empty">
            <p>No results just yet. Try tweaking filters or searching something new.</p>
          </div>
        ) : (
          <div className="media-grid" data-testid="discovery-results">
            {items.map((item) => {
              const alreadyInPlaylist = isInPlaylist(item)
              const disabled = alreadyInPlaylist || !canMutate
              const addLabel = alreadyInPlaylist
                ? 'Already in playlist'
                : canMutate
                  ? 'Add to playlist'
                  : playlistLoading
                    ? 'Loading playlist…'
                    : 'Playlist unavailable'

              return (
                <MediaCard
                  key={item.id}
                  item={item}
                  onAdd={canMutate ? onAddToPlaylist : undefined}
                  inPlaylist={alreadyInPlaylist}
                  disabled={disabled}
                  addLabel={addLabel}
                />
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}

export default DiscoverySection
