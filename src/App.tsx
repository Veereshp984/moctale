import { Navigate, Route, Routes } from 'react-router-dom'
import AuthGuard from './components/AuthGuard'
import Layout from './components/Layout'
import PublicOnlyGuard from './components/PublicOnlyGuard'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Profile from './pages/Profile'
import PublicPlaylist from './pages/PublicPlaylist'
import Signup from './pages/Signup'

const App = () => {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route element={<PublicOnlyGuard />}>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
        </Route>
        <Route element={<AuthGuard />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/profile" element={<Profile />} />
        </Route>
        <Route path="/playlist/:playlistId" element={<PublicPlaylist />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
