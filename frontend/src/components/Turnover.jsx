import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Spinner, Alert } from 'react-bootstrap'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { apiService } from '../services/api'

function Turnover({ datasetId, anoFiltro, mesFiltro }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (datasetId) {
      loadData()
    }
  }, [datasetId, anoFiltro, mesFiltro])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await apiService.getTurnover(datasetId, anoFiltro, mesFiltro)
      setData(response.data.results)
    } catch (err) {
      setError(err.message || 'Erro ao carregar dados')
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
    return <Alert variant="danger">Erro: {error}</Alert>
  }

  if (!data) {
    return <Alert variant="info">Carregue um dataset para ver os dados</Alert>
  }

  const turnoverPeriod = data.turnover_period || {}
  const turnoverHistory = data.turnover_history || []

  return (
    <div>
      <h4 className="mb-4">🔄 Turnover — Indicadores e Evolução Histórica</h4>

      {/* Indicadores do Período */}
      <Card className="mb-4">
        <Card.Header><h5>📊 Indicadores do Período Selecionado</h5></Card.Header>
        <Card.Body>
          <Row>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Turnover Total (%)</div>
                <div className="metric-value">{(turnoverPeriod.turnover_total || 0).toFixed(1)}%</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Turnover Voluntário (%)</div>
                <div className="metric-value">{(turnoverPeriod.turnover_vol || 0).toFixed(1)}%</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Turnover Involuntário (%)</div>
                <div className="metric-value">{(turnoverPeriod.turnover_inv || 0).toFixed(1)}%</div>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Histórico */}
      {turnoverHistory.length > 0 && (
        <Card className="mb-4">
          <Card.Header><h5>📈 Evolução Histórica do Turnover</h5></Card.Header>
          <Card.Body>
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={turnoverHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="Mês" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="Turnover Total (%)" stackId="1" stroke="#667eea" fill="#667eea" fillOpacity={0.6} />
                <Area type="monotone" dataKey="Turnover Voluntário (%)" stackId="2" stroke="#764ba2" fill="#764ba2" fillOpacity={0.6} />
                <Area type="monotone" dataKey="Turnover Involuntário (%)" stackId="3" stroke="#f093fb" fill="#f093fb" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </Card.Body>
        </Card>
      )}
    </div>
  )
}

export default Turnover
