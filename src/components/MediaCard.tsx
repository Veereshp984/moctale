import type { MediaItem } from '../types'

interface MediaCardProps {
  item: MediaItem
  onAdd?: (item: MediaItem) => void
  inPlaylist?: boolean
  annotation?: string
  disabled?: boolean
  addLabel?: string
}

const MediaCard = ({
  item,
  onAdd,
  inPlaylist = false,
  annotation,
  disabled = false,
  addLabel,
}: MediaCardProps) => {
  const handleAdd = () => {
    if (disabled || inPlaylist) {
      return
    }

    if (onAdd) {
      onAdd(item)
    }
  }

  return (
    <article className="media-card" data-testid="media-card">
      <div className="media-card__artwork" aria-hidden="true">
        <img src={item.artwork} alt="" loading="lazy" />
        <span className={`media-card__badge media-card__badge--${item.type}`}>
          {item.type === 'movie' ? 'Film' : 'Track'}
        </span>
      </div>
      <div className="media-card__body">
        <header className="media-card__header">
          <h3>{item.title}</h3>
          <p>{item.creator}</p>
        </header>
        {annotation && <p className="media-card__annotation">{annotation}</p>}
        <p className="media-card__description">{item.description}</p>
        <div className="media-card__meta">
          <span>{item.releaseYear}</span>
          <span>{item.durationMinutes} min</span>
          <span>{item.genres.join(', ')}</span>
        </div>
        <div className="media-card__footer">
          <button
            type="button"
            className="button button--ghost"
            onClick={handleAdd}
            disabled={disabled || inPlaylist}
            data-testid="media-card-add"
          >
            {addLabel ?? (inPlaylist ? 'Already in playlist' : 'Add to playlist')}
          </button>
        </div>
      </div>
    </article>
  )
}

export default MediaCard
