import axios from 'axios'

const API_URL = 'https://people-analytics-api-286602273391.us-central1.run.app'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar token de autenticação
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('firebase_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Upload de dataset
  uploadDataset: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/api/v1/datasets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },

  // Listar datasets
  listDatasets: () => api.get('/api/v1/datasets'),

  // Deletar dataset
  deleteDataset: (datasetId) => api.delete(`/api/v1/datasets/${datasetId}`),

  // Análises
  getOverview: (datasetId, anoFiltro, mesFiltro) =>
    api.post('/api/v1/analyses/overview', {
      dataset_id: datasetId,
      ano_filtro: anoFiltro,
      mes_filtro: mesFiltro,
      analysis_type: 'overview',
    }),

  getHeadcount: (datasetId, anoFiltro, mesFiltro) =>
    api.post('/api/v1/analyses/headcount', {
      dataset_id: datasetId,
      ano_filtro: anoFiltro,
      mes_filtro: mesFiltro,
      analysis_type: 'headcount',
    }),

  getTurnover: (datasetId, anoFiltro, mesFiltro) =>
    api.post('/api/v1/analyses/turnover', {
      dataset_id: datasetId,
      ano_filtro: anoFiltro,
      mes_filtro: mesFiltro,
      analysis_type: 'turnover',
    }),

  getRisk: (datasetId) =>
    api.post('/api/v1/analyses/risk', {
      dataset_id: datasetId,
      analysis_type: 'risk',
    }),
}

export default apiService
