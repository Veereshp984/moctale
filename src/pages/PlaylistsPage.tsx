import { Link } from 'react-router-dom'
import { Clock3, ListMusic, Music4, Plus } from 'lucide-react'

import { Button, buttonClasses } from '@/components/ui/Button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card'
import { Loader } from '@/components/ui/Loader'
import { usePlaylists } from '@/hooks/usePlaylists'

const PlaylistsPage = () => {
  const { playlists, isLoading, isError, error, refresh } = usePlaylists()
  const totalTracks = playlists.reduce((sum, playlist) => sum + playlist.trackCount, 0)

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold lg:text-4xl">Curated playlists</h1>
          <p className="mt-2 max-w-2xl text-base text-muted-foreground">
            Manage your collections, track recent updates, and collaborate with other members of the
            collective.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" className="gap-2" onClick={() => refresh()}>
            <Clock3 className="h-4 w-4" /> Refresh status
          </Button>
          <Link to="/auth" className={buttonClasses('primary', 'md', 'gap-2')}>
            <Plus className="h-4 w-4" /> Invite curator
          </Link>
        </div>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="col-span-1 bg-gradient-to-br from-primary to-accent text-primary-foreground shadow-soft">
          <CardHeader>
            <CardTitle className="text-primary-foreground">Library overview</CardTitle>
            <CardDescription className="text-primary-foreground/75">
              A snapshot of your current playlists and total tracks across the studio.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 text-primary-foreground">
            <div>
              <p className="text-sm uppercase tracking-wide text-primary-foreground/70">Playlists</p>
              <p className="mt-1 text-3xl font-semibold">{playlists.length}</p>
            </div>
            <div>
              <p className="text-sm uppercase tracking-wide text-primary-foreground/70">Tracks curated</p>
              <p className="mt-1 text-3xl font-semibold">{totalTracks}</p>
            </div>
          </CardContent>
          <CardFooter>
            <span className="text-xs uppercase tracking-widest text-primary-foreground/70">
              Continuous improvement
            </span>
            <Button variant="outline" className="border-primary/40 bg-primary/10 text-primary-foreground">
              View insights
            </Button>
          </CardFooter>
        </Card>
      </section>

      {isLoading ? <Loader label="Gathering the latest playlists" /> : null}

      {isError ? (
        <Card className="border border-rose-500/70 bg-rose-500/10 p-6">
          <CardHeader>
            <CardTitle>Couldn&apos;t load playlists</CardTitle>
            <CardDescription>
              {error?.message ?? 'Something went wrong. Please retry in a few moments.'}
            </CardDescription>
          </CardHeader>
          <CardFooter>
            <Button variant="secondary" onClick={() => refresh()}>
              Try again
            </Button>
          </CardFooter>
        </Card>
      ) : null}

      {!isLoading && !isError ? (
        <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          {playlists.map((playlist) => (
            <Card key={playlist.id} className="flex h-full flex-col justify-between">
              <CardHeader>
                <div className="flex items-center gap-4">
                  <div className={`h-12 w-12 rounded-2xl ${playlist.coverColor}`} aria-hidden="true" />
                  <div>
                    <CardTitle className="text-lg">{playlist.title}</CardTitle>
                    <CardDescription>{playlist.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Music4 className="h-4 w-4" /> {playlist.trackCount} tracks • {playlist.mood}
                </div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <ListMusic className="h-4 w-4" /> Updated {playlist.updatedAt}
                </div>
              </CardContent>
              <CardFooter>
                <Button variant="ghost" size="sm">
                  Open in editor
                </Button>
                <Button variant="outline" size="sm">
                  Share
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export default PlaylistsPage
