import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const AuthGuard = () => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="guard guard--loading" role="status" aria-live="polite">
        <div className="spinner" />
        <p>Preparing your dashboard…</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    const from = `${location.pathname}${location.search}${location.hash}`
    return <Navigate to="/login" replace state={{ from }} />
  }

  return <Outlet />
}

export default AuthGuard
