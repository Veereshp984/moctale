import { useEffect } from 'react'
import {
  Compass,
  ListMusic,
  Loader2,
  LogIn,
  Menu,
  MoonStar,
  Sparkles,
  Sun,
  UserRound,
} from 'lucide-react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import clsx from 'clsx'

import { Button } from '@/components/ui/Button'
import { useAppStore } from '@/store/appStore'

const navigationItems = [
  { label: 'Discovery', to: '/discovery', icon: Compass },
  { label: 'Playlists', to: '/playlists', icon: ListMusic },
  { label: 'Profile', to: '/profile', icon: UserRound },
  { label: 'Auth', to: '/auth', icon: LogIn },
]

const AppLayout = () => {
  const location = useLocation()
  const theme = useAppStore((state) => state.theme)
  const toggleTheme = useAppStore((state) => state.toggleTheme)
  const isSidebarOpen = useAppStore((state) => state.isSidebarOpen)
  const toggleSidebar = useAppStore((state) => state.toggleSidebar)
  const closeSidebar = useAppStore((state) => state.closeSidebar)
  const setSyncing = useAppStore((state) => state.setSyncing)
  const user = useAppStore((state) => state.user)
  const isSyncing = useAppStore((state) => state.isSyncing)

  useEffect(() => {
    if (typeof document === 'undefined') {
      return
    }

    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(theme)
  }, [theme])

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const timeout = window.setTimeout(() => setSyncing(false), 1600)
    return () => window.clearTimeout(timeout)
  }, [setSyncing])

  useEffect(() => {
    closeSidebar()
  }, [location.pathname, closeSidebar])

  return (
    <div className="bg-background text-foreground">
      <div className="flex min-h-screen">
        {isSidebarOpen && (
          <button
            type="button"
            aria-label="Close navigation"
            onClick={closeSidebar}
            className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm lg:hidden"
          />
        )}

        <aside
          className={clsx(
            'fixed inset-y-0 left-0 z-40 w-72 border-r border-border bg-surface/95 px-6 py-10 shadow-soft transition-transform duration-200 ease-out backdrop-blur lg:static lg:translate-x-0',
            {
              '-translate-x-full lg:-translate-x-0': !isSidebarOpen,
              'translate-x-0': isSidebarOpen,
            },
          )}
        >
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-soft">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-muted-foreground">Soundwave</p>
              <p className="text-lg font-semibold">Creative Studio</p>
            </div>
          </div>

          <nav className="mt-10 flex flex-col gap-1">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary',
                      isActive
                        ? 'bg-primary text-primary-foreground shadow-soft'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground',
                    )
                  }
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              )
            })}
          </nav>

          <div className="mt-12 rounded-2xl border border-border bg-muted/40 p-5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Library health
            </p>
            <div className="mt-4 flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-accent" />
              <div>
                <p className="text-sm font-semibold">Syncing with catalog…</p>
                <p className="text-xs text-muted-foreground">
                  We keep your collections fresh and discoverable.
                </p>
              </div>
            </div>
          </div>
        </aside>

        <div className="flex min-h-screen flex-1 flex-col lg:ml-0">
          <header className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-surface/90 px-4 py-4 backdrop-blur">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={toggleSidebar}
                aria-label="Toggle navigation menu"
              >
                <Menu className="h-5 w-5" />
              </Button>
              <div className="hidden flex-col lg:flex">
                <span className="text-xs uppercase tracking-widest text-muted-foreground">
                  Welcome back
                </span>
                <span className="text-lg font-semibold">{user.displayName}</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={toggleTheme}
                aria-label="Toggle theme"
              >
                {theme === 'dark' ? <Sun className="h-5 w-5" /> : <MoonStar className="h-5 w-5" />}
              </Button>
              <span className="hidden h-9 items-center rounded-full border border-border bg-muted/60 px-3 text-sm font-medium text-muted-foreground md:flex">
                {isSyncing ? (
                  <span className="flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Syncing assets
                  </span>
                ) : (
                  'Library up to date'
                )}
              </span>
              <div className="flex h-10 w-10 items-center justify-center rounded-full border border-primary/20 bg-primary/10 text-sm font-semibold text-primary">
                {user.initials}
              </div>
            </div>
          </header>

          <main className="flex-1 px-4 py-6 lg:px-10">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  )
}

export default AppLayout
