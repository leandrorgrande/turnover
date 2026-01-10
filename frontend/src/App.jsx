import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import { auth } from './config/firebase'
import { onAuthStateChanged } from 'firebase/auth'
import { apiService } from './services/api'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [apiStatus, setApiStatus] = useState('loading')

  useEffect(() => {
    // Verificar status da API
    apiService.healthCheck()
      .then(() => setApiStatus('healthy'))
      .catch(() => setApiStatus('error'))

    // Verificar autenticação Firebase
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        // Salvar token no localStorage
        user.getIdToken().then((token) => {
          localStorage.setItem('firebase_token', token)
        })
        setUser(user)
      } else {
        localStorage.removeItem('firebase_token')
        setUser(null)
      }
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  if (loading) {
    return (
      <div className="spinner-container">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Carregando...</span>
        </div>
      </div>
    )
  }

  // Por enquanto, não exigir autenticação (MVP)
  // Se user === null, mostrar Login
  // Se user !== null, mostrar Dashboard

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Dashboard apiStatus={apiStatus} />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Router>
  )
}

export default App
