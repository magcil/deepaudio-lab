import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import keycloak from './auth/keycloak'

keycloak
  .init({ onLoad: 'login-required', checkLoginIframe: false })
  .then((authenticated) => {
    if (!authenticated) {
      keycloak.login()
      return
    }
    createRoot(document.getElementById('root')!).render(
      <StrictMode>
        <App />
      </StrictMode>,
    )
  })
  .catch((err) => {
    console.error('Keycloak init failed:', err)
    document.getElementById('root')!.innerHTML =
      '<div style="color:white;padding:2rem">Authentication service unavailable. Is Keycloak running?</div>'
  })
