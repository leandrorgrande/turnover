"""
Módulo para cálculos de KPIs com validação e revisão.
Todos os cálculos são validados e documentados.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Tuple, Optional
from utils.data_loader import col_like


def safe_mean(series: pd.Series) -> float:
    """Calcula média de forma segura, tratando erros."""
    try:
        return round(pd.to_numeric(series, errors="coerce").dropna().mean(), 1)
    except Exception:
        return 0.0


def norm_0_1(s: pd.Series) -> pd.Series:
    """Normaliza série para escala 0-1."""
    s = pd.to_numeric(s, errors="coerce").fillna(0).astype(float)
    if s.empty:
        return s
    minv, maxv = s.min(), s.max()
    rng = maxv - minv
    if rng == 0 or pd.isna(rng):
        return s * 0
    return (s - minv) / rng


def calculate_turnover(
    df: pd.DataFrame,
    periodo_mes: Optional[datetime] = None
) -> Dict[str, float]:
    """
    Calcula turnover total, voluntário e involuntário.
    
    Fórmula: Turnover = (Desligados no período / Ativos no período) * 100
    
    Args:
        df: DataFrame com dados de colaboradores
        periodo_mes: Data de referência (se None, calcula histórico médio)
    
    Returns:
        Dict com turnover_total, turnover_vol, turnover_inv
    """
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    mot_col = col_like(df, "motivo de desligamento")
    
    if not adm_col or not desl_col:
        return {"turnover_total": 0.0, "turnover_vol": 0.0, "turnover_inv": 0.0}
    
    dft = df.copy()
    dft[adm_col] = pd.to_datetime(dft[adm_col], errors="coerce")
    dft[desl_col] = pd.to_datetime(dft[desl_col], errors="coerce")
    
    # Se tem período específico (competência)
    if periodo_mes and "ativo" in df.columns and "desligado_no_mes" in df.columns:
        ativos_mes = df[df["ativo"] == True]
        deslig_mes = df[df["desligado_no_mes"] == True]
        
        a = len(ativos_mes)
        d = len(deslig_mes)
        
        if a == 0:
            return {"turnover_total": 0.0, "turnover_vol": 0.0, "turnover_inv": 0.0}
        
        # Identificar voluntários (contém "Pedido" no motivo)
        if mot_col:
            dv = deslig_mes[mot_col].astype(str).str.contains("Pedido", case=False, na=False).sum()
        else:
            dv = 0
        
        di = d - dv
        
        return {
            "turnover_total": round((d / a) * 100, 1),
            "turnover_vol": round((dv / a) * 100, 1),
            "turnover_inv": round((di / a) * 100, 1),
            "ativos": a,
            "desligados": d,
            "voluntarios": dv,
            "involuntarios": di
        }
    
    # Caso histórico (média mensal)
    dmin = dft[adm_col].min()
    dmax = dft[desl_col].max() if dft[desl_col].notna().any() else datetime.now()
    
    if pd.isna(dmin):
        return {"turnover_total": 0.0, "turnover_vol": 0.0, "turnover_inv": 0.0}
    
    meses = pd.date_range(dmin, dmax, freq="MS")
    vals = []
    
    for mes in meses:
        ativos_mes = dft[(dft[adm_col] <= mes) & ((dft[desl_col].isna()) | (dft[desl_col] > mes))]
        deslig_mes = dft[(dft[desl_col].notna()) & (dft[desl_col].dt.to_period("M") == mes.to_period("M"))]
        
        a, d = len(ativos_mes), len(deslig_mes)
        
        if a == 0:
            continue
        
        if mot_col:
            dv = deslig_mes[mot_col].astype(str).str.contains("Pedido", case=False, na=False).sum()
        else:
            dv = 0
        
        di = d - dv
        vals.append([
            (d/a)*100 if a>0 else 0,
            (dv/a)*100 if a>0 else 0,
            (di/a)*100 if a>0 else 0
        ])
    
    if not vals:
        return {"turnover_total": 0.0, "turnover_vol": 0.0, "turnover_inv": 0.0}
    
    arr = np.array(vals)
    return {
        "turnover_total": round(arr[:, 0].mean(), 1),
        "turnover_vol": round(arr[:, 1].mean(), 1),
        "turnover_inv": round(arr[:, 2].mean(), 1)
    }


def calculate_turnover_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula histórico mensal de turnover.
    
    Returns:
        DataFrame com colunas: Mês, Ativos, Desligados, Voluntários, 
        Involuntários, Turnover Total (%), Turnover Voluntário (%), 
        Turnover Involuntário (%)
    """
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    mot_col = col_like(df, "motivo de desligamento")
    
    if not adm_col or not desl_col:
        return pd.DataFrame()
    
    dft = df.copy()
    dft[adm_col] = pd.to_datetime(dft[adm_col], errors="coerce")
    dft[desl_col] = pd.to_datetime(dft[desl_col], errors="coerce")
    
    dmin = dft[adm_col].min()
    dmax = dft[desl_col].max() if dft[desl_col].notna().any() else datetime.now()
    
    if pd.isna(dmin):
        return pd.DataFrame()
    
    meses = pd.date_range(dmin, dmax, freq="MS")
    rows = []
    
    for mes in meses:
        ativos_mes = dft[(dft[adm_col] <= mes) & ((dft[desl_col].isna()) | (dft[desl_col] > mes))]
        deslig_mes = dft[(dft[desl_col].notna()) & (dft[desl_col].dt.to_period("M") == mes.to_period("M"))]
        
        a, d = len(ativos_mes), len(deslig_mes)
        
        if mot_col:
            dv = deslig_mes[mot_col].astype(str).str.contains("Pedido", case=False, na=False).sum()
        else:
            dv = 0
        
        di = d - dv
        
        rows.append({
            "Mês": mes.strftime("%Y-%m"),
            "Ativos": a,
            "Desligados": d,
            "Voluntários": dv,
            "Involuntários": di,
            "Turnover Total (%)": (d/a)*100 if a>0 else 0,
            "Turnover Voluntário (%)": (dv/a)*100 if a>0 else 0,
            "Turnover Involuntário (%)": (di/a)*100 if a>0 else 0
        })
    
    return pd.DataFrame(rows)


