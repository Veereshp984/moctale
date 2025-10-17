import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import type { MouseEvent } from 'react'
import { useAuth } from '../context/AuthContext'

const Layout = () => {
  const { isAuthenticated, user, logout, isProcessing } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const showContentNav = isAuthenticated && location.pathname === '/'
  const displayName = user?.displayName || user?.email || 'You'
  const avatarInitial = displayName.charAt(0).toUpperCase()

  const handleLogout = async (event: MouseEvent<HTMLButtonElement>) => {
    event.preventDefault()
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <NavLink to="/" className="brand__link">
            Auragraph
          </NavLink>
          <span className="brand__tagline">Discovery dashboard for film & music</span>
        </div>
        <div className="app-header__right">
          {showContentNav && (
            <nav className="app-nav" aria-label="In-page navigation">
              <a className="app-nav__link" href="#discover">
                Discover
              </a>
              <a className="app-nav__link" href="#recommendations">
                Suggestions
              </a>
              <a className="app-nav__link" href="#playlist-manager">
                Playlist
              </a>
            </nav>
          )}
          <div className="app-header__actions">
            {isAuthenticated ? (
              <>
                <NavLink to="/profile" className="app-nav__link app-nav__profile">
                  <span className="app-nav__avatar" aria-hidden="true">
                    {avatarInitial}
                  </span>
                  <span className="app-nav__name">{displayName}</span>
                </NavLink>
                <button
                  type="button"
                  className="app-nav__link app-nav__link--button"
                  onClick={handleLogout}
                  disabled={isProcessing}
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <NavLink to="/login" className="app-nav__link">
                  Log in
                </NavLink>
                <NavLink to="/signup" className="app-nav__link app-nav__link--primary">
                  Sign up
                </NavLink>
              </>
            )}
          </div>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
      <footer className="app-footer">
        <p>Built for creators exploring stories and sounds together.</p>
      </footer>
    </div>
  )
}

export default Layout
