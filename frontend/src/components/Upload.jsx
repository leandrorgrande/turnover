import React, { useState } from 'react'
import { Card } from 'react-bootstrap'

function Upload({ onUpload, loading }) {
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0]
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        onUpload(file)
      } else {
        alert('Por favor, envie apenas arquivos Excel (.xlsx ou .xls)')
      }
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0])
    }
  }

  return (
    <div
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${dragActive ? '#667eea' : '#ccc'}`,
        borderRadius: '10px',
        padding: '3rem',
        textAlign: 'center',
        backgroundColor: dragActive ? 'rgba(102, 126, 234, 0.1)' : 'transparent',
        transition: 'all 0.3s ease',
        cursor: 'pointer'
      }}
    >
      <input
        type="file"
        accept=".xlsx,.xls"
        onChange={handleFileInput}
        disabled={loading}
        style={{ display: 'none' }}
        id="file-upload"
      />
      <label htmlFor="file-upload" style={{ cursor: 'pointer', width: '100%' }}>
        <div>
          <h5>📂 Carregue o Excel (.xlsx)</h5>
          <p className="text-muted mb-3">
            Arraste e solte o arquivo aqui ou clique para selecionar
          </p>
          <p className="text-muted small">
            O arquivo deve conter as abas: <strong>empresa</strong>, <strong>colaboradores</strong> e <strong>performance</strong>
          </p>
          {loading && (
            <div className="mt-3">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Carregando...</span>
              </div>
            </div>
          )}
        </div>
      </label>
    </div>
  )
}

export default Upload
