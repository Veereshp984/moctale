import clsx from 'clsx'

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg'
  label?: string
  className?: string
}

const sizeMap = {
  sm: 'h-4 w-4 border-2',
  md: 'h-6 w-6 border-2',
  lg: 'h-10 w-10 border-[3px]',
}

export const Loader = ({ size = 'md', label, className }: LoaderProps) => {
  const spinnerClass = clsx(
    'inline-flex animate-spin rounded-full border-primary/30 border-t-primary',
    sizeMap[size],
  )

  if (label) {
    return (
      <div
        className={clsx('flex items-center gap-3 text-sm text-muted-foreground', className)}
        role="status"
        aria-live="polite"
      >
        <span aria-hidden="true" className={spinnerClass} />
        <span>{label}</span>
      </div>
    )
  }

  return <span aria-hidden="true" className={clsx(spinnerClass, className)} />
}
