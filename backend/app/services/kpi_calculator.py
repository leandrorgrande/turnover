"""
Serviço para cálculo de KPIs
"""
import pandas as pd
from typing import Dict, Optional
from app.utils import kpi_helpers
import logging

logger = logging.getLogger(__name__)


class KPICalculator:
    """Serviço para calcular KPIs"""
    
    @staticmethod
    def calculate_overview(
        df: pd.DataFrame,
        ano_filtro: Optional[int] = None,
        mes_filtro: Optional[int] = None
    ) -> Dict:
        """
        Calcula KPIs da visão geral.
        
        Returns:
            Dict com todos os KPIs da visão geral
        """
        # KPIs básicos
        basic_kpis = kpi_helpers.calculate_basic_kpis(df)
        
        # Turnover
        turnover = kpi_helpers.calculate_turnover_by_period(df, ano_filtro, mes_filtro)
        
        # Turnover total (para comparação)
        turnover_total = kpi_helpers.calculate_turnover_by_period(df, None, None)
        
        # Tipos de contrato
        contract_types = kpi_helpers.calculate_contract_types(df)
        
        # Desligamentos mensais
        monthly_dismissals = kpi_helpers.calculate_monthly_dismissals(df)
        
        # Tenure
        tenure = kpi_helpers.calculate_tenure(df)
        
        return {
            'basic_kpis': basic_kpis,
            'turnover': turnover,
            'turnover_total': turnover_total,
            'contract_types': contract_types.to_dict('records') if not contract_types.empty else [],
            'monthly_dismissals': monthly_dismissals,
            'tenure': tenure
        }
    
    @staticmethod
    def calculate_headcount_analysis(
        df: pd.DataFrame,
        ano_filtro: Optional[int] = None,
        mes_filtro: Optional[int] = None
    ) -> Dict:
        """
        Calcula análises de headcount.
        
        Returns:
            Dict com análises de headcount
        """
        from datetime import datetime
        
        # Data de referência baseada no filtro
        if ano_filtro and mes_filtro:
            data_ref = datetime(ano_filtro, mes_filtro, 1)
        elif ano_filtro:
            data_ref = datetime(ano_filtro, 12, 31)
        else:
            data_ref = datetime.now()
        
        # Headcount atual por departamento
        headcount_dept = kpi_helpers.calculate_headcount(df, "departamento", data_ref)
        
        # Evolução temporal
        headcount_temporal = kpi_helpers.calculate_headcount_temporal(df, "departamento")
        
        # Crescimento
        headcount_growth = kpi_helpers.calculate_headcount_growth(headcount_temporal, "departamento")
        
        # Por gênero
        headcount_gender = kpi_helpers.calculate_headcount_by_dimension_temporal(df, "genero")
        
        # Por tempo de casa
        headcount_tenure = kpi_helpers.calculate_headcount_by_dimension_temporal(df, "tempo_casa")
        
        # Por performance
        headcount_perf = kpi_helpers.calculate_headcount_by_dimension_temporal(df, "performance")
        
        return {
            'headcount_by_department': headcount_dept.to_dict('records') if not headcount_dept.empty else [],
            'headcount_temporal': headcount_temporal.to_dict('records') if not headcount_temporal.empty else [],
            'headcount_growth': headcount_growth.to_dict('records') if not headcount_growth.empty else [],
            'headcount_gender': headcount_gender.to_dict('records') if not headcount_gender.empty else [],
            'headcount_tenure': headcount_tenure.to_dict('records') if not headcount_tenure.empty else [],
            'headcount_performance': headcount_perf.to_dict('records') if not headcount_perf.empty else []
        }
    
    @staticmethod
    def calculate_turnover_analysis(
        df: pd.DataFrame,
        ano_filtro: Optional[int] = None,
        mes_filtro: Optional[int] = None
    ) -> Dict:
        """
        Calcula análises de turnover.
        
        Returns:
            Dict com análises de turnover
        """
        # Turnover do período
        turnover_period = kpi_helpers.calculate_turnover_by_period(df, ano_filtro, mes_filtro)
        
        # Histórico
        turnover_history = kpi_helpers.calculate_turnover_history(df)
        
        return {
            'turnover_period': turnover_period,
            'turnover_history': turnover_history.to_dict('records') if not turnover_history.empty else []
        }
