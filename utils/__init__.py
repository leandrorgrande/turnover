"""
Módulo de utilitários para o Dashboard de Turnover.
"""
from utils.data_loader import (
    load_and_prepare,
    validate_calculations,
    col_like,
    DATE_COLS
)
from utils.kpi_helpers import (
    calculate_turnover,
    calculate_turnover_by_period,
    calculate_turnover_history,
    calculate_tenure,
    calculate_headcount,
    calculate_basic_kpis,
    calculate_contract_types,
    calculate_monthly_dismissals,
    safe_mean,
    norm_0_1
)

__all__ = [
    "load_and_prepare",
    "validate_calculations",
    "col_like",
    "DATE_COLS",
    "calculate_turnover",
    "calculate_turnover_by_period",
    "calculate_turnover_history",
    "calculate_tenure",
    "calculate_headcount",
    "calculate_basic_kpis",
    "calculate_contract_types",
    "calculate_monthly_dismissals",
    "safe_mean",
    "norm_0_1"
]
