import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Spinner, Alert } from 'react-bootstrap'
import { apiService } from '../services/api'

function Overview({ datasetId, anoFiltro, mesFiltro }) {
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
      const response = await apiService.getOverview(datasetId, anoFiltro, mesFiltro)
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

  const basicKPIs = data.basic_kpis || {}
  const turnover = data.turnover || {}
  const turnoverTotal = data.turnover_total || {}
  const contractTypes = data.contract_types || []
  const monthlyDismissals = data.monthly_dismissals || {}
  const tenure = data.tenure || {}

  // Determinar período
  const mesesMap = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
  }
  
  let periodoTexto = 'Todo o período'
  if (anoFiltro && mesFiltro) {
    periodoTexto = `${mesesMap[mesFiltro]}/${anoFiltro}`
  } else if (anoFiltro) {
    periodoTexto = `Ano ${anoFiltro} (média mensal)`
  } else if (mesFiltro) {
    periodoTexto = `Mês ${mesesMap[mesFiltro]} (média de todos os anos)`
  }

  return (
    <div>
      <h4 className="mb-4">📍 Visão Geral — KPIs Consolidados</h4>
      <p className="text-muted mb-4"><strong>Período selecionado:</strong> {periodoTexto}</p>

      {/* Headcount Atual */}
      <Card className="mb-4">
        <Card.Header><h5>👥 Headcount Atual</h5></Card.Header>
        <Card.Body>
          <Row>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Total Ativos</div>
                <div className="metric-value">{basicKPIs.total_ativos || 0}</div>
              </div>
            </Col>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Feminino</div>
                <div className="metric-value">{basicKPIs.qtd_feminino || 0}</div>
                <div className="metric-label">({basicKPIs.pct_feminino || 0}%)</div>
              </div>
            </Col>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Masculino</div>
                <div className="metric-value">{basicKPIs.qtd_masculino || 0}</div>
                <div className="metric-label">({basicKPIs.pct_masculino || 0}%)</div>
              </div>
            </Col>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Liderança</div>
                <div className="metric-value">{basicKPIs.qtd_lideranca || 0}</div>
                <div className="metric-label">({basicKPIs.pct_lideranca || 0}%)</div>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Tipos de Contrato */}
      <Card className="mb-4">
        <Card.Header><h5>📋 Tipos de Contrato</h5></Card.Header>
        <Card.Body>
          {contractTypes.length > 0 ? (
            <Row>
              {contractTypes.slice(0, 4).map((ct, idx) => (
                <Col md={3} key={idx} className="mb-3">
                  <div className="metric-card">
                    <div className="metric-label">{ct.Tipo || 'N/A'}</div>
                    <div className="metric-value">{ct.Quantidade || 0}</div>
                    <div className="metric-label">({ct['Percentual (%)'] || 0}%)</div>
                  </div>
                </Col>
              ))}
            </Row>
          ) : (
            <Alert variant="info">Não há dados de tipo de contrato disponíveis.</Alert>
          )}
        </Card.Body>
      </Card>

      {/* Turnover */}
      <Card className="mb-4">
        <Card.Header>
          <h5>🔄 Turnover</h5>
          <small className="text-white-50">Calculado com base no headcount do início de cada mês</small>
        </Card.Header>
        <Card.Body>
          <h6>📅 Período Selecionado: {periodoTexto}</h6>
          {turnover.meses_considerados > 0 && (
            <p className="text-muted">Meses considerados: {turnover.meses_considerados}</p>
          )}

          <Row className="mb-4">
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Headcount Médio</div>
                <div className="metric-value">{Math.round(turnover.ativos || 0)}</div>
              </div>
            </Col>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Desligados/mês</div>
                <div className="metric-value">{(turnover.desligados || 0).toFixed(1)}</div>
              </div>
            </Col>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Voluntários/mês</div>
                <div className="metric-value">{(turnover.voluntarios || 0).toFixed(1)}</div>
              </div>
            </Col>
            <Col md={3} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Involuntários/mês</div>
                <div className="metric-value">{(turnover.involuntarios || 0).toFixed(1)}</div>
              </div>
            </Col>
          </Row>

          <Row>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Turnover Total (%)</div>
                <div className="metric-value">{(turnover.turnover_total || 0).toFixed(1)}%</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Turnover Voluntário (%)</div>
                <div className="metric-value">{(turnover.turnover_vol || 0).toFixed(1)}%</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Turnover Involuntário (%)</div>
                <div className="metric-value">{(turnover.turnover_inv || 0).toFixed(1)}%</div>
              </div>
            </Col>
          </Row>

          {/* Comparação com total */}
          {(anoFiltro || mesFiltro) && turnoverTotal && (
            <div className="mt-4">
              <hr />
              <h6>📊 Comparação: Total (Todo o Período Histórico)</h6>
              <Row>
                <Col md={4} className="mb-3">
                  <div className="metric-card">
                    <div className="metric-label">Turnover Total (%)</div>
                    <div className="metric-value">{(turnoverTotal.turnover_total || 0).toFixed(1)}%</div>
                    <div className="metric-label">
                      Δ {((turnover.turnover_total || 0) - (turnoverTotal.turnover_total || 0)).toFixed(1)}%
                    </div>
                  </div>
                </Col>
                <Col md={4} className="mb-3">
                  <div className="metric-card">
                    <div className="metric-label">Turnover Voluntário (%)</div>
                    <div className="metric-value">{(turnoverTotal.turnover_vol || 0).toFixed(1)}%</div>
                    <div className="metric-label">
                      Δ {((turnover.turnover_vol || 0) - (turnoverTotal.turnover_vol || 0)).toFixed(1)}%
                    </div>
                  </div>
                </Col>
                <Col md={4} className="mb-3">
                  <div className="metric-card">
                    <div className="metric-label">Turnover Involuntário (%)</div>
                    <div className="metric-value">{(turnoverTotal.turnover_inv || 0).toFixed(1)}%</div>
                    <div className="metric-label">
                      Δ {((turnover.turnover_inv || 0) - (turnoverTotal.turnover_inv || 0)).toFixed(1)}%
                    </div>
                  </div>
                </Col>
              </Row>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Desligamentos por Mês */}
      <Card className="mb-4">
        <Card.Header><h5>📊 Desligamentos por Mês</h5></Card.Header>
        <Card.Body>
          <Row>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Desligamentos Médios/mês</div>
                <div className="metric-value">{(monthlyDismissals.desligamentos_medio_mes || 0).toFixed(1)}</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Total de Desligados</div>
                <div className="metric-value">{monthlyDismissals.total_desligados || 0}</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Meses com Dados</div>
                <div className="metric-value">{monthlyDismissals.meses_com_dados || 0}</div>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Tenure */}
      <Card className="mb-4">
        <Card.Header><h5>⏳ Tenure (Tempo Médio até Desligamento)</h5></Card.Header>
        <Card.Body>
          <Row>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Tenure Médio Total (meses)</div>
                <div className="metric-value">{(tenure.tenure_total || 0).toFixed(1)}</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Tenure Voluntário (meses)</div>
                <div className="metric-value">{(tenure.tenure_vol || 0).toFixed(1)}</div>
              </div>
            </Col>
            <Col md={4} className="mb-3">
              <div className="metric-card">
                <div className="metric-label">Tenure Involuntário (meses)</div>
                <div className="metric-value">{(tenure.tenure_inv || 0).toFixed(1)}</div>
              </div>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </div>
  )
}

export default Overview
