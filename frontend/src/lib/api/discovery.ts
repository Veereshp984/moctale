import type { DiscoveryItem } from '@/store/appStore'
import { http } from './client'

const FALLBACK_DISCOVERY: DiscoveryItem[] = [
  {
    id: 'discovery-1',
    title: 'Analog warmth',
    description:
      'Soulful downtempo selections with vintage synth textures and modern percussive layers curated for late-night inspiration.',
    tags: ['downtempo', 'organic', 'analog'],
    listens: 2480,
  },
  {
    id: 'discovery-2',
    title: 'Hyperfocus coding',
    description:
      'Dense atmospheric electronica engineered to keep you in deep work mode without interrupting your flow state.',
    tags: ['electronica', 'focus', 'instrumental'],
    listens: 4320,
  },
  {
    id: 'discovery-3',
    title: 'Sunset rooftop',
    description:
      'Balearic beats, crisp house grooves, and chromatic disco for golden-hour gatherings and afterparty transitions.',
    tags: ['house', 'balearic', 'disco'],
    listens: 3189,
  },
  {
    id: 'discovery-4',
    title: 'Cinematic pulse',
    description:
      'Hybrid orchestral cues with evolving textures, bold percussion, and emotive builds made for trailers.',
    tags: ['cinematic', 'orchestral', 'dynamic'],
    listens: 2814,
  },
]

export const fetchDiscoveryFeed = async (): Promise<DiscoveryItem[]> => {
  if (import.meta.env.VITE_API_URL) {
    return http.get<DiscoveryItem[]>('/discovery')
  }

  if (typeof window === 'undefined') {
    return FALLBACK_DISCOVERY
  }

  return new Promise((resolve) => {
    window.setTimeout(() => resolve(FALLBACK_DISCOVERY), 450)
  })
}
