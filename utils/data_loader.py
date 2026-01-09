"""
Módulo para carregamento e validação de dados de múltiplas bases.
Suporta upload de Excel e validação de estrutura.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional, List
import streamlit as st


DATE_COLS = ["data de admissão", "data de desligamento", "ultima promoção", "ultimo mérito"]


def col_like(df: pd.DataFrame, name: str) -> Optional[str]:
    """Encontra coluna por nome (case-insensitive)."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if c.lower().strip() == name.lower().strip():
            return c
    return None


def load_excel(file) -> Dict[str, pd.DataFrame]:
    """Carrega arquivo Excel e retorna dicionário de abas."""
    try:
        return pd.read_excel(file, sheet_name=None)
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return {}


def to_datetime_safe(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Converte colunas para datetime de forma segura."""
    df = df.copy()
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def ensure_core_fields(colab: pd.DataFrame) -> pd.DataFrame:
    """Garante que campos essenciais existam."""
    colab = colab.copy()
    
    # Flag ativo
    desl_col = col_like(colab, "data de desligamento")
    if desl_col:
        colab["ativo"] = colab[desl_col].isna()
    else:
        colab["ativo"] = True
    
    # Tempo de casa (meses)
    adm_col = col_like(colab, "data de admissão")
    if adm_col:
        now = pd.Timestamp.now()
        colab[adm_col] = pd.to_datetime(colab[adm_col], errors="coerce")
        colab["tempo_casa"] = (now - colab[adm_col]).dt.days / 30
    else:
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
        last = p.drop_duplicates(subset=["matricula"], keep="last")
    
    aval_col = col_like(last, "avaliação")
    mat_col = col_like(colab, "matricula")
    
    if aval_col and mat_col:
        colab = colab.merge(
            last[[mat_col, aval_col]], 
            on=mat_col, 
            how="left"
        )
    
    return colab


def clean_and_warn(df: pd.DataFrame, expected: List[str], name: str) -> pd.DataFrame:
    """Valida colunas esperadas e alerta sobre extras/faltantes."""
    if df.empty:
        return df
    
    current = set(df.columns)
    expected_set = set(expected)
    extras = current - expected_set
    missing = expected_set - current
    
    if extras:
        st.info(f"ℹ️ A aba **{name}** contém colunas extras ignoradas: {', '.join(sorted(extras))}")
        df = df[[c for c in df.columns if c in expected_set]]
    
    if missing:
        st.warning(f"⚠️ A aba **{name}** está faltando colunas: {', '.join(sorted(missing))}")
    
    return df


@st.cache_data(show_spinner=True)
def load_and_prepare(file) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, List[str]]]:
    """
    Carrega e prepara dados de forma cacheada.
    Retorna: (empresa, colaboradores, performance, expected_cols)
    """
    sheets = load_excel(file)
    
    empresa = sheets.get("empresa", pd.DataFrame())
    colab = sheets.get("colaboradores", pd.DataFrame())
    perf = sheets.get("performance", pd.DataFrame())
    
    expected_cols = {
        "empresa": ["nome empresa", "cnpj", "unidade", "cidade", "uf"],
        "colaboradores": [
            "matricula", "nome", "departamento", "cargo", "matricula do gestor",
            "tipo_contrato", "genero", "data de admissão", "data de desligamento",
            "motivo de desligamento", "ultima promoção", "ultimo mérito"
        ],
        "performance": ["matricula", "avaliação", "data de encerramento do ciclo"]
    }
    
    # Limpeza e alertas
    empresa = clean_and_warn(empresa, expected_cols["empresa"], "empresa")
    colab = clean_and_warn(colab, expected_cols["colaboradores"], "colaboradores")
    perf = clean_and_warn(perf, expected_cols["performance"], "performance")
    
    # Conversão e merges
    colab = to_datetime_safe(colab, DATE_COLS)
    colab = ensure_core_fields(colab)
    colab = merge_last_performance(colab, perf)
    
    return empresa, colab, perf, expected_cols


def validate_calculations(df: pd.DataFrame) -> Dict[str, any]:
    """
    Valida cálculos de KPIs e retorna relatório de validação.
    Útil para revisar se os números estão corretos.
    """
    validation_report = {
        "erros": [],
        "avisos": [],
        "estatisticas": {}
    }
    
    # Validação de dados básicos
    if df.empty:
        validation_report["erros"].append("DataFrame vazio")
        return validation_report
    
    # Validação de colunas essenciais
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    
    if not adm_col:
        validation_report["erros"].append("Coluna 'data de admissão' não encontrada")
    if not desl_col:
        validation_report["avisos"].append("Coluna 'data de desligamento' não encontrada")
    
    # Validação de datas
    if adm_col:
        adm_dates = pd.to_datetime(df[adm_col], errors="coerce")
        nulos_adm = adm_dates.isna().sum()
        if nulos_adm > 0:
            validation_report["avisos"].append(f"{nulos_adm} registros com data de admissão nula")
        
        # Verificar datas futuras
        futuras = (adm_dates > pd.Timestamp.now()).sum()
        if futuras > 0:
            validation_report["avisos"].append(f"{futuras} registros com data de admissão futura")
    
    if desl_col:
        desl_dates = pd.to_datetime(df[desl_col], errors="coerce")
        # Verificar se desligamento é antes da admissão
        if adm_col:
            adm_dates = pd.to_datetime(df[adm_col], errors="coerce")
            invalidos = ((desl_dates < adm_dates) & desl_dates.notna() & adm_dates.notna()).sum()
            if invalidos > 0:
                validation_report["erros"].append(f"{invalidos} registros com data de desligamento anterior à admissão")
    
    # Estatísticas básicas
    validation_report["estatisticas"] = {
        "total_registros": len(df),
        "ativos": df.get("ativo", pd.Series()).sum() if "ativo" in df.columns else None,
        "desligados": (~df.get("ativo", pd.Series())).sum() if "ativo" in df.columns else None,
    }
    
    return validation_report
