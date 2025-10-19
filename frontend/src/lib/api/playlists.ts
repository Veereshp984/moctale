import type { PlaylistSummary } from '@/store/appStore'
import { http } from './client'

const FALLBACK_PLAYLISTS: PlaylistSummary[] = [
  {
    id: 'playlist-1',
    title: 'Nocturnal sketches',
    description: 'Minimal breakbeats and analogue ambience for deep listening sessions.',
    updatedAt: '3 hours ago',
    trackCount: 42,
    mood: 'after hours',
    coverColor: 'bg-gradient-to-br from-purple-500 via-indigo-500 to-sky-500',
  },
  {
    id: 'playlist-2',
    title: 'Studio sparks',
    description: 'Vibrant UK garage and neo-soul bounce to energise collaborative workshops.',
    updatedAt: 'yesterday',
    trackCount: 58,
    mood: 'energetic',
    coverColor: 'bg-gradient-to-br from-amber-400 via-orange-500 to-rose-500',
  },
  {
    id: 'playlist-3',
    title: 'Cinematic currents',
    description: 'Evolving modern classical cues layered with experimental textures.',
    updatedAt: '2 days ago',
    trackCount: 35,
    mood: 'cinematic',
    coverColor: 'bg-gradient-to-br from-slate-800 via-sky-700 to-cyan-500',
  },
  {
    id: 'playlist-4',
    title: 'Low-end therapy',
    description: 'Warm lofi beats and dusty cuts to decompress designers between sprints.',
    updatedAt: 'this week',
    trackCount: 27,
    mood: 'calm',
    coverColor: 'bg-gradient-to-br from-emerald-400 via-teal-500 to-cyan-400',
  },
]

export const fetchPlaylists = async (): Promise<PlaylistSummary[]> => {
  if (import.meta.env.VITE_API_URL) {
    return http.get<PlaylistSummary[]>('/playlists')
  }

  if (typeof window === 'undefined') {
    return FALLBACK_PLAYLISTS
  }

  return new Promise((resolve) => {
    window.setTimeout(() => resolve(FALLBACK_PLAYLISTS), 360)
  })
}
