"""
Módulo para carregamento e validação de dados.
Migrado do Streamlit para FastAPI.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, List
import io


DATE_COLS = ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]


def col_like(df: pd.DataFrame, name: str) -> Optional[str]:
    """Encontra coluna por nome (case-insensitive)."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if c.lower().strip() == name.lower().strip():
            return c
    return None


def load_excel(file_content: bytes) -> Dict[str, pd.DataFrame]:
    """Carrega arquivo Excel e retorna dicionário de abas."""
    try:
        return pd.read_excel(io.BytesIO(file_content), sheet_name=None)
    except Exception as e:
        raise ValueError(f"Erro ao carregar arquivo: {e}")


def to_datetime_safe(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Converte colunas para datetime de forma segura."""
    df = df.copy()
    for c in cols:
        col = col_like(df, c)
        if col:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def ensure_core_fields(colab: pd.DataFrame) -> pd.DataFrame:
    """
    Garante que campos essenciais existam.
    Funciona de forma flexível - só adiciona campos se as colunas base existirem.
    """
    colab = colab.copy()
    
    # Flag ativo - só adiciona se tiver coluna de desligamento
    desl_col = col_like(colab, "data de desligamento")
    if desl_col:
        colab["ativo"] = colab[desl_col].isna()
    else:
        # Se não tiver data de desligamento, assume que todos estão ativos
        colab["ativo"] = True
    
    # Tempo de casa (meses) - só calcula se tiver data de admissão
    adm_col = col_like(colab, "data de admissão")
    if adm_col:
        now = pd.Timestamp.now()
        # Garantir que é datetime
        if not pd.api.types.is_datetime64_any_dtype(colab[adm_col]):
            colab[adm_col] = pd.to_datetime(colab[adm_col], errors="coerce")
        colab["tempo_casa"] = (now - colab[adm_col]).dt.days / 30
    else:
        # Se não tiver data de admissão, não calcula tempo de casa
        colab["tempo_casa"] = np.nan
    
    return colab


def merge_last_performance(colab: pd.DataFrame, perf: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Mescla última avaliação de performance com colaboradores."""
    if perf is None or perf.empty:
        return colab
    
    p = perf.copy()
    ciclo_col = col_like(p, "data de encerramento do ciclo")
    
    if ciclo_col:
        p[ciclo_col] = pd.to_datetime(p[ciclo_col], errors="coerce")
        last = p.sort_values(["matricula", ciclo_col]).groupby("matricula", as_index=False).tail(1)
    else:
        mat_col = col_like(p, "matricula")
        if mat_col:
            last = p.drop_duplicates(subset=[mat_col], keep="last")
        else:
            return colab
    
    aval_col = col_like(last, "avaliação")
    mat_col = col_like(colab, "matricula")
    
    if aval_col and mat_col:
        colab = colab.merge(
            last[[mat_col, aval_col]], 
            on=mat_col, 
            how="left"
        )
    
    return colab


def load_and_prepare(file_content: bytes) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Carrega e prepara dados.
    Retorna: (empresa, colaboradores, performance)
    """
    sheets = load_excel(file_content)
    
    empresa = sheets.get("empresa", pd.DataFrame())
    colab = sheets.get("colaboradores", pd.DataFrame())
    perf = sheets.get("performance", pd.DataFrame())
    
    # Conversão e merges
    colab = to_datetime_safe(colab, DATE_COLS)
    colab = ensure_core_fields(colab)
    colab = merge_last_performance(colab, perf)
    
    return empresa, colab, perf
