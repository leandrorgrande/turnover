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
    Calcula turnover total, voluntário e involuntário usando tipo desligamento e motivo.
    
    Fórmula: Turnover = (Desligados no mês / Headcount no início do mês) * 100
    
    Args:
        df: DataFrame com dados de colaboradores
        periodo_mes: Data de referência (se None, calcula histórico médio)
    
    Returns:
        Dict com turnover_total, turnover_vol, turnover_inv e quantidades
    """
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    tipo_desl_col = col_like(df, "tipo desligamento")
    mot_col = col_like(df, "motivo de desligamento")
    
    if not adm_col or not desl_col:
        return {
            "turnover_total": 0.0, 
            "turnover_vol": 0.0, 
            "turnover_inv": 0.0,
            "ativos": 0,
            "desligados": 0,
            "voluntarios": 0,
            "involuntarios": 0
        }
    
    dft = df.copy()
    dft[adm_col] = pd.to_datetime(dft[adm_col], errors="coerce")
    dft[desl_col] = pd.to_datetime(dft[desl_col], errors="coerce")
    
    # Se tem período específico (competência)
    if periodo_mes and "ativo" in df.columns and "desligado_no_mes" in df.columns:
        # Headcount: ativos no início do mês (antes dos desligamentos)
        ativos_inicio_mes = df[df["ativo"] == True]
        # Desligados no mês
        deslig_mes = df[df["desligado_no_mes"] == True]
        
        a = len(ativos_inicio_mes)
        d = len(deslig_mes)
        
        if a == 0:
            return {
                "turnover_total": 0.0, 
                "turnover_vol": 0.0, 
                "turnover_inv": 0.0,
                "ativos": 0,
                "desligados": 0,
                "voluntarios": 0,
                "involuntarios": 0
            }
        
        # Identificar voluntários: tipo desligamento contém "voluntário" ou motivo contém "pedido"
        dv = 0
        if tipo_desl_col:
            dv = deslig_mes[tipo_desl_col].astype(str).str.lower().str.contains("voluntário|pedido|demissão|rescisão", case=False, na=False).sum()
        elif mot_col:
            dv = deslig_mes[mot_col].astype(str).str.lower().str.contains("pedido|demissão|rescisão|voluntário", case=False, na=False).sum()
        
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
    
    # Caso histórico (média mensal) - usando headcount do início de cada mês
    dmin = dft[adm_col].min()
    dmax = dft[desl_col].max() if dft[desl_col].notna().any() else datetime.now()
    
    if pd.isna(dmin):
        return {
            "turnover_total": 0.0, 
            "turnover_vol": 0.0, 
            "turnover_inv": 0.0,
            "ativos": 0,
            "desligados": 0,
            "voluntarios": 0,
            "involuntarios": 0
        }
    
    meses = pd.date_range(dmin, dmax, freq="MS")
    vals = []
    total_ativos = 0
    total_desligados = 0
    total_voluntarios = 0
    total_involuntarios = 0
    meses_validos = 0
    
    for mes in meses:
        # Headcount no início do mês: quem foi admitido antes ou no início do mês e ainda não foi desligado
        # Usar primeiro dia do mês para calcular headcount
        inicio_mes = mes.replace(day=1)
        ativos_inicio_mes = dft[
            (dft[adm_col] <= inicio_mes) & 
            ((dft[desl_col].isna()) | (dft[desl_col] > inicio_mes))
        ]
        
        # Desligados no mês
        deslig_mes = dft[
            (dft[desl_col].notna()) & 
            (dft[desl_col].dt.to_period("M") == mes.to_period("M"))
        ]
        
        a = len(ativos_inicio_mes)
        d = len(deslig_mes)
        
        if a == 0:
            continue
        
        meses_validos += 1
        total_ativos += a
        total_desligados += d
        
        # Identificar voluntários usando tipo desligamento ou motivo
        dv = 0
        if tipo_desl_col and not deslig_mes.empty:
            dv = deslig_mes[tipo_desl_col].astype(str).str.lower().str.contains(
                "voluntário|pedido|demissão|rescisão", case=False, na=False
            ).sum()
        elif mot_col and not deslig_mes.empty:
            dv = deslig_mes[mot_col].astype(str).str.lower().str.contains(
                "pedido|demissão|rescisão|voluntário", case=False, na=False
            ).sum()
        
        di = d - dv
        total_voluntarios += dv
        total_involuntarios += di
        
        vals.append([
            (d/a)*100 if a>0 else 0,
            (dv/a)*100 if a>0 else 0,
            (di/a)*100 if a>0 else 0
        ])
    
    if not vals:
        return {
            "turnover_total": 0.0, 
            "turnover_vol": 0.0, 
            "turnover_inv": 0.0,
            "ativos": 0,
            "desligados": 0,
            "voluntarios": 0,
            "involuntarios": 0
        }
    
    arr = np.array(vals)
    
    # Calcular médias
    avg_ativos = int(total_ativos / meses_validos) if meses_validos > 0 else 0
    avg_desligados = round(total_desligados / meses_validos, 1) if meses_validos > 0 else 0.0
    avg_voluntarios = round(total_voluntarios / meses_validos, 1) if meses_validos > 0 else 0.0
    avg_involuntarios = round(total_involuntarios / meses_validos, 1) if meses_validos > 0 else 0.0
    
    return {
        "turnover_total": round(arr[:, 0].mean(), 1),
        "turnover_vol": round(arr[:, 1].mean(), 1),
        "turnover_inv": round(arr[:, 2].mean(), 1),
        "ativos": avg_ativos,
        "desligados": avg_desligados,
        "voluntarios": avg_voluntarios,
        "involuntarios": avg_involuntarios
    }


def calculate_turnover_history(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula histórico mensal de turnover usando headcount do início do mês.
    
    Returns:
        DataFrame com colunas: Mês, Headcount (início), Desligados, Voluntários, 
        Involuntários, Turnover Total (%), Turnover Voluntário (%), 
        Turnover Involuntário (%)
    """
    adm_col = col_like(df, "data de admissão")
    desl_col = col_like(df, "data de desligamento")
    tipo_desl_col = col_like(df, "tipo desligamento")
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
        # Headcount no início do mês (antes dos desligamentos)
        inicio_mes = mes.replace(day=1)
        headcount_inicio = dft[
            (dft[adm_col] <= inicio_mes) & 
            ((dft[desl_col].isna()) | (dft[desl_col] > inicio_mes))
        ]
        
        # Desligados no mês
        deslig_mes = dft[
            (dft[desl_col].notna()) & 
            (dft[desl_col].dt.to_period("M") == mes.to_period("M"))
        ]
        
        hc = len(headcount_inicio)
        d = len(deslig_mes)
        
        # Identificar voluntários usando tipo desligamento ou motivo
        dv = 0
        if tipo_desl_col and not deslig_mes.empty:
            dv = deslig_mes[tipo_desl_col].astype(str).str.lower().str.contains(
                "voluntário|pedido|demissão|rescisão", case=False, na=False
            ).sum()
        elif mot_col and not deslig_mes.empty:
            dv = deslig_mes[mot_col].astype(str).str.lower().str.contains(
                "pedido|demissão|rescisão|voluntário", case=False, na=False
            ).sum()
        
        di = d - dv
        
        rows.append({
            "Mês": mes.strftime("%Y-%m"),
            "Headcount (início)": hc,
            "Desligados": d,
            "Voluntários": dv,
            "Involuntários": di,
            "Turnover Total (%)": (d/hc)*100 if hc>0 else 0,
            "Turnover Voluntário (%)": (dv/hc)*100 if hc>0 else 0,
            "Turnover Involuntário (%)": (di/hc)*100 if hc>0 else 0
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
    
    # Identificar voluntários usando tipo desligamento ou motivo
    tipo_desl_col = col_like(dfd, "tipo desligamento")
    mask_vol = pd.Series([False] * len(dfd), index=dfd.index)
    
    if tipo_desl_col:
        mask_vol = dfd[tipo_desl_col].astype(str).str.lower().str.contains(
            "voluntário|pedido|demissão|rescisão", case=False, na=False
        )
    elif mot_col:
        mask_vol = dfd[mot_col].astype(str).str.lower().str.contains(
            "pedido|demissão|rescisão|voluntário", case=False, na=False
        )
    
    if mask_vol.any():
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
    Exclui apenas quem tem data de desligamento (está desligado).
    
    Args:
        df: DataFrame com colaboradores
        group_by: Coluna para agrupar (padrão: "departamento")
    
    Returns:
        DataFrame com headcount e percentual
    """
    group_col = col_like(df, group_by)
    
    if not group_col:
        return pd.DataFrame()
    
    # Filtrar apenas quem NÃO tem data de desligamento (ativo)
    desl_col = col_like(df, "data de desligamento")
    if desl_col:
        # Apenas quem não tem data de desligamento
        base = df[df[desl_col].isna()].copy()
    elif "ativo" in df.columns:
        base = df[df["ativo"] == True].copy()
    else:
        base = df.copy()
    
    if base.empty:
        return pd.DataFrame()
    
    mat_col = col_like(base, "matricula")
    if not mat_col:
        return pd.DataFrame()
    
    dist = base.groupby(group_col)[mat_col].count().reset_index()
    dist.columns = [group_by, "Headcount"]
    dist["%"] = (dist["Headcount"] / dist["Headcount"].sum()) * 100
    
    return dist.sort_values("Headcount", ascending=False).reset_index(drop=True)


def calculate_contract_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula distribuição de todos os tipos de contrato com % e quantidade.
    
    Returns:
        DataFrame com Tipo, Quantidade, Percentual
    """
    ativos = df[df["ativo"] == True] if "ativo" in df.columns else df
    tipo_c = col_like(ativos, "tipo_contrato")
    
    if not tipo_c or ativos.empty:
        return pd.DataFrame()
    
    # Contar por tipo de contrato
    dist = ativos[tipo_c].value_counts().reset_index()
    dist.columns = ["Tipo", "Quantidade"]
    dist["Percentual (%)"] = (dist["Quantidade"] / dist["Quantidade"].sum() * 100).round(1)
    
    return dist.sort_values("Quantidade", ascending=False).reset_index(drop=True)


def calculate_monthly_dismissals(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calcula desligamentos médios por mês.
    
    Returns:
        Dict com desligamentos_medio_mes e detalhamento
    """
    desl_col = col_like(df, "data de desligamento")
    
    if not desl_col:
        return {
            "desligamentos_medio_mes": 0.0,
            "total_desligados": 0,
            "meses_com_dados": 0
        }
    
    dft = df.copy()
    dft[desl_col] = pd.to_datetime(dft[desl_col], errors="coerce")
    
    # Filtrar apenas quem tem data de desligamento
    desligados = dft[dft[desl_col].notna()]
    
    if desligados.empty:
        return {
            "desligamentos_medio_mes": 0.0,
            "total_desligados": 0,
            "meses_com_dados": 0
        }
    
    # Agrupar por mês
    desligados["mes_ano"] = desligados[desl_col].dt.to_period("M")
    desligados_por_mes = desligados["mes_ano"].value_counts()
    
    if desligados_por_mes.empty:
        return {
            "desligamentos_medio_mes": 0.0,
            "total_desligados": 0,
            "meses_com_dados": 0
        }
    
    deslig_medio = desligados_por_mes.mean()
    total_deslig = len(desligados)
    meses_com_dados = len(desligados_por_mes)
    
    return {
        "desligamentos_medio_mes": round(deslig_medio, 1),
        "total_desligados": total_deslig,
        "meses_com_dados": meses_com_dados
    }


def calculate_basic_kpis(df: pd.DataFrame) -> Dict[str, any]:
    """
    Calcula KPIs básicos consolidados com quantidades e percentuais.
    
    Returns:
        Dict com todos os KPIs básicos incluindo quantidades
    """
    ativos = df[df["ativo"] == True] if "ativo" in df.columns else df
    total_ativos = len(ativos)
    
    # Tipo de contrato
    tipo_c = col_like(ativos, "tipo_contrato")
    if tipo_c and total_ativos > 0:
        mask_clt = ativos[tipo_c].astype(str).str.upper().eq("CLT")
        qtd_clt = mask_clt.sum()
        pct_clt = round((qtd_clt / total_ativos) * 100, 1)
    else:
        qtd_clt = 0
        pct_clt = 0.0
    
    # Gênero
    gen_c = col_like(ativos, "genero")
    if gen_c and total_ativos > 0:
        mask_fem = ativos[gen_c].astype(str).str.lower().eq("feminino")
        mask_masc = ativos[gen_c].astype(str).str.lower().isin(["masculino", "m"])
        qtd_fem = mask_fem.sum()
        qtd_masc = mask_masc.sum()
        pct_fem = round((qtd_fem / total_ativos) * 100, 1)
        pct_masc = round((qtd_masc / total_ativos) * 100, 1)
    else:
        qtd_fem = 0
        qtd_masc = 0
        pct_fem = 0.0
        pct_masc = 0.0
    
    # Liderança
    cargo_c = col_like(ativos, "cargo")
    if cargo_c and total_ativos > 0:
        mask_lider = ativos[cargo_c].astype(str).str.lower().str.contains("coord|gerente|diretor", na=False)
        qtd_lider = mask_lider.sum()
        pct_lider = round((qtd_lider / total_ativos) * 100, 1)
    else:
        qtd_lider = 0
        pct_lider = 0.0
    
    return {
        "total_ativos": total_ativos,
        "qtd_clt": qtd_clt,
        "pct_clt": pct_clt,
        "qtd_feminino": qtd_fem,
        "pct_feminino": pct_fem,
        "qtd_masculino": qtd_masc,
        "pct_masculino": pct_masc,
        "qtd_lideranca": qtd_lider,
        "pct_lideranca": pct_lider
    }
