"""
Schemas Pydantic para validação de dados
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class DatasetMetadata(BaseModel):
    """Metadados de um dataset"""
    name: str
    filename: str
    rows: int
    uploaded_at: datetime
    filters: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    """Request para análise"""
    dataset_id: str
    ano_filtro: Optional[int] = None
    mes_filtro: Optional[int] = None
    analysis_type: str = Field(..., description="Tipo de análise: overview, headcount, turnover")


class AnalysisResponse(BaseModel):
    """Response de análise"""
    dataset_id: str
    analysis_type: str
    results: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None


class UploadResponse(BaseModel):
    """Response de upload"""
    dataset_id: str
    message: str
    metadata: DatasetMetadata


class ErrorResponse(BaseModel):
    """Response de erro"""
    error: str
    detail: Optional[str] = None
