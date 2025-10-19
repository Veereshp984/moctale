import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { Button, buttonClasses } from '../Button'

describe('Button', () => {
  it('renders the provided label', () => {
    render(<Button>Save changes</Button>)

    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument()
  })

  it('calls the provided click handler', async () => {
    const onClick = vi.fn()
    const user = userEvent.setup()

    render(<Button onClick={onClick}>Create</Button>)

    await user.click(screen.getByRole('button', { name: /create/i }))

    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('applies stylistic variants and sizes', () => {
    render(
      <Button variant="secondary" size="lg">
        Secondary
      </Button>,
    )

    const button = screen.getByRole('button', { name: /secondary/i })
    expect(button).toHaveClass('bg-muted')
    expect(button).toHaveClass('h-12')
  })

  it('shares helper classes for custom link buttons', () => {
    const classes = buttonClasses('outline', 'sm')

    expect(classes).toContain('border')
    expect(classes).toContain('h-8')
  })
})
