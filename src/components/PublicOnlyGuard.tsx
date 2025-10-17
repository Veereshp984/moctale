import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const PublicOnlyGuard = () => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="guard guard--loading" role="status" aria-live="polite">
        <div className="spinner" />
        <p>Checking your session…</p>
      </div>
    )
  }

  if (isAuthenticated) {
    const fallback = typeof location.state?.from === 'string' && location.state.from ? location.state.from : '/'
    return <Navigate to={fallback} replace />
  }

  return <Outlet />
}

export default PublicOnlyGuard
