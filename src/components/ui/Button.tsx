import { forwardRef } from 'react'
import type { ButtonHTMLAttributes } from 'react'
import clsx from 'clsx'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'outline' | 'link'
export type ButtonSize = 'sm' | 'md' | 'lg' | 'icon'

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-primary-foreground shadow-soft hover:bg-primary/90 focus-visible:outline-primary',
  secondary:
    'bg-muted text-foreground hover:bg-muted/80 focus-visible:outline-muted-foreground',
  ghost: 'hover:bg-muted text-foreground focus-visible:outline-border',
  outline:
    'border border-border bg-transparent text-foreground hover:bg-muted focus-visible:outline-border',
  link: 'text-primary underline-offset-4 hover:underline focus-visible:outline-primary',
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 rounded-lg px-3 text-sm',
  md: 'h-10 rounded-lg px-4 text-sm',
  lg: 'h-12 rounded-xl px-6 text-base',
  icon: 'h-10 w-10 rounded-xl',
}

export const buttonClasses = (
  variant: ButtonVariant = 'primary',
  size: ButtonSize = 'md',
  className?: string,
) =>
  clsx(
    'inline-flex items-center justify-center gap-2 font-semibold transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60',
    variantStyles[variant],
    sizeStyles[size],
    className,
  )

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'primary', size = 'md', type = 'button', ...props }, ref) => {
    return <button ref={ref} className={buttonClasses(variant, size, className)} type={type} {...props} />
  },
)

Button.displayName = 'Button'
