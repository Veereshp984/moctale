import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import AuthPage from './pages/AuthPage'
import DiscoveryPage from './pages/DiscoveryPage'
import NotFoundPage from './pages/NotFoundPage'
import PlaylistsPage from './pages/PlaylistsPage'
import ProfilePage from './pages/ProfilePage'

const App = () => {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/discovery" replace />} />
        <Route path="auth" element={<AuthPage />} />
        <Route path="discovery" element={<DiscoveryPage />} />
        <Route path="playlists" element={<PlaylistsPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App
