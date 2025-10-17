import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import type { ReactNode } from 'react'
import type { MediaItem, Playlist, PlaylistItem } from '../types'
import { DEFAULT_PLAYLIST_ID, createDefaultPlaylist, getPlaylist, savePlaylist } from '../services/api'

interface PlaylistContextValue {
  playlist: Playlist | null
  isLoading: boolean
  isSaving: boolean
  error: string | null
  addItem: (item: MediaItem) => void
  removeItem: (playlistItemId: string) => void
  moveItem: (startIndex: number, destinationIndex: number) => void
  updateMetadata: (updates: Partial<Pick<Playlist, 'name' | 'description' | 'isPublic' | 'coverImage'>>) => void
  save: () => Promise<boolean>
  hasItem: (item: MediaItem) => boolean
  reset: () => void
}

const PlaylistContext = createContext<PlaylistContextValue | undefined>(undefined)

const generatePlaylistItemId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  return `playlist-item-${Math.random().toString(36).slice(2, 10)}`
}

const clonePlaylist = (playlist: Playlist | null): Playlist | null => {
  if (!playlist) {
    return null
  }

  return {
    ...playlist,
    items: playlist.items.map((item) => ({ ...item })),
  }
}

export const PlaylistProvider = ({ children }: { children: ReactNode }) => {
  const [playlist, setPlaylist] = useState<Playlist | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadPlaylist = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    try {
      const current = await getPlaylist(DEFAULT_PLAYLIST_ID)
      setPlaylist(current)
    } catch (err) {
      console.error('Failed to load playlist', err)
      setError('Unable to load your playlist right now.')
      setPlaylist(null)
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadPlaylist()
  }, [loadPlaylist])

  const addItem = useCallback((item: MediaItem) => {
    setPlaylist((previous) => {
      if (!previous) {
        return previous
      }

      const alreadyExists = previous.items.some(
        (entry) => entry.id === item.id && entry.type === item.type,
      )

      if (alreadyExists) {
        return previous
      }

      const playlistItem: PlaylistItem = {
        ...item,
        playlistItemId: generatePlaylistItemId(),
        addedAt: new Date().toISOString(),
      }

      return {
        ...previous,
        updatedAt: new Date().toISOString(),
        items: [...previous.items, playlistItem],
      }
    })
  }, [])

  const removeItem = useCallback((playlistItemId: string) => {
    setPlaylist((previous) => {
      if (!previous) {
        return previous
      }

      return {
        ...previous,
        updatedAt: new Date().toISOString(),
        items: previous.items.filter((item) => item.playlistItemId !== playlistItemId),
      }
    })
  }, [])

  const moveItem = useCallback((startIndex: number, destinationIndex: number) => {
    setPlaylist((previous) => {
      if (!previous) {
        return previous
      }

      const withinBounds =
        destinationIndex >= 0 && destinationIndex < previous.items.length && startIndex !== destinationIndex

      if (!withinBounds) {
        return previous
      }

      const nextItems = [...previous.items]
      const [moved] = nextItems.splice(startIndex, 1)
      nextItems.splice(destinationIndex, 0, moved)

      return {
        ...previous,
        updatedAt: new Date().toISOString(),
        items: nextItems,
      }
    })
  }, [])

  const updateMetadata = useCallback(
    (updates: Partial<Pick<Playlist, 'name' | 'description' | 'isPublic' | 'coverImage'>>) => {
      setPlaylist((previous) => {
        if (!previous) {
          return previous
        }

        return {
          ...previous,
          ...updates,
          updatedAt: new Date().toISOString(),
        }
      })
    },
    [],
  )

  const save = useCallback(async () => {
    if (!playlist) {
      return false
    }

    setIsSaving(true)
    setError(null)

    try {
      const clone = clonePlaylist(playlist)
      if (!clone) {
        return false
      }

      const saved = await savePlaylist(clone)
      setPlaylist(saved)
      return true
    } catch (err) {
      console.error('Failed to save playlist', err)
      setError('We hit a snag while saving. Please try again.')
      return false
    } finally {
      setIsSaving(false)
    }
  }, [playlist])

  const hasItem = useCallback(
    (item: MediaItem) => {
      if (!playlist) {
        return false
      }

      return playlist.items.some((entry) => entry.id === item.id && entry.type === item.type)
    },
    [playlist],
  )

  const reset = useCallback(() => {
    setPlaylist(createDefaultPlaylist())
  }, [])

  const value = useMemo<PlaylistContextValue>(
    () => ({
      playlist,
      isLoading,
      isSaving,
      error,
      addItem,
      removeItem,
      moveItem,
      updateMetadata,
      save,
      hasItem,
      reset,
    }),
    [addItem, error, hasItem, isLoading, isSaving, moveItem, playlist, removeItem, reset, save, updateMetadata],
  )

  return <PlaylistContext.Provider value={value}>{children}</PlaylistContext.Provider>
}

export const usePlaylist = () => {
  const value = useContext(PlaylistContext)

  if (!value) {
    throw new Error('usePlaylist must be used inside a PlaylistProvider')
  }

  return value
}
