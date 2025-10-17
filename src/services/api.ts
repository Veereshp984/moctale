import type {
  MediaFilter,
  MediaItem,
  MediaQueryOptions,
  MediaType,
  Playlist,
  Recommendation,
} from '../types'
import { availableMoods, availableMovieGenres, availableMusicGenres, movieCatalog, musicCatalog } from '../data/mockData'

const STORAGE_KEY = 'content-discovery.playlist'
export const DEFAULT_PLAYLIST_ID = 'discovery-mix'

let inMemoryPlaylist: Playlist | null = null

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const makeUniqueKey = (item: MediaItem) => `${item.type}:${item.id}`

const genreLookup = new Map<string, string>([
  ...availableMovieGenres.map((genre) => [genre.toLowerCase(), genre]),
  ...availableMusicGenres.map((genre) => [genre.toLowerCase(), genre]),
])

const moodLookup = new Map<string, string>(availableMoods.map((mood) => [mood.toLowerCase(), mood]))

const mediaLibrary: Record<MediaType, MediaItem[]> = {
  movie: movieCatalog,
  music: musicCatalog,
}

type SortOption = NonNullable<MediaFilter['sortBy']>

const sortMedia = (items: MediaItem[], sortBy: SortOption | undefined) => {
  if (sortBy === 'latest') {
    return [...items].sort((a, b) => b.releaseYear - a.releaseYear)
  }

  // Default to popularity
  return [...items].sort((a, b) => b.popularity - a.popularity)
}

const normalize = (value: string) => value.trim().toLowerCase()

const applyFilters = (items: MediaItem[], filters: MediaFilter = {}) => {
  const { genre, mood } = filters

  return items.filter((item) => {
    if (genre) {
      const normalizedGenre = normalize(genre)
      const matchesGenre = item.genres
        .map(normalize)
        .some((itemGenre) => itemGenre === normalizedGenre)

      if (!matchesGenre) {
        return false
      }
    }

    if (mood) {
      const normalizedMood = normalize(mood)
      const matchesMood = item.moods.map(normalize).some((itemMood) => itemMood === normalizedMood)

      if (!matchesMood) {
        return false
      }
    }

    return true
  })
}

const applySearch = (items: MediaItem[], search?: string) => {
  if (!search) {
    return items
  }

  const normalizedSearch = normalize(search)

  return items.filter((item) => {
    const haystack = [item.title, item.description, item.creator, ...(item.tags ?? [])]
      .join(' ')
      .toLowerCase()

    return haystack.includes(normalizedSearch)
  })
}

const simulateNetwork = async <T>(value: T, ms = 320): Promise<T> => {
  await delay(ms)
  return value
}

export const createDefaultPlaylist = (): Playlist => ({
  id: DEFAULT_PLAYLIST_ID,
  name: 'My Discovery Mix',
  description: 'A living playlist that blends the films and tracks you discover here.',
  isPublic: false,
  items: [],
  updatedAt: new Date().toISOString(),
})

const isLocalStorageAvailable = () => {
  try {
    if (typeof window === 'undefined' || !window.localStorage) {
      return false
    }

    const key = '__playlist_test__'
    window.localStorage.setItem(key, 'yes')
    window.localStorage.removeItem(key)
    return true
  } catch (error) {
    return false
  }
}

const readFromStorage = (): Playlist | null => {
  if (isLocalStorageAvailable()) {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return null
    }

    try {
      return JSON.parse(raw) as Playlist
    } catch (error) {
      return null
    }
  }

  return inMemoryPlaylist
}

const writeToStorage = (playlist: Playlist) => {
  if (isLocalStorageAvailable()) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(playlist))
  } else {
    inMemoryPlaylist = playlist
  }
}

export const fetchMedia = async (options: MediaQueryOptions = {}): Promise<MediaItem[]> => {
  const { mediaType = 'all', search, sortBy = 'popularity', limit, ...filters } = options

  let items: MediaItem[] = []
  if (mediaType === 'all') {
    items = [...movieCatalog, ...musicCatalog]
  } else {
    items = mediaLibrary[mediaType]
  }

  const filtered = applyFilters(items, filters)
  const searched = applySearch(filtered, search)
  const sorted = sortMedia(searched, sortBy)

  const limited = typeof limit === 'number' ? sorted.slice(0, limit) : sorted

  return simulateNetwork(limited)
}

