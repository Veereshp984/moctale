import { useEffect, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'
import clsx from 'clsx'

import { Button } from './Button'

export interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  className?: string
  children: ReactNode
}

export const Modal = ({ isOpen, onClose, title, description, className, children }: ModalProps) => {
  useEffect(() => {
    if (!isOpen || typeof window === 'undefined') {
      return
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    document.body.style.overflow = 'hidden'

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [isOpen, onClose])

  if (!isOpen) {
    return null
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={clsx(
          'relative w-full max-w-lg rounded-3xl border border-border/60 bg-surface p-8 shadow-xl',
          className,
        )}
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={onClose}
          aria-label="Close modal"
          className="absolute right-4 top-4"
        >
          <X className="h-5 w-5" />
        </Button>
        <div className="space-y-3 pr-6">
          <h2 id="modal-title" className="text-2xl font-semibold">
            {title}
          </h2>
          {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
        </div>
        <div className="mt-6 space-y-4 text-sm text-muted-foreground">{children}</div>
      </div>
    </div>,
    document.body,
  )
}
