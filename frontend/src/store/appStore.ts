import { create } from 'zustand'

export type ThemeMode = 'light' | 'dark'

export interface DiscoveryItem {
  id: string
  title: string
  description: string
  tags: string[]
  listens: number
}

export interface PlaylistSummary {
  id: string
  title: string
  description: string
  updatedAt: string
  mood: string
  trackCount: number
  coverColor: string
}

export interface UserProfile {
  id: string
  displayName: string
  role: string
  initials: string
  followers: number
  following: number
}

interface AppState {
  theme: ThemeMode
  isSidebarOpen: boolean
  isSyncing: boolean
  discoveryFeed: DiscoveryItem[]
  playlists: PlaylistSummary[]
  user: UserProfile
  setTheme: (theme: ThemeMode) => void
  toggleTheme: () => void
  toggleSidebar: () => void
  setSidebarOpen: (isOpen: boolean) => void
  closeSidebar: () => void
  setDiscoveryFeed: (feed: DiscoveryItem[]) => void
  setPlaylists: (playlists: PlaylistSummary[]) => void
  setSyncing: (value: boolean) => void
}

const THEME_STORAGE_KEY = 'soundwave:theme'

const resolveInitialTheme = (): ThemeMode => {
  if (typeof window === 'undefined') {
    return 'light'
  }

  const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY) as ThemeMode | null
  if (storedTheme === 'light' || storedTheme === 'dark') {
    return storedTheme
  }

  const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
  return prefersDark ? 'dark' : 'light'
}

export const useAppStore = create<AppState>((set) => ({
  theme: resolveInitialTheme(),
  isSidebarOpen: false,
  isSyncing: true,
  discoveryFeed: [],
  playlists: [],
  user: {
    id: 'user-1',
    displayName: 'Indie Sound Collective',
    initials: 'IS',
    role: 'Curator',
    followers: 1280,
    following: 214,
  },
  setTheme: (theme) => {
    set({ theme })
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    }
  },
  toggleTheme: () => {
    set((state) => {
      const nextTheme = state.theme === 'dark' ? 'light' : 'dark'
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme)
      }
      return { theme: nextTheme }
    })
  },
  toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
  setSidebarOpen: (isOpen) => set({ isSidebarOpen: isOpen }),
  closeSidebar: () => set({ isSidebarOpen: false }),
  setDiscoveryFeed: (feed) => set({ discoveryFeed: feed }),
  setPlaylists: (playlists) => set({ playlists }),
  setSyncing: (value) => set({ isSyncing: value }),
}))
