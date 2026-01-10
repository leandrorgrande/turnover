import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Spinner, Alert } from 'react-bootstrap'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { apiService } from '../services/api'

function Headcount({ datasetId, anoFiltro, mesFiltro }) {
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
      const response = await apiService.getHeadcount(datasetId, anoFiltro, mesFiltro)
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

  const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe']

  return (
    <div>
      <h4 className="mb-4">👥 Headcount — Análises Temporais e Comparações</h4>

      {/* Headcount por Departamento */}
      {data.headcount_by_department && data.headcount_by_department.length > 0 && (
        <Card className="mb-4">
          <Card.Header><h5>📊 Headcount Atual por Departamento</h5></Card.Header>
          <Card.Body>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={data.headcount_by_department}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="departamento" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Headcount" fill="#667eea" />
              </BarChart>
            </ResponsiveContainer>
          </Card.Body>
        </Card>
      )}

      {/* Evolução Temporal */}
      {data.headcount_temporal && data.headcount_temporal.length > 0 && (
        <Card className="mb-4">
          <Card.Header><h5>📈 Evolução Temporal do Headcount por Departamento</h5></Card.Header>
          <Card.Body>
            <Alert variant="info">Gráfico de evolução temporal será implementado em breve</Alert>
            {/* TODO: Implementar gráfico de linha temporal */}
          </Card.Body>
        </Card>
      )}

      {/* Por Gênero */}
      {data.headcount_gender && data.headcount_gender.length > 0 && (
        <Card className="mb-4">
          <Card.Header><h5>⚧️ Análise por Gênero ao Longo do Tempo</h5></Card.Header>
          <Card.Body>
            <Row>
              <Col md={6}>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={data.headcount_gender}
                      dataKey="Headcount"
                      nameKey="Gênero"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label
                    >
                      {data.headcount_gender.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}
    </div>
  )
}

export default Headcount