def calculate_tenure(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcula tenure médio (tempo até desligamento).
    
    Returns:
        Dict com tenure_total, tenure_vol, tenure_inv (em meses)
    """
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    mot_col = col_like(df, "motivo de desligamento")
    
    if not adm_col or not desl_col:
        return {"tenure_total": 0.0, "tenure_vol": 0.0, "tenure_inv": 0.0}
    
    # Filtrar apenas desligados
    dfd = df[df["ativo"] == False].copy() if "ativo" in df.columns else df.copy()
    
    if dfd.empty:
        return {"tenure_total": 0.0, "tenure_vol": 0.0, "tenure_inv": 0.0}
    
    dfd[adm_col] = pd.to_datetime(dfd[adm_col], errors="coerce")
    dfd[desl_col] = pd.to_datetime(dfd[desl_col], errors="coerce")
    dfd["tenure_meses"] = (dfd[desl_col] - dfd[adm_col]).dt.days / 30
    
    tenure_total = safe_mean(dfd["tenure_meses"])
    
    if mot_col:
        mask_vol = dfd[mot_col].astype(str).str.contains("Pedido", case=False, na=False)
        tenure_vol = safe_mean(dfd.loc[mask_vol, "tenure_meses"])
        tenure_inv = safe_mean(dfd.loc[~mask_vol, "tenure_meses"])
    else:
        tenure_vol = tenure_total
        tenure_inv = tenure_total
    
    return {
        "tenure_total": tenure_total,
        "tenure_vol": tenure_vol,
        "tenure_inv": tenure_inv
    }


def calculate_headcount(df: pd.DataFrame, group_by: str = "departamento") -> pd.DataFrame:
    """
    Calcula headcount agrupado por coluna especificada.
    
    Args:
        df: DataFrame com colaboradores
        group_by: Coluna para agrupar (padrão: "departamento")
    
    Returns:
        DataFrame com headcount e percentual
    """
    group_col = col_like(df, group_by)
    
    if not group_col:
        return pd.DataFrame()
    
    # Filtrar apenas ativos
    if "ativo" in df.columns:
        base = df[df["ativo"] == True]
    else:
        desl_col = col_like(df, "data de desligamento")
        if desl_col:
            base = df[df[desl_col].isna()]
        else:
            base = df
    
    if base.empty:
        return pd.DataFrame()
    
    mat_col = col_like(base, "matricula")
    if not mat_col:
        return pd.DataFrame()
    
    dist = base.groupby(group_col)[mat_col].count().reset_index()
    dist.columns = [group_by, "Headcount"]
    dist["%"] = (dist["Headcount"] / dist["Headcount"].sum()) * 100
    
    return dist.sort_values("Headcount", ascending=False).reset_index(drop=True)


def calculate_basic_kpis(df: pd.DataFrame) -> Dict[str, any]:
    """
    Calcula KPIs básicos consolidados.
    
    Returns:
        Dict com todos os KPIs básicos
    """
    ativos = df[df["ativo"] == True] if "ativo" in df.columns else df
    
    tipo_c = col_like(ativos, "tipo_contrato")
    pct_clt = round((ativos[tipo_c].astype(str).str.upper().eq("CLT")).mean()*100, 1) if tipo_c else 0
    
    gen_c = col_like(ativos, "genero")
    pct_fem = round((ativos[gen_c].astype(str).str.lower().eq("feminino")).mean()*100, 1) if gen_c else 0
    
    cargo_c = col_like(ativos, "cargo")
    pct_lider = round(
        ativos[cargo_c].astype(str).str.lower().str.contains("coord|gerente|diretor", na=False).mean()*100, 1
    ) if cargo_c else 0
    
    return {
        "total_ativos": len(ativos),
        "pct_clt": pct_clt,
        "pct_feminino": pct_fem,
        "pct_lideranca": pct_lider
    }
