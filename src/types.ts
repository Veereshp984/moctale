export type MediaType = 'movie' | 'music'

export interface MediaItem {
  id: string
  type: MediaType
  title: string
  creator: string
  description: string
  releaseYear: number
  durationMinutes: number
  popularity: number
  genres: string[]
  moods: string[]
  artwork: string
  tags?: string[]
}

export interface MediaFilter {
  mediaType?: MediaType | 'all'
  genre?: string
  mood?: string
  sortBy?: 'popularity' | 'latest'
}

export interface MediaQueryOptions extends MediaFilter {
  search?: string
  limit?: number
}

export interface PlaylistItem extends MediaItem {
  playlistItemId: string
  addedAt: string
  note?: string
}

export interface PlaylistMetadata {
  id: string
  name: string
  description: string
  isPublic: boolean
  coverImage?: string
  updatedAt: string
}

export interface Playlist extends PlaylistMetadata {
  items: PlaylistItem[]
}

export interface Recommendation {
  id: string
  title: string
  reason: string
  item: MediaItem
}
