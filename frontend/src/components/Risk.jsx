import React, { useState, useEffect } from 'react'
import { Card, Spinner, Alert } from 'react-bootstrap'
import { apiService } from '../services/api'

function Risk({ datasetId }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (datasetId) {
      loadData()
    }
  }, [datasetId])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiService.getRisk(datasetId)
      setData(response.data.results)
    } catch (err) {
      setError(err.message || 'Erro ao carregar dados. Esta funcionalidade requer assinatura Premium.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="spinner-container">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Carregando...</span>
        </Spinner>
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="warning">
        <h5>🔒 Análise de Risco (TRI) requer assinatura Premium</h5>
        <p>{error}</p>
        <p className="mb-0">💡 Entre em contato para fazer upgrade e acessar análises avançadas.</p>
      </Alert>
    )
  }

  if (!data) {
    return <Alert variant="info">Carregue um dataset para ver os dados</Alert>
  }

  return (
    <div>
      <h4 className="mb-4">🔮 Risco de Turnover (TRI) — Modelo Avançado</h4>
      <Card>
        <Card.Header><h5>Análise de Risco</h5></Card.Header>
        <Card.Body>
          <Alert variant="info">
            Esta funcionalidade está em desenvolvimento e requer assinatura Premium.
          </Alert>
        </Card.Body>
      </Card>
    </div>
  )
}

export default Risk
