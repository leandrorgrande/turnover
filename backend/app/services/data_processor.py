"""
Serviço para processamento de dados
"""
import pandas as pd
from typing import Dict, Optional
from app.utils.data_loader import load_and_prepare
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """Serviço para processar dados de colaboradores"""
    
    @staticmethod
    def process_upload(file_content: bytes) -> Dict[str, pd.DataFrame]:
        """
        Processa upload de arquivo Excel.
        
        Args:
            file_content: Conteúdo do arquivo em bytes
        
        Returns:
            Dict com 'empresa', 'colaboradores', 'performance'
        """
        try:
            empresa, colaboradores, performance = load_and_prepare(file_content)
            
            return {
                'empresa': empresa,
                'colaboradores': colaboradores,
                'performance': performance
            }
        except Exception as e:
            logger.error(f"Erro ao processar arquivo: {e}")
            raise ValueError(f"Erro ao processar arquivo: {str(e)}")
    
    @staticmethod
    def filter_by_period(
        df: pd.DataFrame,
        ano_filtro: Optional[int] = None,
        mes_filtro: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Filtra DataFrame por período de competência.
        
        Args:
            df: DataFrame de colaboradores
            ano_filtro: Ano de competência
            mes_filtro: Mês de competência
        
        Returns:
            DataFrame filtrado
        """
        if ano_filtro is None and mes_filtro is None:
            return df
        
        from app.utils.data_loader import col_like
        
        adm_col = col_like(df, "data de admissão")
        desl_col = col_like(df, "data de desligamento")
        
        if not adm_col:
            return df
        
        df = df.copy()
        df[adm_col] = pd.to_datetime(df[adm_col], errors="coerce")
        
        if desl_col:
            df[desl_col] = pd.to_datetime(df[desl_col], errors="coerce")
        
        # Aplicar filtros
        if ano_filtro is not None:
            df = df[df[adm_col].dt.year == ano_filtro]
        
        if mes_filtro is not None:
            df = df[df[adm_col].dt.month == mes_filtro]
        
        return df
