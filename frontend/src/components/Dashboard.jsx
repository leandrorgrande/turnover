import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Nav } from 'react-bootstrap'
import Upload from './Upload'
import Overview from './Overview'
import Headcount from './Headcount'
import Turnover from './Turnover'
import Risk from './Risk'
import { apiService } from '../services/api'

function Dashboard({ apiStatus }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [dataset, setDataset] = useState(null)
  const [datasets, setDatasets] = useState([])
  const [anoFiltro, setAnoFiltro] = useState(null)
  const [mesFiltro, setMesFiltro] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadDatasets()
  }, [])

  const loadDatasets = async () => {
    try {
      const response = await apiService.listDatasets()
      setDatasets(response.data.datasets || [])
    } catch (error) {
      console.error('Erro ao carregar datasets:', error)
    }
  }

  const handleFileUpload = async (file) => {
    setLoading(true)
    try {
      const response = await apiService.uploadDataset(file)
      setDataset(response.data.dataset_id)
      await loadDatasets()
      setActiveTab('overview')
    } catch (error) {
      console.error('Erro ao fazer upload:', error)
      alert('Erro ao fazer upload do arquivo')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container fluid className="py-4">
      <Row className="mb-4">
        <Col>
          <Card>
            <Card.Header className="d-flex justify-content-between align-items-center">
              <div>
                <h2 className="mb-0">🚀 People Analytics Platform</h2>
                <p className="mb-0">Dashboard de Turnover e Indicadores de RH</p>
              </div>
              <div>
                {apiStatus === 'healthy' && (
                  <span className="status-badge status-healthy">✅ API Online</span>
                )}
                {apiStatus === 'error' && (
                  <span className="status-badge status-error">❌ API Offline</span>
                )}
              </div>
            </Card.Header>
            <Card.Body>
              <Upload onUpload={handleFileUpload} loading={loading} />
              
              {datasets.length > 0 && (
                <div className="mt-3">
                  <label className="form-label">Dataset Ativo:</label>
                  <select
                    className="form-select"
                    value={dataset || ''}
                    onChange={(e) => setDataset(e.target.value)}
                  >
                    <option value="">Selecione um dataset</option>
                    {datasets.map((ds) => (
                      <option key={ds.id} value={ds.id}>
                        {ds.name || ds.filename} ({ds.rows} linhas)
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="mt-3">
                <Row>
                  <Col md={6}>
                    <label className="form-label">Ano de Competência:</label>
                    <input
                      type="number"
                      className="form-control"
                      placeholder="Todos os anos"
                      value={anoFiltro || ''}
                      onChange={(e) => setAnoFiltro(e.target.value ? parseInt(e.target.value) : null)}
                    />
                  </Col>
                  <Col md={6}>
                    <label className="form-label">Mês de Competência:</label>
                    <select
                      className="form-select"
                      value={mesFiltro || ''}
                      onChange={(e) => setMesFiltro(e.target.value ? parseInt(e.target.value) : null)}
                    >
                      <option value="">Todos os meses</option>
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map((mes) => (
                        <option key={mes} value={mes}>
                          {['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][mes - 1]}
                        </option>
                      ))}
                    </select>
                  </Col>
                </Row>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {dataset && (
        <Row>
          <Col>
            <Card>
              <Card.Header>
                <Nav variant="tabs" activeKey={activeTab} onSelect={(k) => setActiveTab(k)}>
                  <Nav.Item>
                    <Nav.Link eventKey="overview">📍 Visão Geral</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="headcount">👥 Headcount</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="turnover">🔄 Turnover</Nav.Link>
                  </Nav.Item>
                  <Nav.Item>
                    <Nav.Link eventKey="risk">🔮 Risco (TRI) 🔒</Nav.Link>
                  </Nav.Item>
                </Nav>
              </Card.Header>
              <Card.Body>
                {activeTab === 'overview' && (
                  <Overview datasetId={dataset} anoFiltro={anoFiltro} mesFiltro={mesFiltro} />
                )}
                {activeTab === 'headcount' && (
                  <Headcount datasetId={dataset} anoFiltro={anoFiltro} mesFiltro={mesFiltro} />
                )}
                {activeTab === 'turnover' && (
                  <Turnover datasetId={dataset} anoFiltro={anoFiltro} mesFiltro={mesFiltro} />
                )}
                {activeTab === 'risk' && (
                  <Risk datasetId={dataset} />
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}

      {!dataset && (
        <Row>
          <Col>
            <Card>
              <Card.Body className="text-center py-5">
                <h5>📊 Nenhum Dataset Carregado</h5>
                <p className="text-muted">
                  Faça upload de um arquivo Excel para começar a análise.
                </p>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      )}
    </Container>
  )
}

export default Dashboard
