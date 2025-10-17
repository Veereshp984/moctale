import { useEffect, useState } from 'react'
import { usePlaylist } from '../context/PlaylistContext'
import { getRecommendations } from '../services/api'
import type { Recommendation } from '../types'
import MediaCard from './MediaCard'

const RecommendationGrid = () => {
  const { playlist, addItem, hasItem, isLoading } = usePlaylist()
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    const loadRecommendations = async () => {
      setLoading(true)
      setError(null)
      try {
        const results = await getRecommendations(playlist)
        if (!cancelled) {
          setRecommendations(results)
        }
      } catch (err) {
        console.error('Failed to load recommendations', err)
        if (!cancelled) {
          setError('Unable to load personalized picks right now.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadRecommendations()

    return () => {
      cancelled = true
    }
  }, [playlist])

  return (
    <section className="panel" id="recommendations" data-testid="recommendations">
      <header className="panel__header">
        <div>
          <h2>Personalized suggestions</h2>
          <p className="panel__subtitle">
            Smart picks that respond to the tones, moods, and genres living in your playlist.
          </p>
        </div>
      </header>
      <div className="panel__body">
        {loading ? (
          <div className="recommendations-loading" role="status" aria-live="polite">
            <div className="spinner" />
            <p>Curating something special…</p>
          </div>
        ) : error ? (
          <div className="recommendations-error" role="alert">
            <p>{error}</p>
          </div>
        ) : recommendations.length === 0 ? (
          <div className="recommendations-empty">
            <p>Add a few items to your playlist to activate tailored recommendations.</p>
          </div>
        ) : (
          <div className="media-grid media-grid--compact">
            {recommendations.map((recommendation) => {
              const alreadyInPlaylist = hasItem(recommendation.item)
              const disabled = !playlist || isLoading
              const addLabel = alreadyInPlaylist
                ? 'Already in playlist'
                : disabled
                  ? 'Playlist syncing…'
                  : undefined

              return (
                <MediaCard
                  key={recommendation.id}
                  item={recommendation.item}
                  onAdd={!disabled ? addItem : undefined}
                  inPlaylist={alreadyInPlaylist}
                  annotation={recommendation.reason}
                  disabled={disabled || alreadyInPlaylist}
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

export default RecommendationGrid
