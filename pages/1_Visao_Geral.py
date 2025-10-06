import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="📍 Visão Geral — Dashboard de Turnover", layout="wide")

st.title("📍 Visão Geral — KPIs Consolidados de People Analytics")
st.caption("Resumo executivo com os principais indicadores de Headcount, Turnover, Tenure e Risco (TRI)")

# =========================================================
# FUNÇÕES AUXILIARES
# =========================================================
def col(df, name):
    """Busca uma coluna com nome semelhante (ignora maiúsculas e espaços)."""
    cols = [c for c in df.columns if c.lower().strip() == name.lower().strip()]
    return cols[0] if cols else None

def safe_mean(series):
    return round(series.mean(), 1) if not series.empty else 0

# =========================================================
# CARREGAMENTO DE DADOS
# =========================================================
if "df" not in st.session_state:
    st.warning("⚠️ Nenhum dado encontrado. Volte para a tela principal e carregue o arquivo Excel.")
    st.stop()

df = st.session_state["df"].copy()

# Garantir campos essenciais
if "ativo" not in df.columns:
    df["ativo"] = df.get("data de desligamento").isna() if "data de desligamento" in df.columns else True
if "tempo_casa" not in df.columns and "data de admissão" in df.columns:
    now = pd.Timestamp.now()
    df["tempo_casa"] = (now - pd.to_datetime(df["data de admissão"], errors="coerce")).dt.days / 30

# =========================================================
# HEADCOUNT
# =========================================================
ativos = df[df["ativo"] == True]
total_ativos = len(ativos)

tipo_col = col(ativos, "tipo_contrato")
if tipo_col:
    total_clt = (ativos[tipo_col].astype(str).str.upper() == "CLT").sum()
    pct_clt = round((total_clt / total_ativos) * 100, 1) if total_ativos else 0
else:
    pct_clt = 0

gen_col = col(ativos, "genero")
if gen_col:
    pct_fem = round((ativos[gen_col].astype(str).str.lower() == "feminino").mean() * 100, 1)
else:
    pct_fem = 0

cargo_col = col(ativos, "cargo")
if cargo_col:
    cargos_lideranca = ativos[cargo_col].astype(str).str.lower().str.contains("coord|gerente|diretor", na=False)
    pct_lideranca = round((cargos_lideranca.mean()) * 100, 1)
else:
    pct_lideranca = 0

# =========================================================
# TURNOVER
# =========================================================
adm_col = col(df, "data de admissão")
desl_col = col(df, "data de desligamento")
motivo_col = col(df, "motivo de desligamento")

turnover_total_medio = turnover_vol_medio = turnover_invol_medio = 0

if adm_col and desl_col:
    df_turn = df.copy()
    df_turn[adm_col] = pd.to_datetime(df_turn[adm_col], errors="coerce")
    df_turn[desl_col] = pd.to_datetime(df_turn[desl_col], errors="coerce")

    data_min = df_turn[adm_col].min()
    data_max = df_turn[desl_col].max() if df_turn[desl_col].notna().any() else datetime.now()
    meses = pd.date_range(data_min, data_max, freq="MS")

    turnover_data = []
    for mes in meses:
        ativos_mes = df_turn[(df_turn[adm_col] <= mes) & ((df_turn[desl_col].isna()) | (df_turn[desl_col] > mes))]
        desligados_mes = df_turn[(df_turn[desl_col].notna()) & (df_turn[desl_col].dt.to_period("M") == mes.to_period("M"))]
        ativos = len(ativos_mes)
        deslig_total = len(desligados_mes)
        if motivo_col:
            deslig_vol = desligados_mes[motivo_col].astype(str).str.contains("Pedido", case=False, na=False).sum()
        else:
            deslig_vol = 0
        deslig_invol = deslig_total - deslig_vol
        turnover_total = (deslig_total / ativos) * 100 if ativos > 0 else 0
        turnover_vol = (deslig_vol / ativos) * 100 if ativos > 0 else 0
        turnover_invol = (deslig_invol / ativos) * 100 if ativos > 0 else 0
        turnover_data.append([mes, turnover_total, turnover_vol, turnover_invol])

    turnover_df = pd.DataFrame(turnover_data, columns=["mes", "total", "vol", "invol"])
    turnover_total_medio = safe_mean(turnover_df["total"])
    turnover_vol_medio = safe_mean(turnover_df["vol"])
    turnover_invol_medio = safe_mean(turnover_df["invol"])

