import DiscoverySection from '../components/DiscoverySection'
import PlaylistManager from '../components/PlaylistManager'
import RecommendationGrid from '../components/RecommendationGrid'
import { usePlaylist } from '../context/PlaylistContext'
import { formatDuration } from '../utils/format'

const Dashboard = () => {
  const { playlist, addItem, hasItem, isLoading } = usePlaylist()

  const totalDurationMinutes = playlist?.items.reduce((acc, item) => acc + (item.durationMinutes ?? 0), 0) ?? 0
  const totalItems = playlist?.items.length ?? 0

  return (
    <div className="dashboard" data-testid="dashboard">
      <section className="hero">
        <div>
          <h1>Blend stories & sound effortlessly</h1>
          <p>
            Build a living playlist that merges cinematic moments with audio gems. Discover new media, curate the
            perfect order, and share it broadly.
          </p>
        </div>
        <dl className="hero__metrics">
          <div>
            <dt>Playlist items</dt>
            <dd data-testid="metric-item-count">{totalItems}</dd>
          </div>
          <div>
            <dt>Total playtime</dt>
            <dd>{formatDuration(totalDurationMinutes)}</dd>
          </div>
          <div>
            <dt>Last updated</dt>
            <dd>{playlist ? new Date(playlist.updatedAt).toLocaleDateString() : '—'}</dd>
          </div>
        </dl>
      </section>
      <RecommendationGrid />
      <DiscoverySection
        onAddToPlaylist={addItem}
        isInPlaylist={hasItem}
        canMutate={!isLoading && Boolean(playlist)}
        playlistLoading={isLoading}
      />
      <PlaylistManager />
    </div>
  )
}

export default Dashboard
