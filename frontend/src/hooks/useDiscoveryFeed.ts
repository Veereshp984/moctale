import { useCallback, useEffect, useState } from 'react'

import { fetchDiscoveryFeed } from '@/lib/api/discovery'
import type { ApiErrorShape } from '@/lib/api/client'
import { useAppStore } from '@/store/appStore'

export const useDiscoveryFeed = () => {
  const feed = useAppStore((state) => state.discoveryFeed)
  const setDiscoveryFeed = useAppStore((state) => state.setDiscoveryFeed)
  const [error, setError] = useState<ApiErrorShape | null>(null)
  const [isLoading, setIsLoading] = useState(feed.length === 0)

  const loadFeed = useCallback(async () => {
    setIsLoading(true)
    try {
      const items = await fetchDiscoveryFeed()
      setDiscoveryFeed(items)
      setError(null)
    } catch (cause) {
      setError(cause as ApiErrorShape)
    } finally {
      setIsLoading(false)
    }
  }, [setDiscoveryFeed])

  useEffect(() => {
    if (feed.length === 0) {
      void loadFeed()
    }
  }, [feed.length, loadFeed])

  return {
    feed,
    error,
    isLoading,
    isError: Boolean(error),
    refresh: loadFeed,
  }
}
