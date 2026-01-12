"""
Endpoints para análises e KPIs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user, require_premium
from app.models.schemas import AnalysisRequest, AnalysisResponse
from app.services.kpi_calculator import KPICalculator
from app.services.data_processor import DataProcessor
from app.services.firestore_service import FirestoreService
from typing import Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyses", tags=["analyses"])


@router.post("/overview", response_model=AnalysisResponse)
async def get_overview(
    request: AnalysisRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Calcula KPIs da visão geral.
    Disponível para todos os usuários (básico e premium).
    """
    try:
        # Carregar dados do Firestore
        firestore_service = FirestoreService()
        dataset_data = firestore_service.get_dataset_data(user['uid'], request.dataset_id)
        
        if not dataset_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset não encontrado ou sem dados"
            )
        
        # Converter dados flexíveis do Firestore para DataFrames
        import pandas as pd
        
        # Os dados vêm como lista de dicts do Firestore (estrutura flexível)
        # Converter de volta para DataFrame - aceita qualquer estrutura de colunas
        colaboradores_data = dataset_data.get('colaboradores', [])
        
        if not colaboradores_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset não contém dados de colaboradores"
            )
        
        # Criar DataFrame de forma flexível (aceita qualquer estrutura)
        colaboradores_df = pd.DataFrame(colaboradores_data)
        
        # Converter datas de string para datetime (se existirem)
        # Isso é flexível - só converte se as colunas existirem
        from app.utils.data_loader import col_like
        adm_col = col_like(colaboradores_df, "data de admissão")
        desl_col = col_like(colaboradores_df, "data de desligamento")
        
        if adm_col:
            colaboradores_df[adm_col] = pd.to_datetime(colaboradores_df[adm_col], errors="coerce")
        if desl_col:
            colaboradores_df[desl_col] = pd.to_datetime(colaboradores_df[desl_col], errors="coerce")
        
        if colaboradores_df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset não contém dados de colaboradores"
            )
        
        # Calcular KPIs
        calculator = KPICalculator()
        results = calculator.calculate_overview(
            colaboradores_df,
            request.ano_filtro,
            request.mes_filtro
        )
        
        return AnalysisResponse(
            dataset_id=request.dataset_id,
            analysis_type="overview",
            results=results,
            filters={
                'ano_filtro': request.ano_filtro,
                'mes_filtro': request.mes_filtro
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular overview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular análise: {str(e)}"
        )


@router.post("/headcount", response_model=AnalysisResponse)
async def get_headcount_analysis(
    request: AnalysisRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Calcula análises de headcount.
    Disponível para todos os usuários.
    """
    try:
        # Carregar dados do Firestore
        firestore_service = FirestoreService()
        dataset_data = firestore_service.get_dataset_data(user['uid'], request.dataset_id)
        
        if not dataset_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset não encontrado ou sem dados"
            )
        
        # Converter dados flexíveis para DataFrame
        import pandas as pd
        colaboradores_data = dataset_data.get('colaboradores', [])
        
        if not colaboradores_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset não contém dados de colaboradores"
            )
        
        colaboradores_df = pd.DataFrame(colaboradores_data)
        
        # Converter datas (se existirem)
        from app.utils.data_loader import col_like
        adm_col = col_like(colaboradores_df, "data de admissão")
        desl_col = col_like(colaboradores_df, "data de desligamento")
        if adm_col:
            colaboradores_df[adm_col] = pd.to_datetime(colaboradores_df[adm_col], errors="coerce")
        if desl_col:
            colaboradores_df[desl_col] = pd.to_datetime(colaboradores_df[desl_col], errors="coerce")
        
        # Calcular análises de headcount
        calculator = KPICalculator()
        results = calculator.calculate_headcount_analysis(
            colaboradores_df,
            request.ano_filtro,
            request.mes_filtro
        )
        
        return AnalysisResponse(
            dataset_id=request.dataset_id,
            analysis_type="headcount",
            results=results,
            filters={
                'ano_filtro': request.ano_filtro,
                'mes_filtro': request.mes_filtro
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular headcount: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular análise: {str(e)}"
        )


@router.post("/turnover", response_model=AnalysisResponse)
async def get_turnover_analysis(
    request: AnalysisRequest,
    user: Dict = Depends(get_current_user)
):
    """
    Calcula análises de turnover.
    Disponível para todos os usuários.
    """
    try:
        # Carregar dados do Firestore
        firestore_service = FirestoreService()
        dataset_data = firestore_service.get_dataset_data(user['uid'], request.dataset_id)
        
        if not dataset_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset não encontrado ou sem dados"
            )
        
        # Converter dados flexíveis para DataFrame
        import pandas as pd
        colaboradores_data = dataset_data.get('colaboradores', [])
        
        if not colaboradores_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dataset não contém dados de colaboradores"
            )
        
        colaboradores_df = pd.DataFrame(colaboradores_data)
        
        # Converter datas (se existirem)
        from app.utils.data_loader import col_like
        adm_col = col_like(colaboradores_df, "data de admissão")
        desl_col = col_like(colaboradores_df, "data de desligamento")
        if adm_col:
            colaboradores_df[adm_col] = pd.to_datetime(colaboradores_df[adm_col], errors="coerce")
        if desl_col:
            colaboradores_df[desl_col] = pd.to_datetime(colaboradores_df[desl_col], errors="coerce")
        
        # Calcular análises de turnover
        calculator = KPICalculator()
        results = calculator.calculate_turnover_analysis(
            colaboradores_df,
            request.ano_filtro,
            request.mes_filtro
        )
        
        return AnalysisResponse(
            dataset_id=request.dataset_id,
            analysis_type="turnover",
            results=results,
            filters={
                'ano_filtro': request.ano_filtro,
                'mes_filtro': request.mes_filtro
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao calcular turnover: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular análise: {str(e)}"
        )


@router.post("/risk", response_model=AnalysisResponse)
async def get_risk_analysis(
    request: AnalysisRequest,
    user: Dict = Depends(require_premium)
):
    """
    Calcula análise de risco de turnover (TRI).
    Disponível apenas para usuários Premium.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Análise de risco ainda não implementada"
    )