export const getPopularMedia = async (
  mediaType: MediaType | 'all' = 'all',
  filters: MediaFilter = {},
  limit = 12,
): Promise<MediaItem[]> => {
  return fetchMedia({ mediaType, ...filters, limit, sortBy: 'popularity' })
}

export const searchMedia = async (
  search: string,
  mediaType: MediaType | 'all' = 'all',
  filters: MediaFilter = {},
  limit = 20,
): Promise<MediaItem[]> => {
  return fetchMedia({ mediaType, ...filters, search, limit })
}

export const getPlaylist = async (id: string = DEFAULT_PLAYLIST_ID): Promise<Playlist> => {
  const existing = readFromStorage()

  if (existing && existing.id === id) {
    return simulateNetwork(existing)
  }

  const fresh = createDefaultPlaylist()
  writeToStorage(fresh)
  return simulateNetwork(fresh)
}

export const savePlaylist = async (playlist: Playlist): Promise<Playlist> => {
  const payload: Playlist = {
    ...playlist,
    updatedAt: new Date().toISOString(),
  }

  writeToStorage(payload)
  return simulateNetwork(payload, 420)
}

export const getPlaylistById = async (id: string): Promise<Playlist | null> => {
  const existing = await getPlaylist()
  if (existing.id === id) {
    return existing
  }

  return null
}

const tally = (items: string[]) => {
  return items.reduce<Map<string, number>>((acc, value) => {
    const key = value.toLowerCase()
    acc.set(key, (acc.get(key) ?? 0) + 1)
    return acc
  }, new Map())
}

const getTopValues = (counts: Map<string, number>) => {
  return [...counts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([key]) => key)
}

export const getRecommendations = async (playlist: Playlist | null): Promise<Recommendation[]> => {
  const pool = [...movieCatalog, ...musicCatalog]
  const excluded = new Set<string>((playlist?.items ?? []).map((item) => makeUniqueKey(item)))

  let topGenres: string[] = []
  let topMoods: string[] = []

  if (playlist && playlist.items.length > 0) {
    const genreCounts = tally(playlist.items.flatMap((item) => item.genres))
    const moodCounts = tally(playlist.items.flatMap((item) => item.moods))

    topGenres = getTopValues(genreCounts)
    topMoods = getTopValues(moodCounts)
  }

  const scored = pool
    .filter((item) => !excluded.has(makeUniqueKey(item)))
    .map((item) => {
      let score = item.popularity
      let reason = 'Trending with our community'

      const matchingGenre = topGenres.find((genre) =>
        item.genres.map((value) => value.toLowerCase()).includes(genre),
      )

      if (matchingGenre) {
        score += 18
        const readableGenre = genreLookup.get(matchingGenre) ?? matchingGenre
        reason = `Because you enjoy ${readableGenre}`
      } else {
        const matchingMood = topMoods.find((mood) => item.moods.map((value) => value.toLowerCase()).includes(mood))

        if (matchingMood) {
          score += 12
          const readableMood = moodLookup.get(matchingMood) ?? matchingMood
          reason = `Matches your ${readableMood.toLowerCase()} mood`
        }
      }

      // small boost to highlight media variety
      if (playlist && playlist.items.length > 0) {
        const hasMovie = playlist.items.some((entry) => entry.type === 'movie')
        const hasMusic = playlist.items.some((entry) => entry.type === 'music')
        if (hasMovie && item.type === 'music') {
          score += 4
        }
        if (hasMusic && item.type === 'movie') {
          score += 4
        }
      }

      return { item, score, reason }
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 6)

  return simulateNetwork(
    scored.map((entry) => ({
      id: `${entry.item.id}-rec`,
      title: entry.item.title,
      reason: entry.reason,
      item: entry.item,
    })),
    280,
  )
}

export const getMediaFilters = () => {
  return {
    movieGenres: availableMovieGenres,
    musicGenres: availableMusicGenres,
    moods: availableMoods,
  }
}
