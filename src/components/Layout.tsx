import { NavLink } from 'react-router-dom'
import type { PropsWithChildren } from 'react'

const Layout = ({ children }: PropsWithChildren) => {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <NavLink to="/" className="brand__link">
            Auragraph
          </NavLink>
          <span className="brand__tagline">Discovery dashboard for film & music</span>
        </div>
        <nav className="app-nav" aria-label="Primary navigation">
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
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <p>Built for creators exploring stories and sounds together.</p>
      </footer>
    </div>
  )
}

export default Layout
