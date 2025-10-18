import { useState } from 'react'
import { BadgeCheck, LogOut, UserCog } from 'lucide-react'

import { Button } from '@/components/ui/Button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { useAppStore } from '@/store/appStore'

const ProfilePage = () => {
  const user = useAppStore((state) => state.user)
  const theme = useAppStore((state) => state.theme)
  const toggleTheme = useAppStore((state) => state.toggleTheme)
  const [isModalOpen, setModalOpen] = useState(false)

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold lg:text-4xl">Profile</h1>
          <p className="mt-2 max-w-2xl text-base text-muted-foreground">
            Manage your curator details, security preferences, and collaborative status.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" className="gap-2" onClick={toggleTheme}>
            Toggle theme ({theme})
          </Button>
          <Button variant="ghost" className="gap-2 text-rose-500">
            <LogOut className="h-4 w-4" /> Sign out
          </Button>
        </div>
      </header>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-xl font-semibold text-primary">
                {user.initials}
              </span>
              {user.displayName}
              <BadgeCheck className="h-5 w-5 text-accent" />
            </CardTitle>
            <CardDescription className="text-base">
              {user.role} • {user.followers} followers • {user.following} following
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-muted-foreground">
            <p>
              Share your sonic identity, link collaborative spaces, and control who can request access to
              your playlists.
            </p>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-border/80 bg-muted/40 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Primary channel</p>
                <p className="mt-1 font-medium text-foreground">hello@soundwave.fm</p>
              </div>
              <div className="rounded-2xl border border-border/80 bg-muted/40 px-4 py-3">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Timezone</p>
                <p className="mt-1 font-medium text-foreground">Europe/Berlin</p>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button className="gap-2" onClick={() => setModalOpen(true)}>
              <UserCog className="h-4 w-4" /> Edit profile
            </Button>
            <Button variant="ghost">View public page</Button>
          </CardFooter>
        </Card>

        <Card className="border-dashed border-accent/60 bg-accent/10">
          <CardHeader>
            <CardTitle>Collaboration status</CardTitle>
            <CardDescription>
              Share this status with fellow curators so they know when you&apos;re available to collaborate.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <p>Currently accepting submissions for cinematic and ambient playlists.</p>
            <p>Next live listening session: Friday 19:00 CET.</p>
          </CardContent>
        </Card>
      </section>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setModalOpen(false)}
        title="Edit profile"
        description="Refine how other curators see and collaborate with you."
      >
        <form className="grid gap-4">
          <label className="grid gap-2 text-sm font-medium">
            Display name
            <input
              defaultValue={user.displayName}
              className="h-11 rounded-xl border border-border bg-background px-4 text-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Role
            <input
              defaultValue={user.role}
              className="h-11 rounded-xl border border-border bg-background px-4 text-base focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
            />
          </label>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setModalOpen(false)} type="button">
              Cancel
            </Button>
            <Button type="submit">Save changes</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}

export default ProfilePage
