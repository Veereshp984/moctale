import { Link } from 'react-router-dom'
import { Flame, RefreshCw, Sparkle } from 'lucide-react'

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
import { useDiscoveryFeed } from '@/hooks/useDiscoveryFeed'

const DiscoveryPage = () => {
  const { feed, isLoading, isError, error, refresh } = useDiscoveryFeed()

  return (
    <div className="space-y-10">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold lg:text-4xl">Discovery dashboard</h1>
          <p className="mt-2 max-w-2xl text-base text-muted-foreground">
            Track the latest playlists shared by the collective and surface new tracks that resonate with
            your creative direction.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="outline" className="gap-2" onClick={() => refresh()}>
            <RefreshCw className="h-4 w-4" /> Refresh feed
          </Button>
          <Link to="/playlists" className={buttonClasses('primary', 'md', 'gap-2')}>
            <Sparkle className="h-4 w-4" /> Curate a playlist
          </Link>
        </div>
      </header>

      {isLoading ? (
        <Card className="flex flex-col gap-4 p-6">
          <CardHeader>
            <CardTitle>Curating your recommendations</CardTitle>
            <CardDescription>
              We&apos;re analysing collective trends and your favourite moods to suggest fresh material.
            </CardDescription>
          </CardHeader>
          <Loader label="Building personalised feed" />
        </Card>
      ) : null}

      {isError ? (
        <Card className="border-dashed border-2 border-rose-400/80 bg-rose-500/10 p-6">
          <CardHeader>
            <CardTitle>We hit a small snag</CardTitle>
            <CardDescription>
              {error?.message ?? 'An unexpected error occurred while loading the discovery feed.'}
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
          {feed.map((item) => (
            <Card key={item.id} className="flex h-full flex-col justify-between">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                    <Flame className="h-5 w-5" />
                  </span>
                  <div>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                    <CardDescription>{item.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2">
                {item.tags.map((tag) => (
                  <span
                    key={`${item.id}-${tag}`}
                    className="rounded-full bg-muted px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                  >
                    {tag}
                  </span>
                ))}
              </CardContent>
              <CardFooter className="flex items-center justify-between text-xs text-muted-foreground">
                <span>{new Intl.NumberFormat().format(item.listens)} curator plays</span>
                <Button variant="ghost" size="sm" className="gap-1 text-xs">
                  Add to queue
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export default DiscoveryPage
