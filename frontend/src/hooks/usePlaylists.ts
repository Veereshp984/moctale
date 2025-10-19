import { useCallback, useEffect, useState } from 'react'

import { fetchPlaylists } from '@/lib/api/playlists'
import type { ApiErrorShape } from '@/lib/api/client'
import { useAppStore } from '@/store/appStore'

export const usePlaylists = () => {
  const playlists = useAppStore((state) => state.playlists)
  const setPlaylists = useAppStore((state) => state.setPlaylists)
  const [error, setError] = useState<ApiErrorShape | null>(null)
  const [isLoading, setIsLoading] = useState(playlists.length === 0)

  const loadPlaylists = useCallback(async () => {
    setIsLoading(true)
    try {
      const items = await fetchPlaylists()
      setPlaylists(items)
      setError(null)
    } catch (cause) {
      setError(cause as ApiErrorShape)
    } finally {
      setIsLoading(false)
    }
  }, [setPlaylists])

  useEffect(() => {
    if (playlists.length === 0) {
      void loadPlaylists()
    }
  }, [playlists.length, loadPlaylists])

  return {
    playlists,
    error,
    isLoading,
    isError: Boolean(error),
    refresh: loadPlaylists,
  }
}
