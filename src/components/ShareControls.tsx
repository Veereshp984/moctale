import { useMemo, useState } from 'react'

interface ShareControlsProps {
  playlistId: string
  playlistName: string
  description?: string
}

const getShareUrl = (playlistId: string) => {
  if (typeof window !== 'undefined' && window.location) {
    return `${window.location.origin}/playlist/${playlistId}`
  }

  return `/playlist/${playlistId}`
}

const ShareControls = ({ playlistId, playlistName, description }: ShareControlsProps) => {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle')
  const shareUrl = useMemo(() => getShareUrl(playlistId), [playlistId])

  const handleCopy = async () => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(shareUrl)
      } else if (typeof document !== 'undefined') {
        const textarea = document.createElement('textarea')
        textarea.value = shareUrl
        textarea.setAttribute('readonly', '')
        textarea.style.position = 'absolute'
        textarea.style.left = '-9999px'
        document.body.appendChild(textarea)
        textarea.select()
        document.execCommand('copy')
        document.body.removeChild(textarea)
      } else {
        throw new Error('Clipboard APIs unavailable')
      }
      setCopyState('copied')
      setTimeout(() => setCopyState('idle'), 2000)
    } catch (error) {
      console.error('Failed to copy', error)
      setCopyState('error')
      setTimeout(() => setCopyState('idle'), 2000)
    }
  }

  const handleShare = async () => {
    if (typeof navigator !== 'undefined' && navigator.share) {
      try {
        await navigator.share({
          title: playlistName,
          text: description ?? 'Check out my curated playlist mixing film & music.',
          url: shareUrl,
        })
      } catch (error) {
        if ((error as DOMException).name !== 'AbortError') {
          console.error('Native share failed', error)
        }
      }
      return
    }

    if (typeof window !== 'undefined') {
      const text = description ? `${playlistName} — ${description}` : playlistName
      const twitterUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(shareUrl)}`
      window.open(twitterUrl, '_blank', 'noopener')
    }
  }

  return (
    <div className="share-controls" data-testid="share-controls">
      <div>
        <h3>Public sharing link</h3>
        <p className="share-controls__hint">
          Anyone with the link can see a read-only version of your playlist, perfect for newsletters or social posts.
        </p>
      </div>
      <div className="share-controls__actions">
        <label className="field field--inline">
          <span className="visually-hidden">Share URL</span>
          <input value={shareUrl} readOnly data-testid="share-link-input" />
        </label>
        <div className="share-controls__buttons">
          <button type="button" className="button button--ghost" onClick={() => void handleCopy()} data-testid="copy-share-link">
            Copy link
          </button>
          <button type="button" className="button" onClick={() => void handleShare()} data-testid="native-share">
            Share
          </button>
        </div>
        <span className="share-controls__status" aria-live="polite">
          {copyState === 'copied' && 'Link copied!'}
          {copyState === 'error' && 'Could not copy link'}
        </span>
      </div>
    </div>
  )
}

export default ShareControls