# =========================================================
# TENURE
# =========================================================
try:
    df_desl = df[df["ativo"] == False].copy()
    if adm_col and desl_col:
        df_desl["tenure_meses"] = (df_desl[desl_col] - df_desl[adm_col]).dt.days / 30
        tenure_total = safe_mean(df_desl["tenure_meses"])
        tenure_vol = safe_mean(df_desl.loc[df_desl[motivo_col].astype(str).str.contains("Pedido", na=False, case=False), "tenure_meses"])
        tenure_invol = safe_mean(df_desl.loc[~df_desl[motivo_col].astype(str).str.contains("Pedido", na=False, case=False), "tenure_meses"])
    else:
        tenure_total = tenure_vol = tenure_invol = 0
    tenure_ativos = safe_mean(df.loc[df["ativo"], "tempo_casa"])
except Exception:
    tenure_total = tenure_vol = tenure_invol = tenure_ativos = 0

# =========================================================
# RISCO (TRI)
# =========================================================
try:
    now = pd.Timestamp.now()
    df["meses_desde_promocao"] = (now - pd.to_datetime(df.get("ultima promoção"), errors="coerce")).dt.days / 30
    df["meses_desde_merito"] = (now - pd.to_datetime(df.get("ultimo mérito"), errors="coerce")).dt.days / 30

    if "matricula do gestor" in df.columns:
        gestor_size = df.groupby("matricula do gestor")["matricula"].count().rename("tamanho_equipe")
        df = df.merge(gestor_size, left_on="matricula do gestor", right_index=True, how="left")
    else:
        df["tamanho_equipe"] = 1

    perf_map = {"excepcional": 10, "acima do esperado": 7, "dentro do esperado": 4, "abaixo do esperado": 1}
    df["score_perf_raw"] = df.get("avaliação", 4).astype(str).str.lower().map(perf_map).fillna(4)

    def norm_0_1(s):
        s = s.astype(float)
        maxv = s.max(skipna=True)
        return s / maxv if pd.notna(maxv) and maxv not in [0, np.inf] else s.fillna(0)

    df["score_perf_inv"] = 1 - norm_0_1(df["score_perf_raw"])
    df["score_tempo_promo"] = norm_0_1(df["meses_desde_promocao"].fillna(0))
    df["score_tempo_casa"] = norm_0_1(df["tempo_casa"].fillna(0))
    df["score_merito"] = norm_0_1(df["meses_desde_merito"].fillna(0))
    df["score_tamanho_eq"] = norm_0_1(df["tamanho_equipe"].fillna(0))

    df["risco_turnover"] = (
        0.30 * df["score_perf_inv"]
        + 0.25 * df["score_tempo_promo"]
        + 0.15 * df["score_tempo_casa"]
        + 0.15 * df["score_tamanho_eq"]
        + 0.15 * df["score_merito"]
    ) * 100

    risco_medio = safe_mean(df["risco_turnover"])
    risco_alto = round((df["risco_turnover"] > 60).mean() * 100, 1)
except Exception:
    risco_medio = risco_alto = 0

# =========================================================
# EXIBIÇÃO
# =========================================================
st.markdown("### 👥 Headcount")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ativos", total_ativos)
c2.metric("% CLT", f"{pct_clt}%")
c3.metric("% Feminino", f"{pct_fem}%")
c4.metric("% Liderança", f"{pct_lideranca}%")

st.markdown("### 🔄 Turnover (médio anual)")
c5, c6, c7 = st.columns(3)
c5.metric("Total (%)", f"{turnover_total_medio}")
c6.metric("Voluntário (%)", f"{turnover_vol_medio}")
c7.metric("Involuntário (%)", f"{turnover_invol_medio}")

st.markdown("### ⏳ Tenure (Tempo Médio)")
c8, c9, c10, c11 = st.columns(4)
c8.metric("Total (m)", f"{tenure_total}")
c9.metric("Voluntário (m)", f"{tenure_vol}")
c10.metric("Involuntário (m)", f"{tenure_invol}")
c11.metric("Ativos (m)", f"{tenure_ativos}")

st.markdown("### 🔮 Risco de Saída (TRI)")
c12, c13 = st.columns(2)
c12.metric("Risco Médio", f"{risco_medio}")
c13.metric("% em Risco Alto", f"{risco_alto}%")

st.divider()
st.markdown(f"""
📊 *Resumo executivo:*  
Headcount atual de **{total_ativos} colaboradores**, com turnover médio de **{turnover_total_medio}%**  
({turnover_vol_medio}% voluntário e {turnover_invol_medio}% involuntário).  
Tempo médio até desligamento: **{tenure_total} meses**, e risco médio (TRI) em **{risco_medio}**,  
com **{risco_alto}%** dos colaboradores em alto risco de saída.
""")

