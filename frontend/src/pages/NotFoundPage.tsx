import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

import { buttonClasses } from '@/components/ui/Button'

const NotFoundPage = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-background px-4 text-center">
      <div className="max-w-md space-y-3">
        <p className="text-sm font-semibold uppercase tracking-widest text-muted-foreground">404</p>
        <h1 className="text-4xl font-semibold">This space is still tuning up</h1>
        <p className="text-base text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist yet. Choose another view while we ship the next
          update.
        </p>
      </div>
      <Link to="/discovery" className={buttonClasses('primary', 'md', 'gap-2')}>
        <ArrowLeft className="h-4 w-4" /> Back to discovery
      </Link>
    </div>
  )
}

export default NotFoundPage
