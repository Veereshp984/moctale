import type { HTMLAttributes, PropsWithChildren } from 'react'
import clsx from 'clsx'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {}

export const Card = ({ className, ...props }: PropsWithChildren<CardProps>) => {
  return (
    <div
      className={clsx(
        'group relative overflow-hidden rounded-2xl border border-border bg-surface/80 p-6 shadow-soft transition-transform duration-200 hover:-translate-y-1 hover:shadow-lg',
        className,
      )}
      {...props}
    />
  )
}

export const CardHeader = ({ className, ...props }: PropsWithChildren<CardProps>) => (
  <div className={clsx('space-y-1', className)} {...props} />
)

export const CardTitle = ({ className, ...props }: PropsWithChildren<CardProps>) => (
  <h3 className={clsx('text-xl font-semibold tracking-tight', className)} {...props} />
)

export const CardDescription = ({ className, ...props }: PropsWithChildren<CardProps>) => (
  <p className={clsx('text-sm text-muted-foreground', className)} {...props} />
)

export const CardContent = ({ className, ...props }: PropsWithChildren<CardProps>) => (
  <div className={clsx('mt-4 space-y-3 text-sm text-muted-foreground', className)} {...props} />
)

export const CardFooter = ({ className, ...props }: PropsWithChildren<CardProps>) => (
  <div className={clsx('mt-6 flex items-center justify-between text-sm', className)} {...props} />
)
