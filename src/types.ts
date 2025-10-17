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

export interface UserPreferences {
  primaryGenre?: string
  primaryMood?: string
  newsletterOptIn: boolean
}

export interface UserProfile {
  id: string
  email: string
  displayName: string
  bio?: string
  preferences: UserPreferences
}

export interface AuthTokens {
  accessToken: string
  expiresAt?: string
}

export interface SignupPayload {
  email: string
  password: string
  displayName: string
  preferences?: Partial<UserPreferences>
}

export interface LoginPayload {
  email: string
  password: string
}

export interface ProfileUpdatePayload {
  displayName?: string
  bio?: string
  preferences?: Partial<UserPreferences>
}

export interface AuthResponse {
  user: UserProfile
  tokens: AuthTokens
}
