import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import { AuthProvider } from './context/AuthContext'
import { PlaylistProvider } from './context/PlaylistContext'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <PlaylistProvider>
          <App />
        </PlaylistProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
